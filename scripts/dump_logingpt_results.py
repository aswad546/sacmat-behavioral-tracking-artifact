#!/usr/bin/env python3
"""Dump all landscape_analysis_tres docs for a given scan_id to stdout as JSON."""
import json
import os
import sys

from bson import ObjectId
from pymongo import MongoClient

SCAN_ID = sys.argv[1] if len(sys.argv) > 1 else "artifact-smoke-20"
HOST = os.environ.get("MONGODB_HOST", "localhost")
PORT = int(os.environ.get("MONGODB_PORT", "27019"))


def _clean(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def main():
    client = MongoClient(f"mongodb://{HOST}:{PORT}/")
    col = client["sso-monitor"]["landscape_analysis_tres"]
    docs = list(col.find({"scan_config.scan_id": SCAN_ID}))
    print(json.dumps([_clean(d) for d in docs], indent=2))


if __name__ == "__main__":
    main()
