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
        logging.info(f"Order {order.get('id')} -> {result['status']} | {result['rejection_reason'] or 'clean'}")
        write_audit_log(order, result)


def validate_order(order):
    ticker = order.get('ticker', '')
    size   = float(order.get('size', 0))
    value  = float(order.get('value', 0))

    fat_finger_mult = float(r.get('rule:fat_finger_multiplier') or 100)
    daily_limit     = float(r.get('rule:daily_limit_usd') or 50_000_000)
    max_order_size  = float(r.get('rule:max_order_size') or 999_999_999)
    min_equity      = float(r.get('rule:min_account_equity') or 0)
    max_day_trades  = float(r.get('rule:max_day_trades') or 999)
    avg_30d         = float(r.get(f'avg30d:{ticker}') or 1000)
    restricted      = r.smembers('restricted_list')

    # Check restricted list
    if ticker in restricted:
        return {
            'status': 'REJECTED',
            'reason': 'RESTRICTED_TICKER',
            'rejection_reason': f"restricted_list — ticker {ticker} is on restricted list",
        }

    # Check daily limit
    if value > daily_limit:
        return {
            'status': 'REJECTED',
            'reason': 'EXCEEDS_DAILY_LIMIT',
            'rejection_reason': f"rule:daily_limit_usd violated — order value ${value:,.0f} exceeds limit ${daily_limit:,.0f}",
        }

    # Check fat finger
    if size > avg_30d * fat_finger_mult:
        return {
            'status': 'REJECTED',
            'reason': 'FAT_FINGER_DETECTED',
            'rejection_reason': f"rule:fat_finger_multiplier violated — size {size:,.0f} > avg {avg_30d:,.0f} × {fat_finger_mult}x",
        }

    # Check max order size
    if size > max_order_size:
        return {
            'status': 'REJECTED',
            'reason': 'EXCEEDS_MAX_ORDER_SIZE',
            'rejection_reason': f"rule:max_order_size violated — size {size:,.0f} exceeds limit {max_order_size:,.0f}",
        }

    # All checks passed
    return {
        'status': 'APPROVED',
        'reason': 'ALL_CHECKS_PASSED',
        'rejection_reason': None,
    }


def write_audit_log(order, result):
    record = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'order_id': str(order.get('id')),
        'ticker': order.get('ticker'),
        'size': order.get('size'),
        'value': order.get('value'),
        'decision': {
            'status': result['status'],
            'reason': result['reason'],
        },
        'rejection_reason': result['rejection_reason'],
    }
    blob_name = f"{datetime.date.today()}/{uuid.uuid4()}.json"
    bc = BlobServiceClient.from_connection_string(BLOB_CONN)
    bc.get_blob_client('audit-logs', blob_name).upload_blob(json.dumps(record))