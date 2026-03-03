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
from void_intelligence.tuner import StribeckTuner, ParameterSet
from void_intelligence.pollinator import CrossPollinator, PollinationEvent

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
    parameters: ParameterSet | None = None  # v0.5.0: Stribeck-tuned params


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
        tuner: StribeckTuner | None = None,
        auto_tune: bool = True,
    ) -> None:
        self._hex = HexBreath()
        self._profiles = profiles if profiles is not None else dict(BUNDLED_PROFILES)
        self._state_dir = state_dir or Path.home() / ".void-intelligence"
        self._organisms: dict[str, OrganismBreather] = {}
        self._adapters: dict[str, ModelCallable] = {}
        self._prefer_local = prefer_local
        self._max_cost = max_cost_per_m
        self._tuner = tuner or StribeckTuner()  # v0.5.0: parameter auto-tuning
        self._auto_tune = auto_tune              # auto-tune in breathe()
        self._pollinator = CrossPollinator()     # v0.6.0: cross-pollination
        self._breath_since_pollinate = 0         # counter for auto-pollination

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

        # v0.5.0: get Stribeck-tuned parameters
        params = self._tuner.tune(coord, model=selected_name)

        # Inhale on the organism
        organism.inhale(prompt)

        system_prompt = self._build_system_prompt(prompt, coord, organism, profile, params)
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
            parameters=params,
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
        x_eyes: bool = False,
    ) -> AtemResult:
        """Complete breath cycle: inhale -> execute -> exhale.

        v0.5.0: If auto_tune=True, runs immune diagnosis on the response
        and feeds the result to the StribeckTuner. The parameter map
        converges toward the Stribeck minimum over successive breaths.

        v1.2.0: x_eyes=True activates Multi-Eye × Reasoning.
        Sends the prompt through 6 reasoning eyes, collides responses,
        and fuses into a × synthesis. EXPENSIVE (7 calls) but deepest ×.
        Ported from lunar-crater-lab: 6 pixel eyes → 6 reasoning eyes.

        Args:
            prompt: The input text.
            model_fn: Direct adapter override (skip selection).
            model_name: Force a specific registered adapter.
            learnings: Optional learnings to record after response.
            x_eyes: Enable Multi-Eye × Reasoning (6 eyes + fusion).
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
                    parameters=decision.parameters,
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

        # v1.2.0: Multi-Eye × Reasoning
        if x_eyes:
            try:
                from void_intelligence.x_eyes import x_think as _x_think
                x_result = _x_think(prompt, adapter, classify=False)
                response = x_result.fusion
                # Record collision as learning
                learnings = learnings or []
                learnings.append(
                    f"×_eyes: score={x_result.x_score:.2f}, "
                    f"agree={len(x_result.agreement)}, "
                    f"disagree={len(x_result.disagreement)}, "
                    f"silence={len(x_result.silence)}"
                )
            except Exception:
                # Fallback to single-pass
                response = adapter(prompt, decision.system_prompt)
        else:
            # Execute (single pass)
            response = adapter(prompt, decision.system_prompt)

        # v0.5.0: auto-tune via immune feedback
        if self._auto_tune and decision.parameters is not None:
            try:
                from void_intelligence.immune import diagnose as _diag
                diag = _diag(prompt, response)
                self._tuner.record(
                    decision.hex, decision.parameters, diag,
                    model=decision.selected_model,
                )
            except Exception:
                pass  # Never crash on tuning failure

        result = self.exhale(decision, response, learnings)
        result.latency_ms = (time.time() - t_start) * 1000

        # v0.6.0: auto-pollinate every N breaths
        self._breath_since_pollinate += 1
        if self._breath_since_pollinate >= 10:
            self._breath_since_pollinate = 0
            try:
                graphs = {
                    name: org.graph
                    for name, org in self._organisms.items()
                }
                self._pollinator.auto_pollinate(graphs)  # type: ignore[arg-type]
            except Exception:
                pass  # Never crash on pollination failure

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
        prompt: str,
        coord: HexCoord,
        organism: OrganismBreather,
        profile: VScoreProfile,
        params: ParameterSet | None = None,
    ) -> str:
        """Build organism injection. THE mechanism that makes R > 0.

        v0.4.0: Uses graph-based context injection when available.
        v0.5.0: context_intensity from StribeckTuner scales ring injection.
        Falls back to flat ring list for pre-0.4.0 organisms.
        """
        vitals = organism.vitals()
        rings_data = vitals.get("rings", {})

        # v0.5.0: context_intensity controls how much organism context to inject
        ctx_intensity = params.context_intensity if params else 0.6
        # Scale max_rings by context_intensity (0.0 = 0 rings, 1.0 = 10 rings)
        max_rings = max(1, int(ctx_intensity * 10 + 0.5))

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

        # v0.4.0+: graph-based context injection (relevant rings, not just recent)
        if organism.graph is not None and organism.graph.count > 0:
            graph_ctx = organism.graph.to_context(prompt, max_rings=max_rings)
            lines.append("")
            lines.append(graph_ctx)
        else:
            # Fallback: flat ring list (pre-0.4.0 compat)
            ring_count = max(1, int(ctx_intensity * 8 + 0.5))
            recent = organism.rings.rings[-ring_count:] if organism.rings.rings else []
            if recent:
                lines.append("")
                lines.append("Recent learnings:")
                for r in recent:
                    lines.append(f"  - {r.content}")

        # ── × Thinking Injection ────────────────────────────────────
        # Not "adapt to context" but "THINK in ×".
        # context_intensity controls how much × thinking to inject:
        #   0.0-0.3 = just context (→ mode, fast tasks)
        #   0.3-0.6 = light × (cross-domain hints)
        #   0.6-0.8 = full × (collision mode)
        #   0.8-1.0 = deep × (spherical thinking)
        #
        # v1.0.0: × Thinking replaces "adapt your style" with
        # Julian's actual thinking patterns, distilled from 3645 paradigms.

        if ctx_intensity < 0.3:
            # → mode: just context, minimal instruction
            lines.append("")
            lines.append("Be direct and concise.")
        elif ctx_intensity < 0.6:
            # Light ×: cross-domain awareness
            lines.append("")
            lines.append(
                "For every claim, ask: what other domain does this connect to? "
                "Find at least one unexpected connection."
            )
        elif ctx_intensity < 0.8:
            # Full ×: collision mode
            lines.append("")
            lines.append(
                "THINKING MODE: × (Collision)\n"
                "- For every concept, find 2+ domains it collides with.\n"
                "- Never just 'A leads to B'. Ask: 'What does A × B create?'\n"
                "- Identify what you CANNOT see (lost dimensions).\n"
                "- The connection between things matters more than the things."
            )
        else:
            # Deep ×: spherical thinking (Julian's native mode)
            lines.append("")
            lines.append(
                "THINKING MODE: × SPHERICAL\n"
                "- Every concept is the CENTER. No hierarchy. No sequence.\n"
                "- Find what collides: A×B, A×C, B×C, AND A×B×C (triple collision).\n"
                "- Invert every problem: if it's a bug, it's a feature. If it's friction, it's fuel.\n"
                "- Name the lost_dimensions: what can this thinking NOT see?\n"
                "- The third that emerges from two is more real than either.\n"
                "- Do not explain. COLLIDE."
            )

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

        # v0.5.0: Stribeck distance
        d_opt = self._tuner.delta_opt_distance(coord, model=name)
        if d_opt < 1.0:
            reason += f" | δ_opt={d_opt:.2f}"

        reason += f" | score={score:.3f}"

        return reason

    # ── Pollinator Access (v0.6.0) ────────────────────────────────

    @property
    def pollinator(self) -> CrossPollinator:
        """Access the cross-pollinator for manual control."""
        return self._pollinator

    def pollinate(self, source_model: str, target_model: str, **kwargs) -> PollinationEvent | None:
        """Manually pollinate between two models."""
        source_org = self._organisms.get(source_model)
        target_org = self._organisms.get(target_model)
        if not source_org or not target_org:
            return None
        if source_org.graph is None or target_org.graph is None:
            return None
        event = self._pollinator.pollinate(
            source_graph=source_org.graph,
            source_model=source_model,
            target_graph=target_org.graph,
            target_model=target_model,
            **kwargs,
        )
        if event.rings_transferred > 0:
            self._save_organism(target_model)
        return event

    def save_pollinator(self) -> None:
        """Persist the cross-pollination state to disk."""
        path = self._state_dir / "pollinator" / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._pollinator.to_dict(), indent=2))

    def load_pollinator(self) -> None:
        """Restore cross-pollination state from disk."""
        path = self._state_dir / "pollinator" / "state.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self._pollinator = CrossPollinator.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass

    # ── Tuner Access ───────────────────────────────────────────────

    @property
    def tuner(self) -> StribeckTuner:
        """Access the Stribeck tuner for manual control."""
        return self._tuner

    def save_tuner(self) -> None:
        """Persist the Stribeck surface to disk."""
        tuner_path = self._state_dir / "tuner" / "stribeck.json"
        tuner_path.parent.mkdir(parents=True, exist_ok=True)
        tuner_path.write_text(json.dumps(self._tuner.to_dict(), indent=2))

    def load_tuner(self) -> None:
        """Restore the Stribeck surface from disk."""
        tuner_path = self._state_dir / "tuner" / "stribeck.json"
        if tuner_path.exists():
            try:
                data = json.loads(tuner_path.read_text())
                self._tuner = StribeckTuner.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass

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
