# SACMAT 2026 Artifact

Reproducible artifact for the behavioral-tracking detection pipeline: crawl →
VisibleV8 instrumentation → static analysis (PDG + feature extraction) →
Random Forest classification over Postgres.

The original study ran on 160 CPUs + 2× A100 GPUs across 4 machines. This
artifact runs the full pipeline (minus LoginGPT's VLM navigation) on a 16 GB /
12-core laptop using Docker Compose. Pre-computed LoginGPT results are included
as seed data so the pipeline can be evaluated end-to-end without GPU access.

<img width="4400" height="2908" alt="image" src="https://github.com/user-attachments/assets/06f892d1-5cac-4351-98dc-2de25ad8dad4" />

## Hardware requirements

| | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 32 GB |
| CPU | 12 cores | 16+ cores |
| OS | **Windows 11 (tested)** | Windows 11 |
| Software | Docker Desktop, Git | Docker Desktop, Git, Python 3.10+ |
| GPU | Not required | Not required |

> **Note:** This artifact was developed and tested on Windows 11 with Docker
> Desktop. Windows is the recommended platform. Linux and macOS should work
> but have not been tested.

## Prerequisites

1. **Install Docker Desktop** and make sure it is running 
2. **Install Git** (with Git Bash on Windows)
3. **Install Python 3.10+** with `requests` package (`pip install requests`)
4. **If running remotely** (e.g., via VS Code Remote SSH), set up port forwarding for these ports:

| Port | Service | What it shows |
|---|---|---|
| 5555 | Flower | VV8 crawl task status (SUCCESS/FAILURE) |
| 15672 | RabbitMQ | BBSA job queue depth (how many scripts left to analyze) |
| 4000 | VV8 backend | API for submitting URLs |
| 8100 | BBSA API | API for static analysis submissions |
| 3000 | Grafana | Logs and dashboards (optional) |

## Quick start (no GPU required)

Follow these steps exactly in order. Each step must complete before moving to
the next.

### Step 1: Clone and configure

Open a terminal (Git Bash on Windows) and run:

```bash
git clone --recursive https://github.com/aswad546/sacmat-behavioral-tracking-artifact.git
cd sacmat-behavioral-tracking-artifact
cp .env.example .env
```

> **Important:** The `--recursive` flag is required. It pulls the three
> subsystem repos (LoginGPT, visiblev8-crawler, BehavioralBiometricSA) as
> git submodules. If you forgot it, run: `git submodule update --init --recursive`

### Step 2: Start the pipeline

Start both VV8 (crawler) and BBSA (static analysis) together. They must run
at the same time — BBSA processes scripts as VV8 produces them:

```bash
docker compose -f docker-compose.artifact.yml --profile crawl --profile sa up -d
```

Wait about 30 seconds for all containers to start. Verify everything is
running:

```bash
docker ps
```

You should see containers for: `vv8-backend`, `vv8-worker`, `vv8-postgres`,
`vv8-celery-redis`, `vv8-mongo`, `vv8-flower`, `vv8-log-parser-worker`,
`vv8-celery-exporter`, `vv8-redis-exporter`, `vv8-bbsa-forwarder`,
`bbsa-api`, `bbsa-rabbit`, and `bbsa-worker` (multiple replicas).

> **If `bbsa-rabbit` shows as unhealthy:** RabbitMQ can take up to 2 minutes
> to start. Wait and run `docker ps` again. Dependent containers will start
> automatically once it's healthy.

### Step 3: Submit URLs to VV8

Submit the 20 pre-seeded bank website URLs to the VV8 crawler:

```bash
python scripts/submit_to_vv8.py
```

You should see output like:
```
OK    www.fandm.bank -> https://www.fandm.bank/
OK    www.fnbforyou.com -> https://www.olb-ebanking.com/064107994/login/
...
submitted 13, skipped 7 (no candidates)
```

13 URLs with login candidates get submitted; 7 control URLs (no candidates)
are skipped. This is expected.

### Step 4: Wait for VV8 to finish crawling

Open **Flower** in your browser: http://localhost:5555

This shows VV8's Celery task queue. Each submitted URL becomes a task. Wait
until all tasks show status `SUCCESS` (green) or `FAILURE` (red). This
typically takes 5-15 minutes depending on your machine and network speed.

> **What's happening:** For each URL, VV8 launches an instrumented Chromium
> browser, loads the page, triggers behavioral events (clicks, keystrokes,
> mouse movements), and records every JavaScript API call. The log parser
> then extracts individual scripts and inserts them into the `script_flow`
> table in Postgres.

### Step 5: Wait for BBSA to finish static analysis

Open **RabbitMQ Management** in your browser: http://localhost:15672
- Username: `guest`
- Password: `guest`

Go to the **Queues** tab and look at `job_queue`. The **Messages** column shows
how many scripts are queued for static analysis.

This number will:
1. **Go up** as VV8 finishes crawling and the forwarder sends script IDs to BBSA
2. **Go down** as BBSA workers process each script (building program dependence
   graphs, extracting features)

**Wait until `job_queue` Messages reaches 0.** This means all scripts have
been analyzed. This can take 30-60 minutes — PDG construction takes up to
450 seconds per complex script.

You can also check progress from the terminal:

```bash
make results
```

This prints how many scripts have been collected vs analyzed.

### Step 6: Run the classifier

Once the RabbitMQ `job_queue` is empty (all scripts analyzed), run the
Random Forest classifier:

```bash
make classify
```

This will print a summary like:
```
Total scripts processed: 30
Classified as behavioral biometric: 2 (6.7%)
Classified as benign: 28 (93.3%)
Average confidence: 0.952
```

### Step 7: View final results

```bash
make results
```

To see which specific scripts were flagged as behavioral biometric:

```bash
docker compose -f docker-compose.artifact.yml exec vv8-postgres \
  psql -U vv8 -d vv8_backend -c \
  "SELECT r.script_id, sf.url, r.behavioral_biometric_probability, r.confidence_level
   FROM rf_classification_results r
   JOIN script_flow sf ON sf.id = r.script_id
   WHERE r.prediction = 1
   ORDER BY r.behavioral_biometric_probability DESC;"
```

### Step 8: Shut down

```bash
docker compose -f docker-compose.artifact.yml --profile crawl --profile sa down
```

Your data persists in `./data/`. Next time you `up`, everything picks up
where you left off.

---

## LoginGPT + vision-language models (optional, requires GPU)

LoginGPT uses two VLMs (Qwen2.5-VL-7B for login page classification and
OS-Atlas-Base-7B for GUI element grounding) to automatically discover login
pages by navigating websites visually.

For the artifact evaluation, **pre-computed LoginGPT results are included as
seed data** (`seed/mongo_landscape_seed.json`) — the quick start above uses
these directly, bypassing LoginGPT entirely.

To test LoginGPT live, provide any OpenAI-compatible VLM endpoint:

1. Deploy the models to your own infrastructure (Modal scripts in `modal/`,
   local vLLM, or any hosted service)
2. Set `QWEN_BASE_URL` and `OS_ATLAS_BASE_URL` in `.env`
3. Run `make login-only` to start LoginGPT

The `modal/` directory contains reference deployment scripts for Modal
(`qwen_app.py`, `os_atlas_app.py`). See `modal/README.md` for setup.

## Standalone components

Each subsystem can run independently:

```bash
make login-only                # LoginGPT only (requires VLM endpoints)
make crawl-only                # VisibleV8 crawler only
make analyze-only              # BBSA static analysis only
make full                      # everything wired end-to-end
```

## Scaling up 

Edit `.env` to increase parallelism (for 12 core 16GB RAM host keep default configuration from example.env file):

```
WORKER_REPLICAS=8              # LoginGPT browser instances
BBSA_WORKER_REPLICAS=16        # static analysis workers
CELERY_CONCURRENCY=8           # VV8 crawler concurrency
```

To use a different URL list:

```
TARGETS_FILE=targets/targets_full.txt
```

Drop any newline-separated URL list in `targets/`.

## Observability (optional)

```bash
docker compose -f docker-compose.artifact.yml -f docker-compose.observability.yml \
  --profile crawl --profile sa --profile observability up -d
```

This adds:
- **Grafana** (http://localhost:3000, admin/admin) — dashboards and log search
- **Jaeger** (http://localhost:16686) — distributed tracing
- **Prometheus** (http://localhost:9091) — metrics
- **Loki** — log aggregation (query via Grafana → Explore → Loki)

Useful Loki queries in Grafana:
- `{container_name=~".*bbsa-worker.*"}` — static analysis logs
- `{container_name=~".*vv8-worker.*"}` — crawler logs
- `{container_name=~".*forwarder.*"}` — VV8→BBSA handoff logs

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

## Troubleshooting

| Problem | Solution |
|---|---|
| `docker compose` not found | Use `docker-compose` (hyphenated) or update Docker Desktop |
| `bbsa-rabbit` unhealthy on startup | Wait 2 minutes — RabbitMQ is slow to initialize |
| `scripts analyzed` stuck at 0 | Check that `--profile sa` is running: `docker ps \| grep bbsa` |
| BBSA errors about `draw_ast` | Non-fatal — Graphviz rendering fails on some scripts but analysis continues |
| `No more records to process` in forwarder | Normal — all scripts already sent to BBSA |
| VV8 worker shows `exec /entrypoint.sh: no such file or directory` | CRLF issue — rebuild: `docker compose ... up -d --build vv8-worker` |
| Flower (localhost:5555) shows no tasks | VV8 worker may not be running — check `docker ps \| grep vv8-worker` |
| Port already in use | Stop conflicting services or edit ports in `docker-compose.artifact.yml` |
| Want to start fresh | `docker compose ... down` then `rm -rf data/` and restart |

## Paper

[citation + DOI placeholder]
