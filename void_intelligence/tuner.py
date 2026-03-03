"""
void_intelligence.tuner --- The Stribeck Tuner.

Richard Stribeck (Stribeck Curve, 1902): Every parameter has a sweet spot.
Too little friction (temp=0) = dead repetition. Too much (temp=2) = chaos.
The MINIMUM is the sweet spot = delta_opt.

This module auto-tunes LLM parameters per model per hex region,
using immune system feedback as the convergence signal.

Usage:
    from void_intelligence import StribeckTuner, ParameterSet

    tuner = StribeckTuner()

    # Get optimal parameters for a prompt's hex profile
    params = tuner.tune(hex_coord, model="qwen3-14b")

    # After getting a diagnosis, record feedback
    tuner.record(hex_coord, params, diagnosis, model="qwen3-14b")

    # The map converges over time. Check the Stribeck report:
    print(tuner.stribeck_report())
    print(tuner.delta_opt_distance(hex_coord, model="qwen3-14b"))
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from void_intelligence.organism import HexCoord


# -- ParameterSet: What we tune -------------------------------------------

@dataclass
class ParameterSet:
    """Tunable LLM parameters. The axes of the Stribeck surface.

    Each parameter has a friction profile:
        temperature:       0.0 = dead repetition, 2.0 = chaos
        top_p:             0.0 = single token,    1.0 = full vocab
        max_tokens:        too low = truncation,   too high = hallucination
        context_intensity: 0.0 = no rings,         1.0 = full graph injection
    """

    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    context_intensity: float = 0.6

    # Stribeck metadata (NOT tuning targets)
    confidence: float = 0.0   # 0-1: how confident in these values
    observations: int = 0     # how many data points inform this

    @property
    def at_delta_opt(self) -> bool:
        """Is confidence high enough to be at the Stribeck minimum?"""
        return self.confidence >= 0.5 and self.observations >= 5

    def distance_from(self, other: "ParameterSet") -> float:
        """Euclidean distance in parameter space. Normalized."""
        diffs = [
            (self.temperature - other.temperature) / 2.0,       # range 0-2
            (self.top_p - other.top_p),                          # range 0-1
            (self.max_tokens - other.max_tokens) / 8192,         # range ~128-8192
            (self.context_intensity - other.context_intensity),   # range 0-1
        ]
        return math.sqrt(sum(d * d for d in diffs) / 4)

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "context_intensity": self.context_intensity,
            "confidence": round(self.confidence, 3),
            "observations": self.observations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParameterSet":
        return cls(
            temperature=float(data.get("temperature", 0.7)),
            top_p=float(data.get("top_p", 0.9)),
            max_tokens=int(data.get("max_tokens", 2048)),
            context_intensity=float(data.get("context_intensity", 0.6)),
            confidence=float(data.get("confidence", 0.0)),
            observations=int(data.get("observations", 0)),
        )


# -- Hex defaults: initial guess from hex profile -----------------------

def _defaults_from_hex(coord: HexCoord) -> ParameterSet:
    """Initial parameter guess from hex classification.

    The hex profile tells us WHAT KIND of task this is.
    Different tasks have different Stribeck minima:
        - Urgent + fast = lower temp, fewer tokens (focused)
        - Creative = higher temp (diverse exploration)
        - Reflective = moderate temp, more tokens (depth)
        - Collaborative = more context (organism state matters)
    """
    temp = 0.7
    top_p = 0.9
    max_tokens = 2048
    ctx = 0.6

    # Pressure axis: urgent tasks need focused, precise output
    if coord.ruhe_druck > 0.3:
        temp -= 0.15
        max_tokens = min(max_tokens, 1536)
    elif coord.ruhe_druck < -0.3:
        # Calm: space for exploration
        temp += 0.05

    # Create axis: creative tasks benefit from higher temperature
    if coord.empfangen_schaffen > 0.3:
        temp += 0.15
        top_p = min(top_p + 0.05, 1.0)
    elif coord.empfangen_schaffen < -0.3:
        # Receiving: absorbing, lower diversity
        temp -= 0.05

    # Speed axis: fast = concise, slow = thorough
    if coord.langsam_schnell > 0.3:
        max_tokens = min(max_tokens, 1024)
    elif coord.langsam_schnell < -0.3:
        max_tokens = max(max_tokens, 4096)
        ctx = min(ctx + 0.15, 1.0)

    # Together axis: collaborative tasks need more organism context
    if coord.allein_zusammen > 0.3:
        ctx = min(ctx + 0.15, 1.0)

    # Being axis: reflective tasks need moderate temp + more depth
    if coord.sein_tun < -0.3:
        max_tokens = max(max_tokens, 3072)
        temp = max(0.5, min(temp, 0.8))
    elif coord.sein_tun > 0.3:
        # Action: decisive, lower temp
        temp -= 0.05

    # Resonance axis: discussion = more context
    if coord.stille_resonanz > 0.3:
        ctx = min(ctx + 0.1, 1.0)

    return ParameterSet(
        temperature=round(max(0.0, min(2.0, temp)), 2),
        top_p=round(max(0.0, min(1.0, top_p)), 2),
        max_tokens=max(256, min(8192, max_tokens)),
        context_intensity=round(max(0.0, min(1.0, ctx)), 2),
    )


# -- StribeckTuner: the convergence engine --------------------------------

class StribeckTuner:
    """Auto-tune LLM parameters per model per hex region.

    The Stribeck curve (1902): friction vs. sliding speed.
    Too slow = static friction (stuck). Too fast = chaos.
    The MINIMUM between these extremes is the sweet spot.

    For LLMs:
        - Temperature too low (0.0) = repetitive, dead output
        - Temperature too high (2.0) = incoherent chaos
        - Stribeck minimum = the temperature where output is ALIVE

    This tuner finds that minimum for ALL parameters (temp, top_p,
    max_tokens, context_intensity) across ALL hex regions, using
    immune system diagnosis as the convergence signal.

    Usage:
        tuner = StribeckTuner()

        # Get parameters for a prompt's hex profile
        params = tuner.tune(coord, model="qwen3-14b")

        # After immune diagnosis, record feedback
        from void_intelligence import diagnose
        diag = diagnose(prompt, response)
        tuner.record(coord, params, diag, model="qwen3-14b")

        # Over time, the map converges to optimal params per region
        print(tuner.delta_opt_distance(coord, "qwen3-14b"))  # 0.0 = at minimum
    """

    def __init__(self, learning_rate: float = 0.05) -> None:
        self._lr = learning_rate
        # Key: "model:r,r,r,r,r,r" or just "r,r,r,r,r,r" for model-agnostic
        self._map: dict[str, ParameterSet] = {}

    # -- Public API -------------------------------------------------------

    def tune(self, coord: HexCoord, model: str = "") -> ParameterSet:
        """Get optimal parameters for a hex coordinate.

        Priority:
          1. Model-specific learned params (if enough confidence)
          2. Generic learned params (model="")
          3. Hex-based defaults (no data yet)
        """
        # Model-specific
        if model:
            key = self._key(model, coord)
            if key in self._map and self._map[key].observations > 0:
                return self._map[key]

        # Generic
        key = self._key("", coord)
        if key in self._map and self._map[key].observations > 0:
            return self._map[key]

        # Defaults from hex
        return _defaults_from_hex(coord)

    def record(
        self,
        coord: HexCoord,
        params: ParameterSet,
        diagnosis: object,
        model: str = "",
    ) -> None:
        """Record immune feedback. Each call refines the Stribeck surface.

        Args:
            coord: The hex classification of the prompt.
            params: The parameters that were used.
            diagnosis: A Diagnosis object (from immune.diagnose()).
            model: The model name (for model-specific tuning).
        """
        key = self._key(model, coord)

        # Initialize from current params if first observation
        if key not in self._map:
            self._map[key] = ParameterSet(
                temperature=params.temperature,
                top_p=params.top_p,
                max_tokens=params.max_tokens,
                context_intensity=params.context_intensity,
            )

        current = self._map[key]
        current.observations += 1
        lr = self._lr

        # Extract diagnosis properties (duck typing for loose coupling)
        healthy = getattr(diagnosis, "healthy", True)
        flags = getattr(diagnosis, "flags", [])

        if healthy:
            # Good! Increase confidence, nudge toward used params
            current.confidence = min(1.0, current.confidence + lr)
            current.temperature += lr * (params.temperature - current.temperature)
            current.top_p += lr * (params.top_p - current.top_p)
            current.context_intensity += lr * (params.context_intensity - current.context_intensity)
        else:
            # Sick. Decrease confidence, adjust based on specific failures
            current.confidence = max(0.0, current.confidence - lr * 2)

            for flag in flags:
                category = flag.split("(")[0] if "(" in flag else flag
                self._adjust_for_flag(current, category, lr)

        # Clamp all values
        self._clamp(current)

    def delta_opt_distance(self, coord: HexCoord, model: str = "") -> float:
        """Distance from Stribeck minimum. 0.0 = at minimum, 1.0 = no data."""
        key = self._key(model, coord)
        if key not in self._map:
            # Try generic
            key = self._key("", coord)
        if key not in self._map:
            return 1.0
        return round(1.0 - self._map[key].confidence, 3)

    # -- Adjustment logic -------------------------------------------------

    def _adjust_for_flag(self, params: ParameterSet, category: str, lr: float) -> None:
        """Adjust parameters based on a specific immune flag.

        Each flag type maps to specific parameter adjustments:
            repetition    -> temperature too LOW (static friction)
            too_short     -> max_tokens too low
            too_long      -> max_tokens too high
            refusal       -> context overwhelming model, reduce intensity
            hex_divergent -> context wrong, increase intensity to re-anchor
            incoherent    -> temperature too HIGH (turbulent friction)
        """
        if category == "repetition":
            # Static friction: increase temperature to break out
            params.temperature += lr * 3
            params.top_p = min(1.0, params.top_p + lr)
        elif category == "too_short":
            # Not enough output space
            params.max_tokens = min(8192, int(params.max_tokens * 1.5))
        elif category == "too_long":
            # Hallucination: reduce output space
            params.max_tokens = max(256, int(params.max_tokens * 0.7))
        elif category == "refusal":
            # Model overwhelmed by context -> reduce injection
            params.context_intensity = max(0.0, params.context_intensity - lr * 3)
            # Also try slightly higher temp to break out of refusal mode
            params.temperature += lr
        elif category == "hex_divergent":
            # Response drifted from prompt -> increase context anchoring
            params.context_intensity = min(1.0, params.context_intensity + lr * 2)
        elif category == "incoherent":
            # Turbulent friction: reduce temperature
            params.temperature -= lr * 3
            params.top_p = max(0.0, params.top_p - lr)

    @staticmethod
    def _clamp(p: ParameterSet) -> None:
        """Keep parameters in valid ranges."""
        p.temperature = round(max(0.0, min(2.0, p.temperature)), 3)
        p.top_p = round(max(0.0, min(1.0, p.top_p)), 3)
        p.max_tokens = max(128, min(8192, p.max_tokens))
        p.context_intensity = round(max(0.0, min(1.0, p.context_intensity)), 3)

    # -- Region quantization ----------------------------------------------

    @staticmethod
    def _quantize(coord: HexCoord) -> str:
        """Quantize 6D hex coordinate to discrete region.

        Resolution: 0.5 steps -> 5 values per axis (-1, -0.5, 0, 0.5, 1)
        Total regions: 5^6 = 15,625 (but sparse: only populated regions stored)
        """
        def q(v: float) -> float:
            return round(v * 2) / 2  # nearest 0.5

        vals = [
            q(coord.ruhe_druck),
            q(coord.stille_resonanz),
            q(coord.allein_zusammen),
            q(coord.empfangen_schaffen),
            q(coord.sein_tun),
            q(coord.langsam_schnell),
        ]
        return ",".join(f"{v:+.1f}" for v in vals)

    @staticmethod
    def _key(model: str, coord: HexCoord) -> str:
        """Map key: model + quantized hex region."""
        region = StribeckTuner._quantize(coord)
        return f"{model}:{region}" if model else region

    # -- Introspection ----------------------------------------------------

    @property
    def mapped_regions(self) -> int:
        """Number of hex regions with data."""
        return len(self._map)

    @property
    def total_observations(self) -> int:
        """Total recorded diagnoses across all regions."""
        return sum(p.observations for p in self._map.values())

    @property
    def avg_confidence(self) -> float:
        """Average confidence across mapped regions."""
        if not self._map:
            return 0.0
        return sum(p.confidence for p in self._map.values()) / len(self._map)

    def stribeck_report(self) -> dict:
        """Full Stribeck surface report.

        Shows all mapped regions with their current optimal parameters,
        confidence levels, and observation counts.
        """
        if not self._map:
            return {
                "mapped_regions": 0,
                "total_observations": 0,
                "avg_confidence": 0.0,
                "at_delta_opt": 0,
                "regions": {},
            }

        regions = {}
        at_opt = 0
        for key, params in sorted(self._map.items()):
            regions[key] = params.to_dict()
            if params.at_delta_opt:
                at_opt += 1

        return {
            "mapped_regions": len(self._map),
            "total_observations": self.total_observations,
            "avg_confidence": round(self.avg_confidence, 3),
            "at_delta_opt": at_opt,
            "regions": regions,
        }

    def summary(self) -> str:
        """One-line summary."""
        return (
            f"Stribeck: {self.mapped_regions} regions, "
            f"{self.total_observations} observations, "
            f"avg confidence {self.avg_confidence:.2f}"
        )

    # -- Persistence ------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the Stribeck surface."""
        return {
            "version": 1,
            "learning_rate": self._lr,
            "map": {
                key: p.to_dict()
                for key, p in self._map.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StribeckTuner":
        """Restore from dict. Bad data = fresh tuner (never crash)."""
        try:
            tuner = cls(learning_rate=float(data.get("learning_rate", 0.05)))
            for key, pd in data.get("map", {}).items():
                tuner._map[str(key)] = ParameterSet.from_dict(pd)
            return tuner
        except (TypeError, ValueError, KeyError, AttributeError):
            return cls()
