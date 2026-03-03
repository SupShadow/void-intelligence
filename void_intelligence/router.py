"""
void_intelligence.router --- The Atem-Router.

Routes prompts to the model that BREATHES best, not thinks best.
Uses HexBreath classification + V-Score profiles + persistent organism state.

The industry routes by capability. We route by breath.

Usage:
    from void_intelligence import AtemRouter

    router = AtemRouter()
    router.register_adapter("qwen3-14b", my_ollama_fn)
    result = router.breathe("Help me plan the campaign strategy")
    # -> Routes to qwen3-14b (R=0.99, FREE), injects organism state
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from void_intelligence.organism import HexBreath, HexCoord, OrganismBreather
from void_intelligence.profiles import VScoreProfile, BUNDLED_PROFILES

# (prompt, system_prompt) -> response
ModelCallable = Callable[[str, str], str]


@dataclass
class AtemDecision:
    """A routing decision. Named Atem (German: breath) because routing IS breathing."""

    prompt: str
    hex: HexCoord
    selected_model: str
    profile: VScoreProfile
    system_prompt: str
    alternatives: list[str]
    reason: str


@dataclass
class AtemResult:
    """Result after a complete breath cycle."""

    decision: AtemDecision
    response: str
    new_rings: list[str]
    vitals_after: dict
    latency_ms: float


class AtemRouter:
    """V-Score-based model router. The organism decides who breathes.

    Usage:
        router = AtemRouter()
        router.register_adapter("qwen3-14b", my_adapter)
        result = router.breathe("Help me plan the campaign")

    Or just classify + select (no execution):
        decision = router.inhale("Help me plan the campaign")
        print(decision.selected_model, decision.system_prompt)
    """

    def __init__(
        self,
        state_dir: Path | None = None,
        profiles: dict[str, VScoreProfile] | None = None,
        prefer_local: bool = True,
        max_cost_per_m: float = 100.0,
    ) -> None:
        self._hex = HexBreath()
        self._profiles = profiles if profiles is not None else dict(BUNDLED_PROFILES)
        self._state_dir = state_dir or Path.home() / ".void-intelligence"
        self._organisms: dict[str, OrganismBreather] = {}
        self._adapters: dict[str, ModelCallable] = {}
        self._prefer_local = prefer_local
        self._max_cost = max_cost_per_m

    # ── Registration ──────────────────────────────────────────────

    def register_adapter(self, model_name: str, fn: ModelCallable) -> None:
        """Register a callable adapter for a model.

        The adapter signature: fn(prompt: str, system: str = "") -> str
        """
        self._adapters[model_name] = fn

    def register_profile(self, profile: VScoreProfile) -> None:
        """Add or override a V-Score profile."""
        self._profiles[profile.name] = profile

    # ── Organism Management ───────────────────────────────────────

    def _get_organism(self, model_name: str) -> OrganismBreather:
        """Load or create per-model organism. Cached in session."""
        if model_name not in self._organisms:
            state_path = self._state_path(model_name)
            if state_path.exists():
                try:
                    data = json.loads(state_path.read_text())
                    self._organisms[model_name] = OrganismBreather.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    self._organisms[model_name] = OrganismBreather()
            else:
                self._organisms[model_name] = OrganismBreather()
        return self._organisms[model_name]

    def _save_organism(self, model_name: str) -> None:
        """Persist organism state to disk."""
        if model_name not in self._organisms:
            return
        state_path = self._state_path(model_name)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(
            self._organisms[model_name].to_dict(), indent=2,
        ))

    def _state_path(self, model_name: str) -> Path:
        safe_name = model_name.replace("/", "_").replace(":", "_")
        return self._state_dir / "organisms" / safe_name / "state.json"

    # ── The Breath Cycle ──────────────────────────────────────────

    def inhale(self, prompt: str) -> AtemDecision:
        """Classify + Select. No execution.

        1. HexBreath classifies prompt -> 6D coordinates
        2. Score all profiles against hex affinity
        3. Filter by cost + adapter availability
        4. Select best model
        5. Build organism system prompt injection
        """
        coord = self._hex.classify(prompt)
        ranked = self._rank_models(coord)

        if not ranked:
            # Fallback: pick first available profile
            for name in self._profiles:
                ranked = [(name, 0.0)]
                break

        selected_name, score = ranked[0]
        profile = self._profiles[selected_name]
        organism = self._get_organism(selected_name)

        # Inhale on the organism
        organism.inhale(prompt)

        system_prompt = self._build_system_prompt(coord, organism, profile)
        alternatives = [name for name, _ in ranked[1:6]]

        reason = self._explain(selected_name, profile, coord, score)

        return AtemDecision(
            prompt=prompt,
            hex=coord,
            selected_model=selected_name,
            profile=profile,
            system_prompt=system_prompt,
            alternatives=alternatives,
            reason=reason,
        )

    def exhale(
        self,
        decision: AtemDecision,
        response: str,
        learnings: list[str] | None = None,
    ) -> AtemResult:
        """Record what happened. Grow the organism. Persist state."""
        organism = self._get_organism(decision.selected_model)
        exhale_data = organism.exhale(response, learnings)

        self._save_organism(decision.selected_model)

        return AtemResult(
            decision=decision,
            response=response,
            new_rings=exhale_data.get("new_rings", []),
            vitals_after=organism.vitals(),
            latency_ms=0.0,
        )

    def breathe(
        self,
        prompt: str,
        *,
        model_fn: ModelCallable | None = None,
        model_name: str | None = None,
        learnings: list[str] | None = None,
    ) -> AtemResult:
        """Complete breath cycle: inhale -> execute -> exhale.

        Args:
            prompt: The input text.
            model_fn: Direct adapter override (skip selection).
            model_name: Force a specific registered adapter.
            learnings: Optional learnings to record after response.
        """
        t_start = time.time()

        decision = self.inhale(prompt)

        # Determine which adapter to use
        if model_fn is not None:
            adapter = model_fn
        elif model_name and model_name in self._adapters:
            adapter = self._adapters[model_name]
            # Override selection with forced model
            if model_name in self._profiles:
                decision = AtemDecision(
                    prompt=prompt,
                    hex=decision.hex,
                    selected_model=model_name,
                    profile=self._profiles[model_name],
                    system_prompt=decision.system_prompt,
                    alternatives=decision.alternatives,
                    reason=f"Forced: {model_name}",
                )
        elif decision.selected_model in self._adapters:
            adapter = self._adapters[decision.selected_model]
        else:
            # No adapter available
            return AtemResult(
                decision=decision,
                response="[no adapter registered for " + decision.selected_model + "]",
                new_rings=[],
                vitals_after=self._get_organism(decision.selected_model).vitals(),
                latency_ms=0.0,
            )

        # Execute
        response = adapter(prompt, decision.system_prompt)

        result = self.exhale(decision, response, learnings)
        result.latency_ms = (time.time() - t_start) * 1000
        return result

    # ── Scoring ───────────────────────────────────────────────────

    def _rank_models(self, coord: HexCoord) -> list[tuple[str, float]]:
        """Rank all available models for a hex profile."""
        scores = []

        for name, profile in self._profiles.items():
            # Cost filter
            if profile.cost_per_m > self._max_cost:
                continue

            # Adapter filter (only if adapters are registered)
            if self._adapters and name not in self._adapters:
                continue

            score = self._score_model(profile, coord, name)
            scores.append((name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _score_model(
        self, profile: VScoreProfile, coord: HexCoord, name: str,
    ) -> float:
        """Composite score: hex affinity + breath quality + liveness + cost + tau moat."""
        hex_aff = profile.hex_affinity(coord)
        breath_q = profile.breath_quality

        alive_bonus = 0.3 if profile.alive else 0.0
        local_bonus = 0.2 if (profile.is_local and self._prefer_local) else 0.0
        cost_penalty = min(profile.cost_per_m * 0.02, 0.2)

        # tau moat: accumulated rings increase trust
        organism = self._get_organism(name)
        ring_bonus = min(organism.rings.count, 50) * 0.01

        return (
            hex_aff * 0.4
            + breath_q * 0.3
            + alive_bonus
            + local_bonus
            - cost_penalty
            + ring_bonus
        )

    # ── System Prompt Generation ──────────────────────────────────

    def _build_system_prompt(
        self,
        coord: HexCoord,
        organism: OrganismBreather,
        profile: VScoreProfile,
    ) -> str:
        """Build organism injection. THE mechanism that makes R > 0."""
        vitals = organism.vitals()
        rings_data = vitals.get("rings", {})

        lines = [
            "Input classified on 6 axes:",
            f"  Pressure:  {coord.ruhe_druck:+.1f} (-1=calm, +1=urgent)",
            f"  Resonance: {coord.stille_resonanz:+.1f} (-1=silence, +1=discussion)",
            f"  Together:  {coord.allein_zusammen:+.1f} (-1=solo, +1=team)",
            f"  Create:    {coord.empfangen_schaffen:+.1f} (-1=receive, +1=create)",
            f"  Doing:     {coord.sein_tun:+.1f} (-1=reflect, +1=act)",
            f"  Speed:     {coord.langsam_schnell:+.1f} (-1=slow, +1=fast)",
            "",
            f"Organism: {vitals['breaths']} breaths | "
            f"{rings_data.get('total', 0)} rings | "
            f"BPM {vitals['bpm']}",
        ]

        # Include recent learnings (last 5 rings)
        recent = organism.rings.rings[-5:] if organism.rings.rings else []
        if recent:
            lines.append("")
            lines.append("Recent learnings:")
            for r in recent:
                lines.append(f"  - {r.content}")

        lines.append("")
        lines.append("Adapt your response style to match this profile.")
        if recent:
            lines.append("Build on previous learnings where relevant.")

        return "\n".join(lines)

    def _explain(
        self,
        name: str,
        profile: VScoreProfile,
        coord: HexCoord,
        score: float,
    ) -> str:
        """Human-readable explanation of the routing decision."""
        parts = [f"{name} (V={profile.V:.4f}"]
        if profile.alive:
            parts.append("ALIVE")
        if profile.is_local:
            parts.append("LOCAL/FREE")
        parts_str = ", ".join(parts) + ")"

        strengths = []
        if profile.R > 0.3:
            strengths.append(f"R={profile.R:.2f} (breathes with context)")
        if profile.B > 0.7:
            strengths.append(f"B={profile.B:.2f} (adapts to hex)")
        if profile.S > 0.9:
            strengths.append(f"S={profile.S:.2f} (consistent)")
        if profile.W > 0.4:
            strengths.append(f"W={profile.W:.2f} (warm)")
        if profile.E > 0.85:
            strengths.append(f"E={profile.E:.2f} (emergent)")

        organism = self._get_organism(name)
        ring_count = organism.rings.count

        reason = f"Selected {parts_str}"
        if strengths:
            reason += f" | {', '.join(strengths)}"
        if ring_count > 0:
            reason += f" | tau moat: {ring_count} rings"
        reason += f" | score={score:.3f}"

        return reason

    # ── Introspection ─────────────────────────────────────────────

    def available_models(self) -> list[str]:
        """Models with both a profile AND registered adapter."""
        if not self._adapters:
            return list(self._profiles.keys())
        return [n for n in self._profiles if n in self._adapters]

    def organism_states(self) -> dict[str, dict]:
        """All persisted organism states with ring counts."""
        states = {}
        org_dir = self._state_dir / "organisms"
        if org_dir.exists():
            for model_dir in sorted(org_dir.iterdir()):
                state_file = model_dir / "state.json"
                if state_file.exists():
                    try:
                        data = json.loads(state_file.read_text())
                        states[model_dir.name] = {
                            "breaths": data.get("breath_count", 0),
                            "rings": len(data.get("rings", [])),
                            "ring_types": data.get("ring_count_by_type", {}),
                        }
                    except json.JSONDecodeError:
                        pass
        return states
