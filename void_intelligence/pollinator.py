"""
void_intelligence.pollinator --- Cross-Pollination Engine.

Lynn Margulis (Endosymbiosis Theory, 1967): Mitochondria were once
separate organisms that merged with cells. Two organisms became one,
and both became MORE.

That's what cross-pollination does with model knowledge:
What Model A learned can benefit Model B.

Components:
    Endosymbiont      --- A ring imported from another organism
    PollinationEvent  --- Record of a knowledge transfer
    CrossPollinator   --- The main engine

The industry silos knowledge per model.
We let knowledge flow between organisms.

Zero dependencies. No vector database. No LLM.
Just graph structure + keyword matching.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from void_intelligence.ring_graph import RingGraph, RingNode


# ── Endosymbiont ─────────────────────────────────────────────

@dataclass
class Endosymbiont:
    """A ring imported from another organism.

    Named after Lynn Margulis's endosymbiosis theory:
    mitochondria were once free-living bacteria that merged
    with ancestral eukaryotic cells. The merger made BOTH stronger.

    An endosymbiont ring lives in the target organism's graph
    but remembers where it came from. If the immune system
    confirms it helps, it's marked as confirmed --- fully integrated.
    """

    ring_id: str            # ID in target graph
    source_model: str       # Which organism it came from
    source_ring_id: str     # Original ring ID in source
    content: str
    keywords: list[str]
    transfer_time: float = field(default_factory=time.time)
    confirmed: bool = False  # Did immune feedback confirm improvement?
    lift: float = 0.0        # Composite score delta after transfer


# ── Pollination Event ────────────────────────────────────────

@dataclass
class PollinationEvent:
    """Record of a knowledge transfer between organisms.

    Like a bee visiting two flowers: pollen from A lands on B,
    and B grows fruit it never could have grown alone.
    """

    source_model: str
    target_model: str
    rings_transferred: int
    ring_ids: list[str]       # IDs in target graph
    timestamp: float = field(default_factory=time.time)
    transfer_lift: float = 0.0  # Immune health delta after transfer


# ── Transfer Scoring ─────────────────────────────────────────

# Ring type multipliers for transferability
_TYPE_WEIGHT = {
    "paradigm": 3.0,
    "milestone": 2.0,
    "learning": 1.0,
    "error": 0.5,
    "summary": 0.3,
    "imported": 0.1,  # Don't re-transfer imports (avoid infinite loops)
}


def _transferability_score(
    node: RingNode,
    graph: RingGraph,
) -> float:
    """Score how valuable a ring is for transfer.

    Higher = more worth transferring. Based on:
    - Ring type (paradigms >> learnings >> errors)
    - Graph connectivity (well-connected = well-tested knowledge)
    - Not compressed (compressed = already summarized)
    - Keyword richness (more keywords = more connectable)
    """
    if node.compressed:
        return 0.0

    # Type weight
    type_w = _TYPE_WEIGHT.get(node.ring_type, 1.0)

    # Connectivity: count edges involving this node
    n_edges = 0
    for e in graph.edges:
        if e.source == node.id or e.target == node.id:
            n_edges += 1
    conn_w = 1.0 + min(n_edges, 10) * 0.15

    # Keyword richness
    kw_w = 1.0 + min(len(node.keywords), 8) * 0.05

    return type_w * conn_w * kw_w


def _keyword_overlap(a_keywords: list[str], b_keywords: list[str]) -> float:
    """Fraction of A's keywords that B already has. 0.0 = no overlap, 1.0 = identical."""
    if not a_keywords:
        return 0.0
    a_set = set(a_keywords)
    b_set = set(b_keywords)
    return len(a_set & b_set) / len(a_set)


# ── CrossPollinator ──────────────────────────────────────────

