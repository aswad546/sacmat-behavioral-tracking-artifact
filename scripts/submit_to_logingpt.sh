#!/usr/bin/env bash
# Submit a newline-separated URL file to the LoginGPT brain API.
# Intended for reviewers using the "login-only" standalone mode.
set -euo pipefail

URLS_FILE="${1:-targets/targets_mini.txt}"
BRAIN_URL="${BRAIN_URL:-http://localhost:8084}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-changeme}"

[[ -f "$URLS_FILE" ]] || { echo "usage: submit_to_logingpt.sh <urls-file>"; exit 1; }

while IFS= read -r url; do
  [[ -z "$url" || "$url" =~ ^# ]] && continue
  echo "submit: $url"
  curl -fsS -u "${ADMIN_USER}:${ADMIN_PASS}" "${BRAIN_URL}/api/tasks/landscape_analysis/rescan?scan_id=artifact-smoke-20" \
    -X POST -H "Content-Type: application/json" -d "{\"url\":\"${url}\"}" || true
done < "$URLS_FILE"
