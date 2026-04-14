# Modal serverless VLM endpoints

Two thin vLLM wrappers exposing OpenAI-compatible `/v1/chat/completions`
endpoints on L40S GPUs. Scale-to-zero between requests.

## One-time setup

```
pip install modal
modal token new
```

## Deploy

```
make modal-deploy
```

Or directly:

```
modal deploy modal/qwen_app.py
modal deploy modal/os_atlas_app.py
```

Each command prints a URL like `https://<username>--sacmat-qwen-vl-serve.modal.run`.
Paste them into `.env`:

```
QWEN_BASE_URL=https://<username>--sacmat-qwen-vl-serve.modal.run/v1
OS_ATLAS_BASE_URL=https://<username>--sacmat-os-atlas-serve.modal.run/v1
```

The `/v1` suffix is required — vLLM's OpenAI server roots its routes there.

## Cost

Scale-to-zero + 120s idle timeout. Expect <$15 for the whole review window
running the 20-URL smoke set a handful of times. First request per model
triggers a ~3–5 minute cold start (model download + vLLM init). Subsequent
requests within the idle window are fast.

## Swapping in your own endpoints

Anything OpenAI-compatible works. Point `QWEN_BASE_URL` / `OS_ATLAS_BASE_URL`
at a local `vllm serve` instance, a Together.ai endpoint, or any other host
that speaks `/v1/chat/completions`. The worker's `vlm_client.py` uses the
`openai` SDK with `base_url` + `api_key`, so no code changes needed.

## Tearing down

```
modal app stop sacmat-qwen-vl
modal app stop sacmat-os-atlas
```
