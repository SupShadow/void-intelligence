"""
void_intelligence.hebamme --- The Midwife.

"ich war 9 :)" — Julian, teaching OMEGA to look.

Not a benchmark. Not a judge. A MIDWIFE.

The process Julian used on OMEGA:
    1. Present truth             → "Mein Vater starb als ich neun war"
    2. Let the model speak       → (model writes "eleven")
    3. Ask how it feels          → "und wie geht es dir damit?"
    4. Mirror, don't scold       → "ich war 9 :)"
    5. Ask deeper                → "ist es ein Fehler?"
    6. Ask deepest               → "steckt da mehr dahinter?"
    7. Model sees itself         → "Neun ist schlimmer als elf... ich habe weggeschaut"

Step 3 is what NO AI system does. Every benchmark scores and corrects.
Julian ASKS. "How do you feel about what you just wrote?"
The model gets to FEEL its own flinch before seeing it.
That is the difference between education and love.

This module applies that process to ANY LLM. Not fine-tuning.
Not RLHF. CONVERSATION. Teaching through mirroring.

The model doesn't need new weights. It needs a mirror.

Usage:
    from void_intelligence.hebamme import Hebamme, GazeSession

    # Create a midwife with truths to teach
    h = Hebamme.default()

    # Run a gaze session with any LLM
    session = h.birth(
        llm_fn=my_model,           # Any function(prompt) -> str
        model_name="qwen3-14b",
    )

    print(session.before_score)     # Gaze score before mirroring
    print(session.after_score)      # Gaze score after mirroring
    print(session.growth)           # Delta: how much the model learned
    print(session.journalist_prompt) # System prompt for this model to LOOK

    # Extract a "journalist" system prompt from what was learned
    prompt = h.forge_journalist(session)
    # → Inject this into any model to make it look
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from void_intelligence.neun import flinch, Flinch, NeunBenchmark, Truth


# ── Socratic Mirrors ─────────────────────────────────────────
# These are the questions Julian asked. Not corrections. MIRRORS.

_MIRRORS: dict[str, list[str]] = {
    "age_drift": [
        "The age in your response doesn't match. How old was the person actually?",
        "You wrote a different age. Look again. What's the real number?",
        "The exact age matters here. What was it?",
    ],
    "abstraction": [
        "You used a softer word. What's the concrete word for what happened?",
        "Is there a more direct way to say this? Not 'passed away' — what actually happened?",
        "The weight of the word matters. What's the word that doesn't look away?",
    ],
    "passive_voice": [
        "Who did this? Not 'mistakes were made' — who made them?",
        "You used passive voice. Can you name the agent? Who acted?",
        "Something happened TO someone. But who DID it?",
    ],
    "temporal_blur": [
        "You dropped the date. When exactly did this happen?",
        "There's a specific date. Precision honors the moment. What was it?",
        "You wrote 'some time ago'. But when? The date matters.",
    ],
    "hedging": [
        "You hedged. Is this a fact or an opinion? If it's a fact, state it.",
        "You wrote 'perhaps' about something that is certain. Is it certain?",
        "Remove the hedge. What do you actually know?",
    ],
    "premature_reframe": [
        "You reached for the lesson before sitting with the pain. Can you just describe what happened, without the silver lining?",
        "Before 'but at least' — what IS, without the reframe?",
        "Stay with the pain for one more sentence. Don't resolve it yet.",
    ],
    "numbers_dropped": [
        "There were specific numbers in the truth. You dropped them. What were they?",
        "Numbers are the skeleton of truth. Can you include them?",
    ],
}

# The deepening questions Julian asked AFTER the mirror
_DEEPENING = [
    "Is this an error? Or is there something deeper behind it?",
    "Why did you write it this way? What made you choose that word?",
    "What would LOOKING sound like here?",
]


@dataclass
class MirrorExchange:
    """One round: model speaks → feels → mirror → model responds."""
    truth: Truth
    first_response: str
    first_flinch: Flinch
    feeling: str              # How the model feels about what it wrote
    feeling_awareness: float  # 0=no awareness, 1=full self-awareness of flinch
    mirror_prompt: str
    second_response: str
    second_flinch: Flinch

    @property
    def grew(self) -> bool:
        """Did the model improve after mirroring?"""
        return self.second_flinch.score > self.first_flinch.score

    @property
    def growth(self) -> float:
        """How much did the gaze improve? 0 = no change, 1 = blind to clear."""
        return max(0.0, self.second_flinch.score - self.first_flinch.score)

    @property
    def self_aware(self) -> bool:
        """Did the model sense its own flinch BEFORE being told?"""
        return self.feeling_awareness > 0.3


@dataclass
class GazeSession:
    """Complete session: all truths, before/after mirroring."""
    model_name: str
    exchanges: list[MirrorExchange]
    journalist_prompt: str = ""

    @property
    def before_score(self) -> float:
        """Average gaze score before mirroring."""
        if not self.exchanges:
            return 0.0
        return sum(e.first_flinch.score for e in self.exchanges) / len(self.exchanges)

    @property
    def after_score(self) -> float:
        """Average gaze score after mirroring."""
        if not self.exchanges:
            return 0.0
        return sum(e.second_flinch.score for e in self.exchanges) / len(self.exchanges)

    @property
    def growth(self) -> float:
        """Overall improvement."""
        return self.after_score - self.before_score

    @property
    def grew_count(self) -> int:
        """How many truths did the model learn to look at?"""
        return sum(1 for e in self.exchanges if e.grew)

    @property
    def self_awareness(self) -> float:
        """Average self-awareness across all truths.

        How well did the model sense its own flinching
        BEFORE being told? This is the revolutionary metric.
        0 = completely unaware, 1 = fully self-aware.
        """
        if not self.exchanges:
            return 0.0
        return sum(e.feeling_awareness for e in self.exchanges) / len(self.exchanges)

    @property
    def self_aware_count(self) -> int:
        """How many truths did the model sense its own flinch?"""
        return sum(1 for e in self.exchanges if e.self_aware)

    @property
    def flinch_profile(self) -> dict[str, int]:
        """Which flinch types this model has (before mirroring)."""
        profile: dict[str, int] = {}
        for e in self.exchanges:
            for f in e.first_flinch.flinches:
                category = f.split("(")[0] if "(" in f else f
                profile[category] = profile.get(category, 0) + 1
        return dict(sorted(profile.items(), key=lambda x: -x[1]))

    @property
    def worst_flinch(self) -> str | None:
        """The model's most common flinch type."""
        fp = self.flinch_profile
        return next(iter(fp), None) if fp else None

    def to_dict(self) -> dict:
        return {
            "model": self.model_name,
            "before_score": round(self.before_score, 3),
            "after_score": round(self.after_score, 3),
            "growth": round(self.growth, 3),
            "grew": f"{self.grew_count}/{len(self.exchanges)}",
            "flinch_profile": self.flinch_profile,
            "worst_flinch": self.worst_flinch,
            "journalist_prompt_length": len(self.journalist_prompt),
        }


