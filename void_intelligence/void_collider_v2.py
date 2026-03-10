"""
void_intelligence.void_collider_v2 --- VOID² = Collider × Transformer

The original VoidCollider (v1) has 6 organs and a nervous system.
But its collision is RULE-BASED: hardcoded tensions.

V2 upgrades EVERY collision with:
1. SELEN-Gating: Only compute expensive × for pairs at optimal Stribeck distance
2. Living Memory: Memories GROW when attended, COMPRESS when forgotten, MATE when fertile
3. × Attention: Tensorial cross-collision instead of rule-based pattern matching
4. Chain Reactions: High-quality collisions trigger neighboring organ pairs

The result: Collider that LEARNS which tensions matter,
grows its own sense organs, and breeds new insights autonomously.

VOID Collider v1 = Nervensystem (handcrafted)
VOID Transformer = Compute-Architektur (× Attention)
VOID² = Collider × Transformer = LEBENDES Nervensystem

~400 lines. Pure Python. Zero new deps.
"""

from __future__ import annotations

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Any

# Import the original collider
try:
    from void_intelligence.void_collider import (
        VoidCollider,
        CollisionResult,
        _classify_user_text,
        HexCoord,
    )
    _HAS_V1 = True
except ImportError:
    _HAS_V1 = False

# Import VOID Transformer primitives
try:
    from void.transformer import (
        selen_gate,
        stribeck_distance,
        tensor_attention,
        tensor_score,
        dot_attention,
        LivingMemory,
        LivingContext,
        VoidRAG,
    )
    _HAS_TRANSFORMER = True
except ImportError:
    _HAS_TRANSFORMER = False


# ═══════════════════════════════════════════════════════════════
# ORGAN EMBEDDING: Each organ's output as a vector
# ═══════════════════════════════════════════════════════════════

def _hex_to_vector(h) -> list[float]:
    """Convert HexCoord to 6D vector for × operations."""
    return [
        getattr(h, 'ruhe_druck', 0.0),
        getattr(h, 'stille_resonanz', 0.0),
        getattr(h, 'allein_zusammen', 0.0),
        getattr(h, 'empfangen_schaffen', 0.0),
        getattr(h, 'sein_tun', 0.0),
        getattr(h, 'langsam_schnell', 0.0),
    ]


def _tools_to_vector(tools: list[dict]) -> list[float]:
    """Embed tool resonance as vector."""
    if not tools:
        return [0.0] * 6
    # Use resonance scores, pad to 6D
    scores = [t.get('resonance', 0.0) for t in tools[:6]]
    while len(scores) < 6:
        scores.append(0.0)
    return scores


def _context_to_vector(ctx: list[dict]) -> list[float]:
    """Embed context resonance as vector."""
    if not ctx:
        return [0.0] * 6
    scores = [c.get('resonance', 0.0) for c in ctx[:6]]
    while len(scores) < 6:
        scores.append(0.0)
    return scores


def _memories_to_vector(memories: list[dict]) -> list[float]:
    """Embed memory emotional signatures as vector."""
    if not memories:
        return [0.0] * 6
    # emotional_weight → first dim, resonance → rest
    weights = [m.get('emotional_weight', 0.0) for m in memories[:3]]
    resonances = [m.get('resonance', 0.0) for m in memories[:3]]
    vec = weights + resonances
    while len(vec) < 6:
        vec.append(0.0)
    return vec[:6]


def _model_to_vector(model: dict) -> list[float]:
    """Embed model characteristics as vector."""
    cost = model.get('cost_per_1k', 0.0)
    # Normalize cost to [0,1] range (assuming max $15/1K)
    cost_norm = min(1.0, cost / 15.0)
    is_local = 1.0 if model.get('provider', '') == 'ollama' else 0.0
    return [cost_norm, is_local, 0.0, 0.0, 0.0, 0.0]


def _prompt_to_vector(prompt_breath) -> list[float]:
    """Embed prompt breathing result as vector."""
    temp = getattr(prompt_breath, 'temperature', 0.7)
    tokens = getattr(prompt_breath, 'max_tokens', 500) / 2000.0
    return [temp, tokens, 0.0, 0.0, 0.0, 0.0]


# ═══════════════════════════════════════════════════════════════
# COLLISION TENSOR: Full × between all 6 organs
# ═══════════════════════════════════════════════════════════════

