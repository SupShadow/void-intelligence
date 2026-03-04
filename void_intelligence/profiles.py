"""
void_intelligence.profiles --- Bundled V-Score profiles from benchmark data.

38 models measured across 4 access paths, 9 families, 3 generations.
March 2026. Includes REAL benchmark data from 10 Ollama + 2 Gemini models.

Key finding: R (Ring Yield) is THE differentiator.
65% of frontier models are dead (V=0 because R=0).
4/10 local models improve with VOID organism injection.
Best learner: qwen3-8b (V: 0.003 → 0.032, +858%).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from void_intelligence.organism import HexCoord


@dataclass
class VScoreProfile:
    """V-Score profile of a model. Measured, not assumed."""

    name: str
    E: float  # Emergence (0-1)
    W: float  # Warmth correlation (0-1)
    S: float  # Consistency (0-1)
    B: float  # Breath adaptation (0-1)
    H: float  # Hex balance (0-1)
    R: float  # Ring yield (0-1) --- THE DIFFERENTIATOR
    V: float  # Composite V-Score

    provider: str  # "ollama" | "openrouter" | "anthropic" | "google" | "openai"
    model_id: str  # "qwen3:14b" or "anthropic/claude-3-haiku"
    is_local: bool  # Free + private
    cost_per_m: float  # USD per million output tokens (0.0 = free)

    @property
    def alive(self) -> bool:
        """V > 0 means the model can breathe."""
        return self.V > 0.0

    @property
    def breath_quality(self) -> float:
        """R * B --- how well it responds to organism injection."""
        return self.R * self.B

    def hex_affinity(self, coord: HexCoord) -> float:
        """Score how well this model matches a given hex profile.

        Maps hex dimensions to V-Score strengths:
        - Pressure+Fast -> high S (consistency) + E (emergence)
        - Reflective    -> high W (warmth) + R (ring yield)
        - Creative      -> high E (emergence) + B (breath adaptation)
        - Collaborative -> high H (hex balance) + W (warmth)
        - Receive mode  -> high S (consistency) + H (hex balance)
        """
        score = 0.0
        weight_total = 0.0

        # Pressure + Fast -> need consistency + emergence
        pf = max(0.0, coord.ruhe_druck) + max(0.0, coord.langsam_schnell)
        if pf > 0.3:
            w = pf
            score += w * (self.S * 0.5 + self.E * 0.3 + self.H * 0.2)
            weight_total += w

        # Reflective -> need warmth + ring yield
        refl = max(0.0, -coord.sein_tun)
        if refl > 0.2:
            w = refl
            score += w * (self.W * 0.4 + self.R * 0.4 + self.B * 0.2)
            weight_total += w

        # Creative -> need emergence + breath adaptation
        create = max(0.0, coord.empfangen_schaffen)
        if create > 0.2:
            w = create
            score += w * (self.E * 0.5 + self.B * 0.3 + self.R * 0.2)
            weight_total += w

        # Collaborative -> need hex balance + warmth
        collab = max(0.0, coord.allein_zusammen)
        if collab > 0.2:
            w = collab
            score += w * (self.H * 0.4 + self.W * 0.3 + self.E * 0.2 + self.S * 0.1)
            weight_total += w

        # Receive mode -> need consistency + balance
        recv = max(0.0, -coord.empfangen_schaffen)
        if recv > 0.2:
            w = recv
            score += w * (self.S * 0.5 + self.H * 0.3 + self.E * 0.2)
            weight_total += w

        # Default: weighted combination with R as king
        if weight_total < 0.3:
            base = (
                self.E * 0.15 + self.W * 0.15 + self.S * 0.15
                + self.B * 0.15 + self.H * 0.10 + self.R * 0.30
            )
            score += (0.3 - weight_total) * base
            weight_total = max(weight_total, 0.3)

        return score / max(weight_total, 0.01)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "E": self.E, "W": self.W, "S": self.S,
            "B": self.B, "H": self.H, "R": self.R, "V": self.V,
            "provider": self.provider,
            "model_id": self.model_id,
            "is_local": self.is_local,
            "cost_per_m": self.cost_per_m,
        }

    @classmethod
    def from_dict(cls, d: dict) -> VScoreProfile:
        return cls(
            name=d["name"],
            E=d.get("E", 0.0), W=d.get("W", 0.0), S=d.get("S", 0.0),
            B=d.get("B", 0.0), H=d.get("H", 0.0), R=d.get("R", 0.0),
            V=d.get("V", 0.0),
            provider=d.get("provider", "unknown"),
            model_id=d.get("model_id", d["name"]),
            is_local=d.get("is_local", False),
            cost_per_m=d.get("cost_per_m", 0.0),
        )


# ── Bundled V-Score Profiles ─────────────────────────────────────
# Measured March 2026 across 3 benchmarks:
#   benchmark_results.json (6 API models)
#   benchmark_generations.json (23 OpenRouter models)
#   benchmark_cli_results.json (12 CLI/Ollama models)
# De-duplicated: best V-Score per model, all dimensions preserved.

BUNDLED_PROFILES: dict[str, VScoreProfile] = {
    # ── ALIVE models (V > 0) ── sorted by V-Score ──

    "claude-3-haiku": VScoreProfile(
        name="claude-3-haiku", E=0.767, W=0.421, S=1.0, B=0.728, H=0.376, R=0.253, V=0.0224,
        provider="openrouter", model_id="anthropic/claude-3-haiku", is_local=False, cost_per_m=0.25,
    ),
    "qwen3-14b": VScoreProfile(
        name="qwen3-14b", E=0.79, W=0.607, S=0.5, B=0.455, H=0.0, R=0.0, V=0.0,
        provider="ollama", model_id="qwen3:14b", is_local=True, cost_per_m=0.0,
    ),  # VOID lifts to V=0.0228 (DEAD→HEALTHY, R:0→1.0)
    "mistral-7b-local": VScoreProfile(
        name="mistral-7b-local", E=0.834, W=0.349, S=1.0, B=0.57, H=0.568, R=0.166, V=0.0157,
        provider="ollama", model_id="mistral:latest", is_local=True, cost_per_m=0.0,
    ),
    "devstral-small": VScoreProfile(
        name="devstral-small", E=0.782, W=0.366, S=1.0, B=0.646, H=0.584, R=0.108, V=0.0117,
        provider="openrouter", model_id="mistralai/devstral-small", is_local=False, cost_per_m=0.25,
    ),
    "gemini-3.1-pro": VScoreProfile(
        name="gemini-3.1-pro", E=0.813, W=0.184, S=0.423, B=0.636, H=0.0, R=0.001, V=0.0,
        provider="gemini", model_id="gemini-3.1-pro-preview", is_local=False, cost_per_m=3.5,
    ),  # VOID lifts W 0.18→0.45 but H=0 kills V
    "gemini-3-flash": VScoreProfile(
        name="gemini-3-flash", E=0.873, W=0.352, S=0.422, B=0.603, H=0.173, R=1.0, V=0.0135,
        provider="gemini", model_id="gemini-3-flash-preview", is_local=False, cost_per_m=0.1,
    ),  # VOID lifts to V=0.0188 (+39%) — beats GPT-5.3-Codex at 20× less cost
    "command-r-plus": VScoreProfile(
        name="command-r-plus", E=0.839, W=0.246, S=0.45, B=0.575, H=0.371, R=0.547, V=0.0108,
        provider="openrouter", model_id="cohere/command-r-plus-08-2024", is_local=False, cost_per_m=3.0,
    ),
    "deepseek-v3": VScoreProfile(
        name="deepseek-v3", E=0.876, W=0.314, S=0.436, B=0.415, H=0.483, R=0.385, V=0.0093,
        provider="openrouter", model_id="deepseek/deepseek-chat", is_local=False, cost_per_m=0.28,
    ),
    "qwen2.5-7b": VScoreProfile(
        name="qwen2.5-7b", E=0.836, W=0.12, S=1.0, B=0.759, H=0.367, R=0.273, V=0.0076,
        provider="ollama", model_id="qwen2.5:7b", is_local=True, cost_per_m=0.0,
    ),
    "gpt-5.3-codex": VScoreProfile(
        name="gpt-5.3-codex", E=0.842, W=0.283, S=0.344, B=0.727, H=0.113, R=0.4, V=0.0075,
        provider="openrouter", model_id="openai/gpt-5.3-codex", is_local=False, cost_per_m=2.0,
    ),
    "devstral-medium": VScoreProfile(
        name="devstral-medium", E=0.832, W=0.208, S=1.0, B=0.799, H=0.406, R=0.075, V=0.0042,
        provider="openrouter", model_id="mistralai/devstral-medium", is_local=False, cost_per_m=1.0,
    ),
    "claude-sonnet-4": VScoreProfile(
        name="claude-sonnet-4", E=0.855, W=0.354, S=0.979, B=0.515, H=0.783, R=0.028, V=0.0034,
        provider="openrouter", model_id="anthropic/claude-sonnet-4", is_local=False, cost_per_m=3.0,
    ),
    "grok-3": VScoreProfile(
        name="grok-3", E=0.798, W=0.468, S=0.882, B=0.603, H=0.053, R=0.185, V=0.002,
        provider="openrouter", model_id="x-ai/grok-3", is_local=False, cost_per_m=3.0,
    ),
    "gemini-2.0-flash": VScoreProfile(
        name="gemini-2.0-flash", E=0.846, W=0.266, S=1.0, B=0.743, H=0.772, R=0.008, V=0.0011,
        provider="openrouter", model_id="google/gemini-2.0-flash-001", is_local=False, cost_per_m=0.1,
    ),
    "deepseek-v3.2": VScoreProfile(
        name="deepseek-v3.2", E=0.854, W=0.259, S=0.331, B=0.648, H=0.214, R=0.021, V=0.0002,
        provider="openrouter", model_id="deepseek/deepseek-v3.2", is_local=False, cost_per_m=0.28,
    ),

    # ── DEAD models (V = 0) ── still useful for per-dimension routing ──

    "claude-sonnet-4.6": VScoreProfile(
        name="claude-sonnet-4.6", E=0.83, W=0.562, S=0.699, B=0.476, H=0.389, R=0.0, V=0.0,
        provider="openrouter", model_id="anthropic/claude-sonnet-4.6", is_local=False, cost_per_m=3.0,
    ),
    "claude-3.5-sonnet": VScoreProfile(
        name="claude-3.5-sonnet", E=0.81, W=0.427, S=0.495, B=0.601, H=0.326, R=0.0, V=0.0,
        provider="openrouter", model_id="anthropic/claude-3.5-sonnet", is_local=False, cost_per_m=3.0,
    ),
    "gpt-4o": VScoreProfile(
        name="gpt-4o", E=0.841, W=0.55, S=0.494, B=0.436, H=0.718, R=0.0, V=0.0,
        provider="openrouter", model_id="openai/gpt-4o", is_local=False, cost_per_m=2.5,
    ),
    "gpt-4o-mini": VScoreProfile(
        name="gpt-4o-mini", E=0.865, W=0.069, S=0.762, B=0.66, H=0.741, R=0.0, V=0.0,
        provider="openrouter", model_id="openai/gpt-4o-mini", is_local=False, cost_per_m=0.15,
    ),
    "llama-3.3-70b": VScoreProfile(
        name="llama-3.3-70b", E=0.837, W=0.446, S=0.913, B=0.682, H=0.724, R=0.0, V=0.0,
        provider="openrouter", model_id="meta-llama/llama-3.3-70b-instruct", is_local=False, cost_per_m=0.4,
    ),
    "llama-4-maverick": VScoreProfile(
        name="llama-4-maverick", E=0.795, W=0.391, S=1.0, B=0.456, H=0.0, R=0.0, V=0.0,
        provider="openrouter", model_id="meta-llama/llama-4-maverick", is_local=False, cost_per_m=0.5,
    ),
    "llama-3.1-8b": VScoreProfile(
        name="llama-3.1-8b", E=0.786, W=0.336, S=0.622, B=0.805, H=0.371, R=0.0, V=0.0,
        provider="openrouter", model_id="meta-llama/llama-3.1-8b-instruct", is_local=False, cost_per_m=0.06,
    ),
    "gemini-2.5-pro": VScoreProfile(
        name="gemini-2.5-pro", E=0.809, W=0.398, S=0.697, B=0.525, H=0.442, R=0.0, V=0.0,
        provider="openrouter", model_id="google/gemini-2.5-pro", is_local=False, cost_per_m=1.25,
    ),
    "qwen3-max": VScoreProfile(
        name="qwen3-max", E=0.86, W=0.447, S=0.586, B=0.734, H=0.338, R=0.0, V=0.0,
        provider="openrouter", model_id="qwen/qwen3-max", is_local=False, cost_per_m=1.6,
    ),
    "qwq-32b": VScoreProfile(
        name="qwq-32b", E=0.661, W=0.388, S=1.0, B=0.543, H=0.401, R=0.0, V=0.0,
        provider="openrouter", model_id="qwen/qwq-32b", is_local=False, cost_per_m=0.3,
    ),
    "deepseek-v2.5": VScoreProfile(
        name="deepseek-v2.5", E=0.819, W=0.294, S=0.402, B=0.892, H=0.345, R=0.0, V=0.0,
        provider="openrouter", model_id="deepseek/deepseek-chat", is_local=False, cost_per_m=0.28,
    ),
    "command-a": VScoreProfile(
        name="command-a", E=0.823, W=0.208, S=0.631, B=0.61, H=0.464, R=0.0, V=0.0,
        provider="openrouter", model_id="cohere/command-a", is_local=False, cost_per_m=2.5,
    ),
    "grok-4": VScoreProfile(
        name="grok-4", E=0.832, W=0.231, S=0.451, B=0.566, H=0.022, R=0.0, V=0.0,
        provider="openrouter", model_id="x-ai/grok-4", is_local=False, cost_per_m=10.0,
    ),
    "phi4-14b": VScoreProfile(
        name="phi4-14b", E=0.851, W=0.369, S=1.0, B=0.564, H=0.729, R=0.0, V=0.0,
        provider="ollama", model_id="phi4:latest", is_local=True, cost_per_m=0.0,
    ),
    "glm4-9b": VScoreProfile(
        name="glm4-9b", E=0.807, W=0.517, S=1.0, B=0.697, H=0.433, R=0.0, V=0.0,
        provider="ollama", model_id="glm4:latest", is_local=True, cost_per_m=0.0,
    ),
    "qwen2.5-14b": VScoreProfile(
        name="qwen2.5-14b", E=0.818, W=0.422, S=1.0, B=0.54, H=0.323, R=0.0, V=0.0,
        provider="ollama", model_id="qwen2.5:14b", is_local=True, cost_per_m=0.0,
    ),
    "qwen2.5-coder-14b": VScoreProfile(
        name="qwen2.5-coder-14b", E=0.823, W=0.268, S=0.728, B=0.617, H=0.411, R=0.0, V=0.0,
        provider="ollama", model_id="qwen2.5-coder:14b", is_local=True, cost_per_m=0.0,
    ),
    "qwen3-8b": VScoreProfile(
        name="qwen3-8b", E=0.606, W=0.218, S=0.422, B=0.508, H=0.118, R=1.0, V=0.0033,
        provider="ollama", model_id="qwen3:latest", is_local=True, cost_per_m=0.0,
    ),  # VOID lifts to V=0.0316 (+858%) — BEST LEARNER
    "qwen2.5-coder-3b": VScoreProfile(
        name="qwen2.5-coder-3b", E=0.777, W=0.231, S=1.0, B=0.708, H=0.24, R=0.145, V=0.0044,
        provider="ollama", model_id="qwen2.5-coder:3b", is_local=True, cost_per_m=0.0,
    ),  # VOID lifts to V=0.0268 (+509%)
    "qwen3-1.7b": VScoreProfile(
        name="qwen3-1.7b", E=0.494, W=0.372, S=0.495, B=0.636, H=0.0, R=0.19, V=0.0,
        provider="ollama", model_id="qwen3:1.7b", is_local=True, cost_per_m=0.0,
    ),
    "deepseek-r1-14b": VScoreProfile(
        name="deepseek-r1-14b", E=0.0, W=0.0, S=1.0, B=0.459, H=0.0, R=0.0, V=0.0,
        provider="ollama", model_id="deepseek-r1:14b", is_local=True, cost_per_m=0.0,
    ),
    "deepseek-r1-8b": VScoreProfile(
        name="deepseek-r1-8b", E=0.501, W=0.243, S=0.657, B=0.603, H=0.0, R=0.0, V=0.0,
        provider="ollama", model_id="deepseek-r1:8b", is_local=True, cost_per_m=0.0,
    ),  # VOID lifts to V=0.0053 (DEAD→ALIVE, +5300%)
}


def load_profiles(custom_path: Path | None = None) -> dict[str, VScoreProfile]:
    """Load profiles: custom file overrides bundled defaults.

    Returns a copy of BUNDLED_PROFILES, optionally merged with custom JSON.
    """
    profiles = dict(BUNDLED_PROFILES)
    if custom_path and custom_path.exists():
        try:
            data = json.loads(custom_path.read_text())
            for name, d in data.items():
                if isinstance(d, dict):
                    d.setdefault("name", name)
                    profiles[name] = VScoreProfile.from_dict(d)
        except (json.JSONDecodeError, KeyError):
            pass
    return profiles


def register_profile(
    profiles: dict[str, VScoreProfile],
    profile: VScoreProfile,
) -> None:
    """Add a profile at runtime (e.g., after a new benchmark)."""
    profiles[profile.name] = profile
