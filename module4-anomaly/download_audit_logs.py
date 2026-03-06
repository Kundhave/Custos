import os
from dotenv import load_dotenv
from azure.storage.blob import ContainerClient

load_dotenv()

AUDIT_SAS_URL = os.getenv('AUDIT_LOGS_SAS_URL', '')

OUTPUT_DIR = './audit_log_export'
os.makedirs(OUTPUT_DIR, exist_ok=True)

cc = ContainerClient.from_container_url(AUDIT_SAS_URL)
count = 0
for blob in cc.list_blobs():
    data = cc.download_blob(blob.name).readall()
    local_name = blob.name.replace('/', '_')
    with open(f'{OUTPUT_DIR}/{local_name}', 'wb') as f:
        f.write(data)
    count += 1
    print(f'Downloaded: {blob.name}')

print(f'\nDone. {count} audit logs downloaded to {OUTPUT_DIR}/')
print('Now run: python train_models.py')