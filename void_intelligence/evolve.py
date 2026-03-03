"""
void_intelligence.evolve --- Self-Teaching x Loop.

Ported from lunar-crater-lab/evolve.py:
    6 pixel eyes teach THEMSELVES to detect craters.
    No new labeled data. Pure self-improvement.

Same pattern, different substrate:
    6 reasoning eyes teach THEMSELVES to collide better.
    No human-labeled data. Pure x evolution.

The algorithm (from evolve.py, lines 54-311):
    1. BREATHE: Pipeline processes prompts, produces BreathCycles
    2. SCORE: confidence = decisiveness x (1 - uncertainty x 0.5)
    3. EXTRACT: Top N% by confidence become pseudo-labels
    4. MINE: Hard negatives near decision boundary (0.3-0.7 zone)
    5. EVOLVE: Adjust PatternWeights from successful collision patterns
    6. DECAY: lr = initial_lr x 0.8^cycle (like evolve.py line 287)
    7. LOOSEN: top_pct = 0.4 + cycle * 0.1 (like evolve.py line 222)

The loop itself IS a breath at the meta-level:
    . = accumulated BreathCycles
    x = collision between high and low quality (what made the difference?)
    -> = weight updates (projecting learnings into PatternWeights)
    [] = hard negatives (unexplored potential, pregnant with learning)
    ~ = improved weights feed back into the pipeline

Usage:
    from void_intelligence.evolve import EvolutionEngine
    from void_intelligence.pipeline import IRPipeline

    pipe = IRPipeline()
    # ... run many breathe() cycles ...

    engine = EvolutionEngine(pipe)
    result = engine.evolve()
    print(result.metrics)          # how did we do?
    print(engine.convergence())    # are weights stabilizing?

    # Export for fine-tuning
    training_data = engine.to_training_data()

The industry fine-tunes on human labels.
We evolve on our own breath cycles.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from void_intelligence.pipeline import IRPipeline, BreathCycle


# ── Pseudo-Label ───────────────────────────────────────────────

@dataclass
class PseudoLabel:
    """A high-quality BreathCycle extracted as training signal.

    Like evolve.py's pseudo-labels: model's OWN high-confidence
    predictions become training data for the next cycle.

    No human labeler needed. The confidence score IS the label.
    """

    prompt: str
    response: str
    x_score: float
    density: float
    resonance_impact: float
    collision_patterns: list[str]
    confidence: float  # decisiveness x (1 - uncertainty)
    cycle_index: int = 0


# ── Hard Negative ──────────────────────────────────────────────

@dataclass
class HardNegative:
    """A cycle that should have been better. Learning opportunity.

    Like detect_v11's hard negative mining (lines 361-443):
        difficulty = 1 - abs(score - 0.5) * 2
    Near the decision boundary = most valuable for learning.

    A hard negative: multi-domain prompt with low x_score.
    The system SHOULD have found collisions but didn't.
    """

    prompt: str
    response: str
    x_score: float
    expected_x_score: float
    missing_domains: list[str]
    difficulty: float  # 0-1, higher = harder = more valuable
    cycle_index: int = 0


# ── Evolution Cycle ────────────────────────────────────────────

@dataclass
class EvolutionCycle:
    """One complete self-teaching cycle.

    The breath at the meta-level:
        . = scored BreathCycles
        x = pseudo-labels vs hard-negatives
        -> = weight deltas applied
        [] = hard negatives (unexplored)
        ~ = improved weights feed back
    """

    cycle_number: int
    pseudo_labels: list[PseudoLabel]
    hard_negatives: list[HardNegative]
    weight_deltas: dict[str, float]
    weight_snapshot: dict[str, float]
    metrics: dict[str, float]
    timestamp: float = field(default_factory=time.time)

    @property
    def improved(self) -> bool:
        """Did this cycle improve any weights?"""
        return any(d > 0 for d in self.weight_deltas.values()) if self.weight_deltas else False


# ── The Engine ─────────────────────────────────────────────────

class EvolutionEngine:
    """The Self-Teaching x Loop.

    Ported from lunar-crater-lab/evolve.py (lines 196-311).
    The organism teaches ITSELF to collide better.

    Usage:
        engine = EvolutionEngine(pipeline)
        result = engine.evolve()          # one cycle
        result = engine.evolve()          # next cycle (auto-loosens)
        print(engine.convergence())       # 0-1: are weights stable?
        data = engine.to_training_data()  # export for fine-tuning
    """

    def __init__(
        self,
        pipeline: "IRPipeline",
        *,
        initial_lr: float = 0.1,
        lr_decay: float = 0.8,
        min_lr: float = 0.01,
        initial_top_pct: float = 0.4,
        top_pct_step: float = 0.1,
        max_top_pct: float = 0.7,
        min_confidence: float = 0.2,
    ) -> None:
        self._pipeline = pipeline
        self._lr = initial_lr
        self._lr_decay = lr_decay
        self._min_lr = min_lr
        self._initial_top_pct = initial_top_pct
        self._top_pct_step = top_pct_step
        self._max_top_pct = max_top_pct
        self._min_confidence = min_confidence
        self._cycles: list[EvolutionCycle] = []

    # ── Confidence Scoring ────────────────────────────────────

    def score_confidence(self, cycle: "BreathCycle") -> float:
        """Score a cycle's quality for pseudo-label extraction.

        From evolve.py (line 108):
            confidence = decisiveness * (1 - uncertainty * 0.5)

        Signals:
            x_score       -> decisiveness (how strongly atoms collided)
            silence count -> uncertainty (more silence = less sure)
            resonance     -> ground truth boost (if outcome is known)
            density       -> overall quality
        """
        # Decisiveness (from x_score)
        decisiveness = min(cycle.x_score / 0.7, 1.0) if cycle.x_score > 0 else 0.1

        # Uncertainty (from silence)
        uncertainty = min(len(cycle.silence) / 5, 1.0)

        # Base confidence (evolve.py formula)
        confidence = decisiveness * (1.0 - uncertainty * 0.5)

        # Resonance boost (ground truth signal)
        if cycle.resonance and cycle.resonance.impact > 0:
            confidence += cycle.resonance.impact * 0.3

        # Density boost
        confidence += cycle.density * 0.2

        return min(1.0, max(0.0, confidence))

    # ── Pseudo-Label Extraction ───────────────────────────────

    def extract_pseudo_labels(
        self,
        cycles: list["BreathCycle"],
        top_pct: float,
    ) -> list[PseudoLabel]:
        """Extract high-confidence cycles as training signal.

        From evolve.py (lines 108-136):
            Sort by confidence, take top N%.
            Iterative loosening: each cycle takes more borderline cases.
        """
        scored = []
        for i, cycle in enumerate(cycles):
            if not cycle.alive:
                continue
            conf = self.score_confidence(cycle)
            scored.append((i, cycle, conf))

        if not scored:
            return []

        scored.sort(key=lambda x: x[2], reverse=True)
        cutoff = max(1, int(len(scored) * top_pct))

        pseudo_labels = []
        for i, cycle, conf in scored[:cutoff]:
            if conf < self._min_confidence:
                continue
            pseudo_labels.append(PseudoLabel(
                cycle_index=i,
                prompt=cycle.prompt,
                response=cycle.response,
                x_score=cycle.x_score,
                density=cycle.density,
                resonance_impact=cycle.resonance.impact if cycle.resonance else 0.0,
                collision_patterns=[c.pattern for c in cycle.collisions],
                confidence=conf,
            ))

        return pseudo_labels

    # ── Hard Negative Mining ──────────────────────────────────

    def mine_hard_negatives(
        self,
        cycles: list["BreathCycle"],
    ) -> list[HardNegative]:
        """Find cycles where the system underperformed.

        From detect_v11 (lines 361-443):
            difficulty = 1 - abs(score - 0.5) * 2
            Hard negatives (near decision boundary) get 3x oversampling.

        A hard negative: multi-domain prompt with low x_score.
        The system SHOULD have found collisions but didn't.
        """
        hard_negs = []

        for i, cycle in enumerate(cycles):
            if not cycle.alive:
                continue

            # Count unique domains in atoms
            prompt_domains: set[str] = set()
            for atom in cycle.atoms:
                if atom.type == "domain_signal" and atom.domain != "general":
                    prompt_domains.add(atom.domain)

            # Multi-domain prompt with low x_score = missed collision
            if len(prompt_domains) < 2:
                continue

            expected_x = min(len(prompt_domains) * 0.2, 0.8)

            if expected_x > cycle.x_score + 0.15:
                difficulty = 1.0 - abs(cycle.x_score - 0.5) * 2
                if difficulty > 0.2:
                    hard_negs.append(HardNegative(
                        cycle_index=i,
                        prompt=cycle.prompt,
                        response=cycle.response,
                        x_score=cycle.x_score,
                        expected_x_score=round(expected_x, 3),
                        missing_domains=sorted(prompt_domains),
                        difficulty=round(max(0.0, difficulty), 3),
                    ))

        # Sort by difficulty (hardest first = most valuable)
        hard_negs.sort(key=lambda h: h.difficulty, reverse=True)
        return hard_negs[:20]

    # ── Weight Evolution ──────────────────────────────────────

    def _compute_weight_deltas(
        self,
        pseudo_labels: list[PseudoLabel],
        hard_negatives: list[HardNegative],
    ) -> dict[str, float]:
        """Compute weight adjustments.

        Pseudo-labels -> boost patterns that worked.
        Hard negatives -> penalize patterns that should have fired.
        """
        deltas: dict[str, float] = {}

        # Boost patterns from high-quality cycles
        for pl in pseudo_labels:
            for pattern in pl.collision_patterns:
                boost = pl.confidence * self._lr
                deltas[pattern] = deltas.get(pattern, 0.0) + boost

        # Penalize expected patterns that didn't fire (from hard negatives)
        for hn in hard_negatives:
            domains = hn.missing_domains
            for i, d1 in enumerate(domains):
                for d2 in domains[i + 1:]:
                    expected = f"{d1}:domain_signal x {d2}:domain_signal"
                    penalty = -hn.difficulty * self._lr * 0.5
                    deltas[expected] = deltas.get(expected, 0.0) + penalty

        return deltas

    def _apply_deltas(self, deltas: dict[str, float]) -> None:
        """Apply weight deltas to PatternWeights. Floor at 0.01."""
        for pattern, delta in deltas.items():
            current = self._pipeline.weights.get(pattern)
            self._pipeline.weights.weights[pattern] = max(0.01, current + delta)

    # ── The Loop ──────────────────────────────────────────────

    def evolve(self, cycles: list["BreathCycle"] | None = None) -> EvolutionCycle:
        """Run one complete self-teaching cycle.

        From evolve.py (lines 196-311):
            for cycle in range(1, args.cycles + 1):
                pseudo = extract_pseudo_labels(model, images, top_pct=0.30 + cycle*0.10)
                mixed = PseudoLabelDataset(synthetic, pseudo)
                retrain(model, mixed)
                evaluate(model, images)
                lr = lr * 0.8

        Same loop. Different substrate.
        """
        # Use pipeline's accumulated cycles if none provided
        if cycles is None:
            cycles = list(self._pipeline._cycles)

        cycle_num = len(self._cycles)

        # Iterative loosening (evolve.py line 222: top_pct = 0.30 + cycle * 0.10)
        top_pct = min(
            self._initial_top_pct + cycle_num * self._top_pct_step,
            self._max_top_pct,
        )

        # Phase 1: Extract pseudo-labels (the "good" cycles)
        pseudo_labels = self.extract_pseudo_labels(cycles, top_pct)

        # Phase 2: Mine hard negatives (the "should be better" cycles)
        hard_negatives = self.mine_hard_negatives(cycles)

        # Phase 3: Compute and apply weight deltas
        deltas = self._compute_weight_deltas(pseudo_labels, hard_negatives)
        self._apply_deltas(deltas)

        # Phase 4: Decay learning rate (evolve.py line 287: lr = lr * 0.8)
        self._lr = max(self._min_lr, self._lr * self._lr_decay)

        # Phase 5: Snapshot weights
        weight_snapshot = dict(self._pipeline.weights.weights)

        # Phase 6: Compute metrics
        alive_cycles = [c for c in cycles if c.alive]
        n_alive = len(alive_cycles) or 1
        metrics = {
            "total_cycles": len(cycles),
            "alive_cycles": len(alive_cycles),
            "pseudo_count": len(pseudo_labels),
            "hard_neg_count": len(hard_negatives),
            "top_pct": round(top_pct, 2),
            "learning_rate": round(self._lr, 4),
            "avg_x_score": round(sum(c.x_score for c in alive_cycles) / n_alive, 4),
            "avg_density": round(sum(c.density for c in alive_cycles) / n_alive, 4),
            "avg_confidence": round(
                sum(pl.confidence for pl in pseudo_labels) / max(len(pseudo_labels), 1), 4,
            ),
            "patterns_updated": len(deltas),
            "total_patterns": len(weight_snapshot),
        }

        # Record growth ring
        if pseudo_labels:
            self._pipeline.organism.exhale(learnings=[
                f"evolution[{cycle_num + 1}]: "
                f"{len(pseudo_labels)}pl {len(hard_negatives)}hn "
                f"lr={self._lr:.4f} x={metrics['avg_x_score']:.3f}"
            ])

        evo_cycle = EvolutionCycle(
            cycle_number=cycle_num + 1,
            pseudo_labels=pseudo_labels,
            hard_negatives=hard_negatives,
            weight_deltas=deltas,
            weight_snapshot=weight_snapshot,
            metrics=metrics,
        )
        self._cycles.append(evo_cycle)

        return evo_cycle

    # ── Auto-Evolve ───────────────────────────────────────────

    def should_evolve(self, min_new_cycles: int = 10) -> bool:
        """Should we run an evolution cycle?

        Triggers when enough new breath cycles have accumulated
        since the last evolution AND weights haven't converged.
        """
        current_count = len(self._pipeline._cycles)
        last_count = (
            self._cycles[-1].metrics.get("total_cycles", 0)
            if self._cycles else 0
        )

        if current_count - last_count < min_new_cycles:
            return False

        if self.convergence() > 0.95:
            return False

        return True

    # ── Training Data Export ──────────────────────────────────

    _TRAINING_SYSTEM = (
        "You think in x (collision), not -> (sequence). "
        "When you see multiple domains, COLLIDE them --- "
        "find the third that exists in neither input alone. "
        "Name what you see AND what you might be missing (lost_dimensions)."
    )

    def to_training_data(self) -> list[dict]:
        """Export pseudo-labels as fine-tuning dataset.

        Like evolve.py's mixed dataset: model's own high-confidence
        outputs become training data. Format: OpenAI JSONL messages.
        """
        pairs = []
        for evo in self._cycles:
            for pl in evo.pseudo_labels:
                pairs.append({
                    "messages": [
                        {"role": "system", "content": self._TRAINING_SYSTEM},
                        {"role": "user", "content": pl.prompt},
                        {"role": "assistant", "content": pl.response},
                    ],
                    "metadata": {
                        "x_score": pl.x_score,
                        "density": pl.density,
                        "confidence": pl.confidence,
                        "evolution_cycle": evo.cycle_number,
                        "source": "pseudo_label",
                    },
                })
        return pairs

    # ── Weight Trajectory ─────────────────────────────────────

    def weight_trajectory(self, pattern: str) -> list[float]:
        """Track how a pattern's weight evolved over cycles."""
        return [
            evo.weight_snapshot.get(pattern, 1.0)
            for evo in self._cycles
        ]

    def convergence(self) -> float:
        """How stable are the weights? 0.0 = volatile, 1.0 = converged.

        Measured by average absolute weight delta in recent cycles.
        Low deltas = weights have stabilized = convergence.
        """
        if len(self._cycles) < 2:
            return 0.0

        recent = self._cycles[-3:]
        all_deltas = []
        for evo in recent:
            all_deltas.extend(abs(d) for d in evo.weight_deltas.values())

        if not all_deltas:
            return 1.0

        avg_delta = sum(all_deltas) / len(all_deltas)
        return max(0.0, min(1.0, 1.0 - avg_delta * 10))

    # ── Introspection ─────────────────────────────────────────

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)

    @property
    def learning_rate(self) -> float:
        return self._lr

    def summary(self) -> dict:
        """Evolution engine vitals."""
        return {
            "cycles": self.cycle_count,
            "learning_rate": round(self._lr, 4),
            "convergence": round(self.convergence(), 3),
            "total_pseudo_labels": sum(len(e.pseudo_labels) for e in self._cycles),
            "total_hard_negatives": sum(len(e.hard_negatives) for e in self._cycles),
            "total_patterns": len(self._pipeline.weights.weights),
            "latest": self._cycles[-1].metrics if self._cycles else {},
        }

    # ── Persistence ───────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        return {
            "version": 1,
            "learning_rate": self._lr,
            "lr_decay": self._lr_decay,
            "min_lr": self._min_lr,
            "initial_top_pct": self._initial_top_pct,
            "top_pct_step": self._top_pct_step,
            "max_top_pct": self._max_top_pct,
            "min_confidence": self._min_confidence,
            "cycles": [
                {
                    "cycle_number": e.cycle_number,
                    "pseudo_count": len(e.pseudo_labels),
                    "hard_neg_count": len(e.hard_negatives),
                    "weight_deltas": e.weight_deltas,
                    "weight_snapshot": e.weight_snapshot,
                    "metrics": e.metrics,
                    "timestamp": e.timestamp,
                    "improved": e.improved,
                }
                for e in self._cycles
            ],
        }

    @classmethod
    def from_dict(cls, data: dict, pipeline: "IRPipeline") -> "EvolutionEngine":
        """Restore from serialized. Bad data = fresh engine."""
        engine = cls(
            pipeline,
            initial_lr=float(data.get("learning_rate", 0.1)),
            lr_decay=float(data.get("lr_decay", 0.8)),
            min_lr=float(data.get("min_lr", 0.01)),
            initial_top_pct=float(data.get("initial_top_pct", 0.4)),
            top_pct_step=float(data.get("top_pct_step", 0.1)),
            max_top_pct=float(data.get("max_top_pct", 0.7)),
            min_confidence=float(data.get("min_confidence", 0.2)),
        )
        try:
            for cd in data.get("cycles", []):
                evo = EvolutionCycle(
                    cycle_number=int(cd.get("cycle_number", 0)),
                    pseudo_labels=[],  # not restored (too large)
                    hard_negatives=[],
                    weight_deltas=dict(cd.get("weight_deltas", {})),
                    weight_snapshot=dict(cd.get("weight_snapshot", {})),
                    metrics=dict(cd.get("metrics", {})),
                    timestamp=float(cd.get("timestamp", time.time())),
                )
                engine._cycles.append(evo)
        except (TypeError, ValueError, KeyError):
            pass
        return engine
