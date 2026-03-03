"""
void_intelligence.dream --- The Dream Layer.

v1.9.0 — The threshold between parts (v1.x) and whole (v2.0).

The industry builds pipelines that never sleep.
We build organisms that DREAM.

Dreaming is NOT downtime. It's where the REAL learning happens.
Neuroscience: the hippocampus replays the day's experiences.
The cortex integrates them into long-term knowledge.
Creative breakthroughs happen in dreams (Kekulé, McCartney, Tesla).

In void-intelligence, a Dream does:

    1. REPLAY — All breath cycles from the session
    2. DECAY — Ebbinghaus forgetting (weak memories fade)
    3. CONSOLIDATE — Similar memories merge into semantic knowledge
    4. EVOLVE — Self-teaching loop runs on accumulated cycles
    5. SILENCE-MINE — Discover patterns in what was [] (not said)
    6. DREAM-INSIGHT — Connections that waking breath couldn't see

The Dream is the δ_opt between waking and sleeping.
The Kumbhaka between breaths. The [] that becomes .
The hypnagogic state where parts TOUCH each other for the first time.

Usage:
    from void_intelligence.dream import DreamEngine, DreamReport

    engine = DreamEngine(pipeline, memory, evolution)

    # Dream (overnight processing, between sessions)
    report = engine.dream()
    print(report.insights)        # what the dream found
    print(report.consolidated)    # memories merged
    print(report.evolved)         # weights improved
    print(report.silence_patterns)  # persistent [] across cycles

    # Quick nap (lighter version, between conversations)
    nap = engine.nap()

The industry has RAG, fine-tuning, RLHF as separate processes.
We dream. One process. Everything integrates.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from void_intelligence.pipeline import IRPipeline, BreathCycle
    from void_intelligence.evolve import EvolutionEngine, EvolutionCycle
    from void_intelligence.embodied import EmbodiedMemory


# ── Dream Insight ────────────────────────────────────────────

@dataclass
class DreamInsight:
    """One insight born from dreaming.

    Not derived from a single breath. Emerges from the SPACE
    between breaths. The [] that has been building up across
    many cycles, now crystallizing into . during sleep.
    """

    content: str
    insight_type: str  # "silence_pattern" | "cross_cycle" | "decay_survivor" | "consolidation" | "evolution"
    source_cycles: int = 0  # how many cycles contributed
    confidence: float = 0.0
    domains: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "content": self.content[:200],
            "type": self.insight_type,
            "source_cycles": self.source_cycles,
            "confidence": round(self.confidence, 3),
            "domains": self.domains,
            "timestamp": self.timestamp,
        }


# ── Dream Report ─────────────────────────────────────────────

@dataclass
class DreamReport:
    """The result of one dream cycle. What the organism learned while sleeping.

    A dream report is like waking up and remembering:
        - What faded (decay)
        - What merged (consolidation)
        - What improved (evolution)
        - What the silence was saying (silence mining)
        - What new connections emerged (insights)
    """

    # Phase results
    cycles_replayed: int = 0
    memories_decayed: int = 0
    memories_consolidated: int = 0
    evolution_result: "EvolutionCycle | None" = None

    # Insights
    insights: list[DreamInsight] = field(default_factory=list)
    silence_patterns: dict[str, int] = field(default_factory=dict)  # silence -> count

    # Metrics
    dream_duration_ms: float = 0.0
    pre_memory_count: int = 0
    post_memory_count: int = 0
    pre_weight_count: int = 0
    post_weight_count: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def insight_count(self) -> int:
        return len(self.insights)

    @property
    def memory_delta(self) -> int:
        """Net change in alive memories. Negative = healthy forgetting."""
        return self.post_memory_count - self.pre_memory_count

    @property
    def weight_delta(self) -> int:
        """New patterns learned."""
        return self.post_weight_count - self.pre_weight_count

    @property
    def dream_density(self) -> float:
        """How productive was this dream? 0 = empty, 1 = breakthrough."""
        factors = [
            min(self.insight_count / 5, 1.0) * 0.4,
            min(self.memories_consolidated / 3, 1.0) * 0.2,
            (1.0 if self.evolution_result and self.evolution_result.improved else 0.0) * 0.2,
            min(len(self.silence_patterns) / 5, 1.0) * 0.2,
        ]
        return sum(factors)

    def to_dict(self) -> dict:
        return {
            "cycles_replayed": self.cycles_replayed,
            "memories_decayed": self.memories_decayed,
            "memories_consolidated": self.memories_consolidated,
            "evolution_improved": bool(
                self.evolution_result and self.evolution_result.improved
            ),
            "insights": [i.to_dict() for i in self.insights],
            "silence_patterns": dict(list(self.silence_patterns.items())[:10]),
            "dream_density": round(self.dream_density, 3),
            "dream_duration_ms": round(self.dream_duration_ms, 1),
            "memory_delta": self.memory_delta,
            "weight_delta": self.weight_delta,
            "timestamp": self.timestamp,
        }

    def summary(self) -> str:
        """Human-readable dream summary."""
        lines = ["=== DREAM REPORT ==="]
        lines.append(f"Replayed {self.cycles_replayed} breath cycles")
        lines.append(f"Decayed: {self.memories_decayed} | Consolidated: {self.memories_consolidated}")
        if self.evolution_result:
            lines.append(f"Evolution: {'improved' if self.evolution_result.improved else 'stable'}")
        if self.insights:
            lines.append(f"\nInsights ({self.insight_count}):")
            for i in self.insights[:5]:
                lines.append(f"  [{i.insight_type}] {i.content[:80]}")
        if self.silence_patterns:
            lines.append(f"\nPersistent silence ({len(self.silence_patterns)}):")
            for pattern, count in list(self.silence_patterns.items())[:5]:
                lines.append(f"  [{count}x] {pattern}")
        lines.append(f"\nDream density: {self.dream_density:.2f}")
        lines.append(f"Duration: {self.dream_duration_ms:.0f}ms")
        return "\n".join(lines)


# ── Dream Engine ─────────────────────────────────────────────

class DreamEngine:
    """The organism's dreaming system. Where parts first touch.

    Wiring (v1.3-v1.8 → v1.9):
        Pipeline (v1.3) → replayed cycles become training data
        Organism (v1.4) → growth rings record dream insights
        Evolution (v1.5) → self-teaching loop runs on accumulated cycles
        Parallel (v1.6) → (not used in dreams — dreams are single-threaded, like real sleep)
        Memory (v1.7) → decay + consolidation during dream
        Protocol (v1.8) → dream report IS a breath (can be encoded)

    Usage:
        engine = DreamEngine(pipeline, memory, evolution)
        report = engine.dream()
    """

    def __init__(
        self,
        pipeline: "IRPipeline",
        memory: "EmbodiedMemory",
        evolution: "EvolutionEngine | None" = None,
    ) -> None:
        self._pipeline = pipeline
        self._memory = memory
        self._evolution = evolution
        self._dreams: list[DreamReport] = []

    # ── Phase 1: Replay ──────────────────────────────────────

    def _replay(self) -> list["BreathCycle"]:
        """Replay all breath cycles from the pipeline.

        The hippocampus replays the day's experiences.
        In our organism, the pipeline's cycle buffer IS the day.
        """
        return list(self._pipeline._cycles)

    # ── Phase 2: Decay ───────────────────────────────────────

    def _decay(self) -> int:
        """Apply Ebbinghaus forgetting. Weak memories fade.

        During sleep, the brain prunes weak synaptic connections.
        This is HEALTHY. An organism that forgets nothing is pathological.
        """
        return self._memory.decay()

    # ── Phase 3: Consolidate ─────────────────────────────────

    def _consolidate(self) -> int:
        """Merge similar weak memories into semantic knowledge.

        Sleep consolidation: episodic → semantic.
        Many similar experiences become ONE understanding.
        """
        return self._memory.consolidate()

    # ── Phase 4: Evolve ──────────────────────────────────────

    def _evolve(self) -> "EvolutionCycle | None":
        """Self-teaching loop on accumulated cycles.

        REM sleep: the brain rehearses and improves.
        Our evolution engine learns from its own breath cycles.
        """
        if self._evolution is None:
            return None

        # Only evolve if we have enough data
        if not self._evolution.should_evolve():
            return None

        return self._evolution.evolve()

    # ── Phase 5: Mine Silence ────────────────────────────────

    def _mine_silence(self, cycles: list["BreathCycle"]) -> dict[str, int]:
        """Find recurring patterns in what was NOT said across cycles.

        Persistent [] across many breaths = systematic blind spot.
        This is the dream's gift: seeing what waking life couldn't.

        Returns silence pattern → occurrence count.
        """
        counter: Counter[str] = Counter()

        for cycle in cycles:
            for s in cycle.silence:
                counter[s] += 1

        # Only report patterns that recur (appearing in 2+ cycles)
        return {
            pattern: count
            for pattern, count in counter.most_common(20)
            if count >= 2
        }

    # ── Phase 6: Dream Insights ──────────────────────────────

    def _generate_insights(
        self,
        cycles: list["BreathCycle"],
        silence_patterns: dict[str, int],
        memories_consolidated: int,
        evolution_result: "EvolutionCycle | None",
    ) -> list[DreamInsight]:
        """Generate dream insights from all phases.

        This is the creative part of dreaming.
        Not logic. EMERGENCE. Cross-cycle patterns that no
        single breath could see.
        """
        insights: list[DreamInsight] = []

        # ── Silence insights (what keeps not being said?) ────
        for pattern, count in list(silence_patterns.items())[:5]:
            if count >= 3:
                # Strong silence pattern = systematic blind spot
                domains = []
                if ":" in pattern:
                    parts = pattern.split(":")
                    domains = [p for p in parts if p not in ("uncollided", "weak_signal")]
                insights.append(DreamInsight(
                    content=f"Persistent silence: '{pattern}' appeared {count}x across cycles. Systematic blind spot.",
                    insight_type="silence_pattern",
                    source_cycles=count,
                    confidence=min(count / 10, 0.9),
                    domains=domains,
                ))

        # ── Cross-cycle collision patterns ──────────────────
        pattern_counter: Counter[str] = Counter()
        pattern_scores: defaultdict[str, list[float]] = defaultdict(list)
        for cycle in cycles:
            for col in cycle.collisions:
                pattern_counter[col.pattern] += 1
                pattern_scores[col.pattern].append(col.score)

        for pattern, count in pattern_counter.most_common(5):
            if count >= 3:
                avg_score = sum(pattern_scores[pattern]) / len(pattern_scores[pattern])
                insights.append(DreamInsight(
                    content=f"Recurring collision: '{pattern}' ({count}x, avg score {avg_score:.2f}). Core x axis.",
                    insight_type="cross_cycle",
                    source_cycles=count,
                    confidence=min(avg_score, 0.95),
                    domains=list({d for d in pattern.split() if ":" not in d and d != "x"}),
                ))

        # ── Decay survivors ─────────────────────────────────
        strongest = self._memory.strongest(3)
        for mem in strongest:
            if mem.age_hours > 24 and mem.strength > 0.7:
                insights.append(DreamInsight(
                    content=f"Decay survivor: '{mem.content[:80]}' ({mem.age_hours:.0f}h old, strength {mem.strength:.2f}). Core memory.",
                    insight_type="decay_survivor",
                    source_cycles=mem.access_count,
                    confidence=mem.strength,
                    domains=[mem.domain],
                ))

        # ── Consolidation insight ───────────────────────────
        if memories_consolidated > 0:
            insights.append(DreamInsight(
                content=f"Consolidated {memories_consolidated} memory groups. Episodic → semantic compression.",
                insight_type="consolidation",
                source_cycles=memories_consolidated,
                confidence=min(memories_consolidated / 5, 0.8),
            ))

        # ── Evolution insight ───────────────────────────────
        if evolution_result and evolution_result.improved:
            top_deltas = sorted(
                evolution_result.weight_deltas.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )[:3]
            delta_summary = ", ".join(
                f"{p}: {d:+.3f}" for p, d in top_deltas
            )
            insights.append(DreamInsight(
                content=f"Evolution improved weights: {delta_summary}",
                insight_type="evolution",
                source_cycles=len(self._pipeline._cycles),
                confidence=0.7,
            ))

        # ── Domain coverage insight ─────────────────────────
        domain_activity: Counter[str] = Counter()
        for cycle in cycles:
            for atom in cycle.atoms:
                if atom.type == "domain_signal":
                    domain_activity[atom.domain] += 1

        active_domains = {d for d, c in domain_activity.items() if c >= 2}
        memory_domains = set(self._memory.by_domain().keys())
        dormant = memory_domains - active_domains
        if dormant:
            insights.append(DreamInsight(
                content=f"Dormant domains (memories exist but no recent activity): {', '.join(sorted(dormant))}",
                insight_type="silence_pattern",
                source_cycles=len(cycles),
                confidence=0.5,
                domains=sorted(dormant),
            ))

        return insights

    # ── Dream (Full Sleep Cycle) ─────────────────────────────

    def dream(self) -> DreamReport:
        """Full dream cycle. The organism sleeps and integrates.

        Called between sessions, overnight, or when the organism
        detects it needs to consolidate (many cycles, high silence).

        Phase order mirrors biology:
            1. REPLAY (hippocampus replays the day)
            2. DECAY (pruning weak connections)
            3. CONSOLIDATE (episodic → semantic)
            4. EVOLVE (REM: rehearse and improve)
            5. SILENCE-MINE (what was the unconscious processing?)
            6. INSIGHT (the dream crystallizes)
        """
        t0 = time.time()
        report = DreamReport()

        # Capture pre-state
        report.pre_memory_count = self._memory.alive_count
        report.pre_weight_count = len(self._pipeline.weights.weights)

        # 1. REPLAY
        cycles = self._replay()
        report.cycles_replayed = len(cycles)

        # 2. DECAY
        report.memories_decayed = self._decay()

        # 3. CONSOLIDATE
        report.memories_consolidated = self._consolidate()

        # 4. EVOLVE
        report.evolution_result = self._evolve()

        # 5. SILENCE-MINE
        report.silence_patterns = self._mine_silence(cycles)

        # 6. INSIGHT
        report.insights = self._generate_insights(
            cycles,
            report.silence_patterns,
            report.memories_consolidated,
            report.evolution_result,
        )

        # Record post-state
        report.post_memory_count = self._memory.alive_count
        report.post_weight_count = len(self._pipeline.weights.weights)
        report.dream_duration_ms = (time.time() - t0) * 1000

        # Record dream in organism
        for insight in report.insights[:3]:
            self._pipeline.organism.exhale(learnings=[
                f"dream[{insight.insight_type}]: {insight.content[:80]}"
            ])

        self._dreams.append(report)

        return report

    # ── Nap (Light Sleep) ────────────────────────────────────

    def nap(self) -> DreamReport:
        """Quick nap. Decay + consolidate only. No evolution, no deep mining.

        Called between conversations. Lighter than dream().
        Like a 20-minute power nap vs. 8 hours of sleep.
        """
        t0 = time.time()
        report = DreamReport()

        report.pre_memory_count = self._memory.alive_count
        report.pre_weight_count = len(self._pipeline.weights.weights)

        # Only light phases
        report.memories_decayed = self._decay()
        report.memories_consolidated = self._consolidate()

        # Quick silence check (no deep mining)
        cycles = self._replay()
        report.cycles_replayed = len(cycles)
        silence_counter: Counter[str] = Counter()
        for cycle in cycles[-10:]:  # Only recent cycles
            for s in cycle.silence:
                silence_counter[s] += 1
        report.silence_patterns = {
            p: c for p, c in silence_counter.most_common(5) if c >= 2
        }

        report.post_memory_count = self._memory.alive_count
        report.post_weight_count = len(self._pipeline.weights.weights)
        report.dream_duration_ms = (time.time() - t0) * 1000

        self._dreams.append(report)
        return report

    # ── Should Dream? ────────────────────────────────────────

    def should_dream(self) -> bool:
        """Should the organism dream now?

        Biological triggers:
            - Enough cycles accumulated (enough experiences to process)
            - High silence ratio (the unconscious has material)
            - Long time since last dream
            - Memory pressure (too many weak memories)
        """
        cycles = self._pipeline._cycles
        if len(cycles) < 5:
            return False

        # Time since last dream
        if self._dreams:
            hours_since = (time.time() - self._dreams[-1].timestamp) / 3600
            if hours_since < 0.5:  # Don't dream twice in 30 min
                return False

        # Silence ratio (high = lots of unprocessed potential)
        total_silence = sum(len(c.silence) for c in cycles)
        avg_silence = total_silence / max(len(cycles), 1)
        if avg_silence > 2.0:
            return True

        # Memory pressure
        weak = sum(
            1 for a in self._memory._atoms.values()
            if a.alive and a.strength < 0.3
        )
        if weak > 10:
            return True

        # Enough cycles
        return len(cycles) >= 20

    # ── Introspection ────────────────────────────────────────

    @property
    def dream_count(self) -> int:
        return len(self._dreams)

    @property
    def last_dream(self) -> DreamReport | None:
        return self._dreams[-1] if self._dreams else None

    def avg_dream_density(self) -> float:
        if not self._dreams:
            return 0.0
        return sum(d.dream_density for d in self._dreams) / len(self._dreams)

    def all_insights(self) -> list[DreamInsight]:
        """All insights from all dreams."""
        return [i for d in self._dreams for i in d.insights]

    def summary(self) -> dict:
        """Dream system vitals."""
        return {
            "dreams": self.dream_count,
            "total_insights": len(self.all_insights()),
            "avg_density": round(self.avg_dream_density(), 3),
            "last_dream": self._dreams[-1].to_dict() if self._dreams else None,
            "should_dream": self.should_dream(),
        }

    def to_dict(self) -> dict:
        """Serialize dream history."""
        return {
            "version": 1,
            "dreams": [d.to_dict() for d in self._dreams[-20:]],
            "summary": self.summary(),
        }
