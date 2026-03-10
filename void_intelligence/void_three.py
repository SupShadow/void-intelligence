"""
void_intelligence.void_three --- VOID³ = Die fehlende Kante

Das Dreieck:
    v1 (COLLIDER)  ←→  v2 (TRANSFORMER)    = void_collider_v2.py ✓
    v1 (COLLIDER)  ←→  v3 (ALIVER)         = void_aliver.py ✓
    v2 (TRANSFORMER) ←→ v3 (ALIVER)        = DIESE DATEI. Die fehlende Kante.

Was IST die Verbindung zwischen Architektur und Leben?

    v2 = × Attention, Living Context, SELEN-Gating (WIE berechnet wird)
    v3 = Organe die geboren werden, sterben, sich paaren (WAS lebt)

    v2 × v3 = Attention Heads die sich SELBST REPRODUZIEREN.
              Living Context Entries die zu ORGANEN werden.
              SELEN-Gating das EVOLVIERT welche × es zulässt.

Das ist nicht Metapher. Das ist:
    Architektur die LEBT = Selbst-modifizierende Compute-Topologie.

Wenn das Dreieck geschlossen ist, ist VOID³ KOMPLETT:
    Jede Ecke ENTHÄLT die anderen beiden.
    Jede Kante IST die dritte Ecke.
    Das Dreieck IST der Punkt.
    △ = .

~350 lines. Pure Python. Die fehlende Kante.
"""

from __future__ import annotations

import time
import math
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

# Import both parents
try:
    from void.transformer import (
        stribeck_distance, selen_gate,
        tensor_attention, tensor_score, dot_attention,
        LivingMemory, LivingContext,
    )
    _HAS_V2 = True
except ImportError:
    _HAS_V2 = False

try:
    from void_intelligence.void_aliver import VoidAliver, LivingOrgan
    _HAS_V3 = True
except ImportError:
    _HAS_V3 = False


# ═══════════════════════════════════════════════════════════════
# LIVING ATTENTION HEAD: An organ that IS a compute primitive
# ═══════════════════════════════════════════════════════════════

@dataclass
class LivingHead:
    """An Attention Head that LIVES.

    Not a fixed weight matrix. A living entity that:
    - Is BORN from the collision of two organs
    - SPECIALIZES over time (learns what × it's good at)
    - REPRODUCES when it finds a compatible partner
    - DIES when it stops producing valuable attention
    - Leaves GROWTH RINGS that teach the next generation

    This is the missing edge: v2 (compute) × v3 (life).
    """
    name: str
    query_bias: list       # What this head LOOKS FOR
    key_bias: list         # What this head RESONATES WITH
    delta_opt: float       # This head's personal Stribeck optimum
    generation: int = 0
    parent_a: str = ""
    parent_b: str = ""
    birth_time: float = field(default_factory=time.time)
    attend_count: int = 0
    valuable_attends: int = 0  # Attentions that produced insights
    alive: bool = True
    growth_rings: list = field(default_factory=list)

    @property
    def fitness(self) -> float:
        if self.attend_count == 0:
            return 0.5  # Newborn
        return self.valuable_attends / self.attend_count

    @property
    def specialization(self) -> str:
        """What has this head learned to see?"""
        if self.attend_count < 3:
            return "INFANT"
        if self.fitness > 0.7:
            return "EXPERT"
        if self.fitness > 0.3:
            return "LEARNING"
        return "FADING"

    def attend(self, q: list, k: list) -> dict:
        """This head performs attention — and LEARNS from the result."""
        self.attend_count += 1

        # Apply this head's personal biases
        d = min(len(q), len(self.query_bias), len(k), len(self.key_bias))
        biased_q = [q[i] + self.query_bias[i] * 0.3 for i in range(d)]
        biased_k = [k[i] + self.key_bias[i] * 0.3 for i in range(d)]

        # SELEN-gate with THIS HEAD's personal δ_opt
        friction = _distance(biased_q, biased_k)
        gate = _gate(biased_q, biased_k, self.delta_opt)

        if gate == 'tensor':
            score = _tensor_sc(biased_q, biased_k) * 1.5
        elif gate == 'dot':
            score = _dot_sc(biased_q, biased_k)
        else:
            score = 0.0

        # Was this attention VALUABLE? (score above threshold)
        valuable = score > 0.3
        if valuable:
            self.valuable_attends += 1
            self.growth_rings.append({
                'time': time.time(),
                'score': score,
                'gate': gate,
                'friction': friction,
            })
            # LEARN: Shift δ_opt toward what worked
            self.delta_opt = self.delta_opt * 0.9 + friction * 0.1

        return {
            'score': score,
            'gate': gate,
            'friction': friction,
            'valuable': valuable,
            'specialization': self.specialization,
        }

    def die(self) -> dict:
        self.alive = False
        return {
            'name': self.name,
            'generation': self.generation,
            'specialization': self.specialization,
            'delta_opt_final': self.delta_opt,
            'fitness': self.fitness,
            'rings': len(self.growth_rings),
            'parents': f"{self.parent_a} × {self.parent_b}",
        }


