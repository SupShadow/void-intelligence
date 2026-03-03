"""
void_intelligence.ring_graph --- Fractal Knowledge Structure.

Growth rings become a GRAPH, not a flat list. Knowledge is self-similar
across scales. A ring about "email tone" connects to "communication style"
connects to "team dynamics." The graph IS the fractal.

Genius: Benoit Mandelbrot (Fractal Geometry, 1982)

Components:
    RingNode   --- A single ring (learning, error, paradigm, milestone, summary)
    RingEdge   --- Typed connection between rings
    RingGraph  --- The full fractal structure

Zero dependencies. No vector database. No LLM.
Just graph structure + keyword TF-IDF.

The industry stores knowledge in flat lists.
We grow knowledge in fractal rings.
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from void_intelligence.organism import HexBreath, HexCoord


# ── Tokenization (zero deps) ────────────────────────────────────

_STOP = frozenset({
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "up", "about", "into", "through",
    "and", "but", "or", "nor", "not", "no", "so", "if", "then", "that",
    "this", "it", "its", "me", "my", "we", "our", "you", "your",
    "he", "she", "they", "them", "his", "her", "their",
    # German
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "nicht",
    "ist", "sind", "war", "hat", "mit", "von", "fuer", "auf", "zu",
    "an", "bei", "nach", "ueber", "als", "wie", "ich", "du",
    "er", "sie", "wir", "ihr", "es", "den", "dem", "des", "im", "am",
})

_WORD_RE = re.compile(r"[a-z0-9äöüß]{2,}")


def _tokenize(text: str) -> list[str]:
    """Extract meaningful words. Lowercase, no stop words."""
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP]


# ── Ring Node ────────────────────────────────────────────────────

@dataclass
class RingNode:
    """A ring in the graph. A single learning, persisted forever.

    Like a tree ring: proof of having lived through something.
    Unlike a log entry: it connects to other rings structurally.
    """

    id: str
    content: str
    ring_type: str = "learning"  # learning | error | paradigm | milestone | summary
    timestamp: float = field(default_factory=time.time)
    depth: int = 0
    hex_coord: dict | None = None  # HexCoord.to_dict() at birth
    keywords: list[str] = field(default_factory=list)
    compressed: bool = False  # True if merged into a summary ring


# ── Ring Edge ────────────────────────────────────────────────────

@dataclass
class RingEdge:
    """Typed connection between rings.

    Edge types:
        caused_by       --- This ring was learned BECAUSE of that ring
        related         --- These rings cover similar topics (auto-detected)
        compressed_into --- Old ring merged into a summary ring
        contradicts     --- This ring corrects/overrides that ring
        deepens         --- This ring adds depth to that ring
    """

    source: str
    target: str
    edge_type: str = "related"
    weight: float = 0.5  # 0.0 to 1.0


# ── Ring Graph ───────────────────────────────────────────────────

class RingGraph:
    """Directed graph of growth rings. Fractal knowledge structure.

    The graph IS the memory. Not a flat list that forgets order.
    Not a vector database that forgets structure.
    A GRAPH that remembers RELATIONSHIPS between learnings.

    Usage:
        graph = RingGraph()
        r1 = graph.add("Email classification uses 6 dimensions")
        r2 = graph.add("Urgency shifts tone toward direct language", caused_by=r1.id)

        results = graph.query("email tone urgency")
        context = graph.to_context("Help me write an urgent email")
    """

    def __init__(self) -> None:
        self.nodes: dict[str, RingNode] = {}
        self.edges: list[RingEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse: dict[str, list[str]] = defaultdict(list)
        self._next_id: int = 0
        self._hex = HexBreath()
        self._index: dict[str, set[str]] = defaultdict(set)

    # ── Add ──────────────────────────────────────────────────────

    def add(
        self,
        content: str,
        ring_type: str = "learning",
        hex_coord: HexCoord | None = None,
        caused_by: str | None = None,
    ) -> RingNode:
        """Add a ring. Optionally connect to its cause.

        Auto-detects related rings by keyword overlap (>= 2 shared words).

        Args:
            content: What was learned.
            ring_type: learning | error | paradigm | milestone.
            hex_coord: Hex classification at birth.
            caused_by: Ring ID that caused this learning.
        """
        ring_id = f"r{self._next_id:04d}"
        self._next_id += 1

        keywords = _tokenize(content)

        node = RingNode(
            id=ring_id,
            content=content,
            ring_type=ring_type,
            depth=len(self.nodes),
            hex_coord=hex_coord.to_dict() if hex_coord else None,
            keywords=keywords,
        )
        self.nodes[ring_id] = node

        for word in set(keywords):
            self._index[word].add(ring_id)

        if caused_by and caused_by in self.nodes:
            self.connect(ring_id, caused_by, "caused_by", 0.8)

        self._auto_relate(node)

        return node

    def _auto_relate(self, node: RingNode, min_shared: int = 2) -> None:
        """Auto-detect related rings by keyword overlap."""
        if not node.keywords:
            return

        candidates: Counter = Counter()
        for word in set(node.keywords):
            for ring_id in self._index.get(word, set()):
                if ring_id != node.id:
                    candidates[ring_id] += 1

        for ring_id, shared in candidates.most_common(3):
            if shared >= min_shared:
                weight = min(shared / max(len(node.keywords), 1), 1.0)
                self.connect(node.id, ring_id, "related", round(weight, 2))

    # ── Connect ──────────────────────────────────────────────────

    def connect(
        self,
        source_id: str,
        target_id: str,
        edge_type: str = "related",
        weight: float = 0.5,
    ) -> RingEdge | None:
        """Create a directed edge between two rings."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        for e in self.edges:
            if e.source == source_id and e.target == target_id and e.edge_type == edge_type:
                e.weight = max(e.weight, weight)
                return e

        edge = RingEdge(source_id, target_id, edge_type, weight)
        self.edges.append(edge)
        self._adjacency[source_id].append(target_id)
        self._reverse[target_id].append(source_id)
        return edge

    # ── Query (TF-IDF, zero deps) ────────────────────────────────

    def query(self, topic: str, top_k: int = 5) -> list[RingNode]:
        """Search rings by keyword relevance.

        TF-IDF scoring: rarer words across the corpus score higher.
        Graph centrality bonus: well-connected rings rank higher.
        Compressed rings are excluded.
        """
        if not self.nodes:
            return []

        words = _tokenize(topic)
        if not words:
            active = [n for n in self.nodes.values() if not n.compressed]
            return sorted(active, key=lambda n: n.timestamp, reverse=True)[:top_k]

        n_total = max(len(self.nodes), 1)
        scores: Counter = Counter()

        for word in words:
            matching = self._index.get(word, set())
            if not matching:
                continue
            idf = math.log((n_total + 1) / (len(matching) + 1)) + 1.0
            for ring_id in matching:
                if not self.nodes[ring_id].compressed:
                    scores[ring_id] += idf

        for ring_id in scores:
            n_edges = len(self._adjacency.get(ring_id, []))
            n_edges += len(self._reverse.get(ring_id, []))
            scores[ring_id] *= (1.0 + min(n_edges, 10) * 0.05)

        return [self.nodes[rid] for rid, _ in scores.most_common(top_k)]

    # ── Fractal Themes ───────────────────────────────────────────

    def themes(self, depth: int = 1) -> dict[str, list[RingNode]]:
        """Fractal clustering at multiple scales.

        Depth 1: Broad themes by most frequent keywords.
        Depth 2+: Sub-themes within each theme.
        """
        if not self.nodes:
            return {}

        all_kw: Counter = Counter()
        for n in self.nodes.values():
            if not n.compressed:
                all_kw.update(set(n.keywords))

        if not all_kw:
            return {"general": [n for n in self.nodes.values() if not n.compressed]}

        n_themes = max(3, min(len(all_kw), 12))
        theme_words = [w for w, _ in all_kw.most_common(n_themes)]

        clusters: dict[str, list[RingNode]] = defaultdict(list)
        assigned: set[str] = set()

        for word in theme_words:
            for ring_id in self._index.get(word, set()):
                if ring_id not in assigned and not self.nodes[ring_id].compressed:
                    clusters[word].append(self.nodes[ring_id])
                    assigned.add(ring_id)

        for ring_id, node in self.nodes.items():
            if ring_id not in assigned and not node.compressed:
                clusters["other"].append(node)

        if depth >= 2:
            refined: dict[str, list[RingNode]] = {}
            for theme, rings in clusters.items():
                if len(rings) <= 3:
                    refined[theme] = rings
                    continue
                sub_kw: Counter = Counter()
                for r in rings:
                    sub_kw.update(w for w in set(r.keywords) if w != theme)
                if sub_kw:
                    top_sub = sub_kw.most_common(1)[0][0]
                    sub_a = [r for r in rings if top_sub in r.keywords]
                    sub_b = [r for r in rings if top_sub not in r.keywords]
                    if sub_a and sub_b:
                        refined[f"{theme}/{top_sub}"] = sub_a
                        refined[f"{theme}/other"] = sub_b
                    else:
                        refined[theme] = rings
                else:
                    refined[theme] = rings
            return refined

        return dict(clusters)

    # ── Compression ──────────────────────────────────────────────

    def compress(
        self,
        min_age_sec: float = 3600.0,
        max_cluster: int = 5,
    ) -> list[RingNode]:
        """Compress old rings into denser summary rings.

        Like tree rings: the core is dense, the outer is fresh.
        Originals are marked compressed, not deleted.
        """
        now = time.time()
        old = [
            n for n in self.nodes.values()
            if not n.compressed and n.ring_type != "summary"
            and (now - n.timestamp) > min_age_sec
        ]

        if len(old) < 2:
            return []

        clusters: dict[str, list[RingNode]] = defaultdict(list)
        for ring in old:
            key = ring.keywords[0] if ring.keywords else "general"
            clusters[key].append(ring)

        summaries: list[RingNode] = []

        for theme, rings in clusters.items():
            if len(rings) < 2:
                continue

            batch = rings[:max_cluster]
            merged = f"[{theme}] " + " | ".join(r.content for r in batch)
            summary = self.add(merged, ring_type="summary")

            for r in batch:
                r.compressed = True
                self.connect(r.id, summary.id, "compressed_into", 0.9)

            summaries.append(summary)

        return summaries

    # ── Traversal ────────────────────────────────────────────────

    def ancestors(self, ring_id: str, max_depth: int = 10) -> list[RingNode]:
        """Rings that caused this ring. Walks caused_by edges outward."""
        visited: set[str] = set()
        result: list[RingNode] = []

        def _walk(rid: str, d: int) -> None:
            if d > max_depth or rid in visited:
                return
            visited.add(rid)
            for e in self.edges:
                if e.source == rid and e.edge_type in ("caused_by", "deepens"):
                    if e.target in self.nodes:
                        result.append(self.nodes[e.target])
                        _walk(e.target, d + 1)

        _walk(ring_id, 0)
        return result

    def descendants(self, ring_id: str, max_depth: int = 10) -> list[RingNode]:
        """Rings caused BY this ring. Walks caused_by edges inward."""
        visited: set[str] = set()
        result: list[RingNode] = []

        def _walk(rid: str, d: int) -> None:
            if d > max_depth or rid in visited:
                return
            visited.add(rid)
            for e in self.edges:
                if e.target == rid and e.edge_type in ("caused_by", "deepens"):
                    if e.source in self.nodes:
                        result.append(self.nodes[e.source])
                        _walk(e.source, d + 1)

        _walk(ring_id, 0)
        return result

    def neighbors(self, ring_id: str) -> list[tuple[RingNode, str, float]]:
        """All directly connected rings with edge type and weight."""
        result = []
        for e in self.edges:
            if e.source == ring_id and e.target in self.nodes:
                result.append((self.nodes[e.target], e.edge_type, e.weight))
            elif e.target == ring_id and e.source in self.nodes:
                result.append((self.nodes[e.source], e.edge_type, e.weight))
        return result

    # ── Context Injection ────────────────────────────────────────

    def to_context(self, prompt: str, max_rings: int = 10) -> str:
        """Generate context from relevant rings for system prompt injection.

        THE method that makes rings useful. Turns the graph into context
        that actually improves model responses.

        1. Query by prompt keywords (TF-IDF)
        2. Expand via graph edges (related rings)
        3. Deduplicate and rank
        4. Format as structured context
        """
        if not self.nodes:
            return ""

        relevant = self.query(prompt, top_k=max_rings)

        if not relevant:
            active = [n for n in self.nodes.values() if not n.compressed]
            relevant = sorted(active, key=lambda n: n.timestamp, reverse=True)[:max_rings]

        # Expand via edges (neighbors of top results)
        expanded: set[str] = {r.id for r in relevant}
        for r in relevant[:3]:
            for neighbor, _, weight in self.neighbors(r.id):
                if neighbor.id not in expanded and not neighbor.compressed and weight > 0.3:
                    relevant.append(neighbor)
                    expanded.add(neighbor.id)
                    if len(relevant) >= max_rings:
                        break

        n_active = sum(1 for n in self.nodes.values() if not n.compressed)
        lines = [f"Organic memory ({len(relevant)} relevant from {n_active} rings):"]

        for r in relevant[:max_rings]:
            prefix = "  *" if r.ring_type == "paradigm" else "  -"
            lines.append(f"{prefix} {r.content}")

        themes = self.themes(depth=1)
        if len(themes) > 1:
            theme_str = ", ".join(
                f"{k}({len(v)})" for k, v in sorted(
                    themes.items(), key=lambda x: len(x[1]), reverse=True,
                )[:5]
            )
            lines.append(f"  Themes: {theme_str}")

        lines.append("Build on these learnings where relevant.")
        return "\n".join(lines)

    # ── Fractal Summary ──────────────────────────────────────────

    def fractal_summary(self) -> str:
        """Multi-scale view. Like zooming out on a fractal."""
        if not self.nodes:
            return "Empty graph. No rings yet."

        active = sum(1 for n in self.nodes.values() if not n.compressed)
        compressed = self.count - active

        lines = [f"Ring Graph: {active} active, {compressed} compressed, {len(self.edges)} edges"]

        themes = self.themes(depth=1)
        if themes:
            lines.append("Themes:")
            for theme, rings in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True):
                lines.append(f"  {theme}: {len(rings)} rings")

        conn: Counter = Counter()
        for e in self.edges:
            conn[e.source] += 1
            conn[e.target] += 1

        if conn:
            lines.append("Hub rings:")
            for rid, cnt in conn.most_common(3):
                if rid in self.nodes:
                    lines.append(f"  [{rid}] {cnt} edges: {self.nodes[rid].content[:60]}")

        return "\n".join(lines)

    # ── Export / Import ──────────────────────────────────────────

    def export_rings(self) -> dict:
        """Export for transfer between organisms. Strips timing."""
        return {
            "version": 1,
            "rings": [
                {"content": n.content, "ring_type": n.ring_type, "keywords": n.keywords}
                for n in self.nodes.values()
                if not n.compressed and n.ring_type != "summary"
            ],
            "edges": [
                {
                    "source_content": self.nodes.get(e.source, RingNode("", "")).content,
                    "target_content": self.nodes.get(e.target, RingNode("", "")).content,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                }
                for e in self.edges
                if e.edge_type in ("caused_by", "related", "deepens")
            ],
        }

    @classmethod
    def import_rings(cls, data: dict) -> "RingGraph":
        """Import rings from export. Rebuilds graph structure."""
        graph = cls()
        try:
            for rd in data.get("rings", []):
                graph.add(str(rd.get("content", "")), str(rd.get("ring_type", "learning")))
        except (TypeError, ValueError, KeyError):
            pass
        return graph

    # ── Persistence ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize full graph."""
        return {
            "version": 1,
            "next_id": self._next_id,
            "nodes": {
                rid: {
                    "content": n.content,
                    "ring_type": n.ring_type,
                    "timestamp": n.timestamp,
                    "depth": n.depth,
                    "hex_coord": n.hex_coord,
                    "keywords": n.keywords,
                    "compressed": n.compressed,
                }
                for rid, n in self.nodes.items()
            },
            "edges": [
                {"source": e.source, "target": e.target,
                 "edge_type": e.edge_type, "weight": e.weight}
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RingGraph":
        """Restore from serialized. Bad data = fresh graph (never crash)."""
        graph = cls()
        try:
            graph._next_id = int(data.get("next_id", 0))

            for rid, nd in data.get("nodes", {}).items():
                keywords = nd.get("keywords", [])
                if not keywords:
                    keywords = _tokenize(str(nd.get("content", "")))

                node = RingNode(
                    id=rid,
                    content=str(nd.get("content", "")),
                    ring_type=str(nd.get("ring_type", "learning")),
                    timestamp=float(nd.get("timestamp", time.time())),
                    depth=int(nd.get("depth", 0)),
                    hex_coord=nd.get("hex_coord"),
                    keywords=keywords,
                    compressed=bool(nd.get("compressed", False)),
                )
                graph.nodes[rid] = node

                for word in set(keywords):
                    graph._index[word].add(rid)

            for ed in data.get("edges", []):
                source = str(ed.get("source", ""))
                target = str(ed.get("target", ""))
                if source in graph.nodes and target in graph.nodes:
                    edge = RingEdge(
                        source=source, target=target,
                        edge_type=str(ed.get("edge_type", "related")),
                        weight=float(ed.get("weight", 0.5)),
                    )
                    graph.edges.append(edge)
                    graph._adjacency[source].append(target)
                    graph._reverse[target].append(source)
        except (TypeError, ValueError, KeyError):
            return cls()

        return graph

    # ── Properties ───────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self.nodes)

    @property
    def active_count(self) -> int:
        return sum(1 for n in self.nodes.values() if not n.compressed)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def summary(self) -> dict:
        """Stats for vitals."""
        by_type: Counter = Counter()
        for n in self.nodes.values():
            if not n.compressed:
                by_type[n.ring_type] += 1

        return {
            "total": self.count,
            "active": self.active_count,
            "compressed": self.count - self.active_count,
            "edges": self.edge_count,
            "by_type": dict(by_type),
        }
