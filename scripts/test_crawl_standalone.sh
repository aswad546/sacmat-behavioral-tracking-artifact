#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

make crawl-only
sleep 15

curl -fsS -X POST http://localhost:4000/api/v1/urlsubmit-actions \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "rerun": false, "parser_config": {"delete_log_after_parsing": false, "output_format": "postgresql"}}'

echo
echo ">>> waiting for script_flow row..."
for i in $(seq 1 30); do
  n=$(docker exec $(docker compose -f docker-compose.artifact.yml ps -q vv8-postgres) \
      psql -U "${POSTGRES_USER:-vv8}" -d "${POSTGRES_DB:-vv8_backend}" -Atc \
      "SELECT COUNT(*) FROM script_flow WHERE url LIKE 'https://example.com%';" 2>/dev/null || echo 0)
  echo "[${i}/30] script_flow rows for example.com: ${n}"
  [[ "${n}" -gt 0 ]] && exit 0
  sleep 10
done
echo "FAIL: no script_flow rows after 5 minutes" >&2
exit 1
