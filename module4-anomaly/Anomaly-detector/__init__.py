# AnomalyDetector/__init__.py
# ADVISORY ONLY --- reads audit logs, scores for anomalies, writes alerts
# Uses: Azure ML (model registry), Azure Service Bus (alerts), Azure Table Storage (history)

import azure.functions as func
import json, os, io, pickle, logging, datetime
import pandas as pd, numpy as np
import torch, torch.nn as nn
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.data.tables import TableServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.monitor.opentelemetry import configure_azure_monitor
from feature_engineering import load_records, engineer_features, FEATURE_COLS

log = logging.getLogger('custos.anomaly')

BLOB_CONN       = os.environ['BLOB_CONN_STRING']
AUDIT_SAS       = os.environ['AUDIT_LOGS_SAS_URL']
TABLE_CONN      = os.environ['TABLE_STORAGE_CONN']
SERVICEBUS_CONN = os.environ['SERVICEBUS_CONN']
WINDOW_MIN      = 15


class TradeAutoencoder(nn.Module):
    def __init__(self, n):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n, 16), nn.ReLU(), nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 4))
        self.decoder = nn.Sequential(
            nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, n))

    def forward(self, x): return self.decoder(self.encoder(x))


def load_models():
    """Load trained models from Azure Blob (ml-models container)."""
    bc = BlobServiceClient.from_connection_string(BLOB_CONN)

    def fetch(name):
        return bc.get_blob_client('ml-models', name).download_blob().readall()

    scaler        = pickle.loads(fetch('scaler.pkl'))
    iso           = pickle.loads(fetch('isolation_forest.pkl'))
    ae_threshold  = float(fetch('ae_threshold.txt').decode())
    ae            = TradeAutoencoder(len(FEATURE_COLS))
    ae.load_state_dict(torch.load(io.BytesIO(fetch('autoencoder.pt')), map_location='cpu'))
    ae.eval()
    return scaler, iso, ae, ae_threshold


def fetch_recent_logs() -> list:
    """Read recent audit logs from blob storage via SAS token."""
    cc = ContainerClient.from_container_url(AUDIT_SAS)
    now    = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(minutes=WINDOW_MIN)
    records = []
    for blob in cc.list_blobs(name_starts_with=now.strftime('%Y-%m-%d')):
        data = cc.download_blob(blob.name).readall()
        rec  = json.loads(data)
        if rec.get('timestamp', '') >= cutoff.isoformat():
            records.append(rec)
    log.info(f'Fetched {len(records)} records for scoring window')
    return records


def score(df, scaler, iso, ae, ae_threshold):
    """Run IsolationForest + Autoencoder scoring."""
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


def write_alerts_to_blob(flagged: pd.DataFrame):
    """Write alert JSON files to anomaly-alerts blob container."""
    bc  = BlobServiceClient.from_connection_string(BLOB_CONN)
    now = datetime.datetime.utcnow().isoformat()
    for _, row in flagged.iterrows():
        alert = {
            'alert_generated_at': now,
            'order_id':           row['order_id'],
            'ticker':             row['ticker'],
            'timestamp':          str(row['timestamp']),
            'anomaly_score':      round(float(row['anomaly_score']), 4),
            'iso_score':          round(float(row['iso_score']), 4),
            'ae_score':           round(float(row['ae_score']), 4),
            'feature_snapshot':   {c: round(float(row[c]), 4) for c in FEATURE_COLS},
            'advisory_only':      True
        }
        blob_name = f"{datetime.date.today()}/alert_{row['order_id']}.json"
        bc.get_blob_client('anomaly-alerts', blob_name).upload_blob(
            json.dumps(alert), overwrite=True)
    log.info(f'{len(flagged)} anomaly alerts written to blob.')


def write_scores_to_table(scored: pd.DataFrame):
    """Store ALL scored records in Azure Table Storage for history/analytics."""
    table_service = TableServiceClient.from_connection_string(TABLE_CONN)
    table_client  = table_service.get_table_client('anomalyscores')

    try:
        table_service.create_table('anomalyscores')
    except Exception:
        pass

    entities = []
    for _, row in scored.iterrows():
        entity = {
            "PartitionKey": str(datetime.date.today()),
            # ✅ Already fixed by you — unique per record
            "RowKey": f"{row['ticker']}_{row['order_id']}",
            'ticker':        str(row['ticker']),
            'anomaly_score': round(float(row['anomaly_score']), 4),
            'iso_score':     round(float(row['iso_score']), 4),
            'ae_score':      round(float(row['ae_score']), 4),
            'is_flagged':    bool(row['is_flagged']),
            'advisory_only': True
        }
        entities.append(('upsert', entity))

    # ✅ Chunk into batches of 100 (Azure Table Storage hard limit per transaction)
    BATCH_SIZE = 100
    for i in range(0, len(entities), BATCH_SIZE):
        chunk = entities[i:i + BATCH_SIZE]
        table_client.submit_transaction(chunk)

    log.info(f'{len(entities)} score records written to Table Storage.')

def send_alerts_to_servicebus(flagged: pd.DataFrame):
    """Send high-severity alerts to Azure Service Bus for downstream consumers."""
    if flagged.empty:
        return

    with ServiceBusClient.from_connection_string(SERVICEBUS_CONN) as sb_client:
        with sb_client.get_queue_sender('anomaly-alerts') as sender:
            messages = []
            for _, row in flagged.iterrows():
                payload = json.dumps({
                    'order_id':      row['order_id'],
                    'ticker':        row['ticker'],
                    'anomaly_score': round(float(row['anomaly_score']), 4),
                    'advisory_only': True,
                    'generated_at':  datetime.datetime.utcnow().isoformat()
                })
                messages.append(ServiceBusMessage(payload))
            sender.send_messages(messages)
    log.info(f'{len(flagged)} alerts sent to Service Bus queue.')


def main(timer: func.TimerRequest) -> None:
    log.info('=== CUSTOS Anomaly Detector - Shadow Mode ===')

    records = fetch_recent_logs()
    if len(records) < 5:
        log.info('Insufficient records for scoring this window. Skipping.')
        return

    scaler, iso, ae, ae_threshold = load_models()
    df     = engineer_features(load_records(records))
    scored = score(df, scaler, iso, ae, ae_threshold)
    flagged = scored[scored['is_flagged']]

    log.info(f'Scored {len(scored)} records. {len(flagged)} flagged as anomalous.')

    # Write to all 3 destinations
    write_alerts_to_blob(flagged)           # Blob Storage
    write_scores_to_table(scored)           # Table Storage (NEW)
    send_alerts_to_servicebus(flagged)      # Service Bus (NEW)
