# train_models.py --- run OFFLINE: python train_models.py
# Produces: models/isolation_forest.pkl, models/autoencoder.pt, models/scaler.pkl, models/ae_threshold.txt
# Also registers model in Azure ML workspace

import json, os, glob, pickle, logging
import pandas as pd, numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import torch, torch.nn as nn
from feature_engineering import load_records, engineer_features, FEATURE_COLS
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('custos.trainer')

class TradeAutoencoder(nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 4))
        self.decoder = nn.Sequential(
            nn.Linear(4, 8), nn.ReLU(),
            nn.Linear(8, 16), nn.ReLU(),
            nn.Linear(16, n_features))

    def forward(self, x): return self.decoder(self.encoder(x))


def train(log_dir='./audit_log_export', output_dir='./models'):
    os.makedirs(output_dir, exist_ok=True)

    records = [json.load(open(p))
               for p in glob.glob(f'{log_dir}/**/*.json', recursive=True)]
    log.info(f'Loaded {len(records)} audit records')

    if len(records) < 10:
        log.error('Need at least 10 records to train. Run simulator.py first.')
        return

    df = engineer_features(load_records(records))
    X = df[FEATURE_COLS].fillna(0.0).values

    # Train scaler
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    with open(f'{output_dir}/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    log.info('Scaler saved.')

    # Train Isolation Forest
    iso = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    iso.fit(Xs)
    with open(f'{output_dir}/isolation_forest.pkl', 'wb') as f:
        pickle.dump(iso, f)
    log.info('Isolation Forest trained.')

    # Train Autoencoder
    n = Xs.shape[1]
    ae = TradeAutoencoder(n)
    opt = torch.optim.Adam(ae.parameters(), lr=1e-3)
    mse = nn.MSELoss()
    t = torch.FloatTensor(Xs)

    for epoch in range(100):
        opt.zero_grad()
        loss = mse(ae(t), t)
        loss.backward()
        opt.step()
        if epoch % 20 == 0:
            log.info(f'Epoch {epoch}: loss={loss.item():.6f}')

    torch.save(ae.state_dict(), f'{output_dir}/autoencoder.pt')

    ae_threshold = float(np.percentile([
        mse(ae(torch.FloatTensor([row])), torch.FloatTensor([row])).item()
        for row in Xs], 98))

    with open(f'{output_dir}/ae_threshold.txt', 'w') as f:
        f.write(str(ae_threshold))

    log.info(f'Done. AE 98th-pct threshold: {ae_threshold:.6f}')

    # ── Register model in Azure ML ──────────────────────────────────────
    try:
        from azure.ai.ml import MLClient
        from azure.ai.ml.entities import Model
        from azure.ai.ml.constants import AssetTypes
        from azure.identity import DefaultAzureCredential

        ml_client = MLClient(
            credential=DefaultAzureCredential(),
            subscription_id=os.environ.get('AZURE_SUBSCRIPTION_ID', ''),
            resource_group_name=os.environ.get('AZURE_RESOURCE_GROUP', 'custos-k-rg'),
            workspace_name=os.environ.get('AML_WORKSPACE_NAME', 'custos-aml')
        )

        model = Model(
            path=output_dir,
            name='custos-anomaly-detector',
            description='IsolationForest + Autoencoder anomaly detection for trade orders',
            type=AssetTypes.CUSTOM_MODEL,
            tags={'module': 'module4', 'project': 'custos'}
        )
        registered = ml_client.models.create_or_update(model)
        log.info(f'Model registered in Azure ML: {registered.name} v{registered.version}')
    except Exception as e:
        log.warning(f'Azure ML registration skipped (run locally without AML): {e}')


if __name__ == '__main__':
    train()
