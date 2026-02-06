# CenterBack.AI

> AI-Powered Network Intrusion Detection System
> "Your Network's Last Line of Defense"

CenterBack.AI is your network's last line of defense by using machine learning to detect and classify network intrusions in real-time.

![Dashboard Screenshot](assets/dashboard.png)

## Features

- **Multi-class Classification**: Detects 14 different attack types
- **Real-time Analysis**: Fast inference via REST API
- **Interactive Dashboard**: Visualize threats with Apache ECharts
- **CSV Upload**: Batch analyze network flow data
- **Durable Event Storage**: Classification events and alerts persisted in SQL
- **Auth + RBAC**: JWT auth with viewer/analyst/admin roles
- **OIDC + SCIM Ready**: External IdP token verification and SCIM v2 user provisioning endpoints
- **Ingestion Queue**: DB-backed queue with retry and dead-letter handling
- **Idempotent Ingestion**: Duplicate flow suppression and queue backpressure controls
- **Audit Trail**: Tracks sensitive operational actions
- **Model Registry**: Version registration and promotion endpoints
- **Canary + Drift Governance**: Canary model rollout controls and drift/evaluation APIs
- **Model Accuracy**: Demo model reports ~82.87% accuracy on synthetic CICIDS2017-shaped data (train locally to enable real inference)

## Tech Stack

- **Backend**: Python, FastAPI
- **ML**: scikit-learn (Random Forest)
- **Frontend**: Next.js, React, TypeScript
- **Visualization**: Apache ECharts
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Google Cloud Run

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Train a model (first time only)
# Option A (quick demo): generate synthetic sample data
python ml/generate_sample.py
python ml/train.py
#
# Option B: download full CICIDS2017 dataset (manual/Kaggle), then train
# python ml/download_data.py
# python ml/train.py

# Run server
uvicorn app.main:app --reload

# Optional: run DB migrations
alembic -c alembic.ini upgrade head
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/auth/login` | JWT login |
| GET | `/api/auth/me` | Current user profile |
| POST | `/api/auth/users` | Create user (admin) |
| GET | `/api/scim/v2/Users` | SCIM list users |
| POST | `/api/scim/v2/Users` | SCIM create user |
| PATCH | `/api/scim/v2/Users/{id}` | SCIM patch user |
| DELETE | `/api/scim/v2/Users/{id}` | SCIM deactivate user |
| POST | `/api/classify` | Classify single flow |
| POST | `/api/classify/batch` | Classify CSV file |
| POST | `/api/classify/sample` | Classify demo sample |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/stats/session` | Session aggregate stats |
| POST | `/api/stats/session/reset` | Reset stats (admin) |
| GET | `/api/stats/attacks` | Attack distribution |
| GET | `/api/stats/distribution` | Attack distribution alias |
| GET | `/api/alerts` | Recent detections |
| GET | `/api/alerts/{id}` | Alert detail |
| PATCH | `/api/alerts/{id}/status` | Alert lifecycle transition |
| GET | `/api/model/info` | Active model metadata |
| GET | `/api/model/versions` | List model versions |
| POST | `/api/model/versions` | Register model version (admin) |
| POST | `/api/model/versions/{id}/promote` | Promote model version (admin) |
| GET | `/api/model/canary/status` | Canary rollout status |
| POST | `/api/model/canary/enable` | Enable canary rollout (admin) |
| POST | `/api/model/canary/disable` | Disable canary rollout (admin) |
| GET | `/api/model/drift` | Drift analytics report |
| GET | `/api/model/evaluations` | Canary divergence metrics |
| POST | `/api/ingest/flows` | Queue flow ingestion |
| GET | `/api/ingest/queue` | Queue status summary |
| GET | `/api/ingest/dlq` | Dead-letter queue (admin) |
| POST | `/api/ingest/retry/{message_id}` | Requeue dead-letter message (admin) |
| GET | `/api/integrations/status` | Integration channel status |
| POST | `/api/integrations/notify/test` | Send test notification (admin) |
| GET | `/api/dataset/info` | Dataset metadata |
| GET | `/api/dataset/preview` | Dataset preview table |
| GET | `/api/dataset/download` | Download sample dataset |

