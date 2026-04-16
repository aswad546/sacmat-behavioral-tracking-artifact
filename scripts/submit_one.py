#!/usr/bin/env python3
import sys
import uuid
import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.fandm.bank/"
VV8_URL = "http://localhost:4000/api/v1/urlsubmit-actions"

r = requests.post(VV8_URL, json={
    "url": URL,
    "actions": [],
    "rerun": True,
    "scan_domain": URL.split("//")[1].split("/")[0],
    "task_id": str(uuid.uuid4()),
    "parser_config": {"parser": "flow", "delete_log_after_parsing": False, "output_format": "postgresql"},
})
print(r.status_code, r.text)
