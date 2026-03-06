import azure.functions as func
import json, os, io, pickle, logging, datetime
import pandas as pd, numpy as np
import torch, torch.nn as nn
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.data.tables import TableServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from feature_engineering import load_records, engineer_features, FEATURE_COLS

log = logging.getLogger('custos.anomaly')

BLOB_CONN       = os.environ['BLOB_CONN_STRING']
AUDIT_SAS       = os.environ['AUDIT_LOGS_SAS_URL']
TABLE_CONN      = os.environ['TABLE_STORAGE_CONN']
SERVICEBUS_CONN = os.environ['SERVICEBUS_CONN']
WINDOW_MIN      = 60  # wider window for manual trigger

class TradeAutoencoder(nn.Module):
    def __init__(self, n):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(n,16), nn.ReLU(), nn.Linear(16,8), nn.ReLU(), nn.Linear(8,4))
        self.decoder = nn.Sequential(nn.Linear(4,8), nn.ReLU(), nn.Linear(8,16), nn.ReLU(), nn.Linear(16,n))
    def forward(self, x): return self.decoder(self.encoder(x))

def load_models():
    bc = BlobServiceClient.from_connection_string(BLOB_CONN)
    def fetch(name): return bc.get_blob_client('ml-models', name).download_blob().readall()
    scaler       = pickle.loads(fetch('scaler.pkl'))
    iso          = pickle.loads(fetch('isolation_forest.pkl'))
    ae_threshold = float(fetch('ae_threshold.txt').decode())
    ae           = TradeAutoencoder(len(FEATURE_COLS))
    ae.load_state_dict(torch.load(io.BytesIO(fetch('autoencoder.pt')), map_location='cpu'))
    ae.eval()
    return scaler, iso, ae, ae_threshold

def fetch_logs(window_min) -> list:
    cc = ContainerClient.from_container_url(AUDIT_SAS)
    now    = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(minutes=window_min)
    records = []
    for blob in cc.list_blobs(name_starts_with=now.strftime('%Y-%m-%d')):
        data = cc.download_blob(blob.name).readall()
        rec  = json.loads(data)
        if rec.get('timestamp', '') >= cutoff.isoformat():
            records.append(rec)
    return records

def score(df, scaler, iso, ae, ae_threshold):
    X  = df[FEATURE_COLS].fillna(0.0).values
    Xs = scaler.transform(X)
    iso_raw   = -iso.decision_function(Xs)
    iso_score = (iso_raw - iso_raw.min()) / (iso_raw.max() - iso_raw.min() + 1e-9)
    t   = torch.FloatTensor(Xs)
    mse = nn.MSELoss(reduction='none')
    with torch.no_grad():
        recon_errors = mse(ae(t), t).mean(dim=1).numpy()
    ae_score = np.clip(recon_errors / ae_threshold, 0, 1)
    combined = (iso_score + ae_score) / 2
    df = df.copy()
    df['iso_score']     = iso_score
    df['ae_score']      = ae_score
    df['anomaly_score'] = combined
    df['is_flagged']    = (combined > 0.65) & (iso_score > 0.5) & (ae_score > 0.5)
    return df

def write_alerts(flagged, scored):
    bc  = BlobServiceClient.from_connection_string(BLOB_CONN)
    now = datetime.datetime.utcnow().isoformat()
    alerts_written = []
    for _, row in flagged.iterrows():
        alert = {
            'alert_generated_at': now,
            'order_id':      row['order_id'],
            'ticker':        row['ticker'],
            'timestamp':     str(row['timestamp']),
            'anomaly_score': round(float(row['anomaly_score']), 4),
            'iso_score':     round(float(row['iso_score']), 4),
            'ae_score':      round(float(row['ae_score']), 4),
            'feature_snapshot': {c: round(float(row[c]), 4) for c in FEATURE_COLS},
            'advisory_only': True
        }
        blob_name = f"{datetime.date.today()}/alert_{row['order_id']}.json"
        bc.get_blob_client('anomaly-alerts', blob_name).upload_blob(json.dumps(alert), overwrite=True)
        alerts_written.append(alert)

    # Table Storage
    table_service = TableServiceClient.from_connection_string(TABLE_CONN)
    table_client  = table_service.get_table_client('anomalyscores')
    try: table_service.create_table('anomalyscores')
    except: pass
    batch = []
    for _, row in scored.iterrows():
        entity = {
            'PartitionKey': str(datetime.date.today()),
            'RowKey':       str(row['order_id']),
            'ticker':       str(row['ticker']),
            'anomaly_score': round(float(row['anomaly_score']), 4),
            'iso_score':    round(float(row['iso_score']), 4),
            'ae_score':     round(float(row['ae_score']), 4),
            'is_flagged':   bool(row['is_flagged']),
            'advisory_only': True
        }
        batch.append(('upsert', entity))
    if batch:
        table_client.submit_transaction(batch)

    # Service Bus
    if not flagged.empty:
        with ServiceBusClient.from_connection_string(SERVICEBUS_CONN) as sb:
            with sb.get_queue_sender('anomaly-alerts') as sender:
                msgs = [ServiceBusMessage(json.dumps({
                    'order_id': row['order_id'],
                    'ticker':   row['ticker'],
                    'anomaly_score': round(float(row['anomaly_score']), 4),
                    'advisory_only': True
                })) for _, row in flagged.iterrows()]
                sender.send_messages(msgs)

    return alerts_written

def main(req: func.HttpRequest) -> func.HttpResponse:
    log.info('=== CUSTOS Manual Trigger ===')
    try:
        records = fetch_logs(WINDOW_MIN)
        if len(records) < 5:
            return func.HttpResponse(
                json.dumps({'status': 'skipped', 'reason': f'Only {len(records)} records in window', 'records_found': len(records)}),
                mimetype='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )
        scaler, iso, ae, ae_threshold = load_models()
        df      = engineer_features(load_records(records))
        scored  = score(df, scaler, iso, ae, ae_threshold)
        flagged = scored[scored['is_flagged']]
        alerts  = write_alerts(flagged, scored)
        return func.HttpResponse(
            json.dumps({
                'status':          'ok',
                'records_scored':  len(scored),
                'alerts_flagged':  len(flagged),
                'alerts':          alerts,
                'advisory_only':   True
            }),
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except Exception as e:
        log.error(f'RunDetector error: {e}')
        return func.HttpResponse(
            json.dumps({'status': 'error', 'message': str(e)}),
            status_code=500,
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )
