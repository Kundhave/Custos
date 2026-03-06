import os, json
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from datetime import date

load_dotenv()

bc = BlobServiceClient.from_connection_string(os.environ['BLOB_CONN_STRING'])
cc = bc.get_container_client('audit-logs')

blobs = list(cc.list_blobs(name_starts_with=str(date.today())))
print(f"Total audit logs today: {len(blobs)}\n")

for b in blobs[-10:]:
    data = json.loads(cc.download_blob(b.name).readall())
    ticker   = data.get('ticker', '?')
    status   = data.get('decision', {}).get('status', '?')
    reason   = data.get('decision', {}).get('reason', '')
    value    = data.get('value', 0)
    print(f"{ticker:20} {status:10} value={value:>12,.0f}  {reason}")
