"""
Voyantra Robust Vector Repository
Implements single-writer process-isolated vector storage with cross-process file locking,
atomic shadow swaps (zero-downtime rebuilds), generation tracking, and benchmarking.
"""
from abc import ABC, abstractmethod
import os
import time
import json
import uuid
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ....core.config import settings


class CrossProcessLock:
    """A cross-process file lock using an exclusive atomic lock file."""
    def __init__(self, lock_path: Path, timeout: float = 10.0, poll_interval: float = 0.05):
        self.lock_path = lock_path
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._fd: Optional[int] = None

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # O_CREAT | O_EXCL ensures atomic creation across processes
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.time() - start_time >= self.timeout:
                    # Break stale lock if lock file is older than 30 seconds
                    try:
                        mtime = os.path.getmtime(str(self.lock_path))
                        if time.time() - mtime > 30.0:
                            os.remove(str(self.lock_path))
                            continue
                    except Exception:
                        pass
                    raise TimeoutError(f"Could not acquire cross-process lock {self.lock_path} within {self.timeout}s")
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            try:
                if self.lock_path.exists():
                    os.remove(str(self.lock_path))
            except Exception:
                pass


class BaseVectorRepository(ABC):
    @abstractmethod
    def add_vectors(self, records: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_vectors(self, vector_ids: List[str]) -> int:
        pass


class LocalVectorRepository(BaseVectorRepository):
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.KNOWLEDGE_VECTOR_INDEX_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.storage_dir / "index.json"
        self.meta_file = self.storage_dir / "index.meta.json"
        self.lock_file = self.storage_dir / "index.lock"

        # In-memory cached representation for fast searches
        self._cached_generation_id: Optional[str] = None
        self._records: List[Dict[str, Any]] = []
        self._vectors_matrix: Optional[np.ndarray] = None
        self._id_to_index: Dict[str, int] = {}

        self._load_index_if_updated()

    def _get_on_disk_generation_id(self) -> Optional[str]:
        if not self.meta_file.exists():
            return None
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("generation_id")
        except Exception:
            return None

    def _load_index_if_updated(self):
        """Cross-process cache invalidation: reloads index if on-disk generation differs."""
        disk_gen = self._get_on_disk_generation_id()
        if disk_gen is not None and disk_gen == self._cached_generation_id:
            return  # Cache is fresh

        if not self.index_file.exists():
            self._records = []
            self._vectors_matrix = None
            self._id_to_index = {}
            self._cached_generation_id = None
            return

        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._records = data.get("records", [])
            self._cached_generation_id = disk_gen or data.get("generation_id", str(uuid.uuid4()))

            if self._records:
                vecs = [r["vector"] for r in self._records]
                self._vectors_matrix = np.array(vecs, dtype=np.float32)
                self._id_to_index = {r["id"]: idx for idx, r in enumerate(self._records)}
            else:
                self._vectors_matrix = None
                self._id_to_index = {}
        except Exception:
            pass

    def add_vectors(self, records: List[Dict[str, Any]]) -> int:
        """Adds or updates vectors using cross-process locking and atomic shadow swap."""
        if not records:
            return 0

        with CrossProcessLock(self.lock_file):
            self._load_index_if_updated()
            existing_map = {r["id"]: r for r in self._records}

            for rec in records:
                existing_map[rec["id"]] = rec

            updated_records = list(existing_map.values())
            new_generation_id = str(uuid.uuid4())

            # 1. Write shadow files
            shadow_index = self.storage_dir / f"index_shadow_{new_generation_id[:8]}.tmp"
            shadow_meta = self.storage_dir / f"meta_shadow_{new_generation_id[:8]}.tmp"

            payload = {
                "generation_id": new_generation_id,
                "records": updated_records,
                "count": len(updated_records),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(shadow_index, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            meta_payload = {
                "generation_id": new_generation_id,
                "count": len(updated_records),
                "dimension": len(updated_records[0]["vector"]) if updated_records else 0,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(shadow_meta, "w", encoding="utf-8") as f:
                json.dump(meta_payload, f)

            # 2. Atomic swap
            os.replace(str(shadow_index), str(self.index_file))
            os.replace(str(shadow_meta), str(self.meta_file))

            # 3. Reload in-memory
            self._load_index_if_updated()

        return len(records)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Executes vector search with cosine similarity and metadata pre-filtering."""
        self._load_index_if_updated()

        if self._vectors_matrix is None or len(self._records) == 0:
            return []

        q_arr = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr = q_arr / q_norm

        # Compute dot product against normalized matrix (cosine similarity)
        scores = np.dot(self._vectors_matrix, q_arr)

        # Apply metadata filters
        candidate_indices = []
        for idx, rec in enumerate(self._records):
            match = True
            if filter_dict:
                meta = rec.get("metadata", {})
                for k, v in filter_dict.items():
                    if meta.get(k) != v:
                        match = False
                        break
            if match:
                candidate_indices.append(idx)

        if not candidate_indices:
            return []

        # Sort candidate indices by score descending
        sorted_indices = sorted(candidate_indices, key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in sorted_indices:
            r = self._records[idx]
            results.append({
                "id": r["id"],
                "score": float(scores[idx]),
                "metadata": r.get("metadata", {}),
            })
        return results

    def delete_vectors(self, vector_ids: List[str]) -> int:
        """Deletes vectors by ID via atomic shadow swap."""
        if not vector_ids:
            return 0
        del_set = set(vector_ids)

        with CrossProcessLock(self.lock_file):
            self._load_index_if_updated()
            kept = [r for r in self._records if r["id"] not in del_set]
            deleted_count = len(self._records) - len(kept)
            if deleted_count == 0:
                return 0

            new_generation_id = str(uuid.uuid4())
            shadow_index = self.storage_dir / f"index_shadow_{new_generation_id[:8]}.tmp"
            shadow_meta = self.storage_dir / f"meta_shadow_{new_generation_id[:8]}.tmp"

            payload = {
                "generation_id": new_generation_id,
                "records": kept,
                "count": len(kept),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(shadow_index, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            meta_payload = {
                "generation_id": new_generation_id,
                "count": len(kept),
                "dimension": len(kept[0]["vector"]) if kept else 0,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(shadow_meta, "w", encoding="utf-8") as f:
                json.dump(meta_payload, f)

            os.replace(str(shadow_index), str(self.index_file))
            os.replace(str(shadow_meta), str(self.meta_file))
            self._load_index_if_updated()

        return deleted_count

    def benchmark_index(self) -> Dict[str, Any]:
        """Benchmarks query latency and storage size."""
        self._load_index_if_updated()
        count = len(self._records)
        dim = len(self._records[0]["vector"]) if count > 0 else 0

        # Run 50 warm-up & benchmark queries
        dummy_query = [0.1] * (dim or 384)
        t0 = time.time()
        for _ in range(50):
            self.search(dummy_query, top_k=5)
        elapsed = time.time() - t0
        avg_latency_ms = (elapsed / 50.0) * 1000.0

        size_bytes = self.index_file.stat().st_size if self.index_file.exists() else 0

        return {
            "document_count": count,
            "dimension": dim,
            "avg_latency_ms": round(avg_latency_ms, 3),
            "size_kb": round(size_bytes / 1024.0, 2),
            "generation_id": self._cached_generation_id,
        }


vector_repository = LocalVectorRepository()