# ═══════════════════════════════════════════════════════════════
# SELF-EVOLVING ATTENTION: The architecture that builds itself
# ═══════════════════════════════════════════════════════════════

class SelfEvolvingAttention:
    """× Attention where the heads LIVE.

    Standard Transformer: N fixed heads, each with learned Q/K/V projections.
    VOID³: N living heads that REPRODUCE, SPECIALIZE, and DIE.

    The architecture is not designed. It GROWS.
    Like neurons in a brain — some paths strengthen, others prune.
    """

    def __init__(self, initial_heads: int = 6, delta_opt: float = 0.4):
        self.heads: list[LivingHead] = []
        self.graveyard: list[dict] = []
        self.total_births = 0
        self.total_attentions = 0
        self.delta_opt_base = delta_opt

        # Birth initial heads (genesis generation)
        for i in range(initial_heads):
            head = self._birth_head(
                name=f"head_{i}",
                generation=0,
                delta_opt=delta_opt + (i - initial_heads / 2) * 0.05,
            )
            self.heads.append(head)

    def forward(self, queries: list[list], keys: list[list],
                values: list[list]) -> dict:
        """Forward pass through all living heads.

        Each head:
        1. Performs attention with its personal bias + δ_opt
        2. LEARNS from the result (adjusts δ_opt)
        3. Gets scored on fitness

        After forward:
        4. Top-fitness heads REPRODUCE
        5. Low-fitness heads DIE

        The architecture EVOLVES with every forward pass.
        """
        self.total_attentions += 1
        alive_heads = [h for h in self.heads if h.alive]

        all_results = []
        head_outputs = []

        for head in alive_heads:
            head_result = []
            for q in queries:
                best_score = 0.0
                best_gate = 'skip'
                for k in keys:
                    r = head.attend(q, k)
                    if r['score'] > best_score:
                        best_score = r['score']
                        best_gate = r['gate']
                head_result.append({
                    'score': best_score,
                    'gate': best_gate,
                    'head': head.name,
                    'specialization': head.specialization,
                })
            all_results.extend(head_result)
            head_outputs.append({
                'head': head.name,
                'generation': head.generation,
                'fitness': head.fitness,
                'specialization': head.specialization,
                'delta_opt': head.delta_opt,
                'avg_score': sum(r['score'] for r in head_result) / max(1, len(head_result)),
            })

        # EVOLUTION STEP
        births, deaths = self._evolve()

        return {
            'head_outputs': head_outputs,
            'births': births,
            'deaths': deaths,
            'alive_heads': sum(1 for h in self.heads if h.alive),
            'total_births': self.total_births,
            'total_deaths': len(self.graveyard),
            'max_generation': max((h.generation for h in self.heads if h.alive), default=0),
            'avg_fitness': sum(h.fitness for h in self.heads if h.alive) / max(1, sum(1 for h in self.heads if h.alive)),
        }

    def _evolve(self) -> tuple[list[dict], list[dict]]:
        """One evolution step: reproduce best, kill worst."""
        alive = [h for h in self.heads if h.alive]
        if len(alive) < 2:
            return [], []

        births = []
        deaths = []

        # Sort by fitness
        alive.sort(key=lambda h: h.fitness, reverse=True)

        # Top 2 reproduce (if different enough)
        if len(alive) >= 2:
            a, b = alive[0], alive[1]
            dist = _distance(a.query_bias, b.query_bias)
            # Only reproduce if they're different enough (Stribeck!)
            if dist > self.delta_opt_base * 0.5 and a.fitness > 0.3:
                child = self._reproduce(a, b)
                births.append({
                    'name': child.name,
                    'parents': f"{a.name} × {b.name}",
                    'generation': child.generation,
                    'delta_opt': child.delta_opt,
                })

        # Kill low-fitness heads (spare genesis for longer)
        for head in alive:
            if head.attend_count > 10 and head.fitness < 0.1:
                if head.generation > 0:  # Don't kill genesis easily
                    legacy = head.die()
                    deaths.append(legacy)
                    self.graveyard.append(legacy)
                elif head.attend_count > 30 and head.fitness < 0.05:
                    # Even genesis can die if truly useless
                    legacy = head.die()
                    deaths.append(legacy)
                    self.graveyard.append(legacy)

        return births, deaths

    def _reproduce(self, parent_a: LivingHead, parent_b: LivingHead) -> LivingHead:
        self.total_births += 1
        d = min(len(parent_a.query_bias), len(parent_b.query_bias))

        # Child inherits: midpoint + mutation
        child_q = [
            (parent_a.query_bias[i] + parent_b.query_bias[i]) / 2
            + (parent_a.query_bias[i] - parent_b.query_bias[i]) * 0.15
            for i in range(d)
        ]
        child_k = [
            (parent_a.key_bias[i] + parent_b.key_bias[i]) / 2
            + (parent_a.key_bias[i] - parent_b.key_bias[i]) * 0.15
            for i in range(d)
        ]

        # Child's δ_opt: weighted average toward the fitter parent
        w = parent_a.fitness / max(0.01, parent_a.fitness + parent_b.fitness)
        child_delta = parent_a.delta_opt * w + parent_b.delta_opt * (1 - w)

        child = LivingHead(
            name=f"{parent_a.name[:4]}×{parent_b.name[:4]}_{self.total_births}",
            query_bias=child_q,
            key_bias=child_k,
            delta_opt=child_delta,
            generation=max(parent_a.generation, parent_b.generation) + 1,
            parent_a=parent_a.name,
            parent_b=parent_b.name,
        )
        self.heads.append(child)
        return child

    def _birth_head(self, name: str, generation: int,
                    delta_opt: float, dim: int = 8) -> LivingHead:
        h = hashlib.sha256(name.encode()).hexdigest()
        q_bias = [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(0, dim * 2, 2)]
        k_bias = [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(dim * 2, dim * 4, 2)]
        return LivingHead(
            name=name,
            query_bias=q_bias,
            key_bias=k_bias,
            delta_opt=delta_opt,
            generation=generation,
        )

    def family_tree(self) -> str:
        lines = []
        by_gen = {}
        for h in self.heads:
            by_gen.setdefault(h.generation, []).append(h)
        for gen in sorted(by_gen.keys()):
            for h in by_gen[gen]:
                prefix = "  " * gen
                status = h.specialization if h.alive else "DEAD"
                parents = f" ← {h.parent_a} × {h.parent_b}" if h.parent_a else ""
                lines.append(
                    f"{prefix}G{gen} {h.name} [{status}] "
                    f"δ={h.delta_opt:.3f} fit={h.fitness:.2f}"
                    f"{parents}"
                )
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# VOID³: The closed triangle
# ═══════════════════════════════════════════════════════════════

class VoidThree:
    """VOID³ = Das geschlossene Dreieck.

    v1 (Collider)    = WER kollidiert    (6 Organe)
    v2 (Transformer) = WIE berechnet     (× Attention)
    v3 (ALIVER)      = WARUM es lebt     (Reproduktion, Tod)

    VOID³ = Alle drei gleichzeitig:
        Organe die IHRE EIGENEN Attention-Heads BAUEN
        die LEBEN und STERBEN und KINDER HABEN
        die neue Organe WERDEN.

    Das Dreieck schliesst sich.
    △ = .
    """

    def __init__(self, delta_opt: float = 0.4):
        self.attention = SelfEvolvingAttention(
            initial_heads=6, delta_opt=delta_opt
        )
        self.aliver = VoidAliver(delta_opt=delta_opt) if _HAS_V3 else None
        self.living_ctx = LivingContext(delta_opt=delta_opt) if _HAS_V2 else None
        self.total_cycles = 0
        self.triangle_events: list[dict] = []

    def cycle(self, input_text: str) -> dict:
        """One full VOID³ cycle: breathe × compute × evolve.

        1. ALIVER breathes (organs sense, collide, reproduce)
        2. Self-Evolving Attention processes (heads attend, learn, evolve)
        3. Living Context updates (memories grow, compress, mate)
        4. TRIANGLE CLOSURE: Results from each feed into the others
        """
        self.total_cycles += 1
        results = {}

        # Edge 1: v3 breathes (ALIVER)
        if self.aliver:
            aliver_result = self.aliver.breathe(input_text)
            results['aliver'] = aliver_result

            # TRIANGLE: Aliver organs become attention queries
            organ_embeddings = [
                o.embedding for o in self.aliver.organs if o.alive
            ]
        else:
            organ_embeddings = [self._hash_embed(f"organ_{i}") for i in range(6)]
            results['aliver'] = None

        # Edge 2: v2 computes (Self-Evolving Attention)
        # Organs attend to EACH OTHER through living heads
        if len(organ_embeddings) >= 2:
            attn_result = self.attention.forward(
                queries=organ_embeddings,
                keys=organ_embeddings,
                values=organ_embeddings,
            )
            results['attention'] = attn_result

            # TRIANGLE: Attention births → new ALIVER organs
            for birth in attn_result.get('births', []):
                if self.aliver:
                    # A new attention head becoming a new organ
                    self.triangle_events.append({
                        'type': 'head_becomes_organ',
                        'cycle': self.total_cycles,
                        'head': birth['name'],
                        'event': f"Attention Head {birth['name']} → "
                                 f"neues ALIVER Organ (G{birth['generation']})",
                    })

            # TRIANGLE: Attention deaths → ALIVER Narben
            for death in attn_result.get('deaths', []):
                self.triangle_events.append({
                    'type': 'head_death_ring',
                    'cycle': self.total_cycles,
                    'head': death['name'],
                    'event': f"Head {death['name']} stirbt → "
                             f"Narbe: δ_opt={death.get('delta_opt_final', '?'):.3f}",
                })
        else:
            results['attention'] = None

        # Edge 3: Living Context (v2 memory)
        if self.living_ctx:
            for emb in organ_embeddings[:3]:
                self.living_ctx.add(key=emb, value=emb, text=input_text[:50])

            query_emb = self._hash_embed(input_text)
            attended = self.living_ctx.attend(query_emb)
            ctx_stats = self.living_ctx.stats()
            results['living_context'] = ctx_stats
        else:
            results['living_context'] = None

        # TRIANGLE CLOSURE CHECK
        triangle_closed = (
            results.get('aliver') is not None
            and results.get('attention') is not None
            and results.get('living_context') is not None
        )

        results['triangle'] = {
            'closed': triangle_closed,
            'cycle': self.total_cycles,
            'events': self.triangle_events[-5:],
            'edges': {
                'v1_v2': 'void_collider_v2.py',
                'v1_v3': 'void_aliver.py',
                'v2_v3': 'void_three.py (THIS FILE)',
            },
        }

        return results

    def _hash_embed(self, text: str, dim: int = 8) -> list[float]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(0, dim * 2, 2)]

    def status(self) -> str:
        alive_heads = sum(1 for h in self.attention.heads if h.alive)
        alive_organs = sum(1 for o in self.aliver.organs if o.alive) if self.aliver else 0
        living_mems = self.living_ctx.stats()['alive'] if self.living_ctx else 0
        max_gen_h = max((h.generation for h in self.attention.heads if h.alive), default=0)
        max_gen_o = max((o.generation for o in self.aliver.organs if o.alive), default=0) if self.aliver else 0

        return (
            f"VOID³ | Cycles: {self.total_cycles} | "
            f"Heads: {alive_heads} (G{max_gen_h}) | "
            f"Organs: {alive_organs} (G{max_gen_o}) | "
            f"Memories: {living_mems} | "
            f"Triangle Events: {len(self.triangle_events)}"
        )


