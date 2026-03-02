# simulator.py — run this to send test orders
import asyncio, json, random
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

CONN_STR = "<YOUR_EVENTHUB_CONNECTION_STRING>"
TICKERS  = ['AAPL', 'GOOG', 'MSFT', 'TSLA', 'RESTRICTED_STOCK']

async def send_orders(n=10):
async with EventHubProducerClient.from_connection_string(CONN_STR, eventhub_name='trade-orders') as p:
for i in range(n):
order = {'id': i, 'ticker': random.choice(TICKERS), 'size': random.randint(100,200000), 'value': random.randint(10000,100000000)}
batch = await p.create_batch()
batch.add(EventData(json.dumps(order)))
await p.send_batch(batch)
print(f'Sent order {i}: {order}')

asyncio.run(send_orders(20))
