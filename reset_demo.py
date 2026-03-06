"""
reset_demo.py -- CUSTOS Redis Rule Reset
Clears all Redis rules for a fresh demo run.
Uses RedisCluster to handle Azure Managed Redis -MOVED redirects gracefully.
"""
import os, sys
from pathlib import Path
from urllib.parse import quote

# Load .env from module1-validator/ (absolute path relative to this script)
script_dir = Path(__file__).resolve().parent
env_path = script_dir / 'module1-validator' / '.env'
if not env_path.exists():
    env_path = script_dir / '.env'

print(f"Loading .env from: {env_path}")
print(f"  .env exists: {env_path.exists()}")

from dotenv import load_dotenv
load_dotenv(env_path, override=True)

import redis
from redis.cluster import RedisCluster

REDIS_HOST = os.getenv('REDIS_HOST', '')
REDIS_PORT = os.getenv('REDIS_PORT', '10000')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

if not REDIS_HOST or not REDIS_PASSWORD:
    print("[FATAL] REDIS_HOST or REDIS_PASSWORD not found in .env!")
    sys.exit(1)

print(f"\nConnecting to Redis Cluster...")
print(f"  Host: {REDIS_HOST}")
print(f"  Port: {REDIS_PORT}")
print(f"  SSL:  True\n")

def main():
    print("=" * 60)
    print("  CUSTOS -- REDIS RULE RESET")
    print("=" * 60)

    # Use RedisCluster to handle Azure -MOVED redirects natively
    try:
        r = RedisCluster(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            password=REDIS_PASSWORD,
            ssl=True, 
            ssl_cert_reqs=None, 
            decode_responses=True
        )
        pong = r.ping()
        print(f"  Redis PING: {pong}")
    except Exception as e:
        print(f"  [FATAL] Cannot connect to Redis Cluster: {type(e).__name__}: {e}")
        # Fallback to StrictRedis just in case it's not actually a cluster
        try:
            print("  Falling back to StrictRedis...")
            r = redis.StrictRedis(
                host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
                ssl=True, ssl_cert_reqs=None, decode_responses=True
            )
            r.ping()
        except Exception as e2:
            print(f"  [FATAL] Fallback failed: {type(e2).__name__}: {e2}")
            sys.exit(1)

    # ---- SCAN: Find all rule:* keys ----
    print("\n-- Scanning for rule:* keys --")
    rule_keys = []
    
    # RedisCluster scan_iter can sometimes be tricky across nodes, 
    # but redis-py handles it automatically
    try:
        for key in r.scan_iter("rule:*"):
            val = r.get(key)
            print(f"  Found: {key} = {val}")
            rule_keys.append(key)
    except Exception as e:
        print(f"  [!] Scan error: {e}")

    if not rule_keys:
        print("  (no rule:* keys found)")

    # ---- CHECK: restricted_list ----
    print("\n-- Checking restricted_list --")
    try:
        restricted_exists = r.exists("restricted_list")
        if restricted_exists:
            members = r.smembers("restricted_list")
            print(f"  Found: restricted_list = {list(members)}")
        else:
            print("  (restricted_list does not exist)")
    except Exception as e:
        print(f"  [!] Exists error: {e}")
        restricted_exists = False

    total_found = len(rule_keys) + (1 if restricted_exists else 0)
    print(f"\n  Total keys to delete: {total_found}")

    if total_found == 0:
        print("\n" + "=" * 60)
        print("  REDIS IS ALREADY CLEAN -- no rules to delete")
        print("=" * 60)
        return

    # ---- DELETE: rule:* keys ----
    print("\n-- Deleting keys --")
    deleted = 0
    for key in rule_keys:
        try:
            r.delete(key)
            print(f"  Deleted: {key}")
            deleted += 1
        except Exception as e:
            print(f"  [FAILED] {key}: {e}")

    # ---- DELETE: restricted_list ----
    if restricted_exists:
        try:
            r.delete("restricted_list")
            print("  Deleted: restricted_list")
            deleted += 1
        except Exception as e:
            print(f"  [FAILED] restricted_list: {e}")

    # ---- VERIFY: scan again ----
    print("\n-- Verification scan after delete --")
    try:
        remaining_rules = list(r.scan_iter("rule:*"))
        restricted_still = r.exists("restricted_list")
        
        print(f"  Keys remaining with rule:* pattern: {len(remaining_rules)}")
        if remaining_rules:
            for k in remaining_rules:
                print(f"    [!] STILL EXISTS: {k}")
        print(f"  restricted_list exists: {bool(restricted_still)}")

        if len(remaining_rules) == 0 and not restricted_still:
            print("\n  REDIS CLEARED SUCCESSFULLY")
        else:
            print("\n  [WARNING] Some keys were NOT deleted!")
    except Exception as e:
        print(f"  [!] Verify error: {e}")

    print(f"\n  Total deleted: {deleted}")
    print("\n" + "=" * 60)
    print(f"  [OK] REDIS RESET COMPLETE -- {deleted} key(s) deleted")
    print("=" * 60)


if __name__ == "__main__":
    main()
