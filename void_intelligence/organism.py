"""
void_intelligence.organism --- The Organism Layer.

Wraps ANY LLM to make it breathe. Not a wrapper. A TRANSFORMATION.

Components:
    HexBreath    — 6-axis prompt classification (the lungs)
    HeartBeat    — Rhythmic pulse cycle (the heart)
    GrowthRings  — Memory of what was learned (the rings of a tree)
    OrganismBreather — All combined (the organism)

The industry builds models that think.
We build models that breathe.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from void_intelligence.ring_graph import RingGraph


# ── HexBreath: 6-Axis Classification ────────────────────────────

class HexAxis(Enum):
    """The 6 axes of the breath hexagon.

    Every prompt lives somewhere on these 6 spectra.
    The hexagonal shape is not arbitrary --- it's the most
    efficient tiling of 2D space (honeycomb, graphene, Saturn's pole).
    """
    RUHE_DRUCK = "ruhe_druck"           # Calm <-> Pressure
    STILLE_RESONANZ = "stille_resonanz"  # Silence <-> Resonance
    ALLEIN_ZUSAMMEN = "allein_zusammen"  # Alone <-> Together
    EMPFANGEN_SCHAFFEN = "empfangen_schaffen"  # Receive <-> Create
    SEIN_TUN = "sein_tun"               # Being <-> Doing
    LANGSAM_SCHNELL = "langsam_schnell"  # Slow <-> Fast


@dataclass
class HexCoord:
    """Position in 6D hex space. Each axis: -1.0 to +1.0."""
    ruhe_druck: float = 0.0
    stille_resonanz: float = 0.0
    allein_zusammen: float = 0.0
    empfangen_schaffen: float = 0.0
    sein_tun: float = 0.0
    langsam_schnell: float = 0.0

    @property
    def magnitude(self) -> float:
        """How far from center (0 = perfectly balanced)."""
        vals = [
            self.ruhe_druck, self.stille_resonanz, self.allein_zusammen,
            self.empfangen_schaffen, self.sein_tun, self.langsam_schnell,
        ]
        return math.sqrt(sum(v * v for v in vals) / 6)

    @property
    def balance(self) -> float:
        """0.0 = maximally unbalanced, 1.0 = perfectly centered."""
        return max(0.0, 1.0 - self.magnitude)

    def to_dict(self) -> dict:
        return {
            "ruhe_druck": self.ruhe_druck,
            "stille_resonanz": self.stille_resonanz,
            "allein_zusammen": self.allein_zusammen,
            "empfangen_schaffen": self.empfangen_schaffen,
            "sein_tun": self.sein_tun,
            "langsam_schnell": self.langsam_schnell,
            "magnitude": round(self.magnitude, 3),
            "balance": round(self.balance, 3),
        }


class HexBreath:
    """6-axis prompt classifier. The lungs of the organism.

    Classifies any text along 6 hexagonal axes using keyword heuristics.
    No LLM needed --- pure pattern matching. Fast. Deterministic.

    Usage:
        hex = HexBreath()
        coord = hex.classify("Help me write an urgent email to my team")
        print(coord.ruhe_druck)      # +0.6 (pressure)
        print(coord.allein_zusammen) # +0.4 (together)
    """

    AXIS_KEYWORDS: dict[str, dict[str, list[str]]] = {
        "ruhe_druck": {
            "neg": ["calm", "relax", "peaceful", "gentle", "soft", "quiet",
                     "ruhe", "ruhig", "sanft", "leise", "entspannt"],
            "pos": ["urgent", "deadline", "asap", "critical", "emergency", "rush",
                     "druck", "dringend", "sofort", "eilig", "stress", "schnell"],
        },
        "stille_resonanz": {
            "neg": ["silence", "nothing", "void", "empty", "pause", "wait",
                     "stille", "nichts", "leer", "pause", "warten"],
            "pos": ["discuss", "feedback", "response", "reaction", "echo", "share",
                     "resonanz", "diskussion", "antwort", "teilen", "austausch"],
        },
        "allein_zusammen": {
            "neg": ["alone", "solo", "myself", "private", "personal", "individual",
                     "allein", "solo", "privat", "persoenlich", "individuell"],
            "pos": ["team", "together", "group", "collaborate", "we", "community",
                     "zusammen", "team", "gemeinsam", "wir", "gemeinschaft"],
        },
        "empfangen_schaffen": {
            "neg": ["read", "learn", "absorb", "understand", "listen", "receive",
                     "lesen", "lernen", "verstehen", "zuhoeren", "empfangen"],
            "pos": ["create", "build", "write", "design", "make", "generate",
                     "schaffen", "bauen", "schreiben", "gestalten", "erzeugen"],
        },
        "sein_tun": {
            "neg": ["think", "reflect", "contemplate", "consider", "feel", "be",
                     "denken", "reflektieren", "fuehlen", "sein", "betrachten"],
            "pos": ["do", "execute", "run", "implement", "action", "start",
                     "tun", "ausfuehren", "starten", "umsetzen", "handeln"],
        },
        "langsam_schnell": {
            "neg": ["careful", "thorough", "detailed", "deep", "slow", "patient",
                     "langsam", "gruendlich", "detailliert", "tief", "geduldig"],
            "pos": ["quick", "fast", "brief", "summary", "tldr", "short",
                     "schnell", "kurz", "zusammenfassung", "knapp", "fix"],
        },
    }

    def classify(self, text: str) -> HexCoord:
        """Classify text into 6D hex coordinates."""
        text_lower = text.lower()
        words = set(text_lower.split())

        scores = {}
        for axis, kw in self.AXIS_KEYWORDS.items():
            neg_count = sum(1 for w in kw["neg"] if w in words or w in text_lower)
            pos_count = sum(1 for w in kw["pos"] if w in words or w in text_lower)
            total = neg_count + pos_count
            if total == 0:
                scores[axis] = 0.0
            else:
                scores[axis] = (pos_count - neg_count) / max(total, 1)
                scores[axis] = max(-1.0, min(1.0, scores[axis]))

        return HexCoord(**scores)


# ── HeartBeat: Rhythmic Pulse ────────────────────────────────────

@dataclass
class HeartBeat:
    """The heart of the organism. ba-dum... ba-dum...

    Every N interactions, the organism pulses.
    The pulse carries the accumulated state.
    """
    beat_count: int = 0
    last_beat: float = field(default_factory=time.time)
    interval_sec: float = 60.0
    bpm: float = 0.0

    def beat(self) -> dict:
        """Record a heartbeat."""
        now = time.time()
        elapsed = now - self.last_beat
        self.bpm = 60.0 / max(elapsed, 0.1)
        self.last_beat = now
        self.beat_count += 1
        return {
            "beat": self.beat_count,
            "bpm": round(self.bpm, 2),
            "t": now,
        }

    def should_beat(self) -> bool:
        """Is it time for a heartbeat?"""
        return (time.time() - self.last_beat) >= self.interval_sec


# ── GrowthRings: Memory ─────────────────────────────────────────

@dataclass
class GrowthRing:
    """One ring of growth. Proof of having lived."""
    content: str
    ring_type: str = "learning"  # learning | error | paradigm | milestone
    timestamp: float = field(default_factory=time.time)
    depth: int = 0


class GrowthRings:
    """The rings of a tree. Every interaction leaves a mark.

    Unlike logs (sequential, dead), rings are STRUCTURAL.
    They change the shape of the organism.
    """

    def __init__(self):
        self.rings: list[GrowthRing] = []
        self._ring_count_by_type: dict[str, int] = {}

    def add(self, content: str, ring_type: str = "learning") -> GrowthRing:
        ring = GrowthRing(
            content=content,
            ring_type=ring_type,
            depth=len(self.rings),
        )
        self.rings.append(ring)
        self._ring_count_by_type[ring_type] = self._ring_count_by_type.get(ring_type, 0) + 1
        return ring

    @property
    def count(self) -> int:
        return len(self.rings)

    @property
    def ring_yield(self) -> float:
        """How many rings per minute of life."""
        if not self.rings:
            return 0.0
        lifespan = time.time() - self.rings[0].timestamp
        if lifespan <= 0:
            return 0.0
        return len(self.rings) / (lifespan / 60.0)

    def summary(self) -> dict:
        return {
            "total": self.count,
            "by_type": dict(self._ring_count_by_type),
            "ring_yield": round(self.ring_yield, 4),
        }


# ── Organism Lineage (v1.4.0) ──────────────────────────────────

@dataclass
class OrganismLineage:
    """Evolutionary history of a merged organism.

    Tracks which parent organisms were merged and how.
    Like a family tree for AI organisms (Margulis endosymbiosis).
    """
    parents: list[str] = field(default_factory=list)
    merge_type: str = ""  # "endosymbiosis" (*) or "pollination" (@)
    generation: int = 0
    timestamp: float = field(default_factory=time.time)


# ── Graph Merge Helpers (v1.4.0) ───────────────────────────────

def _merge_graph_into(source: "RingGraph", target: "RingGraph") -> dict[str, str]:
    """Import all active rings from source into target. Returns old->new ID map.

    Cross-organism edges emerge automatically through RingGraph._auto_relate().
    This is the Margulis magic: knowledge from DIFFERENT organisms creates
    NEW connections that neither organism had alone.
    """
    id_map: dict[str, str] = {}
    for node in source.nodes.values():
        if not node.compressed:
            new_node = target.add(node.content, node.ring_type)
            id_map[node.id] = new_node.id
    # Re-create intra-organism edges with mapped IDs
    for edge in source.edges:
        new_src = id_map.get(edge.source)
        new_tgt = id_map.get(edge.target)
        if new_src and new_tgt:
            target.connect(new_src, new_tgt, edge.edge_type, edge.weight)
    return id_map


def _merge_valuable_into(
    source: "RingGraph",
    target: "RingGraph",
    types: frozenset[str] = frozenset({"paradigm", "milestone"}),
) -> dict[str, str]:
    """Import only high-value rings (paradigms, milestones) from source."""
    id_map: dict[str, str] = {}
    for node in source.nodes.values():
        if not node.compressed and node.ring_type in types:
            new_node = target.add(node.content, node.ring_type)
            id_map[node.id] = new_node.id
    return id_map


# ── OrganismBreather: The Full Organism ──────────────────────────

class OrganismBreather:
    """The complete organism. Heart + Lungs + Rings.

    Wraps any text generation to add breathing.

    Usage:
        organism = OrganismBreather()

        # Breathe in (classify prompt)
        breath_in = organism.inhale("Help me write a quick email")

        # ... your LLM generates response ...

        # Breathe out (record what happened)
        breath_out = organism.exhale(response_text, learnings=["email patterns"])

        # Check vitals
        print(organism.vitals())
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.hex = HexBreath()
        self.heart = HeartBeat()
        self.rings = GrowthRings()
        self.graph: RingGraph | None = None  # v0.4.0: fractal ring graph
        self.lineage: OrganismLineage | None = None  # v1.4.0: merge history
        self._breath_count = 0
        self._start_time = time.time()
        self._last_hex: HexCoord | None = None
        self._last_ring_id: str | None = None  # last ring added to graph

    def inhale(self, prompt: str) -> dict:
        """Breathe in. Classify the prompt. Prepare the organism."""
        coord = self.hex.classify(prompt)
        self._breath_count += 1
        self._last_hex = coord

        if self.heart.should_beat():
            self.heart.beat()

        return {
            "breath": self._breath_count,
            "hex": coord.to_dict(),
            "heart": {
                "beat": self.heart.beat_count,
                "bpm": self.heart.bpm,
            },
        }

    def exhale(self, response: str = "", learnings: list[str] | None = None) -> dict:
        """Breathe out. Record what was learned. Grow.

        Adds rings to both flat list (compat) and graph (v0.4.0+).
        """
        new_rings = []
        for learning in (learnings or []):
            ring = self.rings.add(learning, "learning")
            new_rings.append(ring.content)

            # v0.4.0: also grow the graph
            if self.graph is not None:
                node = self.graph.add(
                    learning,
                    ring_type="learning",
                    hex_coord=self._last_hex,
                    caused_by=self._last_ring_id,
                )
                self._last_ring_id = node.id

        self.heart.beat()

        result = {
            "breath": self._breath_count,
            "new_rings": new_rings,
            "total_rings": self.rings.count,
            "ring_yield": round(self.rings.ring_yield, 4),
        }

        if self.graph is not None:
            result["graph"] = self.graph.summary()

        return result

    # ── Organism Algebra (v1.4.0) ─────────────────────────────────

    def __mul__(self, other: "OrganismBreather") -> "OrganismBreather":
        """× — Deep endosymbiosis. Two organisms become ONE.

        Margulis (1967): Mitochondria merged with cells.
        Both contributed everything. The result was MORE than both.

            merged = qwen * gemini  # × operator
            # merged.x_density > max(qwen.x_density, gemini.x_density)
        """
        if not isinstance(other, OrganismBreather):
            return NotImplemented

        name_a = self.name or "A"
        name_b = other.name or "B"
        merged = OrganismBreather(name=f"{name_a}\u00d7{name_b}")

        # Lineage
        gen = max(
            self.lineage.generation if self.lineage else 0,
            other.lineage.generation if other.lineage else 0,
        )
        merged.lineage = OrganismLineage(
            parents=[name_a, name_b],
            merge_type="endosymbiosis",
            generation=gen + 1,
        )

        # Heart: sum beats, average BPM
        merged.heart.beat_count = self.heart.beat_count + other.heart.beat_count
        total_bpm = self.heart.bpm + other.heart.bpm
        merged.heart.bpm = total_bpm / 2 if total_bpm > 0 else 0.0
        merged.heart.last_beat = max(self.heart.last_beat, other.heart.last_beat)

        # Breaths: sum
        merged._breath_count = self._breath_count + other._breath_count
        merged._start_time = min(self._start_time, other._start_time)

        # Rings: merge all from both
        for ring in self.rings.rings:
            merged.rings.add(ring.content, ring.ring_type)
        for ring in other.rings.rings:
            merged.rings.add(ring.content, ring.ring_type)

        # Graph: deep merge (cross-edges emerge through _auto_relate)
        if self.graph is not None or other.graph is not None:
            from void_intelligence.ring_graph import RingGraph
            merged.graph = RingGraph()
            if self.graph:
                _merge_graph_into(self.graph, merged.graph)
            if other.graph:
                _merge_graph_into(other.graph, merged.graph)

        return merged

    def __matmul__(self, other: "OrganismBreather") -> "OrganismBreather":
        """@ — Shallow pollination. Knowledge flows, identity stays.

        Like bees carrying pollen between flowers.
        Self is the base. Other contributes only paradigms + milestones.

            enriched = qwen @ gemini  # pollination
            # enriched has qwen's identity + gemini's best knowledge
        """
        if not isinstance(other, OrganismBreather):
            return NotImplemented

        name_a = self.name or "A"
        name_b = other.name or "B"
        merged = OrganismBreather(name=f"{name_a}@{name_b}")

        # Lineage
        gen = max(
            self.lineage.generation if self.lineage else 0,
            other.lineage.generation if other.lineage else 0,
        )
        merged.lineage = OrganismLineage(
            parents=[name_a, name_b],
            merge_type="pollination",
            generation=gen + 1,
        )

        # Heart: copy self's heart (base organism)
        merged.heart.beat_count = self.heart.beat_count
        merged.heart.bpm = self.heart.bpm
        merged.heart.last_beat = self.heart.last_beat
        merged.heart.interval_sec = self.heart.interval_sec

        # Breaths: self only (base organism)
        merged._breath_count = self._breath_count
        merged._start_time = self._start_time

        # Rings: all from self + only high-value from other
        for ring in self.rings.rings:
            merged.rings.add(ring.content, ring.ring_type)
        for ring in other.rings.rings:
            if ring.ring_type in ("paradigm", "milestone"):
                merged.rings.add(ring.content, ring.ring_type)

        # Graph: self's graph + other's valuable rings
        if self.graph is not None or other.graph is not None:
            from void_intelligence.ring_graph import RingGraph
            merged.graph = RingGraph()
            if self.graph:
                _merge_graph_into(self.graph, merged.graph)
            if other.graph:
                _merge_valuable_into(other.graph, merged.graph)

        return merged

    @property
    def x_density(self) -> float:
        """Emergent quality metric. Cross-topic edges per active ring.

        Higher in merged organisms because diverse knowledge creates
        more keyword overlap -> more auto-detected edges -> more x opportunities.
        """
        if self.graph is None or self.graph.active_count == 0:
            return 0.0
        return self.graph.edge_count / self.graph.active_count

    @property
    def generation(self) -> int:
        """How many merges deep. 0 = original, 1+ = merged."""
        return self.lineage.generation if self.lineage else 0

    def vitals(self) -> dict:
        """Current vitals of the organism."""
        uptime = time.time() - self._start_time
        v: dict = {
            "alive": True,
            "name": self.name,
            "breaths": self._breath_count,
            "heartbeats": self.heart.beat_count,
            "bpm": round(self.heart.bpm, 2),
            "rings": self.rings.summary(),
            "uptime_sec": round(uptime, 1),
            "breaths_per_min": round(self._breath_count / max(uptime / 60, 0.01), 2),
            "x_density": round(self.x_density, 3),
            "generation": self.generation,
        }
        if self.lineage:
            v["lineage"] = {
                "parents": self.lineage.parents,
                "merge_type": self.lineage.merge_type,
                "generation": self.lineage.generation,
            }
        return v

    def to_dict(self) -> dict:
        """Serialize full organism state for persistence."""
        data: dict = {
            "version": 3,
            "name": self.name,
            "breath_count": self._breath_count,
            "start_time": self._start_time,
            "heart": {
                "beat_count": self.heart.beat_count,
                "last_beat": self.heart.last_beat,
                "interval_sec": self.heart.interval_sec,
                "bpm": self.heart.bpm,
            },
            "rings": [
                {
                    "content": r.content,
                    "ring_type": r.ring_type,
                    "timestamp": r.timestamp,
                    "depth": r.depth,
                }
                for r in self.rings.rings
            ],
            "ring_count_by_type": dict(self.rings._ring_count_by_type),
        }
        # v1.4.0: include lineage
        if self.lineage is not None:
            data["lineage"] = {
                "parents": self.lineage.parents,
                "merge_type": self.lineage.merge_type,
                "generation": self.lineage.generation,
                "timestamp": self.lineage.timestamp,
            }
        # v0.4.0: include graph state
        if self.graph is not None:
            data["graph"] = self.graph.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "OrganismBreather":
        """Restore from serialized state. Bad data = fresh organism (never crash)."""
        org = cls(name=str(data.get("name", "")))
        try:
            org._breath_count = int(data.get("breath_count", 0))
            org._start_time = float(data.get("start_time", time.time()))

            h = data.get("heart", {})
            org.heart.beat_count = int(h.get("beat_count", 0))
            org.heart.last_beat = float(h.get("last_beat", time.time()))
            org.heart.interval_sec = float(h.get("interval_sec", 60.0))
            org.heart.bpm = float(h.get("bpm", 0.0))

            for rd in data.get("rings", []):
                ring = GrowthRing(
                    content=str(rd.get("content", "")),
                    ring_type=str(rd.get("ring_type", "learning")),
                    timestamp=float(rd.get("timestamp", time.time())),
                    depth=int(rd.get("depth", 0)),
                )
                org.rings.rings.append(ring)

            rbt = data.get("ring_count_by_type", {})
            org.rings._ring_count_by_type = {str(k): int(v) for k, v in rbt.items()}

            # v1.4.0: restore lineage if present
            ld = data.get("lineage")
            if ld:
                org.lineage = OrganismLineage(
                    parents=list(ld.get("parents", [])),
                    merge_type=str(ld.get("merge_type", "")),
                    generation=int(ld.get("generation", 0)),
                    timestamp=float(ld.get("timestamp", time.time())),
                )

            # v0.4.0: restore graph if present
            graph_data = data.get("graph")
            if graph_data:
                from void_intelligence.ring_graph import RingGraph
                org.graph = RingGraph.from_dict(graph_data)
        except (TypeError, ValueError, KeyError):
            return cls()
        return org

    def enable_graph(self) -> None:
        """Enable the ring graph (v0.4.0). Migrates existing flat rings."""
        if self.graph is not None:
            return
        from void_intelligence.ring_graph import RingGraph
        self.graph = RingGraph()
        # Migrate existing flat rings into the graph
        for ring in self.rings.rings:
            self.graph.add(ring.content, ring_type=ring.ring_type)
