#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient

HOST = os.environ.get("MONGODB_HOST", "logingpt-mongo")
PORT = int(os.environ.get("MONGODB_PORT", "27017"))
DB = os.environ.get("MONGODB_DATABASE", "sso-monitor")
COLLECTION = "landscape_analysis_tres"
SEED_FILE = os.environ.get("SEED_FILE", "/seed/mongo_landscape_seed.json")


def main():
    docs = json.loads(Path(SEED_FILE).read_text())
    if not isinstance(docs, list):
        print(f"seed file must contain a JSON array, got {type(docs).__name__}", file=sys.stderr)
        sys.exit(1)

    client = MongoClient(f"mongodb://{HOST}:{PORT}/")
    col = client[DB][COLLECTION]

    inserted = updated = 0
    for doc in docs:
        key = {
            "domain": doc["domain"],
            "scan_config.scan_id": doc["scan_config"]["scan_id"],
        }
        result = col.replace_one(key, doc, upsert=True)
        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count:
            updated += 1

    print(f"seed complete: {inserted} inserted, {updated} updated, total {len(docs)}")


if __name__ == "__main__":
    main()
