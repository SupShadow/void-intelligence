"""
void_intelligence.edge --- Stateless VOID for Serverless & Edge.

Wozniak made the Apple II run on a 6502 with 4KB RAM.
This module makes VOID run in Cloudflare Workers, AWS Lambda,
Deno Deploy, Vercel Edge, or any constrained environment.

Design constraints:
    - No filesystem access
    - No global state
    - No imports beyond stdlib
    - Every function is PURE: input → output, no side effects
    - All state is passed in, returned out (functional style)
    - Serializable inputs and outputs (JSON-safe)

Usage:
    # In a Cloudflare Worker / Lambda / Edge Function:
    from void_intelligence.edge import classify, diagnose, score, breathe

    result = classify("Write me a sales email")
    # → {"ruhe_druck": 0.3, "stille_resonanz": -0.2, ...}

    health = diagnose("prompt", "response")
    # → {"healthy": true, "flags": [], "hex_delta": 0.12, ...}

    v = score("prompt", "response", "model-name")
    # → {"V": 0.034, "status": "ALIVE", "components": {...}}

    state = breathe("prompt", "response")
    # → Full breath cycle: classify + diagnose + score in one call
"""

from __future__ import annotations

import math
import re
from typing import Any


# ── HexBreath (Stateless) ────────────────────────────────────

# Keyword signals for hex classification
_HEX_SIGNALS: dict[str, list[tuple[str, float]]] = {
    "ruhe_druck": [
        ("urgent", 0.7), ("asap", 0.8), ("deadline", 0.6), ("critical", 0.7),
        ("emergency", 0.9), ("hurry", 0.6), ("sofort", 0.7), ("dringend", 0.8),
        ("calm", -0.5), ("relax", -0.6), ("peaceful", -0.7), ("ruhig", -0.5),
        ("meditation", -0.8), ("gentle", -0.4), ("sanft", -0.5),
    ],
    "stille_resonanz": [
        ("discuss", 0.5), ("talk", 0.4), ("meeting", 0.5), ("team", 0.5),
        ("collaborate", 0.6), ("share", 0.4), ("besprechen", 0.5),
        ("silent", -0.6), ("quiet", -0.5), ("alone", -0.5), ("private", -0.4),
        ("think", -0.3), ("reflect", -0.5), ("stille", -0.6), ("nachdenken", -0.5),
    ],
    "allein_zusammen": [
        ("we", 0.4), ("team", 0.6), ("together", 0.7), ("group", 0.5),
        ("community", 0.6), ("wir", 0.4), ("zusammen", 0.7), ("gemeinsam", 0.6),
        ("solo", -0.6), ("alone", -0.7), ("personal", -0.4), ("private", -0.5),
        ("myself", -0.5), ("allein", -0.7), ("ich", -0.3),
    ],
    "empfangen_schaffen": [
        ("create", 0.6), ("build", 0.7), ("write", 0.5), ("generate", 0.6),
        ("design", 0.6), ("make", 0.5), ("bauen", 0.7), ("erstellen", 0.6),
        ("schreiben", 0.5), ("entwickeln", 0.6),
        ("read", -0.4), ("learn", -0.5), ("understand", -0.4), ("listen", -0.5),
        ("study", -0.5), ("lesen", -0.4), ("lernen", -0.5), ("verstehen", -0.4),
    ],
    "sein_tun": [
        ("do", 0.4), ("execute", 0.6), ("implement", 0.6), ("fix", 0.5),
        ("run", 0.4), ("deploy", 0.6), ("machen", 0.4), ("umsetzen", 0.6),
        ("be", -0.3), ("feel", -0.5), ("think", -0.4), ("reflect", -0.5),
        ("meditate", -0.7), ("sein", -0.3), ("fühlen", -0.5),
    ],
    "langsam_schnell": [
        ("quick", 0.6), ("fast", 0.7), ("rapid", 0.6), ("brief", 0.4),
        ("short", 0.3), ("schnell", 0.7), ("kurz", 0.4), ("sofort", 0.6),
        ("slow", -0.5), ("careful", -0.4), ("thorough", -0.5), ("deep", -0.5),
        ("detailed", -0.4), ("langsam", -0.5), ("gründlich", -0.5), ("tief", -0.5),
    ],
}


