# TradeValidator/__init__.py
import azure.functions as func
import json, logging, redis, os

r = redis.StrictRedis.from_url(os.environ["REDIS_CONN"], decode_responses=True)

def main(events: list[func.EventHubEvent]):
for event in events:
order = json.loads(event.get_body().decode('utf-8'))
result = validate_order(order)
logging.info(f"Order {order.get('id')} -> {result}")

def validate_order(order):
ticker   = order.get('ticker', '')
size     = float(order.get('size', 0))
value    = float(order.get('value', 0))

# Fetch rules from Redis (set by FinDistill / Module 2)
fat_finger_mult  = float(r.get('rule:fat_finger_multiplier') or 100)
daily_limit      = float(r.get('rule:daily_limit_usd')     or 50_000_000)
avg_30d          = float(r.get(f'avg30d:{ticker}')         or 1000)
restricted       = r.smembers('restricted_list')

# Check 1: Restricted list
if ticker in restricted:
return {'status': 'REJECTED', 'reason': 'RESTRICTED_TICKER'}

# Check 2: Fat-finger detection
if size > avg_30d * fat_finger_mult:
return {'status': 'FLAGGED', 'reason': 'FAT_FINGER_DETECTED'}

# Check 3: Daily limit
if value > daily_limit:
return {'status': 'REJECTED', 'reason': 'EXCEEDS_DAILY_LIMIT'}

return {'status': 'MATCHED', 'reason': 'ALL_CHECKS_PASSED'}
