"""Configuration and model client factory for Agentic Verification Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env if present
load_dotenv()


def _resolve_openrouter_key() -> str:
    """Resolve OpenRouter API key from env or configs/secrets.yaml."""
    if os.getenv("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]

    # Check ai-agent-lab/configs/secrets.yaml
    possible_paths = [
        Path.cwd() / "configs" / "secrets.yaml",
        Path.cwd().parent / "configs" / "secrets.yaml",
        Path(__file__).resolve().parents[3] / "configs" / "secrets.yaml",
    ]
    for p in possible_paths:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    key = data.get("openrouter", {}).get("api_key")
                    if key and str(key).startswith("sk-or-"):
                        return str(key)
            except Exception:
                pass
    return ""


@dataclass
class EngineConfig:
    """Runtime configuration for LLM providers and verification thresholds."""

    provider: str = os.getenv("LLM_PROVIDER", "openrouter")
    openrouter_api_key: str = ""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    default_model: str = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.0
    max_tokens: int = 1500

    def __post_init__(self):
        if not self.openrouter_api_key:
            self.openrouter_api_key = _resolve_openrouter_key()


def get_model(config: EngineConfig | None = None, model_name: str | None = None) -> ChatOpenAI:
    """Instantiate a ChatOpenAI client routed through OpenRouter or direct provider."""
    cfg = config or EngineConfig()
    selected_model = model_name or cfg.default_model

    if cfg.provider == "openrouter":
        api_key = cfg.openrouter_api_key
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Please set it in your environment or configs/secrets.yaml."
            )
        return ChatOpenAI(
            model=selected_model,
            openai_api_key=api_key,
            openai_api_base=cfg.openrouter_base_url,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            default_headers={
                "HTTP-Referer": "https://github.com/iocfinc/agentic-verification-engine",
                "X-Title": "Agentic Verification Engine",
            },
        )
    else:
        api_key = cfg.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        return ChatOpenAI(
            model=selected_model,
            openai_api_key=api_key,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
