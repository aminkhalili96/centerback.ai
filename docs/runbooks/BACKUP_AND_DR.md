# CenterBack.AI Backup and Disaster Recovery Runbook

## Scope

This runbook covers backup and restore for:

1. Application database (`DATABASE_URL`)
2. Model artifacts (`backend/ml/models/*.joblib` or managed model storage)
3. Configuration and secrets references (`.env` source, secret manager entries)

## Recovery Targets

- **RPO target**: 15 minutes
- **RTO target**: 60 minutes

## Backup Strategy

### PostgreSQL (recommended production)

1. Run logical backups every 15 minutes:
   ```bash
   pg_dump "$DATABASE_URL" --format=custom --file "backups/centerback_$(date +%Y%m%d_%H%M%S).dump"
   ```
2. Retain:
   - Last 96 backups (24 hours)
   - Daily snapshots for 30 days
3. Encrypt and store off-site (cloud bucket with versioning + lifecycle policy).

### SQLite (development / fallback)

1. Quiesce writes briefly (maintenance window).
2. Copy `backend/data/centerback.db` to backup storage.
3. Store checksum for integrity verification.

## Restore Procedure

### PostgreSQL Restore

1. Provision target database.
2. Restore most recent consistent backup:
   ```bash
   pg_restore --clean --if-exists --no-owner --dbname "$DATABASE_URL" backups/centerback_<timestamp>.dump
   ```
3. Run migrations:
   ```bash
   cd backend
   alembic -c alembic.ini upgrade head
   ```
4. Validate:
   - `GET /health`
   - `GET /api/stats` with analyst/admin token
   - `GET /api/model/info`

### SQLite Restore

1. Stop backend process.
2. Replace `backend/data/centerback.db` with backup copy.
3. Start backend and validate health/status endpoints.

## DR Drill Checklist

Run quarterly:

1. Restore into isolated environment.
2. Validate auth (`/api/auth/login` or OIDC), ingestion (`/api/ingest/queue`), and detection paths.
3. Verify model governance endpoints (`/api/model/drift`, `/api/model/evaluations`).
4. Record:
   - Restore start/end timestamps
   - Data loss window (RPO actual)
   - Service restoration time (RTO actual)
   - Incidents and remediation tasks

## Incident Escalation

1. Declare severity and incident commander.
2. Freeze non-essential deployments.
3. Restore database and model artifacts.
4. Re-enable ingestion pipeline after validation.
5. Publish post-incident report with corrective actions.