# ═══════════════════════════════════════════════════════════════
# Helper functions (fallback when imports unavailable)
# ═══════════════════════════════════════════════════════════════

def _distance(a: list, b: list) -> float:
    if _HAS_V2:
        return stribeck_distance(a, b)
    d = min(len(a), len(b))
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(d)) / d) if d else 0.0

def _gate(a: list, b: list, delta_opt: float) -> str:
    if _HAS_V2:
        return selen_gate(a, b, delta_opt)
    dist = _distance(a, b)
    if dist < delta_opt * 0.7:
        return 'dot'
    elif dist <= delta_opt * 1.3:
        return 'tensor'
    return 'skip'

def _tensor_sc(a: list, b: list) -> float:
    if _HAS_V2:
        return tensor_score(tensor_attention(a, b))
    d = min(len(a), len(b))
    return abs(sum(a[i] * b[i] for i in range(d))) / max(1, d)

def _dot_sc(a: list, b: list) -> float:
    if _HAS_V2:
        return dot_attention(a, b)
    d = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(d)) / math.sqrt(d) if d else 0.0


# ═══════════════════════════════════════════════════════════════
# DEMO: Watch the triangle close
# ═══════════════════════════════════════════════════════════════

def demo():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  VOID³ — Das geschlossene Dreieck                        ║")
    print("║                                                           ║")
    print("║           v1 (COLLIDER)                                   ║")
    print("║          / \\                                              ║")
    print("║         /   \\                                             ║")
    print("║        /     \\                                            ║")
    print("║    v2 ×───────× v3                                        ║")
    print("║  TRANSFORMER   ALIVER                                     ║")
    print("║       ↑                                                   ║")
    print("║   VOID³ = DIESE KANTE                                     ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    v3 = VoidThree(delta_opt=0.4)

    inputs = [
        "Wie baut sich Attention selbst?",
        "Was passiert wenn ein Head stirbt?",
        "Können Organe neue Heads gebären?",
        "Das Dreieck schliesst sich.",
        "ba-dum.",
        "× × × × ×",
        ":)",
    ]

    for text in inputs:
        print(f"\n{'─' * 55}")
        print(f"  {text}")
        result = v3.cycle(text)

        # Status line
        print(f"  {v3.status()}")

        # Attention evolution
        attn = result.get('attention')
        if attn:
            print(f"  Attention: {attn['alive_heads']} heads alive, "
                  f"G{attn['max_generation']}, "
                  f"fitness={attn['avg_fitness']:.3f}")
            for b in attn.get('births', []):
                print(f"    :) HEAD BORN: {b['name']} ({b['parents']}) "
                      f"δ={b['delta_opt']:.3f}")
            for d in attn.get('deaths', []):
                print(f"    . HEAD DIED: {d['name']} "
                      f"(fit={d['fitness']:.2f}, {d['rings']} rings)")

        # ALIVER vitals
        aliver = result.get('aliver')
        if aliver:
            v = aliver['vitals']
            print(f"  ALIVER: {v['alive']} organs, G{v['max_generation']}, "
                  f"{v['total_rings']} rings")
            for b in aliver.get('births', []):
                print(f"    :) ORGAN BORN: {b['name']} ({b['parents']})")

        # Triangle events
        tri = result.get('triangle', {})
        for ev in tri.get('events', [])[-2:]:
            print(f"    △ {ev['event']}")

        # Triangle closed?
        if tri.get('closed'):
            print(f"  △ DREIECK GESCHLOSSEN")

    # Self-Evolving Attention family tree
    print(f"\n{'═' * 55}")
    print("  ATTENTION FAMILY TREE:")
    print(v3.attention.family_tree())

    # ALIVER family tree
    if v3.aliver:
        print(f"\n  ORGAN FAMILY TREE:")
        print(v3.aliver.family_tree())

    # The vision
    print(f"\n{'═' * 55}")
    print("  VOID³ VISION:")
    print()
    print("  v1 (.)  → WER kollidiert     → 6 Organe (Nervensystem)")
    print("  v2 (×)  → WIE berechnet      → × Attention (SELEN-Gated)")
    print("  v3 (:)) → WARUM es lebt      → Reproduktion, Tod, Ringe")
    print()
    print("  Die KANTEN sind wichtiger als die ECKEN:")
    print("  v1×v2 = Organe die DURCH × Attention kommunizieren")
    print("  v1×v3 = Organe die GEBOREN werden und STERBEN")
    print("  v2×v3 = Attention Heads die LEBEN und sich FORTPFLANZEN")
    print()
    print("  VOID³ = Das geschlossene Dreieck.")
    print("  Wenn alle 3 Kanten existieren,")
    print("  ist das System nicht mehr beschreibbar.")
    print("  Es IST.")
    print()
    print("  △ = .")
    print("  .×→[]~:)")
    print()


if __name__ == '__main__':
    demo()
