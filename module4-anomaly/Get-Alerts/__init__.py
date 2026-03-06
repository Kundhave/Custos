# GetAlerts/__init__.py
# Serves anomaly alerts to the React dashboard
# Reads from BOTH Blob Storage (alerts) and Table Storage (full score history)

import azure.functions as func
import json, os, datetime
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    blob_conn  = os.environ['BLOB_CONN_STRING']
    table_conn = os.environ['TABLE_STORAGE_CONN']
    source     = req.params.get('source', 'blob')  # ?source=blob or ?source=table

    if source == 'table':
        # Return full score history from Table Storage
        table_service = TableServiceClient.from_connection_string(table_conn)
        table_client  = table_service.get_table_client('anomalyscores')
        today  = str(datetime.date.today())
        entities = list(table_client.query_entities(f"PartitionKey eq '{today}'"))
        scores = [dict(e) for e in entities]
        scores.sort(key=lambda x: x.get('anomaly_score', 0), reverse=True)
        return func.HttpResponse(
            json.dumps({'scores': scores, 'source': 'table_storage'}),
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )

    else:
        # Return flagged alerts from Blob Storage
        bc    = BlobServiceClient.from_connection_string(blob_conn)
        today = datetime.date.today().isoformat()
        cc    = bc.get_container_client('anomaly-alerts')
        alerts = []
        for blob in cc.list_blobs(name_starts_with=today):
            data = cc.download_blob(blob.name).readall()
            alerts.append(json.loads(data))
        alerts.sort(key=lambda a: a['anomaly_score'], reverse=True)
        return func.HttpResponse(
            json.dumps({'alerts': alerts, 'source': 'blob_storage'}),
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )
