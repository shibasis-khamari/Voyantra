import os
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
import json
import bcrypt
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "voyantra_db")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def hash_password(plain_pw: str) -> str:
    """Hash plaintext password with bcrypt."""
    if plain_pw.startswith("$2b$") or plain_pw.startswith("$2a$"):
        return plain_pw
    return bcrypt.hashpw(plain_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    """Verify password against bcrypt hash, with fallback to plaintext for unmigrated demo seeds."""
    if not hashed_pw:
        return False
    if hashed_pw.startswith("$2b$") or hashed_pw.startswith("$2a$"):
        try:
            return bcrypt.checkpw(plain_pw.encode("utf-8"), hashed_pw.encode("utf-8"))
        except Exception:
            return False
    return plain_pw == hashed_pw

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self._memory_users: List[Dict[str, Any]] = [
            {
                "id": "usr-demo-01",
                "name": "Demo Traveler",
                "email": "user@voyantra.com",
                "password": hash_password("user123"),
                "role": "user"
            },
            {
                "id": "adm-demo-01",
                "name": "System Administrator",
                "email": "admin@voyantra.com",
                "password": hash_password("admin123"),
                "role": "admin"
            }
        ]
        self._init_connection()

    def _init_connection(self):
        try:
            timeout_ms = 7000 if "mongodb+srv" in MONGODB_URL else 2000
            self.client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=timeout_ms)
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            self.is_connected = True
            print(f"[MongoDBManager] Successfully connected to MongoDB database '{DB_NAME}'")
            self._seed_default_users()
            self._seed_all_collections()
        except Exception as e:
            self.is_connected = False
            print(f"[MongoDBManager] MongoDB connection notice ({e}). Operating with resilient storage.")

    def _seed_default_users(self):
        if not self.is_connected or self.db is None:
            return
        users_col = self.db["users"]
        if users_col.count_documents({}) == 0:
            for u in self._memory_users:
                users_col.insert_one(dict(u))
            print("[MongoDBManager] Seeded default users into MongoDB 'users' collection.")
        # Ensure all existing users in DB have bcrypt-hashed passwords
        for existing in users_col.find():
            existing_pw = existing.get("password", "")
            if existing_pw and not (existing_pw.startswith("$2b$") or existing_pw.startswith("$2a$")):
                hashed = hash_password(existing_pw)
                users_col.update_one({"_id": existing["_id"]}, {"$set": {"password": hashed}})

    def _seed_all_collections(self):
        """Seed places, hotels, and festivals collections into voyantra_db from JSON files."""
        if not self.is_connected or self.db is None:
            return

        # 1. Seed places
        places_col = self.db["places"]
        if places_col.count_documents({}) == 0:
            all_places = []
            for file in DATA_DIR.glob("*_places.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        all_places.extend(items)
                except Exception as e:
                    print(f"[MongoDBManager] Error reading {file.name}: {e}")
            if all_places:
                # Deduplicate by id
                seen_ids = set()
                unique_places = []
                for p in all_places:
                    if p.get("id") not in seen_ids:
                        seen_ids.add(p.get("id"))
                        unique_places.append(p)
                places_col.insert_many(unique_places)
                print(f"[MongoDBManager] Seeded {len(unique_places)} places into MongoDB 'places' collection.")

        # 2. Seed hotels
        hotels_col = self.db["hotels"]
        if hotels_col.count_documents({}) == 0:
            all_hotels = []
            for file in DATA_DIR.glob("*_hotels.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        all_hotels.extend(items)
                except Exception as e:
                    print(f"[MongoDBManager] Error reading {file.name}: {e}")
            if all_hotels:
                hotels_col.insert_many(all_hotels)
                print(f"[MongoDBManager] Seeded {len(all_hotels)} hotels into MongoDB 'hotels' collection.")

        # 3. Seed festivals
        festivals_col = self.db["festivals"]
        if festivals_col.count_documents({}) == 0:
            all_festivals = []
            for file in DATA_DIR.glob("*_festivals.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        all_festivals.extend(items)
                except Exception as e:
                    print(f"[MongoDBManager] Error reading {file.name}: {e}")
            if all_festivals:
                festivals_col.insert_many(all_festivals)
                print(f"[MongoDBManager] Seeded {len(all_festivals)} festivals into MongoDB 'festivals' collection.")

    def get_users_collection(self):
        if self.is_connected and self.db is not None:
            return self.db["users"]
        return None

    def get_collection(self, name: str):
        if self.is_connected and self.db is not None:
            return self.db[name]
        return None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.db is not None:
            doc = self.db["users"].find_one({"email": email.lower()})
            if doc:
                doc["_id"] = str(doc.get("_id", doc.get("id")))
                return doc
        
        for u in self._memory_users:
            if u["email"].lower() == email.lower():
                return u
        return None

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.db is not None:
            query = {"id": user_id}
            try:
                from bson import ObjectId
                query = {"$or": [{"id": user_id}, {"_id": ObjectId(user_id)}]}
            except Exception:
                pass
            doc = self.db["users"].find_one(query)
            if doc:
                doc["_id"] = str(doc.get("_id", doc.get("id")))
                if "id" not in doc:
                    doc["id"] = str(doc["_id"])
                return doc
        for u in self._memory_users:
            if u.get("id") == user_id or str(u.get("_id")) == user_id:
                return u
        return None

    def list_all_users(self) -> List[Dict[str, Any]]:
        results = []
        if self.is_connected and self.db is not None:
            for doc in self.db["users"].find():
                u_id = str(doc.get("id") or doc.get("_id"))
                results.append({
                    "id": u_id,
                    "name": doc.get("name", "Traveler"),
                    "email": doc.get("email", ""),
                    "role": doc.get("role", "user"),
                    "avatar_url": doc.get("avatar_url"),
                    "created_at": doc.get("created_at")
                })
            return results
        for u in self._memory_users:
            results.append({
                "id": str(u.get("id") or u.get("_id")),
                "name": u.get("name", "Traveler"),
                "email": u.get("email", ""),
                "role": u.get("role", "user"),
                "avatar_url": u.get("avatar_url"),
                "created_at": u.get("created_at")
            })
        return results

    def delete_user(self, user_id: str) -> bool:
        if self.is_connected and self.db is not None:
            query = {"id": user_id}
            try:
                from bson import ObjectId
                query = {"$or": [{"id": user_id}, {"_id": ObjectId(user_id)}]}
            except Exception:
                pass
            res = self.db["users"].delete_one(query)
            return res.deleted_count > 0
        for i, u in enumerate(self._memory_users):
            if u.get("id") == user_id or str(u.get("_id")) == user_id:
                self._memory_users.pop(i)
                return True
        return False

    def update_user_role(self, user_id: str, new_role: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.db is not None:
            query = {"id": user_id}
            try:
                from bson import ObjectId
                query = {"$or": [{"id": user_id}, {"_id": ObjectId(user_id)}]}
            except Exception:
                pass
            self.db["users"].update_one(query, {"$set": {"role": new_role}})
            return self.find_user_by_id(user_id)
        for u in self._memory_users:
            if u.get("id") == user_id or str(u.get("_id")) == user_id:
                u["role"] = new_role
                return u
        return None

    def insert_user(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        user_dict["email"] = user_dict["email"].lower()
        if self.is_connected and self.db is not None:
            res = self.db["users"].insert_one(user_dict)
            user_dict["id"] = str(res.inserted_id)
            return user_dict
        
        self._memory_users.append(user_dict)
        return user_dict

db_manager = MongoDBManager()
db = db_manager

