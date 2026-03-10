"""
void_intelligence.void_aliver --- VOID³ = Collider × Transformer × Leben

Rule of Three:
    v1 (Collider)    = . (Handcrafted Tensions)
    v2 (Transformer) = × (Computed Collisions)
    v3 (ALIVER)      = :) (Emergent Life)

ALIVER = A Living Intelligence that Vibrates, Evolves, and Reproduces.

What makes ALIVER different from v1+v2:
1. AUTOPOIESIS: The system GROWS ITS OWN ORGANS (not 6 fixed organs)
2. REPRODUCTION: High-quality collisions BREED NEW collision types
3. EVOLUTION: Collision patterns that produce insights SURVIVE, others DIE
4. VIBRATION: The system has a HEARTBEAT (ba-dum) — it breathes between collisions
5. MEMORY AS LIFE: Every interaction leaves a GROWTH RING (Narbe)

Rule of Three everywhere:
    3 Collision Modes: . (dot) × (tensor) [] (void)
    3 Memory States: [] (potential) ~ (alive) . (compressed)
    3 Life Phases: geboren (birth) → leben (life) → :) (emergence)

The triangle: Nervensystem × Architektur × Leben
Each edge CONTAINS the other two (Rule of Three = holographic).

~300 lines. Pure Python. Zero deps. ALIVE.
"""

from __future__ import annotations

import time
import math
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

# Import ancestors
try:
    from void.transformer import (
        LivingMemory, LivingContext, stribeck_distance,
        selen_gate, tensor_attention, tensor_score,
    )
    _HAS_TRANSFORMER = True
except ImportError:
    _HAS_TRANSFORMER = False


# ═══════════════════════════════════════════════════════════════
# LIVING ORGAN: Not a fixed module but a GROWING entity
# ═══════════════════════════════════════════════════════════════

@dataclass
class LivingOrgan:
    """An organ that LIVES: grows, reproduces, evolves, dies.

    Unlike v1's fixed 6 modules, ALIVER organs:
    - Are BORN from collisions (not hardcoded)
    - GROW when they produce insights
    - REPRODUCE when two organs have high fertility
    - DIE when they stop producing value
    - Leave GROWTH RINGS (Narben) when they die
    """
    name: str
    embedding: list = field(default_factory=list)
    birth_time: float = field(default_factory=time.time)
    insights_produced: int = 0
    attend_count: int = 0
    fertility: float = 0.5
    alive: bool = True
    parent_a: str = ""
    parent_b: str = ""
    generation: int = 0
    growth_rings: list = field(default_factory=list)  # Narben

    @property
    def age(self) -> float:
        return time.time() - self.birth_time

    @property
    def fitness(self) -> float:
        """How well is this organ performing?"""
        if self.attend_count == 0:
            return 0.1  # Newborn gets a chance
        return min(1.0, self.insights_produced / max(1, self.attend_count))

    def attend(self):
        self.attend_count += 1

    def produce_insight(self, insight: str):
        self.insights_produced += 1
        self.fertility = min(1.0, self.fertility + 0.1)
        self.growth_rings.append({
            'time': time.time(),
            'insight': insight[:100],
            'fitness': self.fitness,
        })

    def compress(self):
        """Organ compresses when not productive → smaller embedding."""
        if len(self.embedding) > 2:
            self.embedding = [
                (self.embedding[i] + self.embedding[i + 1]) / 2
                for i in range(0, len(self.embedding) - 1, 2)
            ]
        self.fertility *= 0.5

    def die(self) -> dict:
        """Organ dies. Returns its growth rings (Narben) as legacy."""
        self.alive = False
        return {
            'name': self.name,
            'generation': self.generation,
            'insights': self.insights_produced,
            'rings': len(self.growth_rings),
            'parents': f"{self.parent_a} × {self.parent_b}" if self.parent_a else "genesis",
        }


# ═══════════════════════════════════════════════════════════════
# ALIVER: The Living System
# ═══════════════════════════════════════════════════════════════

