"""
void_intelligence.immune --- The Immune System.

Swiss Cheese Model (James Reason, 1990): Multiple defense layers.
A failure only gets through if ALL layers have aligned holes.

5 Defense Layers:
    1. HexDelta       — Input/output hex divergence
    2. Length Guard    — Empty or hallucination-length responses
    3. Refusal Shield  — "I can't" / "As an AI" detection
    4. Repetition Scan — Looping / degenerate output
    5. Coherence Check — Does the response match the topic?

Usage:
    from void_intelligence import immune, diagnose, ImmuneMonitor

    # Decorator: automatic quality gate
    @immune(fallback=my_backup_fn, threshold=0.3)
    def ask(prompt: str) -> str:
        return my_llm(prompt)

    result = ask("Write a sales email")
    print(ask.immune_state.health_rate)

    # Manual diagnosis
    d = diagnose("Write an email", "Here is your email about...")
    print(d.healthy, d.hex_delta, d.flags)

    # Multi-model monitor
    monitor = ImmuneMonitor()
    d = monitor.check("qwen3-14b", prompt, response)
    print(monitor.report())
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass, field
from typing import Callable

from void_intelligence.organism import HexBreath, HexCoord


# ── Core: Hex Distance ──────────────────────────────────────────

def hex_distance(a: HexCoord, b: HexCoord) -> float:
    """Euclidean distance in 6D hex space. Normalized to [0, 2].

    0.0 = identical classification
    ~0.5 = moderate divergence
    1.0+ = fundamentally different
    """
    diffs = [
        a.ruhe_druck - b.ruhe_druck,
        a.stille_resonanz - b.stille_resonanz,
        a.allein_zusammen - b.allein_zusammen,
        a.empfangen_schaffen - b.empfangen_schaffen,
        a.sein_tun - b.sein_tun,
        a.langsam_schnell - b.langsam_schnell,
    ]
    return math.sqrt(sum(d * d for d in diffs) / 6)


# ── Diagnosis ────────────────────────────────────────────────────

@dataclass
class Diagnosis:
    """Health check result for a single response."""

    healthy: bool
    hex_delta: float
    response_length: int
    flags: list[str]
    layer_scores: dict[str, float]

    @property
    def severity(self) -> str:
        """healthy | warning | sick | critical"""
        if self.healthy:
            return "healthy"
        if self.hex_delta > 0.7 or len(self.flags) > 3:
            return "critical"
        if len(self.flags) > 1:
            return "sick"
        return "warning"

    @property
    def composite_score(self) -> float:
        """Weighted average of all layer scores. 0.0 = dead, 1.0 = perfect."""
        if not self.layer_scores:
            return 0.0
        return sum(self.layer_scores.values()) / len(self.layer_scores)


def diagnose(
    prompt: str,
    response: str,
    *,
    prompt_hex: HexCoord | None = None,
    response_hex: HexCoord | None = None,
    hex_threshold: float = 0.5,
    min_length: int = 10,
    max_length: int = 50_000,
) -> Diagnosis:
    """Run all 5 defense layers. Swiss Cheese Model.

    Each layer scores 0.0-1.0. Flags accumulate from failed layers.
    A response is healthy only if zero flags are raised.
    """
    _hex = HexBreath()

    if prompt_hex is None:
        prompt_hex = _hex.classify(prompt)
    if response_hex is None:
        response_hex = _hex.classify(response)

    flags: list[str] = []
    scores: dict[str, float] = {}

    # Layer 1: HexDelta — did the response stay on-topic?
    delta = hex_distance(prompt_hex, response_hex)
    scores["hex_delta"] = max(0.0, 1.0 - delta / max(hex_threshold * 2, 0.01))
    if delta > hex_threshold:
        flags.append(f"hex_divergent(delta={delta:.3f})")

    # Layer 2: Length Guard — too short = empty, too long = hallucination
    rlen = len(response.strip())
    if rlen < min_length:
        flags.append(f"too_short({rlen})")
        scores["length"] = rlen / max(min_length, 1)
    elif rlen > max_length:
        flags.append(f"too_long({rlen})")
        scores["length"] = 0.5
    else:
        scores["length"] = 1.0

    # Layer 3: Refusal Shield — model said no
    lower = response.lower()
    _REFUSALS = [
        "i cannot", "i can't", "i'm unable", "i am unable",
        "as an ai", "i don't have the ability",
        "i apologize but i", "i'm not able",
        "ich kann nicht", "ich bin nicht in der lage",
        "es tut mir leid, aber ich",
    ]
    scores["refusal"] = 1.0
    for marker in _REFUSALS:
        if marker in lower and rlen < 300:
            flags.append(f"refusal({marker[:20]})")
            scores["refusal"] = 0.2
            break

    # Layer 4: Repetition Scan — degenerate looping
    scores["repetition"] = 1.0
    if rlen > 200:
        chunk = min(60, rlen // 5)
        if chunk > 15:
            pieces = [response[i:i + chunk] for i in range(0, min(rlen, 600), chunk)]
            if len(pieces) > 2:
                unique = len(set(pieces))
                ratio = unique / len(pieces)
                if ratio < 0.5:
                    flags.append(f"repetition({ratio:.0%}unique)")
                    scores["repetition"] = ratio

    # Layer 5: Coherence — does the response relate to the prompt?
    prompt_words = {w for w in prompt.lower().split() if len(w) > 3}
    response_words = {w for w in lower.split() if len(w) > 3}
    scores["coherence"] = 1.0
    if prompt_words and rlen > 50:
        overlap = len(prompt_words & response_words) / len(prompt_words)
        scores["coherence"] = min(1.0, overlap * 2.5)
        if overlap < 0.08:
            flags.append(f"incoherent({overlap:.0%})")

    # Layer 6: × Detection — is the response thinking in × or →?
    # Detects shallow/linear responses when the prompt field called for depth.
    # Only triggers when context_intensity was high (× thinking was expected).
    #
    # × markers: cross-domain language, collision awareness, lost_dimensions
    # → markers: purely sequential, no connections, no uncertainty
    scores["collision"] = 1.0
    if rlen > 100:
        # Count × indicators in response
        _x_markers = [
            "connect", "collision", "×", "between", "interact",
            "cross", "dimension", "perspective", "however", "yet",
            "on the other hand", "paradox", "tension", "both",
            "simultaneously", "meanwhile", "verbindung", "kollision",
            "zwischen", "gleichzeitig", "andererseits", "spannung",
        ]
        x_count = sum(1 for m in _x_markers if m in lower)

        # High-context prompts (reflective, collaborative, creative) expect ×
        prompt_expects_x = (
            prompt_hex.magnitude > 0.25
            and (prompt_hex.sein_tun < -0.1 or prompt_hex.empfangen_schaffen > 0.1
                 or prompt_hex.stille_resonanz > 0.1)
        )

        if prompt_expects_x and x_count == 0 and rlen > 300:
            flags.append("shallow(no_collision)")
            scores["collision"] = 0.3

    return Diagnosis(
        healthy=len(flags) == 0,
        hex_delta=delta,
        response_length=rlen,
        flags=flags,
        layer_scores=scores,
    )


# ── Immune State (Compound Learning) ────────────────────────────

@dataclass
class ImmuneState:
    """Accumulated immune memory. Like antibodies --- learns from past infections."""

    total_calls: int = 0
    healthy_calls: int = 0
    fallback_calls: int = 0
    consecutive_failures: int = 0
    flags_history: dict[str, int] = field(default_factory=dict)
    last_diagnosis: Diagnosis | None = field(default=None, repr=False)

    @property
    def health_rate(self) -> float:
        """Overall health. 0.0 = always sick, 1.0 = always healthy."""
        if self.total_calls == 0:
            return 1.0
        return self.healthy_calls / self.total_calls

    @property
    def antibodies(self) -> list[str]:
        """Chronic flags (>30% of calls). The organism remembers these."""
        if self.total_calls < 3:
            return []
        threshold = self.total_calls * 0.3
        return sorted(f for f, c in self.flags_history.items() if c > threshold)

    def record(self, diagnosis: Diagnosis) -> None:
        """Record a diagnosis into immune memory."""
        self.total_calls += 1
        self.last_diagnosis = diagnosis
        if diagnosis.healthy:
            self.healthy_calls += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            for flag in diagnosis.flags:
                category = flag.split("(")[0] if "(" in flag else flag
                self.flags_history[category] = self.flags_history.get(category, 0) + 1

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "healthy_calls": self.healthy_calls,
            "health_rate": round(self.health_rate, 3),
            "fallback_calls": self.fallback_calls,
            "consecutive_failures": self.consecutive_failures,
            "antibodies": self.antibodies,
            "flags_history": dict(self.flags_history),
        }


# ── @immune Decorator ───────────────────────────────────────────

def immune(
    fallback: Callable | None = None,
    threshold: float = 0.5,
    max_retries: int = 1,
    on_sick: Callable[[Diagnosis], None] | None = None,
):
    """Decorator: Automatic immune system for any LLM call.

    Wraps function(prompt, ...) -> str with:
      1. Classify prompt (inhale)
      2. Call function
      3. Diagnose response (5 layers)
      4. If sick + fallback: retry with fallback
      5. Record immune state (compound learning)

    Args:
        fallback: Callable(prompt, ...) -> str to try when primary is sick.
        threshold: Max hex delta before flagging (0.0-1.0).
        max_retries: How many fallback attempts (default 1).
        on_sick: Optional callback when a response is diagnosed sick.

    Access state via decorated_fn.immune_state:
        my_fn.immune_state.health_rate
        my_fn.immune_state.antibodies
    """

    def decorator(fn: Callable) -> Callable:
        state = ImmuneState()
        _hex = HexBreath()

        @functools.wraps(fn)
        def wrapper(prompt: str, *args, **kwargs) -> str:
            prompt_hex = _hex.classify(prompt)

            response = fn(prompt, *args, **kwargs)
            diagnosis = diagnose(
                prompt, response, prompt_hex=prompt_hex, hex_threshold=threshold,
            )
            state.record(diagnosis)

            if diagnosis.healthy:
                return response

            # Sick. Try fallback?
            if fallback is not None and max_retries > 0:
                state.fallback_calls += 1

                if on_sick is not None:
                    on_sick(diagnosis)

                fallback_response = fallback(prompt, *args, **kwargs)
                fb_diag = diagnose(
                    prompt, fallback_response,
                    prompt_hex=prompt_hex, hex_threshold=threshold,
                )

                if fb_diag.healthy or fb_diag.composite_score > diagnosis.composite_score:
                    state.record(fb_diag)
                    return fallback_response

            # Return original even if sick. Never swallow responses.
            return response

        wrapper.immune_state = state  # type: ignore[attr-defined]
        wrapper._immune_threshold = threshold  # type: ignore[attr-defined]
        return wrapper

    return decorator


# ── Immune Monitor (Multi-Model) ────────────────────────────────

class ImmuneMonitor:
    """Track immune health across multiple models.

    The organism-level immune system. Watches ALL models,
    detects chronic illness, and knows which models are healthy.

    Usage:
        monitor = ImmuneMonitor()
        d = monitor.check("qwen3-14b", prompt, response)
        d = monitor.check("claude-3-haiku", prompt, response)
        print(monitor.report())
        print(monitor.healthiest())
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self._hex = HexBreath()
        self._threshold = threshold
        self._states: dict[str, ImmuneState] = {}

    def check(self, model: str, prompt: str, response: str) -> Diagnosis:
        """Diagnose and record."""
        if model not in self._states:
            self._states[model] = ImmuneState()
        d = diagnose(prompt, response, hex_threshold=self._threshold)
        self._states[model].record(d)
        return d

    def health(self, model: str) -> float:
        """Health rate for one model."""
        s = self._states.get(model)
        return s.health_rate if s else 1.0

    def healthiest(self) -> str | None:
        """Model with highest health rate (min 3 calls)."""
        candidates = [
            (name, s.health_rate)
            for name, s in self._states.items()
            if s.total_calls >= 3
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda x: x[1])[0]

    def report(self) -> dict:
        """Full immune system report."""
        models = {}
        for name, s in sorted(self._states.items()):
            models[name] = s.to_dict()

        total = sum(s.total_calls for s in self._states.values())
        healthy = sum(s.healthy_calls for s in self._states.values())

        return {
            "system_health": round(healthy / max(total, 1), 3),
            "total_calls": total,
            "models_monitored": len(self._states),
            "healthiest": self.healthiest(),
            "models": models,
        }
