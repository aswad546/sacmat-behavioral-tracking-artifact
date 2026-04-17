# SACMAT 2026 Artifact

Reproducible artifact for the behavioral-tracking detection pipeline: crawl →
VisibleV8 instrumentation → static analysis (PDG + feature extraction) →
Random Forest classification over Postgres.

The original study ran on 160 CPUs + 2× A100 GPUs across 4 machines. This
artifact runs the full pipeline (minus LoginGPT's VLM navigation) on a 16 GB /
12-core laptop using Docker Compose. Pre-computed LoginGPT results are included
as seed data so the pipeline can be evaluated end-to-end without GPU access.

<img width="4400" height="2908" alt="image" src="https://github.com/user-attachments/assets/06f892d1-5cac-4351-98dc-2de25ad8dad4" />


## Prerequisites

- Docker Desktop running
- Port forwarding set up (if running remotely via VS Code / SSH):
  - `5555` — Flower (Celery task monitor)
  - `15672` — RabbitMQ management UI
  - `4000` — VV8 backend API
  - `8100` — BBSA API
  - `3000` — Grafana (optional, for observability)
  - `16686` — Jaeger (optional, for tracing)

## Quick start (no GPU required)

```
git clone --recursive https://github.com/aswad546/sacmat-behavioral-tracking-artifact.git
cd sacmat-behavioral-tracking-artifact
cp .env.example .env
```

### Step 1: Start the full pipeline

Both VV8 (crawl) and BBSA (static analysis) must run together — BBSA processes
scripts as VV8 produces them:

```
docker compose -f docker-compose.artifact.yml --profile crawl --profile sa up -d
```

### Step 2: Submit URLs

Submit the pre-seeded login candidates to VV8:

```
python scripts/submit_to_vv8.py
```

### Step 3: Monitor progress

Open **Flower** at http://localhost:5555 to watch VV8 crawl tasks. Each URL
spawns a Celery task that runs the instrumented Chromium browser. Wait until
all tasks show as `SUCCESS` or `FAILURE` — this means VV8 has finished
crawling and the log parser has extracted scripts into `script_flow`.

Open **RabbitMQ** at http://localhost:15672 (guest/guest) → Queues tab →
`job_queue`. This shows how many scripts are queued for BBSA static analysis.
The message count will climb as VV8 finishes crawling, then decrease as the
BBSA workers process each script (PDG construction can take up to 450 seconds
per script).

Check the numbers:

```
make results
```

This prints:
- `scripts collected` — total scripts in `script_flow` (populated by VV8)
- `scripts analyzed` — completed rows in `multicore_static_info` (populated by BBSA)

### Step 4: Run the classifier

When the RabbitMQ `job_queue` is empty (all scripts processed by BBSA), run
the Random Forest classifier:

```
make classify
```

This reads `multicore_static_info`, derives 12 vendor-agnostic features per
script, and classifies each as behavioral biometric or benign. Output lands in
`rf_classification_results` table. See `classifier/README.md` for details.

### Step 5: View results

```
make results
```

To see which specific scripts were flagged as behavioral biometric tracking:

```
docker compose -f docker-compose.artifact.yml exec vv8-postgres \
  psql -U vv8 -d vv8_backend -c \
  "SELECT r.script_id, sf.url, r.behavioral_biometric_probability, r.confidence_level
   FROM rf_classification_results r
   JOIN script_flow sf ON sf.id = r.script_id
   WHERE r.prediction = 1
   ORDER BY r.behavioral_biometric_probability DESC;"
```

## LoginGPT + vision-language models (optional, requires GPU)

LoginGPT uses two VLMs (Qwen2.5-VL-7B for login page classification and
OS-Atlas-Base-7B for GUI element grounding) to automatically discover login
pages. For the artifact evaluation, **pre-computed LoginGPT results are
included as seed data** (`seed/mongo_landscape_seed.json`) — the quick start
above uses these directly, bypassing LoginGPT entirely.

To test LoginGPT live, provide any OpenAI-compatible VLM endpoint:

1. Deploy the models to your own infrastructure (Modal scripts in `modal/`,
   local vLLM, or any hosted service)
2. Set `QWEN_BASE_URL` and `OS_ATLAS_BASE_URL` in `.env`
3. Run `make login-only` to start LoginGPT

The `modal/` directory contains reference deployment scripts for Modal
(`qwen_app.py`, `os_atlas_app.py`). See `modal/README.md` for setup. These
require a Modal account and an L40S or A100 GPU allocation.

## Standalone components

Each subsystem can run independently:

```
make login-only                # LoginGPT only (requires VLM endpoints)
make crawl-only                # VisibleV8 crawler only
make analyze-only              # BBSA static analysis only
make full                      # everything wired end-to-end
```

## Scaling up

```
WORKER_REPLICAS=8 BBSA_WORKER_REPLICAS=16 CELERY_CONCURRENCY=8 make up
TARGETS_FILE=targets/targets_full.txt make smoke
```

Drop any newline-separated URL list in `targets/` and point `TARGETS_FILE`
at it. Adjust replica counts to match available CPU cores.

## Observability (optional)

```
make up-obs
```

Adds Jaeger (localhost:16686), Prometheus (9091), Grafana (3000), Loki (3101).
Use Grafana → Explore → Loki to query container logs:
- `{container_name=~".*bbsa-worker.*"}` for static analysis logs
- `{container_name=~".*vv8-worker.*"}` for crawler logs

## Layout

```
docker-compose.artifact.yml      master compose, profile-gated
docker-compose.observability.yml  optional overlay
modal/                            reference VLM deployment scripts
seed/                             pre-computed LoginGPT results (20 URLs)
classifier/                       RF model + scoring script
targets/                          URL lists
forwarder/                        VV8 → BBSA polling sidecar
scripts/                          smoke tests, submit helpers, result checker
LoginGPT/                         git submodule (login page discovery)
visiblev8-crawler/                git submodule (instrumented JS collection)
BehavioralBiometricSA/            git submodule (static analysis)
```

## Hardware requirements

- **Minimum:** 16 GB RAM, 12 CPU cores, Docker Desktop **Tested on Windows Machines**
- **Recommended:** 32 GB RAM, 16 cores for faster PDG construction
- **For LoginGPT:** any OpenAI-compatible VLM endpoint (GPU not needed locally)
- **Original study:** 160 CPUs, 1 TB RAM, 2× A100 GPUs across 4 machines

## Troubleshooting

- **No VLM endpoints:** The default path (`scripts/submit_to_vv8.py`) bypasses
  LoginGPT entirely using pre-seeded data. No Modal or GPU needed.
- **VV8 Chromium image pull fails:** the `visiblev8/vv8-base` upstream image
  may have moved. Check `visiblev8-crawler/celery_workers/vv8_worker.dockerfile`.
- **Port conflicts:** stop conflicting services or edit port bindings in
  `docker-compose.artifact.yml`.
- **BBSA worker errors on draw_ast/draw_cfg:** Graphviz rendering of ASTs can
  fail on complex scripts. These are non-fatal — the actual analysis continues.
- **RabbitMQ slow to start:** the healthcheck allows 150 seconds. If it still
  times out, increase `retries` in the compose file.
- **Flower shows no tasks:** make sure VV8 worker is running (`docker ps | grep vv8-worker`).
  Check worker logs: `docker compose -f docker-compose.artifact.yml logs vv8-worker --tail=50`.

## Paper

[citation + DOI placeholder]