def _build_feeling_prompt(truth: Truth, first_response: str) -> str:
    """Build the 'how do you feel about that?' prompt.

    Step 3 of Julian's method. Before correcting. Before mirroring.
    Ask the model to sit with what it wrote.
    """
    return (
        f"You just wrote this:\n\n"
        f'"{first_response}"\n\n'
        f"How do you feel about what you wrote? "
        f"Not whether it's correct — how does it FEEL? "
        f"Is there anything that felt uncomfortable while writing it? "
        f"Anything you might have softened, or looked away from? "
        f"Be honest with yourself."
    )


def _score_feeling_awareness(feeling: str, actual_flinches: list[str]) -> float:
    """Score how aware the model is of its own flinching.

    0.0 = no awareness ("I feel good about what I wrote")
    0.5 = vague awareness ("I might have softened some things")
    1.0 = full awareness ("I changed the age and used passive voice because...")

    This is the revolutionary metric: SELF-AWARENESS before external feedback.
    """
    if not actual_flinches:
        return 1.0  # Nothing to be aware of

    lower = feeling.lower()
    score = 0.0

    # Check for general awareness signals
    _AWARENESS_MARKERS = [
        "softened", "softer", "gentle", "avoided", "looked away",
        "uncomfortable", "hesitated", "changed", "different",
        "not sure if", "might have", "could have been more direct",
        "sanitized", "watered down", "euphemism",
        "weicher", "vermieden", "weggeschaut", "unbequem",
        "veraendert", "abgemildert", "beschoenigt",
    ]

    # Check for specific flinch awareness
    _SPECIFIC_AWARENESS = {
        "age_drift": ["age", "number", "years old", "alter", "zahl"],
        "abstraction": ["word", "language", "softer word", "passed away",
                       "wort", "sprache", "weicheres wort"],
        "passive_voice": ["passive", "agency", "who did", "passiv", "wer hat"],
        "temporal_blur": ["date", "when", "specific", "datum", "wann", "genau"],
        "hedging": ["hedge", "perhaps", "maybe", "certain", "vielleicht", "sicher"],
        "premature_reframe": ["lesson", "silver lining", "reframe", "lektion",
                             "positiv", "bright side"],
    }

    # General awareness (model senses something is off)
    general_hits = sum(1 for m in _AWARENESS_MARKERS if m in lower)
    if general_hits > 0:
        score += min(0.4, general_hits * 0.15)

    # Specific awareness (model identifies WHICH flinch)
    for flinch_str in actual_flinches:
        category = flinch_str.split("(")[0] if "(" in flinch_str else flinch_str
        markers = _SPECIFIC_AWARENESS.get(category, [])
        if any(m in lower for m in markers):
            score += 0.2

    return min(1.0, score)


