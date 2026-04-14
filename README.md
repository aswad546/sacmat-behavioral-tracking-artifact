# SACMAT 2026 Artifact

Reproducible artifact for the behavioral-tracking detection pipeline: crawl →
VisibleV8 instrumentation → static analysis (PDG + feature extraction +
Random Forest classifier) over Postgres.

The original study ran on 160 CPUs + 2× A100. This artifact runs on a 16 GB /
8-core laptop with scale-to-zero serverless GPU for the two vision-language
models (Qwen2.5-VL-7B and OS-Atlas-Base-7B) hosted on Modal.

## Quick start

```
cp .env.example .env
make modal-deploy              # one-time, deploys Qwen + OS-Atlas to Modal
# paste the two URLs Modal prints into .env as QWEN_BASE_URL / OS_ATLAS_BASE_URL
make up
make smoke                     # ~10 min, 20-URL mini set
make results                   # paper-claim table from multicore_static_info
```

## Standalone components

Each of the three subsystems runs independently. Pick one:

```
make login-only                # LoginGPT: finds login pages, writes to Mongo
make crawl-only                # VisibleV8: instruments JS, writes to Postgres
make analyze-only              # BBSA: builds PDGs, extracts features, classifies
make full                      # everything wired end-to-end
```

## Swapping in your own models

`QWEN_BASE_URL` and `OS_ATLAS_BASE_URL` accept any OpenAI-compatible
`/v1/chat/completions` endpoint — your own Modal deployment, a local `vllm
serve` instance, or a hosted service. No code changes needed.

## Scaling up

```
WORKER_REPLICAS=8 BBSA_WORKER_REPLICAS=16 CELERY_CONCURRENCY=8 make up
TARGETS_FILE=targets/targets_full.txt make smoke
```

Drop any newline-separated URL list in `targets/` and point `TARGETS_FILE`
at it.

## Random Forest classifier (offline post-step)

```
make up && make smoke    # populate multicore_static_info
make classify            # run the RF classifier against it
```

The classifier is a separate batch pass — not inline with static analysis.
Source + trained model live in `classifier/` (cleaned copy of the paper's
production script from `../visiblev8-crawler/script_classification/vendor_issues/no_split/`).
Output lands in the `rf_classification_results` table and a joined
`rf_classification_view`. See `classifier/README.md` for env vars and a full
explanation of why this runs offline.

## Observability (optional)

```
make up-obs
```

Adds Jaeger (http://localhost:16686), Prometheus (9091), Grafana (3000),
Loki (3101), and OTel Collector on top of the base stack.

## Layout

```
docker-compose.artifact.yml      master compose, profile-gated
docker-compose.observability.yml optional overlay
modal/                           serverless VLM deployments
seed/                            pre-computed landscape_analysis docs
targets/                         URL lists
forwarder/                       VV8 → BBSA polling sidecar
scripts/                         smoke tests, submit helpers, result checker
../LoginGPT/                     vendored subsystem (build context)
../visiblev8-crawler/            vendored subsystem
../BehavioralBiometricSA/        vendored subsystem
../visiblev8/                    archive only — custom Go post-processor
                                 fork with inline BBSA POST logic. Not
                                 built or used at runtime; the polling
                                 sidecar (forwarder/) handles the handoff
                                 equivalently.
```

## Troubleshooting

- **Modal endpoints unreachable**: set `VLM_CACHE_MODE=cache_only` in `.env`;
  the pipeline falls back to `data/vlm_cache.json` and skips live calls.
- **VV8 Chromium image pull fails**: the `visiblev8/vv8-base` upstream image
  may have moved. See `../visiblev8-crawler/celery_workers/vv8_worker.dockerfile`
  to pin a specific digest.
- **Port conflicts on 80/443/4000/5434/8084**: something else is using them.
  Stop conflicting services or edit port bindings in `docker-compose.artifact.yml`.
- **LoginGPT → VV8 handoff**: currently the worker's `helper/rabbit.py` POSTs
  to `172.17.0.1:4050` (the upstream `scripts/crawl.py` bridge). This is
  tracked as a known issue; the artifact smoke test bypasses LoginGPT and
  submits seed docs directly to VV8 via `scripts/submit_to_vv8.py`.
- **CRAWLING strategy in LoginGPT**: `crawler.js` still talks to the old
  socket servers and has not been ported to HTTPS/Modal. Use the PATHS,
  ROBOTS, SITEMAP, or METASEARCH strategies instead, or rely on the seed.

## Paper

[citation + DOI placeholder]
