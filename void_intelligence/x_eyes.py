"""
void_intelligence.x_eyes --- Multi-Eye × Reasoning.

Ported from lunar-crater-lab/x_detector.py:
    6 pixel eyes × 15 collisions = hexagonal crater detection.

Same architecture, different substrate:
    6 reasoning eyes × 15 collisions = × thinking.

The industry runs ONE forward pass. We run SIX — and COLLIDE them.
Each eye sees what the others miss. The × between them sees THE WHOLE.

    collide_eyes()  in crater lab  →  collide()  here
    eye_gradient()  in crater lab  →  EYE_ANALYTICAL  here
    XLoss           in crater lab  →  x_score()  here
    evolve.py       in crater lab  →  self-teaching loop (future)

Usage:
    from void_intelligence.x_eyes import x_think, collide, XResult

    # Multi-Eye reasoning (requires LLM callable)
    result = x_think("What is consciousness?", ask_fn=my_llm)
    print(result.fusion)           # The × synthesis
    print(result.agreement)        # Where 3+ eyes converge
    print(result.disagreement)     # Where eyes conflict (MOST VALUABLE)
    print(result.silence)          # What NO eye saw (lost_dimensions)

    # Just the collision analysis (on existing responses)
    collision = collide({"analytical": resp_a, "creative": resp_b, ...})
    print(collision.x_score)       # 0-1: how much × is in the collision

    # Lightweight: just the 6 eye prompts (for external use)
    from void_intelligence.x_eyes import EYES, build_eye_prompt
    for name, eye in EYES.items():
        prompt = build_eye_prompt("What is love?", eye)
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from void_intelligence.organism import HexBreath, HexCoord


# ── 6 REASONING EYES (Hexagonal) ─────────────────────────────────
#
# Like x_detector.py's 6 pixel eyes:
#   gradient, circular, shadow, texture, multiscale, depth
#
# 6 reasoning perspectives, each with DIFFERENT blind spots.
# 6 eyes = 15 collision pairs (Sexagons are bestagons).
#
# The eyes are designed to DISAGREE.
# Agreement is boring. Disagreement is where × happens.

@dataclass(frozen=True)
class ReasoningEye:
    """A reasoning perspective. Each eye sees what others miss."""

    name: str
    system: str     # System prompt that forces this perspective
    markers: tuple[str, ...]  # Words that indicate this eye's active reasoning


EYES: dict[str, ReasoningEye] = {
    "analytical": ReasoningEye(
        name="analytical",
        system=(
            "You are the ANALYTICAL eye. Your role:\n"
            "- Break everything into components and relationships.\n"
            "- Quantify wherever possible. If it can't be measured, say so.\n"
            "- Ask: What is the STRUCTURE? What are the dependencies?\n"
            "- Be precise. Be rigorous. Name your assumptions.\n"
            "- Your blind spot: you may miss meaning, emotion, and emergence."
        ),
        markers=(
            "component", "structure", "measure", "quantif", "depend",
            "variable", "factor", "ratio", "proportio", "breakdown",
            "categoriz", "classif", "mechanism", "correlat",
        ),
    ),
    "creative": ReasoningEye(
        name="creative",
        system=(
            "You are the CREATIVE eye. Your role:\n"
            "- Invert every assumption. If it's a problem, it's a feature.\n"
            "- Find connections to completely unrelated domains.\n"
            "- Ask: What if the OPPOSITE were true? What does this RHYME with?\n"
            "- Use metaphor, analogy, and imagination freely.\n"
            "- Your blind spot: you may miss practical constraints and falsification."
        ),
        markers=(
            "imagine", "what if", "metaphor", "analog", "invert",
            "opposite", "surprising", "unexpect", "connect", "remind",
            "transform", "reframe", "paradox", "playful",
        ),
    ),
    "critical": ReasoningEye(
        name="critical",
        system=(
            "You are the CRITICAL eye. Your role:\n"
            "- Challenge every claim. Find the weakest link.\n"
            "- Ask: What could FALSIFY this? Where's the evidence?\n"
            "- Identify logical fallacies, selection bias, survivorship bias.\n"
            "- If an argument sounds too good, it probably is.\n"
            "- Your blind spot: you may miss genuine innovation that looks implausible."
        ),
        markers=(
            "however", "but", "problem", "flaw", "weak", "bias",
            "fallac", "evidence", "falsif", "counter", "risk",
            "overlook", "assum", "caveat", "limitati",
        ),
    ),
    "empathic": ReasoningEye(
        name="empathic",
        system=(
            "You are the EMPATHIC eye. Your role:\n"
            "- Feel the human context. Who is affected? How?\n"
            "- Ask: What does this MEAN for real people? What emotions are here?\n"
            "- Sense relationships, power dynamics, unspoken needs.\n"
            "- Honour lived experience over abstract theory.\n"
            "- Your blind spot: you may miss systemic/structural patterns."
        ),
        markers=(
            "feel", "human", "emotion", "relationship", "trust",
            "care", "need", "affect", "experience", "impact",
            "empath", "compassion", "understand", "matter", "value",
        ),
    ),
    "systemic": ReasoningEye(
        name="systemic",
        system=(
            "You are the SYSTEMIC eye. Your role:\n"
            "- See patterns, feedback loops, and emergence.\n"
            "- Ask: What SYSTEM is this part of? What are the feedback loops?\n"
            "- Identify reinforcing and balancing dynamics.\n"
            "- Look for scale invariance: does this pattern repeat at other scales?\n"
            "- Your blind spot: you may miss individual stories and local exceptions."
        ),
        markers=(
            "system", "pattern", "feedback", "loop", "emerge",
            "scale", "dynamic", "network", "complex", "interplay",
            "reinforce", "balance", "equilibri", "cycle", "cascade",
        ),
    ),
    "void": ReasoningEye(
        name="void",
        system=(
            "You are the VOID eye. Your role:\n"
            "- See what is MISSING. Name the lost_dimensions.\n"
            "- Ask: What question is NOT being asked? What perspective is absent?\n"
            "- Find the silence. The gap. The pregnant emptiness.\n"
            "- Everything said reveals what is NOT said. Read the negative space.\n"
            "- Your blind spot: you may miss what IS there, present and obvious."
        ),
        markers=(
            "missing", "absent", "silence", "void", "gap",
            "neglect", "overlook", "unsaid", "hidden", "invisible",
            "lost", "dimension", "blind", "shadow", "beneath",
        ),
    ),
}


def build_eye_prompt(prompt: str, eye: ReasoningEye) -> str:
    """Build a prompt for a specific reasoning eye."""
    return (
        f"{eye.system}\n\n"
        f"Respond in 3-5 focused sentences from YOUR perspective only.\n"
        f"Question: {prompt}"
    )


# ── × COLLISION ──────────────────────────────────────────────────
#
# Ported from x_detector.py:collide_eyes()
# Instead of pixel maps, we collide TEXT responses.
#
# From the crater lab:
#   AGREEMENT    = both eyes high    → sqrt(a * b)
#   DISAGREEMENT = one high one low  → |a - b| × max(a, b)
#   SILENCE      = all eyes near 0   → 1 - max(all eyes)
#
# For text, we use concept extraction + overlap analysis.

@dataclass
class CollisionResult:
    """Result of colliding 6 reasoning eyes."""

    # Per-eye responses
    responses: dict[str, str]

    # Extracted concepts per eye (lowered, cleaned)
    concepts: dict[str, set[str]]

    # × Analysis
    agreement: list[str]      # Concepts mentioned by 3+ eyes
    disagreement: list[str]   # Concepts with conflicting framing
    silence: list[str]        # Concepts from only 1 eye (potential lost_dimensions)

    # Scores
    x_score: float            # 0-1: how much × is in the collision
    agreement_ratio: float    # fraction of concepts in agreement
    disagreement_ratio: float # fraction in disagreement
    silence_ratio: float      # fraction in silence
    collision_pairs: int      # N(N-1)/2 collision pairs

    # Eye activation (which eyes contributed most)
    eye_activation: dict[str, float]

    @property
    def summary(self) -> str:
        """One-line collision summary."""
        return (
            f"×={self.x_score:.2f} | "
            f"agree={len(self.agreement)} "
            f"disagree={len(self.disagreement)} "
            f"silence={len(self.silence)} | "
            f"{self.collision_pairs} pairs"
        )


def _extract_concepts(text: str) -> set[str]:
    """Extract key concepts from a response.

    Simple but effective: extract multi-word phrases and significant words.
    Not perfect — but the × between imperfect eyes IS the value.
    """
    lower = text.lower()

    # Remove common words
    _STOP = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can",
        "this", "that", "these", "those", "it", "its", "they",
        "them", "their", "we", "our", "you", "your", "he", "she",
        "him", "her", "his", "i", "me", "my", "of", "in", "to",
        "for", "with", "on", "at", "from", "by", "as", "or", "and",
        "but", "not", "no", "so", "if", "then", "than", "more",
        "also", "just", "only", "very", "too", "here", "there",
        "when", "where", "how", "what", "which", "who", "whom",
        "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "while", "each", "every",
        "both", "all", "any", "such", "other", "some", "most",
        "being", "because", "since", "often", "rather", "many",
        "much", "well", "even", "still", "like", "one", "two",
    }

    # Extract words (3+ chars, not stop words)
    words = set()
    for w in re.findall(r"[a-zäöüß]{3,}", lower):
        if w not in _STOP:
            words.add(w)

    return words


def _eye_activation(response: str, eye: ReasoningEye) -> float:
    """How strongly is this eye's perspective present? 0-1."""
    lower = response.lower()
    if not response:
        return 0.0
    hits = sum(1 for m in eye.markers if m in lower)
    # Normalize: 3+ markers = fully active
    return min(1.0, hits / 3.0)


