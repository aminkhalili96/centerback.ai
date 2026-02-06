#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date +%Y%m%d_%H%M%S)"
mkdir -p backups

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is not set."
  exit 1
fi

if [[ "${DATABASE_URL}" == sqlite:///* ]]; then
  db_path="${DATABASE_URL#sqlite:///}"
  cp "${db_path}" "backups/centerback_${timestamp}.db"
  echo "SQLite backup written to backups/centerback_${timestamp}.db"
  exit 0
fi

pg_dump "${DATABASE_URL}" --format=custom --file "backups/centerback_${timestamp}.dump"
echo "PostgreSQL backup written to backups/centerback_${timestamp}.dump"
