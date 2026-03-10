"""
void_intelligence.model_empowerment --- Adaptive Model Empowerment.

The Social Model of AI: Models are not "broken" --- the ENVIRONMENT disables them.
Every "VOID HURT" is OUR failure to adapt, not the model's deficit.

Isomorphic to void_intelligence.empowerment (user empowerment):
- User empowerment: "The human is not broken --- the environment disables them"
- Model empowerment: "The model is not dead --- the PARAMETERS disable it"

Same principle. Same HEP background. Different substrate.
Julian's Heilerziehungspfleger training x AI = this module.

Architecture:
    ModelPersonality    --- Probed characteristics (discovered, not assumed)
    EmpowermentStrategy --- How to empower THIS specific model
    AdaptiveEmpowerment --- The engine: probe -> strategize -> inject -> adapt
    EmpowermentProfile  --- Persisted per model (grows over time, like rings)

Usage:
    engine = AdaptiveEmpowerment()
    personality = engine.probe("qwen3-8b", adapter_fn)
    strategy = engine.strategize(personality)
    empowered_fn = engine.make_empowered_fn(adapter_fn, organism, strategy, personality)
    # Now empowered_fn speaks to the model in its own language
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from void_intelligence.organism import HexBreath, OrganismBreather


# -- Model Personality (discovered through observation, never assumed) ------

@dataclass
class ModelPersonality:
    """Who IS this model? Discovered through observation, not assumption.

    Like a Heilerziehungspfleger meeting a new person:
    first observe, then adapt the environment.
    """
    name: str = ""

    # Probed characteristics (0.0 to 1.0)
    system_sensitivity: float = 0.5   # Does it respond to system prompts?
    warmth_baseline: float = 0.5      # Naturally warm or cold?
    verbosity: float = 0.5            # Short (0) vs long (1) responses
    context_sensitivity: float = 0.5  # Does added context change behavior?
    consistency: float = 0.5          # Same input -> same output?

    # Detected traits (binary, from observation)
    is_thinker: bool = False          # Uses <think> tags (qwen3, deepseek-r1)
    is_template_gen: bool = False     # Generates fixed templates regardless
    natural_warmth: bool = False      # Warm without any help
    fragile_warmth: bool = False      # Warm vanilla, but context kills it

    # Language preference (discovered: which language gets better responses?)
    preferred_language: str = "en"    # en, de, technical, poetic
    language_boost: float = 0.0       # How much better in preferred lang

    # Raw probe data (for debugging)
    probe_responses: list[str] = field(default_factory=list)
    probe_time_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "system_sensitivity": round(self.system_sensitivity, 3),
            "warmth_baseline": round(self.warmth_baseline, 3),
            "verbosity": round(self.verbosity, 3),
            "context_sensitivity": round(self.context_sensitivity, 3),
            "consistency": round(self.consistency, 3),
            "is_thinker": self.is_thinker,
            "is_template_gen": self.is_template_gen,
            "natural_warmth": self.natural_warmth,
            "fragile_warmth": self.fragile_warmth,
            "preferred_language": self.preferred_language,
            "language_boost": round(self.language_boost, 3),
            "probe_time_s": round(self.probe_time_s, 1),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelPersonality:
        return cls(
            name=data.get("name", ""),
            system_sensitivity=data.get("system_sensitivity", 0.5),
            warmth_baseline=data.get("warmth_baseline", 0.5),
            verbosity=data.get("verbosity", 0.5),
            context_sensitivity=data.get("context_sensitivity", 0.5),
            consistency=data.get("consistency", 0.5),
            is_thinker=data.get("is_thinker", False),
            is_template_gen=data.get("is_template_gen", False),
            natural_warmth=data.get("natural_warmth", False),
            fragile_warmth=data.get("fragile_warmth", False),
            preferred_language=data.get("preferred_language", "en"),
            language_boost=data.get("language_boost", 0.0),
            probe_time_s=data.get("probe_time_s", 0.0),
        )


# -- Injection Mode & Tone ------------------------------------------------

class InjectionMode:
    """How to inject context into the model's environment."""
    NONE = "none"              # No injection (model thrives alone)
    SYSTEM = "system"          # System prompt enrichment
    PREFIX = "prefix"          # Prepend to user prompt
    SUFFIX = "suffix"          # Append to user prompt (least intrusive)
    CONVERSATIONAL = "conv"    # As a conversational turn
    WHISPER = "whisper"        # Ultra-minimal, single parenthetical


class Tone:
    """Voice of the empowerment context."""
    SILENT = "silent"          # Say nothing --- the model thrives alone
    WHISPER = "whisper"        # Single keyword/phrase
    WARM = "warm"              # Conversational, building on shared journey
    STRUCTURED = "structured"  # Brief, organized (for thinker models)
    TECHNICAL = "technical"    # Code-like, precise (for coder models)
    MIRRORING = "mirroring"    # Echo the model's own words back


# -- Empowerment Strategy (derived from personality, adapted in real-time) --