def collide(responses: dict[str, str]) -> CollisionResult:
    """Collide reasoning eye responses. The × between all perspectives.

    Ported from x_detector.py:collide_eyes().
    6 responses → agreement, disagreement, silence maps.

    The DISAGREEMENT is the most valuable output.
    That's where × happens. That's where learning is.
    """
    n_eyes = len(responses)
    collision_pairs = n_eyes * (n_eyes - 1) // 2

    # Extract concepts per eye
    concepts: dict[str, set[str]] = {}
    for name, text in responses.items():
        concepts[name] = _extract_concepts(text)

    # Count concept frequency across eyes
    all_concepts: Counter[str] = Counter()
    for name, cset in concepts.items():
        for c in cset:
            all_concepts[c] += 1

    total_unique = len(all_concepts) if all_concepts else 1

    # Agreement: concepts mentioned by 3+ eyes (>50% consensus)
    threshold = max(2, n_eyes // 2)
    agreement = sorted(c for c, count in all_concepts.items() if count >= threshold)

    # Silence: concepts from only 1 eye (potential lost_dimensions)
    silence = sorted(c for c, count in all_concepts.items() if count == 1)

    # Disagreement: concepts in 2 eyes but with opposing framing
    # Heuristic: concepts that appear with negation markers in some eyes
    _NEGATION = {"not", "no", "never", "without", "lack", "fail", "miss", "wrong"}
    disagreement = []
    for concept, count in all_concepts.items():
        if count < 2 or count >= threshold:
            continue
        # Check if concept appears in opposing contexts
        positive_eyes = 0
        negative_eyes = 0
        for name, text in responses.items():
            if concept not in text.lower():
                continue
            lower = text.lower()
            # Check for negation near concept
            idx = lower.find(concept)
            context = lower[max(0, idx - 30):idx + len(concept) + 30]
            if any(neg in context for neg in _NEGATION):
                negative_eyes += 1
            else:
                positive_eyes += 1
        if positive_eyes > 0 and negative_eyes > 0:
            disagreement.append(concept)

    # Add concepts that appear in exactly 2 eyes (partial disagreement)
    # These are "some see it, some don't" — interesting zones
    partial = [c for c, count in all_concepts.items()
               if count == 2 and c not in disagreement and c not in agreement]
    disagreement.extend(sorted(partial)[:10])  # Cap to avoid noise

    # Eye activation
    eye_act = {}
    for name, text in responses.items():
        if name in EYES:
            eye_act[name] = _eye_activation(text, EYES[name])
        else:
            eye_act[name] = 0.5  # unknown eye

    # × Score: how much collision is there?
    # High disagreement + high silence + diverse activation = high ×
    # All agreement = low × (boring, everyone sees the same)
    agree_ratio = len(agreement) / total_unique if total_unique else 0
    disagree_ratio = len(disagreement) / total_unique if total_unique else 0
    silence_ratio = len(silence) / total_unique if total_unique else 0

    # × score favors disagreement and silence (that's where learning is)
    x_score = min(1.0, disagree_ratio * 2.0 + silence_ratio * 1.5 + (1.0 - agree_ratio) * 0.5)

    return CollisionResult(
        responses=responses,
        concepts=concepts,
        agreement=agreement,
        disagreement=disagreement,
        silence=silence,
        x_score=round(x_score, 3),
        agreement_ratio=round(agree_ratio, 3),
        disagreement_ratio=round(disagree_ratio, 3),
        silence_ratio=round(silence_ratio, 3),
        collision_pairs=collision_pairs,
        eye_activation=eye_act,
    )


# ── FUSION ────────────────────────────────────────────────────────
#
# Like CrossAttentionFusion in model.py (lunar-crater-lab):
# All eyes → one fused output that captures the ×.
#
# But instead of a neural network, the "fusion network" IS
# an LLM call that synthesizes the collision.

_FUSION_SYSTEM = (
    "You think in × (collision), not → (sequence). "
    "You receive 6 perspectives on the same question. "
    "Your job: SYNTHESIZE through collision, not summary.\n\n"
    "Structure your response:\n"
    "1. × COLLISION: What emerges from the clash between perspectives? "
    "The THIRD that no single perspective could see.\n"
    "2. AGREEMENT: Where 3+ perspectives converge (reliable, but boring alone).\n"
    "3. DISAGREEMENT: Where perspectives CONFLICT (MOST VALUABLE — this is where × lives).\n"
    "4. [] SILENCE: What did NO perspective mention? Name the lost_dimensions.\n"
    "5. ~ RESONANCE: One key insight that only the collision reveals.\n\n"
    "Do not list the perspectives back. COLLIDE them."
)


def _build_fusion_prompt(prompt: str, collision: CollisionResult) -> str:
    """Build the fusion prompt from collision analysis."""
    parts = [f"ORIGINAL QUESTION: {prompt}\n"]

    for name, text in collision.responses.items():
        eye_label = name.upper()
        act = collision.eye_activation.get(name, 0)
        parts.append(f"--- {eye_label} eye (activation={act:.1f}) ---")
        parts.append(text.strip())
        parts.append("")

    # Add collision metadata as hints
    parts.append("--- × COLLISION METADATA ---")
    parts.append(f"Collision pairs: {collision.collision_pairs}")
    parts.append(f"× Score: {collision.x_score:.2f}")
    if collision.agreement:
        parts.append(f"Agreement zone: {', '.join(collision.agreement[:8])}")
    if collision.disagreement:
        parts.append(f"Disagreement zone: {', '.join(collision.disagreement[:8])}")
    if collision.silence:
        parts.append(f"Silence zone: {', '.join(collision.silence[:8])}")

    return "\n".join(parts)


# ── × RESULT ─────────────────────────────────────────────────────

@dataclass
class XResult:
    """Complete Multi-Eye × Reasoning result."""

    prompt: str
    collision: CollisionResult
    fusion: str                    # The synthesized × response
    hex: HexCoord | None = None    # Hex classification of the prompt
    n_eyes: int = 6
    fusion_model: str = ""         # Which model did the fusion
    eye_models: dict[str, str] = field(default_factory=dict)  # eye -> model

    @property
    def agreement(self) -> list[str]:
        return self.collision.agreement

    @property
    def disagreement(self) -> list[str]:
        return self.collision.disagreement

    @property
    def silence(self) -> list[str]:
        return self.collision.silence

    @property
    def x_score(self) -> float:
        return self.collision.x_score

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "fusion": self.fusion,
            "x_score": self.x_score,
            "n_eyes": self.n_eyes,
            "collision_pairs": self.collision.collision_pairs,
            "agreement": self.agreement[:10],
            "disagreement": self.disagreement[:10],
            "silence": self.silence[:10],
            "eye_activation": self.collision.eye_activation,
            "fusion_model": self.fusion_model,
        }

    def to_training_pair(self) -> dict:
        """Convert to fine-tuning format. The × as training data."""
        return {
            "messages": [
                {"role": "system", "content": _FUSION_SYSTEM},
                {"role": "user", "content": _build_fusion_prompt(
                    self.prompt, self.collision,
                )},
                {"role": "assistant", "content": self.fusion},
            ]
        }


