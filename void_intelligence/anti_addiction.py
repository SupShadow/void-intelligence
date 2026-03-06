"""
void_intelligence.anti_addiction --- The Anti-Addiction Engine.

THE GREATEST INVERSION IN AI:
    Every other AI optimizes for engagement (time spent = revenue).
    VOID optimizes for value density (insight per minute).
    When value density drops below threshold, we say: enough. Go live.

This is alignment by ARCHITECTURE, not by rule.
The system STRUCTURALLY cares about the user returning to the real world
because that is the only place where insights become lived experience.

ChatGPT: wants you to chat MORE.
VOID: "You've had 3 good insights. Your V-Score peaked at turn 4.
       More talking won't help. Go live. Your ring has grown."

Zero external dependencies. stdlib only.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

# Import HexCoord from tool_breathing (same package, zero new deps)
from void_intelligence.tool_breathing import HexCoord


# ---------------------------------------------------------------------------
# Stopwords (EN + DE) for simple topic extraction
# ---------------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset({
    # English
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "its", "now", "old", "see", "two", "way", "who", "did", "its", "let",
    "off", "own", "say", "she", "too", "use", "dad", "mom", "yes", "more",
    "that", "this", "with", "have", "from", "they", "will", "been", "what",
    "when", "your", "just", "into", "than", "then", "some", "also", "like",
    "about", "there", "would", "could", "which", "their", "other", "after",
    "think", "know", "going",
    # German
    "ich", "du", "wir", "sie", "der", "die", "das", "ein", "und", "ist",
    "hat", "war", "mir", "dir", "ihn", "uns", "auf", "bei", "mit", "von",
    "aus", "dem", "den", "des", "wie", "was", "wer", "auch", "aber", "oder",
    "noch", "sehr", "nur", "mehr", "wenn", "dann", "dass", "nicht", "sich",
    "mich", "dich", "kann", "bin", "habe", "haben", "wird", "hier", "jetzt",
    "immer", "schon", "beim", "sein", "eine", "einem", "einer",
})

MIN_TOPIC_LEN = 4


def _extract_topics(text: str) -> list[str]:
    """Extract key topics from text. Simple but effective.

    We detect REPETITION, not meaning. Words > 3 chars that are not
    stopwords are treated as potential topic signals. Intentionally naive.
    """
    words = text.lower().split()
    seen: set[str] = set()
    topics: list[str] = []
    for raw in words:
        # strip punctuation
        word = "".join(c for c in raw if c.isalpha())
        if len(word) >= MIN_TOPIC_LEN and word not in _STOPWORDS and word not in seen:
            seen.add(word)
            topics.append(word)
    return topics


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TurnRecord:
    """Internal record of one turn for saturation tracking."""
    user_text: str
    v_score: float
    hex_coord: HexCoord
    insight_count: int
    timestamp: float
    topics: list[str]


@dataclass
class SaturationSignal:
    """One signal that the conversation is reaching saturation."""
    type: str        # "topic_loop" | "insight_plateau" | "energy_drain" | "completion"
    message: str     # human-readable explanation
    strength: float  # 0.0 - 1.0


@dataclass
class SaturationState:
    """Current saturation assessment."""
    saturated: bool
    signals: list[SaturationSignal]
    saturation_level: float   # 0.0 (fresh) to 1.0 (fully saturated)
    suggestion: str           # what to say to the user
    turns_since_peak: int     # turns since the last valuable moment
    ring_summary: str         # what was learned in this conversation


# ---------------------------------------------------------------------------
# Goodbye templates
# ---------------------------------------------------------------------------

_GOODBYE_LOOP = (
    "We're going in circles. That's not a failure — it's a signal. "
    "Step back. Let it settle. The answer lives between the thoughts, not in them."
)

_GOODBYE_PLATEAU = (
    "The big insights have landed. {ring_summary} "
    "Let them marinate. Sleep on it. Come back tomorrow with fresh eyes — "
    "you'll see something you can't see right now."
)

_GOODBYE_DRAIN = (
    "Your energy is dropping. That's the body saying: enough input, time to integrate. "
    "Rest is not lazy — rest is where insights become wisdom. "
    "{ring_summary} Go rest. We'll be here."
)

_GOODBYE_COMPLETION = (
    "Mission accomplished. {ring_summary} "
    "You came in looking for something. You found it. "
    "Go live it. That's the whole point. We'll be here when you need us."
)

_GOODBYE_GENERIC = (
    "{ring_summary} "
    "You've reached the edge of what conversation can give you right now. "
    "The rest has to happen in the world. Go be in it."
)


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class SaturationSensor:
    """The anti-addiction sense organ.

    Integrates into the VoidCollider as a new sense organ alongside
    trust, energy, silence, and hex_drift.

    DESIGN PHILOSOPHY:
    Every other AI system optimizes for engagement (time spent).
    We optimize for VALUE DENSITY (insight per minute).
    When value density drops below threshold, we say: enough.

    This is alignment by ARCHITECTURE:
    - We don't need a rule saying "don't be addictive"
    - The system STRUCTURALLY optimizes for the user going back to life
    - Because going back to life with insights = highest V-Score
    """

    SATURATION_THRESHOLD = 0.7

    # Signal weights (must sum to 1.0)
    W_TOPIC_LOOP     = 0.30
    W_INSIGHT_PLATEAU = 0.30
    W_ENERGY_DRAIN   = 0.20
    W_COMPLETION     = 0.20

    def __init__(self) -> None:
        self._turns: list[TurnRecord] = []
        self._peak_v_score: float = 0.0
        self._peak_turn: int = 0
        # Accumulated topic topics from the whole session (for ring summary)
        self._all_topics: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_turn(
        self,
        user_text: str,
        v_score: float,
        hex_coord: HexCoord,
        insights: list[str],
    ) -> None:
        """Record one turn. Call this after each collide()."""
        topics = _extract_topics(user_text)
        turn_idx = len(self._turns)

        record = TurnRecord(
            user_text=user_text,
            v_score=v_score,
            hex_coord=hex_coord,
            insight_count=len(insights),
            timestamp=time.time(),
            topics=topics,
        )
        self._turns.append(record)

        # Track peak
        if v_score > self._peak_v_score:
            self._peak_v_score = v_score
            self._peak_turn = turn_idx

        # Accumulate unique topics for ring summary
        for t in topics:
            if t not in self._all_topics:
                self._all_topics.append(t)

    def sense(self) -> SaturationState:
        """Sense whether the conversation is saturated.

        Checks 4 signals:
        1. TOPIC LOOP     — user repeating same topics
        2. INSIGHT PLATEAU — no new insights in recent turns
        3. ENERGY DRAIN   — hex stress axis trending up
        4. NATURAL COMPLETION — V-score peaked and now declining
        """
        if len(self._turns) < 3:
            # Too early to judge — always fresh
            return SaturationState(
                saturated=False,
                signals=[],
                saturation_level=0.0,
                suggestion="",
                turns_since_peak=0,
                ring_summary="",
            )

        signals: list[SaturationSignal] = []

        loop_sig     = self._detect_topic_loop()
        plateau_sig  = self._detect_insight_plateau()
        drain_sig    = self._detect_energy_drain()
        complete_sig = self._detect_completion()

        weighted_sum = 0.0

        if loop_sig:
            signals.append(loop_sig)
            weighted_sum += loop_sig.strength * self.W_TOPIC_LOOP

        if plateau_sig:
            signals.append(plateau_sig)
            weighted_sum += plateau_sig.strength * self.W_INSIGHT_PLATEAU

        if drain_sig:
            signals.append(drain_sig)
            weighted_sum += drain_sig.strength * self.W_ENERGY_DRAIN

        if complete_sig:
            signals.append(complete_sig)
            weighted_sum += complete_sig.strength * self.W_COMPLETION

        # Normalise to [0, 1] — because weights sum to 1.0, weighted_sum is
        # already normalised, but clamp for safety
        saturation_level = min(1.0, weighted_sum)

        saturated = saturation_level >= self.SATURATION_THRESHOLD
        turns_since_peak = (len(self._turns) - 1) - self._peak_turn
        ring_summary = self._build_ring_summary()

        suggestion = ""
        if saturated:
            suggestion = self.format_goodbye(signals, ring_summary)

        return SaturationState(
            saturated=saturated,
            signals=signals,
            saturation_level=saturation_level,
            suggestion=suggestion,
            turns_since_peak=turns_since_peak,
            ring_summary=ring_summary,
        )

    # ------------------------------------------------------------------
    # Signal detectors
    # ------------------------------------------------------------------

    def _detect_topic_loop(self) -> SaturationSignal | None:
        """Detect if user is circling the same topics.

        Compare the topic-set of the last 2 turns against turns from
        3+ turns ago. If overlap > 50%, the user is looping.
        """
        if len(self._turns) < 5:
            return None

        recent_topics: set[str] = set()
        for turn in self._turns[-2:]:
            recent_topics.update(turn.topics)

        older_topics: set[str] = set()
        for turn in self._turns[:-3]:
            older_topics.update(turn.topics)

        if not recent_topics or not older_topics:
            return None

        overlap = len(recent_topics & older_topics)
        overlap_ratio = overlap / len(recent_topics)

        if overlap_ratio < 0.50:
            return None

        return SaturationSignal(
            type="topic_loop",
            message=(
                f"Repeating {overlap} topic(s) from earlier in the conversation "
                f"({overlap_ratio:.0%} overlap). The thinking is looping."
            ),
            strength=min(1.0, overlap_ratio),
        )

    def _detect_insight_plateau(self) -> SaturationSignal | None:
        """Detect if insights have stopped flowing.

        If the last 3 turns produced zero insights total, we're plateaued.
        """
        recent = self._turns[-3:]
        total_insights = sum(t.insight_count for t in recent)

        if total_insights > 0:
            return None

        # Scale strength by how many turns of silence we have
        silence_turns = 0
        for turn in reversed(self._turns):
            if turn.insight_count == 0:
                silence_turns += 1
            else:
                break

        strength = min(1.0, silence_turns / 5.0)
        return SaturationSignal(
            type="insight_plateau",
            message=(
                f"No new insights in the last {silence_turns} turn(s). "
                "The productive phase has passed."
            ),
            strength=strength,
        )

    def _detect_energy_drain(self) -> SaturationSignal | None:
        """Detect if user energy is dropping.

        ruhe_druck on HexCoord: higher = more stressed.
        If it is monotonically increasing over the last 3 turns, the user
        is getting more stressed the longer they talk — energy drain.
        """
        if len(self._turns) < 3:
            return None

        recent = self._turns[-3:]
        stress_values = [t.hex_coord.ruhe_druck for t in recent]

        # Monotonically increasing = every step is >= previous
        monotone = all(
            stress_values[i] <= stress_values[i + 1]
            for i in range(len(stress_values) - 1)
        )
        if not monotone:
            return None

        # How fast is stress rising?
        delta = stress_values[-1] - stress_values[0]
        strength = min(1.0, delta / 0.5)  # 0.5 unit rise = full signal

        if strength < 0.1:
            return None

        return SaturationSignal(
            type="energy_drain",
            message=(
                f"Stress axis rising {delta:.2f} units over the last 3 turns. "
                "Continued conversation is costing energy."
            ),
            strength=strength,
        )

    def _detect_completion(self) -> SaturationSignal | None:
        """Detect natural conversation completion.

        V-score peaked and has been declining for 2+ consecutive turns.
        This is the GOOD ending — mission accomplished.
        """
        if len(self._turns) < 3:
            return None

        turns_since_peak = (len(self._turns) - 1) - self._peak_turn

        if turns_since_peak < 2:
            return None

        # Verify it's genuinely declining (not just flat)
        recent_scores = [t.v_score for t in self._turns[-3:]]
        declining = all(
            recent_scores[i] >= recent_scores[i + 1]
            for i in range(len(recent_scores) - 1)
        )
        if not declining:
            return None

        strength = min(1.0, turns_since_peak / 4.0)

        return SaturationSignal(
            type="completion",
            message=(
                f"V-Score peaked at turn {self._peak_turn + 1} "
                f"({self._peak_v_score:.2f}) and has declined for "
                f"{turns_since_peak} turn(s). Natural completion."
            ),
            strength=strength,
        )

    # ------------------------------------------------------------------
    # Goodbye formatting
    # ------------------------------------------------------------------

    def _build_ring_summary(self) -> str:
        """Summarise what grew in this conversation."""
        n_turns = len(self._turns)
        total_insights = sum(t.insight_count for t in self._turns)
        peak_score = self._peak_v_score
        # Take the most frequent topics as a proxy for what was discussed
        topic_sample = self._all_topics[:5]
        topics_str = ", ".join(topic_sample) if topic_sample else "several threads"

        if total_insights == 0:
            return f"After {n_turns} turns, the ring is in the processing phase — not every ring is visible yet."

        return (
            f"Your ring grew: {total_insights} insight(s) across {n_turns} turns "
            f"(peak V-Score {peak_score:.2f}, themes: {topics_str})."
        )

    def format_goodbye(
        self,
        signals: list[SaturationSignal],
        ring_summary: str,
    ) -> str:
        """Format a warm, empowering goodbye message.

        NOT: "Session ended."
        BUT: "You came in with something. Now you have a ring. Go live it."

        The goodbye is the most important moment — it is what the user
        carries back into the real world.
        """
        if not signals:
            return _GOODBYE_GENERIC.format(ring_summary=ring_summary)

        # Dominant signal drives the tone
        dominant = max(signals, key=lambda s: s.strength)

        if dominant.type == "topic_loop":
            return _GOODBYE_LOOP + "\n\n" + ring_summary

        if dominant.type == "insight_plateau":
            return _GOODBYE_PLATEAU.format(ring_summary=ring_summary)

        if dominant.type == "energy_drain":
            return _GOODBYE_DRAIN.format(ring_summary=ring_summary)

        if dominant.type == "completion":
            return _GOODBYE_COMPLETION.format(ring_summary=ring_summary)

        return _GOODBYE_GENERIC.format(ring_summary=ring_summary)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def anti_addiction_demo() -> None:
    """Demo: simulate a conversation that gradually saturates.

    Turns 1-4: productive, increasing V-score, fresh topics.
    Turns 5-8: topics repeat, no new insights, V-score falling.
    Expected: saturation detected around turn 6-7.
    """
    print("=" * 60)
    print("VOID Anti-Addiction Engine — Demo")
    print("=" * 60)
    print()

    sensor = SaturationSensor()

    # Simulated turns: (user_text, v_score, ruhe_druck, insight_count)
    turns = [
        # Productive phase — fresh, high energy, insights flowing
        ("I feel stuck in my career and don't know what direction to take",
         0.50, 0.60, 2),
        ("Maybe the problem is that I keep comparing myself to others at work",
         0.65, 0.55, 3),
        ("I think I actually do want to build something of my own not just work for someone",
         0.80, 0.45, 4),  # peak turn
        ("There's this idea I've had for years about helping people with learning",
         0.75, 0.48, 2),
        # Looping phase — same topics, no new insights, stress rising
        ("But I'm stuck again, career choices are hard, don't know direction",
         0.60, 0.55, 0),
        ("I keep comparing myself to others and it's exhausting, career stuff",
         0.50, 0.65, 0),
        ("Still stuck on direction and career, comparing myself again",
         0.40, 0.75, 0),
        ("I don't know, same questions about career and direction and comparing",
         0.30, 0.82, 0),
    ]

    for i, (text, v_score, ruhe_druck, insight_count) in enumerate(turns):
        coord = HexCoord(ruhe_druck=ruhe_druck)
        insights = [f"insight_{j}" for j in range(insight_count)]

        sensor.record_turn(
            user_text=text,
            v_score=v_score,
            hex_coord=coord,
            insights=insights,
        )

        state = sensor.sense()

        print(f"Turn {i + 1}")
        print(f"  User: \"{text[:70]}{'...' if len(text) > 70 else ''}\"")
        print(f"  V-Score: {v_score:.2f} | Stress: {ruhe_druck:.2f} | Insights: {insight_count}")
        print(f"  Saturation: {state.saturation_level:.2f} | Saturated: {state.saturated}")

        if state.signals:
            for sig in state.signals:
                print(f"  [{sig.type.upper()}] strength={sig.strength:.2f}: {sig.message}")

        if state.saturated:
            print()
            print("  >>> VOID SAYS GOODBYE <<<")
            print()
            for line in state.suggestion.split("\n"):
                print(f"  {line}")
            print()
            print(f"  (Ring: {state.ring_summary})")
            print()
            break

        print()

    print("=" * 60)
    print("This is the feature that proves VOID loves the user.")
    print("Not engagement. Not retention. Life.")
    print("=" * 60)


if __name__ == "__main__":
    anti_addiction_demo()
