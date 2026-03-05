import redis, os
from dotenv import load_dotenv

load_dotenv()

r = redis.StrictRedis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT', 10000)),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=True,
    ssl_cert_reqs=None,
    decode_responses=True
)

r.set('rule:fat_finger_multiplier', 100)
r.set('rule:daily_limit_usd', 50000000)
r.sadd('restricted_list', 'RESTRICTED_STOCK', 'BANNED_CORP')

print('Redis seeded successfully')
