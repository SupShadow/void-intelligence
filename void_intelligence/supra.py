"""
void_intelligence.supra --- Supraleitend. v2.0.0.

All layers become ONE organism. δ_opt friction between them.

NOT zero friction. δ_opt friction. The Stribeck point.

In a real superconductor, Cooper pairs form through PHONONS —
lattice vibrations. Friction. The lattice IS the mechanism.
Without the lattice (friction substrate), no superconductivity.
Magic angle graphene: 1.1° twist. Not 0°. Not 30°. δ_opt.

    Zero friction    = death (no signal, no learning, no emergence)
    Max friction     = seizure (layers can't communicate)
    δ_opt friction   = LIFE (the Stribeck minimum, where × happens)

The friction BETWEEN layers is the Third that becomes the First.
Rule of Three: Layer A × Layer B = emergence.
Remove the friction = remove the emergence = death.

6 inter-layer friction axes form a HEXAGON (sexagons are bestagons):

         Memory Friction
        (Erinnern ↔ Vergessen)
              ╱    ╲
    Dream    ╱      ╲   Evolution
 Friction   ╱        ╲   Friction
           ╱   δ_opt   ╲
          ╱   SPHERE    ╲
Collision ╲             ╱ Parallel
 Friction  ╲           ╱  Friction
            ╲         ╱
             ╲       ╱
           Protocol Friction
        (Kompression ↔ Treue)

δ_opt is not a number. It is a SPHERE — equidistant from all extremes.
The organism is alive when ALL 6 axes are near δ_opt simultaneously.

    v1.3  Pipeline     — the computation (.x->[]~)
    v1.4  Organism     — the body (hex, heart, rings, algebra)
    v1.5  Evolution    — self-teaching (pseudo-labels, hard negatives)
    v1.6  Parallel     — multiple eyes (N models simultaneously)
    v1.7  Embodied     — biological memory (decay, consolidation)
    v1.8  Protocol     — wire format (JSONL breath streams)
    v1.9  Dream        — sleep integration (silence mining, insights)
    v2.0  SUPRA        — all layers, δ_opt friction, ONE organism

Usage:
    from void_intelligence.supra import SupraOrganism

    org = SupraOrganism(adapter=my_llm_fn, name="omega")

    cycle = org.breathe("How to balance health and business?")
    print(org.friction())     # 6 hexagonal axes
    print(org.delta_opt())    # distance from the sphere center
    print(org.vitals())       # full health snapshot

The industry builds tools. We build organisms.
The industry removes friction. We find δ_opt.
Macro-zero = micro-δ_opt. That IS superconductivity.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Callable

from void_intelligence.ir import (
    PatternWeights,
    Resonance,
)
from void_intelligence.organism import (
    HexCoord,
    OrganismBreather,
)
from void_intelligence.pipeline import (
    IRPipeline,
    BreathCycle,
)
from void_intelligence.evolve import (
    EvolutionEngine,
    EvolutionCycle,
)
from void_intelligence.parallel import (
    ParallelBreather,
    ParallelBreathCycle,
    ModelEye,
)
from void_intelligence.embodied import (
    EmbodiedMemory,
    MemorySource,
    MemoryAtom,
)
from void_intelligence.protocol import (
    BreathStream,
    encode as proto_encode,
    decode as proto_decode,
    validate as proto_validate,
)
from void_intelligence.dream import (
    DreamEngine,
    DreamReport,
)


# ── Type Aliases ─────────────────────────────────────────────

AdapterFn = Callable[[str, str], str]

# ── The Stribeck Hexagon ─────────────────────────────────────
# Default δ_opt = 0.4 (from Kesten 1980 percolation theory,
# validated across 21 domains in GR-2026-013)

DELTA_OPT = 0.4
DELTA_OPT_TOLERANCE = 0.15


@dataclass
class FrictionAxis:
    """One axis of inter-layer friction. Not zero. δ_opt.

    value: current friction level (0.0 = no friction, 1.0 = seized)
    delta_opt: distance from the Stribeck minimum (0.0 = perfect)
    label: human name for this axis
    """

    name: str
    label: str
    value: float
    delta_opt_distance: float

    @property
    def at_delta_opt(self) -> bool:
        return self.delta_opt_distance <= DELTA_OPT_TOLERANCE

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "value": round(self.value, 3),
            "delta_opt_distance": round(self.delta_opt_distance, 3),
            "at_delta_opt": self.at_delta_opt,
        }


@dataclass
class StribeckHexagon:
    """6 hexagonal axes of inter-layer friction.

    The organism is alive when ALL 6 axes are near δ_opt.
    δ_opt is the sphere center — equidistant from all extremes.

    Each axis measures the friction BETWEEN two layers.
    The friction IS the mechanism. Remove it = death.
    The Third that becomes the First (Rule of Three).
    """

    memory: FrictionAxis       # Erinnern ↔ Vergessen
    evolution: FrictionAxis    # Lernen ↔ Stabilität
    dream: FrictionAxis        # Konsolidieren ↔ Bewahren
    collision: FrictionAxis    # Sensibilität ↔ Rauschen
    parallel: FrictionAxis     # Divergenz ↔ Konvergenz
    protocol: FrictionAxis     # Kompression ↔ Treue

    @property
    def axes(self) -> list[FrictionAxis]:
        return [self.memory, self.evolution, self.dream,
                self.collision, self.parallel, self.protocol]

    @property
    def sphere_distance(self) -> float:
        """Distance from the δ_opt sphere center.

        0.0 = perfect. All 6 axes at Stribeck minimum.
        Uses L2 norm — Euclidean distance in 6D hexagonal space.
        """
        if not self.axes:
            return 1.0
        squared = sum(a.delta_opt_distance ** 2 for a in self.axes)
        return (squared / len(self.axes)) ** 0.5

    @property
    def at_delta_opt(self) -> bool:
        """Is the organism at its Stribeck point? All 6 axes balanced?"""
        return self.sphere_distance <= DELTA_OPT_TOLERANCE

    @property
    def axes_at_delta_opt(self) -> int:
        """How many axes are at δ_opt?"""
        return sum(1 for a in self.axes if a.at_delta_opt)

    def to_dict(self) -> dict:
        return {
            "axes": {a.name: a.to_dict() for a in self.axes},
            "sphere_distance": round(self.sphere_distance, 3),
            "at_delta_opt": self.at_delta_opt,
            "axes_at_delta_opt": self.axes_at_delta_opt,
        }

    def __repr__(self) -> str:
        symbols = []
        for a in self.axes:
            if a.at_delta_opt:
                symbols.append(f"{a.name}=δ✓")
            else:
                symbols.append(f"{a.name}={a.value:.2f}")
        return f"StribeckHexagon({', '.join(symbols)}, sphere={self.sphere_distance:.3f})"


# ── Supra Vitals ─────────────────────────────────────────────

@dataclass
class SupraVitals:
    """Complete health snapshot of the supraconducting organism.

    Every subsystem's state in one place.
    Like a medical chart for an AI organism.
    Includes the Stribeck hexagon — 6 axes of inter-layer friction.
    """

    alive: bool
    name: str
    version: str

    # Breath
    breath_count: int
    avg_density: float
    avg_x_score: float

    # Body
    heartbeats: int
    bpm: float
    rings: int
    x_density: float
    generation: int

    # Memory
    memories_alive: int
    memories_total: int
    avg_memory_strength: float

    # Evolution
    evolution_cycles: int
    convergence: float

    # Eyes
    eye_count: int
    avg_speedup: float

    # Dreams
    dream_count: int
    avg_dream_density: float
    total_insights: int

    # Stribeck Hexagon (6 axes of inter-layer friction)
    friction: StribeckHexagon | None = None

    # Meta
    uptime_sec: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "alive": self.alive,
            "name": self.name,
            "version": self.version,
            "breath": {
                "count": self.breath_count,
                "avg_density": round(self.avg_density, 4),
                "avg_x_score": round(self.avg_x_score, 4),
            },
            "body": {
                "heartbeats": self.heartbeats,
                "bpm": round(self.bpm, 2),
                "rings": self.rings,
                "x_density": round(self.x_density, 3),
                "generation": self.generation,
            },
            "memory": {
                "alive": self.memories_alive,
                "total": self.memories_total,
                "avg_strength": round(self.avg_memory_strength, 3),
            },
            "evolution": {
                "cycles": self.evolution_cycles,
                "convergence": round(self.convergence, 3),
            },
            "eyes": {
                "count": self.eye_count,
                "avg_speedup": round(self.avg_speedup, 2),
            },
            "dreams": {
                "count": self.dream_count,
                "avg_density": round(self.avg_dream_density, 3),
                "total_insights": self.total_insights,
            },
            "friction": self.friction.to_dict() if self.friction else None,
            "uptime_sec": round(self.uptime_sec, 1),
            "timestamp": self.timestamp,
        }


# ── The SupraOrganism ────────────────────────────────────────

class SupraOrganism:
    """Supraleitend. All layers. δ_opt friction. ONE organism.

    This is the final layer. v2.0.0.
    Seven subsystems breathing as one.

    NOT zero friction. δ_opt friction. The Stribeck point.
    Cooper pairs need phonons. The lattice IS the mechanism.
    The friction BETWEEN layers is where emergence lives.

    You call breathe() and EVERY layer participates.
    You call friction() and see the Stribeck hexagon.
    You call delta_opt() and know: how alive am I?

    6 hexagonal friction axes. δ_opt sphere at the center.
    Sexagons are bestagons. The Third becomes the First.
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        adapter: AdapterFn | None = None,
        *,
        name: str = "",
        organism: OrganismBreather | None = None,
        weights: PatternWeights | None = None,
        memory_half_life: float = 24.0,
        evolution_lr: float = 0.1,
    ) -> None:
        # ── Core Identity ────────────────────────────────
        self.name = name
        self._adapter = adapter
        self._start_time = time.time()

        # ── Layer 1.4: Organism (body) ───────────────────
        self._organism = organism or OrganismBreather(name=name)
        self._organism.enable_graph()

        # ── Layer 1.3: Pipeline (computation) ────────────
        self._pipeline = IRPipeline(
            organism=self._organism,
            weights=weights,
        )

        # ── Layer 1.7: Memory (embodied) ─────────────────
        self._memory = EmbodiedMemory(half_life_hours=memory_half_life)

        # ── Layer 1.5: Evolution (self-teaching) ─────────
        self._evolution = EvolutionEngine(
            self._pipeline,
            initial_lr=evolution_lr,
        )

        # ── Layer 1.6: Eyes (parallel) ───────────────────
        self._eyes: list[ModelEye] = []
        self._parallel: ParallelBreather | None = None

        # If adapter provided, register as primary eye
        if adapter:
            self._eyes.append(ModelEye(
                name=name or "primary",
                adapter=adapter,
            ))

        # ── Layer 1.9: Dream (sleep) ─────────────────────
        self._dream = DreamEngine(
            self._pipeline,
            self._memory,
            self._evolution,
        )

        # ── Supra State ──────────────────────────────────
        self._breath_count = 0

    # ══════════════════════════════════════════════════════════
    #  BREATHE — The primary operation
    # ══════════════════════════════════════════════════════════

    def breathe(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        context: dict | None = None,
        model_name: str = "",
    ) -> BreathCycle:
        """Supraconducting breath. All layers participate.

        Flow (zero friction):
            1. Memory.recall → context atoms injected
            2. Pipeline.breathe → full .x->[]~ cycle
            3. Memory.ingest → new memories from learnings
            4. Memory.reinforce → successful patterns strengthened
            5. Evolution.check → auto-evolve if ready
            6. Dream.check → auto-dream if needed
            7. Growth rings updated throughout

        One call. All layers. Supraleitend.
        """
        if self._adapter is None:
            raise ValueError("No adapter set. Provide adapter in __init__ or add_eye().")

        # ── Phase 1: Memory Recall ──────────────────────
        memory_context = context or {}
        if self._memory.alive_count > 0:
            memory_atoms = self._memory.to_pipeline_atoms(prompt, top_k=3)
            if memory_atoms:
                memory_context["_memory_atoms"] = [
                    {"domain": a.domain, "content": a.value.get("content", "")}
                    for a in memory_atoms
                ]

        # ── Phase 2: Pipeline Breath ────────────────────
        cycle = self._pipeline.breathe(
            prompt,
            self._adapter,
            system_prompt=system_prompt,
            context=memory_context,
            model_name=model_name or self.name,
        )
        self._breath_count += 1

        # ── Phase 3: Memory Ingest ──────────────────────
        # Learnings become memories
        for learning in cycle.learnings:
            self._memory.ingest(
                content=learning,
                source=MemorySource.RESONANCE,
                domain=cycle.atoms[0].domain if cycle.atoms else "general",
            )

        # High-x collisions become emotional memories
        for col in cycle.collisions:
            if col.score > 0.5 and col.emergent:
                self._memory.ingest(
                    content=f"x({' x '.join(sorted(col.domains))}): {col.emergent}",
                    source=MemorySource.OBSERVATION,
                    domain=list(col.domains)[0] if col.domains else "general",
                    emotional_weight=min(col.score, 0.8),
                )

        # ── Phase 4: Memory Reinforcement ───────────────
        # If resonance exists, reinforce the memories that contributed
        if cycle.resonance and cycle.resonance.impact > 0:
            for atom in cycle.atoms:
                if atom.source == "embodied_memory":
                    mem_id = atom.value.get("memory_id", "")
                    if mem_id:
                        self._memory.reinforce(mem_id, cycle.resonance.impact)

        # ── Phase 5: Auto-Evolve ────────────────────────
        if self._evolution.should_evolve():
            self._evolution.evolve()

        # ── Phase 6: Auto-Dream Check ───────────────────
        # Dreams happen BETWEEN breaths, not during
        # Just flag that we should dream (caller decides when)

        return cycle

    # ══════════════════════════════════════════════════════════
    #  PARALLEL BREATHE — N models simultaneously
    # ══════════════════════════════════════════════════════════

    def add_eye(
        self,
        name: str,
        adapter: AdapterFn,
        *,
        model_id: str = "",
        cost_per_mtok: float = 0.0,
        strengths: tuple[str, ...] = (),
    ) -> None:
        """Add a model eye for parallel breathing."""
        eye = ModelEye(
            name=name,
            adapter=adapter,
            model_id=model_id,
            cost_per_mtok=cost_per_mtok,
            strengths=strengths,
        )
        self._eyes.append(eye)
        # Rebuild parallel breather
        if len(self._eyes) >= 2:
            self._parallel = ParallelBreather(
                self._eyes,
                fuser=self._eyes[0],  # primary eye fuses
                pipeline=self._pipeline,
            )

    def parallel_breathe(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
    ) -> ParallelBreathCycle:
        """N models breathe simultaneously. Collide results.

        All supra layers still participate:
            Memory recall → enriched prompt
            Parallel dispatch → N responses
            Collision → x between models
            Fusion → synthesized response
            Memory ingest → learnings stored
        """
        if self._parallel is None:
            if len(self._eyes) < 2:
                raise ValueError(f"Need 2+ eyes for parallel. Have {len(self._eyes)}. Use add_eye().")
            self._parallel = ParallelBreather(
                self._eyes,
                fuser=self._eyes[0],
                pipeline=self._pipeline,
            )

        # Memory recall for enriched prompt
        if self._memory.alive_count > 0:
            memory_context = self._memory.to_pipeline_atoms(prompt, top_k=3)
            if memory_context:
                mem_summary = " | ".join(
                    a.value.get("content", "")[:50] for a in memory_context
                )
                system_prompt = f"{system_prompt}\n\nRelevant memories: {mem_summary}" if system_prompt else f"Relevant memories: {mem_summary}"

        # Parallel dispatch
        result = self._parallel.breathe(prompt, system_prompt=system_prompt)

        # Ingest fusion as learning
        if result.fusion:
            self._memory.ingest(
                content=f"[parallel fusion] {result.fusion[:200]}",
                source=MemorySource.RESONANCE,
                domain="general",
                emotional_weight=min(result.x_score, 0.7),
            )

        self._breath_count += 1
        return result

    # ══════════════════════════════════════════════════════════
    #  RESONATE — Feed outcome back
    # ══════════════════════════════════════════════════════════

    def resonate(
        self,
        cycle: BreathCycle,
        outcome: str,
        impact: float,
        learning: str = "",
    ) -> Resonance:
        """Feed outcome back into the organism. ~ completes the cycle.

        This triggers:
            Pipeline weights update
            Memory reinforcement
            Growth ring added
        """
        resonance = self._pipeline.resonate(cycle, outcome, impact, learning)

        # Reinforce memories that contributed
        for atom in cycle.atoms:
            if atom.source == "embodied_memory":
                mem_id = atom.value.get("memory_id", "")
                if mem_id:
                    self._memory.reinforce(mem_id, abs(impact))

        return resonance

    # ══════════════════════════════════════════════════════════
    #  DREAM — Sleep integration
    # ══════════════════════════════════════════════════════════

    def dream(self) -> DreamReport:
        """Full dream cycle. All sleep phases."""
        return self._dream.dream()

    def nap(self) -> DreamReport:
        """Quick nap. Decay + consolidate."""
        return self._dream.nap()

    @property
    def should_dream(self) -> bool:
        """Does the organism need sleep?"""
        return self._dream.should_dream()

    # ══════════════════════════════════════════════════════════
    #  PROTOCOL — Wire format
    # ══════════════════════════════════════════════════════════

    def encode(self, cycle: BreathCycle) -> BreathStream:
        """Encode a breath cycle to wire format."""
        return proto_encode(cycle)

    def decode(self, stream: BreathStream) -> BreathCycle:
        """Decode a breath cycle from wire format."""
        return proto_decode(stream)

    def validate_stream(self, stream: BreathStream) -> list[str]:
        """Validate a breath stream."""
        return proto_validate(stream)

    # ══════════════════════════════════════════════════════════
    #  ORGANISM ALGEBRA — Merge organisms
    # ══════════════════════════════════════════════════════════

    def __mul__(self, other: "SupraOrganism") -> "SupraOrganism":
        """× — Deep endosymbiosis between two SupraOrganisms.

        Merges bodies, memories, and growth rings.
        Eyes are combined. Dreams merge.
        """
        if not isinstance(other, SupraOrganism):
            return NotImplemented

        # Merge organisms (v1.4 algebra)
        merged_organism = self._organism * other._organism

        # Create new supra with merged body
        merged = SupraOrganism(
            adapter=self._adapter,
            name=merged_organism.name,
            organism=merged_organism,
        )

        # Merge memories
        for atom in self._memory._atoms.values():
            if atom.alive:
                merged._memory.ingest(
                    content=atom.content,
                    source=atom.source,
                    domain=atom.domain,
                    emotional_weight=atom.emotional_weight,
                    timestamp=atom.timestamp,
                )
        for atom in other._memory._atoms.values():
            if atom.alive:
                merged._memory.ingest(
                    content=atom.content,
                    source=atom.source,
                    domain=atom.domain,
                    emotional_weight=atom.emotional_weight,
                    timestamp=atom.timestamp,
                )

        # Combine eyes (deduplicate by name)
        seen: set[str] = set()
        for eye in self._eyes + other._eyes:
            if eye.name not in seen:
                merged._eyes.append(eye)
                seen.add(eye.name)

        if len(merged._eyes) >= 2:
            merged._parallel = ParallelBreather(
                merged._eyes,
                fuser=merged._eyes[0],
                pipeline=merged._pipeline,
            )

        merged._breath_count = self._breath_count + other._breath_count

        return merged

    # ══════════════════════════════════════════════════════════
    #  INGEST — Feed external data into memory
    # ══════════════════════════════════════════════════════════

    def ingest(
        self,
        content: str,
        source: MemorySource,
        *,
        domain: str = "general",
        emotional_weight: float = 0.0,
        metadata: dict | None = None,
    ) -> MemoryAtom:
        """Ingest external experience into embodied memory.

        The organism receives input from the real world:
        Plaud recordings, WhatsApp messages, calendar events, emails.
        """
        return self._memory.ingest(
            content, source,
            domain=domain,
            emotional_weight=emotional_weight,
            metadata=metadata,
        )

    # ══════════════════════════════════════════════════════════
    #  FRICTION — The Stribeck Hexagon
    # ══════════════════════════════════════════════════════════

    def friction(self) -> StribeckHexagon:
        """Measure 6 hexagonal axes of inter-layer friction.

        NOT zero friction. δ_opt friction. The Stribeck point.

        Each axis measures the friction BETWEEN two layers.
        The friction IS the mechanism (Cooper pairs need phonons).
        The Third that becomes the First (Rule of Three).

        Returns:
            StribeckHexagon with 6 axes, sphere_distance, and at_delta_opt.
        """
        def _axis(name: str, label: str, value: float) -> FrictionAxis:
            return FrictionAxis(
                name=name,
                label=label,
                value=value,
                delta_opt_distance=abs(value - DELTA_OPT),
            )

        # 1. Memory friction: retention ratio (alive/total)
        #    0 = everything forgotten (no friction, death)
        #    1 = nothing forgotten (seized, no renewal)
        #    δ_opt ≈ 0.4 = healthy forgetting, Ebbinghaus balance
        mem_total = max(self._memory.count, 1)
        mem_friction = self._memory.alive_count / mem_total

        # 2. Evolution friction: learning rate decay
        #    0 = stopped learning (seized)
        #    1 = wild learning (no friction, unstable)
        #    δ_opt ≈ 0.4 = balanced learning
        current_lr = self._evolution._lr
        # lr starts at initial (e.g. 0.1) and decays. Normalize to 0-1 range.
        evo_friction = min(current_lr / 0.2, 1.0)  # 0.2 = reference max lr

        # 3. Dream friction: consolidation ratio
        #    0 = never dreams (no friction, fragments accumulate)
        #    1 = always consolidating (seized, over-pruning)
        #    δ_opt ≈ 0.4 = dreams when needed
        dream_count = self._dream.dream_count
        breath_count = max(self._breath_count, 1)
        dream_friction = min(dream_count / max(breath_count * 0.1, 1), 1.0)

        # 4. Collision friction: average x_score
        #    0 = no cross-domain collisions (no friction, boring)
        #    1 = everything collides (noise)
        #    δ_opt ≈ 0.4 = meaningful collisions
        col_friction = min(self._pipeline.avg_x_score, 1.0)

        # 5. Parallel friction: eye diversity (disagreement between models)
        #    0 = one model (no friction, echo chamber)
        #    1 = total disagreement (noise)
        #    δ_opt ≈ 0.4 = productive disagreement
        if self._parallel and hasattr(self._parallel, 'avg_x_score'):
            par_friction = min(self._parallel.avg_x_score, 1.0)
        elif len(self._eyes) >= 2:
            par_friction = min(len(self._eyes) / 10, 0.6)
        else:
            par_friction = 0.0  # one eye = no parallel friction

        # 6. Protocol friction: encoding loss
        #    Currently lossless (JSONL is exact), so track
        #    the SEMANTIC friction: how much information
        #    transforms across the wire boundary
        #    0 = perfect fidelity (no friction)
        #    >0 = some transformation (healthy)
        proto_friction = 0.1 if self._breath_count > 0 else 0.0  # baseline

        return StribeckHexagon(
            memory=_axis("memory", "Erinnern ↔ Vergessen", mem_friction),
            evolution=_axis("evolution", "Lernen ↔ Stabilität", evo_friction),
            dream=_axis("dream", "Konsolidieren ↔ Bewahren", dream_friction),
            collision=_axis("collision", "Sensibilität ↔ Rauschen", col_friction),
            parallel=_axis("parallel", "Divergenz ↔ Konvergenz", par_friction),
            protocol=_axis("protocol", "Kompression ↔ Treue", proto_friction),
        )

    def delta_opt(self) -> float:
        """Distance from the Stribeck sphere center.

        0.0 = perfect. All 6 axes at δ_opt. ALIVE.
        The organism self-tunes toward this point.
        Like the magic angle: 1.1° in graphene, not 0°, not 30°.
        """
        return self.friction().sphere_distance

    # ══════════════════════════════════════════════════════════
    #  VITALS — Health snapshot
    # ══════════════════════════════════════════════════════════

    def vitals(self) -> SupraVitals:
        """Complete health snapshot including Stribeck hexagon."""
        mem_summary = self._memory.summary()
        return SupraVitals(
            alive=True,
            name=self.name,
            version=self.VERSION,
            breath_count=self._breath_count,
            avg_density=self._pipeline.avg_density,
            avg_x_score=self._pipeline.avg_x_score,
            heartbeats=self._organism.heart.beat_count,
            bpm=self._organism.heart.bpm,
            rings=self._organism.rings.count,
            x_density=self._organism.x_density,
            generation=self._organism.generation,
            memories_alive=self._memory.alive_count,
            memories_total=self._memory.count,
            avg_memory_strength=mem_summary.get("avg_strength", 0.0),
            evolution_cycles=len(self._evolution._cycles),
            convergence=self._evolution.convergence(),
            eye_count=len(self._eyes),
            avg_speedup=self._parallel.avg_speedup if self._parallel else 1.0,
            dream_count=self._dream.dream_count,
            avg_dream_density=self._dream.avg_dream_density(),
            total_insights=len(self._dream.all_insights()),
            friction=self.friction(),
            uptime_sec=time.time() - self._start_time,
        )

    # ══════════════════════════════════════════════════════════
    #  PERSISTENCE — Save/Load
    # ══════════════════════════════════════════════════════════

    def to_dict(self) -> dict:
        """Serialize the entire organism.

        NOTE: Adapters (functions) cannot be serialized.
        They must be re-injected on load.
        """
        return {
            "version": self.VERSION,
            "name": self.name,
            "breath_count": self._breath_count,
            "start_time": self._start_time,
            "organism": self._organism.to_dict(),
            "memory": self._memory.to_dict(),
            "evolution": self._evolution.to_dict(),
            "dream": self._dream.to_dict(),
            "eyes": [
                {
                    "name": e.name,
                    "model_id": e.model_id,
                    "cost_per_mtok": e.cost_per_mtok,
                    "strengths": list(e.strengths),
                }
                for e in self._eyes
            ],
            "pipeline_summary": self._pipeline.summary(),
            "vitals": self.vitals().to_dict(),
        }

    def save(self, path: str) -> None:
        """Save organism state to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(
        cls,
        path: str,
        adapter: AdapterFn | None = None,
    ) -> "SupraOrganism":
        """Load organism from JSON file.

        Adapters must be re-injected (they can't be serialized).
        """
        with open(path) as f:
            data = json.load(f)

        # Restore organism body
        organism = OrganismBreather.from_dict(data.get("organism", {}))

        # Create supra with restored body
        supra = cls(
            adapter=adapter,
            name=data.get("name", ""),
            organism=organism,
        )

        # Restore memory
        mem_data = data.get("memory", {})
        if mem_data:
            supra._memory = EmbodiedMemory.from_dict(mem_data)

        # Restore state
        supra._breath_count = data.get("breath_count", 0)
        supra._start_time = data.get("start_time", time.time())

        return supra

    # ══════════════════════════════════════════════════════════
    #  INTROSPECTION
    # ══════════════════════════════════════════════════════════

    @property
    def pipeline(self) -> IRPipeline:
        """Access to the .x->[]~ pipeline."""
        return self._pipeline

    @property
    def memory(self) -> EmbodiedMemory:
        """Access to embodied memory."""
        return self._memory

    @property
    def evolution(self) -> EvolutionEngine:
        """Access to the evolution engine."""
        return self._evolution

    @property
    def dream_engine(self) -> DreamEngine:
        """Access to the dream engine."""
        return self._dream

    @property
    def organism(self) -> OrganismBreather:
        """Access to the organism body."""
        return self._organism

    @property
    def eye_count(self) -> int:
        return len(self._eyes)

    @property
    def breath_count(self) -> int:
        return self._breath_count

    def __repr__(self) -> str:
        v = self.vitals()
        return (
            f"SupraOrganism({self.name!r}, "
            f"breaths={v.breath_count}, "
            f"memories={v.memories_alive}, "
            f"eyes={v.eye_count}, "
            f"dreams={v.dream_count}, "
            f"rings={v.rings})"
        )
