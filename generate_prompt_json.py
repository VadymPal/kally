#!/usr/bin/env python3
"""
Generate a JSON payload for image/game generation using OpenRouter.

Output JSON shape:
{
  "style": "<style description like 'cartoon', 'anime', 'sci‑fi'...>",
  "scenery": "<prompt describing the scenery>",
  "world_settings": "<setting like 'Ancient Egypt', 'Mesopotamian', ...>"
}

Usage:
  python generate_prompt_json.py [--model MODEL] [--seed N] [--out FILE]

Environment:
  OPENROUTER_API_KEY  Required.
  OPENROUTER_MODEL    Optional default model name (overridden by --model). Example: "meta-llama/llama-3.1-8b-instruct".

Notes:
- This script always uses OpenRouter and will error if no API key is configured.
- Minimal addition to repo: this single file; existing code remains untouched.
"""

import argparse
import json
import os
import random
import sys
from typing import Dict, Optional

import datetime

try:
    import requests  # type: ignore
except Exception:
    requests = None  # Fallback if requests isn't installed; local mode will still work.


STYLES = [
    "cartoon",
    "anime",
    "sci-fi",
    "fantasy",
    "cyberpunk",
    "steampunk",
    "pixel art",
    "watercolor",
    "oil painting",
    "low-poly",
    "isometric",
    "realistic",
    "noir",
    "surreal",
]

WORLD_SETTINGS = [
    "Ancient Egypt",
    "Mesopotamian",
    "Classical Greece",
    "Feudal Japan",
    "Viking Age Scandinavia",
    "Aztec Empire",
    "Mughal India",
    "Renaissance Italy",
    "Byzantine Empire",
    "Mayan Civilization",
    "Qin Dynasty China",
    "Cyberpunk Megacity",
    "Post-apocalyptic Wasteland",
    "High Fantasy Kingdom",
]

SCENERY_TEMPLATES = [
    "A bustling marketplace at dawn with vendors arranging wares, soft light filtering through awnings, and distant mountains.",
    "A tranquil lakeside under a star-filled sky, reflections shimmering, and lanterns floating across the water.",
    "A dense jungle ruin with creeping vines, broken statues, and sunbeams cutting through the canopy.",
    "A cliffside village with terraced farms, sea spray misting the air, and gulls circling above.",
    "An underground cavern with crystalline formations, bioluminescent fungi, and a subterranean river.",
    "A snow-covered citadel during a blizzard, banners whipping in the wind and warm light glowing from windows.",
    "A neon-drenched alleyway with holographic signs, rain-slick pavement, and bustling night traffic.",
    "A windswept desert with towering dunes, a caravan on the horizon, and heat haze wavering in the distance.",
    "A misty forest path with ancient trees, mossy stones, and faint will-o'-wisps hovering between roots.",
    "A cliffside temple at sunset, bells tolling softly as pilgrims ascend wide stone steps.",
]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def _openrouter_generate(model: str, seed: Optional[int]) -> Optional[Dict[str, str]]:
    api_key = OPENROUTER_API_KEY
    if not api_key:
        return None
    if requests is None:
        return None

    # Compose a compact but strict instruction to ensure JSON-only output.
    system_prompt = (
        "You are a generator for image prompts. Return only a compact JSON object with keys "
        "style, scenery, world_settings. No backticks, no prefix text. Styles must be simple labels "
        "like 'cartoon', 'anime', 'sci-fi', 'fantasy', etc. Scenery should be a vivid one-sentence "
        "description. world_settings should be a concise era/civilization or setting like 'Ancient Egypt' "
        "or 'Mesopotamian'."
    )

    # Give the model some randomized candidates to steer variety while keeping format strict.
    candidate_styles = ", ".join(random.sample(STYLES, k=min(6, len(STYLES))))
    candidate_worlds = ", ".join(
        random.sample(WORLD_SETTINGS, k=min(6, len(WORLD_SETTINGS)))
    )

    user_prompt = (
        f"""Randomly choose one style from: 
        [{candidate_styles}] and one world_settings from: [{candidate_worlds}]. """ +
        """Invent a vivid one-sentence scenery description that fits both. 
        Output strictly: \"style\": \"{style_prompt}\", 
\"scenery\": \"{scenery}\", 
\"world_setting\": \"{world_settings}\",
\"level_of_detail\": \"{level_of_detail}\", 
\"crowd_density\": \"{crowd_density}\", 
\"color_palette\": \"{color_palette}\""""
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional routing headers can be added if desired:
        # "HTTP-Referer": "https://your-site.example/",
        # "X-Title": "Kallie Prompt Generator",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,
        "response_format": {"type": "json_object"},
    }
    if seed is not None:
        # OpenRouter supports a seed field for some backends
        body["seed"] = int(seed)

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(body),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        )
        if not content:
            return None
        # Ensure strict JSON; if the model returned code fences, strip them
        if content.startswith("```") and content.endswith("```"):
            # Remove code fences commonly used by some models
            lines = [
                ln for ln in content.splitlines() if not ln.strip().startswith("```")
            ]
            content = "\n".join(lines).strip()
        parsed = json.loads(content)
        # Validate keys exist and are strings
        if not all(k in parsed for k in ("style", "scenery", "world_settings")):
            return None
        for k in ("style", "scenery", "world_settings"):
            if not isinstance(parsed[k], str):
                return None
        return parsed
    except Exception:
        return None


def generate_prompt(
    model: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, str]:
    """
    Programmatic API to generate a prompt JSON.

    Parameters:
    - model: OpenRouter model name. If None, uses env OPENROUTER_MODEL or default.
    - seed: Optional integer seed for determinism (passed to API when supported).

    Returns:
    - Dict with keys: style, scenery, world_settings.

    Example:
        from generate_prompt_json import generate_prompt
        data = generate_prompt(seed=42)
        # data -> {"style": "...", "scenery": "...", "world_settings": "..."}
    """
    if model is None:
        model = os.getenv("OPENROUTER_MODEL", "openrouter/auto")

    result: Optional[Dict[str, str]] = _openrouter_generate(model, seed)
    if result is None:
        raise RuntimeError(
            "OpenRouter generation failed or returned invalid response. Ensure OPENROUTER_API_KEY and model are set."
        )
    return result
