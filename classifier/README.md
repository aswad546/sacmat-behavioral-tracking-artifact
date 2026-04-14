# Random Forest classifier (offline post-step)

Runs **after** the main pipeline populates `multicore_static_info`. Pulls rows
from Postgres, derives 12 vendor-agnostic features, scores each script with
the trained behavioral-biometric classifier, and writes results to a new table
+ view.

Source: this is a cleaned, env-parameterized copy of
`../visiblev8-crawler/script_classification/vendor_issues/no_split/classify.py`.
The model is the July 11, 2025 build
(`behavioral_biometric_classifier_binary_20250711_161434.pkl`) which the
paper uses as its final classifier.

## Run

The main pipeline must have already produced rows in `multicore_static_info`.
Then:

```
make classify
```

This builds a one-shot Docker image, attaches it to the artifact network so it
can reach `vv8-postgres`, runs the classifier, and exits. Output:

- **`rf_classification_results`** table — one row per script with `prediction`,
  `behavioral_biometric_probability`, `benign_probability`, `confidence`,
  `confidence_level`, `classification_timestamp`, `model_version`.
- **`rf_classification_view`** — a LEFT JOIN of `multicore_static_info` with
  `rf_classification_results`, convenient for querying.

## Env vars

| Var | Default | Notes |
|---|---|---|
| `PGHOST` | `vv8-postgres` | Set by `make classify` |
| `PGPORT` | `5432` | Set by `make classify` |
| `PGUSER` / `PGPASSWORD` / `PGDATABASE` | `vv8` / `vv8` / `vv8_backend` | |
| `CLASSIFIER_MODEL_PATH` | `final_models/behavioral_biometric_classifier_binary_20250711_161434.pkl` | Swap to use a different trained model |
| `CLASSIFIER_SOURCE_TABLE` | `multicore_static_info` | Point at a snapshot table if you want |
| `CLASSIFIER_RESULTS_TABLE` | `rf_classification_results` | |
| `CLASSIFIER_VIEW_NAME` | `rf_classification_view` | |
| `CLASSIFIER_LIMIT` | unset (all rows) | e.g. `100` for a quick test |

## Why this isn't inline

Features like `tracks_coordinates`, `uses_screen_fp`, `sophistication_score`
are **derived** in `create_vendor_agnostic_features()` by string-matching over
the JSONB `behavioral_source_apis` / `fingerprinting_source_apis` columns.
They're not raw DB fields. Running the classifier inline per-script during
static analysis would either duplicate that logic in BBSA's worker (bloat) or
feed garbage into the model. Keeping it offline against the completed table is
both simpler and matches how the paper's experiments were actually run.
