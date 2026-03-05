import asyncio, json, random, os
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from dotenv import load_dotenv

load_dotenv()

CONN_STR = os.getenv('EVENTHUB_CONN')
TICKERS  = ['AAPL', 'GOOG', 'MSFT', 'TSLA', 'RESTRICTED_STOCK']

async def send_orders(n=20):
    async with EventHubProducerClient.from_connection_string(
            CONN_STR, eventhub_name='trade-orders') as producer:
        for i in range(n):
            order = {
                'id':     i,
                'ticker': random.choice(TICKERS),
                'size':   random.randint(100, 200000),
                'value':  random.randint(10000, 100000000)
            }
            batch = await producer.create_batch()
            batch.add(EventData(json.dumps(order)))
            await producer.send_batch(batch)
            print(f'Sent order {i}: {order}')

asyncio.run(send_orders(20))