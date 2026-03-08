# CUSTOS
### Pre-Trade Risk & Regulatory Intelligence Platform

> *Real-time trade validation, AI-powered regulatory rule extraction, immutable audit logging, and ML anomaly detection — fully deployed on Microsoft Azure.*

![Platform](https://img.shields.io/badge/Platform-Microsoft%20Azure-0078D4?style=flat&logo=microsoftazure)
![Frontend](https://img.shields.io/badge/Frontend-Azure%20Static%20Web%20Apps-0078D4?style=flat&logo=microsoftazure)
![Backend](https://img.shields.io/badge/Backend-Azure%20Functions%20Python%203.12-0062AD?style=flat&logo=azurefunctions)
![ML](https://img.shields.io/badge/ML-IsolationForest%20%2B%20PyTorch-EE4C2C?style=flat&logo=pytorch)
![LLM](https://img.shields.io/badge/LLM-Groq%20API-F55036?style=flat)
![Compliance](https://img.shields.io/badge/Compliance-MiFID%20II%20%7C%20SEC%20%7C%20FINRA-green?style=flat)

---

## Overview

CUSTOS is a cloud-native RegTech (Regulatory Technology) platform that enforces financial compliance at the point of trade execution. It solves a real problem in financial markets: how do you ensure every trade order is validated against current regulations, every decision is permanently recorded, and suspicious trading patterns are caught — all in real time, at scale?

The platform operates across four tightly integrated modules:

1. **Trade Validator** — validates every incoming trade order against Redis-stored rules in milliseconds
2. **FinDistill** — extracts enforceable trading rules directly from regulatory PDF documents using an LLM
3. **Audit Log** — ensures every trade decision is permanently tamper-proof using WORM immutability
4. **Anomaly Detection** — continuously scores trade patterns using two ML models to flag suspicious behavior

All four modules were fully deployed on Microsoft Azure with a live React dashboard hosted on Azure Static Web Apps.

---

## Live Deployment

> **Note:** Azure resources have been deprovisioned after project completion due to student subscription cost management. All infrastructure was fully operational during development and demonstration.
Link: https://delightful-coast-002ae4800.6.azurestaticapps.net
<img width="906" height="442" alt="image" src="https://github.com/user-attachments/assets/224d0b1b-e70e-4e37-bff9-e1f8f9212561" />

<img width="891" height="375" alt="image" src="https://github.com/user-attachments/assets/317c2531-b53a-4998-a457-f2d4417f1e7f" />

### Deployed Resources (deprovisioned post-demo)

| Resource | Type | Region | Purpose |
|---|---|---|---|
| `custos-k-rg` | Resource Group | Central India | Container for all project resources |
| `custos-validator-fn-K` | Azure Function App | Central India | Module 1 — Trade Validator |
| `custos-finDistill-fn` | Azure Function App | Central India | Module 2 — FinDistill |
| `custos-anomaly-fn` | Azure Function App | Central India | Module 4 — Anomaly Detector |
| `custos-eventhubs-k` | Azure Event Hubs | Central India | Trade order ingestion pipeline |
| `custos-redis-K` | Azure Managed Redis | Central India | Real-time rule storage |
| `custosblob2` | Azure Storage Account | Central India | Audit logs, ML models, anomaly alerts |
| `custos-servicebus-k` | Azure Service Bus | Central India | Real-time anomaly alert queue |
| Azure AI Search | Cognitive Search | Central India | Regulatory PDF indexing |
| Azure Static Web Apps | Static Web App | Global CDN | React dashboard — GitHub Actions CI/CD |

### Live Endpoint URLs (during deployment)

```
Dashboard:        https://delightful-coast-002ae4800.6.azurestaticapps.net
Validator API:    https://custos-validator-fn-k-fqf4fhf4fqaqd8dq.centralindia-01.azurewebsites.net
FinDistill API:   https://custos-findistill-fn-c8atg8edhagncaf7.centralindia-01.azurewebsites.net
Anomaly API:      https://custos-anomaly-fn-aac2a0hsakdwd5gr.centralindia-01.azurewebsites.net
```

### CI/CD Pipeline

The React frontend was deployed via **GitHub Actions** with automatic deployment to Azure Static Web Apps on every push to `main`. The workflow was provisioned by Azure and stored in `.github/workflows/azure-static-web-apps.yml`.

Azure Function Apps were deployed using Azure Functions Core Tools:

```bash
func azure functionapp publish custos-validator-fn-K
func azure functionapp publish custos-finDistill-fn
func azure functionapp publish custos-anomaly-fn
```

---

## Architecture

```
                    ┌──────────────────────────────────────────────────────────────┐
                    │                     CUSTOS PLATFORM                         │
                    │                                                              │
                    │   ┌─────────────┐    ┌──────────────────┐                  │
  simulator.py ────▶│   │ EVENT HUBS  │───▶│ TRADE VALIDATOR  │                  │
  (trade orders)    │   │ trade-orders│    │ Azure Function   │                  │
                    │   └─────────────┘    └────────┬─────────┘                  │
                    │                               │                             │
                    │   ┌─────────────┐             │ reads rules                │
                    │   │    REDIS    │◀────────────┘                            │
                    │   │ trading rules│             │ writes decision            │
                    │   └──────┬──────┘             ▼                            │
                    │          │             ┌──────────────┐                    │
  Regulatory PDFs ─▶│   ┌──────┴──────┐     │  BLOB STORAGE│                   │
                    │   │  FINDISTILL  │     │  audit-logs  │◀── WORM Policy    │
                    │   │  AI Search   │     │  (immutable) │    Module 3        │
                    │   │  + Groq LLM  │     └──────┬───────┘                   │
                    │   └─────────────┘             │ read-only SAS token        │
                    │                               ▼                            │
                    │                    ┌─────────────────────┐                 │
                    │                    │  ANOMALY DETECTOR   │                 │
                    │                    │  Timer: every 1 min │                 │
                    │                    └──────────┬──────────┘                 │
                    │                               │                            │
                    │              ┌────────────────┼────────────────┐           │
                    │              ▼                ▼                ▼           │
                    │        Blob Storage     Table Storage    Service Bus       │
                    │        anomaly-alerts   anomalyscores    anomaly-alerts    │
                    │        (audit trail)    (score history)  (real-time alerts)│
                    └──────────────────────────────────────────────────────────┘
                                              │
                                    ┌─────────▼──────────┐
                                    │  REACT DASHBOARD   │
                                    │  Azure Static      │
                                    │  Web Apps          │
                                    │  GitHub Actions CI │
                                    └────────────────────┘
```

---

## Module Breakdown

### Module 1 — Trade Validator

**What it does:** Validates every incoming trade order against regulatory rules in real time and writes a permanent audit record of every decision.

**Flow:**
```
simulator.py → Event Hubs → TradeValidator Function
→ Read rules from Redis → APPROVED or REJECTED
→ Write audit log to Blob Storage (audit-logs/{date}/{order_id}.json)
```

**Rules enforced:**
- `rule:daily_limit_usd` — maximum order value in USD
- `rule:fat_finger_multiplier` — flags orders N times larger than session average
- `rule:min_account_equity` — minimum account equity required
- `rule:max_day_trades` — maximum day trades in 5 business days
- `restricted_list` — blocked ticker symbols

**Audit log format:**
```json
{
  "order_id": "rand-12",
  "ticker": "MSFT",
  "order_size": 111232,
  "order_value": 2898803,
  "status": "REJECTED",
  "rejection_reason": "rule:fat_finger_multiplier violated — size 111,232 > avg 1,000 × 100x",
  "timestamp": "2026-03-07T17:30:41Z"
}
```

**Services:** Azure Event Hubs · Azure Managed Redis · Azure Blob Storage · Azure Functions

---

### Module 2 — FinDistill: Regulatory Intelligence

**What it does:** Extracts enforceable trading rules from regulatory PDF documents using AI and pushes approved rules to Redis where Module 1 enforces them immediately on the next trade.

**Flow:**
```
Upload PDF → PDFIngestion Function
→ Index pages into Azure AI Search
→ Extract full text → Send to Groq LLM
→ Structured rules with source quotes returned
→ Display on dashboard for review
→ Approve → Push to Redis → Module 1 enforces immediately
```

**Groq extraction output example:**
```json
[
  {
    "key": "rule:min_account_equity",
    "value": 25000,
    "source_quote": "The minimum equity requirement for a customer designated as a pattern day trader is $25,000"
  },
  {
    "key": "rule:max_day_trades",
    "value": 4,
    "source_quote": "FINRA rules define a pattern day trader as any customer who executes four or more day trades within five business days"
  }
]
```

**Duplicate rule handling:** If the same rule key appears twice with different values (e.g. from two PDFs), the most recently approved value wins and the older one is discarded from Redis.

**Services:** Azure Functions · Azure AI Search · Groq API · Azure Managed Redis

---

### Module 3 — Immutable Audit Log

**What it does:** Enforces WORM (Write Once Read Many) immutability on all audit logs. No record can be modified or deleted once written — not even by the storage account owner.

**Configuration:**
- Policy type: Time-based retention
- Retention period: 7 days (test mode, unlocked)
- Production equivalent: 2,557 days (7 years) per MiFID II
- SAS token: read-only (`rltfx` permissions) issued to Module 4

**Compliance:**
- **MiFID II Article 17** — algorithmic trading audit trail, 7-year retention
- **SEC Rule 17a-4** — tamper-proof non-rewritable electronic records

**Services:** Azure Blob Storage WORM immutability policy (no additional service)

---

### Module 4 — Anomaly Detection

**What it does:** Runs in shadow mode — continuously monitors all validated trade patterns, scores each trade through two ML models, and publishes anomaly alerts to three destinations simultaneously.

**Trigger mechanisms:**
- **Timer trigger** — automatic, every 1 minute, processes last 15 minutes of audit logs
- **HTTP trigger (RunDetector)** — manual button on dashboard, processes last 60 minutes

**Feature engineering — 7 features per trade:**

| Feature | What it detects |
|---|---|
| `order_size_zscore` | Abnormal order size vs ticker historical average |
| `order_value_zscore` | Abnormal order value vs ticker historical average |
| `hour_of_day` | After-hours and off-market trading |
| `time_since_last_order_sec` | Rapid-fire spoofing patterns |
| `rejection_rate_session` | Repeated rule violation attempts (manipulation probing) |
| `value_concentration` | Single order dominating entire session value (layering) |
| `session_order_count` | Abnormally high order frequency |

**ML Models:**

*IsolationForest (sklearn)*
- 200 trees, contamination=0.02
- Anomalies require fewer splits to isolate from the dense cluster of normal data
- Normalised score: 0 (normal) → 1 (anomalous)

*PyTorch Autoencoder*
- Architecture: `Input(7) → Linear(16) → ReLU → Linear(8) → ReLU → Linear(4) → Linear(8) → ReLU → Linear(16) → ReLU → Output(7)`
- Trained to reconstruct normal patterns — high reconstruction error = anomaly
- Threshold: 98th percentile MSE from training data

*Combined flagging logic:*
```python
combined_score = (iso_score + ae_score) / 2
is_flagged = combined_score > 0.65 AND iso_score > 0.5 AND ae_score > 0.5
# Both models must independently agree — minimises false positives
```

**Three output destinations:**

| Destination | What gets written | Purpose |
|---|---|---|
| `custosblob2/anomaly-alerts/` | Full alert JSON per flagged trade | Immutable compliance record |
| `anomalyscores` Table Storage | Every scored trade (flagged + clean) | Score history for dashboard |
| `custos-servicebus-k/anomaly-alerts` | Only flagged alerts as queue messages | Real-time downstream alerting |

**Shadow mode:** All alerts carry `advisory_only: true`. The system monitors without blocking execution, satisfying MiFID II Article 17 and SEC Rule 15c3-5 for pre-approved algorithmic risk systems.

**Services:** Azure Functions · Azure Blob Storage · Azure Table Storage · Azure Service Bus

---

## Services Summary

| # | Service | Module(s) | Role |
|---|---|---|---|
| 1 | Azure Event Hubs | 1 | Trade order ingestion — `trade-orders` hub |
| 2 | Azure Managed Redis | 1, 2 | Real-time rule storage, validation lookup, rule updates |
| 3 | Azure Blob Storage | 1, 3, 4 | Audit logs (WORM), ML model files, anomaly alert records |
| 4 | Azure Functions | 1, 2, 4 | All backend processing — 3 apps, 7 total functions |
| 5 | Azure AI Search | 2 | Regulatory PDF indexing and text retrieval |
| 6 | Azure Table Storage | 4 | Complete anomaly score history for every trade |
| 7 | Azure Service Bus | 4 | Real-time anomaly alert notification queue |
| 8 | Azure Static Web Apps | All | React dashboard hosting — GitHub Actions CI/CD |
| 9 | Groq API (external) | 2 | LLM rule extraction from regulatory document text |

**9 services across 4 modules on a single Azure student subscription.**

---

## Dashboard

React single-page application hosted on **Azure Static Web Apps** with automatic deployment via **GitHub Actions** on every push to `main`. Dark terminal aesthetic with Orbitron, Rajdhani, and Share Tech Mono fonts.

**Trade Validator Tab** — Audit log table with ORDER ID, TICKER, VALUE, STATUS badge, and REASON column showing exact rule violation details. Real-time activity feed (newest-first). Summary banner with approval rate and most violated rule.

**FinDistill Tab** — PDF upload with ingest button. Proposed rules appear immediately post-ingestion with source quotes from the document proving where each rule came from. Approve & Push sends to Redis. Active Redis Rules panel shows all currently enforced rules.

**Audit Log Tab** — WORM policy details, SAS token configuration, retention period, and compliance citations for auditor review.

**Anomaly Detection Tab** — Manual RUN DETECTOR NOW trigger with live result. Flagged alerts with feature snapshot grids. Score history table. ML models panel. Auto-refreshes every 60 seconds.

---

## Demo Flow

```bash
# STEP 1 — Full reset for clean demo
python reset_demo.py
# Clears: Redis rules, today's Table Storage, today's anomaly alerts
# Preserves: audit logs (WORM protected), ML models

# STEP 2 — Run simulator with no rules
cd module1-validator
python simulator.py
# Expected: all orders APPROVED — no rules to block them

# STEP 3 — Load rules via Module 2 dashboard
# Upload daytrading.pdf → INGEST → rules appear with source quotes
# Click APPROVE & PUSH TO REDIS
# Repeat for additional PDFs

# STEP 4 — Run simulator again with rules active
python simulator.py
# Expected: orders REJECTED with specific rule violation reasons shown

# STEP 5 — Trigger anomaly detection
# Dashboard → Anomaly Detection tab → ⚡ RUN DETECTOR NOW
# Spoofing patterns from simulator flagged automatically
```

---

## Regulatory Compliance

| Regulation | Requirement | Implementation |
|---|---|---|
| MiFID II Article 17 | Algorithmic trading controls + 7-year audit trail | WORM immutable audit logs + shadow mode detection |
| SEC Rule 17a-4 | Tamper-proof non-rewritable record keeping | Blob Storage time-based retention policy |
| SEC Rule 15c3-5 | Pre-trade risk controls (Market Access Rule) | Redis rule validation on every order pre-execution |
| FINRA Rule 3110 | Supervisory systems for member trading activity | Dual-model anomaly detection with advisory alerts |

---

## Tech Stack

**Backend:** Python 3.12 · Azure Functions V1 · scikit-learn · PyTorch · azure-eventhub (AmqpOverWebsocket) · azure-storage-blob · azure-data-tables · azure-servicebus · redis-py (SSL port 10000) · groq · pdfplumber

**Frontend:** React 18 · Tailwind CSS · Orbitron + Rajdhani + Share Tech Mono · Dark terminal theme

**Infrastructure:** Microsoft Azure Central India · GitHub Actions CI/CD · Azure Functions Core Tools

---

## Project Structure

```
Custos-Pre-Trade-Risk-Regulatory-Intelligence-Platform/
├── module1-validator/
│   ├── TradeValidator/          # Event Hub trigger → Redis validation → audit log
│   ├── simulator.py             # Trade order generator + anomaly pattern injection
│   ├── seed_redis.py            # Seed initial Redis rules
│   └── .env
├── module2-finDistill/
│   ├── PDFIngestion/            # PDF upload + AI Search indexing + Groq extraction
│   ├── ApproveRules/            # Push approved rules to Redis
│   ├── RuleExtractor/           # Backup extraction endpoint
│   ├── regulatory_pdfs/         # Source FINRA/SEC regulatory documents
│   ├── reset_rules.py           # Redis-only reset
│   └── requirements.txt
├── module4-anomaly/
│   ├── Anomaly-detector/        # Timer trigger — dual ML scoring every 1 min
│   ├── Get-Alerts/              # HTTP — fetch alerts for dashboard
│   ├── RunDetector/             # HTTP — manual 60-min window trigger
│   ├── feature_engineering.py   # 7-feature computation shared across functions
│   └── train_models.py          # Local model training script
├── frontend/
│   └── src/App.js               # Complete React dashboard (single file)
├── .github/workflows/
│   └── azure-static-web-apps.yml  # GitHub Actions CI/CD
└── reset_demo.py                # Full demo reset script
```
