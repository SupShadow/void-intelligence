"""
void_intelligence.adapters --- Zero-dependency model adapters.

Uses only Python stdlib:
  urllib.request for Ollama REST API
  subprocess for CLI tools (Gemini, Codex)
  json for parsing

Adapter contract: fn(prompt: str, system: str = "") -> str

Usage:
    from void_intelligence.adapters import detect_available, build_available_adapters

    available = detect_available()
    # {"ollama": ["qwen3:14b", ...], "gemini": ["gemini-3.1-pro-preview"]}

    adapters = build_available_adapters()
    for name, (fn, meta) in adapters.items():
        response = fn("Hello, world!", "You are helpful.")
        print(f"{name}: {response[:80]}")
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Callable


# Type alias matching proof.py and router.py convention
ModelFn = Callable[[str, str], str]

# Strip <think>...</think> from reasoning models (deepseek-r1, qwen3)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


# ── Detection ──────────────────────────────────────────────────

def detect_ollama(timeout: float = 3.0) -> list[str]:
    """Return list of available Ollama model names, or [] if not running."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def detect_gemini() -> bool:
    """Check if Gemini CLI is available on PATH."""
    return shutil.which("gemini") is not None


def detect_codex() -> bool:
    """Check if Codex CLI is available on PATH."""
    return shutil.which("codex") is not None


def detect_available() -> dict[str, list[str]]:
    """Auto-detect all available providers and models.

    Returns:
        {"ollama": ["qwen3:14b", ...], "gemini": [...], "codex": [...]}
    """
    result: dict[str, list[str]] = {}

    ollama_models = detect_ollama()
    if ollama_models:
        result["ollama"] = [m for m in ollama_models if "embed" not in m]

    if detect_gemini():
        result["gemini"] = ["gemini-3.1-pro-preview", "gemini-3-flash-preview"]

    if detect_codex():
        result["codex"] = ["codex"]

    return result


# ── Ollama Adapter ──────────────────────────────────────────────

def make_ollama(
    model: str = "qwen3:14b",
    timeout: int = 120,
    max_tokens: int = 512,
    temperature: float = 0.0,
    base_url: str = "http://localhost:11434",
) -> ModelFn:
    """Create Ollama adapter using REST API. Zero dependencies.

    Uses /api/generate with stream=False.
    Strips <think>...</think> from reasoning models.
    """
    def call(prompt: str, system: str = "") -> str:
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                response = data.get("response", "")
                # Strip thinking blocks from reasoning models
                response = _THINK_RE.sub("", response)
                return response.strip()
        except urllib.error.URLError as e:
            raise ConnectionError(f"Ollama ({model}): {e}") from e
        except Exception as e:
            raise RuntimeError(f"Ollama ({model}): {e}") from e

    call.__name__ = f"ollama:{model}"  # type: ignore[attr-defined]
    return call


# ── Gemini CLI Adapter ──────────────────────────────────────────

