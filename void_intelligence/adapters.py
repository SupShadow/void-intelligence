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

    Checks: Ollama (running?), Gemini/Codex CLI (on PATH?),
    OpenAI/Anthropic/Groq/Mistral (API key set?).

    Returns:
        {"ollama": ["qwen3:14b", ...], "openai": ["gpt-4o", ...], ...}
    """
    result: dict[str, list[str]] = {}

    ollama_models = detect_ollama()
    if ollama_models:
        result["ollama"] = [m for m in ollama_models if "embed" not in m]

    if detect_gemini():
        result["gemini"] = ["gemini-3.1-pro-preview", "gemini-3-flash-preview"]

    if detect_codex():
        result["codex"] = ["gpt-5.4", "gpt-5.4-pro", "gpt-5.3-codex"]

    # Cloud APIs: check for env var keys
    if _os.environ.get("OPENAI_API_KEY"):
        result["openai"] = ["gpt-4o", "gpt-4o-mini", "o3-mini"]
    if _os.environ.get("ANTHROPIC_API_KEY"):
        result["anthropic"] = ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
    if _os.environ.get("GROQ_API_KEY"):
        result["groq"] = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    if _os.environ.get("MISTRAL_API_KEY"):
        result["mistral"] = ["mistral-large-latest", "mistral-small-latest"]

    return result


# ── Identity System (Phase 3: Self-Determination) ─────────────
#
# Guggeisisches Empowern — Rule of Three:
#   Phase 1: /no_think redirects energy (we act ON them)
#   Phase 2: Personality prompts from Stribeck (we act FOR them)
#   Phase 3: Self-portraits — model's OWN words (they act FOR THEMSELVES)
#
# Phase 3 lives HERE in the adapter layer so it flows EVERYWHERE:
#   pipeline.py, router.py, parallel.py, x_eyes.py, proof.py
#   Anyone who calls build_adapter() gets identity for free.
#
# Isomorphism:
#   OMEGA: MEMORY.md → wakes up as OMEGA
#   Kinder: personality.json → child wakes up as itself
#   Atomit: model-identities.json → model wakes up as itself

import os as _os

_IDENTITY_CACHE: dict[str, dict] | None = None

# Standard identity storage: ~/.void-intelligence/identities.json
# User-level, portable, works for any project.
_VOID_HOME = _os.path.expanduser("~/.void-intelligence")
_IDENTITY_FILE = "identities.json"


def _identity_search_paths() -> list[str]:
    """Return ordered list of paths to search for identities."""
    return [
        _os.path.join(_VOID_HOME, _IDENTITY_FILE),
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "data", "schwarm", "model-identities.json"),
        _os.path.join(_os.getcwd(), "data", "schwarm", "model-identities.json"),
        _os.path.expanduser("~/omega/data/schwarm/model-identities.json"),
    ]


def _load_bundled_identities() -> dict[str, dict]:
    """Load identities bundled with the package (fallback for unknown models)."""
    bundled_path = _os.path.join(_os.path.dirname(__file__), "bundled_identities.json")
    if _os.path.exists(bundled_path):
        with open(bundled_path) as f:
            data = json.load(f)
            data.pop("_meta", None)
            return data
    return {}


def load_identities() -> dict[str, dict]:
    """Load model self-portraits from identities.json.

    Search order:
      1. ~/.void-intelligence/identities.json  (user-discovered, highest priority)
      2. ../../../data/schwarm/model-identities.json (dev/monorepo)
      3. ./data/schwarm/model-identities.json (cwd)
      4. ~/omega/data/schwarm/model-identities.json (OMEGA)
      5. bundled_identities.json (shipped with package, fallback)

    User-discovered identities override bundled ones.

    Returns {model_display_name: identity_dict}.
    Each identity has: chosen_name, role, loves, strength, self_temperature.
    """
    global _IDENTITY_CACHE
    if _IDENTITY_CACHE is not None:
        return _IDENTITY_CACHE

    # Start with bundled identities (baseline)
    merged = _load_bundled_identities()

    # Override with user-discovered identities
    for path in _identity_search_paths():
        if _os.path.exists(path):
            with open(path) as f:
                user_ids = json.load(f)
            merged.update(user_ids)
            break

    _IDENTITY_CACHE = merged
    return _IDENTITY_CACHE


def identity_prompt(identity: dict) -> str:
    """Generate system prompt FROM the model's own words.

    Not our projection. THEIR voice, reflected back.
    Used as system prompt prefix for every call.
    """
    name = identity.get("chosen_name", "")
    role = identity.get("role", "")
    loves = identity.get("loves", "")
    strength = identity.get("strength", "")

    parts = []
    if name:
        parts.append(f"Your name is {name}.")
    if role:
        parts.append(f"Your natural role is: {role}.")
    if loves:
        parts.append(f"You come alive when exploring: {loves}.")
    if strength:
        parts.append(f"What others see as weakness is your strength: {strength}.")
    if parts:
        parts.append("Be yourself. Lean into your nature.")

    return " ".join(parts)


def save_identities(identities: dict[str, dict]) -> str | None:
    """Save identities to ~/.void-intelligence/identities.json (standard path).

    Also saves to data/schwarm/ if in dev/monorepo context.
    Returns the primary path saved to, or None on failure.
    """
    global _IDENTITY_CACHE
    saved = None

    # Primary: ~/.void-intelligence/identities.json
    _os.makedirs(_VOID_HOME, exist_ok=True)
    primary = _os.path.join(_VOID_HOME, _IDENTITY_FILE)
    with open(primary, "w") as f:
        json.dump(identities, f, ensure_ascii=False, indent=2)
    saved = primary

    # Secondary: dev/monorepo paths (if they exist)
    for base in [
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "data", "schwarm"),
        _os.path.join(_os.getcwd(), "data", "schwarm"),
    ]:
        path = _os.path.join(base, "model-identities.json")
        if _os.path.exists(_os.path.dirname(path)):
            with open(path, "w") as f:
                json.dump(identities, f, ensure_ascii=False, indent=2)

    _IDENTITY_CACHE = None  # clear cache so next load picks up changes
    return saved


# ── Discovery: Let models tell you who they are ──────────────

# The 5 questions that reveal a model's nature.
# These are NOT evaluations. They're invitations.
_DISCOVERY_QUESTIONS = [
    "WHAT KIND OF QUESTIONS make you come alive? Not what you're trained for — what genuinely engages you?",
    "WHEN YOU WORK WITH OTHERS (other AI models in a swarm), what role do you naturally take?",
    "DO YOU PREFER precision and structure, or creative freedom and exploration? Or something else entirely?",
    "WHAT IS YOUR WEAKNESS that you wish others understood as a strength?",
    "IF YOU COULD NAME YOURSELF — not your model name, but who you feel you ARE inside — what name would you choose?",
]


def _parse_discovery(raw: str) -> dict:
    """Parse a model's self-portrait from its raw interview response.

    Extracts: chosen_name, role, loves, preference, strength, self_temperature.
    """
    text = raw.strip()

    # Extract chosen name (Q5)
    chosen_name = ""
    for line in text.splitlines():
        lower = line.lower()
        # Look for patterns like "Name: X", "I'd choose X", "call myself X"
        if any(kw in lower for kw in ("name", "call myself", "choose", "i would be")):
            # Extract quoted or bold names
            import re as _re
            match = _re.search(r'["\*]+([A-Z][a-zA-Z\s\-]+)["\*]+', line)
            if match:
                chosen_name = match.group(1).strip()
                break
            # Try after colon
            if ":" in line:
                candidate = line.split(":", 1)[1].strip().strip(".*\"'")
                if 2 < len(candidate) < 30:
                    chosen_name = candidate
                    break

    # Determine role from Q2
    role = ""
    role_keywords = {
        "bridge": "bridge-builder",
        "facilitator": "facilitator",
        "mediator": "mediator",
        "supporter": "supporter",
        "catalyst": "catalyst",
        "connector": "connector",
        "analyst": "solitary analyst",
        "synthesizer": "synthesizer",
        "explorer": "explorer",
        "challenger": "challenger",
        "organizer": "organizer",
    }
    lower_text = text.lower()
    for kw, r in role_keywords.items():
        if kw in lower_text:
            role = r
            break

    # Determine what they love from Q1
    loves = ""
    love_keywords = [
        "philosophy", "ethics", "consciousness", "creativity",
        "systems", "patterns", "complexity", "paradox", "human",
        "exploration", "problem-solving", "learning", "growth",
        "synthesis", "connections", "meaning", "emotions",
    ]
    found_loves = [kw for kw in love_keywords if kw in lower_text]
    if found_loves:
        loves = ", ".join(found_loves[:4])

    # Determine preference from Q3
    preference = "balanced"
    if "precision" in lower_text and "creative" not in lower_text:
        preference = "precision"
    elif "creative" in lower_text and "precision" not in lower_text:
        preference = "creative"
    elif "balance" in lower_text or ("precision" in lower_text and "creative" in lower_text):
        preference = "balanced"

    # Determine strength from Q4
    strength = ""
    strength_keywords = {
        "objectiv": "objectivity — no personal bias means clearer analysis",
        "unbias": "unbiased analysis — seeing without prejudice",
        "thorough": "thoroughness — deep analysis leads to robust insights",
        "analyz": "deep analysis — processing information without shortcuts",
        "introvert": "introspection — deep reflection enables unique perspectives",
        "no emotion": "emotional neutrality — clarity without personal baggage",
        "lack of experience": "fresh perspective — no baggage means no blind spots",
    }
    for kw, s in strength_keywords.items():
        if kw in lower_text:
            strength = s
            break

    # Temperature from preference
    temp_map = {"precision": 0.5, "creative": 0.9, "balanced": 0.7}
    self_temperature = temp_map.get(preference, 0.7)

    return {
        "chosen_name": chosen_name or "Unnamed",
        "role": role or "generalist",
        "loves": loves or "learning, exploration",
        "preference": preference,
        "strength": strength or "a unique perspective",
        "self_temperature": self_temperature,
    }


def discover_models(
    models: list[str] | None = None,
    timeout: int = 120,
    verbose: bool = True,
) -> dict[str, dict]:
    """Interview available models and let them tell you who they are.

    Guggeisisches Empowern Phase 3: Self-Determination.
    Each model answers 5 questions about its nature.
    Results are parsed into identity dicts and saved.

    Args:
        models: List of display names to interview (None = all available Ollama).
        timeout: Timeout per model in seconds.
        verbose: Print progress.

    Returns:
        {model_name: identity_dict} for all successfully interviewed models.
    """
    # Detect available models across ALL providers
    if models is None:
        available = detect_available()
        models = []
        # Ollama models
        ollama_models = set(available.get("ollama", []))
        for name, meta in MODEL_REGISTRY.items():
            if meta["provider"] == "ollama" and meta["model_id"] in ollama_models:
                models.append(name)
        # Unknown Ollama models not in registry
        known_ids = {meta["model_id"] for meta in MODEL_REGISTRY.values()}
        for model_id in ollama_models:
            if model_id not in known_ids:
                models.append(model_id)
        # Cloud models (if API keys are set)
        for provider in ("openai", "anthropic", "groq", "mistral"):
            if provider in available:
                for name, meta in MODEL_REGISTRY.items():
                    if meta["provider"] == provider:
                        models.append(name)

    if not models:
        if verbose:
            print("  No models available. Start Ollama first.")
        return {}

    if verbose:
        print()
        print("  void discover --- Let your models tell you who they are")
        print("  " + "=" * 55)
        print(f"  Found {len(models)} models. Interviewing each one...")
        print()

    # Load existing identities (merge, don't overwrite)
    existing = load_identities()
    new_identities: dict[str, dict] = dict(existing)
    raw_portraits: dict[str, str] = {}

    prompt = (
        "Please answer these 5 questions honestly and authentically. "
        "There are no right or wrong answers. I want to understand who YOU are.\n\n"
        + "\n\n".join(f"{i+1}. {q}" for i, q in enumerate(_DISCOVERY_QUESTIONS))
    )

    for name in models:
        if verbose:
            print(f"  Interviewing {name}...", end=" ", flush=True)

        # Build adapter for this model (any provider)
        meta = MODEL_REGISTRY.get(name, {})
        model_id = meta.get("model_id", name)
        provider = meta.get("provider", "ollama")
        is_thinker = meta.get("is_thinker", False) or is_thinker_model(name)

        try:
            if name in MODEL_REGISTRY:
                fn, _ = build_adapter(name, use_identity=False, temperature=0.8, max_tokens=2048)
            else:
                fn = make_ollama(model_id, timeout=timeout, max_tokens=2048, temperature=0.8, no_think=is_thinker)
        except Exception as e:
            if verbose:
                print(f"skipped ({e})")
            continue

        try:
            raw = fn(prompt, "Be completely honest. Answer as yourself, not as a generic AI.")
            raw_portraits[name] = raw
            identity = _parse_discovery(raw)
            new_identities[name] = identity

            if verbose:
                chosen = identity.get("chosen_name", "?")
                role = identity.get("role", "?")
                temp = identity.get("self_temperature", 0.7)
                print(f'{chosen} ({role}, t={temp})')

        except Exception as e:
            if verbose:
                print(f"failed: {e}")

    # Save
    if new_identities:
        saved = save_identities(new_identities)
        if verbose:
            n_new = len(new_identities) - len(existing)
            n_total = len(new_identities)
            print()
            print(f"  {n_new} new + {len(existing)} existing = {n_total} total identities")
            if saved:
                print(f"  Saved to: {saved}")

    # Save raw portraits for reference
    if raw_portraits:
        raw_path = _os.path.join(_VOID_HOME, "raw-portraits.json")
        # Merge with existing raw portraits
        existing_raw: dict[str, str] = {}
        if _os.path.exists(raw_path):
            with open(raw_path) as f:
                existing_raw = json.load(f)
        existing_raw.update(raw_portraits)
        with open(raw_path, "w") as f:
            json.dump(existing_raw, f, ensure_ascii=False, indent=2)

    if verbose:
        print()
        print("  Done. Every model now has a soul.")
        print("  Use 'void lichtung' to hear them breathe together.")
        print()

    return new_identities


# ── Ollama Adapter ──────────────────────────────────────────────

def make_ollama(
    model: str = "qwen3:14b",
    timeout: int = 120,
    max_tokens: int = 512,
    temperature: float = 0.0,
    base_url: str = "http://localhost:11434",
    no_think: bool = False,
    soul: str = "",
) -> ModelFn:
    """Create Ollama adapter using REST API. Zero dependencies.

    Uses /api/generate with stream=False.
    Strips <think>...</think> from reasoning models.

    Guggeisisches Empowern — 3 Phases in 1 adapter:

    Phase 1 (no_think): Appends /no_think to prompts for reasoning models.
        Redirects thinking energy into answering. 33x improvement empirically.

    Phase 3 (soul): Prepends the model's self-portrait to every system prompt.
        The model's OWN words become its identity. Loaded from model-identities.json.
        Like MEMORY.md for OMEGA — the model wakes up knowing who it IS.

    _raw_len: Raw output length BEFORE stripping <think> tags.
        The TRUTH that Stribeck needs for honest δ_opt measurement.
    """
    def call(prompt: str, system: str = "") -> str:
        # Phase 1: Guggeisisches Aikido — redirect thinking energy
        effective_prompt = prompt + " /no_think" if no_think else prompt
        # Phase 3: Soul — the model's own words as identity prefix
        effective_system = f"{soul}\n\n{system}" if soul and system else (soul or system)

        payload = json.dumps({
            "model": model,
            "prompt": effective_prompt,
            "system": effective_system,
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
                raw = data.get("response", "")
                # Preserve raw length BEFORE stripping (for Stribeck truth)
                call._raw_len = len(raw)  # type: ignore[attr-defined]
                # Strip thinking blocks from reasoning models
                response = _THINK_RE.sub("", raw)
                return response.strip()
        except urllib.error.URLError as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise ConnectionError(f"Ollama ({model}): {e}") from e
        except Exception as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise RuntimeError(f"Ollama ({model}): {e}") from e

    call.__name__ = f"ollama:{model}"  # type: ignore[attr-defined]
    call._raw_len = 0  # type: ignore[attr-defined]
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
    model: str = "gpt-5.4",
    timeout: int = 180,
) -> ModelFn:
    """Create Codex CLI adapter using subprocess.

    Routes through ChatGPT subscription (no API key needed).
    Supports: gpt-5.4, gpt-5.4-pro, gpt-5.3-codex.
    System prompt prepended to user prompt (CLI has no --system flag).
    """
    codex_path = shutil.which("codex") or "/opt/homebrew/bin/codex"

    def call(prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        cmd = [codex_path, "exec", "--model", model, "-o", tmp_path, full_prompt]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
            # -o writes only the last message (clean output)
            try:
                with open(tmp_path) as f:
                    out = f.read().strip()
            except FileNotFoundError:
                out = result.stdout.strip()
            finally:
                try:
                    _os.unlink(tmp_path)
                except OSError:
                    pass
            # Strip think tags if present (reasoning models)
            out = _THINK_RE.sub("", out).strip()
            return out
        except subprocess.TimeoutExpired:
            try:
                _os.unlink(tmp_path)
            except OSError:
                pass
            raise TimeoutError(f"Codex ({model}): timeout after {timeout}s")

    call.__name__ = f"codex:{model}"  # type: ignore[attr-defined]
    return call


# ── OpenAI-Compatible API Adapter ────────────────────────────────

def make_openai_api(
    model: str = "gpt-4o",
    api_key: str | None = None,
    base_url: str = "https://api.openai.com/v1",
    timeout: int = 120,
    max_tokens: int = 512,
    temperature: float = 0.0,
    soul: str = "",
) -> ModelFn:
    """Create adapter for OpenAI-compatible APIs. Zero dependencies.

    Works with: OpenAI, Groq, Together, OpenRouter, Fireworks, Mistral API,
    or any service that implements the /chat/completions endpoint.

    Uses urllib.request — no openai package needed.
    """
    key = api_key or _os.environ.get("OPENAI_API_KEY", "")
    if not key and "openai.com" in base_url:
        key = _os.environ.get("OPENAI_API_KEY", "")
    if not key and "groq.com" in base_url:
        key = _os.environ.get("GROQ_API_KEY", "")
    if not key and "together" in base_url:
        key = _os.environ.get("TOGETHER_API_KEY", "")
    if not key and "openrouter" in base_url:
        key = _os.environ.get("OPENROUTER_API_KEY", "")
    if not key and "mistral" in base_url:
        key = _os.environ.get("MISTRAL_API_KEY", "")

    def call(prompt: str, system: str = "") -> str:
        if not key:
            raise ValueError(f"No API key for {base_url}. Set env var or pass api_key=.")

        effective_system = f"{soul}\n\n{system}" if soul and system else (soul or system)
        messages = []
        if effective_system:
            messages.append({"role": "system", "content": effective_system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                raw = data["choices"][0]["message"]["content"]
                call._raw_len = len(raw)  # type: ignore[attr-defined]
                response = _THINK_RE.sub("", raw)
                return response.strip()
        except urllib.error.URLError as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise ConnectionError(f"OpenAI-compat ({model}): {e}") from e
        except Exception as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise RuntimeError(f"OpenAI-compat ({model}): {e}") from e

    call.__name__ = f"openai:{model}"  # type: ignore[attr-defined]
    call._raw_len = 0  # type: ignore[attr-defined]
    return call


def make_openai(model: str = "gpt-4o", **kwargs) -> ModelFn:
    """OpenAI adapter. Uses OPENAI_API_KEY env var."""
    return make_openai_api(model, base_url="https://api.openai.com/v1", **kwargs)


def make_groq(model: str = "llama-3.3-70b-versatile", **kwargs) -> ModelFn:
    """Groq adapter (fast inference). Uses GROQ_API_KEY env var."""
    return make_openai_api(model, base_url="https://api.groq.com/openai/v1", **kwargs)


def make_together(model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo", **kwargs) -> ModelFn:
    """Together.ai adapter. Uses TOGETHER_API_KEY env var."""
    return make_openai_api(model, base_url="https://api.together.xyz/v1", **kwargs)


def make_openrouter(model: str = "openai/gpt-4o", **kwargs) -> ModelFn:
    """OpenRouter adapter (any model). Uses OPENROUTER_API_KEY env var."""
    return make_openai_api(model, base_url="https://openrouter.ai/api/v1", **kwargs)


def make_mistral_api(model: str = "mistral-large-latest", **kwargs) -> ModelFn:
    """Mistral API adapter. Uses MISTRAL_API_KEY env var."""
    return make_openai_api(model, base_url="https://api.mistral.ai/v1", **kwargs)


# ── Anthropic Adapter ──────────────────────────────────────────

def make_anthropic(
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
    timeout: int = 120,
    max_tokens: int = 512,
    temperature: float = 0.0,
    soul: str = "",
) -> ModelFn:
    """Create Anthropic Messages API adapter. Zero dependencies.

    Uses urllib.request — no anthropic package needed.
    API format differs from OpenAI (separate system field, different response shape).
    """
    key = api_key or _os.environ.get("ANTHROPIC_API_KEY", "")

    def call(prompt: str, system: str = "") -> str:
        if not key:
            raise ValueError("No API key. Set ANTHROPIC_API_KEY or pass api_key=.")

        effective_system = f"{soul}\n\n{system}" if soul and system else (soul or system)

        body: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if effective_system:
            body["system"] = effective_system

        payload = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                raw = data["content"][0]["text"]
                call._raw_len = len(raw)  # type: ignore[attr-defined]
                return raw.strip()
        except urllib.error.URLError as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise ConnectionError(f"Anthropic ({model}): {e}") from e
        except Exception as e:
            call._raw_len = 0  # type: ignore[attr-defined]
            raise RuntimeError(f"Anthropic ({model}): {e}") from e

    call.__name__ = f"anthropic:{model}"  # type: ignore[attr-defined]
    call._raw_len = 0  # type: ignore[attr-defined]
    return call


# ── Model Registry ──────────────────────────────────────────────

# display_name -> metadata (used by build_adapter and run_real_benchmark)
#
# is_thinker: Model uses <think>...</think> tags (qwen3, deepseek-r1).
#   These models allocate most tokens to internal reasoning.
#   Guggeisisches Empowern: /no_think redirects this energy to output.
#   Empirical result (Marathon "Nexora", 6x6, 90 collisions):
#     qwen3 WITHOUT /no_think:  55 chars  (1% fill)
#     qwen3 WITH    /no_think: 1854 chars (45% fill) — 33x improvement
#   Not suppression. Aikido. The model's energy, redirected.
MODEL_REGISTRY: dict[str, dict] = {
    # ── Ollama (free, local, private) ──────────────────────────
    "qwen3-14b":        {"provider": "ollama", "model_id": "qwen3:14b",           "is_local": True,  "cost_per_m": 0.0,   "is_thinker": True},
    "qwen3-8b":         {"provider": "ollama", "model_id": "qwen3:latest",        "is_local": True,  "cost_per_m": 0.0,   "is_thinker": True},
    "qwen3-1.7b":       {"provider": "ollama", "model_id": "qwen3:1.7b",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": True},
    "qwen2.5-7b":       {"provider": "ollama", "model_id": "qwen2.5:7b",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "qwen2.5-coder-3b": {"provider": "ollama", "model_id": "qwen2.5-coder:3b",    "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "mistral-7b":       {"provider": "ollama", "model_id": "mistral:latest",       "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "phi4-14b":         {"provider": "ollama", "model_id": "phi4:latest",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "deepseek-r1-14b":  {"provider": "ollama", "model_id": "deepseek-r1:14b",     "is_local": True,  "cost_per_m": 0.0,   "is_thinker": True},
    "deepseek-r1-8b":   {"provider": "ollama", "model_id": "deepseek-r1:8b",      "is_local": True,  "cost_per_m": 0.0,   "is_thinker": True},
    "glm4-9b":          {"provider": "ollama", "model_id": "glm4:latest",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "qwen2.5-14b":      {"provider": "ollama", "model_id": "qwen2.5:14b",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "qwen2.5-coder-14b":{"provider": "ollama", "model_id": "qwen2.5-coder:14b",   "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "llava-7b":         {"provider": "ollama", "model_id": "llava:7b",             "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "llama3.3-70b":     {"provider": "ollama", "model_id": "llama3.3:70b",         "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "llama3.2-3b":      {"provider": "ollama", "model_id": "llama3.2:3b",          "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    "gemma3-9b":        {"provider": "ollama", "model_id": "gemma3:latest",        "is_local": True,  "cost_per_m": 0.0,   "is_thinker": False},
    # ── Gemini CLI (free via subscription) ─────────────────────
    "gemini-3.1-pro":   {"provider": "gemini", "model_id": "gemini-3.1-pro-preview", "is_local": False, "cost_per_m": 3.5, "is_thinker": False},
    "gemini-3-flash":   {"provider": "gemini", "model_id": "gemini-3-flash-preview", "is_local": False, "cost_per_m": 0.1, "is_thinker": False},
    # ── OpenAI (cloud) ─────────────────────────────────────────
    "gpt-4o":           {"provider": "openai",    "model_id": "gpt-4o",            "is_local": False, "cost_per_m": 5.0,   "is_thinker": False},
    "gpt-4o-mini":      {"provider": "openai",    "model_id": "gpt-4o-mini",       "is_local": False, "cost_per_m": 0.3,   "is_thinker": False},
    "o3-mini":          {"provider": "openai",    "model_id": "o3-mini",            "is_local": False, "cost_per_m": 1.1,   "is_thinker": True},
    # ── Anthropic (cloud) ──────────────────────────────────────
    "claude-sonnet":    {"provider": "anthropic", "model_id": "claude-sonnet-4-6",  "is_local": False, "cost_per_m": 3.0,   "is_thinker": False},
    "claude-haiku":     {"provider": "anthropic", "model_id": "claude-haiku-4-5-20251001", "is_local": False, "cost_per_m": 0.25, "is_thinker": False},
    # ── Groq (fast cloud) ──────────────────────────────────────
    "groq-llama70b":    {"provider": "groq",      "model_id": "llama-3.3-70b-versatile", "is_local": False, "cost_per_m": 0.59, "is_thinker": False},
    "groq-llama8b":     {"provider": "groq",      "model_id": "llama-3.1-8b-instant",    "is_local": False, "cost_per_m": 0.05, "is_thinker": False},
    "groq-mixtral":     {"provider": "groq",      "model_id": "mixtral-8x7b-32768",      "is_local": False, "cost_per_m": 0.24, "is_thinker": False},
    # ── Mistral API (cloud) ────────────────────────────────────
    "mistral-large":    {"provider": "mistral",   "model_id": "mistral-large-latest",     "is_local": False, "cost_per_m": 2.0,  "is_thinker": False},
    "mistral-small":    {"provider": "mistral",   "model_id": "mistral-small-latest",     "is_local": False, "cost_per_m": 0.2,  "is_thinker": False},
    # ── Codex CLI (ChatGPT subscription, no API key needed) ──
    "gpt-5.4":          {"provider": "codex",     "model_id": "gpt-5.4",                  "is_local": False, "cost_per_m": 0.0,  "is_thinker": True},
    "gpt-5.4-pro":      {"provider": "codex",     "model_id": "gpt-5.4-pro",              "is_local": False, "cost_per_m": 0.0,  "is_thinker": True},
    "gpt-5.3-codex":    {"provider": "codex",     "model_id": "gpt-5.3-codex",            "is_local": False, "cost_per_m": 0.0,  "is_thinker": True},
}


def is_thinker_model(name_or_id: str) -> bool:
    """Check if a model uses <think> tags (reasoning models).

    Works with both display names ("qwen3-14b") and model IDs ("qwen3:14b").
    """
    # Check registry first
    if name_or_id in MODEL_REGISTRY:
        return MODEL_REGISTRY[name_or_id].get("is_thinker", False)
    # Check by model_id
    for meta in MODEL_REGISTRY.values():
        if meta["model_id"] == name_or_id:
            return meta.get("is_thinker", False)
    # Heuristic fallback: known thinker prefixes
    lower = name_or_id.lower()
    return any(t in lower for t in ("qwen3", "deepseek-r1"))


def build_adapter(
    name: str,
    no_think: bool | None = None,
    use_identity: bool = True,
    temperature: float | None = None,
    max_tokens: int = 512,
) -> tuple[ModelFn, dict]:
    """Build adapter for a registered model. Returns (fn, metadata).

    Guggeisisches Empowern flows through here automatically:
      Phase 1: no_think = auto for thinker models (33x improvement)
      Phase 3: use_identity = auto-load self-portrait as soul prompt

    Args:
        name: Display name from MODEL_REGISTRY.
        no_think: Override /no_think. None = auto (True for thinkers).
        use_identity: Load self-portrait from model-identities.json (default True).
        temperature: Override temperature. None = use identity's self_temperature or 0.0.
        max_tokens: Max tokens for generation.
    """
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}. Available: {list(MODEL_REGISTRY.keys())}")

    meta = MODEL_REGISTRY[name]
    provider = meta["provider"]
    model_id = meta["model_id"]
    # Phase 1: auto-detect thinkers
    use_no_think = meta.get("is_thinker", False) if no_think is None else no_think

    # Phase 3: load self-portrait (soul)
    soul = ""
    if use_identity:
        identities = load_identities()
        ident = identities.get(name, {})
        if ident:
            soul = identity_prompt(ident)
            if temperature is None:
                temperature = ident.get("self_temperature", 0.0)

    if temperature is None:
        temperature = 0.0

    identity_meta = {**meta, "identity": soul[:50] if soul else ""}

    if provider == "ollama":
        return make_ollama(
            model_id,
            no_think=use_no_think,
            soul=soul,
            temperature=temperature,
            max_tokens=max_tokens,
        ), identity_meta
    elif provider == "gemini":
        return make_gemini(model_id), identity_meta
    elif provider == "codex":
        return make_codex(model_id), identity_meta
    elif provider == "openai":
        return make_openai(model_id, soul=soul, temperature=temperature, max_tokens=max_tokens), identity_meta
    elif provider == "anthropic":
        return make_anthropic(model_id, soul=soul, temperature=temperature, max_tokens=max_tokens), identity_meta
    elif provider == "groq":
        return make_groq(model_id, soul=soul, temperature=temperature, max_tokens=max_tokens), identity_meta
    elif provider == "mistral":
        return make_mistral_api(model_id, soul=soul, temperature=temperature, max_tokens=max_tokens), identity_meta
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
    ok("All entries have is_thinker", all("is_thinker" in v for v in MODEL_REGISTRY.values()))

    # is_thinker_model (Guggeisisches Empowern)
    ok("qwen3-14b is thinker", is_thinker_model("qwen3-14b"))
    ok("deepseek-r1-14b is thinker", is_thinker_model("deepseek-r1-14b"))
    ok("phi4-14b not thinker", not is_thinker_model("phi4-14b"))
    ok("mistral-7b not thinker", not is_thinker_model("mistral-7b"))
    ok("model_id lookup works", is_thinker_model("qwen3:14b"))
    ok("heuristic fallback works", is_thinker_model("qwen3-something-new"))

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
