#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

make analyze-only
sleep 15

pg=$(docker compose -f docker-compose.artifact.yml ps -q vv8-postgres)

docker exec "$pg" psql -U "${POSTGRES_USER:-vv8}" -d "${POSTGRES_DB:-vv8_backend}" -c \
  "INSERT INTO script_flow (url, code, apis) VALUES
   ('https://test.artifact/probe.js', 'document.addEventListener(\"keydown\", function(e){});', '[{\"API\":\"Document.addEventListener\",\"offset\":0}]'::jsonb)
   RETURNING id;"

echo ">>> waiting for forwarder + bbsa-worker to populate multicore_static_info..."
for i in $(seq 1 30); do
  n=$(docker exec "$pg" psql -U "${POSTGRES_USER:-vv8}" -d "${POSTGRES_DB:-vv8_backend}" -Atc \
      "SELECT COUNT(*) FROM multicore_static_info WHERE script_url = 'https://test.artifact/probe.js';" 2>/dev/null || echo 0)
  echo "[${i}/30] analysis rows: ${n}"
  [[ "${n}" -gt 0 ]] && exit 0
  sleep 10
done
echo "FAIL: no analysis result after 5 minutes" >&2
exit 1