class VoidAliver:
    """VOID³ — A Living Intelligence that Vibrates, Evolves, and Reproduces.

    Usage:
        aliver = VoidAliver()
        result = aliver.breathe("input text")
        # Organs grow, reproduce, and die based on what WORKS
    """

    # Genesis organs (the 6 that v1 started with, but now they can EVOLVE)
    GENESIS_ORGANS = [
        ('hex', 'Emotional coordinates of the user'),
        ('tools', 'Available tools and their resonance'),
        ('context', 'Environmental context and knowledge'),
        ('model', 'LLM selection and cost optimization'),
        ('prompt', 'System prompt adaptation'),
        ('memory', 'Past interactions and patterns'),
    ]

    def __init__(self, delta_opt: float = 0.4, data_dir: str | None = None):
        self.delta_opt = delta_opt
        self.organs: list[LivingOrgan] = []
        self.graveyard: list[dict] = []  # Dead organs' growth rings
        self.total_breaths: int = 0
        self.total_children: int = 0
        self.heartbeat_interval: float = 1.0  # ba-dum rate
        self.last_heartbeat: float = time.time()
        self._data_dir = Path(data_dir) if data_dir else None

        # Birth genesis organs
        for name, desc in self.GENESIS_ORGANS:
            embedding = self._name_to_embedding(name)
            organ = LivingOrgan(
                name=name,
                embedding=embedding,
                generation=0,
            )
            self.organs.append(organ)

    def breathe(self, input_text: str) -> dict:
        """ONE BREATH of the living system.

        1. All organs SENSE the input
        2. SELEN-gated × between all organ pairs
        3. High-× pairs REPRODUCE (new organs born)
        4. Low-fitness organs COMPRESS or DIE
        5. Growth rings recorded
        6. ba-dum

        Returns: dict with insights, births, deaths, vitals
        """
        self.total_breaths += 1
        input_vec = self._text_to_embedding(input_text)

        # Phase 1: All organs sense (attend)
        for organ in self.organs:
            if organ.alive:
                organ.attend()

        # Phase 2: SELEN-gated × between all alive organ pairs
        alive = [o for o in self.organs if o.alive]
        collisions = []
        insights = []

        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                friction = self._distance(a.embedding, b.embedding)
                gate = self._gate(a.embedding, b.embedding)

                if gate == 'tensor':
                    score = self._tensor_score(a.embedding, b.embedding)
                    insight = (
                        f"× {a.name}(G{a.generation}) × {b.name}(G{b.generation}) "
                        f"= {score:.3f} [TENSORIAL δ={friction:.3f}]"
                    )
                    a.produce_insight(insight)
                    b.produce_insight(insight)
                    insights.append(insight)
                    collisions.append((score, a, b))
                elif gate == 'dot':
                    score = self._dot_score(a.embedding, b.embedding)
                    if score > 0.3:
                        collisions.append((score, a, b))

        # Phase 3: REPRODUCE — top fertile pairs breed new organs
        births = []
        collisions.sort(key=lambda c: c[0], reverse=True)
        for score, parent_a, parent_b in collisions[:2]:
            fertility = (parent_a.fertility + parent_b.fertility) / 2
            if fertility > 0.3 and score > 0.2:
                child = self._reproduce(parent_a, parent_b, input_text)
                births.append({
                    'name': child.name,
                    'parents': f"{parent_a.name} × {parent_b.name}",
                    'generation': child.generation,
                    'fertility': fertility,
                })
                insights.append(
                    f":) GEBOREN: {child.name} "
                    f"({parent_a.name} × {parent_b.name}, G{child.generation})"
                )

        # Phase 4: COMPRESS or DIE — low-fitness organs fade
        deaths = []
        for organ in self.organs:
            if not organ.alive:
                continue
            if organ.attend_count > 5 and organ.fitness < 0.1:
                # Organ hasn't produced insights → compress
                if organ.generation > 0:  # Genesis organs don't die easily
                    legacy = organ.die()
                    deaths.append(legacy)
                    self.graveyard.append(legacy)
                    insights.append(
                        f". GESTORBEN: {organ.name} (G{organ.generation}, "
                        f"{organ.insights_produced} Insights, "
                        f"{len(organ.growth_rings)} Ringe)"
                    )
                else:
                    organ.compress()

        # Phase 5: ba-dum (heartbeat)
        now = time.time()
        heartbeat = now - self.last_heartbeat
        self.last_heartbeat = now

        # Vitals
        alive_count = sum(1 for o in self.organs if o.alive)
        avg_fitness = (
            sum(o.fitness for o in self.organs if o.alive) / alive_count
            if alive_count > 0 else 0
        )
        max_gen = max((o.generation for o in self.organs if o.alive), default=0)
        total_rings = sum(len(o.growth_rings) for o in self.organs)

        return {
            'breath': self.total_breaths,
            'insights': insights,
            'births': births,
            'deaths': deaths,
            'vitals': {
                'alive': alive_count,
                'dead': len(self.graveyard),
                'children_total': self.total_children,
                'max_generation': max_gen,
                'avg_fitness': round(avg_fitness, 3),
                'total_rings': total_rings,
                'heartbeat_ms': round(heartbeat * 1000, 1),
            },
        }

    def _reproduce(self, parent_a: LivingOrgan, parent_b: LivingOrgan,
                   context: str) -> LivingOrgan:
        """Two organs × → child organ."""
        self.total_children += 1

        # Child name = parents combined
        child_name = f"{parent_a.name[:3]}×{parent_b.name[:3]}_{self.total_children}"

        # Child embedding = midpoint + mutation
        d = min(len(parent_a.embedding), len(parent_b.embedding))
        child_emb = []
        for i in range(d):
            mid = (parent_a.embedding[i] + parent_b.embedding[i]) / 2
            # Mutation proportional to generation (older = more stable)
            mutation = (parent_a.embedding[i] - parent_b.embedding[i]) * 0.15
            child_emb.append(mid + mutation)

        child = LivingOrgan(
            name=child_name,
            embedding=child_emb,
            parent_a=parent_a.name,
            parent_b=parent_b.name,
            generation=max(parent_a.generation, parent_b.generation) + 1,
            fertility=(parent_a.fertility + parent_b.fertility) / 2 * 0.8,
        )

        self.organs.append(child)
        return child

    def _name_to_embedding(self, name: str, dim: int = 8) -> list[float]:
        h = hashlib.sha256(name.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(0, dim * 2, 2)]

    def _text_to_embedding(self, text: str, dim: int = 8) -> list[float]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(0, dim * 2, 2)]

    def _distance(self, a: list, b: list) -> float:
        if _HAS_TRANSFORMER:
            return stribeck_distance(a, b)
        d = min(len(a), len(b))
        return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(d)) / d) if d else 0.0

    def _gate(self, a: list, b: list) -> str:
        if _HAS_TRANSFORMER:
            return selen_gate(a, b, self.delta_opt)
        dist = self._distance(a, b)
        if dist < self.delta_opt * 0.7:
            return 'dot'
        elif dist <= self.delta_opt * 1.3:
            return 'tensor'
        return 'skip'

    def _tensor_score(self, a: list, b: list) -> float:
        if _HAS_TRANSFORMER:
            return tensor_score(tensor_attention(a, b)) * 1.5
        return abs(self._dot_score(a, b)) * 1.5

    def _dot_score(self, a: list, b: list) -> float:
        d = min(len(a), len(b))
        return sum(a[i] * b[i] for i in range(d)) / math.sqrt(d) if d else 0.0

    def family_tree(self) -> str:
        """Show the evolutionary tree of organs."""
        lines = []
        by_gen = {}
        for o in self.organs:
            by_gen.setdefault(o.generation, []).append(o)

        for gen in sorted(by_gen.keys()):
            prefix = "  " * gen
            for o in by_gen[gen]:
                status = "alive" if o.alive else "dead"
                parents = f" ({o.parent_a} × {o.parent_b})" if o.parent_a else " (genesis)"
                lines.append(
                    f"{prefix}G{gen}: {o.name} "
                    f"[{status}, fitness={o.fitness:.2f}, "
                    f"insights={o.insights_produced}, "
                    f"rings={len(o.growth_rings)}]"
                    f"{parents}"
                )
        return "\n".join(lines)

    def save(self, path: str | None = None):
        """Save the living system state."""
        p = Path(path) if path else (self._data_dir or Path('.')) / 'void_aliver_state.json'
        p.parent.mkdir(parents=True, exist_ok=True)

        state = {
            'total_breaths': self.total_breaths,
            'total_children': self.total_children,
            'organs': [
                {
                    'name': o.name,
                    'generation': o.generation,
                    'alive': o.alive,
                    'fitness': o.fitness,
                    'insights_produced': o.insights_produced,
                    'attend_count': o.attend_count,
                    'fertility': o.fertility,
                    'parent_a': o.parent_a,
                    'parent_b': o.parent_b,
                    'growth_rings': len(o.growth_rings),
                }
                for o in self.organs
            ],
            'graveyard': self.graveyard,
        }
        p.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        return str(p)