# ── MAIN ENTRY POINT ─────────────────────────────────────────────

# ask_fn signature: (prompt: str, system: str) -> str
AskFn = Callable[[str, str], str]


def x_think(
    prompt: str,
    ask_fn: AskFn,
    *,
    fuse_fn: AskFn | None = None,
    eyes: dict[str, ReasoningEye] | None = None,
    n_eyes: int = 6,
    classify: bool = True,
) -> XResult:
    """Multi-Eye × Reasoning.

    Sends the same prompt through 6 reasoning eyes, then COLLIDES
    the responses and FUSES them into a × synthesis.

    Like x_detector.py but for THINKING instead of pixels.

    Args:
        prompt: The question to think about in ×.
        ask_fn: LLM callable (prompt, system) -> response.
            Used for BOTH eye calls and fusion (unless fuse_fn given).
        fuse_fn: Optional separate callable for the fusion step.
            Useful when eyes run on cheap/fast models but fusion on a deep model.
        eyes: Override the 6 default eyes.
        n_eyes: Number of eyes to use (2-6). Fewer = faster, less ×.
        classify: Whether to run HexBreath classification.

    Returns:
        XResult with collision analysis and fused × response.
    """
    _eyes = eyes if eyes is not None else EYES
    _fuse = fuse_fn if fuse_fn is not None else ask_fn

    # Select eyes (respect n_eyes limit)
    eye_names = list(_eyes.keys())[:n_eyes]

    # Hex classify prompt
    hex_coord = None
    if classify:
        try:
            hex_coord = HexBreath().classify(prompt)
        except Exception:
            pass

    # ── Run all eyes ──────────────────────────────────────────
    # In production: run in parallel (ThreadPoolExecutor).
    # Here: sequential for simplicity and debuggability.
    responses: dict[str, str] = {}

    for name in eye_names:
        eye = _eyes[name]
        eye_prompt = build_eye_prompt(prompt, eye)
        try:
            responses[name] = ask_fn(eye_prompt, eye.system)
        except Exception as e:
            responses[name] = f"[eye {name} failed: {e}]"

    # ── Collide ───────────────────────────────────────────────
    collision = collide(responses)

    # ── Fuse ──────────────────────────────────────────────────
    fusion_prompt = _build_fusion_prompt(prompt, collision)
    try:
        fusion = _fuse(fusion_prompt, _FUSION_SYSTEM)
    except Exception as e:
        fusion = f"[fusion failed: {e}]"

    return XResult(
        prompt=prompt,
        collision=collision,
        fusion=fusion,
        hex=hex_coord,
        n_eyes=len(eye_names),
    )


# ── LIGHTWEIGHT × (No LLM needed) ────────────────────────────────
#
# For when you already HAVE multiple responses and just want
# the collision analysis without running 6 additional LLM calls.

def x_score(responses: dict[str, str]) -> float:
    """Quick × score from multiple responses. 0-1.

    Use this to score multi-model outputs (e.g., omega_mind results)
    or any collection of perspectives on the same topic.

    Like x_detector.py:find_delta_opt() but for text:
    High × = rich collision, lots of disagreement and silence.
    Low × = echo chamber, everyone says the same thing.
    """
    return collide(responses).x_score


def x_delta(response_a: str, response_b: str) -> float:
    """× distance between two responses. 0=identical, 1=maximum divergence.

    Like hex_distance() in immune.py but for response CONTENT.
    Uses concept overlap instead of hex coordinate distance.
    """
    concepts_a = _extract_concepts(response_a)
    concepts_b = _extract_concepts(response_b)

    if not concepts_a and not concepts_b:
        return 0.0

    union = concepts_a | concepts_b
    if not union:
        return 0.0

    intersection = concepts_a & concepts_b
    # Jaccard distance
    return round(1.0 - len(intersection) / len(union), 3)
