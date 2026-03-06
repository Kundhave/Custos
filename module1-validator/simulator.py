import asyncio, json, random, os, time
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from dotenv import load_dotenv

load_dotenv()

CONN_STR = os.getenv('EVENTHUB_CONN')
TICKERS  = ['AAPL', 'GOOG', 'MSFT', 'TSLA', 'RESTRICTED_STOCK']

# ── Guaranteed anomaly patterns injected at the end of every run ──────────────
ANOMALY_ORDERS = [
    # Spoofing pattern — rapid alternating large/tiny orders on same ticker
    {"id": "anomaly-spoof-1", "ticker": "MSFT", "size": 999999, "value": 95000000},
    {"id": "anomaly-spoof-2", "ticker": "MSFT", "size": 1,      "value": 50},
    {"id": "anomaly-spoof-3", "ticker": "MSFT", "size": 999999, "value": 95000000},
    {"id": "anomaly-spoof-4", "ticker": "MSFT", "size": 1,      "value": 50},
    {"id": "anomaly-spoof-5", "ticker": "MSFT", "size": 999999, "value": 95000000},

    # Fat finger — massively oversized order
    {"id": "anomaly-fat-1",   "ticker": "AAPL", "size": 500000, "value": 88000000},

    # Restricted stock attempt
    {"id": "anomaly-rest-1",  "ticker": "RESTRICTED_STOCK", "size": 10000, "value": 500000},
]


async def send_orders(n=20):
    async with EventHubProducerClient.from_connection_string(
            CONN_STR, eventhub_name='trade-orders') as producer:

        # ── Phase 1: Specific test cases ──────────────────────────────
        test_orders = [
            {'id': 'test-1-pass',  'ticker': 'AAPL', 'size': 100,    'value': 15000},
            {'id': 'test-2-limit', 'ticker': 'GOOG', 'size': 200000, 'value': 26000000},
            {'id': 'test-3-rest',  'ticker': 'TSLA', 'size': 100,    'value': 20000},
            {'id': 'test-4-fat',   'ticker': 'MSFT', 'size': 100,    'value': 100000},
            {'id': 'test-5-pass',  'ticker': 'AAPL', 'size': 500,    'value': 75000},
        ]

        print("=" * 60)
        print("  CUSTOS SIMULATOR — Sending trade orders")
        print("=" * 60)
        print()

        print("── Phase 1: Specific test orders ──")
        for order in test_orders:
            batch = await producer.create_batch()
            batch.add(EventData(json.dumps(order)))
            await producer.send_batch(batch)
            print(f'  Sent: {order["id"]:20s}  {order["ticker"]:6s}  ${order["value"]:>12,.0f}')

        # ── Phase 2: Random general orders ────────────────────────────
        print(f"\n── Phase 2: Random orders ({n - 5} orders) ──")
        for i in range(5, n):
            order = {
                'id':     f'rand-{i}',
                'ticker': random.choice(TICKERS),
                'size':   random.randint(100, 200000),
                'value':  random.randint(10000, 10000000)
            }
            batch = await producer.create_batch()
            batch.add(EventData(json.dumps(order)))
            await producer.send_batch(batch)
            print(f'  Sent: {order["id"]:20s}  {order["ticker"]:6s}  ${order["value"]:>12,.0f}')

        # ── Phase 3: Anomaly injection ────────────────────────────────
        print()
        print("=" * 60)
        print("  ⚠ INJECTING ANOMALY PATTERNS...")
        print("=" * 60)
        for order in ANOMALY_ORDERS:
            batch = await producer.create_batch()
            batch.add(EventData(json.dumps(order)))
            await producer.send_batch(batch)
            label = "SPOOF" if "spoof" in order["id"] else "FAT" if "fat" in order["id"] else "RESTRICTED"
            print(f'  [{label:10s}]  {order["id"]:20s}  {order["ticker"]:6s}  ${order["value"]:>12,.0f}  size={order["size"]}')
            await asyncio.sleep(0.1)  # rapid-fire with small delay

        total = len(test_orders) + (n - 5) + len(ANOMALY_ORDERS)
        print()
        print("=" * 60)
        print(f"  ✓ COMPLETE — {total} orders sent ({len(ANOMALY_ORDERS)} anomaly patterns)")
        print("=" * 60)

asyncio.run(send_orders(15))