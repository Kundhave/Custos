# feature_engineering.py
import pandas as pd
import numpy as np

def load_records(records: list) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['status'] = df['decision'].apply(lambda d: d.get('status', 'UNKNOWN') if isinstance(d, dict) else 'UNKNOWN')
    df['size'] = df['size'].astype(float)
    df['value'] = df['value'].astype(float)
    return df.sort_values('timestamp').reset_index(drop=True)

def compute_ticker_baselines(df: pd.DataFrame) -> pd.DataFrame:
    stats = df.groupby('ticker')['size'].agg(
        ticker_size_mean='mean',
        ticker_size_std='std'
    ).reset_index()
    stats['ticker_size_std'] = stats['ticker_size_std'].fillna(1.0)
    return df.merge(stats, on='ticker', how='left')

def compute_session_features(df: pd.DataFrame) -> pd.DataFrame:
    df['time_bucket'] = df['timestamp'].dt.floor('30min')
    df['session_id'] = df['ticker'] + '_' + df['time_bucket'].astype(str)
    session = df.groupby('session_id').agg(
        session_order_count=('order_id', 'count'),
        session_total_value=('value', 'sum'),
        session_reject_count=('status', lambda s: (s == 'REJECTED').sum())
    ).reset_index()
    session['rejection_rate_session'] = (
        session['session_reject_count'] / session['session_order_count'].clip(lower=1))
    return df.merge(session, on='session_id', how='left')

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_ticker_baselines(df)
    df = compute_session_features(df)
    df['order_size_zscore'] = (
        (df['size'] - df['ticker_size_mean']) / df['ticker_size_std'].clip(lower=0.001))
    df['order_value_zscore'] = (
        (df['value'] - df['value'].mean()) / max(df['value'].std(), 0.001))
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['time_since_last_order_sec'] = (
    df.groupby('session_id')['timestamp']
    .diff().dt.total_seconds().fillna(300).clip(0, 300))
    df['value_concentration'] = df['value'] / df['session_total_value'].clip(lower=1)
    for col in ['order_size_zscore', 'order_value_zscore']:
        df[col] = df[col].clip(-10, 10)
    return df

FEATURE_COLS = [
    'order_size_zscore', 'order_value_zscore', 'hour_of_day',
    'time_since_last_order_sec', 'rejection_rate_session',
    'value_concentration', 'session_order_count',
]