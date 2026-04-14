import subprocess

import modal

app = modal.App("sacmat-qwen-vl")

MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
API_KEY = "token-abc123"
PORT = 8000

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.3.post1",
        "huggingface_hub[hf_transfer]==0.26.2",
        "transformers==4.45.2",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache = modal.Volume.from_name("sacmat-hf-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="L40S",
    volumes={"/root/.cache/huggingface": hf_cache},
    timeout=30 * 60,
    container_idle_timeout=120,
    allow_concurrent_inputs=10,
)
@modal.web_server(port=PORT, startup_timeout=10 * 60)
def serve():
    subprocess.Popen([
        "vllm", "serve", MODEL,
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--api-key", API_KEY,
        "--max-model-len", "8192",
        "--gpu-memory-utilization", "0.90",
        "--trust-remote-code",
    ])
