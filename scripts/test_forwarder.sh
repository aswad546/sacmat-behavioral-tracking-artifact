#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

pg=$(docker compose -f docker-compose.artifact.yml ps -q vv8-postgres)
fwd=$(docker compose -f docker-compose.artifact.yml ps -q vv8-bbsa-forwarder)

docker exec "$pg" psql -U "${POSTGRES_USER:-vv8}" -d "${POSTGRES_DB:-vv8_backend}" -c \
  "INSERT INTO script_flow (url, code, apis) VALUES
   ('https://test.artifact/fwd.js', 'var x = 1;', '[]'::jsonb) RETURNING id;"

echo ">>> tailing forwarder logs (up to 30s)..."
timeout 30 docker logs -f "$fwd" 2>&1 | grep -q "Sending batch" && echo "OK: forwarder picked up the row" || {
  echo "FAIL: forwarder did not emit 'Sending batch' within 30s"; exit 1;
}
