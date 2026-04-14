#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

make login-only
echo ">>> waiting 30s for brain + worker to come up..."
sleep 30

# seed container runs once and exits; check mongo has the 20 seed docs
n=$(docker exec $(docker compose -f docker-compose.artifact.yml ps -q logingpt-mongo) \
    mongo sso-monitor --quiet --eval \
    'db.landscape_analysis_tres.countDocuments({"scan_config.scan_id": "artifact-smoke-20"})')
echo "seed docs in logingpt-mongo: ${n}"
if [[ "${n}" != "20" ]]; then
  echo "FAIL: expected 20 seed docs, got ${n}" >&2
  exit 1
fi

# brain responds
curl -fsS http://localhost:8084/api/ping || { echo "FAIL: brain /api/ping"; exit 1; }
echo "OK: logingpt stack healthy, seed loaded"