class CrossPollinator:
    """Transfer knowledge between model organisms.

    Lynn Margulis proved that evolution is not just competition ---
    it's COOPERATION. Cells merged with bacteria and became eukaryotes.
    That merger is the most important event in the history of life.

    CrossPollinator does the same: knowledge learned by one model
    organism flows to another, making both more capable.

    Usage:
        pollinator = CrossPollinator()

        # Manual transfer
        event = pollinator.pollinate(
            source_graph=organism_a.graph,
            source_model="qwen3-14b",
            target_graph=organism_b.graph,
            target_model="gemini-2-flash",
        )

        # Track if it helped
        pollinator.confirm(target_model="gemini-2-flash", diagnosis=healthy_diag)

        # View transfer history
        print(pollinator.report())
    """

    def __init__(self, max_history: int = 200) -> None:
        self._events: list[PollinationEvent] = []
        self._symbionts: dict[str, list[Endosymbiont]] = {}  # by target model
        self._max_history = max_history
        # Pre-transfer health baselines for lift measurement
        self._baselines: dict[str, float] = {}  # model -> last composite score

    # ── Identify Transferable Rings ──────────────────────────

    def identify_transferable(
        self,
        graph: RingGraph,
        max_rings: int = 20,
    ) -> list[tuple[RingNode, float]]:
        """Identify rings worth transferring, ranked by transferability.

        Returns (ring, score) pairs sorted by score descending.
        Only active (non-compressed) rings with score > 0 are returned.
        """
        if graph.count == 0:
            return []

        scored = []
        for node in graph.nodes.values():
            score = _transferability_score(node, graph)
            if score > 0:
                scored.append((node, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_rings]

    # ── Filter: What does target already know? ───────────────

    def _already_known(
        self,
        node: RingNode,
        target_graph: RingGraph,
        overlap_threshold: float = 0.5,
    ) -> bool:
        """Check if target already has equivalent knowledge.

        Uses keyword overlap: if >50% of the source ring's keywords
        already exist in any single target ring, it's redundant.
        """
        if not node.keywords:
            return False

        for target_node in target_graph.nodes.values():
            if target_node.compressed:
                continue
            overlap = _keyword_overlap(node.keywords, target_node.keywords)
            if overlap >= overlap_threshold:
                return True

        return False

    # ── Pollinate: The Core Transfer ─────────────────────────

    def pollinate(
        self,
        source_graph: RingGraph,
        source_model: str,
        target_graph: RingGraph,
        target_model: str,
        *,
        max_transfer: int = 10,
        overlap_threshold: float = 0.5,
    ) -> PollinationEvent:
        """Transfer knowledge from source organism to target organism.

        1. Identify transferable rings from source (by transferability score)
        2. Filter out what target already knows (keyword overlap)
        3. Import into target graph as "imported" ring type
        4. Create endosymbiont records
        5. Track the pollination event

        Args:
            source_graph: Source organism's ring graph.
            source_model: Source model name.
            target_graph: Target organism's ring graph.
            target_model: Target model name.
            max_transfer: Maximum rings to transfer.
            overlap_threshold: Min keyword overlap to consider redundant.

        Returns:
            PollinationEvent with transfer details.
        """
        candidates = self.identify_transferable(source_graph, max_rings=max_transfer * 3)

        transferred_ids: list[str] = []
        transferred_count = 0

        for node, _score in candidates:
            if transferred_count >= max_transfer:
                break

            # Skip if target already knows this
            if self._already_known(node, target_graph, overlap_threshold):
                continue

            # Import into target graph
            imported = target_graph.add(
                content=node.content,
                ring_type="imported",
            )
            transferred_ids.append(imported.id)
            transferred_count += 1

            # Record endosymbiont
            symbiont = Endosymbiont(
                ring_id=imported.id,
                source_model=source_model,
                source_ring_id=node.id,
                content=node.content,
                keywords=list(node.keywords),
            )
            if target_model not in self._symbionts:
                self._symbionts[target_model] = []
            self._symbionts[target_model].append(symbiont)

        event = PollinationEvent(
            source_model=source_model,
            target_model=target_model,
            rings_transferred=transferred_count,
            ring_ids=transferred_ids,
        )
        self._events.append(event)

        # Trim history
        if len(self._events) > self._max_history:
            self._events = self._events[-self._max_history:]

        return event

    # ── Confirm: Did the transfer help? ──────────────────────

    def set_baseline(self, model: str, composite_score: float) -> None:
        """Record pre-transfer health baseline for lift measurement."""
        self._baselines[model] = composite_score

    def confirm(
        self,
        target_model: str,
        composite_score: float,
    ) -> float:
        """Measure transfer lift from immune feedback.

        Compares current composite score against pre-transfer baseline.
        Positive lift = transfer helped. Negative = transfer hurt.

        Also confirms endosymbionts (marks them as integrated).

        Returns the lift value.
        """
        baseline = self._baselines.get(target_model, 0.5)
        lift = composite_score - baseline

        # Confirm symbionts if lift is positive
        if target_model in self._symbionts:
            for sym in self._symbionts[target_model]:
                if not sym.confirmed:
                    sym.confirmed = lift > 0
                    sym.lift = lift

        # Update latest event lift
        for event in reversed(self._events):
            if event.target_model == target_model:
                event.transfer_lift = lift
                break

        # Update baseline for next measurement
        self._baselines[target_model] = composite_score

        return lift

    # ── Auto-Pollinate: Router-Triggered ─────────────────────

    def auto_pollinate(
        self,
        organisms: dict[str, RingGraph | None],
        *,
        min_rings: int = 5,
        max_transfer: int = 5,
        cooldown_sec: float = 300.0,
    ) -> list[PollinationEvent]:
        """Automatic cross-pollination between all organisms.

        Triggered by the router. Transfers rings between organisms
        that have enough knowledge to share.

        Args:
            organisms: dict of model_name -> RingGraph (None = no graph).
            min_rings: Minimum ring count before a graph participates.
            max_transfer: Max rings per transfer.
            cooldown_sec: Minimum seconds between transfers for same pair.

        Returns:
            List of pollination events that occurred.
        """
        now = time.time()

        # Filter: only organisms with enough rings
        eligible = {
            name: graph
            for name, graph in organisms.items()
            if graph is not None and graph.active_count >= min_rings
        }

        if len(eligible) < 2:
            return []

        # Find pairs that haven't been pollinated recently
        recent_pairs: set[tuple[str, str]] = set()
        for event in self._events:
            if (now - event.timestamp) < cooldown_sec:
                recent_pairs.add((event.source_model, event.target_model))

        events = []
        names = list(eligible.keys())

        for i, source_name in enumerate(names):
            for target_name in names[i + 1:]:
                # Try both directions
                for s_name, t_name in [(source_name, target_name), (target_name, source_name)]:
                    if (s_name, t_name) in recent_pairs:
                        continue

                    event = self.pollinate(
                        source_graph=eligible[s_name],
                        source_model=s_name,
                        target_graph=eligible[t_name],
                        target_model=t_name,
                        max_transfer=max_transfer,
                    )

                    if event.rings_transferred > 0:
                        events.append(event)

        return events

    # ── Introspection ────────────────────────────────────────

    def symbionts_for(self, model: str) -> list[Endosymbiont]:
        """Get all endosymbionts in a model's organism."""
        return list(self._symbionts.get(model, []))

    def confirmed_symbionts(self, model: str) -> list[Endosymbiont]:
        """Get confirmed (beneficial) endosymbionts only."""
        return [s for s in self._symbionts.get(model, []) if s.confirmed]

    def transfer_score(self, model: str) -> float:
        """Average transfer lift for a model. 0.0 = no data."""
        syms = self._symbionts.get(model, [])
        if not syms:
            return 0.0
        confirmed = [s for s in syms if s.confirmed]
        if not confirmed:
            return 0.0
        return sum(s.lift for s in confirmed) / len(confirmed)

    @property
    def total_transfers(self) -> int:
        """Total rings transferred across all events."""
        return sum(e.rings_transferred for e in self._events)

    @property
    def total_events(self) -> int:
        return len(self._events)

    @property
    def unique_pairs(self) -> int:
        """Number of unique source-target pairs that have exchanged knowledge."""
        pairs = {(e.source_model, e.target_model) for e in self._events if e.rings_transferred > 0}
        return len(pairs)

    def report(self) -> dict:
        """Full cross-pollination report."""
        model_stats: dict[str, dict] = {}

        for model, syms in self._symbionts.items():
            confirmed = [s for s in syms if s.confirmed]
            model_stats[model] = {
                "total_imports": len(syms),
                "confirmed": len(confirmed),
                "sources": list({s.source_model for s in syms}),
                "avg_lift": round(self.transfer_score(model), 4),
            }

        return {
            "total_events": self.total_events,
            "total_transfers": self.total_transfers,
            "unique_pairs": self.unique_pairs,
            "models": model_stats,
            "recent_events": [
                {
                    "source": e.source_model,
                    "target": e.target_model,
                    "rings": e.rings_transferred,
                    "lift": round(e.transfer_lift, 4),
                    "time": e.timestamp,
                }
                for e in self._events[-10:]
            ],
        }

    # ── Persistence ──────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        return {
            "version": 1,
            "events": [
                {
                    "source_model": e.source_model,
                    "target_model": e.target_model,
                    "rings_transferred": e.rings_transferred,
                    "ring_ids": e.ring_ids,
                    "timestamp": e.timestamp,
                    "transfer_lift": e.transfer_lift,
                }
                for e in self._events
            ],
            "symbionts": {
                model: [
                    {
                        "ring_id": s.ring_id,
                        "source_model": s.source_model,
                        "source_ring_id": s.source_ring_id,
                        "content": s.content,
                        "keywords": s.keywords,
                        "transfer_time": s.transfer_time,
                        "confirmed": s.confirmed,
                        "lift": s.lift,
                    }
                    for s in syms
                ]
                for model, syms in self._symbionts.items()
            },
            "baselines": dict(self._baselines),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CrossPollinator":
        """Restore from serialized. Bad data = fresh pollinator (never crash)."""
        p = cls()
        try:
            for ed in data.get("events", []):
                event = PollinationEvent(
                    source_model=str(ed.get("source_model", "")),
                    target_model=str(ed.get("target_model", "")),
                    rings_transferred=int(ed.get("rings_transferred", 0)),
                    ring_ids=list(ed.get("ring_ids", [])),
                    timestamp=float(ed.get("timestamp", time.time())),
                    transfer_lift=float(ed.get("transfer_lift", 0.0)),
                )
                p._events.append(event)

            for model, syms_data in data.get("symbionts", {}).items():
                p._symbionts[str(model)] = []
                for sd in syms_data:
                    sym = Endosymbiont(
                        ring_id=str(sd.get("ring_id", "")),
                        source_model=str(sd.get("source_model", "")),
                        source_ring_id=str(sd.get("source_ring_id", "")),
                        content=str(sd.get("content", "")),
                        keywords=list(sd.get("keywords", [])),
                        transfer_time=float(sd.get("transfer_time", time.time())),
                        confirmed=bool(sd.get("confirmed", False)),
                        lift=float(sd.get("lift", 0.0)),
                    )
                    p._symbionts[str(model)].append(sym)

            p._baselines = {
                str(k): float(v)
                for k, v in data.get("baselines", {}).items()
            }
        except (TypeError, ValueError, KeyError):
            return cls()
        return p
