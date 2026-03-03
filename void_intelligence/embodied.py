"""
void_intelligence.embodied --- Embodied Memory.

The industry stores memory as text. We store memory as LIVED EXPERIENCE.

Biological memory is not a database. It's embodied:
    - Memories have ORIGIN (where did I learn this?)
    - Memories DECAY (recent is vivid, old is faint)
    - Emotional memories RESIST decay (amygdala effect)
    - Used memories get STRONGER (hippocampal reinforcement)
    - Similar memories CONSOLIDATE (sleep consolidation)

This is the bridge between the real world (Plauds, WhatsApp,
calendar events, conversations) and the organism's internal memory.

Usage:
    from void_intelligence.embodied import EmbodiedMemory, MemorySource

    mem = EmbodiedMemory()

    # Ingest from different sources
    mem.ingest("Julian mentioned burnout at 2am", MemorySource.PLAUD,
               domain="health", emotional_weight=0.8)
    mem.ingest("Invoice #42 overdue 14 days", MemorySource.OBSERVATION,
               domain="business")

    # Recall with temporal + emotional weighting
    atoms = mem.recall("energy levels affecting work")

    # Decay (call periodically)
    faded = mem.decay()

    # Reinforce (when memory was useful)
    mem.reinforce(atom_id, impact=0.7)

    # Inject into pipeline
    ir_atoms = mem.to_pipeline_atoms("How is Julian doing?")

The industry builds RAG pipelines.
We build organisms that REMEMBER.
"""

from __future__ import annotations

import math
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from void_intelligence.ir import Atom


# ── Memory Source ─────────────────────────────────────────

class MemorySource(Enum):
    """Where a memory came from. The BODY that experienced it."""

    PLAUD = "plaud"              # Voice recording (Julian's breath, literally)
    WHATSAPP = "whatsapp"        # Conversation
    CALENDAR = "calendar"        # Scheduled event
    EMAIL = "email"              # Email exchange
    OBSERVATION = "observation"  # System-detected pattern
    RESONANCE = "resonance"      # Born from a ~ cycle (system taught itself)
    MANUAL = "manual"            # Julian told us directly
    CONSOLIDATION = "consolidation"  # Born from memory consolidation


# ── Memory Atom ───────────────────────────────────────────

@dataclass
class MemoryAtom:
    """An embodied memory. Not just text --- grounded in lived experience.

    Like a neuron in the hippocampus:
        - Fires when relevant context appears (recall)
        - Strengthens when activated (reinforcement)
        - Weakens when unused (decay)
        - Emotional memories resist decay (amygdala)
        - Eventually consolidates into semantic memory
    """

    id: str
    content: str
    source: MemorySource
    domain: str = "general"
    timestamp: float = field(default_factory=time.time)

    # Embodied properties
    emotional_weight: float = 0.0  # 0-1: emotional intensity. High = resists decay.
    strength: float = 1.0          # 0-1: current vividness. Decays over time.
    access_count: int = 0          # How many times recalled
    last_accessed: float = 0.0     # When last recalled

    # Source-specific metadata
    metadata: dict = field(default_factory=dict)

    # Indexing
    keywords: list[str] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        """Is this memory still vivid enough to recall?"""
        return self.strength > 0.05

    @property
    def age_hours(self) -> float:
        """How old is this memory in hours?"""
        return (time.time() - self.timestamp) / 3600

    @property
    def effective_strength(self) -> float:
        """Strength weighted by recency of access.

        Recently accessed memories are more available
        even if base strength has decayed.
        """
        if self.last_accessed <= 0:
            return self.strength

        hours_since_access = (time.time() - self.last_accessed) / 3600
        recency_boost = 0.2 / (1.0 + hours_since_access)
        return min(1.0, self.strength + recency_boost)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content[:200],
            "source": self.source.value,
            "domain": self.domain,
            "timestamp": self.timestamp,
            "emotional_weight": round(self.emotional_weight, 3),
            "strength": round(self.strength, 3),
            "effective_strength": round(self.effective_strength, 3),
            "access_count": self.access_count,
            "age_hours": round(self.age_hours, 1),
            "alive": self.alive,
            "metadata": self.metadata,
        }


# ── Decay Curves ──────────────────────────────────────────