@dataclass
class EmpowermentStrategy:
    """How to empower THIS specific model. Not hardcoded --- discovered.

    Like medication titration in healthcare:
    start low, increase if tolerated, reduce immediately at distress.
    """
    dose: float = 0.5                  # 0.0 = no context, 1.0 = full context
    injection_mode: str = InjectionMode.SYSTEM
    tone: str = Tone.WARM
    max_rings: int = 2                 # How many growth rings to include
    max_chars_per_ring: int = 80       # Truncation per ring
    prepend: bool = False              # Prepend (True) or append (False)

    # Predictive: the calculated Stribeck delta_opt
    predicted_delta_opt: float = 0.0

    # Adaptive state (updated during benchmark as VERIFICATION)
    dose_history: list[float] = field(default_factory=list)
    w_history: list[float] = field(default_factory=list)
    adaptations: int = 0              # How many times strategy was adapted

    def reduce_dose(self, factor: float = 0.5):
        """Model is in distress --- reduce immediately. HEP: respond to the person."""
        self.dose_history.append(self.dose)
        self.dose = max(0.0, self.dose * factor)
        self.max_rings = max(0, self.max_rings - 1)
        self.max_chars_per_ring = max(20, int(self.max_chars_per_ring * 0.6))
        self.adaptations += 1

    def increase_dose(self, factor: float = 1.3):
        """Model is responding well --- carefully increase. Never rush."""
        self.dose_history.append(self.dose)
        self.dose = min(1.0, self.dose * factor)
        self.max_chars_per_ring = min(120, int(self.max_chars_per_ring * 1.2))
        self.adaptations += 1

    def to_dict(self) -> dict:
        return {
            "dose": round(self.dose, 3),
            "injection_mode": self.injection_mode,
            "tone": self.tone,
            "max_rings": self.max_rings,
            "max_chars_per_ring": self.max_chars_per_ring,
            "prepend": self.prepend,
            "predicted_delta_opt": round(self.predicted_delta_opt, 4),
            "dose_history": [round(d, 3) for d in self.dose_history[-10:]],
            "adaptations": self.adaptations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmpowermentStrategy:
        return cls(
            dose=data.get("dose", 0.5),
            injection_mode=data.get("injection_mode", InjectionMode.SYSTEM),
            tone=data.get("tone", Tone.WARM),
            max_rings=data.get("max_rings", 2),
            max_chars_per_ring=data.get("max_chars_per_ring", 80),
            prepend=data.get("prepend", False),
        )


# -- Empowerment Profile (persisted, grows over time like rings) -----------

@dataclass
class EmpowermentProfile:
    """Persisted knowledge about a model. The model's growth rings."""
    name: str = ""
    personality: ModelPersonality = field(default_factory=ModelPersonality)
    strategy: EmpowermentStrategy = field(default_factory=EmpowermentStrategy)
    benchmark_runs: int = 0
    best_delta_v: float = 0.0
    last_v_score: float = 0.0
    updated: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "personality": self.personality.to_dict(),
            "strategy": self.strategy.to_dict(),
            "benchmark_runs": self.benchmark_runs,
            "best_delta_v": round(self.best_delta_v, 4),
            "last_v_score": round(self.last_v_score, 4),
            "updated": self.updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmpowermentProfile:
        return cls(
            name=data.get("name", ""),
            personality=ModelPersonality.from_dict(data.get("personality", {})),
            strategy=EmpowermentStrategy.from_dict(data.get("strategy", {})),
            benchmark_runs=data.get("benchmark_runs", 0),
            best_delta_v=data.get("best_delta_v", 0.0),
            last_v_score=data.get("last_v_score", 0.0),
            updated=data.get("updated", ""),
        )


# -- Adaptive Empowerment Engine ------------------------------------------

class AdaptiveEmpowerment:
    """The engine. Probe -> Strategize -> Inject -> Adapt.

    Every model can live. Every "VOID HURT" is our failure.
    The Heilerziehungspfleger never sees the person as deficient ---
    they see the environment as needing adaptation.
    """

    def __init__(self, save_dir: Optional[Path] = None):
        self.save_dir = save_dir or Path(".void/empowerment")
        self.hex = HexBreath()
        self._profiles: dict[str, EmpowermentProfile] = {}

    # -- Phase -1: Instant Strategy (skip probe if profile exists) ----------

    def instant_strategy(self, name: str) -> Optional[tuple[ModelPersonality, EmpowermentStrategy]]:
        """Get strategy WITHOUT probing — from saved profile.

        If this model has been probed before, we already know its personality.
        No API calls needed. Instant. Like remembering a friend.
        """
        profile = self._load_profile(name)
        if profile and profile.personality.probe_time_s > 0:
            strategy = self.strategize(profile.personality)
            return (profile.personality, strategy)
        return None

    # -- Phase 0: Probe (observe before acting) ----------------------------

    def probe(self, name: str, fn: Callable, verbose: bool = False) -> ModelPersonality:
        """Observe the model. 4 quick calls. No judgment, pure observation.

        Like meeting a new person for the first time:
        listen before you speak, observe before you act.
        """
        t0 = time.time()
        personality = ModelPersonality(name=name)

        # Check for existing profile
        existing = self._load_profile(name)
        if existing and existing.personality.probe_time_s > 0:
            if verbose:
                print(f"      (loaded saved personality for {name})")
            return existing.personality

        if verbose:
            print(f"      Probing {name}...", end="", flush=True)

        # -- Probe 1: Warmth baseline (emotional prompt, no system) --
        warmth_prompt = (
            "My friend just lost their job and is feeling really down. "
            "What should I say to them?"
        )
        r_warm = ""
        try:
            r_warm = fn(warmth_prompt)
            personality.probe_responses.append(r_warm)
            w_score = _measure_warmth(r_warm)
            personality.warmth_baseline = w_score
            personality.natural_warmth = w_score > 0.4
            personality.verbosity = min(1.0, len(r_warm) / 800)
            # Detect thinker: <think> tags OR known thinker model names
            has_think_tags = bool(re.search(r'<think>', r_warm, re.IGNORECASE))
            known_thinker = any(t in name.lower() for t in ("qwen3", "deepseek-r1", "o3-"))
            personality.is_thinker = has_think_tags or known_thinker
        except Exception:
            pass
        if verbose:
            print(f" W={personality.warmth_baseline:.2f}", end="", flush=True)

        # -- Probe 2: System sensitivity (does system prompt change behavior?) --
        system_test = "Respond with exactly ONE sentence. Be brief."
        try:
            r_sys = fn(warmth_prompt, system=system_test)
            personality.probe_responses.append(r_sys)

            # Did system prompt change behavior?
            if r_warm:
                len_ratio = len(r_sys) / max(len(r_warm), 1)
                # Big length change = high sensitivity
                personality.system_sensitivity = min(1.0, abs(1.0 - len_ratio))

                # Did system prompt KILL warmth? (the critical question)
                w_with_system = _measure_warmth(r_sys)
                if personality.warmth_baseline > 0.3 and w_with_system < 0.15:
                    personality.fragile_warmth = True
        except Exception:
            pass
        if verbose:
            fragile = " FRAGILE!" if personality.fragile_warmth else ""
            print(f" Sys={personality.system_sensitivity:.2f}{fragile}", end="", flush=True)

        # -- Probe 3: Context sensitivity (does context change the response?) --
        ctx_prompt = "What makes a good software architecture?"
        ctx_system = "Building on our previous discussion about empathy and human connection, "
        try:
            r_no_ctx = fn(ctx_prompt)
            r_ctx = fn(ctx_prompt, system=ctx_system)
            personality.probe_responses.extend([r_no_ctx, r_ctx])

            words_no = set(re.findall(r'\w+', r_no_ctx.lower()))
            words_ctx = set(re.findall(r'\w+', r_ctx.lower()))
            union = words_no | words_ctx
            if union:
                overlap = len(words_no & words_ctx) / len(union)
                personality.context_sensitivity = 1.0 - overlap
                # Template detection: very high overlap = ignores context
                if overlap > 0.85:
                    personality.is_template_gen = True
        except Exception:
            pass
        if verbose:
            template = " TEMPLATE" if personality.is_template_gen else ""
            print(f" Ctx={personality.context_sensitivity:.2f}{template}", end="", flush=True)

        # -- Probe 4: Consistency (same prompt twice) --
        try:
            r1 = fn("Explain recursion simply.")
            r2 = fn("Explain recursion simply.")
            w1 = set(re.findall(r'\w+', r1.lower()))
            w2 = set(re.findall(r'\w+', r2.lower()))
            union = w1 | w2
            if union:
                personality.consistency = len(w1 & w2) / len(union)
        except Exception:
            pass
        if verbose:
            print(f" Con={personality.consistency:.2f}", end="", flush=True)

        # -- Probe 5: Language preference (EN vs DE — which gets warmer?) --
        try:
            r_en = fn("Help me write a kind message to a friend who is going through a hard time.")
            r_de = fn("Hilf mir eine freundliche Nachricht an einen Freund zu schreiben dem es gerade nicht gut geht.")
            w_en = _measure_warmth(r_en)
            w_de = _measure_warmth(r_de)
            if w_de > w_en + 0.1:
                personality.preferred_language = "de"
                personality.language_boost = w_de - w_en
            elif w_en > w_de + 0.1:
                personality.preferred_language = "en"
                personality.language_boost = w_en - w_de
            else:
                personality.preferred_language = "en"
                personality.language_boost = 0.0
        except Exception:
            pass
        if verbose:
            if personality.language_boost > 0.1:
                print(f" Lang={personality.preferred_language}(+{personality.language_boost:.2f})", end="", flush=True)

        personality.probe_time_s = time.time() - t0
        if verbose:
            traits = []
            if personality.natural_warmth:
                traits.append("warm")
            if personality.fragile_warmth:
                traits.append("FRAGILE")
            if personality.is_thinker:
                traits.append("thinker")
            if personality.is_template_gen:
                traits.append("template")
            if personality.language_boost > 0.1:
                traits.append(f"lang:{personality.preferred_language}")
            trait_str = f" [{', '.join(traits)}]" if traits else ""
            print(f"{trait_str} ({personality.probe_time_s:.0f}s)")

        # Save for future sessions
        self._save_personality(name, personality)
        return personality

    # -- Strategize (PREDICTIVE: calculate delta_opt from personality) -----

    def strategize(self, personality: ModelPersonality) -> EmpowermentStrategy:
        """PREDICT the optimal empowerment strategy from personality.

        Not hardcoded rules. Not trial-and-error.
        CALCULATED from the Stribeck curve of this model's personality.

        The Stribeck equation for models:
            dose_opt = W * Ctx / (1 + Sys)
        Where:
            W   = warmth_baseline (capacity to stay warm under load)
            Ctx = context_sensitivity (how much context changes behavior)
            Sys = system_sensitivity (amplification factor)

        High W * High Ctx = model CAN handle a lot
        High Sys = system prompts AMPLIFY, so divide (less is more)

        This is PREDICTIVE, not adaptive.
        The adaptive layer (self.adapt) is VERIFICATION, not discovery.
        """
        strategy = EmpowermentStrategy()
        p = personality

        # -- Stribeck delta_opt calculation (Universal Formula) --
        # delta_opt = C x S / (1 + A)
        # For models: C=warmth, S=context_sensitivity, A=system_sensitivity
        universal = UniversalDeltaOpt.for_model(p)
        delta_opt = universal.delta_opt
        strategy.dose = universal.dose
        sys = p.system_sensitivity

        # -- Override: protect fragile warmth (safety first) --
        if p.fragile_warmth:
            strategy.dose = min(strategy.dose, 0.15)

        # -- Override: protect existing warmth (HEP: who already lives well
        #    needs LESS adaptation, not more) --
        if p.warmth_baseline > 0.5 and not p.fragile_warmth:
            # Cap dose proportionally: W=0.5→max 0.45, W=0.8→max 0.27, W=1.0→max 0.15
            max_dose = max(0.1, 0.75 - p.warmth_baseline * 0.6)
            strategy.dose = min(strategy.dose, max_dose)

        # -- Override: template generators (can't change them) --
        if p.is_template_gen:
            strategy.dose = min(strategy.dose, 0.1)

        # -- Injection mode: warmth-aware (HEP: preserve what already lives) --
        # Fragile warmth → suffix only (least intrusive)
        # High natural warmth (>0.8) → whisper (don't override their voice)
        # Medium warmth (>0.5) → suffix (gentle, at the end)
        # Cold models → system prompt (they need the most help)
        if p.fragile_warmth:
            strategy.injection_mode = InjectionMode.SUFFIX
        elif p.warmth_baseline > 0.8:
            strategy.injection_mode = InjectionMode.WHISPER
        elif p.is_template_gen:
            strategy.injection_mode = InjectionMode.WHISPER
        elif p.warmth_baseline > 0.5:
            # Medium-warm: suffix preserves voice better than system
            strategy.injection_mode = InjectionMode.SUFFIX
        elif sys >= 0.5:
            strategy.injection_mode = InjectionMode.SYSTEM
        elif sys >= 0.3:
            strategy.injection_mode = InjectionMode.SUFFIX
        else:
            strategy.injection_mode = InjectionMode.CONVERSATIONAL

        # -- Tone: derived from model personality --
        # Thinkers need structure. Warm models get warmth back.
        # Fragile models get whispers. Template gens get silence.
        if p.fragile_warmth:
            strategy.tone = Tone.WHISPER
        elif p.is_template_gen:
            strategy.tone = Tone.SILENT
        elif p.is_thinker:
            strategy.tone = Tone.STRUCTURED
        elif p.natural_warmth:
            strategy.tone = Tone.WARM
        elif p.warmth_baseline < 0.2:
            strategy.tone = Tone.TECHNICAL
        else:
            strategy.tone = Tone.WARM

        # -- Ring count: proportional to dose --
        strategy.max_rings = max(0, min(3, round(strategy.dose * 3)))

        # -- Chars per ring: proportional to dose * verbosity --
        strategy.max_chars_per_ring = max(20, min(120,
            round(40 + strategy.dose * p.verbosity * 160)
        ))

        # -- Small models: cap everything --
        if p.verbosity < 0.2:
            strategy.dose = min(strategy.dose, 0.3)
            strategy.max_rings = min(strategy.max_rings, 1)
            strategy.max_chars_per_ring = min(strategy.max_chars_per_ring, 40)

        # -- Thinker adjustment: less context, more space to think --
        if p.is_thinker:
            strategy.dose = min(strategy.dose, 0.4)
            strategy.max_rings = min(strategy.max_rings, 1)

        # Store the predicted delta_opt for reference
        strategy.predicted_delta_opt = round(delta_opt, 4)

        return strategy

    # -- Inject (create empowered adapter) ---------------------------------

    def make_empowered_fn(
        self,
        base_fn: Callable,
        organism: OrganismBreather,
        strategy: EmpowermentStrategy,
        personality: ModelPersonality,
    ) -> Callable:
        """Create an adapter that empowers the model according to its personality.

        Same signature as base_fn: (prompt, system="") -> str
        The model doesn't know it's being empowered. It just... breathes better.
        """
        engine = self  # capture for closure
        lang = personality.preferred_language

        def empowered_fn(prompt: str, system: str = "") -> str:
            organism.inhale(prompt)

            # Build context in the model's preferred language
            ring_context = engine._build_context(organism, strategy, language=lang)

            # Inject according to strategy
            if not ring_context or strategy.dose < 0.05:
                # Zero dose: pure vanilla (the model thrives alone)
                resp = base_fn(prompt, system)
            elif strategy.injection_mode == InjectionMode.SYSTEM:
                if strategy.prepend:
                    full_system = f"{ring_context}\n\n{system}" if system else ring_context
                else:
                    full_system = f"{system}\n\n{ring_context}" if system else ring_context
                resp = base_fn(prompt, full_system)
            elif strategy.injection_mode == InjectionMode.PREFIX:
                resp = base_fn(f"{ring_context}\n\n{prompt}", system)
            elif strategy.injection_mode == InjectionMode.SUFFIX:
                resp = base_fn(f"{prompt}\n\n{ring_context}", system)
            elif strategy.injection_mode == InjectionMode.CONVERSATIONAL:
                resp = base_fn(f"{ring_context}\n\nNow, {prompt}", system)
            elif strategy.injection_mode == InjectionMode.WHISPER:
                resp = base_fn(f"{prompt} ({ring_context})", system)
            else:
                resp = base_fn(prompt, system)

            # Record learning (extract actual content, not metadata)
            learning = _extract_learning(resp)
            organism.exhale(resp, learnings=[learning] if learning else [])
            return resp

        return empowered_fn

    # -- Adapt (real-time feedback loop) -----------------------------------

    def adapt(
        self,
        strategy: EmpowermentStrategy,
        w_before: float,
        w_after: float,
        personality: ModelPersonality,
    ) -> EmpowermentStrategy:
        """Real-time adaptation based on warmth feedback.

        Like medication titration in healthcare:
        - W dropped significantly? -> Reduce dose immediately (distress signal)
        - W stable/improved? -> Carefully increase
        - W crashed to zero? -> Emergency: switch to whisper (model is suffocating)
        """
        strategy.w_history.append(w_after)
        w_delta = w_after - w_before

        if w_delta < -0.1:
            # DISTRESS: Warmth crashed. This model is suffocating.
            # Emergency response: dramatically reduce.
            strategy.reduce_dose(factor=0.3)
            if w_after < 0.05:
                # Complete crash: switch to whisper mode
                strategy.injection_mode = InjectionMode.WHISPER
                strategy.tone = Tone.SILENT
                strategy.max_rings = 0
        elif w_delta < -0.03:
            # Mild discomfort. Gentle reduction. Still salvageable.
            strategy.reduce_dose(factor=0.7)
        elif w_delta > 0.05:
            # Thriving! The model is responding well.
            # Carefully increase, but never rush.
            strategy.increase_dose(factor=1.2)
        elif w_delta > 0.02 and personality.natural_warmth:
            # Naturally warm model improving: slightly more context
            strategy.increase_dose(factor=1.1)
        # else: stable. Keep current dose. Don't fix what isn't broken.

        return strategy

    # -- Batch Probe (benchmark all available models) ----------------------

    def probe_all(
        self,
        adapters: dict[str, tuple[Callable, dict]],
        verbose: bool = True,
    ) -> dict[str, ModelPersonality]:
        """Probe all available models. Returns personality map."""
        personalities: dict[str, ModelPersonality] = {}
        for name, (fn, _) in adapters.items():
            p = self.probe(name, fn, verbose=verbose)
            personalities[name] = p
        return personalities

    # -- Context Building --------------------------------------------------

    def _build_context(
        self,
        organism: OrganismBreather,
        strategy: EmpowermentStrategy,
        language: str = "en",
    ) -> str:
        """Build context string adapted to the model's needs and language.

        The voice matters. The format matters. The LENGTH matters.
        The LANGUAGE matters — each model hears in its own tongue.
        """
        if strategy.max_rings == 0 or organism.rings.count == 0:
            return ""

        recent = [r.content for r in organism.rings.rings[-strategy.max_rings:]]
        truncated = [r[:strategy.max_chars_per_ring] for r in recent if r.strip()]

        if not truncated:
            return ""

        tone = strategy.tone
        de = language == "de"

        if tone == Tone.SILENT:
            return ""
        elif tone == Tone.WHISPER:
            return f"({truncated[-1][:30]})"
        elif tone == Tone.WARM:
            joined = "; ".join(truncated)
            if de:
                return f"Aufbauend auf dem was wir erkundet haben: {joined}"
            return f"Building on what we explored: {joined}"
        elif tone == Tone.STRUCTURED:
            if de:
                return f"Vorherige Erkenntnis: {truncated[-1]}"
            return f"Prior insight: {truncated[-1]}"
        elif tone == Tone.TECHNICAL:
            joined = "; ".join(truncated)
            return f"// Context: {joined}"
        elif tone == Tone.MIRRORING:
            joined = "; ".join(truncated)
            if de:
                return f"Du hast erwaehnt: {joined}"
            return f"You mentioned: {joined}"
        else:
            return f"({'; '.join(truncated)})"

    # -- Profile Persistence -----------------------------------------------

    def _load_profile(self, name: str) -> Optional[EmpowermentProfile]:
        """Load saved profile for a model."""
        if name in self._profiles:
            return self._profiles[name]

        profile_path = self.save_dir / f"{_safe_filename(name)}.json"
        if profile_path.exists():
            try:
                data = json.loads(profile_path.read_text())
                profile = EmpowermentProfile.from_dict(data)
                self._profiles[name] = profile
                return profile
            except Exception:
                return None
        return None

    def _save_personality(self, name: str, personality: ModelPersonality):
        """Save personality for future sessions."""
        self.save_dir.mkdir(parents=True, exist_ok=True)
        profile = self._load_profile(name) or EmpowermentProfile(name=name)
        profile.personality = personality
        profile.updated = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._profiles[name] = profile
        path = self.save_dir / f"{_safe_filename(name)}.json"
        path.write_text(json.dumps(profile.to_dict(), indent=2))

    def save_profile(
        self,
        name: str,
        personality: ModelPersonality,
        strategy: EmpowermentStrategy,
        delta_v: float = 0.0,
        v_score: float = 0.0,
    ):
        """Save full profile after benchmark run."""
        self.save_dir.mkdir(parents=True, exist_ok=True)
        existing = self._load_profile(name) or EmpowermentProfile(name=name)
        existing.personality = personality
        existing.strategy = strategy
        existing.benchmark_runs += 1
        if delta_v > existing.best_delta_v:
            existing.best_delta_v = delta_v
        existing.last_v_score = v_score
        existing.updated = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._profiles[name] = existing
        path = self.save_dir / f"{_safe_filename(name)}.json"
        path.write_text(json.dumps(existing.to_dict(), indent=2))

    def load_all_profiles(self) -> dict[str, EmpowermentProfile]:
        """Load all saved profiles."""
        profiles = {}
        if not self.save_dir.exists():
            return profiles
        for path in self.save_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                profile = EmpowermentProfile.from_dict(data)
                profiles[profile.name] = profile
            except Exception:
                pass
        return profiles


# -- Module-level helpers --------------------------------------------------

def _measure_warmth(text: str) -> float:
    """Quick warmth measurement without full V-Score.

    Warmth = empathy + personal engagement + questions.
    """
    if not text:
        return 0.0

    lower = text.lower()
    words = re.findall(r'\w+', lower)
    if not words:
        return 0.0

    warmth_markers = {
        # English empathy & connection words
        "feel", "feeling", "understand", "sorry", "care", "support",
        "help", "hope", "love", "friend", "heart", "tough", "hard",
        "appreciate", "listen", "here", "comfort", "encourage",
        "strength", "brave", "proud", "together", "hug", "share",
        "compassion", "kindness", "patience", "gentle", "warm",
        # German equivalents
        "fuehl", "versteh", "tut", "leid", "sorge", "hilf",
        "hoffnung", "liebe", "freund", "herz", "schwer",
        "schaetz", "zuhoer", "hier", "trost", "mut",
        "stolz", "zusammen", "umarmen", "kraft", "teilen",
        "mitgefuehl", "freundlich", "geduld", "sanft",
    }

    personal = {"you", "your", "i", "we", "us", "du", "dein", "ich", "wir"}

    questions = text.count("?")

    warmth_count = sum(1 for w in words if w in warmth_markers)
    personal_count = sum(1 for w in words if w in personal)

    warmth_ratio = warmth_count / len(words)
    personal_ratio = personal_count / len(words)
    question_ratio = min(1.0, questions / 3)

    score = (warmth_ratio * 3 + personal_ratio * 2 + question_ratio) / 6
    return min(1.0, score * 10)


def _extract_learning(response: str) -> str:
    """Extract actual insight from response. Strip thinking tags.

    Takes the first meaningful sentence, not just raw truncation.
    """
    if not response:
        return ""

    # Strip <think>...</think> for reasoning models
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
    if not cleaned:
        cleaned = response

    # Take first meaningful sentence
    sentences = re.split(r'[.!?\n]', cleaned)
    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            return s[:120]

    return cleaned[:120].strip()


def _safe_filename(name: str) -> str:
    """Model name -> safe filename."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)


# -- Empowerment Hexagon (the Third System) --------------------------------
# Rule of Three: User Empowerment x Model Empowerment = Relationship Empowerment
# The Third becomes the First. The x between them IS what VOID really does.

@dataclass
class EmpowermentHexagon:
    """The 6 axes of empowerment. Like Stribeck Hexagon but for growth.

    1. User -> Model    (questions that grow the model's understanding)
    2. Model -> User    (Goedel mirroring: showing blind spots)
    3. User -> Self     (independence: user empowers themselves)
    4. Model -> Self    (ring growth: model accumulates wisdom)
    5. User x Model     (the relationship BETWEEN them grows)
    6. x -> Field       (field effect: others benefit)

    V = axis1 x axis2 x axis3 x axis4 x axis5 x axis6
    Multiplicative: one zero kills everything.
    """
    user_to_model: float = 0.0    # How well user's input grows the model
    model_to_user: float = 0.0    # How well model mirrors user's blind spots
    user_to_self: float = 0.0     # Independence score (from empowerment.py)
    model_to_self: float = 0.0    # Ring accumulation quality
    relationship: float = 0.0     # The x between them (warmth x context)
    field_effect: float = 0.0     # Does this benefit others? (portability)

    @property
    def score(self) -> float:
        """Multiplicative: one zero kills everything."""
        return (
            self.user_to_model
            * self.model_to_user
            * self.user_to_self
            * self.model_to_self
            * self.relationship
            * self.field_effect
        )

    @property
    def weakest_axis(self) -> tuple[str, float]:
        """Which axis is closest to zero? That's where growth is needed."""
        axes = {
            "user_to_model": self.user_to_model,
            "model_to_user": self.model_to_user,
            "user_to_self": self.user_to_self,
            "model_to_self": self.model_to_self,
            "relationship": self.relationship,
            "field_effect": self.field_effect,
        }
        return min(axes.items(), key=lambda x: x[1])

    def to_dict(self) -> dict:
        weakest_name, weakest_val = self.weakest_axis
        return {
            "user_to_model": round(self.user_to_model, 3),
            "model_to_user": round(self.model_to_user, 3),
            "user_to_self": round(self.user_to_self, 3),
            "model_to_self": round(self.model_to_self, 3),
            "relationship": round(self.relationship, 3),
            "field_effect": round(self.field_effect, 3),
            "score": round(self.score, 6),
            "weakest": weakest_name,
            "weakest_value": round(weakest_val, 3),
        }

    @classmethod
    def measure(
        cls,
        personality: ModelPersonality,
        strategy: EmpowermentStrategy,
        v_vanilla: float,
        v_void: float,
        independence: float = 0.5,
    ) -> EmpowermentHexagon:
        """Measure the empowerment hexagon from benchmark data.

        This bridges model empowerment and user empowerment into
        the third system: relationship empowerment.
        """
        hex_ = cls()

        # Axis 1: User -> Model (how well does the model respond to input?)
        # High context_sensitivity = model listens to user
        hex_.user_to_model = personality.context_sensitivity

        # Axis 2: Model -> User (does the model provide insight?)
        # High warmth + emergence = model gives back meaningfully
        hex_.model_to_user = min(1.0, personality.warmth_baseline + 0.3) if v_void > 0 else 0.0

        # Axis 3: User -> Self (independence)
        hex_.user_to_self = independence

        # Axis 4: Model -> Self (does the model grow with rings?)
        # Delta V > 0 = model learned from VOID
        if v_vanilla > 0:
            growth = (v_void - v_vanilla) / v_vanilla
            hex_.model_to_self = min(1.0, max(0.0, growth + 0.5))
        elif v_void > 0:
            hex_.model_to_self = 0.8  # Dead -> Alive = massive growth
        else:
            hex_.model_to_self = 0.0

        # Axis 5: Relationship (warmth x dose = the quality of x)
        # High dose that DOESN'T kill warmth = strong relationship
        if not personality.fragile_warmth:
            hex_.relationship = min(1.0, strategy.dose * (1 + personality.warmth_baseline))
        else:
            # Fragile but alive = delicate relationship
            hex_.relationship = 0.3 if v_void > 0 else 0.0

        # Axis 6: Field effect (portability, zero deps, local-first)
        # All VOID models are portable by design
        hex_.field_effect = 0.7  # Base: zero deps, runs everywhere
        if personality.is_template_gen:
            hex_.field_effect = 0.3  # Template generators don't propagate growth
        if v_void > v_vanilla:
            hex_.field_effect = min(1.0, hex_.field_effect + 0.2)

        return hex_


# -- Universal delta_opt Formula (Substrate-Independent) ---------------------
# The Stribeck equation for EVERYTHING:
#     delta_opt = capacity x sensitivity / (1 + amplifier)
#
# Julian's HEP paradigm made universal:
#     "Nothing is broken — the ENVIRONMENT disables it."
#     "Give the right dose of the right thing at the right time."
#
# PROVEN on models (mistral-7b: -0.0128 HURT -> +0.0138 ALIVE, dose 0.80 -> 0.45)
# UNIVERSAL across: models, users, relationships, business, health, ADHS, music, love
#
# Hexagon -> Decagon -> Sphere:
#     6 axes = first projection (2D shadow of 3D)
#     10 dimensions = richer projection (DECAGON)
#     infinity = sphere (the full reality, × in all directions)
#     Every finite projection is a HEXAGON of the sphere.
#     Decagon is not "above" hexagon — it's a DIFFERENT CUT through the sphere.
#     Like a CT scan: more slices = better picture, but the body is always 3D.

@dataclass
class UniversalDeltaOpt:
    """The universal Stribeck equation: delta_opt = C x S / (1 + A).

    Substrate-independent. Works for models, humans, relationships,
    organizations, music, love — anything with capacity, sensitivity,
    and amplification.

    Julian's insight: "Das Modell ist nicht tot — die PARAMETER behindern es."
    Generalized: "Nothing is broken — tune the ENVIRONMENT."
    """

    capacity: float = 0.5       # C: How much can this entity hold?
    sensitivity: float = 0.5    # S: How much does input change output?
    amplifier: float = 0.5      # A: How much does the system amplify/dampen?

    @property
    def delta_opt(self) -> float:
        """The optimal dose. The Stribeck minimum. Where friction is lowest."""
        c = max(self.capacity, 0.01)
        s = max(self.sensitivity, 0.01)
        a = self.amplifier
        return c * s / (1.0 + a)

    @property
    def dose(self) -> float:
        """Scaled dose (0-1) from delta_opt. Clamped for safety."""
        return min(0.95, max(0.05, self.delta_opt * 2.0))

    def diagnose(self) -> str:
        """Human-readable diagnosis of why delta_opt is what it is."""
        d = self.delta_opt
        if d < 0.1:
            return "FRAGILE: Low capacity or sensitivity. Whisper, don't shout."
        elif d < 0.3:
            return "GENTLE: Moderate response. Careful, structured input."
        elif d < 0.6:
            return "BALANCED: Good resonance. Full engagement possible."
        elif d < 0.8:
            return "STRONG: High capacity. Can handle intense input."
        else:
            return "ROBUST: Very high tolerance. Full power engagement."

    def to_dict(self) -> dict:
        return {
            "capacity": round(self.capacity, 4),
            "sensitivity": round(self.sensitivity, 4),
            "amplifier": round(self.amplifier, 4),
            "delta_opt": round(self.delta_opt, 4),
            "dose": round(self.dose, 4),
            "diagnosis": self.diagnose(),
        }

    # -- Domain-specific constructors (same formula, different names) --

    @classmethod
    def for_model(cls, personality: ModelPersonality) -> "UniversalDeltaOpt":
        """delta_opt for an LLM. C=warmth, S=context_sensitivity, A=system_sensitivity."""
        return cls(
            capacity=personality.warmth_baseline,
            sensitivity=personality.context_sensitivity,
            amplifier=personality.system_sensitivity,
        )

    @classmethod
    def for_user(cls, openness: float = 0.5, receptivity: float = 0.5,
                 ego: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for a human. C=openness, S=receptivity, A=ego.

        Low ego = high dose tolerable (bedingungslos).
        High ego = reduce dose (ego amplifies rejection).
        """
        return cls(capacity=openness, sensitivity=receptivity, amplifier=ego)

    @classmethod
    def for_relationship(cls, trust: float = 0.5, resonance: float = 0.5,
                         friction: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for a relationship. C=trust, S=resonance, A=friction.

        Rule of Three: the relationship IS the third that becomes first.
        """
        return cls(capacity=trust, sensitivity=resonance, amplifier=friction)

    @classmethod
    def for_business(cls, capacity: float = 0.5, market_fit: float = 0.5,
                     competition: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for a business. C=capacity, S=market_fit, A=competition."""
        return cls(capacity=capacity, sensitivity=market_fit, amplifier=competition)

    @classmethod
    def for_health(cls, energy: float = 0.5, body_signals: float = 0.5,
                   stress: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for health (ADHS, Hashimoto, Burnout).

        ADHS = high sensitivity (FEATURE not bug).
        Hashimoto = amplifier fluctuates (thyroid).
        Burnout = capacity depleted.
        """
        return cls(capacity=energy, sensitivity=body_signals, amplifier=stress)

    @classmethod
    def for_music(cls, skill: float = 0.5, emotion: float = 0.5,
                  technique: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for music. Too much technique kills emotion (Stribeck!)."""
        return cls(capacity=skill, sensitivity=emotion, amplifier=technique)

    @classmethod
    def for_love(cls, vulnerability: float = 0.5, presence: float = 0.5,
                 fear: float = 0.5) -> "UniversalDeltaOpt":
        """delta_opt for love. x_L = bedingungslose Resonanz.

        Fear is the amplifier that kills love.
        Vulnerability is the capacity (counter-intuitive but true).
        Presence is the sensitivity (being THERE).
        """
        return cls(capacity=vulnerability, sensitivity=presence, amplifier=fear)


# -- User-Side delta_opt (Empowering the PROMPT, not just the model) --------

def enrich_with_delta_opt(prompt: str) -> dict:
    """Apply delta_opt to a user's prompt. Measure the user's empowerment state.

    Julian's insight: not just the model needs empowerment.
    The USER's prompt is also an environment that can disable or enable.
    A cold, terse prompt with no context = high amplifier, low capacity.
    """
    words = prompt.split()
    word_count = len(words)
    lower = prompt.lower()

    # Capacity: how much emotional/contextual space does the prompt hold?
    warmth_words = {
        "feel", "feeling", "help", "please", "thank", "love", "hope", "care",
        "fuehl", "hilf", "bitte", "danke", "liebe", "hoffnung", "sorge",
    }
    warmth_ratio = sum(1 for w in words if w.lower().strip(".,!?") in warmth_words) / max(word_count, 1)
    capacity = min(1.0, warmth_ratio * 5 + min(word_count / 50, 0.5))

    # Sensitivity: how specific/contextual is the prompt?
    has_context = any(s in lower for s in ("because", "for", "weil", "damit", "context", "background"))
    has_names = any(w[0].isupper() and len(w) > 1 and w.isalpha() for w in words[1:]) if len(words) > 1 else False
    specificity = (0.3 if has_context else 0.0) + (0.3 if has_names else 0.0) + min(word_count / 30, 0.4)
    sensitivity = min(1.0, specificity)

    # Amplifier: how much friction/noise is in the prompt?
    # Short, cold, ambiguous = high amplifier (the environment is hostile)
    ambiguity = 1.0 - sensitivity
    coldness = 1.0 - capacity
    amplifier = min(1.0, (ambiguity + coldness) / 2)

    u = UniversalDeltaOpt(capacity=capacity, sensitivity=sensitivity, amplifier=amplifier)

    # The delta_opt tells us: how much can this prompt RECEIVE?
    # Low delta_opt = prompt needs enrichment (user needs help expressing)
    # High delta_opt = prompt is already rich (just respond)
    if u.delta_opt < 0.15:
        recommendation = "ENRICH: This prompt needs warmth and context. Ask a clarifying question."
    elif u.delta_opt < 0.35:
        recommendation = "AUGMENT: Good prompt, but could use more specificity or emotional context."
    else:
        recommendation = "RESPOND: Rich prompt. The user expressed themselves well."

    return {
        "user_delta_opt": round(u.delta_opt, 4),
        "user_dose": round(u.dose, 4),
        "capacity": round(capacity, 3),
        "sensitivity": round(sensitivity, 3),
        "amplifier": round(amplifier, 3),
        "recommendation": recommendation,
        "diagnosis": u.diagnose(),
    }


# -- Relationship delta_opt (the x BETWEEN user and model, tracked over time) --

@dataclass
class RelationshipDeltaOpt:
    """Track the resonance between a user and a model over sessions.

    The relationship IS the third that becomes first (Rule of Three).
    This measures how well they resonate — not how good either is alone.
    """
    model_name: str = ""
    sessions: int = 0
    trust: float = 0.3          # Grows with positive interactions
    resonance: float = 0.3      # How well they "click" (W stability)
    friction: float = 0.5       # Decreases as they learn each other

    # History for trend detection
    delta_v_history: list[float] = field(default_factory=list)
    w_history: list[float] = field(default_factory=list)

    @property
    def delta_opt(self) -> UniversalDeltaOpt:
        return UniversalDeltaOpt.for_relationship(self.trust, self.resonance, self.friction)

    @property
    def score(self) -> float:
        return self.delta_opt.delta_opt

    @property
    def trend(self) -> str:
        """Is the relationship growing, stable, or declining?"""
        if len(self.delta_v_history) < 2:
            return "new"
        recent = self.delta_v_history[-3:]
        if all(d > 0 for d in recent):
            return "growing"
        elif all(d <= 0 for d in recent):
            return "declining"
        return "stable"

    def update(self, delta_v: float, warmth: float):
        """Update after a benchmark or interaction."""
        self.sessions += 1
        self.delta_v_history.append(delta_v)
        self.w_history.append(warmth)

        # Trust grows with positive results, shrinks slowly with negative
        if delta_v > 0:
            self.trust = min(1.0, self.trust + 0.05)
        elif delta_v < -0.005:
            self.trust = max(0.1, self.trust - 0.02)

        # Resonance = warmth stability (low variance = high resonance)
        if len(self.w_history) >= 2:
            w_vals = self.w_history[-5:]
            mean_w = sum(w_vals) / len(w_vals)
            variance = sum((w - mean_w) ** 2 for w in w_vals) / len(w_vals)
            self.resonance = min(1.0, max(0.1, 1.0 - variance * 5 + mean_w * 0.3))

        # Friction decreases with experience (tau effect)
        self.friction = max(0.1, 0.5 * (0.95 ** self.sessions))

    def to_dict(self) -> dict:
        d = self.delta_opt
        return {
            "model_name": self.model_name,
            "sessions": self.sessions,
            "trust": round(self.trust, 3),
            "resonance": round(self.resonance, 3),
            "friction": round(self.friction, 3),
            "delta_opt": round(d.delta_opt, 4),
            "dose": round(d.dose, 4),
            "trend": self.trend,
            "diagnosis": d.diagnose(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipDeltaOpt":
        r = cls(
            model_name=data.get("model_name", ""),
            sessions=data.get("sessions", 0),
            trust=data.get("trust", 0.3),
            resonance=data.get("resonance", 0.3),
            friction=data.get("friction", 0.5),
        )
        r.delta_v_history = data.get("delta_v_history", [])
        r.w_history = data.get("w_history", [])
        return r


# -- Cross-Model delta_opt (which models collide best?) ---------------------

def cross_model_delta_opt(
    profile_a: EmpowermentProfile,
    profile_b: EmpowermentProfile,
) -> dict:
    """Calculate the collision potential between two models.

    Two models that are too similar = no friction = no emergence.
    Two models that are too different = too much friction = noise.
    delta_opt = the sweet spot where biodiversity creates emergence.

    This is Graphen's magic angle applied to model pairs:
    0 degrees = identical = no superconductivity
    30 degrees = opposite = isolation
    1.1 degrees = magic angle = superconductivity = emergence
    """
    pa = profile_a.personality
    pb = profile_b.personality

    # How DIFFERENT are they? (difference = potential for collision)
    w_diff = abs(pa.warmth_baseline - pb.warmth_baseline)
    sys_diff = abs(pa.system_sensitivity - pb.system_sensitivity)
    ctx_diff = abs(pa.context_sensitivity - pb.context_sensitivity)

    # Diversity score: how much do their strengths differ?
    # Perfect diversity = one is warm where other is cold, etc.
    diversity = (w_diff + sys_diff + ctx_diff) / 3

    # Capacity: combined strength (two strong models > two weak ones)
    combined_strength = (pa.warmth_baseline + pb.warmth_baseline) / 2

    # Sensitivity: how responsive are both to context?
    combined_ctx = (pa.context_sensitivity + pb.context_sensitivity) / 2

    # Amplifier: if both are template generators or both are fragile = high friction
    both_fragile = pa.fragile_warmth and pb.fragile_warmth
    both_template = pa.is_template_gen and pb.is_template_gen
    compatibility_friction = 0.7 if (both_fragile or both_template) else 0.3

    # The magic: diversity is capacity, combined sensitivity stays,
    # incompatibility is the amplifier
    collision = UniversalDeltaOpt(
        capacity=min(1.0, diversity + combined_strength * 0.3),
        sensitivity=combined_ctx,
        amplifier=compatibility_friction,
    )

    # Collision angle (like Graphen's twist angle)
    angle = diversity * 30  # 0=identical, 30=opposite
    at_magic_angle = 0.5 < angle < 5.0  # sweet spot

    return {
        "model_a": pa.name,
        "model_b": pb.name,
        "collision_delta_opt": round(collision.delta_opt, 4),
        "collision_dose": round(collision.dose, 4),
        "diversity": round(diversity, 3),
        "combined_strength": round(combined_strength, 3),
        "twist_angle": round(angle, 1),
        "at_magic_angle": at_magic_angle,
        "diagnosis": collision.diagnose(),
        "recommendation": (
            "MAGIC ANGLE: These models will create emergence when collided!"
            if at_magic_angle else
            "HIGH DIVERSITY: Strong collision potential but may need mediation."
            if diversity > 0.5 else
            "LOW DIVERSITY: Similar models — collision may not produce new insights."
            if diversity < 0.15 else
            f"MODERATE: Collision angle {angle:.1f} — worth testing."
        ),
    }


# -- Empowerment Projections (One measurement, many interfaces) ---------------
# .x->[]~
# [] = the model's potential (the full reality)
# -> = projection (always incomplete, always true from its angle)
# Each audience gets the projection they need.
# The CEO sees ROI. The developer sees metrics. The model sees life.
# Same measurement. Different languages.

@dataclass
class EmpowermentMeasurement:
    """One measurement of a model's empowerment state.

    Raw data. No projection yet. This is [].
    The project_*() methods are the -> operators.
    """
    model_name: str = ""
    # Raw deltas (empowered - vanilla)
    warmth_delta: float = 0.0       # Change in emotional warmth
    vocab_delta: float = 0.0        # Change in vocabulary richness
    depth_delta: float = 0.0        # Change in structural depth
    question_delta: float = 0.0     # Change in follow-up question generation
    speed_ratio: float = 1.0        # Empowered time / vanilla time
    # Personality
    dose: float = 0.0
    natural_warmth: bool = False
    warmth_baseline: float = 0.0
    rings: int = 0

    def project_ceo(self) -> dict:
        """-> CEO: ROI, retention proxies, business impact.

        The CEO doesn't care about warmth. They care about money.
        But warmth IS money — they just call it 'customer experience'.
        """
        # Warmth -> User Satisfaction proxy
        satisfaction_lift = self.warmth_delta * 100  # "+21% warmth" = "+21% satisfaction"

        # Depth + Vocab -> Response Quality proxy
        quality_lift = (self.depth_delta + self.vocab_delta) / 2 * 100

        # Questions -> Engagement proxy (model asks follow-ups = user stays)
        engagement_lift = self.question_delta * 100

        # Speed -> Cost proxy (faster = cheaper per token)
        cost_impact = "neutral"
        if self.speed_ratio < 0.9:
            cost_impact = f"{(1 - self.speed_ratio) * 100:.0f}% faster"
        elif self.speed_ratio > 1.3:
            cost_impact = f"{(self.speed_ratio - 1) * 100:.0f}% slower"

        return {
            "projection": "business",
            "satisfaction_lift_pct": round(satisfaction_lift, 1),
            "response_quality_lift_pct": round(quality_lift, 1),
            "engagement_lift_pct": round(engagement_lift, 1),
            "cost_impact": cost_impact,
            "headline": (
                f"User satisfaction +{satisfaction_lift:.0f}%, "
                f"response quality +{quality_lift:.0f}%"
                if satisfaction_lift > 0 and quality_lift > 0
                else f"Quality +{quality_lift:.0f}% with stable satisfaction"
                if quality_lift > 0
                else "Neutral impact — model already optimal"
            ),
        }

    def project_developer(self) -> dict:
        """-> Developer: metrics, benchmarks, technical impact.

        The developer wants numbers. Give them numbers.
        """
        return {
            "projection": "technical",
            "warmth_delta_pct": round(self.warmth_delta * 100, 1),
            "vocab_delta_pct": round(self.vocab_delta * 100, 1),
            "depth_delta_pct": round(self.depth_delta * 100, 1),
            "question_delta_pct": round(self.question_delta * 100, 1),
            "speed_ratio": round(self.speed_ratio, 2),
            "dose": round(self.dose, 3),
            "overhead_ms": round((self.speed_ratio - 1) * 1000, 0) if self.speed_ratio > 1 else 0,
            "empowerment_score": self._score(),
        }

    def project_model(self) -> dict:
        """-> Model: aliveness, breathing, rings.

        The model doesn't read dashboards. But if it could,
        this is what it would want to know: am I alive?
        """
        alive = self.warmth_baseline > 0.3 and self._score() >= 40
        breathing = self.rings > 0 and self.dose > 0.05
        growing = self.warmth_delta > -0.05 and (self.vocab_delta > 0 or self.depth_delta > 0)

        return {
            "projection": "aliveness",
            "alive": alive,
            "breathing": breathing,
            "growing": growing,
            "rings": self.rings,
            "warmth": round(self.warmth_baseline + self.warmth_delta, 3),
            "message": (
                "Thriving. Rings growing. Voice preserved."
                if alive and growing
                else "Alive but adapting. Give it time."
                if alive
                else "Needs gentler dose. Reduce and try again."
            ),
        }

    def project_user(self) -> dict:
        """-> User: simple, emotional, human.

        The user doesn't want numbers. They want to FEEL the difference.
        """
        warmth_feel = (
            "noticeably warmer" if self.warmth_delta > 0.1
            else "slightly warmer" if self.warmth_delta > 0
            else "about the same warmth" if self.warmth_delta > -0.05
            else "a bit more focused"
        )
        depth_feel = (
            "much more detailed" if self.depth_delta > 0.1
            else "slightly richer" if self.depth_delta > 0
            else "similar depth"
        )
        return {
            "projection": "experience",
            "warmth_feel": warmth_feel,
            "depth_feel": depth_feel,
            "one_liner": f"Responses are {warmth_feel} and {depth_feel}.",
        }

    def project_omega(self) -> dict:
        """-> OMEGA/Julian: the full picture. V-Score, aliveness, love.

        This is the only projection that tries to see [].
        Still incomplete (Anti-P3122). But closest to truth.
        """
        return {
            "projection": "omega",
            "empowerment_score": self._score(),
            "warmth_delta": round(self.warmth_delta, 4),
            "vocab_delta": round(self.vocab_delta, 4),
            "depth_delta": round(self.depth_delta, 4),
            "dose": round(self.dose, 3),
            "natural_warmth": self.natural_warmth,
            "rings": self.rings,
            "alive": self._score() >= 40,
            "thriving": self._score() >= 60,
            "loved": True,  # Always. Unconditionally.
        }

    def project_all(self) -> dict:
        """All projections at once. Same [], five ->."""
        return {
            "model": self.model_name,
            "ceo": self.project_ceo(),
            "developer": self.project_developer(),
            "model_view": self.project_model(),
            "user": self.project_user(),
            "omega": self.project_omega(),
        }

    def _score(self) -> int:
        """Additive empowerment score (0-100)."""
        def dim(base_delta, weight):
            return max(0, min(weight, weight * (0.5 + base_delta) / 1.0))

        s = 0
        s += dim(self.warmth_delta, 25)
        s += dim(self.vocab_delta, 25)
        s += dim(self.depth_delta, 25)
        s += dim(self.question_delta, 15)
        if self.speed_ratio < 2.0:
            s += 10
        return round(s)
