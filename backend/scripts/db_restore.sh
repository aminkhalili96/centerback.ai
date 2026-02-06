#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

backup_file="$1"

if [[ ! -f "${backup_file}" ]]; then
  echo "Backup file not found: ${backup_file}"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is not set."
  exit 1
fi

if [[ "${DATABASE_URL}" == sqlite:///* ]]; then
  db_path="${DATABASE_URL#sqlite:///}"
  cp "${backup_file}" "${db_path}"
  echo "SQLite restore complete: ${db_path}"
  exit 0
fi

pg_restore --clean --if-exists --no-owner --dbname "${DATABASE_URL}" "${backup_file}"
echo "PostgreSQL restore complete from ${backup_file}"
