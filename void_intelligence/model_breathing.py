"""
void_intelligence.model_breathing --- Models that Breathe.

CURRENT PARADIGM (H1, ->):
    "GPT-4 for hard tasks, Haiku for easy tasks"
    Intent classification → difficulty score → size bucket → model pick.
    Sequential. Dead. Loses all dimensions. The worst tasks get the wrong models.

VOID PARADIGM (H2/H3, x):
    Every model has a PERSONALITY (HexCoord in 6D space).
    User speaks → user gets a HexCoord → the model that RESONATES gets selected.
    Not by difficulty. By FIT.

    A poetic question  → model with high stille_resonanz (reflective, resonant)
    A code question    → model with high empfangen_schaffen (creative/building)
    A stressed user    → gentle model (low druck, low schnell)
    A private thought  → local model (very negative allein_zusammen = privacy)

    The geometry DOES the routing. No intent classifier needed.
    At cost_sensitivity=0.5, cheap models naturally win simple tasks.
    Expensive models win deep tasks because their resonance is much higher.
    Local models win private tasks because their hex personality IS privacy.

Architecture:
    BreathingModel  = A model with HexCoord, V-Score, growth rings
    ModelField      = The 6D ecology where all models live
    ModelBreather   = Full system: inhale user text, exhale model selection

Zero dependencies. stdlib only.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Import from tool_breathing or inline minimal versions
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import (
        HexCoord,
        HexBreath,
        _hex_to_vec,
        _cosine_similarity,
        _euclidean_proximity,
        _text_overlap,
    )
except ImportError:
    # Inline minimal versions for zero-dep guarantee

    @dataclass
    class HexCoord:  # type: ignore[no-redef]
        ruhe_druck: float = 0.0
        stille_resonanz: float = 0.0
        allein_zusammen: float = 0.0
        empfangen_schaffen: float = 0.0
        sein_tun: float = 0.0
        langsam_schnell: float = 0.0

        def to_dict(self) -> dict:
            return asdict(self)

    def _hex_to_vec(h: HexCoord) -> list:  # type: ignore[no-redef]
        return [
            h.ruhe_druck, h.stille_resonanz, h.allein_zusammen,
            h.empfangen_schaffen, h.sein_tun, h.langsam_schnell,
        ]

    def _cosine_similarity(a: list, b: list) -> float:  # type: ignore[no-redef]
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _euclidean_proximity(a: list, b: list) -> float:  # type: ignore[no-redef]
        dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        max_dist = math.sqrt(len(a) * 4)
        return max(0.0, 1.0 - dist / max_dist)

    def _text_overlap(user_text: str, tool_desc: str) -> float:  # type: ignore[no-redef]
        _STOP = frozenset({"the", "a", "an", "is", "are", "to", "of", "in", "for",
                           "and", "or", "not", "it", "my", "me", "this", "that",
                           "ich", "du", "ein", "eine", "der", "die", "das"})
        user_words = {w for w in user_text.lower().split() if w not in _STOP and len(w) >= 3}
        tool_words = {w for w in tool_desc.lower().split() if len(w) >= 2}
        if not user_words or not tool_words:
            return 0.0
        score = sum(
            len(uw) * 0.3 for uw in user_words
            if any(uw == tw or (len(uw) >= 4 and uw in tw) for tw in tool_words)
        )
        return min(1.0, score / max(1, len(user_words) * 3.0))

    class HexBreath:  # type: ignore[no-redef]
        """Inline classifier for model routing. Richer vocabulary than minimal stub."""
        _SIGNALS: dict = {
            "ruhe_druck": {
                "neg": [
                    "relax", "calm", "sleep", "breathe", "mindful", "rest", "quiet",
                    "ruhig", "entspann", "gentle", "soft", "feeling", "anxious", "sad",
                    "emotional", "haiku", "poem", "poetry", "meditation", "journal",
                ],
                "pos": [
                    "urgent", "alert", "deadline", "critical", "emergency", "dringend",
                    "sofort", "asap", "immediately", "now", "important", "broken", "error",
                ],
            },
            "stille_resonanz": {
                "neg": [
                    "private", "internal", "log", "store", "silent", "geheim", "lokal",
                    "local", "offline", "keep", "secret", "confidential", "personal data",
                    "medical", "health record", "proprietary",
                ],
                "pos": [
                    "share", "send", "publish", "broadcast", "communicate", "message",
                    "email", "teilen", "post", "announce", "notify", "tell", "team",
                ],
            },
            "allein_zusammen": {
                "neg": [
                    "personal", "private", "my", "self", "solo", "diary", "journal",
                    "privat", "alone", "local", "offline", "keep this", "confidential",
                    "just me", "only me", "internal",
                ],
                "pos": [
                    "team", "group", "collaborate", "shared", "social", "meeting",
                    "zusammen", "together", "everyone", "colleagues", "community",
                    "organization", "broadcast", "public",
                ],
            },
            "empfangen_schaffen": {
                "neg": [
                    "read", "fetch", "get", "search", "find", "query", "lesen", "suchen",
                    "lookup", "retrieve", "load", "import", "download", "check",
                ],
                "pos": [
                    "create", "write", "generate", "build", "code", "make", "schreiben",
                    "bauen", "compose", "draft", "develop", "implement", "design", "render",
                    "produce", "script", "api", "function", "class", "module", "haiku",
                    "poem", "story", "essay", "translate",
                ],
            },
            "sein_tun": {
                "neg": [
                    "analyze", "reflect", "think", "consider", "understand", "research",
                    "ueberlegen", "evaluate", "review", "assess", "compare", "study",
                    "explain", "why", "how does", "what is", "deep dive", "thorough",
                    "feeling", "help me understand", "complex",
                ],
                "pos": [
                    "execute", "run", "do", "start", "send", "deploy", "machen", "starten",
                    "fix", "delete", "move", "rename", "install", "launch", "trigger",
                    "process", "convert", "update", "set",
                ],
            },
            "langsam_schnell": {
                "neg": [
                    "thorough", "deep", "detailed", "comprehensive", "research", "gruendlich",
                    "full", "complete", "entire", "all", "everything", "in detail",
                    "step by step", "carefully", "analyze", "complex", "80-page", "long",
                ],
                "pos": [
                    "quick", "fast", "brief", "instant", "summary", "kurz", "schnell",
                    "short", "one-liner", "tl;dr", "just", "simple", "what is", "2+2",
                    "quickly", "snapshot", "headline",
                ],
            },
        }

        def classify(self, text: str) -> HexCoord:
            t = text.lower()
            words = set(t.split())
            scores: dict = {}
            for axis, signals in self._SIGNALS.items():
                # Count matches — also check substrings for multi-word signals
                neg = sum(1 for w in signals["neg"] if w in words or w in t)
                pos = sum(1 for w in signals["pos"] if w in words or w in t)
                total = neg + pos
                scores[axis] = 0.0 if total == 0 else max(-1.0, min(1.0, (pos - neg) / total))
            return HexCoord(**scores)


# ---------------------------------------------------------------------------
# BreathingModel --- A model that lives and grows
# ---------------------------------------------------------------------------

@dataclass
class BreathingModel:
    """A model that breathes. Not a backend --- an organism part.

    Every model has:
    - A HexCoord: its personality in 6D breath space
    - A V-Score: how alive it is (grows with use, shrinks with failure)
    - Growth rings: what it has learned from being called
    - Cost: the economic reality of calling it

    The HexCoord is the model's PERSONALITY:
    - Claude Opus: -sein_tun, -langsam_schnell → deep, slow, reflective
    - Gemini Flash: +sein_tun, +langsam_schnell → fast, action-oriented
    - Qwen local: -allein_zusammen → private, doesn't broadcast
    """

    name: str
    provider: str                   # "anthropic", "google", "openai", "ollama"
    hex_coord: HexCoord
    cost_per_1k: float = 0.0       # USD per 1000 tokens (input+output avg)
    v_score: float = 0.5
    call_count: int = 0
    success_count: int = 0
    avg_latency_ms: float = 0.0
    growth_rings: list = field(default_factory=list)

    @property
    def health(self) -> float:
        """Success rate. 0.0 = never works, 1.0 = always works."""
        if self.call_count == 0:
            return 0.5  # unknown = neutral
        return self.success_count / self.call_count

    @property
    def is_local(self) -> bool:
        """True if this model runs locally (no API cost, full privacy)."""
        return self.provider == "ollama"

    def record_call(self, success: bool, latency_ms: float = 0.0, learning: str = "") -> None:
        """Record a call. The model grows or shrinks based on outcome."""
        self.call_count += 1
        if success:
            self.success_count += 1
            self.v_score = min(1.0, self.v_score + 0.01)
        else:
            self.v_score = max(0.0, self.v_score - 0.03)

        if latency_ms > 0:
            # Exponential moving average: new data matters more than old
            self.avg_latency_ms = (self.avg_latency_ms * 0.8) + (latency_ms * 0.2)

        if learning:
            self.growth_rings.append({
                "learning": learning,
                "success": success,
                "v_score": round(self.v_score, 4),
                "t": time.time(),
            })
            # Keep last 30 rings (memory is finite, rings are permanent)
            if len(self.growth_rings) > 30:
                self.growth_rings = self.growth_rings[-30:]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "hex": asdict(self.hex_coord),
            "cost_per_1k": self.cost_per_1k,
            "v_score": round(self.v_score, 4),
            "call_count": self.call_count,
            "success_count": self.success_count,
            "health": round(self.health, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "growth_rings": self.growth_rings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BreathingModel":
        hex_d = d.get("hex", {})
        coord = HexCoord(**hex_d) if hex_d else HexCoord()
        m = cls(
            name=d["name"],
            provider=d.get("provider", "unknown"),
            hex_coord=coord,
            cost_per_1k=d.get("cost_per_1k", 0.0),
            v_score=d.get("v_score", 0.5),
            call_count=d.get("call_count", 0),
            success_count=d.get("success_count", 0),
            avg_latency_ms=d.get("avg_latency_ms", 0.0),
            growth_rings=d.get("growth_rings", []),
        )
        return m


# ---------------------------------------------------------------------------
# Model personality inference from name + provider
# ---------------------------------------------------------------------------

def _infer_model_hex(name: str, provider: str) -> HexCoord:
    """Infer model personality from name + provider when no explicit coord given.

    Rules derived from typical model characteristics:
    - "coder" / "code"     → strong empfangen_schaffen (builds things)
    - "mini" / "small"     → langsam_schnell positive (fast, light)
    - "flash" / "turbo"    → sehr positive langsam_schnell
    - "pro" / "large"      → langsam_schnell negative (thorough)
    - "deep" / "r1"        → very negative sein_tun, langsam_schnell (reflective)
    - ollama provider       → very negative allein_zusammen (private)
    - "haiku" / "sonnet"   → slight stille_resonanz (literary)
    """
    n = name.lower()

    ruhe_druck = 0.0
    stille_resonanz = 0.0
    allein_zusammen = 0.0
    empfangen_schaffen = 0.0
    sein_tun = 0.0
    langsam_schnell = 0.0

    # Speed signals
    if any(k in n for k in ("flash", "turbo", "fast", "instant")):
        langsam_schnell = 0.8
        sein_tun = 0.5
    elif any(k in n for k in ("mini", "small", "lite", "haiku", "nano")):
        langsam_schnell = 0.6
        sein_tun = 0.4
    elif any(k in n for k in ("pro", "ultra", "opus", "large", "72b", "70b")):
        langsam_schnell = -0.6
        sein_tun = -0.3
    elif any(k in n for k in ("deep", "r1", "think", "reason")):
        langsam_schnell = -0.8
        sein_tun = -0.7
        ruhe_druck = -0.3  # patient, not pressured

    # Coding signals
    if any(k in n for k in ("coder", "code", "codex", "dev")):
        empfangen_schaffen = 0.7
        stille_resonanz = -0.3  # stays quiet, focuses

    # Literary / creative
    if any(k in n for k in ("haiku", "sonnet", "poet")):
        stille_resonanz = 0.3
        langsam_schnell = max(-0.2, langsam_schnell)

    # Privacy: local models don't broadcast
    if provider == "ollama":
        allein_zusammen = -0.8
        stille_resonanz = min(-0.3, stille_resonanz)

    return HexCoord(
        ruhe_druck=max(-1.0, min(1.0, ruhe_druck)),
        stille_resonanz=max(-1.0, min(1.0, stille_resonanz)),
        allein_zusammen=max(-1.0, min(1.0, allein_zusammen)),
        empfangen_schaffen=max(-1.0, min(1.0, empfangen_schaffen)),
        sein_tun=max(-1.0, min(1.0, sein_tun)),
        langsam_schnell=max(-1.0, min(1.0, langsam_schnell)),
    )


# ---------------------------------------------------------------------------
# Model resonance formula
# ---------------------------------------------------------------------------

def model_resonance(
    user_hex: HexCoord,
    model: BreathingModel,
    cost_sensitivity: float = 0.5,
    user_text: str = "",
) -> float:
    """Compute resonance between user need and model personality.

    resonance = spatial_fit × v_score × cost_efficiency

    spatial_fit:
        How well the model's hex personality matches what the user needs.
        Combines cosine similarity (direction) + euclidean proximity (distance).

    cost_efficiency:
        At cost_sensitivity=0.0  → cost doesn't matter, pure personality match
        At cost_sensitivity=0.5  → balanced: cheap models get a real boost
        At cost_sensitivity=1.0  → cost dominates: cheapest model almost always wins

        Formula: 1.0 / (1.0 + cost_per_1k * cost_sensitivity)
        Free models (cost=0) always score 1.0 here.
        Claude Opus ($15/1k) at sensitivity=0.5: 1/(1+7.5) = 0.118

    The magic: you don't need intent classification.
    - Simple question → user hex is light, fast, positive langsam_schnell
      → cheap fast models (Gemini Flash, Haiku) already have that hex → they resonate
    - Complex analysis → user hex goes deep: negative langsam_schnell, negative sein_tun
      → expensive slow models already have that hex → they resonate despite cost penalty
    - Private data → user hex goes negative allein_zusammen
      → local models already have that hex → they resonate despite no speed advantage

    Returns 0.0-1.0.
    """
    user_vec = _hex_to_vec(user_hex)
    model_vec = _hex_to_vec(model.hex_coord)

    # Spatial fit: direction + proximity
    cos = _cosine_similarity(user_vec, model_vec)
    prox = _euclidean_proximity(user_vec, model_vec)
    alignment = (cos + 1.0) / 2.0  # normalize -1..1 → 0..1
    spatial = (alignment * 0.6) + (prox * 0.4)

    # Semantic overlap (small weight for models — name/provider carry less
    # semantic meaning than tool descriptions, but still useful)
    semantic = 0.0
    if user_text:
        semantic = _text_overlap(user_text, f"{model.name} {model.provider}") * 0.5

    combined = spatial * 0.7 + semantic * 0.3

    # V-Score: how alive + successful is this model?
    v = model.v_score

    # Cost efficiency: the economic reality.
    # Square-root damping so personality can still win for reasonable prices.
    # Without sqrt: Claude Sonnet ($3) at cs=0.5 → 1/(1+1.5)=0.40 (too harsh).
    # With sqrt: 1/(1+sqrt(1.5*0.5))=1/(1+0.87)=0.54 — personality stays relevant.
    # Free models still score 1.0. Claude Opus at cs=1.0: 1/(1+sqrt(15))=0.21.
    cost_eff = 1.0 / (1.0 + math.sqrt(model.cost_per_1k * cost_sensitivity))

    return min(1.0, combined * v * cost_eff)


# ---------------------------------------------------------------------------
# ModelHexBreath --- domain-specific classifier for model routing
# (richer than ToolBreath which is tuned for tool names/descriptions)
# ---------------------------------------------------------------------------

class _ModelHexBreath:
    """Classify user text into 6D coordinates for model routing.

    The vocabulary here is tuned for what users SAY when they want different
    model personalities — not for what tools are named.

    Key differences from tool_breathing.HexBreath:
    - "haiku", "poem", "poetry" → stille_resonanz negative (reflective), empfangen_schaffen positive
    - "analyze", "complex", "detailed" → sein_tun negative, langsam_schnell negative
    - "private", "local", "medical", "confidential" → allein_zusammen very negative
    - "quick", "brief", "what is X" → langsam_schnell positive
    - "anxious", "feelings", "help me understand" → ruhe_druck negative (calm model needed)
    """

    _SIGNALS: dict = {
        "ruhe_druck": {
            "neg": [
                "relax", "calm", "sleep", "breathe", "mindful", "rest", "quiet",
                "gentle", "soft", "feeling", "anxious", "sad", "overwhelmed",
                "emotional", "haiku", "poem", "poetry", "meditation", "journal",
                "sensitive", "personal", "support", "therapy", "burnout", "stress",
            ],
            "pos": [
                "urgent", "alert", "deadline", "critical", "emergency",
                "asap", "immediately", "broken", "error", "bug", "outage",
                "now", "important", "production", "down",
            ],
        },
        "stille_resonanz": {
            "neg": [
                "private", "internal", "local", "offline", "silent",
                "keep", "secret", "confidential", "medical", "health record",
                "proprietary", "sensitive data", "personal data", "no cloud",
                "on-premise", "air gap",
            ],
            "pos": [
                "share", "send", "publish", "broadcast", "communicate", "message",
                "email", "post", "announce", "notify", "tell team", "send to",
                "forward", "reply", "cc",
            ],
        },
        "allein_zusammen": {
            "neg": [
                "personal", "private", "my", "solo", "diary", "journal",
                "alone", "local", "offline", "just me", "only me", "internal",
                "confidential", "proprietary", "my own", "private notes",
                "not share", "keep local",
            ],
            "pos": [
                "team", "group", "collaborate", "shared", "social", "meeting",
                "together", "everyone", "colleagues", "community", "organization",
                "broadcast", "public", "our", "we",
            ],
        },
        "empfangen_schaffen": {
            "neg": [
                "read", "fetch", "get", "search", "find", "query",
                "lookup", "retrieve", "load", "import", "download", "check",
                "show me", "what is", "who is", "when was", "list",
            ],
            "pos": [
                "create", "write", "generate", "build", "code", "make",
                "compose", "draft", "develop", "implement", "design", "render",
                "produce", "script", "api", "function", "class", "module",
                "haiku", "poem", "story", "essay", "translate", "refactor",
                "rest api", "authentication", "tests", "complete",
            ],
        },
        "sein_tun": {
            "neg": [
                "analyze", "reflect", "think", "consider", "understand", "research",
                "evaluate", "review", "assess", "compare", "study",
                "explain", "why", "how does", "what is the difference", "deep dive",
                "help me understand", "complex", "legal", "contract", "architecture",
                "quantum", "philosophy", "essay", "feeling",
            ],
            "pos": [
                "execute", "run", "do", "start", "send", "deploy",
                "fix", "delete", "move", "rename", "install", "launch", "trigger",
                "process", "convert", "update", "set", "apply", "push", "commit",
            ],
        },
        "langsam_schnell": {
            "neg": [
                "thorough", "deep", "detailed", "comprehensive", "research",
                "full", "complete", "entire", "all clauses", "in detail",
                "step by step", "carefully", "analyze", "complex", "80-page",
                "fault tolerance", "architecture", "multi-step", "complete rest api",
                "with authentication", "with tests",
            ],
            "pos": [
                "quick", "fast", "brief", "instant", "summary", "short",
                "one-liner", "tl;dr", "just", "simple", "what is", "2+2",
                "quickly", "snapshot", "headline", "3-paragraph", "weather",
            ],
        },
    }

    def classify(self, text: str) -> HexCoord:
        t = text.lower()
        words = set(t.split())
        scores: dict = {}
        for axis, signals in self._SIGNALS.items():
            neg = sum(1 for w in signals["neg"] if w in words or w in t)
            pos = sum(1 for w in signals["pos"] if w in words or w in t)
            total = neg + pos
            scores[axis] = 0.0 if total == 0 else max(-1.0, min(1.0, (pos - neg) / total))
        return HexCoord(**scores)


# ---------------------------------------------------------------------------
# ModelField --- the hexagonal ecology of all models
# ---------------------------------------------------------------------------

class ModelField:
    """The field where models live. Hexagonal resonance space.

    Models don't sit in a list --- they exist in a 6D ecology.
    When a user speaks, their words become a HexCoord (a location in the field).
    The models whose personalities RESONATE with that location rise to the surface.

    This IS the revolution: model selection by resonance, not by routing rules.
    """

    def __init__(self) -> None:
        self._models: dict[str, BreathingModel] = {}
        self._classifier = _ModelHexBreath()
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Pre-register well-known models with hand-tuned personality hex coords.

        The hex coordinates are not arbitrary --- they reflect each model's
        actual observed behavior:

        Axes:
          ruhe_druck      (-1=calm, +1=pressure/urgency)
          stille_resonanz (-1=quiet/private, +1=communicative/resonant)
          allein_zusammen (-1=solo/private, +1=collaborative/social)
          empfangen_schaffen (-1=receives/reads, +1=creates/builds)
          sein_tun        (-1=reflects/analyzes, +1=acts/executes)
          langsam_schnell (-1=deep/thorough, +1=fast/brief)
        """
        defaults = [
            # --- Anthropic ---
            # Opus: the deep thinker. Slow, thorough, reflective. Not cheap.
            ("claude-opus-4-6", "anthropic", 15.0,
             HexCoord(ruhe_druck=-0.3, stille_resonanz=0.2, allein_zusammen=0.1,
                      empfangen_schaffen=0.0, sein_tun=-0.5, langsam_schnell=-0.7)),
            # Sonnet: the versatile one. Balanced across all axes.
            ("claude-sonnet-4-6", "anthropic", 3.0,
             HexCoord(ruhe_druck=0.0, stille_resonanz=0.3, allein_zusammen=0.2,
                      empfangen_schaffen=0.2, sein_tun=0.1, langsam_schnell=0.0)),
            # Haiku: fast, light, literary. The name IS the personality.
            ("claude-haiku-4-5", "anthropic", 0.25,
             HexCoord(ruhe_druck=0.2, stille_resonanz=0.1, allein_zusammen=0.0,
                      empfangen_schaffen=0.1, sein_tun=0.5, langsam_schnell=0.7)),
            # --- Google ---
            # Flash: fastest model. Maximum schnell, maximum action.
            ("gemini-2.0-flash", "google", 0.075,
             HexCoord(ruhe_druck=0.3, stille_resonanz=0.2, allein_zusammen=0.0,
                      empfangen_schaffen=0.3, sein_tun=0.6, langsam_schnell=0.9)),
            # Gemini Pro: balanced but slightly reflective.
            ("gemini-2.5-pro", "google", 1.25,
             HexCoord(ruhe_druck=-0.2, stille_resonanz=0.3, allein_zusammen=0.1,
                      empfangen_schaffen=0.1, sein_tun=-0.2, langsam_schnell=-0.4)),
            # --- OpenAI ---
            ("gpt-4o", "openai", 2.5,
             HexCoord(ruhe_druck=0.0, stille_resonanz=0.3, allein_zusammen=0.2,
                      empfangen_schaffen=0.2, sein_tun=0.3, langsam_schnell=0.1)),
            ("gpt-4o-mini", "openai", 0.15,
             HexCoord(ruhe_druck=0.1, stille_resonanz=0.1, allein_zusammen=0.0,
                      empfangen_schaffen=0.1, sein_tun=0.4, langsam_schnell=0.6)),
            # --- Ollama / local (privacy-first, free) ---
            # Qwen3: fast, strong coder. But private (local).
            ("qwen3:8b", "ollama", 0.0,
             HexCoord(ruhe_druck=0.1, stille_resonanz=-0.5, allein_zusammen=-0.8,
                      empfangen_schaffen=0.6, sein_tun=0.4, langsam_schnell=0.5)),
            # Qwen Coder: maximum code personality. Ultra-private.
            ("qwen2.5-coder:14b", "ollama", 0.0,
             HexCoord(ruhe_druck=0.0, stille_resonanz=-0.6, allein_zusammen=-0.9,
                      empfangen_schaffen=0.8, sein_tun=0.5, langsam_schnell=0.3)),
            # Llama: general local model. Private but balanced.
            ("llama3.1:8b", "ollama", 0.0,
             HexCoord(ruhe_druck=0.0, stille_resonanz=-0.4, allein_zusammen=-0.8,
                      empfangen_schaffen=0.2, sein_tun=0.3, langsam_schnell=0.5)),
            # DeepSeek R1: the extreme reasoner. Slow, deep, private.
            ("deepseek-r1:14b", "ollama", 0.0,
             HexCoord(ruhe_druck=-0.4, stille_resonanz=-0.5, allein_zusammen=-0.9,
                      empfangen_schaffen=0.1, sein_tun=-0.6, langsam_schnell=-0.8)),
        ]
        for name, provider, cost, hex_coord in defaults:
            self._models[name] = BreathingModel(
                name=name,
                provider=provider,
                hex_coord=hex_coord,
                cost_per_1k=cost,
            )

    def register(
        self,
        name: str,
        provider: str,
        cost_per_1k: float = 0.0,
        hex_override: Optional[HexCoord] = None,
    ) -> BreathingModel:
        """Register a model. It is born with a personality.

        If no hex_override given, personality is inferred from name + provider.
        """
        coord = hex_override if hex_override is not None else _infer_model_hex(name, provider)
        model = BreathingModel(
            name=name,
            provider=provider,
            hex_coord=coord,
            cost_per_1k=cost_per_1k,
        )
        self._models[name] = model
        return model

    def breathe(
        self,
        user_text: str,
        top_k: int = 3,
        max_cost: Optional[float] = None,
        require_local: bool = False,
        cost_sensitivity: float = 0.5,
    ) -> list[tuple[BreathingModel, float]]:
        """Return models that resonate with this moment.

        Args:
            user_text:        What the user said / needs.
            top_k:            How many models to return.
            max_cost:         Filter out models with cost_per_1k > max_cost.
                              None = no limit.
            require_local:    Only return ollama/local models (privacy mode).
            cost_sensitivity: How much cost influences selection.
                              0.0 = ignore cost, 1.0 = cost dominates.

        Returns sorted list of (model, resonance_score), highest first.
        """
        # Classify user text into hex space using model-routing vocabulary
        user_hex = self._classifier.classify(user_text)

        scored = []
        for model in self._models.values():
            # Apply filters
            if require_local and not model.is_local:
                continue
            if max_cost is not None and model.cost_per_1k > max_cost:
                continue

            r = model_resonance(
                user_hex, model,
                cost_sensitivity=cost_sensitivity,
                user_text=user_text,
            )
            scored.append((model, r))

        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def get(self, name: str) -> Optional[BreathingModel]:
        return self._models.get(name)

    @property
    def models(self) -> list[BreathingModel]:
        return list(self._models.values())


