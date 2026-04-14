#!/usr/bin/env python3
"""Single-request probe against Qwen and OS-Atlas Modal endpoints."""
import base64
import os
import sys
from pathlib import Path

from openai import OpenAI

QWEN_BASE_URL = os.environ["QWEN_BASE_URL"]
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "token-abc123")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")

OS_ATLAS_BASE_URL = os.environ["OS_ATLAS_BASE_URL"]
OS_ATLAS_API_KEY = os.environ.get("OS_ATLAS_API_KEY", "token-abc123")
OS_ATLAS_MODEL = os.environ.get("OS_ATLAS_MODEL", "OS-Copilot/OS-Atlas-Base-7B")


def probe(name, base_url, api_key, model, image_path, prompt):
    b = Path(image_path).read_bytes()
    url = "data:image/png;base64," + base64.b64encode(b).decode()
    client = OpenAI(base_url=base_url, api_key=api_key)
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": url}},
            {"type": "text", "text": prompt},
        ]}],
        max_tokens=256,
    )
    print(f"=== {name} ===\n{r.choices[0].message.content.strip()}\n")


def main():
    if len(sys.argv) < 2:
        print("usage: test_vlm.py <screenshot.png>", file=sys.stderr)
        sys.exit(1)
    img = sys.argv[1]
    probe("Qwen2.5-VL", QWEN_BASE_URL, QWEN_API_KEY, QWEN_MODEL, img,
          "Does this page contain a login form? Answer YES or NO.")
    probe("OS-Atlas", OS_ATLAS_BASE_URL, OS_ATLAS_API_KEY, OS_ATLAS_MODEL, img,
          "Return the bounding box of the login button as (x1, y1, x2, y2).")


if __name__ == "__main__":
    main()
