# Mongo landscape seed

Pre-populates the `sso-monitor.landscape_analysis_tres` collection in
`logingpt-mongo` with 20 curated `landscape_analysis_result` docs so the
smoke test doesn't have to wait minutes per URL for metasearch / sitemap /
robots / paths detection to run live.

Loaded by the `logingpt-mongo-seed` one-shot container at compose startup.
Idempotent — upserts by `(domain, scan_config.scan_id)`.

## Regenerating from a live run

After a full `make smoke`, dump the collection:

```
docker exec logingpt-mongo mongo sso-monitor \
  --eval 'db.landscape_analysis_tres.find({"scan_config.scan_id": "<your-scan-id>"}).toArray()' \
  --quiet > seed/mongo_landscape_seed.json
```

Then strip `_id` fields and set `scan_config.scan_id` to `artifact-smoke-20`.
