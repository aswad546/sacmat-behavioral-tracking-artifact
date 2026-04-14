#!/usr/bin/env python3
"""Read seed docs and POST each candidate URL + actions to vv8-backend."""
import json
import os
import sys
import uuid
from pathlib import Path

import requests

SEED = os.environ.get("SEED_FILE", "seed/mongo_landscape_seed.json")
VV8_URL = os.environ.get("VV8_URL", "http://localhost:4000/api/v1/urlsubmit-actions")


def main():
    docs = json.loads(Path(SEED).read_text())
    submitted = skipped = 0
    for doc in docs:
        candidates = doc["landscape_analysis_result"].get("login_page_candidates") or []
        if not candidates:
            skipped += 1
            continue
        c = candidates[0]
        payload = {
            "url": c["login_page_candidate"],
            "actions": c.get("login_page_actions") or [],
            "rerun": False,
            "scan_domain": doc["domain"],
            "task_id": str(uuid.uuid4()),
            "parser_config": {"delete_log_after_parsing": False, "output_format": "postgresql"},
        }
        r = requests.post(VV8_URL, json=payload, timeout=30)
        if r.status_code >= 400:
            print(f"FAIL  {doc['domain']}: HTTP {r.status_code} {r.text[:120]}", file=sys.stderr)
            continue
        print(f"OK    {doc['domain']} -> {c['login_page_candidate']}")
        submitted += 1
    print(f"\nsubmitted {submitted}, skipped {skipped} (no candidates)")


if __name__ == "__main__":
    main()
