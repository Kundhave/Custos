import azure.functions as func
import json, logging, redis, os, datetime, uuid
from azure.storage.blob import BlobServiceClient
from typing import List
r = redis.StrictRedis.from_url(
    os.environ['REDIS_CONN'], decode_responses=True, ssl_cert_reqs=None)

BLOB_CONN = os.environ['BLOB_CONN_STRING']

def main(events: List[func.EventHubEvent]):
    for event in events:
        order = json.loads(event.get_body().decode('utf-8'))
        result = validate_order(order)
        logging.info(f"Order {order.get('id')} -> {result}")
        write_audit_log(order, result)

def validate_order(order):
    ticker = order.get('ticker', '')
    size   = float(order.get('size', 0))
    value  = float(order.get('value', 0))
    fat_finger_mult = float(r.get('rule:fat_finger_multiplier') or 100)
    daily_limit     = float(r.get('rule:daily_limit_usd') or 50_000_000)
    avg_30d         = float(r.get(f'avg30d:{ticker}') or 1000)
    restricted      = r.smembers('restricted_list')
    if ticker in restricted:
        return {'status': 'REJECTED', 'reason': 'RESTRICTED_TICKER'}
    if size > avg_30d * fat_finger_mult:
        return {'status': 'FLAGGED', 'reason': 'FAT_FINGER_DETECTED'}
    if value > daily_limit:
        return {'status': 'REJECTED', 'reason': 'EXCEEDS_DAILY_LIMIT'}
    return {'status': 'MATCHED', 'reason': 'ALL_CHECKS_PASSED'}

def write_audit_log(order, result):
    record = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'order_id': str(order.get('id')),
        'ticker': order.get('ticker'),
        'size': order.get('size'),
        'value': order.get('value'),
        'decision': result
    }
    blob_name = f"{datetime.date.today()}/{uuid.uuid4()}.json"
    bc = BlobServiceClient.from_connection_string(BLOB_CONN)
    bc.get_blob_client('audit-logs', blob_name).upload_blob(json.dumps(record))