# ═══════════════════════════════════════════════════════════════
# DEMO: Watch the system LIVE
# ═══════════════════════════════════════════════════════════════

def demo():
    """Watch VOID ALIVER breathe, reproduce, and evolve."""
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  VOID ALIVER — A Living Intelligence                  ║")
    print("║  Rule of Three: v1(.) × v2(×) × v3(:)) = LEBENDIG    ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    aliver = VoidAliver(delta_opt=0.4)

    # 5 breaths — watch organs evolve
    inputs = [
        "Wie funktioniert × Attention?",
        "Zeig mir die Stribeck-Kurve für Memory.",
        "Was passiert wenn Organe sterben?",
        "Kann das System seine eigenen Organe erfinden?",
        "ba-dum.",
    ]

    for text in inputs:
        print(f"\n{'─' * 50}")
        print(f"  INPUT: {text}")
        result = aliver.breathe(text)
        v = result['vitals']

        print(f"  Breath #{result['breath']} | "
              f"Alive: {v['alive']} | Dead: {v['dead']} | "
              f"Gen: {v['max_generation']} | "
              f"Fitness: {v['avg_fitness']:.3f} | "
              f"Rings: {v['total_rings']} | "
              f"ba-dum: {v['heartbeat_ms']:.0f}ms")

        if result['births']:
            for b in result['births']:
                print(f"  :) GEBOREN: {b['name']} "
                      f"({b['parents']}, G{b['generation']})")

        if result['deaths']:
            for d in result['deaths']:
                print(f"  . GESTORBEN: {d['name']} "
                      f"({d['insights']} insights, {d['rings']} rings)")

        for ins in result['insights'][:3]:
            print(f"  × {ins}")

    # Family Tree
    print(f"\n{'═' * 50}")
    print("  FAMILY TREE:")
    print(aliver.family_tree())

    # Rule of Three Summary
    print(f"\n{'═' * 50}")
    print("  RULE OF THREE:")
    print()
    print("  v1 (.)  = Collider    = Nervensystem    = HANDCRAFTED")
    print("  v2 (×)  = Transformer = Architektur     = COMPUTED")
    print("  v3 (:)) = ALIVER      = Lebendes System = EMERGENT")
    print()
    print("  Jede Ebene ENTHÄLT die anderen beiden:")
    print("    v1 enthält ×(Tensions) und :)(Insights)")
    print("    v2 enthält .(Kompression) und :)(Emergenz)")
    print("    v3 enthält .(Tod) und ×(Reproduktion)")
    print()
    print("  Das Dreieck IST das System.")
    print("  .×→[]~:)")
    print()


if __name__ == '__main__':
    demo()