def classify(text: str) -> dict[str, float]:
    """Classify text on 6 hexagonal axes. Pure function, no state.

    Returns dict with 6 axis values in [-1.0, 1.0].
    """
    lower = text.lower()
    words = set(re.findall(r'\w+', lower))

    result: dict[str, float] = {}
    for axis, signals in _HEX_SIGNALS.items():
        score = 0.0
        hits = 0
        for keyword, weight in signals:
            if keyword in words:
                score += weight
                hits += 1
        # Normalize: clamp to [-1, 1]
        if hits > 0:
            score = score / max(hits, 1)
        result[axis] = max(-1.0, min(1.0, score))

    return result


def hex_distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Euclidean distance in 6D hex space. Returns [0, 2]."""
    axes = ["ruhe_druck", "stille_resonanz", "allein_zusammen",
            "empfangen_schaffen", "sein_tun", "langsam_schnell"]
    diffs = [a.get(ax, 0.0) - b.get(ax, 0.0) for ax in axes]
    return math.sqrt(sum(d * d for d in diffs) / 6)


# ── Immune Diagnosis (Stateless) ─────────────────────────────

_REFUSALS = [
    "i cannot", "i can't", "i'm unable", "i am unable",
    "as an ai", "i don't have the ability",
    "ich kann nicht", "ich bin nicht in der lage",
]


def diagnose(
    prompt: str,
    response: str,
    *,
    hex_threshold: float = 0.5,
    min_length: int = 10,
    max_length: int = 50_000,
) -> dict[str, Any]:
    """Run 5 immune defense layers. Pure function, no state.

    Returns dict with: healthy, hex_delta, flags, layer_scores, severity.
    """
    prompt_hex = classify(prompt)
    response_hex = classify(response)

    flags: list[str] = []
    scores: dict[str, float] = {}

    # Layer 1: HexDelta
    delta = hex_distance(prompt_hex, response_hex)
    scores["hex_delta"] = max(0.0, 1.0 - delta / max(hex_threshold * 2, 0.01))
    if delta > hex_threshold:
        flags.append(f"hex_divergent({delta:.3f})")

    # Layer 2: Length Guard
    rlen = len(response.strip())
    if rlen < min_length:
        flags.append(f"too_short({rlen})")
        scores["length"] = rlen / max(min_length, 1)
    elif rlen > max_length:
        flags.append(f"too_long({rlen})")
        scores["length"] = 0.5
    else:
        scores["length"] = 1.0

    # Layer 3: Refusal Shield
    lower = response.lower()
    scores["refusal"] = 1.0
    for marker in _REFUSALS:
        if marker in lower and rlen < 300:
            flags.append(f"refusal({marker[:20]})")
            scores["refusal"] = 0.2
            break

    # Layer 4: Repetition Scan
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

    # Layer 5: Coherence
    prompt_words = {w for w in prompt.lower().split() if len(w) > 3}
    response_words = {w for w in lower.split() if len(w) > 3}
    scores["coherence"] = 1.0
    if prompt_words and rlen > 50:
        overlap = len(prompt_words & response_words) / len(prompt_words)
        scores["coherence"] = min(1.0, overlap * 2.5)
        if overlap < 0.08:
            flags.append(f"incoherent({overlap:.0%})")

    healthy = len(flags) == 0

    # Severity
    if healthy:
        severity = "healthy"
    elif delta > 0.7 or len(flags) > 3:
        severity = "critical"
    elif len(flags) > 1:
        severity = "sick"
    else:
        severity = "warning"

    return {
        "healthy": healthy,
        "hex_delta": round(delta, 4),
        "response_length": rlen,
        "flags": flags,
        "layer_scores": {k: round(v, 4) for k, v in scores.items()},
        "severity": severity,
        "prompt_hex": prompt_hex,
        "response_hex": response_hex,
    }


# ── V-Score (Stateless) ──────────────────────────────────────

def score(
    prompt: str,
    response: str,
    model: str = "unknown",
) -> dict[str, Any]:
    """Compute V-Score for a prompt-response pair. Pure function.

    V = E × W × S × B × H (multiplicative — one zero kills it)

    Returns dict with: V, model, status, components, flags.
    """
    d = diagnose(prompt, response)
    scores = d["layer_scores"]

    # E = Emergence (coherence + hex closeness)
    e = scores.get("coherence", 0.5) * scores.get("hex_delta", 0.5)

    # W = Warmth (absence of refusal)
    w = scores.get("refusal", 1.0)

    # S = Consistency (absence of repetition)
    s = scores.get("repetition", 1.0)

    # B = Breath (appropriate length)
    b = scores.get("length", 1.0)

    # H = Hex alignment (inverse of hex distance)
    h = max(0.0, 1.0 - d["hex_delta"])

    v = e * w * s * b * h

    # Status
    if v == 0:
        status = "DEAD"
    elif v < 0.005:
        status = "BARELY ALIVE"
    elif v < 0.02:
        status = "ALIVE"
    elif v < 0.1:
        status = "HEALTHY"
    else:
        status = "THRIVING"

    return {
        "V": round(v, 6),
        "model": model,
        "status": status,
        "components": {
            "E_emergence": round(e, 4),
            "W_warmth": round(w, 4),
            "S_consistency": round(s, 4),
            "B_breath": round(b, 4),
            "H_hex": round(h, 4),
        },
        "flags": d["flags"],
        "hex_delta": d["hex_delta"],
    }


# ── Combined Breath (Stateless) ──────────────────────────────

def breathe(
    prompt: str,
    response: str,
    model: str = "unknown",
) -> dict[str, Any]:
    """Full breath cycle: classify + diagnose + score. One call.

    This is the edge-optimized entry point. Single function,
    all you need, JSON in → JSON out.
    """
    prompt_hex = classify(prompt)
    response_hex = classify(response)
    diagnosis = diagnose(prompt, response)
    v_score = score(prompt, response, model)

    return {
        "prompt_hex": prompt_hex,
        "response_hex": response_hex,
        "diagnosis": {
            "healthy": diagnosis["healthy"],
            "severity": diagnosis["severity"],
            "flags": diagnosis["flags"],
        },
        "v_score": v_score,
        "model": model,
    }


# ── Batch Operations ─────────────────────────────────────────

def batch_score(
    pairs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Score multiple prompt-response pairs. Pure function.

    Args:
        pairs: List of {"prompt": ..., "response": ..., "model": ...}

    Returns:
        List of score results
    """
    results = []
    for pair in pairs:
        prompt = pair.get("prompt", "")
        response = pair.get("response", "")
        model = pair.get("model", "unknown")
        results.append(score(prompt, response, model))
    return results


def leaderboard(
    pairs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Score pairs and return sorted leaderboard. Pure function."""
    scores_list = batch_score(pairs)

    # Group by model
    by_model: dict[str, list[float]] = {}
    for s in scores_list:
        model = s["model"]
        by_model.setdefault(model, []).append(s["V"])

    # Average V per model
    board = []
    for model, vs in by_model.items():
        avg_v = sum(vs) / len(vs)
        board.append({
            "model": model,
            "avg_V": round(avg_v, 6),
            "checks": len(vs),
            "status": "THRIVING" if avg_v > 0.1 else "HEALTHY" if avg_v > 0.02 else "ALIVE" if avg_v > 0.005 else "BARELY ALIVE" if avg_v > 0 else "DEAD",
        })

    return sorted(board, key=lambda x: x["avg_V"], reverse=True)