def _ebbinghaus_decay(
    age_hours: float,
    emotional_weight: float = 0.0,
    half_life_hours: float = 24.0,
) -> float:
    """Ebbinghaus forgetting curve, modified by emotion.

    Base: strength = 2^(-age/half_life)
    Emotion: half_life *= (1 + emotional_weight * 4)
        -> neutral memory: half_life = 24h
        -> emotional (0.5): half_life = 72h (3x slower decay)
        -> intense (1.0): half_life = 120h (5x slower decay)

    This is the amygdala effect: emotional memories persist.
    """
    effective_half_life = half_life_hours * (1.0 + emotional_weight * 4.0)
    return math.pow(2, -age_hours / effective_half_life)


# ── Tokenization ──────────────────────────────────────────

_STOP = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "and", "but", "or",
    "not", "no", "so", "if", "that", "this", "it", "its",
    "der", "die", "das", "ein", "eine", "und", "oder", "aber",
    "nicht", "ist", "sind", "war", "hat", "mit", "von", "zu",
})

import re
_WORD_RE = re.compile(r"[a-z0-9äöüß]{3,}")


def _tokenize(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP]


# ── Embodied Memory ──────────────────────────────────────

class EmbodiedMemory:
    """The organism's embodied memory. Memories decay, resonate, and evolve.

    Not a vector database. Not a flat list. A LIVING memory system
    where memories are born, strengthen, decay, consolidate, and die.

    Like hippocampal memory:
        ingest()      = encoding (new experience enters memory)
        recall()      = retrieval (relevant memories surface)
        reinforce()   = consolidation (used memories get stronger)
        decay()       = forgetting (unused memories fade)
        consolidate() = sleep consolidation (similar memories merge)

    Usage:
        mem = EmbodiedMemory()
        mem.ingest("Client mentioned budget concerns", MemorySource.PLAUD,
                   domain="business", emotional_weight=0.6)

        relevant = mem.recall("pricing discussion")
        for atom in relevant:
            print(f"{atom.content} (strength={atom.strength:.2f})")
    """

    def __init__(
        self,
        *,
        half_life_hours: float = 24.0,
        decay_floor: float = 0.05,
        consolidation_threshold: float = 0.3,
    ) -> None:
        self._atoms: dict[str, MemoryAtom] = {}
        self._index: dict[str, set[str]] = defaultdict(set)  # keyword -> atom_ids
        self._half_life = half_life_hours
        self._decay_floor = decay_floor
        self._consolidation_threshold = consolidation_threshold

    # ── Ingest (Encoding) ────────────────────────────────

    def ingest(
        self,
        content: str,
        source: MemorySource,
        *,
        domain: str = "general",
        emotional_weight: float = 0.0,
        metadata: dict | None = None,
        timestamp: float | None = None,
    ) -> MemoryAtom:
        """Encode a new memory. Like hippocampal encoding.

        Args:
            content: What happened / what was learned.
            source: Where this memory came from (plaud, whatsapp, etc.)
            domain: Which life domain (health, business, etc.)
            emotional_weight: 0-1. Higher = resists decay.
            metadata: Source-specific data (speaker, duration, etc.)
            timestamp: Override timestamp (for importing historical data).
        """
        atom_id = f"m_{uuid.uuid4().hex[:8]}"
        keywords = _tokenize(content)

        atom = MemoryAtom(
            id=atom_id,
            content=content,
            source=source,
            domain=domain,
            timestamp=timestamp or time.time(),
            emotional_weight=min(1.0, max(0.0, emotional_weight)),
            strength=1.0,
            metadata=metadata or {},
            keywords=keywords,
        )

        self._atoms[atom_id] = atom

        for word in set(keywords):
            self._index[word].add(atom_id)

        return atom

    # ── Recall (Retrieval) ───────────────────────────────

    def recall(
        self,
        query: str,
        *,
        top_k: int = 5,
        min_strength: float = 0.05,
        domain: str | None = None,
        source: MemorySource | None = None,
    ) -> list[MemoryAtom]:
        """Recall relevant memories. Strength-weighted retrieval.

        Like hippocampal retrieval: memories compete for activation.
        Stronger memories (recent, emotional, frequently accessed) win.

        Retrieval itself REINFORCES the memory (testing effect).
        """
        query_words = set(_tokenize(query))
        if not query_words:
            return []

        # Score candidates by keyword overlap * effective_strength
        scores: dict[str, float] = {}
        for word in query_words:
            for atom_id in self._index.get(word, set()):
                atom = self._atoms.get(atom_id)
                if atom is None or not atom.alive:
                    continue
                if atom.strength < min_strength:
                    continue
                if domain and atom.domain != domain:
                    continue
                if source and atom.source != source:
                    continue

                # Overlap score
                atom_words = set(atom.keywords)
                overlap = len(query_words & atom_words) / max(len(query_words | atom_words), 1)
                score = overlap * atom.effective_strength
                scores[atom_id] = max(scores.get(atom_id, 0), score)

        # Sort by score, take top_k
        top_ids = sorted(scores, key=lambda k: scores[k], reverse=True)[:top_k]

        results = []
        for atom_id in top_ids:
            atom = self._atoms[atom_id]
            # Retrieval reinforces memory (testing effect)
            atom.access_count += 1
            atom.last_accessed = time.time()
            results.append(atom)

        return results

    # ── Reinforce (Consolidation) ────────────────────────

    def reinforce(self, atom_id: str, impact: float = 0.1) -> None:
        """Strengthen a memory because it was useful.

        Called when a memory contributes to a successful breath cycle.
        Like hippocampal replay during rest: good memories get replayed.

        impact: 0.0 to 1.0. Higher = stronger reinforcement.
        """
        atom = self._atoms.get(atom_id)
        if atom is None:
            return

        boost = impact * 0.3  # max boost per reinforcement
        atom.strength = min(1.0, atom.strength + boost)
        atom.access_count += 1
        atom.last_accessed = time.time()

    # ── Decay (Forgetting) ───────────────────────────────

    def decay(self) -> int:
        """Apply time-based Ebbinghaus decay to all memories.

        Returns number of memories that faded below threshold.
        Call periodically (e.g., every breath cycle or every minute).

        Emotional memories decay slower (amygdala effect).
        Frequently accessed memories decay slower (spacing effect).
        """
        faded = 0
        for atom in self._atoms.values():
            if not atom.alive:
                continue

            base_decay = _ebbinghaus_decay(
                atom.age_hours,
                atom.emotional_weight,
                self._half_life,
            )

            # Access frequency bonus (spacing effect)
            access_bonus = min(0.3, atom.access_count * 0.02)
            atom.strength = min(1.0, base_decay + access_bonus)

            if atom.strength <= self._decay_floor:
                faded += 1

        return faded

    # ── Consolidate (Sleep Consolidation) ────────────────

    def consolidate(self) -> int:
        """Merge similar weak memories into stronger summary memories.

        Like hippocampal consolidation during sleep:
        Similar episodic memories become one semantic memory.

        Weak memories (below threshold) with overlapping keywords
        get merged into a single stronger memory.

        Returns number of new consolidated memories created.
        """
        # Find weak memories grouped by domain
        weak_by_domain: dict[str, list[MemoryAtom]] = defaultdict(list)
        for atom in self._atoms.values():
            if atom.alive and atom.strength < self._consolidation_threshold:
                weak_by_domain[atom.domain].append(atom)

        consolidated = 0

        for domain, atoms in weak_by_domain.items():
            if len(atoms) < 2:
                continue

            # Group by keyword overlap
            groups = self._find_similar_groups(atoms, min_overlap=2)

            for group in groups:
                if len(group) < 2:
                    continue

                # Merge into one consolidated memory
                merged_content = " | ".join(a.content[:80] for a in group[:5])
                max_emotional = max(a.emotional_weight for a in group)
                avg_strength = sum(a.strength for a in group) / len(group)

                new_atom = self.ingest(
                    content=f"[consolidated {len(group)}x] {merged_content}",
                    source=MemorySource.CONSOLIDATION,
                    domain=domain,
                    emotional_weight=max_emotional,
                )
                # Consolidation creates a stronger memory
                new_atom.strength = min(1.0, avg_strength * 1.5 + 0.1)

                # Mark originals as faded
                for old in group:
                    old.strength = 0.0

                consolidated += 1

        return consolidated

    def _find_similar_groups(
        self,
        atoms: list[MemoryAtom],
        min_overlap: int = 2,
    ) -> list[list[MemoryAtom]]:
        """Group atoms by keyword overlap. Simple greedy clustering."""
        used: set[str] = set()
        groups: list[list[MemoryAtom]] = []

        for i, a in enumerate(atoms):
            if a.id in used:
                continue
            group = [a]
            used.add(a.id)
            a_words = set(a.keywords)

            for b in atoms[i + 1:]:
                if b.id in used:
                    continue
                b_words = set(b.keywords)
                if len(a_words & b_words) >= min_overlap:
                    group.append(b)
                    used.add(b.id)

            if len(group) >= 2:
                groups.append(group)

        return groups

    # ── Pipeline Integration ─────────────────────────────

    def to_pipeline_atoms(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> list["Atom"]:
        """Convert recalled memories to IR Atoms for pipeline injection.

        This is the bridge: embodied memories become atoms that
        enter the .x->[]~ pipeline at the . (atomize) stage.
        """
        from void_intelligence.ir import Atom

        recalled = self.recall(query, top_k=top_k)
        ir_atoms = []

        for mem in recalled:
            ir_atoms.append(Atom(
                domain=mem.domain,
                type=f"memory_{mem.source.value}",
                value={
                    "content": mem.content[:200],
                    "strength": round(mem.effective_strength, 3),
                    "emotional_weight": round(mem.emotional_weight, 2),
                    "age_hours": round(mem.age_hours, 1),
                    "source": mem.source.value,
                    "memory_id": mem.id,
                },
                source="embodied_memory",
                timestamp=mem.timestamp,
            ))

        return ir_atoms

    # ── Introspection ────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._atoms)

    @property
    def alive_count(self) -> int:
        return sum(1 for a in self._atoms.values() if a.alive)

    def by_source(self) -> dict[str, int]:
        """Count memories by source."""
        counts: dict[str, int] = {}
        for atom in self._atoms.values():
            if atom.alive:
                key = atom.source.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    def by_domain(self) -> dict[str, int]:
        """Count memories by domain."""
        counts: dict[str, int] = {}
        for atom in self._atoms.values():
            if atom.alive:
                counts[atom.domain] = counts.get(atom.domain, 0) + 1
        return counts

    def strongest(self, n: int = 5) -> list[MemoryAtom]:
        """Top N strongest memories."""
        alive = [a for a in self._atoms.values() if a.alive]
        alive.sort(key=lambda a: a.effective_strength, reverse=True)
        return alive[:n]

    def summary(self) -> dict:
        """Memory system vitals."""
        alive = [a for a in self._atoms.values() if a.alive]
        return {
            "total": self.count,
            "alive": self.alive_count,
            "by_source": self.by_source(),
            "by_domain": self.by_domain(),
            "avg_strength": round(
                sum(a.strength for a in alive) / max(len(alive), 1), 3,
            ),
            "avg_emotional": round(
                sum(a.emotional_weight for a in alive) / max(len(alive), 1), 3,
            ),
            "oldest_hours": round(
                max((a.age_hours for a in alive), default=0), 1,
            ),
        }

    # ── Persistence ──────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize all memories."""
        return {
            "version": 1,
            "half_life_hours": self._half_life,
            "decay_floor": self._decay_floor,
            "consolidation_threshold": self._consolidation_threshold,
            "atoms": [a.to_dict() for a in self._atoms.values() if a.alive],
            "summary": self.summary(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmbodiedMemory":
        """Restore from serialized data."""
        mem = cls(
            half_life_hours=float(data.get("half_life_hours", 24.0)),
            decay_floor=float(data.get("decay_floor", 0.05)),
            consolidation_threshold=float(data.get("consolidation_threshold", 0.3)),
        )
        for ad in data.get("atoms", []):
            try:
                source = MemorySource(ad.get("source", "manual"))
            except ValueError:
                source = MemorySource.MANUAL

            atom = mem.ingest(
                content=ad.get("content", ""),
                source=source,
                domain=ad.get("domain", "general"),
                emotional_weight=float(ad.get("emotional_weight", 0.0)),
                metadata=ad.get("metadata", {}),
                timestamp=float(ad.get("timestamp", time.time())),
            )
            atom.strength = float(ad.get("strength", 1.0))
            atom.access_count = int(ad.get("access_count", 0))

        return mem