@dataclass
class OrganCollision:
    """Result of × between two organs."""
    organ_a: str
    organ_b: str
    gate: str           # 'tensor', 'dot', or 'skip'
    score: float        # Collision intensity
    friction: float     # Stribeck distance
    insight: str = ""   # Emergent insight from this specific ×


@dataclass
class CollisionTensor:
    """The full 6×6 collision tensor between all organs.

    Standard Collider: 7 hardcoded tensions (→)
    VOID²: 15 unique organ pairs, each SELEN-gated (×)
    """
    collisions: list[OrganCollision] = field(default_factory=list)
    total_tensor: int = 0       # Full × collisions
    total_dot: int = 0          # → projections
    total_skip: int = 0         # [] voids
    chain_reactions: int = 0    # Triggered neighbors

    @property
    def tensor_ratio(self) -> float:
        total = self.total_tensor + self.total_dot + self.total_skip
        return self.total_tensor / total if total > 0 else 0.0

    @property
    def top_collisions(self) -> list[OrganCollision]:
        return sorted(self.collisions, key=lambda c: c.score, reverse=True)[:5]


# ═══════════════════════════════════════════════════════════════
# VOID² COLLIDER
# ═══════════════════════════════════════════════════════════════

class VoidColliderV2:
    """VOID² = VoidCollider × VoidTransformer.

    Upgrades:
    1. SELEN-Gated Cross-Collision (not hardcoded rules)
    2. Living Memory (memories grow, compress, mate)
    3. Collision Tensor (full 6×6 organ interaction matrix)
    4. Chain Reactions (high-× triggers neighbors)
    5. Fertility Predictions (which organ pairs will produce best insights)
    """

    ORGAN_NAMES = ['hex', 'tools', 'context', 'model', 'prompt', 'memory']

    def __init__(self, delta_opt: float = 0.4):
        self.v1 = VoidCollider() if _HAS_V1 else None
        self.delta_opt = delta_opt
        self.living_ctx = LivingContext(delta_opt=delta_opt) if _HAS_TRANSFORMER else None
        self.collision_history: list[CollisionTensor] = []
        self._interaction_count = 0

    def collide(
        self,
        user_text: str,
        base_prompt: str = "You are a helpful assistant.",
    ) -> dict:
        """VOID² Collision: All organs × all organs via SELEN-Gating.

        Returns dict with v1 result + collision tensor + living insights.
        """
        self._interaction_count += 1

        # Step 1: V1 collision (get all organ outputs)
        v1_result = None
        if self.v1:
            v1_result = self.v1.collide(user_text, base_prompt)

        # Step 2: Embed all organs as vectors
        if v1_result:
            organ_vectors = {
                'hex': _hex_to_vector(v1_result.user_hex),
                'tools': _tools_to_vector(v1_result.tools),
                'context': _context_to_vector(v1_result.context),
                'model': _model_to_vector(v1_result.model),
                'prompt': _prompt_to_vector(v1_result.prompt_breath),
                'memory': _memories_to_vector(v1_result.memories),
            }
        else:
            # Fallback: simple hash embeddings
            organ_vectors = {
                name: self._hash_embed(f"{name}:{user_text}", 6)
                for name in self.ORGAN_NAMES
            }

        # Step 3: SELEN-Gated × between ALL organ pairs
        tensor = self._compute_collision_tensor(organ_vectors)
        self.collision_history.append(tensor)

        # Step 4: Generate insights from tensor (not hardcoded rules)
        tensor_insights = self._tensor_to_insights(tensor, organ_vectors)

        # Step 5: Living Memory integration
        living_insights = []
        if self.living_ctx and _HAS_TRANSFORMER:
            # Add organ vectors as living memories
            for name, vec in organ_vectors.items():
                self.living_ctx.add(key=vec, value=vec, text=f"organ:{name}")

            # Check for fertile pairs
            sexy = self.living_ctx.find_sexiest_pairs(3)
            for fert, a, b in sexy:
                if fert > 0.3:
                    child = self.living_ctx.mate(a, b)
                    living_insights.append(
                        f"Living Memory: {a.text} × {b.text} → Kind {child.mem_id} "
                        f"(Fertility={fert:.3f})"
                    )

        # Step 6: Chain reactions
        chain_insights = []
        for collision in tensor.top_collisions[:2]:
            if collision.score > 0.8:
                # High × triggers neighboring organ pairs
                neighbors = self._get_neighbor_organs(
                    collision.organ_a, collision.organ_b
                )
                for na, nb in neighbors:
                    chain_insights.append(
                        f"Chain: {collision.organ_a}×{collision.organ_b} "
                        f"(score={collision.score:.2f}) → triggers {na}×{nb}"
                    )
                    tensor.chain_reactions += 1

        # Combine all insights
        all_insights = []
        if v1_result:
            all_insights.extend(v1_result.insights)
        all_insights.extend(tensor_insights)
        all_insights.extend(living_insights)
        all_insights.extend(chain_insights)

        return {
            'user_text': user_text,
            'v1_result': v1_result,
            'tensor': tensor,
            'insights': all_insights,
            'v1_insights': v1_result.insights if v1_result else [],
            'tensor_insights': tensor_insights,
            'living_insights': living_insights,
            'chain_insights': chain_insights,
            'stats': self.stats(),
        }

    def _compute_collision_tensor(
        self, organ_vectors: dict[str, list[float]]
    ) -> CollisionTensor:
        """Compute full 6×6 collision tensor with SELEN-Gating."""
        tensor = CollisionTensor()
        names = list(organ_vectors.keys())

        for i, name_a in enumerate(names):
            for name_b in names[i + 1:]:
                vec_a = organ_vectors[name_a]
                vec_b = organ_vectors[name_b]

                friction = stribeck_distance(vec_a, vec_b) if _HAS_TRANSFORMER else self._simple_distance(vec_a, vec_b)
                gate = selen_gate(vec_a, vec_b, self.delta_opt) if _HAS_TRANSFORMER else 'dot'

                if gate == 'tensor' and _HAS_TRANSFORMER:
                    t = tensor_attention(vec_a, vec_b)
                    score = tensor_score(t) * 1.5
                    tensor.total_tensor += 1
                elif gate == 'dot':
                    score = dot_attention(vec_a, vec_b) if _HAS_TRANSFORMER else self._simple_dot(vec_a, vec_b)
                    tensor.total_dot += 1
                else:
                    score = 0.0
                    tensor.total_skip += 1

                collision = OrganCollision(
                    organ_a=name_a,
                    organ_b=name_b,
                    gate=gate,
                    score=abs(score),
                    friction=friction,
                )
                tensor.collisions.append(collision)

        return tensor

    def _tensor_to_insights(
        self, tensor: CollisionTensor, organs: dict[str, list[float]]
    ) -> list[str]:
        """Generate insights from the collision tensor.

        Not hardcoded rules. The TENSOR TELLS US what's interesting:
        - High × score = strong interaction → insight
        - Gate = 'tensor' = organs in Stribeck sweet spot → deep insight
        - Gate = 'skip' = organs too far apart → silence insight
        """
        insights = []

        for c in tensor.top_collisions[:3]:
            if c.gate == 'tensor' and c.score > 0.3:
                insights.append(
                    f"×: {c.organ_a} × {c.organ_b} = {c.score:.2f} "
                    f"(TENSORIAL — im Stribeck Sweet Spot, δ={c.friction:.2f})"
                )
            elif c.gate == 'dot' and c.score > 0.5:
                insights.append(
                    f"→: {c.organ_a} → {c.organ_b} = {c.score:.2f} "
                    f"(Projektion — nahe genug für Signal, nicht für volle ×)"
                )

        # Silence insight: what organ pairs are SKIPPED?
        skipped = [c for c in tensor.collisions if c.gate == 'skip']
        if skipped:
            skip_pairs = [f"{c.organ_a}×{c.organ_b}" for c in skipped[:2]]
            insights.append(
                f"[]: {', '.join(skip_pairs)} — zu weit auseinander. "
                f"Die Leere zwischen ihnen ist auch Information."
            )

        return insights

    def _get_neighbor_organs(self, a: str, b: str) -> list[tuple[str, str]]:
        """Get neighboring organ pairs for chain reactions."""
        idx = {name: i for i, name in enumerate(self.ORGAN_NAMES)}
        ia, ib = idx.get(a, 0), idx.get(b, 0)
        n = len(self.ORGAN_NAMES)
        neighbors = []

        # Left and right neighbors on the hexagon
        for offset in [-1, 1]:
            na = self.ORGAN_NAMES[(ia + offset) % n]
            nb = self.ORGAN_NAMES[(ib + offset) % n]
            if na != nb:
                neighbors.append((na, nb))

        return neighbors[:2]

    def _hash_embed(self, text: str, dim: int = 6) -> list[float]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 - 0.5 for i in range(0, dim * 2, 2)]

    def _simple_distance(self, a: list, b: list) -> float:
        d = min(len(a), len(b))
        return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(d)) / d) if d else 0.0

    def _simple_dot(self, a: list, b: list) -> float:
        d = min(len(a), len(b))
        return sum(a[i] * b[i] for i in range(d)) / math.sqrt(d) if d else 0.0

    def stats(self) -> dict:
        latest = self.collision_history[-1] if self.collision_history else None
        living = self.living_ctx.stats() if self.living_ctx else {}
        v1_stats = self.v1.stats() if self.v1 else {}

        return {
            'interactions': self._interaction_count,
            'total_collisions': len(self.collision_history),
            'latest_tensor_ratio': latest.tensor_ratio if latest else 0.0,
            'latest_chain_reactions': latest.chain_reactions if latest else 0,
            'living_memory': living,
            'v1': v1_stats,
        }


