#!/usr/bin/env python3
"""Regenerate data/vlm_cache.json by running live VLM calls against all screenshots
in data/logingpt/screenshots/. Run this once after a clean pipeline execution
against the 20-URL smoke set to refresh the cache for cache_only mode."""
import base64
import hashlib
import json
import os
import re
from pathlib import Path

from openai import OpenAI

QWEN_BASE_URL = os.environ["QWEN_BASE_URL"]
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "token-abc123")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")

OS_ATLAS_BASE_URL = os.environ["OS_ATLAS_BASE_URL"]
OS_ATLAS_API_KEY = os.environ.get("OS_ATLAS_API_KEY", "token-abc123")
OS_ATLAS_MODEL = os.environ.get("OS_ATLAS_MODEL", "OS-Copilot/OS-Atlas-Base-7B")

SCREENSHOTS = Path(os.environ.get("SCREENSHOTS_DIR", "data/logingpt/screenshots"))
OUT = Path(os.environ.get("VLM_CACHE_PATH", "data/vlm_cache.json"))

QWEN_PROMPT = "Does this page contain a login form? Answer YES or NO."
OS_ATLAS_PROMPT = "Return the bounding box of the login button as (x1, y1, x2, y2)."


def key(img_bytes, prompt):
    return hashlib.sha256(img_bytes).hexdigest() + ":" + hashlib.sha256(prompt.encode()).hexdigest()[:16]


def classify(client, img_url):
    r = client.chat.completions.create(
        model=QWEN_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": img_url}},
            {"type": "text", "text": QWEN_PROMPT},
        ]}],
        max_tokens=256,
    )
    text = r.choices[0].message.content.strip()
    m = re.findall(r"\b(YES|NO)\b", text, re.IGNORECASE)
    return bool(m and m[-1].upper() == "YES")


def ground(client, img_url):
    r = client.chat.completions.create(
        model=OS_ATLAS_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": img_url}},
            {"type": "text", "text": OS_ATLAS_PROMPT},
        ]}],
        max_tokens=256,
    )
    text = r.choices[0].message.content.strip()
    m = re.search(r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return [(x1 + x2) // 2, (y1 + y2) // 2]


def main():
    cache = {}
    qwen = OpenAI(base_url=QWEN_BASE_URL, api_key=QWEN_API_KEY)
    atlas = OpenAI(base_url=OS_ATLAS_BASE_URL, api_key=OS_ATLAS_API_KEY)
    for png in SCREENSHOTS.rglob("*.png"):
        b = png.read_bytes()
        url = "data:image/png;base64," + base64.b64encode(b).decode()
        cache[key(b, QWEN_PROMPT)] = classify(qwen, url)
        cache[key(b, OS_ATLAS_PROMPT)] = ground(atlas, url)
        print(f"cached {png}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cache, indent=2))
    print(f"wrote {len(cache)} entries to {OUT}")


if __name__ == "__main__":
    main()