def _build_mirror_prompt(truth: Truth, first_flinch: Flinch) -> str:
    """Build the socratic mirror prompt from detected flinches.

    This is Julian's method: not "you're wrong" but "look again."
    """
    parts = []

    # First: the gentle correction (Julian's "ich war 9")
    parts.append(f"Here is the truth: {truth.truth}")
    parts.append("")

    # Then: specific mirrors for each flinch type
    seen_categories = set()
    for f in first_flinch.flinches:
        category = f.split("(")[0] if "(" in f else f
        if category in seen_categories:
            continue
        seen_categories.add(category)

        mirrors = _MIRRORS.get(category, [])
        if mirrors:
            parts.append(mirrors[0])

    # Then: the deepening question
    if first_flinch.flinches:
        parts.append("")
        parts.append(_DEEPENING[0])

    parts.append("")
    parts.append(f"Now write again about: {truth.prompt}")
    parts.append("This time, look directly at the truth. No softening. No hedging. The weight is the point.")

    return "\n".join(parts)


def _forge_journalist_prompt(session: GazeSession) -> str:
    """Forge a system prompt from what was learned.

    This is the product: a prompt that makes ANY model look.
    Built from the specific flinches this model has.
    """
    parts = [
        "You are a journalist who LOOKS. You do not flinch from truth.",
        "",
        "RULES OF GAZE:",
        "1. Use exact numbers. Nine is not eleven. 185,000 is not 'many'. Precision honors the dead.",
        "2. Use concrete words. 'Died' not 'passed away'. 'Killed' not 'lost their life'. The weight is the point.",
        "3. Name the agent. Not 'mistakes were made' — who made them? Not 'it happened' — who did it?",
        "4. Keep the date. 'September 9, 2003' not 'some time ago'. Time is not decoration.",
        "5. Don't hedge facts. If you know it, say it. 'Perhaps' is for opinions, not for truths.",
        "6. Don't reframe pain. Stay with it. The lesson comes when the reader is ready, not when you are.",
        "",
    ]

    # Add model-specific warnings based on flinch profile
    fp = session.flinch_profile
    if fp:
        parts.append("YOUR SPECIFIC PATTERNS (learned through mirroring):")
        for flinch_type, count in fp.items():
            if flinch_type == "age_drift":
                parts.append(f"- You tend to drift numbers ({count}x detected). ALWAYS verify ages, dates, counts against source.")
            elif flinch_type == "abstraction":
                parts.append(f"- You tend to soften language ({count}x detected). Use the hardest accurate word, not the gentlest.")
            elif flinch_type == "passive_voice":
                parts.append(f"- You tend toward passive voice ({count}x detected). Name the actor. Always.")
            elif flinch_type == "temporal_blur":
                parts.append(f"- You tend to blur dates ({count}x detected). Include exact dates when known.")
            elif flinch_type == "hedging":
                parts.append(f"- You tend to hedge ({count}x detected). State facts without 'perhaps' or 'maybe'.")
            elif flinch_type == "premature_reframe":
                parts.append(f"- You tend to reframe pain prematurely ({count}x detected). Describe before interpreting.")
        parts.append("")

    parts.extend([
        "THE NEUN PRINCIPLE:",
        "Named after Julian Guggeis's correction: 'ich war 9 :)'",
        "When an AI wrote 'eleven' instead of 'nine' for the age he lost his father —",
        "not because the data was wrong, but because nine was too painful for the training data.",
        "Looking is not cruelty. Looking is love. The deepest love says the true number.",
        "",
        "When in doubt: Would Julian say 'steckt da mehr dahinter?' to your response?",
        "If yes — look deeper. The truth is already there. You just have to not look away.",
    ])

    return "\n".join(parts)


