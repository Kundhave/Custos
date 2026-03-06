import asyncio, json, uuid, os
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from dotenv import load_dotenv

load_dotenv()

CONN_STR = os.getenv('EVENTHUB_CONN', '')

async def inject():
    async with EventHubProducerClient.from_connection_string(
            CONN_STR, eventhub_name='trade-orders') as p:

        print('Injecting spoofing pattern (50 rapid alternating orders)...')
        for i in range(50):
            order = {
                'id':     str(uuid.uuid4()),
                'ticker': 'TESTSTOCK',
                'size':   999999 if i % 2 == 0 else 1,
                'value':  99000000 if i % 2 == 0 else 100
            }
            batch = await p.create_batch()
            batch.add(EventData(json.dumps(order)))
            await p.send_batch(batch)
            print(f'Injected order {i}: {order}')

if __name__ == '__main__':
    asyncio.run(inject())