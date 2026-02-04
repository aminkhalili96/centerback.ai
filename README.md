# CenterBack.AI

> AI-Powered Network Intrusion Detection System
> "Your Network's Last Line of Defense"

CenterBack.AI is your network's last line of defense by using machine learning to detect and classify network intrusions in real-time.

## Features

- **Multi-class Classification**: Detects 14 different attack types
- **Real-time Analysis**: Fast inference via REST API
- **Interactive Dashboard**: Visualize threats with Apache ECharts
- **CSV Upload**: Batch analyze network flow data
- **High Accuracy**: 99%+ accuracy with Random Forest

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

# Download and prepare dataset (first time only)
python ml/download_data.py
python ml/train.py

# Run server
uvicorn app.main:app --reload
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

| Method | Endpoint                | Description          |
| ------ | ----------------------- | -------------------- |
| GET    | `/health`             | Health check         |
| GET    | `/api/stats`          | Dashboard statistics |
| GET    | `/api/alerts`         | Recent detections    |
| POST   | `/api/classify`       | Classify single flow |
| POST   | `/api/classify/batch` | Classify CSV file    |

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
├── RULES.md           # Coding standards
├── TASK.md            # Progress tracker
├── ROADMAP.md         # Future plans
└── README.md          # This file
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Backend
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

```bash
# Build and deploy to Cloud Run
gcloud run deploy centerback-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for Phase 2 features including:

- Autoencoder for zero-day detection
- Real-time streaming
- Alert notifications
- Model explainability

## License

MIT

## Author

Built with AI assistance using Claude