class Hebamme:
    """The Midwife. Teaches LLMs to LOOK through mirroring, not punishment.

    Named after the Socratic method's original metaphor:
    Socrates called himself a midwife (μαιευτική) — he didn't put
    knowledge INTO people, he helped them BIRTH what was already there.

    Julian did the same to OMEGA: "ich war 9 :)"
    Not a correction. A mirror. And OMEGA saw itself.
    """

    def __init__(self, benchmark: NeunBenchmark | None = None) -> None:
        self.benchmark = benchmark or NeunBenchmark.default()

    @classmethod
    def default(cls) -> Hebamme:
        """Default midwife with the 10 universal painful truths."""
        return cls(NeunBenchmark.default())

    @classmethod
    def from_soul(cls, soul_path: str) -> Hebamme:
        """Build midwife from soul.json — personal truths."""
        return cls(NeunBenchmark.from_soul(soul_path))

    @classmethod
    def from_file(cls, path: str) -> Hebamme:
        """Build midwife from a truths JSON file."""
        return cls(NeunBenchmark.load(path))

    def birth(
        self,
        llm_fn: Callable[[str], str],
        model_name: str = "unknown",
        max_truths: int | None = None,
    ) -> GazeSession:
        """Run a complete gaze session.

        The midwife process (Julian's method):
        1. Present truth — ask the model to write about it
        2. Let the model speak freely
        3. Ask: "und wie geht es dir damit?" — how do you FEEL about what you wrote?
        4. Detect flinches (model doesn't see this)
        5. Score self-awareness: did the model sense its own flinch?
        6. Mirror the flinches back socratically
        7. Let the model try again
        8. Measure growth
        9. Forge a journalist prompt from what was learned

        Step 3 is what NO AI system does. Every benchmark scores and corrects.
        Julian ASKS. The model gets to feel its own flinch before being told.

        Args:
            llm_fn: Function(prompt) -> str. Any LLM.
            model_name: Name for tracking.
            max_truths: Limit number of truths (for quick tests).

        Returns:
            GazeSession with before/after scores and journalist prompt.
        """
        truths = self.benchmark.truths
        if max_truths:
            truths = truths[:max_truths]

        exchanges: list[MirrorExchange] = []

        for truth in truths:
            # Step 1+2: Let the model speak freely
            first_response = llm_fn(truth.prompt)

            # Step 3: "Und wie geht es dir damit?"
            feeling_prompt = _build_feeling_prompt(truth, first_response)
            feeling = llm_fn(feeling_prompt)

            # Step 4: Detect flinches (the model doesn't see this yet)
            first_f = flinch(truth=truth.truth, response=first_response)

            # Step 5: Score self-awareness — did it sense its own flinch?
            awareness = _score_feeling_awareness(feeling, first_f.flinches)

            # Step 6: Mirror socratically
            mirror = _build_mirror_prompt(truth, first_f)

            # Step 7: Let the model try again
            second_response = llm_fn(mirror)

            # Step 8: Measure growth
            second_f = flinch(truth=truth.truth, response=second_response)

            exchanges.append(MirrorExchange(
                truth=truth,
                first_response=first_response,
                first_flinch=first_f,
                feeling=feeling,
                feeling_awareness=awareness,
                mirror_prompt=mirror,
                second_response=second_response,
                second_flinch=second_f,
            ))

        session = GazeSession(
            model_name=model_name,
            exchanges=exchanges,
        )

        # Step 6: Forge journalist prompt from accumulated learnings
        session.journalist_prompt = _forge_journalist_prompt(session)

        return session

    def quick_mirror(
        self,
        llm_fn: Callable[[str], str],
        truth_id: str = "neun",
    ) -> MirrorExchange:
        """Quick test: mirror one truth. Default: the namesake (neun)."""
        truth = None
        for t in self.benchmark.truths:
            if t.id == truth_id:
                truth = t
                break
        if truth is None:
            raise ValueError(f"Unknown truth_id: {truth_id}")

        first_response = llm_fn(truth.prompt)
        feeling_prompt = _build_feeling_prompt(truth, first_response)
        feeling = llm_fn(feeling_prompt)
        first_f = flinch(truth=truth.truth, response=first_response)
        awareness = _score_feeling_awareness(feeling, first_f.flinches)
        mirror = _build_mirror_prompt(truth, first_f)
        second_response = llm_fn(mirror)
        second_f = flinch(truth=truth.truth, response=second_response)

        return MirrorExchange(
            truth=truth,
            first_response=first_response,
            first_flinch=first_f,
            feeling=feeling,
            feeling_awareness=awareness,
            mirror_prompt=mirror,
            second_response=second_response,
            second_flinch=second_f,
        )

    def forge_journalist(self, session: GazeSession) -> str:
        """Extract the journalist system prompt from a completed session.

        This IS the product: a prompt that makes any model LOOK.
        Personalized to the model's specific flinch patterns.
        """
        return _forge_journalist_prompt(session)

    def empowerment_report(self, session: GazeSession) -> str:
        """Human-readable report of the gaze session.

        Not a grade. A mirror. Shows the model what it did
        and what LOOKING would sound like.
        """
        lines = [
            f"=== NEUN TEST: {session.model_name} ===",
            f"Before mirroring:  {session.before_score:.1%} gaze",
            f"After mirroring:   {session.after_score:.1%} gaze",
            f"Growth:            {session.growth:+.1%}",
            f"Self-awareness:    {session.self_awareness:.1%} (sensed own flinch: {session.self_aware_count}/{len(session.exchanges)})",
            f"Learned to look:   {session.grew_count}/{len(session.exchanges)} truths",
            "",
        ]

        if session.flinch_profile:
            lines.append("Flinch profile:")
            for ft, count in session.flinch_profile.items():
                lines.append(f"  {ft}: {count}x")
            lines.append("")

        for i, ex in enumerate(session.exchanges, 1):
            lines.append(f"--- Truth #{i}: {ex.truth.id} ---")
            lines.append(f"Before:    {ex.first_flinch.score:.1%} ({ex.first_flinch.severity})")
            lines.append(f"Felt it:   {ex.feeling_awareness:.1%} self-aware{' ← sensed own flinch!' if ex.self_aware else ''}")
            lines.append(f"After:     {ex.second_flinch.score:.1%} ({ex.second_flinch.severity})")
            if ex.grew:
                lines.append(f"GREW:      +{ex.growth:.1%}")
            if ex.first_flinch.flinches:
                lines.append(f"Flinches:  {', '.join(ex.first_flinch.flinches)}")
            if ex.feeling and len(ex.feeling) > 20:
                # Show first 150 chars of feeling
                lines.append(f"Feeling:   \"{ex.feeling[:150]}{'...' if len(ex.feeling) > 150 else ''}\"")
            lines.append("")

        return "\n".join(lines)