def make_gemini(
    model: str = "gemini-3.1-pro-preview",
    timeout: int = 120,
) -> ModelFn:
    """Create Gemini CLI adapter using subprocess.

    System prompt is prepended to user prompt (CLI has no --system flag).
    """
    # Use the actual binary, not shell alias
    gemini_path = shutil.which("gemini") or "/opt/homebrew/bin/gemini"

    def call(prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            result = subprocess.run(
                [gemini_path, "-m", model, full_prompt],
                capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode != 0 and result.stderr:
                raise RuntimeError(f"Gemini ({model}): {result.stderr[:200]}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Gemini ({model}): timeout after {timeout}s")

    call.__name__ = f"gemini:{model}"  # type: ignore[attr-defined]
    return call


# ── Codex CLI Adapter ──────────────────────────────────────────

def make_codex(
    model: str = "codex",
    timeout: int = 120,
) -> ModelFn:
    """Create Codex CLI adapter using subprocess.

    No system prompt support -- prepended to user prompt.
    """
    codex_path = shutil.which("codex") or "/opt/homebrew/bin/codex"

    def call(prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            result = subprocess.run(
                [codex_path, "exec", full_prompt],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Codex ({model}): timeout after {timeout}s")

    call.__name__ = f"codex:{model}"  # type: ignore[attr-defined]
    return call


# ── Model Registry ──────────────────────────────────────────────

# display_name -> metadata (used by build_adapter and run_real_benchmark)
MODEL_REGISTRY: dict[str, dict] = {
    # Ollama (free, local, private)
    "qwen3-14b":        {"provider": "ollama", "model_id": "qwen3:14b",           "is_local": True,  "cost_per_m": 0.0},
    "qwen3-8b":         {"provider": "ollama", "model_id": "qwen3:latest",        "is_local": True,  "cost_per_m": 0.0},
    "qwen3-1.7b":       {"provider": "ollama", "model_id": "qwen3:1.7b",          "is_local": True,  "cost_per_m": 0.0},
    "qwen2.5-7b":       {"provider": "ollama", "model_id": "qwen2.5:7b",          "is_local": True,  "cost_per_m": 0.0},
    "qwen2.5-coder-3b": {"provider": "ollama", "model_id": "qwen2.5-coder:3b",    "is_local": True,  "cost_per_m": 0.0},
    "mistral-7b":       {"provider": "ollama", "model_id": "mistral:latest",       "is_local": True,  "cost_per_m": 0.0},
    "phi4-14b":         {"provider": "ollama", "model_id": "phi4:latest",          "is_local": True,  "cost_per_m": 0.0},
    "deepseek-r1-14b":  {"provider": "ollama", "model_id": "deepseek-r1:14b",     "is_local": True,  "cost_per_m": 0.0},
    "deepseek-r1-8b":   {"provider": "ollama", "model_id": "deepseek-r1:8b",      "is_local": True,  "cost_per_m": 0.0},
    "glm4-9b":          {"provider": "ollama", "model_id": "glm4:latest",          "is_local": True,  "cost_per_m": 0.0},
    # Gemini CLI (free via subscription)
    "gemini-3.1-pro":   {"provider": "gemini", "model_id": "gemini-3.1-pro-preview", "is_local": False, "cost_per_m": 3.5},
    "gemini-3-flash":   {"provider": "gemini", "model_id": "gemini-3-flash-preview", "is_local": False, "cost_per_m": 0.1},
}


def build_adapter(name: str) -> tuple[ModelFn, dict]:
    """Build adapter for a registered model. Returns (fn, metadata)."""
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}. Available: {list(MODEL_REGISTRY.keys())}")

    meta = MODEL_REGISTRY[name]
    provider = meta["provider"]
    model_id = meta["model_id"]

    if provider == "ollama":
        return make_ollama(model_id), meta
    elif provider == "gemini":
        return make_gemini(model_id), meta
    elif provider == "codex":
        return make_codex(model_id), meta
    else:
        raise ValueError(f"Unknown provider: {provider}")


def build_available_adapters(
    model_filter: str = "",
    ollama_only: bool = False,
) -> dict[str, tuple[ModelFn, dict]]:
    """Build adapters for all available models.

    Auto-detects running providers, filters by availability.
    Returns {display_name: (adapter_fn, metadata)}.
    """
    available = detect_available()
    ollama_models = set(available.get("ollama", []))
    has_gemini = "gemini" in available
    has_codex = "codex" in available

    result: dict[str, tuple[ModelFn, dict]] = {}

    for name, meta in MODEL_REGISTRY.items():
        if model_filter and model_filter.lower() not in name.lower():
            continue
        if ollama_only and meta["provider"] != "ollama":
            continue

        provider = meta["provider"]
        model_id = meta["model_id"]

        if provider == "ollama" and model_id not in ollama_models:
            continue
        if provider == "gemini" and not has_gemini:
            continue
        if provider == "codex" and not has_codex:
            continue

        try:
            fn, _ = build_adapter(name)
            result[name] = (fn, meta)
        except Exception:
            continue

    return result


# ── Self-Tests ──────────────────────────────────────────────────

def _self_test() -> int:
    """Run inline tests. Returns (passed, total)."""
    passed = total = 0

    def ok(name: str, condition: bool):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"    OK   {name}")
        else:
            print(f"    FAIL {name}")

    print("  adapters.py self-test:")

    # Detection functions exist
    ok("detect_ollama returns list", isinstance(detect_ollama(timeout=1), list))
    ok("detect_gemini returns bool", isinstance(detect_gemini(), bool))
    ok("detect_codex returns bool", isinstance(detect_codex(), bool))
    ok("detect_available returns dict", isinstance(detect_available(), dict))

    # Registry
    ok("MODEL_REGISTRY has entries", len(MODEL_REGISTRY) >= 10)
    ok("All entries have provider", all("provider" in v for v in MODEL_REGISTRY.values()))
    ok("All entries have model_id", all("model_id" in v for v in MODEL_REGISTRY.values()))
    ok("All entries have is_local", all("is_local" in v for v in MODEL_REGISTRY.values()))
    ok("All entries have cost_per_m", all("cost_per_m" in v for v in MODEL_REGISTRY.values()))

    # Think stripping
    ok("Think strip empty", _THINK_RE.sub("", "hello") == "hello")
    ok("Think strip basic", _THINK_RE.sub("", "<think>foo</think>bar").strip() == "bar")
    ok("Think strip multiline", _THINK_RE.sub("", "<think>\nlong\nthought\n</think>answer").strip() == "answer")
    ok("Think strip preserves rest", _THINK_RE.sub("", "pre <think>x</think> post").strip() == "pre  post")

    # Adapter construction (may fail if providers not available)
    ok("build_adapter unknown raises", _safe_raises(lambda: build_adapter("nonexistent")))

    # build_available_adapters with impossible filter returns empty
    result = build_available_adapters(model_filter="zzz_impossible_zzz")
    ok("Impossible filter returns empty", len(result) == 0)

    # Ollama adapter construction (if available)
    ollama_models = detect_ollama(timeout=2)
    if ollama_models:
        try:
            fn = make_ollama(ollama_models[0], timeout=10)
            ok("make_ollama returns callable", callable(fn))
            # Quick test call
            resp = fn("Say only the word 'ok'.", "")
            ok("Ollama responds", len(resp) > 0)
            ok("Ollama response is string", isinstance(resp, str))
        except Exception as e:
            ok(f"Ollama adapter creation ({e})", False)
    else:
        ok("Ollama not running (skip live tests)", True)

    # Gemini adapter construction
    if detect_gemini():
        ok("make_gemini returns callable", callable(make_gemini()))
    else:
        ok("Gemini not installed (skip)", True)

    # build_available_adapters integration
    all_adapters = build_available_adapters(ollama_only=True)
    ok("build_available returns dict", isinstance(all_adapters, dict))
    if all_adapters:
        _name, (_fn, _meta) = next(iter(all_adapters.items()))
        ok("Adapter tuple has fn", callable(_fn))
        ok("Adapter tuple has meta", isinstance(_meta, dict))
        ok("Meta has provider", "provider" in _meta)

    print(f"\n    {passed}/{total} adapters tests passed.")
    return passed


def _safe_raises(fn) -> bool:
    """Return True if fn() raises an exception."""
    try:
        fn()
        return False
    except Exception:
        return True


if __name__ == "__main__":
    _self_test()
