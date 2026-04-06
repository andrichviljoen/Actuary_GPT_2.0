"""OpenAI-compatible AI assistant wrapper."""

from __future__ import annotations

import json
import os
from typing import Any


def is_ai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_prompt(context_payload: dict[str, Any], user_question: str) -> str:
    context_json = json.dumps(context_payload, indent=2)
    return (
        "You are an actuarial reserving assistant. Use only the JSON context and clearly state assumptions. "
        "This is advisory and not a substitute for actuarial judgment.\n\n"
        f"Context JSON:\n{context_json}\n\n"
        f"Question: {user_question}"
    )


def query_openai_compatible(context_payload: dict[str, Any], user_question: str) -> str:
    if not is_ai_enabled():
        return (
            "AI is disabled because OPENAI_API_KEY is not configured. "
            "The core reserving workflow remains fully functional."
        )

    from openai import OpenAI

    client = OpenAI()
    prompt = build_prompt(context_payload, user_question)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=prompt,
        temperature=0.2,
    )
    return response.output_text