## Attack Types Detected

| Category       | Attack Types                                                   |
| -------------- | -------------------------------------------------------------- |
| DoS/DDoS       | DDoS, DoS Hulk, DoS GoldenEye, DoS Slowloris, DoS Slowhttptest |
| Reconnaissance | PortScan                                                       |
| Brute Force    | FTP-Patator, SSH-Patator                                       |
| Web Attacks    | Brute Force, XSS, SQL Injection                                |
| Other          | Bot, Infiltration, Heartbleed                                  |

## Dataset

Uses the **CICIDS2017** dataset from the Canadian Institute for Cybersecurity:

- 2.8M labeled network flows
- 78 features per flow
- 15 classes (1 benign + 14 attack types)

## Project Structure

```
centerback.ai/
├── backend/           # Python FastAPI backend
├── frontend/          # Next.js frontend
├── CLAUDE.md          # AI context file
├── Codex.md           # AI context file (Codex)
├── RULES.md           # Coding standards
├── TASK.md            # Progress tracker
├── ROADMAP.md         # Future plans
└── README.md          # This file
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Backend
# DATABASE_URL=postgresql+psycopg://user:pass@host:5432/centerback
# AUTH_REQUIRED=true
# AUTH_MODE=local
# AUTH_JWT_SECRET=replace-this-in-production
# AUTH_JWT_ALGORITHM=HS256
# AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60
# BOOTSTRAP_ADMIN_USERNAME=admin
# BOOTSTRAP_ADMIN_PASSWORD=change-me-now
# AUTH_OIDC_ISSUER=https://issuer/
# AUTH_OIDC_AUDIENCE=centerback-api
# AUTH_OIDC_JWKS_URL=https://issuer/.well-known/jwks.json
# AUTH_OIDC_USERNAME_CLAIM=email
# SCIM_BEARER_TOKEN=replace-with-random-token

# Optional: override model artifact path (defaults to backend/ml/models/random_forest_v1.joblib)
MODEL_PATH=ml/models/random_forest_v1.joblib

# Optional: CORS overrides (defaults allow localhost + Vercel previews)
# CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# CORS_ALLOW_ORIGIN_REGEX=https://.*\.vercel\.app

# Optional hardening and worker controls
# RATE_LIMIT_PER_MINUTE=120
# MAX_REQUEST_BYTES=5242880
# ENABLE_DEMO_FALLBACK=false
# INGEST_PIPELINE_ENABLED=true
# INGEST_POLL_INTERVAL_SECONDS=2
# INGEST_BATCH_SIZE=100
# INGEST_MAX_ATTEMPTS=5
# INGEST_MAX_QUEUE_DEPTH=5000
# INGEST_IDEMPOTENCY_WINDOW_MINUTES=30
# ALERT_DEDUP_WINDOW_MINUTES=10
# NOTIFICATION_WEBHOOK_URL=https://hooks.example.com/centerback
# NOTIFICATION_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
# NOTIFICATION_TIMEOUT_SECONDS=5
# CANARY_ENABLED=false
# CANARY_MODEL_PATH=ml/models/random_forest_v2.joblib
# CANARY_TRAFFIC_PERCENT=5
# DRIFT_WINDOW_EVENTS=500
# DRIFT_ALERT_THRESHOLD=0.2

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
# Optional static token fallback for protected APIs
# NEXT_PUBLIC_API_TOKEN=<jwt-token>
```

## Validation

```bash
# Backend
pytest backend/tests -q
python -m compileall backend/app backend/ml

# Frontend
cd frontend && npm run lint && npm run build
```

## Operations Runbooks

- Documentation index: `docs/README.md`
- Backup and DR runbook: `docs/runbooks/BACKUP_AND_DR.md`
- Enterprise status and implementation checklist: `Codex.md`
- Delivery task tracker: `TASK.md`

## Deployment

```bash
# Build and deploy to Cloud Run
gcloud run deploy centerback-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Roadmap

See `ROADMAP.md` for post-foundation phases:

- Scale hardening (`v0.3.0`)
- SOC integrations (`v0.4.0`)
- Compliance automation (`v0.5.0`)

## License

MIT

## Author

Built with AI assistance using Claude