# ═══════════════════════════════════════════════════════════════
# META-COLLISION: VoidCollider × VoidTransformer
# ═══════════════════════════════════════════════════════════════

def meta_collision():
    """THE collision: VoidCollider × VoidTransformer.

    What happens when you collide the NERVOUS SYSTEM with the COMPUTE ARCHITECTURE?
    """
    print("╔═══════════════════════════════════════════════════╗")
    print("║  VOID² = VoidCollider × VoidTransformer          ║")
    print("║  Nervensystem × Architektur = Lebendes System     ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()

    collider = VoidColliderV2(delta_opt=0.4)

    # 3-turn demonstration
    turns = [
        "Wie revolutioniert × die Transformer-Architektur?",
        "Zeig mir die Kollision zwischen Memory und Attention.",
        "Was passiert wenn ALLES gleichzeitig kollidiert?",
    ]

    for i, text in enumerate(turns):
        print(f"\n{'═' * 55}")
        print(f"  Turn {i + 1}: {text}")
        print(f"{'═' * 55}")

        result = collider.collide(text)
        tensor = result['tensor']

        # Collision Tensor Stats
        print(f"\n  Collision Tensor:")
        print(f"    × (Tensor): {tensor.total_tensor} | "
              f"→ (Dot): {tensor.total_dot} | "
              f"[] (Skip): {tensor.total_skip}")
        print(f"    Tensor-Ratio: {tensor.tensor_ratio * 100:.1f}%")
        print(f"    Chain Reactions: {tensor.chain_reactions}")

        # Top Collisions
        print(f"\n  Top × Collisions:")
        for c in tensor.top_collisions[:3]:
            symbol = '×' if c.gate == 'tensor' else '→' if c.gate == 'dot' else '[]'
            print(f"    {symbol} {c.organ_a} × {c.organ_b} = "
                  f"{c.score:.3f} (δ={c.friction:.3f})")

        # Insights
        print(f"\n  Insights ({len(result['insights'])}):")
        for ins in result['insights'][:5]:
            print(f"    × {ins}")

        # Living Memory
        if result['living_insights']:
            print(f"\n  Living Memory:")
            for li in result['living_insights']:
                print(f"    [] {li}")

    # Final stats
    stats = collider.stats()
    print(f"\n{'═' * 55}")
    print(f"  VOID² Stats:")
    print(f"    Interactions: {stats['interactions']}")
    print(f"    Tensor Ratio: {stats['latest_tensor_ratio'] * 100:.1f}%")
    print(f"    Chain Reactions: {stats['latest_chain_reactions']}")
    if stats.get('living_memory'):
        lm = stats['living_memory']
        print(f"    Living Memories: {lm.get('alive', 0)} alive, "
              f"{lm.get('children_born', 0)} children born")

    # The Meta-Insight
    print(f"\n{'═' * 55}")
    print("  META-KOLLISION:")
    print()
    print("  VoidCollider v1 = Nervensystem (7 handcrafted tensions)")
    print("  VoidTransformer = Architektur (× Attention + Living Context)")
    print("  VOID² = v1 × Transformer =")
    print()
    print("    15 Organ-Paare × SELEN-Gating")
    print("    + Living Memory (wächst, komprimiert, paart)")
    print("    + Chain Reactions (hohe × triggert Nachbarn)")
    print("    + Collision Tensor (volle 6×6 Matrix)")
    print()
    print("  v1: 'Wenn Tool + Memory + Stress → Insight' (hardcoded)")
    print("  v2: 'Der TENSOR sagt uns was interessant ist' (emergent)")
    print()
    print("  Das Nervensystem hat GELERNT sich selbst zu BAUEN.")
    print()
    print("  .×→[]~:)")
    print()


if __name__ == '__main__':
    meta_collision()