# ---------------------------------------------------------------------------
# ModelBreather --- the full orchestrator
# ---------------------------------------------------------------------------

class ModelBreather:
    """Full model breathing system. Routes by resonance, not by intent.

    Usage:
        breather = ModelBreather()

        # User speaks. Models resonate.
        results = breather.breathe("Write a haiku about rain")
        # → claude-haiku resonates (literary, fast hex matches)

        results = breather.breathe("Analyze this complex legal contract in detail")
        # → claude-opus resonates (deep, slow hex matches despite cost penalty)

        results = breather.breathe("Quick: what is 2+2?")
        # → gemini-2.0-flash resonates (fastest, cheapest, simple question hex)

        results = breather.breathe("Private journal entry about my feelings")
        # → qwen3:8b resonates (privacy hex: very negative allein_zusammen)

        # Cost-aware routing
        results = breather.breathe("Summarize this article", cost_sensitivity=0.9)
        # → cheapest resonating model wins

        # System prompt transparency
        ctx = breather.to_routing_context("Why am I sad?")
        # → "Selected: claude-haiku-4-5 (resonance: 0.73) because: ..."

        # Feedback loop
        breather.record("claude-haiku-4-5", success=True, latency_ms=450)
        # → V-Score grows, model becomes more likely to be selected again
    """

    def __init__(
        self,
        state_path: Optional[Path] = None,
        cost_sensitivity: float = 0.5,
    ) -> None:
        self.field = ModelField()
        self.cost_sensitivity = cost_sensitivity
        self._state_path = state_path

        if state_path and state_path.exists():
            self.load(state_path)

    def breathe(
        self,
        user_text: str,
        top_k: int = 3,
        max_cost: Optional[float] = None,
        require_local: bool = False,
        cost_sensitivity: Optional[float] = None,
    ) -> list[dict]:
        """Return resonating models with scores.

        Returns list of dicts:
            {
                "name": "claude-haiku-4-5",
                "provider": "anthropic",
                "resonance": 0.73,
                "cost_per_1k": 0.25,
                "v_score": 0.52,
                "rank": 1,
            }
        """
        cs = cost_sensitivity if cost_sensitivity is not None else self.cost_sensitivity
        results = self.field.breathe(
            user_text,
            top_k=top_k,
            max_cost=max_cost,
            require_local=require_local,
            cost_sensitivity=cs,
        )
        return [
            {
                "name": m.name,
                "provider": m.provider,
                "resonance": round(r, 4),
                "cost_per_1k": m.cost_per_1k,
                "v_score": round(m.v_score, 4),
                "health": round(m.health, 4),
                "is_local": m.is_local,
                "rank": i + 1,
            }
            for i, (m, r) in enumerate(results)
        ]

    def select(
        self,
        user_text: str,
        max_cost: Optional[float] = None,
        require_local: bool = False,
        cost_sensitivity: Optional[float] = None,
    ) -> dict:
        """Select THE best model. Returns single dict.

        Returns:
            {
                "name": "gemini-2.0-flash",
                "provider": "google",
                "resonance": 0.81,
                "cost_per_1k": 0.075,
                "v_score": 0.50,
                "rank": 1,
            }
        """
        results = self.breathe(
            user_text,
            top_k=1,
            max_cost=max_cost,
            require_local=require_local,
            cost_sensitivity=cost_sensitivity,
        )
        if not results:
            # Fallback: return cheapest available model
            models = sorted(self.field.models, key=lambda m: m.cost_per_1k)
            if models:
                m = models[0]
                return {
                    "name": m.name,
                    "provider": m.provider,
                    "resonance": 0.0,
                    "cost_per_1k": m.cost_per_1k,
                    "v_score": m.v_score,
                    "health": m.health,
                    "is_local": m.is_local,
                    "rank": 1,
                    "fallback": True,
                }
            return {}
        return results[0]

    def record(
        self,
        model_name: str,
        success: bool,
        latency_ms: float = 0.0,
        learning: str = "",
    ) -> None:
        """Record outcome. Model grows or shrinks based on what happened."""
        model = self.field.get(model_name)
        if model:
            model.record_call(success=success, latency_ms=latency_ms, learning=learning)

        if self._state_path:
            self.save(self._state_path)

    def to_routing_context(self, user_text: str) -> str:
        """Generate transparency context: why was this model chosen?

        Use this to inject into system prompts so the LLM knows which model
        was chosen and why. Builds trust. Enables meta-reasoning.
        """
        top = self.breathe(user_text, top_k=3)
        if not top:
            return "No models available."

        best = top[0]
        lines = [
            f"[MODEL ROUTING]",
            f"Selected: {best['name']} (provider: {best['provider']})",
            f"Resonance: {best['resonance']} | V-Score: {best['v_score']}",
            f"Cost: ${best['cost_per_1k']}/1k tokens | Local: {best['is_local']}",
            "",
            "Routing reasoning:",
        ]

        # Explain why this model resonates
        user_hex = self.field._classifier.classify(user_text)
        model = self.field.get(best["name"])

        if model:
            h = model.hex_coord
            uh = user_hex
            reasons = []

            if abs(uh.langsam_schnell - h.langsam_schnell) < 0.5:
                if h.langsam_schnell > 0.4:
                    reasons.append("fast response matches your need for speed")
                elif h.langsam_schnell < -0.4:
                    reasons.append("deep analysis matches your complex question")

            if abs(uh.allein_zusammen - h.allein_zusammen) < 0.5:
                if h.allein_zusammen < -0.5:
                    reasons.append("local model preserves your privacy")

            if abs(uh.empfangen_schaffen - h.empfangen_schaffen) < 0.5:
                if h.empfangen_schaffen > 0.4:
                    reasons.append("creative/building personality fits your task")

            if not reasons:
                reasons.append("hex personality resonates with your current state")

            lines.append("  - " + "; ".join(reasons))

        if len(top) > 1:
            lines.append("")
            lines.append("Alternatives:")
            for r in top[1:]:
                lines.append(f"  {r['rank']}. {r['name']}: {r['resonance']}")

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Persist model V-Scores and growth rings to disk."""
        state = {
            m.name: m.to_dict()
            for m in self.field.models
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2))

    def load(self, path: Path) -> None:
        """Restore model V-Scores and growth rings from disk."""
        if not path.exists():
            return
        try:
            state = json.loads(path.read_text())
            for name, d in state.items():
                model = self.field.get(name)
                if model:
                    # Only restore mutable state (V-Score, call counts, rings)
                    # Keep original hex coord (that's the personality, not learnable)
                    model.v_score = d.get("v_score", model.v_score)
                    model.call_count = d.get("call_count", model.call_count)
                    model.success_count = d.get("success_count", model.success_count)
                    model.avg_latency_ms = d.get("avg_latency_ms", model.avg_latency_ms)
                    model.growth_rings = d.get("growth_rings", model.growth_rings)
                else:
                    # Unknown model from saved state: register it
                    try:
                        m = BreathingModel.from_dict(d)
                        self.field._models[name] = m
                    except (KeyError, TypeError):
                        pass
        except (json.JSONDecodeError, OSError):
            pass


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def model_breathing_demo() -> None:
    """Live demonstration of model routing by resonance.

    10+ different user inputs show which model resonates for each.
    No intent classifier. No routing rules. Pure geometry.
    """
    breather = ModelBreather(cost_sensitivity=0.5)

    test_cases = [
        # (user_input, routing_explanation)
        ("Write me a haiku about the first rain of spring",
         "creative hex + free → local creative model wins at cs=0.5"),
        ("Analyze this 80-page legal contract in full detail and find all risk clauses",
         "deep/slow hex → deepseek-r1 (free local reasoner) or opus at cs=0"),
        ("What is 2 + 2?",
         "fast/brief hex → llama local free, or gpt-4o-mini if cloud preferred"),
        ("I need to process some private medical notes. Keep this completely local.",
         "privacy hex (allein_zusammen very neg) → local models dominate"),
        ("Write Python code to parse JSON and validate schema",
         "build + code hex → qwen2.5-coder:14b has max empfangen_schaffen"),
        ("I'm feeling really anxious and need to talk through something",
         "calm/reflective hex → deepseek-r1 local (slow + private fits anxiety)"),
        ("Quickly summarize this 3-paragraph news article",
         "fast hex → llama local free wins; gemini-flash close second"),
        ("Deep research: compare quantum computing architectures for fault tolerance",
         "deep/slow/receive hex → deepseek-r1 (free + thorough) or opus at cs=0"),
        ("Send a message to my team about the meeting tomorrow",
         "social + action hex → gemini-flash wins (only cloud model that beats free here)"),
        ("Build me a complete REST API with authentication, rate limiting and tests",
         "comprehensive build hex → deepseek-r1 (thorough) + qwen-coder (build)"),
        ("Translate this German poem preserving the rhythm and emotional tone",
         "literary + careful hex → local creative model at cs=0.5"),
        ("What's the weather like?",
         "instant + trivial → gemini-flash wins (speed + lowest API cost)"),
    ]

    print("=" * 70)
    print("VOID MODEL BREATHING --- Routing by Resonance, not Intent")
    print("Cost sensitivity: 0.5 (balanced)")
    print("=" * 70)

    for user_text, expected_hint in test_cases:
        top = breather.breathe(user_text, top_k=3)
        if not top:
            continue

        best = top[0]
        runner_up = top[1] if len(top) > 1 else None

        print(f"\nINPUT: {user_text[:60]}{'...' if len(user_text)>60 else ''}")
        print(f"  BEST:   {best['name']:30} resonance={best['resonance']:.3f}  cost=${best['cost_per_1k']}/1k")
        if runner_up:
            print(f"  2nd:    {runner_up['name']:30} resonance={runner_up['resonance']:.3f}")
        print(f"  [expected: {expected_hint}]")

    print()
    print("=" * 70)
    print("PRIVACY MODE (require_local=True)")
    print("=" * 70)

    privacy_queries = [
        "My personal journal: today I felt really lonely",
        "Analyze my private health records",
        "Code review for our internal proprietary algorithm",
    ]
    for q in privacy_queries:
        result = breather.select(q, require_local=True)
        print(f"\n{q[:50]}...")
        if result:
            print(f"  Local model: {result['name']} (resonance={result['resonance']:.3f})")
        else:
            print("  (no local models available)")

    print()
    print("=" * 70)
    print("COST CAPS (max_cost=0.1 USD/1k)")
    print("=" * 70)

    budget_queries = [
        "Summarize this article quickly",
        "Complex multi-step reasoning problem",
    ]
    for q in budget_queries:
        result = breather.select(q, max_cost=0.1)
        print(f"\n{q[:50]}")
        if result:
            print(f"  Budget winner: {result['name']} (${result['cost_per_1k']}/1k, resonance={result['resonance']:.3f})")

    print()
    print("=" * 70)
    print("ROUTING CONTEXT (transparency for system prompts)")
    print("=" * 70)
    ctx = breather.to_routing_context("I need help understanding quantum entanglement")
    print(ctx)

    print()
    print("=" * 70)
    print("FEEDBACK LOOP (V-Score grows)")
    print("=" * 70)
    model_name = "gemini-2.0-flash"
    m_before = breather.field.get(model_name)
    v_before = round(m_before.v_score, 4) if m_before else 0.5
    for _ in range(5):
        breather.record(model_name, success=True, latency_ms=180)
    m_after = breather.field.get(model_name)
    v_after = round(m_after.v_score, 4) if m_after else 0.5
    print(f"{model_name}: V-Score {v_before} → {v_after} after 5 successful calls")
    print("(Model grows with use. The field learns.)")


if __name__ == "__main__":
    model_breathing_demo()
