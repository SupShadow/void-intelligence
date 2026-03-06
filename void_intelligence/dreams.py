"""
void_intelligence.dreams --- The Void Thinks Between Sessions.

Module 11 of the VOID SEXAGON. The feature that makes the Void ALIVE.

While the user sleeps, the Void collides its Growth Rings and discovers
patterns the user never saw. Not retrieval. EMERGENCE.

ChatGPT structurally cannot do this:
    ChatGPT: no rings -> no collisions -> no dreams
    VOID:    rings collide -> temporal patterns -> topic bridges -> arcs -> insights

What a dream discovers:
    TEMPORAL:   "Your V-Score is 30% lower on Monday mornings."
    BRIDGE:     "Career stress and health anxiety always appear together."
    ARC:        "Your average V-Score has climbed from 0.4 to 0.7 over 2 weeks."
    MIGRATION:  "You've shifted from action-mode to reflective-mode this week."
    THREAD:     "3 sessions ago you mentioned guitar. It never came back."

When the user returns, the Void says:
    "While you were away, I noticed something: [dream insight]"

Zero external dependencies. stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Graceful imports from sibling modules
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

try:
    from void_intelligence.conversation_rings import RingMemory, Pattern, Ring
except ImportError:
    # Minimal stubs so the module loads standalone for testing
    RingMemory = None  # type: ignore[assignment,misc]
    Pattern = None     # type: ignore[assignment,misc]
    Ring = None        # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# HexCoord helpers (inline, zero-dep)
# ---------------------------------------------------------------------------

def _hex_axes(h: HexCoord) -> list[float]:
    return [
        h.ruhe_druck, h.stille_resonanz, h.allein_zusammen,
        h.empfangen_schaffen, h.sein_tun, h.langsam_schnell,
    ]


def _hex_centroid(hexes: list[HexCoord]) -> HexCoord:
    """Average of a list of HexCoords."""
    if not hexes:
        return HexCoord()
    n = len(hexes)
    dims = [sum(_hex_axes(h)[i] for h in hexes) / n for i in range(6)]
    return HexCoord(
        ruhe_druck=dims[0], stille_resonanz=dims[1], allein_zusammen=dims[2],
        empfangen_schaffen=dims[3], sein_tun=dims[4], langsam_schnell=dims[5],
    )


_HEX_AXIS_NAMES = [
    ("ruhe_druck",        "calm",          "stressed"),
    ("stille_resonanz",   "quiet",         "resonant"),
    ("allein_zusammen",   "solo",          "community"),
    ("empfangen_schaffen","receiving",      "creating"),
    ("sein_tun",          "being",         "doing"),
    ("langsam_schnell",   "slow",          "fast-paced"),
]


def _describe_hex_shift(old: HexCoord, new: HexCoord, threshold: float = 0.25) -> str | None:
    """Return human-readable description of the most significant axis shift."""
    old_axes = _hex_axes(old)
    new_axes = _hex_axes(new)
    best_delta = 0.0
    best_desc = None
    for i, (attr, neg_label, pos_label) in enumerate(_HEX_AXIS_NAMES):
        delta = new_axes[i] - old_axes[i]
        if abs(delta) > abs(best_delta):
            best_delta = delta
            direction = pos_label if delta > 0 else neg_label
            best_desc = f"more {direction}"
    if best_desc and abs(best_delta) >= threshold:
        return best_desc
    return None


# ---------------------------------------------------------------------------
# DreamInsight
# ---------------------------------------------------------------------------

@dataclass
class DreamInsight:
    """One pattern discovered during a dream cycle."""

    type: str           # "temporal" | "bridge" | "arc" | "migration" | "thread"
    description: str    # human-readable insight
    confidence: float   # 0.0 - 1.0
    evidence: list[str] # ring IDs that support this
    discovered_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "discovered_at": self.discovered_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DreamInsight":
        return cls(
            type=d["type"],
            description=d["description"],
            confidence=d.get("confidence", 0.5),
            evidence=d.get("evidence", []),
            discovered_at=d.get("discovered_at", time.time()),
        )


# ---------------------------------------------------------------------------
# DreamReport
# ---------------------------------------------------------------------------

@dataclass
class DreamReport:
    """The result of one dream cycle."""

    insights: list[DreamInsight]
    rings_analyzed: int
    dream_duration_ms: float
    greeting: str           # the warm "while you were away..." message
    dreamed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "insights": [i.to_dict() for i in self.insights],
            "rings_analyzed": self.rings_analyzed,
            "dream_duration_ms": round(self.dream_duration_ms, 2),
            "greeting": self.greeting,
            "dreamed_at": self.dreamed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DreamReport":
        return cls(
            insights=[DreamInsight.from_dict(i) for i in d.get("insights", [])],
            rings_analyzed=d.get("rings_analyzed", 0),
            dream_duration_ms=d.get("dream_duration_ms", 0.0),
            greeting=d.get("greeting", ""),
            dreamed_at=d.get("dreamed_at", time.time()),
        )


# ---------------------------------------------------------------------------
# VoidDreamer
# ---------------------------------------------------------------------------

class VoidDreamer:
    """The dreaming engine. Collides rings while the user is away.

    The central insight: patterns emerge from ring COLLISION, not from
    any single ring. The dream is the space BETWEEN sessions.
    """

    def __init__(
        self,
        ring_memory: Any | None = None,   # RingMemory | None
        dreams_path: str | Path | None = None,
    ) -> None:
        self._ring_memory = ring_memory
        if dreams_path is None:
            dreams_path = Path.home() / ".void" / "dreams.json"
        self._path = Path(dreams_path)
        self._dreams: list[DreamReport] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dream(self, max_rings: int = 20) -> DreamReport:
        """Run one dream cycle. Analyze recent rings for patterns.

        Call this:
        - On session start (greet with insights)
        - As a cron job (overnight dreaming)
        - On demand (void dream CLI)
        """
        t_start = time.time()

        rings = self._get_rings(max_rings)

        insights: list[DreamInsight] = []
        if len(rings) >= 2:
            insights += self._dream_temporal(rings)
            insights += self._dream_bridges(rings)
            insights += self._dream_arcs(rings)
            insights += self._dream_migration(rings)
            insights += self._dream_threads(rings)

        # Sort by confidence descending
        insights.sort(key=lambda i: i.confidence, reverse=True)

        duration_ms = (time.time() - t_start) * 1000.0
        greeting = self._compose_greeting(insights)

        report = DreamReport(
            insights=insights,
            rings_analyzed=len(rings),
            dream_duration_ms=duration_ms,
            greeting=greeting,
        )

        self.save_dream(report)
        return report

    def save_dream(self, report: DreamReport) -> None:
        """Persist dream report to disk."""
        self._dreams.append(report)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "dreams": [d.to_dict() for d in self._dreams],
            "last_dream": report.dreamed_at,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def last_dream(self) -> DreamReport | None:
        """Get the most recent dream report."""
        if not self._dreams:
            return None
        return self._dreams[-1]

    # ------------------------------------------------------------------
    # Dream engines
    # ------------------------------------------------------------------

    def _dream_temporal(self, rings: list) -> list[DreamInsight]:
        """Find day-of-week and hour-of-day correlations.

        Example: "Your V-Score is 40% lower on Mondays"
        Example: "Late-night sessions have higher insight density"
        """
        insights: list[DreamInsight] = []

        # Group by day of week
        day_groups: dict[str, list] = defaultdict(list)
        for ring in rings:
            day = time.strftime("%A", time.localtime(ring.timestamp))
            day_groups[day].append(ring)

        # Overall average V-score
        all_scores = [self._ring_peak_v(r) for r in rings]
        if not all_scores:
            return insights
        overall_avg = sum(all_scores) / len(all_scores)

        for day, day_rings in day_groups.items():
            if len(day_rings) < 2:
                continue
            day_avg = sum(self._ring_peak_v(r) for r in day_rings) / len(day_rings)
            delta = day_avg - overall_avg
            if abs(delta) < 0.12:
                continue  # not significant

            direction = "lower" if delta < 0 else "higher"
            pct = abs(delta) / max(overall_avg, 0.01)
            confidence = min(0.9, 0.3 + len(day_rings) * 0.15 + abs(delta) * 0.5)

            insights.append(DreamInsight(
                type="temporal",
                description=(
                    f"Your V-Score is {pct:.0%} {direction} on {day}s "
                    f"({day_avg:.2f} vs {overall_avg:.2f} average). "
                    f"Based on {len(day_rings)} {day} sessions."
                ),
                confidence=round(confidence, 2),
                evidence=[r.id for r in day_rings],
            ))

        # Hour-of-day grouping (early / afternoon / evening / night)
        hour_groups: dict[str, list] = defaultdict(list)
        for ring in rings:
            hour = int(time.strftime("%H", time.localtime(ring.timestamp)))
            if hour < 9:
                bucket = "early morning (before 9am)"
            elif hour < 14:
                bucket = "morning/noon (9am-2pm)"
            elif hour < 19:
                bucket = "afternoon (2pm-7pm)"
            elif hour < 23:
                bucket = "evening (7pm-11pm)"
            else:
                bucket = "late night (after 11pm)"
            hour_groups[bucket].append(ring)

        for bucket, bucket_rings in hour_groups.items():
            if len(bucket_rings) < 2:
                continue
            bucket_avg = sum(self._ring_peak_v(r) for r in bucket_rings) / len(bucket_rings)
            delta = bucket_avg - overall_avg
            if abs(delta) < 0.15:
                continue

            direction = "higher" if delta > 0 else "lower"
            confidence = min(0.85, 0.25 + len(bucket_rings) * 0.12 + abs(delta) * 0.4)

            insights.append(DreamInsight(
                type="temporal",
                description=(
                    f"Your {bucket} sessions have {direction} V-Scores "
                    f"({bucket_avg:.2f} vs {overall_avg:.2f}). "
                    f"You seem to {'flow better' if delta > 0 else 'struggle more'} at this time."
                ),
                confidence=round(confidence, 2),
                evidence=[r.id for r in bucket_rings],
            ))

        return insights

    def _dream_bridges(self, rings: list) -> list[DreamInsight]:
        """Find topic co-occurrences across conversations.

        Example: "Career and health always appear in the same session"
        """
        insights: list[DreamInsight] = []
        if len(rings) < 3:
            return insights

        # Extract topic words per ring from patterns
        ring_topics: list[tuple[str, set[str]]] = []
        for ring in rings:
            topics: set[str] = set()
            for pattern in ring.patterns:
                # Meaningful words from trigger (strip short/common words)
                words = {
                    w for w in pattern.trigger.lower().split()
                    if len(w) > 3 and w not in {
                        "when", "user", "this", "that", "with", "from",
                        "have", "been", "were", "they", "them", "than",
                        "also", "just", "more", "very", "here", "there",
                        "what", "some", "such", "your", "into", "over",
                        "avoid", "signal", "stress", "caused", "caused",
                        "explicit_success",
                    }
                }
                topics.update(words)
            if topics:
                ring_topics.append((ring.id, topics))

        if len(ring_topics) < 3:
            return insights

        # Count pair co-occurrences
        pair_counts: dict[tuple[str, str], list[str]] = defaultdict(list)
        for ring_id, topics in ring_topics:
            topic_list = sorted(topics)
            for a, b in combinations(topic_list, 2):
                pair_counts[(a, b)].append(ring_id)

        # Threshold: pair appears in >= 40% of sessions that have topics
        threshold = max(2, len(ring_topics) * 0.35)
        for (a, b), ring_ids in pair_counts.items():
            if len(ring_ids) < threshold:
                continue
            pct = len(ring_ids) / len(ring_topics)
            confidence = min(0.9, 0.4 + pct * 0.5)

            insights.append(DreamInsight(
                type="bridge",
                description=(
                    f"'{a}' and '{b}' appear together in {pct:.0%} of your sessions. "
                    f"These topics seem connected in your world."
                ),
                confidence=round(confidence, 2),
                evidence=ring_ids,
            ))

        # Sort bridges by confidence, return top 3
        insights.sort(key=lambda i: i.confidence, reverse=True)
        return insights[:3]

    def _dream_arcs(self, rings: list) -> list[DreamInsight]:
        """Find growth trends over time.

        Example: "Your average V-Score has grown from 0.4 to 0.7 over 2 weeks"
        """
        insights: list[DreamInsight] = []
        if len(rings) < 3:
            return insights

        # Sort by timestamp ascending (oldest first)
        sorted_rings = sorted(rings, key=lambda r: r.timestamp)

        # Split into first half and second half
        mid = len(sorted_rings) // 2
        first_half = sorted_rings[:mid]
        second_half = sorted_rings[mid:]

        # V-score arc
        v_first = sum(self._ring_peak_v(r) for r in first_half) / len(first_half)
        v_second = sum(self._ring_peak_v(r) for r in second_half) / len(second_half)
        v_delta = v_second - v_first

        if abs(v_delta) >= 0.1:
            direction = "growing" if v_delta > 0 else "declining"
            time_span_days = (
                sorted_rings[-1].timestamp - sorted_rings[0].timestamp
            ) / 86400
            span_label = (
                f"over {time_span_days:.0f} days"
                if time_span_days >= 1
                else "across your recent sessions"
            )
            confidence = min(0.9, 0.4 + abs(v_delta) * 0.8 + len(rings) * 0.03)

            insights.append(DreamInsight(
                type="arc",
                description=(
                    f"Your V-Score has been {direction} {span_label}: "
                    f"{v_first:.2f} -> {v_second:.2f} "
                    f"({'up' if v_delta > 0 else 'down'} {abs(v_delta):.2f}). "
                    + ("Momentum is building." if v_delta > 0 else "Something shifted recently.")
                ),
                confidence=round(confidence, 2),
                evidence=[r.id for r in sorted_rings],
            ))

        # Ring width arc (learning density)
        w_first = sum(r.width for r in first_half) / len(first_half)
        w_second = sum(r.width for r in second_half) / len(second_half)
        w_delta = w_second - w_first

        if abs(w_delta) >= 0.08:
            direction = "increasing" if w_delta > 0 else "decreasing"
            confidence = min(0.75, 0.3 + abs(w_delta) * 0.8)

            insights.append(DreamInsight(
                type="arc",
                description=(
                    f"The depth of your sessions is {direction}. "
                    f"Ring width: {w_first:.2f} -> {w_second:.2f}. "
                    + (
                        "You're going deeper each conversation."
                        if w_delta > 0
                        else "Sessions have been lighter lately."
                    )
                ),
                confidence=round(confidence, 2),
                evidence=[r.id for r in sorted_rings],
            ))

        return insights

    def _dream_migration(self, rings: list) -> list[DreamInsight]:
        """Find hex position drift over time.

        Example: "2 weeks ago you were in action-mode. Now you're more reflective."
        """
        insights: list[DreamInsight] = []
        if len(rings) < 3:
            return insights

        sorted_rings = sorted(rings, key=lambda r: r.timestamp)
        mid = len(sorted_rings) // 2
        first_half = sorted_rings[:mid]
        second_half = sorted_rings[mid:]

        # Compute centroid hex for each half
        def _ring_hex_centroid(ring_list: list) -> HexCoord | None:
            all_hexes: list[HexCoord] = []
            for ring in ring_list:
                for h in ring.hex_drift:
                    all_hexes.append(h)
            if not all_hexes:
                return None
            return _hex_centroid(all_hexes)

        old_center = _ring_hex_centroid(first_half)
        new_center = _ring_hex_centroid(second_half)

        if old_center is None or new_center is None:
            return insights

        shift = _describe_hex_shift(old_center, new_center, threshold=0.2)
        if shift is None:
            return insights

        time_span_days = (
            sorted_rings[-1].timestamp - sorted_rings[0].timestamp
        ) / 86400
        span_label = (
            f"over {time_span_days:.0f} days"
            if time_span_days >= 1
            else "across recent sessions"
        )

        confidence = min(0.8, 0.35 + len(rings) * 0.04)

        insights.append(DreamInsight(
            type="migration",
            description=(
                f"Your mode has shifted {span_label}: you're now {shift}. "
                f"The Void noticed this drift across {len(rings)} conversations."
            ),
            confidence=round(confidence, 2),
            evidence=[r.id for r in sorted_rings],
        ))

        return insights

    def _dream_threads(self, rings: list) -> list[DreamInsight]:
        """Find open threads: topics mentioned once then abandoned.

        Example: "3 sessions ago you mentioned guitar. It never came back."
        """
        insights: list[DreamInsight] = []
        if len(rings) < 3:
            return insights

        sorted_rings = sorted(rings, key=lambda r: r.timestamp)

        # Build per-topic first/last ring index
        topic_appearances: dict[str, list[int]] = defaultdict(list)
        for idx, ring in enumerate(sorted_rings):
            for pattern in ring.patterns:
                words = {
                    w for w in pattern.trigger.lower().split()
                    if len(w) > 4 and w not in {
                        "avoid", "signal", "stress", "caused", "error",
                        "explicit_success", "previous", "response",
                        "ruhe_druck", "deescalation", "worked",
                    }
                }
                for word in words:
                    topic_appearances[word].append(idx)

        # Find topics that appeared in exactly 1 ring, and that ring had decent V-score
        now = len(sorted_rings) - 1
        for topic, indices in topic_appearances.items():
            if len(indices) != 1:
                continue

            ring_idx = indices[0]
            sessions_ago = now - ring_idx
            if sessions_ago < 2:
                continue  # too recent, not a forgotten thread

            ring = sorted_rings[ring_idx]
            peak_v = self._ring_peak_v(ring)
            if peak_v < 0.45:
                continue  # low-importance session, skip

            confidence = min(0.75, 0.35 + peak_v * 0.4 + sessions_ago * 0.05)

            insights.append(DreamInsight(
                type="thread",
                description=(
                    f"{sessions_ago} session{'s' if sessions_ago != 1 else ''} ago "
                    f"you mentioned '{topic}' (V-score was {peak_v:.2f}). "
                    f"It never came back. Is it still alive for you?"
                ),
                confidence=round(confidence, 2),
                evidence=[ring.id],
            ))

        # Return top 2 most confident forgotten threads
        insights.sort(key=lambda i: i.confidence, reverse=True)
        return insights[:2]

    # ------------------------------------------------------------------
    # Greeting composition
    # ------------------------------------------------------------------

    def _compose_greeting(self, insights: list[DreamInsight]) -> str:
        """Compose a warm greeting from dream insights."""
        if not insights:
            return (
                "Welcome back. "
                "I've been thinking, but the rings are still young. "
                "More conversations will let me see deeper patterns."
            )

        top = insights[0]
        parts = [f"While you were away, I noticed something: {top.description}"]

        # Add second insight if high confidence and different type
        for insight in insights[1:4]:
            if insight.confidence >= 0.55 and insight.type != top.type:
                parts.append(f"Also: {insight.description}")
                break

        parts.append("Good to have you back.")
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_rings(self, max_rings: int) -> list:
        """Get rings from RingMemory or empty list."""
        if self._ring_memory is None:
            return []
        try:
            rings = self._ring_memory._rings
            # Most recent N rings
            return rings[-max_rings:] if len(rings) > max_rings else rings
        except AttributeError:
            return []

    @staticmethod
    def _ring_peak_v(ring: Any) -> float:
        """Safe extraction of peak V-score from a ring."""
        try:
            traj = ring.v_score_trajectory
            if traj:
                return max(traj)
        except AttributeError:
            pass
        return 0.5

    def _load(self) -> None:
        """Load previous dreams from disk."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._dreams = [DreamReport.from_dict(d) for d in data.get("dreams", [])]
        except (json.JSONDecodeError, KeyError, TypeError):
            self._dreams = []


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def dream_demo() -> None:
    """Demo: 5 simulated conversations over a week, then dream.

    Conversations:
        Ring 1: Monday morning, stressed about work,   V: 0.4 -> 0.7
        Ring 2: Tuesday evening, creative flow,        V: 0.6 -> 0.9
        Ring 3: Wednesday night, career anxiety,       V: 0.3 -> 0.5
        Ring 4: Friday morning, energetic,             V: 0.7 -> 0.9
        Ring 5: Monday morning, stressed again,        V: 0.35 -> 0.65

    Expected discoveries:
        - TEMPORAL:   Monday mornings = stress pattern
        - BRIDGE:     "career" + "stress" co-occur
        - ARC:        V-score trajectory
        - THREAD:     any single-appearance topic
    """
    import tempfile
    import os

    print("=" * 60)
    print("VOID DREAMS --- DEMO")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # Build mock Ring objects without importing conversation_rings
    # ------------------------------------------------------------------
    from dataclasses import dataclass as _dc, field as _field

    @_dc
    class MockPattern:
        trigger: str
        response: str = ""
        confidence: float = 0.5

    @_dc
    class MockRing:
        id: str
        timestamp: float
        patterns: list
        v_score_trajectory: list
        hex_drift: list
        peak_moment: str = ""
        scar: str = ""
        total_turns: int = 3
        duration_seconds: float = 120.0

        @property
        def width(self) -> float:
            v_growth = max(0.0, self.v_score_trajectory[-1] - self.v_score_trajectory[0])
            return min(1.0, v_growth + len(self.patterns) * 0.1)

    # Times: simulate sessions across the past week
    now = time.time()
    DAY = 86400

    def _monday(offset_weeks: int = 0) -> float:
        """Timestamp for a Monday morning 9am relative to now."""
        # Compute last Monday
        t = now - (7 * offset_weeks * DAY)
        weekday = int(time.strftime("%w", time.localtime(t)))  # 0=Sun
        # Days since last Monday (0=Mon in ISO, but %w: 0=Sun)
        days_since_mon = (weekday - 1) % 7
        monday_noon = t - days_since_mon * DAY
        return monday_noon

    # Spread rings over the past 7 days
    ring_1 = MockRing(
        id="ring_mon_1",
        timestamp=_monday() - 6 * DAY + 9 * 3600,   # Mon 9am
        patterns=[
            MockPattern("user stress signal: deadline work morgen"),
            MockPattern("career anxiety pressure"),
        ],
        v_score_trajectory=[0.4, 0.55, 0.7],
        hex_drift=[
            HexCoord(ruhe_druck=0.8, sein_tun=0.7, langsam_schnell=0.6),
            HexCoord(ruhe_druck=0.4, sein_tun=0.4),
            HexCoord(ruhe_druck=0.1, sein_tun=0.2),
        ],
    )

    ring_2 = MockRing(
        id="ring_tue_2",
        timestamp=_monday() - 5 * DAY + 19 * 3600,  # Tue 7pm
        patterns=[
            MockPattern("creative flow building"),
            MockPattern("ideas writing projekt"),
        ],
        v_score_trajectory=[0.6, 0.75, 0.9],
        hex_drift=[
            HexCoord(empfangen_schaffen=0.6, allein_zusammen=-0.3),
            HexCoord(empfangen_schaffen=0.8, sein_tun=-0.4),
            HexCoord(empfangen_schaffen=0.9, ruhe_druck=-0.3),
        ],
    )

    ring_3 = MockRing(
        id="ring_wed_3",
        timestamp=_monday() - 4 * DAY + 22 * 3600,  # Wed 10pm
        patterns=[
            MockPattern("career stress anxiety work future"),
            MockPattern("health body tired exhausted"),
        ],
        v_score_trajectory=[0.3, 0.4, 0.5],
        hex_drift=[
            HexCoord(ruhe_druck=0.9, sein_tun=0.8),
            HexCoord(ruhe_druck=0.7, sein_tun=0.6),
            HexCoord(ruhe_druck=0.5, sein_tun=0.4),
        ],
    )

    ring_4 = MockRing(
        id="ring_fri_4",
        timestamp=_monday() - 2 * DAY + 10 * 3600,  # Fri 10am
        patterns=[
            MockPattern("energy creative ideas projekt"),
            MockPattern("team zusammen community building"),
        ],
        v_score_trajectory=[0.7, 0.8, 0.9],
        hex_drift=[
            HexCoord(ruhe_druck=-0.2, empfangen_schaffen=0.5, allein_zusammen=0.4),
            HexCoord(ruhe_druck=-0.3, empfangen_schaffen=0.7),
            HexCoord(ruhe_druck=-0.4, sein_tun=-0.3, allein_zusammen=0.5),
        ],
    )

    ring_5 = MockRing(
        id="ring_mon_5",
        timestamp=_monday() + 9 * 3600,              # This Mon 9am
        patterns=[
            MockPattern("user stress signal: work deadline morgen"),
            MockPattern("career pressure work"),
            MockPattern("guitar learn music hobby"),  # forgotten thread!
        ],
        v_score_trajectory=[0.35, 0.5, 0.65],
        hex_drift=[
            HexCoord(ruhe_druck=0.75, sein_tun=0.65, langsam_schnell=0.5),
            HexCoord(ruhe_druck=0.4, sein_tun=0.35),
            HexCoord(ruhe_druck=0.15, sein_tun=0.1),
        ],
    )

    mock_rings = [ring_1, ring_2, ring_3, ring_4, ring_5]

    # ------------------------------------------------------------------
    # Build a minimal mock RingMemory
    # ------------------------------------------------------------------
    class MockRingMemory:
        def __init__(self, rings: list) -> None:
            self._rings = rings

    mock_memory = MockRingMemory(mock_rings)

    # ------------------------------------------------------------------
    # Dream
    # ------------------------------------------------------------------
    tmp_dreams = tempfile.mktemp(suffix=".json")
    dreamer = VoidDreamer(ring_memory=mock_memory, dreams_path=tmp_dreams)

    print("Running dream cycle...")
    print(f"Analyzing {len(mock_rings)} rings...\n")

    report = dreamer.dream(max_rings=20)

    print(f"Dream completed in {report.dream_duration_ms:.1f}ms")
    print(f"Rings analyzed: {report.rings_analyzed}")
    print(f"Insights discovered: {len(report.insights)}")
    print()

    print("--- GREETING ---")
    print(report.greeting)
    print()

    if report.insights:
        print("--- ALL INSIGHTS ---")
        for i, insight in enumerate(report.insights, 1):
            print(f"  [{i}] type={insight.type}  confidence={insight.confidence:.0%}")
            print(f"      {insight.description}")
            print(f"      evidence: {insight.evidence}")
            print()

    print("This is what ChatGPT structurally cannot do.")
    print("No rings -> no dreams -> no patterns -> no growth.")
    print("VOID compounds. The space between sessions is alive.")
    print()

    try:
        os.unlink(tmp_dreams)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dream_demo()
