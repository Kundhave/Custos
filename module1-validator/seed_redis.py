import os
import redis
from dotenv import load_dotenv

load_dotenv()

redis_conn = os.getenv("REDIS_CONN")

r = redis.StrictRedis.from_url(
    redis_conn,
    decode_responses=True,
    ssl_cert_reqs=None  # ← add this
)

r.set('rule:fat_finger_multiplier', 100)
r.set('rule:daily_limit_usd', 50_000_000)
r.sadd('restricted_list', 'RESTRICTED_STOCK', 'BANNED_CORP')
print('Redis seeded successfully')