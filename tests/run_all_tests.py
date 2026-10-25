import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    tests_dir = Path(__file__).parent.resolve()
    # Find all test_*.py and verify_all_fixes.py
    test_files = sorted([
        f for f in tests_dir.glob("test_*.py")
    ] + [tests_dir / "verify_all_fixes.py"])

    print("=" * 70)
    print(f"VOYANTRA CONSOLIDATED TEST SUITE RUNNER")
    print(f"Discovered {len(test_files)} test suites in {tests_dir}")
    print("=" * 70)

    results = []
    total_start = time.time()

    for idx, test_file in enumerate(test_files, 1):
        test_name = test_file.name
        print(f"\n[{idx}/{len(test_files)}] RUNNING: {test_name} ...", flush=True)
        t0 = time.time()
        try:
            res = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=180,
                encoding="utf-8",
                errors="replace"
            )
            elapsed = time.time() - t0
            passed = (res.returncode == 0)
            status_str = "PASS" if passed else f"FAIL (exit {res.returncode})"
            results.append({
                "name": test_name,
                "status": status_str,
                "passed": passed,
                "elapsed": elapsed,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode
            })
            print(f"  -> {status_str} in {elapsed:.2f}s")
            if not passed:
                print(f"  [ERROR OUTPUT for {test_name}]:")
                print("\n".join(res.stdout.splitlines()[-10:]))
                print("\n".join(res.stderr.splitlines()[-10:]))
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            results.append({
                "name": test_name,
                "status": "TIMEOUT",
                "passed": False,
                "elapsed": elapsed,
                "stdout": "",
                "stderr": "Execution timed out after 180s",
                "returncode": -1
            })
            print(f"  -> TIMEOUT after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - t0
            results.append({
                "name": test_name,
                "status": f"ERROR ({type(e).__name__})",
                "passed": False,
                "elapsed": elapsed,
                "stdout": "",
                "stderr": str(e),
                "returncode": -2
            })
            print(f"  -> ERROR: {e}")

    total_elapsed = time.time() - total_start
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count

    print("\n" + "=" * 70)
    print("FINAL CONSOLIDATED TEST SUMMARY")
    print("=" * 70)
    print(f"{'Test File':<40} | {'Status':<12} | {'Time (s)':<8}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<40} | {r['status']:<12} | {r['elapsed']:>6.2f}s")
    print("-" * 70)
    print(f"Total Suites: {len(results)} | Passed: {passed_count} | Failed: {failed_count} | Total Time: {total_elapsed:.2f}s")
    print("=" * 70)

    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
