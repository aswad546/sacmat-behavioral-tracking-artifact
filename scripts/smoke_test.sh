#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo ">>> submitting seed URLs to vv8-backend"
python scripts/submit_to_vv8.py

echo ">>> waiting up to 10 minutes for multicore_static_info rows..."
for i in $(seq 1 60); do
  n=$(docker exec $(docker compose -f docker-compose.artifact.yml ps -q vv8-postgres) \
      psql -U "${POSTGRES_USER:-vv8}" -d "${POSTGRES_DB:-vv8_backend}" -Atc \
      "SELECT COUNT(*) FROM multicore_static_info;" 2>/dev/null || echo 0)
  echo "[${i}/60] multicore_static_info rows: ${n}"
  if [[ "${n}" -gt 0 ]]; then
    break
  fi
  sleep 10
done

echo ">>> results"
python scripts/check_results.py
