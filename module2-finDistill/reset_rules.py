"""
reset_rules.py — CUSTOS Demo Reset Utility
Clears all compliance rules from Azure Managed Redis (cluster mode).
Run from module2-finDistill/ directory:  python reset_rules.py
"""
import os
import sys
import redis
from redis.cluster import RedisCluster
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', '10000'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

if not REDIS_HOST or not REDIS_PASSWORD:
    print("ERROR: REDIS_HOST and REDIS_PASSWORD must be set in .env")
    print("Expected .env file in this directory with:")
    print("  REDIS_HOST=custos-redis-K.centralindia.redis.azure.net")
    print("  REDIS_PORT=10000")
    print("  REDIS_PASSWORD=<your-password>")
    sys.exit(1)


def get_redis_client():
    """Try cluster mode first (Azure Managed Redis), fall back to standalone."""
    try:
        rc = RedisCluster(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            ssl=True,
            ssl_cert_reqs=None,
            decode_responses=True,
        )
        rc.ping()
        return rc, "cluster"
    except Exception:
        r = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            ssl=True,
            ssl_cert_reqs=None,
            decode_responses=True,
        )
        r.ping()
        return r, "standalone"


def reset_rules():
    print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")

    try:
        r, mode = get_redis_client()
        print(f"Connected successfully ({mode} mode).\n")
    except Exception as e:
        print(f"ERROR: Cannot connect to Redis: {e}")
        sys.exit(1)

    deleted_count = 0

    # 1. Delete all rule:* keys
    for key in r.scan_iter("rule:*"):
        r.delete(key)
        print(f"  Deleted: {key}")
        deleted_count += 1

    # 2. Delete restricted_list set
    try:
        if r.exists("restricted_list"):
            r.delete("restricted_list")
            print("  Deleted: restricted_list")
            deleted_count += 1
    except Exception as e:
        print(f"  Warning: Could not check/delete restricted_list: {e}")

    print(f"\n{'='*40}")
    print(f"Reset complete! Deleted {deleted_count} key(s) from Redis.")
    print(f"{'='*40}")


if __name__ == "__main__":
    reset_rules()
