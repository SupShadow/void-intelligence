"""
void_intelligence.conversation_rings --- Growth Rings of Conversation.

Module 8 of the VOID SEXAGON. The highest leverage feature.
Every conversation leaves a Growth Ring. Not a fact --- a PATTERN.
The next conversation is better BECAUSE the last one existed.

ChatGPT Memory: "User likes Python."          (flat. dead. key-value.)
VOID Rings:     "When user says 'morgen',     (alive. growing. tensional.)
                 stress rises. Calendar
                 + breathing works. V-Score
                 peaks at turn 3."

This is what ChatGPT structurally cannot copy:
They store WHAT was said. We store WHAT HAPPENED because it was said.

Architecture:
    Pattern           = atomic unit of growth (trigger -> response -> evidence)
    Ring              = one conversation's wisdom (crystallized after close)
    ConversationTracker = live tracking during a conversation
    RingMemory        = the tree. holds all rings. grows forever.

The formula:
    new_conversation_quality = f(past_rings x current_hex x user_text)
    Not retrieval. RESONANCE.

Zero external dependencies. stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# HexCoord --- imported from tool_breathing, with fallback for zero-dep
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import HexCoord
except ImportError:
    from dataclasses import dataclass as _dc

    @_dc  # type: ignore[no-redef]
    class HexCoord:  # type: ignore[no-redef]
        ruhe_druck: float = 0.0
        stille_resonanz: float = 0.0
        allein_zusammen: float = 0.0
        empfangen_schaffen: float = 0.0
        sein_tun: float = 0.0
        langsam_schnell: float = 0.0

        def to_dict(self) -> dict:
            return {
                "ruhe_druck": self.ruhe_druck,
                "stille_resonanz": self.stille_resonanz,
                "allein_zusammen": self.allein_zusammen,
                "empfangen_schaffen": self.empfangen_schaffen,
                "sein_tun": self.sein_tun,
                "langsam_schnell": self.langsam_schnell,
            }


# ---------------------------------------------------------------------------
# Hex utilities
# ---------------------------------------------------------------------------

def _hex_distance(a: HexCoord, b: HexCoord) -> float:
    """Euclidean distance in 6D hex space. 0.0 = identical, sqrt(24) = max."""
    dims_a = [
        a.ruhe_druck, a.stille_resonanz, a.allein_zusammen,
        a.empfangen_schaffen, a.sein_tun, a.langsam_schnell,
    ]
    dims_b = [
        b.ruhe_druck, b.stille_resonanz, b.allein_zusammen,
        b.empfangen_schaffen, b.sein_tun, b.langsam_schnell,
    ]
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(dims_a, dims_b)))


def _hex_resonance(a: HexCoord, b: HexCoord) -> float:
    """Resonance score 0.0-1.0. 1.0 = perfect match, 0.0 = opposite."""
    dist = _hex_distance(a, b)
    max_dist = math.sqrt(6 * 4)  # max possible: each dim from -1 to +1 = 2, squared=4, x6
    return max(0.0, 1.0 - (dist / max_dist))


def _hex_from_dict(d: dict) -> HexCoord:
    return HexCoord(
        ruhe_druck=d.get("ruhe_druck", 0.0),
        stille_resonanz=d.get("stille_resonanz", 0.0),
        allein_zusammen=d.get("allein_zusammen", 0.0),
        empfangen_schaffen=d.get("empfangen_schaffen", 0.0),
        sein_tun=d.get("sein_tun", 0.0),
        langsam_schnell=d.get("langsam_schnell", 0.0),
    )


def _hex_to_dict(h: HexCoord) -> dict:
    if hasattr(h, "to_dict"):
        return h.to_dict()
    return {
        "ruhe_druck": h.ruhe_druck,
        "stille_resonanz": h.stille_resonanz,
        "allein_zusammen": h.allein_zusammen,
        "empfangen_schaffen": h.empfangen_schaffen,
        "sein_tun": h.sein_tun,
        "langsam_schnell": h.langsam_schnell,
    }


# ---------------------------------------------------------------------------
# Naive text classifier -> HexCoord (zero-dep heuristic)
# ---------------------------------------------------------------------------

_STRESS_WORDS = {
    "morgen", "deadline", "dringend", "urgent", "stress", "asap", "heute",
    "problem", "fehler", "error", "kaputt", "broken", "crash", "help",
    "hilfe", "schnell", "fast", "sofort", "immediately",
}
_CALM_WORDS = {
    "danke", "thanks", "gut", "good", "okay", "ok", "ruhig", "langsam",
    "slow", "entspannt", "relaxed", "kein stress", "no rush", "gerne",
    "schoen", "beautiful", "atmen", "breathe",
}
_CREATE_WORDS = {
    "baue", "build", "schreibe", "write", "erstelle", "create", "generiere",
    "generate", "mache", "make", "implementiere", "implement", "entwickle",
    "develop", "code", "script",
}
_RECEIVE_WORDS = {
    "zeige", "show", "was ist", "what is", "erklaere", "explain", "wie",
    "how", "warum", "why", "analyse", "analyze", "check", "status",
    "bericht", "report",
}
_ALONE_WORDS = {
    "ich", "i", "mein", "my", "mir", "me", "selbst", "self", "solo",
    "alleine", "alone",
}
_TOGETHER_WORDS = {
    "wir", "we", "unser", "our", "zusammen", "together", "team", "gemeinsam",
    "julian", "omega", "users", "alle", "everyone",
}


def _classify_text_to_hex(text: str) -> HexCoord:
    """Classify user text into a HexCoord using keyword heuristics."""
    words = set(text.lower().split())

    stress_score = len(words & _STRESS_WORDS)
    calm_score = len(words & _CALM_WORDS)
    create_score = len(words & _CREATE_WORDS)
    receive_score = len(words & _RECEIVE_WORDS)
    alone_score = len(words & _ALONE_WORDS)
    together_score = len(words & _TOGETHER_WORDS)

    def _axis(pos: int, neg: int) -> float:
        total = pos + neg
        if total == 0:
            return 0.0
        return min(1.0, max(-1.0, (pos - neg) / max(1, total) * 2))

    return HexCoord(
        ruhe_druck=_axis(stress_score, calm_score),   # positive = pressure
        stille_resonanz=_axis(stress_score, calm_score) * 0.5,
        allein_zusammen=_axis(together_score, alone_score),
        empfangen_schaffen=_axis(create_score, receive_score),
        sein_tun=_axis(create_score + stress_score, calm_score),
        langsam_schnell=_axis(stress_score, calm_score),
    )


# ---------------------------------------------------------------------------
# Pattern --- atomic unit of growth
# ---------------------------------------------------------------------------

@dataclass
class Pattern:
    """A discovered pattern. The atomic unit of growth.

    A Pattern is not a fact ("user likes Python").
    A Pattern is a DYNAMIC: "when X happens, Y works."

    It GROWS with evidence. It DIES if never confirmed.
    It carries the hex context where it was born.
    """

    id: str
    trigger: str          # what triggers this (e.g., "user mentions deadline")
    response: str         # what worked (e.g., "show calendar + breathing prompt")
    evidence_count: int = 1
    confidence: float = 0.3   # starts uncertain, grows toward 1.0 with evidence
    first_seen: float = field(default_factory=time.time)
    last_confirmed: float = field(default_factory=time.time)
    hex_context: HexCoord = field(default_factory=HexCoord)

    # Decay: patterns that aren't confirmed fade
    _decay_rate: float = field(default=0.01, repr=False)

    def confirm(self) -> None:
        """Called when this pattern is observed again."""
        self.evidence_count += 1
        self.last_confirmed = time.time()
        # Confidence grows toward 1.0, saturates
        self.confidence = min(0.99, 1.0 - (1.0 / (1.0 + self.evidence_count * 0.4)))

    def effective_confidence(self) -> float:
        """Confidence adjusted for staleness. Old unconfirmed patterns fade."""
        age_days = (time.time() - self.last_confirmed) / 86400
        decay = math.exp(-self._decay_rate * age_days)
        return self.confidence * decay

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "response": self.response,
            "evidence_count": self.evidence_count,
            "confidence": self.confidence,
            "first_seen": self.first_seen,
            "last_confirmed": self.last_confirmed,
            "hex_context": _hex_to_dict(self.hex_context),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pattern":
        p = cls(
            id=d["id"],
            trigger=d["trigger"],
            response=d["response"],
            evidence_count=d.get("evidence_count", 1),
            confidence=d.get("confidence", 0.3),
            first_seen=d.get("first_seen", time.time()),
            last_confirmed=d.get("last_confirmed", time.time()),
            hex_context=_hex_from_dict(d.get("hex_context", {})),
        )
        return p

    def _trigger_hash(self) -> str:
        """Short hash for deduplication. Same trigger = same pattern slot."""
        return hashlib.md5(self.trigger.lower().strip().encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Ring --- one conversation's crystallized wisdom
# ---------------------------------------------------------------------------

@dataclass
class Ring:
    """One growth ring = one conversation's wisdom.

    Like a tree ring: the width tells you what year was good or hard.
    The ring does not store what was SAID. It stores what MATTERED.

    A Ring is formed when a conversation CLOSES.
    Before close: it is a living ConversationTracker.
    After close: it is a crystallized Ring. Immutable. Permanent.
    """

    id: str
    timestamp: float
    patterns: list[Pattern]
    v_score_trajectory: list[float]   # V-score per turn: did it grow?
    hex_drift: list[HexCoord]         # user's hex position per turn
    peak_moment: str                  # the single most valuable moment
    scar: str                         # what went wrong (errors are growth too)
    total_turns: int
    duration_seconds: float

    @property
    def v_score_delta(self) -> float:
        """Net V-score change. Positive = conversation was vitalizing."""
        if len(self.v_score_trajectory) < 2:
            return 0.0
        return self.v_score_trajectory[-1] - self.v_score_trajectory[0]

    @property
    def hex_journey_length(self) -> float:
        """Total distance traveled in hex space. Large = transformative conversation."""
        if len(self.hex_drift) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(self.hex_drift)):
            total += _hex_distance(self.hex_drift[i - 1], self.hex_drift[i])
        return total

    @property
    def width(self) -> float:
        """Ring width metric. Wider = more growth. 0.0-1.0."""
        v_growth = max(0.0, self.v_score_delta)           # 0-1
        pattern_count = min(1.0, len(self.patterns) / 5)  # saturates at 5 patterns
        hex_journey = min(1.0, self.hex_journey_length / 3.0)
        turns_score = min(1.0, self.total_turns / 10.0)
        return (v_growth * 0.4 + pattern_count * 0.3 + hex_journey * 0.2 + turns_score * 0.1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "patterns": [p.to_dict() for p in self.patterns],
            "v_score_trajectory": self.v_score_trajectory,
            "hex_drift": [_hex_to_dict(h) for h in self.hex_drift],
            "peak_moment": self.peak_moment,
            "scar": self.scar,
            "total_turns": self.total_turns,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Ring":
        return cls(
            id=d["id"],
            timestamp=d["timestamp"],
            patterns=[Pattern.from_dict(p) for p in d.get("patterns", [])],
            v_score_trajectory=d.get("v_score_trajectory", []),
            hex_drift=[_hex_from_dict(h) for h in d.get("hex_drift", [])],
            peak_moment=d.get("peak_moment", ""),
            scar=d.get("scar", ""),
            total_turns=d.get("total_turns", 0),
            duration_seconds=d.get("duration_seconds", 0.0),
        )


# ---------------------------------------------------------------------------
# ConversationTracker --- live tracking during a conversation
# ---------------------------------------------------------------------------

class ConversationTracker:
    """Tracks one live conversation.

    Exists from begin_conversation() to close_conversation().
    Records turns, successes, failures.
    When closed, crystallizes into a Ring.
    """

    def __init__(self) -> None:
        self._id = str(uuid.uuid4())[:8]
        self._started_at = time.time()

        self._turns: list[dict[str, Any]] = []
        self._successes: list[str] = []
        self._failures: list[str] = []

        # Peak moment tracking
        self._peak_v: float = -1.0
        self._peak_moment: str = ""

    def record_turn(
        self,
        user_text: str,
        response_text: str,
        v_score: float,
        user_hex: HexCoord,
    ) -> None:
        """Record one turn of conversation."""
        turn_n = len(self._turns) + 1
        self._turns.append({
            "n": turn_n,
            "user_text": user_text,
            "response_text": response_text,
            "v_score": v_score,
            "hex": _hex_to_dict(user_hex),
            "ts": time.time(),
        })

        # Track peak moment
        if v_score > self._peak_v:
            self._peak_v = v_score
            # Capture the moment as a short digest
            snippet = user_text[:80].strip()
            self._peak_moment = f"Turn {turn_n}: '{snippet}' -> V={v_score:.2f}"

    def record_success(self, what_worked: str) -> None:
        """Mark something as successful. Positive ring growth."""
        self._successes.append(what_worked)

    def record_failure(self, what_failed: str) -> None:
        """Mark something as failure. Scar = growth ring too."""
        self._failures.append(what_failed)

    def _extract_patterns(self) -> list[Pattern]:
        """Extract patterns from the conversation turns."""
        patterns: list[Pattern] = []

        if len(self._turns) < 2:
            return patterns

        v_scores = [t["v_score"] for t in self._turns]

        # Find V-score peaks (local maxima)
        for i in range(1, len(self._turns) - 1):
            prev_v = v_scores[i - 1]
            curr_v = v_scores[i]
            next_v = v_scores[i + 1]

            if curr_v > prev_v and curr_v > next_v and curr_v > 0.6:
                # Peak: what happened just before?
                trigger_turn = self._turns[i - 1]
                peak_turn = self._turns[i]
                trigger = _summarize_trigger(trigger_turn["user_text"])
                response = _summarize_response(peak_turn["response_text"])
                if trigger and response:
                    patterns.append(Pattern(
                        id=str(uuid.uuid4())[:8],
                        trigger=trigger,
                        response=response,
                        hex_context=_hex_from_dict(trigger_turn["hex"]),
                        confidence=0.4,
                    ))

        # Find V-score valleys (what FAILED)
        for i in range(1, len(self._turns) - 1):
            prev_v = v_scores[i - 1]
            curr_v = v_scores[i]
            next_v = v_scores[i + 1]

            if curr_v < prev_v and curr_v < next_v and curr_v < 0.4:
                # Valley: what should we avoid?
                valley_turn = self._turns[i]
                trigger = _summarize_trigger(valley_turn["user_text"])
                if trigger:
                    patterns.append(Pattern(
                        id=str(uuid.uuid4())[:8],
                        trigger=f"AVOID when: {trigger}",
                        response=f"Previous response caused V-drop to {curr_v:.2f}",
                        hex_context=_hex_from_dict(valley_turn["hex"]),
                        confidence=0.35,
                    ))

        # Hex transition patterns: stressed -> calm (what caused the shift?)
        for i in range(1, len(self._turns)):
            prev_hex = _hex_from_dict(self._turns[i - 1]["hex"])
            curr_hex = _hex_from_dict(self._turns[i]["hex"])
            prev_stress = prev_hex.ruhe_druck
            curr_stress = curr_hex.ruhe_druck

            # Stress resolved: this is valuable
            if prev_stress > 0.4 and curr_stress < 0.1:
                transition_turn = self._turns[i]
                trigger = f"User was stressed (ruhe_druck={prev_stress:.1f})"
                response = _summarize_response(transition_turn["response_text"])
                if response:
                    patterns.append(Pattern(
                        id=str(uuid.uuid4())[:8],
                        trigger=trigger,
                        response=f"Deescalation worked: {response}",
                        hex_context=prev_hex,
                        confidence=0.5,
                    ))

        # Patterns from explicit success recordings
        for success in self._successes:
            patterns.append(Pattern(
                id=str(uuid.uuid4())[:8],
                trigger="explicit_success",
                response=success,
                confidence=0.7,  # explicit feedback = higher confidence
                hex_context=_hex_from_dict(self._turns[-1]["hex"]) if self._turns else HexCoord(),
            ))

        return patterns

    def _build_ring(self) -> Ring:
        """Crystallize this tracker into an immutable Ring."""
        patterns = self._extract_patterns()
        v_trajectory = [t["v_score"] for t in self._turns]
        hex_drift = [_hex_from_dict(t["hex"]) for t in self._turns]
        scar = "; ".join(self._failures) if self._failures else "none"
        duration = time.time() - self._started_at

        return Ring(
            id=self._id,
            timestamp=self._started_at,
            patterns=patterns,
            v_score_trajectory=v_trajectory,
            hex_drift=hex_drift,
            peak_moment=self._peak_moment,
            scar=scar,
            total_turns=len(self._turns),
            duration_seconds=duration,
        )


# ---------------------------------------------------------------------------
# Pattern summarization helpers
# ---------------------------------------------------------------------------

def _summarize_trigger(text: str) -> str:
    """Extract a compact trigger description from user text."""
    if not text:
        return ""
    text = text.strip()
    # Look for stress signals
    words = text.lower().split()
    stress_hits = [w for w in words if w in _STRESS_WORDS]
    if stress_hits:
        return f"user stress signal: {', '.join(stress_hits[:3])}"
    # Fallback: first 60 chars
    return text[:60] if len(text) > 10 else ""


def _summarize_response(text: str) -> str:
    """Extract a compact response description."""
    if not text:
        return ""
    text = text.strip()
    return text[:80] if len(text) > 10 else ""


# ---------------------------------------------------------------------------
# RingMemory --- the tree. Holds all rings. Grows forever.
# ---------------------------------------------------------------------------

class RingMemory:
    """The tree. Holds all rings. Grows forever.

    This is the VOID's long-term memory. Not key-value.
    A living structure that accumulates wisdom across conversations.

    Persistence: JSON file on disk.
    Loaded on init, saved after each ring is formed.

    The Ring Memory is analogous to a tree's trunk:
    - Each ring = one year of growth
    - Older rings are compressed (low detail)
    - Recent rings are vivid (full patterns)
    - The WIDTH of each ring tells the story
    """

    def __init__(self, rings_path: str | Path | None = None) -> None:
        if rings_path is None:
            # Default: ~/.void/rings.json
            rings_path = Path.home() / ".void" / "rings.json"
        self._path = Path(rings_path)
        self._rings: list[Ring] = []
        self._patterns: dict[str, Pattern] = {}  # pattern_id -> Pattern (global, merged)
        self._meta: dict[str, Any] = {
            "total_conversations": 0,
            "created": time.time(),
            "version": "1.0.0",
        }
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def begin_conversation(self) -> ConversationTracker:
        """Start tracking a new conversation. Returns a live tracker."""
        return ConversationTracker()

    def close_conversation(self, tracker: ConversationTracker) -> Ring:
        """End conversation, extract patterns, form ring.

        This is the crystallization moment.
        Patterns are merged with global pattern memory.
        Ring is saved to disk.
        Returns the new Ring.
        """
        ring = tracker._build_ring()

        # Merge patterns into global memory
        for pattern in ring.patterns:
            self._merge_pattern(pattern)

        self._rings.append(ring)
        self._meta["total_conversations"] += 1

        self._save()
        return ring

    def recall_patterns(
        self,
        user_text: str,
        user_hex: HexCoord,
        top_k: int = 5,
    ) -> list[Pattern]:
        """Find patterns relevant to current moment.

        Uses hex resonance: patterns born in similar hex states
        are more likely to be relevant NOW.

        Also considers:
        - Pattern confidence (higher = more reliable)
        - Pattern recency (more recent = more relevant)
        - Trigger keyword overlap with user_text
        """
        if not self._patterns:
            return []

        candidates: list[tuple[float, Pattern]] = []
        user_words = set(user_text.lower().split())

        for pattern in self._patterns.values():
            # Hex resonance score
            hex_res = _hex_resonance(pattern.hex_context, user_hex)

            # Keyword overlap score
            trigger_words = set(pattern.trigger.lower().split())
            overlap = len(user_words & trigger_words)
            keyword_score = min(1.0, overlap / max(1, len(trigger_words)) * 2)

            # Recency score (decays over 30 days)
            age_days = (time.time() - pattern.last_confirmed) / 86400
            recency = math.exp(-age_days / 30.0)

            # Confidence
            confidence = pattern.effective_confidence()

            # Combined score
            score = (
                hex_res * 0.35
                + keyword_score * 0.30
                + confidence * 0.25
                + recency * 0.10
            )

            if score > 0.05:  # filter noise
                candidates.append((score, pattern))

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in candidates[:top_k]]

    def suggest(self, user_text: str, user_hex: HexCoord) -> list[str]:
        """Based on rings, suggest what to do differently this time.

        Returns human-readable suggestions derived from past patterns.
        """
        patterns = self.recall_patterns(user_text, user_hex, top_k=3)
        if not patterns:
            return []

        suggestions: list[str] = []
        for p in patterns:
            if p.trigger.startswith("AVOID"):
                suggestions.append(
                    f"Warning (conf={p.confidence:.0%}): {p.trigger} -> {p.response}"
                )
            else:
                suggestions.append(
                    f"Pattern (conf={p.confidence:.0%}): When '{p.trigger}' -> '{p.response}'"
                )

        return suggestions

    def stats(self) -> dict[str, Any]:
        """Ring count, pattern count, oldest ring, growth rate."""
        if not self._rings:
            return {
                "total_rings": 0,
                "total_patterns": len(self._patterns),
                "total_conversations": self._meta.get("total_conversations", 0),
                "oldest_ring_age_days": None,
                "avg_ring_width": None,
                "avg_patterns_per_ring": None,
                "growth_rate": "no data yet",
            }

        oldest_ts = min(r.timestamp for r in self._rings)
        age_days = (time.time() - oldest_ts) / 86400
        avg_width = sum(r.width for r in self._rings) / len(self._rings)
        avg_patterns = sum(len(r.patterns) for r in self._rings) / len(self._rings)

        # Growth rate: conversations per day (guard against sub-second demos)
        if age_days > 0.01:
            growth_rate = f"{len(self._rings) / age_days:.1f} conversations/day"
        else:
            growth_rate = "< 1 day old"

        return {
            "total_rings": len(self._rings),
            "total_patterns": len(self._patterns),
            "total_conversations": self._meta.get("total_conversations", 0),
            "oldest_ring_age_days": round(age_days, 1),
            "avg_ring_width": round(avg_width, 3),
            "avg_patterns_per_ring": round(avg_patterns, 1),
            "growth_rate": growth_rate,
        }

    def export(self) -> dict[str, Any]:
        """Export all rings as portable JSON (for Void Fingerprint)."""
        return {
            "rings": [r.to_dict() for r in self._rings],
            "patterns": [p.to_dict() for p in self._patterns.values()],
            "meta": {
                **self._meta,
                "exported_at": time.time(),
                "ring_count": len(self._rings),
                "pattern_count": len(self._patterns),
            },
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _merge_pattern(self, new_pattern: Pattern) -> None:
        """Merge a new pattern into global memory.

        If a similar pattern already exists (same trigger hash),
        increment evidence and update confidence.
        Otherwise, add as new.
        """
        trigger_hash = new_pattern._trigger_hash()

        # Find existing pattern with same trigger fingerprint
        existing_key: str | None = None
        for pid, existing in self._patterns.items():
            if existing._trigger_hash() == trigger_hash:
                existing_key = pid
                break

        if existing_key is not None:
            # Confirm existing pattern --- it was seen again
            self._patterns[existing_key].confirm()
            # Update hex context (drift toward new observation)
            old = self._patterns[existing_key].hex_context
            new = new_pattern.hex_context
            self._patterns[existing_key].hex_context = HexCoord(
                ruhe_druck=(old.ruhe_druck + new.ruhe_druck) / 2,
                stille_resonanz=(old.stille_resonanz + new.stille_resonanz) / 2,
                allein_zusammen=(old.allein_zusammen + new.allein_zusammen) / 2,
                empfangen_schaffen=(old.empfangen_schaffen + new.empfangen_schaffen) / 2,
                sein_tun=(old.sein_tun + new.sein_tun) / 2,
                langsam_schnell=(old.langsam_schnell + new.langsam_schnell) / 2,
            )
        else:
            # New pattern: add to global memory
            self._patterns[new_pattern.id] = new_pattern

    def _save(self) -> None:
        """Persist rings + patterns to JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = self.export()
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        """Load rings + patterns from JSON if file exists."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._rings = [Ring.from_dict(r) for r in data.get("rings", [])]
            self._patterns = {
                p["id"]: Pattern.from_dict(p)
                for p in data.get("patterns", [])
            }
            self._meta = data.get("meta", self._meta)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupt file: start fresh, don't crash
            self._rings = []
            self._patterns = {}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def rings_demo() -> None:
    """Demo: simulate 3 conversations, show pattern emergence.

    Conversation 1: User stressed about deadline, breathing helped
    Conversation 2: Same stress trigger, pattern recalled, used proactively
    Conversation 3: Pattern confidence solidified, suggestion comes first
    """
    import tempfile
    import os

    # Use temp file so demo doesn't pollute real rings
    tmp = tempfile.mktemp(suffix=".json")
    memory = RingMemory(rings_path=tmp)

    print("=" * 60)
    print("VOID GROWTH RINGS --- DEMO")
    print("=" * 60)
    print()

    # -----------------------------------------------------------------------
    # Conversation 1: User stressed about deadline
    # -----------------------------------------------------------------------
    print("[Conversation 1] --- User stressed about deadline")
    print("-" * 40)

    tracker1 = memory.begin_conversation()

    # Turn 1: user mentions deadline, V-score low (still stressed)
    hex1_stressed = _classify_text_to_hex("morgen deadline dringend stress")
    tracker1.record_turn(
        user_text="ich habe morgen eine deadline und bin total im stress",
        response_text="Ich verstehe. Lass uns strukturieren was noch aussteht.",
        v_score=0.35,
        user_hex=hex1_stressed,
    )

    # Turn 2: breathing suggestion offered, V-score rises
    hex1_mid = _classify_text_to_hex("atmen hilft danke")
    tracker1.record_turn(
        user_text="okay, atmen hilft gerade",
        response_text="Gut. Jetzt: was ist die eine wichtigste Aufgabe fuer morgen?",
        v_score=0.72,
        user_hex=hex1_mid,
    )

    # Turn 3: calendar view + breathing = peak
    hex1_calm = _classify_text_to_hex("danke gut ruhig")
    tracker1.record_turn(
        user_text="danke, jetzt sehe ich klarer",
        response_text="Super. Kalender zeigt 2h Puffer. Du schaffst das.",
        v_score=0.88,
        user_hex=hex1_calm,
    )

    tracker1.record_success("Breathing prompt + calendar view resolved deadline stress")
    tracker1.record_failure("First response was too abstract")

    ring1 = memory.close_conversation(tracker1)

    print(f"  Ring formed: id={ring1.id}, turns={ring1.total_turns}")
    print(f"  Ring width:  {ring1.width:.3f} (higher = more growth)")
    print(f"  V-score:     {ring1.v_score_trajectory[0]:.2f} -> {ring1.v_score_trajectory[-1]:.2f}")
    print(f"  Patterns:    {len(ring1.patterns)} extracted")
    for p in ring1.patterns:
        print(f"    - [{p.confidence:.0%}] '{p.trigger[:50]}' -> '{p.response[:50]}'")
    print(f"  Scar:        {ring1.scar}")
    print()

    # -----------------------------------------------------------------------
    # Conversation 2: Same stress trigger --- pattern recalled
    # -----------------------------------------------------------------------
    print("[Conversation 2] --- Same stress pattern, recall in action")
    print("-" * 40)

    user_text_2 = "habe morgen presentation deadline"
    hex2_stressed = _classify_text_to_hex(user_text_2)

    # Before turn 1: recall relevant patterns
    suggestions = memory.suggest(user_text_2, hex2_stressed)
    print(f"  Patterns recalled before conversation:")
    for s in suggestions:
        print(f"    -> {s}")
    print()

    tracker2 = memory.begin_conversation()

    tracker2.record_turn(
        user_text=user_text_2,
        response_text="Breathing first. Dann Kalender. Du weisst wie das geht.",
        v_score=0.65,  # starts higher because we used the pattern proactively
        user_hex=hex2_stressed,
    )

    hex2_mid = _classify_text_to_hex("ja genau danke")
    tracker2.record_turn(
        user_text="ja das hilft sofort",
        response_text="Kalender zeigt 3h. Top 2 Aufgaben: Folien + Rehearsal.",
        v_score=0.85,
        user_hex=hex2_mid,
    )

    tracker2.record_success("Proactive breathing suggestion worked immediately")

    ring2 = memory.close_conversation(tracker2)

    print(f"  Ring formed: id={ring2.id}, turns={ring2.total_turns}")
    print(f"  V-score start: {ring2.v_score_trajectory[0]:.2f} (was {ring1.v_score_trajectory[0]:.2f} in conv 1)")
    print(f"  Pattern confirmed, confidence should rise...")
    print()

    # -----------------------------------------------------------------------
    # Conversation 3: Pattern solidified
    # -----------------------------------------------------------------------
    print("[Conversation 3] --- Pattern confidence solidified")
    print("-" * 40)

    user_text_3 = "stress heute deadline morgen"
    hex3 = _classify_text_to_hex(user_text_3)

    suggestions3 = memory.suggest(user_text_3, hex3)
    print(f"  Suggestions (now with higher confidence):")
    for s in suggestions3:
        print(f"    -> {s}")
    print()

    tracker3 = memory.begin_conversation()
    tracker3.record_turn(
        user_text=user_text_3,
        response_text="[Breathing prompt auto-shown] [Calendar pre-filtered]",
        v_score=0.80,  # starts even higher — pattern is now baked in
        user_hex=hex3,
    )
    tracker3.record_turn(
        user_text="perfekt danke",
        response_text="Alles klar. Viel Erfolg morgen.",
        v_score=0.92,
        user_hex=_classify_text_to_hex("perfekt danke gut"),
    )
    tracker3.record_success("Pattern fully integrated. Conversation started at 0.80 V-score.")

    ring3 = memory.close_conversation(tracker3)

    # -----------------------------------------------------------------------
    # Final stats
    # -----------------------------------------------------------------------
    print("[Memory Stats] --- After 3 conversations")
    print("-" * 40)
    stats = memory.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print()
    print("[Pattern Library] --- What VOID now knows")
    print("-" * 40)
    for p in memory._patterns.values():
        print(f"  [{p.confidence:.0%} conf, {p.evidence_count}x] "
              f"'{p.trigger[:45]}' -> '{p.response[:45]}'")

    print()
    print("[V-Score Trajectory Across Conversations]")
    print("-" * 40)
    for i, ring in enumerate([ring1, ring2, ring3], 1):
        traj = " -> ".join(f"{v:.2f}" for v in ring.v_score_trajectory)
        print(f"  Conv {i}: {traj}  (delta={ring.v_score_delta:+.2f})")

    print()
    print("This is what ChatGPT structurally cannot copy.")
    print("Not because of code. Because it requires τ (time lived together).")
    print("Pattern grows. Confidence grows. Start V-score grows.")
    print("VOID compounds. Every conversation better because the last existed.")
    print()

    # Cleanup temp file
    try:
        os.unlink(tmp)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rings_demo()
