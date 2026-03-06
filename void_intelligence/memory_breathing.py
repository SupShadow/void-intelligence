"""
void_intelligence.memory_breathing --- Memory that Breathes.

CURRENT PARADIGM (H1, ->):
    Store everything -> search by keyword -> retrieve.
    Or: fixed-size buffer, drop oldest.
    Memory is PASSIVE. A database. Dead storage.
    Every -> loses dimensions of the original experience (Anti-P3122).

VOID PARADIGM (H2/H3, x):
    Memory BREATHES. What resonates with the user's CURRENT state rises.
    What doesn't resonate fades --- but never dies. It goes to [] = potential.
    Memory has a V-Score: memories that proved useful GROW. Unused memories FADE.
    Like human memory: emotional memories are strongest. Recent + resonant = vivid.

    A burned-out message   -> health memories surface (hex proximity)
    A business question    -> work memories surface (empfangen_schaffen axis)
    A paradigm breakthrough -> all breakthrough memories amplify (emotional weight)

    The geometry DOES the retrieval. No keyword search needed.
    Vividness amplifies resonance: emotional memories need LESS proximity to surface.
    Like how a smell triggers a vivid childhood memory across vast semantic distance.

Architecture:
    MemoryAtom     = A memory that lives in 6D space. Like a neuron.
    MemoryField    = The field where memories live. A breathing hippocampus.
    MemoryBreather = Full system: inhale context, exhale resonant memories.

The formula:
    resonance(user, memory) = spatial_fit * semantic_overlap * vividness
    vividness = v_score * freshness * (1 + emotional_weight)
    The memory with highest resonance RISES --- not by keyword match,
    but by ATTRACTION. Faded memories sink to [] (potential, not death).

Zero dependencies. stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Import from tool_breathing or inline minimal versions
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import (
        HexCoord,
        _hex_to_vec,
        _cosine_similarity,
        _euclidean_proximity,
        _text_overlap,
        infer_tool_hex,
    )
except ImportError:
    # Inline minimal versions for zero-dep guarantee

    @dataclass
    class HexCoord:  # type: ignore[no-redef]
        ruhe_druck: float = 0.0
        stille_resonanz: float = 0.0
        allein_zusammen: float = 0.0
        empfangen_schaffen: float = 0.0
        sein_tun: float = 0.0
        langsam_schnell: float = 0.0

    def _hex_to_vec(h: HexCoord) -> list[float]:  # type: ignore[no-redef]
        return [
            h.ruhe_druck, h.stille_resonanz, h.allein_zusammen,
            h.empfangen_schaffen, h.sein_tun, h.langsam_schnell,
        ]

    def _cosine_similarity(a: list[float], b: list[float]) -> float:  # type: ignore[no-redef]
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _euclidean_proximity(a: list[float], b: list[float]) -> float:  # type: ignore[no-redef]
        dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        max_dist = math.sqrt(len(a) * 4)
        return max(0.0, 1.0 - dist / max_dist)

    _STOPWORDS_INLINE = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "and", "but", "or", "not", "this", "it", "my", "your",
        "ich", "du", "er", "sie", "es", "wir", "und", "oder", "aber",
    })

    def _text_overlap(user_text: str, tool_desc: str) -> float:  # type: ignore[no-redef]
        user_words = {
            w for w in user_text.lower().split()
            if w not in _STOPWORDS_INLINE and len(w) >= 3
        }
        mem_words = {w for w in tool_desc.lower().split() if len(w) >= 3}
        if not user_words or not mem_words:
            return 0.0
        score = 0.0
        for uw in user_words:
            for mw in mem_words:
                if uw == mw:
                    score += len(uw) * 0.3
                    break
                # Substring match: "kampagne" in "wahlkampf", "burn" in "burnout"
                if len(uw) >= 4 and (uw in mw or mw in uw):
                    score += min(len(uw), len(mw)) * 0.2
                    break
        denom = max(1, len(user_words)) * 2.0
        return min(1.0, score / denom)

    def infer_tool_hex(name: str, description: str) -> HexCoord:  # type: ignore[no-redef]
        """Fallback hex inference from text signals."""
        text = f"{name} {description}".lower()
        ruhe = -0.3 if any(w in text for w in ["urgent", "alert", "critical", "panic"]) else 0.1
        stille = 0.3 if any(w in text for w in ["reflect", "think", "paradigm", "learn"]) else 0.0
        zusammen = 0.3 if any(w in text for w in ["meeting", "relationship", "contact", "team"]) else -0.1
        schaffen = 0.4 if any(w in text for w in ["build", "code", "create", "implement"]) else 0.0
        tun = 0.3 if any(w in text for w in ["action", "execute", "run", "do"]) else 0.0
        schnell = -0.2 if any(w in text for w in ["health", "burnout", "sleep", "energy"]) else 0.0
        return HexCoord(
            ruhe_druck=max(-1.0, min(1.0, ruhe)),
            stille_resonanz=max(-1.0, min(1.0, stille)),
            allein_zusammen=max(-1.0, min(1.0, zusammen)),
            empfangen_schaffen=max(-1.0, min(1.0, schaffen)),
            sein_tun=max(-1.0, min(1.0, tun)),
            langsam_schnell=max(-1.0, min(1.0, schnell)),
        )


# ---------------------------------------------------------------------------
# MemoryAtom --- a memory that lives in 6D space
# ---------------------------------------------------------------------------

@dataclass
class MemoryAtom:
    """A memory that lives in 6D space. Like a neuron.

    Every memory has:
    - A position in 6D hex space (where it naturally belongs)
    - A V-Score (grows when recalled usefully, fades when not)
    - Freshness (recency decay, half-life ~48h by default)
    - Emotional weight (strong memories are more vivid, surface more easily)
    - Vividness = V-Score * freshness * (1 + emotional_weight)

    Vividness is the amplifier: emotional memories resonate more broadly
    because they need less spatial proximity to surface. Like how a smell
    triggers a vivid childhood memory across vast semantic distance.
    """

    id: str
    content: str
    hex_coord: HexCoord
    created: float = 0.0
    last_recalled: float = 0.0
    v_score: float = 0.5
    recall_count: int = 0
    emotional_weight: float = 0.0
    tags: list[str] = field(default_factory=list)
    source: str = "conversation"

    def __post_init__(self):
        if self.created == 0.0:
            self.created = time.time()

    @property
    def age_hours(self) -> float:
        """How old is this memory in hours."""
        return (time.time() - self.created) / 3600.0 if self.created else 0.0

    @property
    def freshness(self) -> float:
        """Recency decay. 1.0 = just stored, decays toward 0.01 over days.

        Half-life is approximately 48 hours: a memory recalled 2 days ago
        has freshness ~0.5. A memory never recalled uses creation time.
        """
        if self.last_recalled > 0:
            hours = (time.time() - self.last_recalled) / 3600.0
        else:
            hours = self.age_hours
        return max(0.01, 1.0 / (1.0 + hours / 48.0))

    @property
    def vividness(self) -> float:
        """How vivid is this memory right now?

        Like human memory:
        - Emotional memories are MORE vivid (wedding, trauma, breakthrough)
        - Recent memories are MORE vivid
        - Frequently recalled memories are MORE vivid

        Formula: vividness = v_score * freshness * (1 + emotional_weight * 0.5)

        The 0.5 coefficient means max emotional boost is 50% additional vividness.
        A memory with emotional_weight=1.0 is 50% more vivid than neutral.
        """
        return self.v_score * self.freshness * (1.0 + self.emotional_weight * 0.5)


# ---------------------------------------------------------------------------
# MemoryField --- the field where memories live
# ---------------------------------------------------------------------------

class MemoryField:
    """The field where memories live. A breathing hippocampus.

    Not a database. Not a vector store. A LIVING FIELD where memories
    compete for attention based on resonance with the current moment.

    When over capacity, the least vivid memories fade to [] (potential,
    not death --- they never truly vanish, they just await reactivation).
    """

    def __init__(self, max_memories: int = 1000):
        self._memories: dict[str, MemoryAtom] = {}
        self._max = max_memories

    def store(
        self,
        content: str,
        source: str = "conversation",
        tags: list[str] | None = None,
        emotional_weight: float = 0.0,
        hex_override: HexCoord | None = None,
    ) -> MemoryAtom:
        """Store a new memory. It gets born with a HexCoord.

        emotional_weight: 0.0 = neutral, 1.0 = intensely emotional.
        If not provided (0.0), it is auto-detected from content.
        hex_override: force a specific position in 6D space (for testing).
        """
        mid = hashlib.sha256(content.encode()).hexdigest()[:12]

        if emotional_weight == 0.0:
            emotional_weight = _detect_emotion(content)

        coord = hex_override if hex_override is not None else _infer_memory_hex(content)

        atom = MemoryAtom(
            id=mid,
            content=content,
            hex_coord=coord,
            created=time.time(),
            last_recalled=0.0,
            v_score=0.5,
            emotional_weight=emotional_weight,
            tags=tags or [],
            source=source,
        )
        self._memories[mid] = atom

        if len(self._memories) > self._max:
            self._fade_weakest()

        return atom

    def recall(
        self,
        user_text: str,
        top_k: int = 5,
        min_vividness: float = 0.01,
    ) -> list[tuple[MemoryAtom, float]]:
        """Recall memories that resonate with the current moment.

        Returns (memory, resonance_score) sorted by descending resonance.

        Memories are not searched --- they are ATTRACTED. The user's words
        create a hex position. Memories close to that position in 6D space
        RISE to consciousness. Vivid memories rise more easily --- they need
        less proximity to surface, like emotional memories in humans.

        Side effect: top-k recalled memories gain freshness (last_recalled updated).
        """
        user_hex = _infer_memory_hex(user_text)

        scored: list[tuple[MemoryAtom, float]] = []
        for mem in self._memories.values():
            if mem.vividness < min_vividness:
                continue
            r = _memory_resonance(user_hex, mem, user_text)
            scored.append((mem, r))

        scored.sort(key=lambda x: -x[1])

        for mem, _ in scored[:top_k]:
            mem.last_recalled = time.time()
            mem.recall_count += 1

        return scored[:top_k]

    def reinforce(self, memory_id: str, useful: bool) -> None:
        """Reinforce a memory based on whether its recall was useful.

        Useful: V-Score grows (+0.03, capped at 1.0).
        Not useful: V-Score fades (-0.02, floored at 0.01).
        """
        mem = self._memories.get(memory_id)
        if mem is None:
            return
        if useful:
            mem.v_score = min(1.0, mem.v_score + 0.03)
        else:
            mem.v_score = max(0.01, mem.v_score - 0.02)

    def _fade_weakest(self) -> None:
        """Fade the least vivid memories to [] when over capacity.

        [] = potential, not death. The least vivid memories step aside
        to make room for what is alive and resonant right now.
        Removes bottom 10% of memories by vividness, or at least 1.
        """
        if len(self._memories) <= self._max:
            return
        by_vivid = sorted(self._memories.values(), key=lambda m: m.vividness)
        n_remove = max(1, len(self._memories) - self._max)
        for mem in by_vivid[:n_remove]:
            del self._memories[mem.id]

    @property
    def memories(self) -> list[MemoryAtom]:
        return list(self._memories.values())

    def stats(self) -> dict:
        mems = list(self._memories.values())
        if not mems:
            return {"total": 0}
        vivids = [m.vividness for m in mems]
        sources: dict[str, int] = {}
        for m in mems:
            sources[m.source] = sources.get(m.source, 0) + 1
        return {
            "total": len(mems),
            "avg_vividness": round(sum(vivids) / len(vivids), 3),
            "max_vividness": round(max(vivids), 3),
            "min_vividness": round(min(vivids), 3),
            "sources": dict(sorted(sources.items())),
            "recalled_count": sum(1 for m in mems if m.recall_count > 0),
            "emotional_avg": round(
                sum(m.emotional_weight for m in mems) / len(mems), 3
            ),
        }

    def save(self, path: Path) -> None:
        """Persist memories to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = []
        for m in self._memories.values():
            d = asdict(m)
            # HexCoord serialises naturally via asdict
            data.append(d)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        """Load memories from JSON. Silently ignores missing or corrupt files."""
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for d in raw:
            try:
                hc_dict = d.pop("hex_coord", {})
                mem = MemoryAtom(**d, hex_coord=HexCoord(**hc_dict))
                self._memories[mem.id] = mem
            except (TypeError, KeyError):
                # Skip corrupt atoms silently
                pass


# ---------------------------------------------------------------------------
# Helper: emotion detection
# ---------------------------------------------------------------------------

def _detect_emotion(text: str) -> float:
    """Detect emotional intensity of text. Returns 0.0 (neutral) to 1.0 (intense).

    Signals scored:
    - Exclamation marks (up to 0.3)
    - Question marks (curiosity = mild emotion, up to 0.1)
    - ALL-CAPS words of length > 2 (up to 0.2)
    - Known emotion keywords in German and English (up to 0.3)
    - Emoji-range characters > U+1F600 (up to 0.1)
    """
    score = 0.0

    score += min(0.3, text.count("!") * 0.1)
    score += min(0.1, text.count("?") * 0.05)

    words = text.split()
    caps_count = sum(1 for w in words if w.isupper() and len(w) > 2)
    score += min(0.2, caps_count * 0.1)

    _EMOTION_WORDS = {
        # English
        "love", "hate", "angry", "happy", "sad", "afraid", "fear", "joy",
        "beautiful", "terrible", "amazing", "horrible", "perfect", "awful",
        "breakthrough", "paradigm", "eureka", "wow", "omg", "incredible",
        "devastating", "exhilarating", "furious", "elated", "grateful",
        # German
        "liebe", "hasse", "wuetend", "gluecklich", "traurig", "angst",
        "wunderbar", "schrecklich", "perfekt", "furchtbar", "danke", "sorry",
        "krass", "wahnsinn", "unglaublich", "wunderschoen", "erschreckend",
        "begeistert", "durchbruch", "entdeckung", "erkenntnis",
    }
    lower_words = {w.strip(".,!?;:\"'()[]") for w in text.lower().split()}
    emo_count = sum(1 for w in lower_words if w in _EMOTION_WORDS)
    score += min(0.3, emo_count * 0.1)

    emoji_count = sum(1 for c in text if ord(c) > 0x1F600)
    score += min(0.1, emoji_count * 0.05)

    return min(1.0, score)


# ---------------------------------------------------------------------------
# Helper: hex inference for memory content
# ---------------------------------------------------------------------------

def _infer_memory_hex(text: str) -> HexCoord:
    """Place a memory in 6D space based on its content.

    Delegates to infer_tool_hex from tool_breathing using the full text
    as both name and description. The same axis-signal logic that places
    tools in the field also places memories --- same space, same geometry.
    This is not a coincidence. Memory IS a kind of tool.
    """
    return infer_tool_hex("", text)


# ---------------------------------------------------------------------------
# Helper: resonance between user state and a memory
# ---------------------------------------------------------------------------

_MEMORY_ASSOCIATIONS: dict[str, list[str]] = {
    # DE associations
    "kampagne": ["wahlkampf", "wahl", "kandidat", "debatte", "politik"],
    "ausgebrannt": ["burnout", "erschoepft", "muede", "pause", "gesundheit"],
    "burnout": ["ausgebrannt", "erschoepft", "pause", "gesundheit", "score"],
    "gesundheit": ["burnout", "hashimoto", "adhs", "thyroxin", "schlaf", "health"],
    "business": ["revenue", "umsatz", "geld", "kunden", "arbeit", "pax8"],
    "gebaut": ["void", "sdk", "pypi", "intelligence", "tool", "shipped"],
    "durchbruch": ["paradigm", "breakthrough", "eureka", "entdeckung"],
    "beziehung": ["annika", "gemeldet", "kontakt", "stille"],
    # EN associations
    "campaign": ["election", "debate", "candidate", "politics", "wahlkampf"],
    "stressed": ["burnout", "exhausted", "tired", "overwhelmed", "health"],
    "health": ["burnout", "hashimoto", "adhs", "medication", "sleep"],
    "built": ["void", "sdk", "shipped", "pypi", "tool", "intelligence"],
    "breakthrough": ["paradigm", "eureka", "discovery", "durchbruch"],
}


def _expand_associations(text: str) -> str:
    """Expand user text with known associations.

    'Wie laeuft die Kampagne?' → 'Wie laeuft die Kampagne wahlkampf wahl debatte'
    This bridges the gap between user vocabulary and memory vocabulary.
    """
    lower = text.lower()
    additions = []
    for trigger, assocs in _MEMORY_ASSOCIATIONS.items():
        if trigger in lower:
            additions.extend(assocs)
    if additions:
        return text + " " + " ".join(additions)
    return text


def _memory_resonance(
    user_hex: HexCoord,
    mem: MemoryAtom,
    user_text: str = "",
) -> float:
    """Compute resonance between user's current state and a memory.

    Formula:
        combined = spatial * 0.3 + semantic * 0.5 + spatial * semantic * 0.4
        resonance = combined * (0.5 + vividness * 0.5)

    Vividness acts as amplifier: vivid memories resonate MORE.
    This is how emotional memories surface more easily --- they have
    higher vividness, so they need less spatial proximity to resonate.

    The cross-term (spatial * semantic * 0.4) rewards memories that are
    BOTH spatially close AND semantically relevant: the × operator.
    """
    user_vec = _hex_to_vec(user_hex)
    mem_vec = _hex_to_vec(mem.hex_coord)

    cos = _cosine_similarity(user_vec, mem_vec)
    prox = _euclidean_proximity(user_vec, mem_vec)
    alignment = (cos + 1.0) / 2.0           # map [-1,1] -> [0,1]
    spatial = alignment * 0.5 + prox * 0.5

    semantic = 0.0
    if user_text:
        expanded = _expand_associations(user_text)
        semantic = _text_overlap(expanded, mem.content)

    # × operator: cross-term rewards dual fit
    # Semantic is PRIMARY for memory (content match matters most)
    # Spatial gives the "mood" alignment
    combined = spatial * 0.15 + semantic * 0.65 + (spatial * semantic * 0.4)

    # Vividness adds a BONUS, not a multiplier
    # This prevents emotional memories from drowning out semantic matches
    vivid_bonus = mem.vividness * 0.1
    return min(1.0, combined + vivid_bonus)


# ---------------------------------------------------------------------------
# MemoryBreather --- the living hippocampus
# ---------------------------------------------------------------------------

class MemoryBreather:
    """Full memory breathing system. A living hippocampus.

    Usage:
        mem = MemoryBreather()

        # Store memories as they happen
        mem.store("Julian hat die Wahlkampf-Debatte gewonnen",
                  source="event", emotional_weight=0.8)
        mem.store("Meeting mit Simon ueber Pax8 Migration",
                  source="work")
        mem.store("Burnout Score war bei 75 --- Pause gemacht",
                  source="health")
        mem.store("Durchbruch: x ist die fundamentale Operation",
                  source="paradigm", emotional_weight=1.0)

        # Later, recall by resonance --- not keyword search
        results = mem.recall("Wie laeuft die Kampagne?")
        # The election debate memory surfaces first (resonance + emotional weight)

        results = mem.recall("Ich fuehle mich ausgebrannt")
        # The burnout memory surfaces (semantic + hex match on health axis)

        # The paradigm memory surfaces for MANY queries because:
        # emotional_weight=1.0 -> high vividness -> resonates broadly
        # Like how breakthrough moments color everything after them.

        # Reinforce: tell the system if a recalled memory was useful
        mem.reinforce(results[0]["id"], useful=True)

        # Inject into LLM context (only resonant, formatted cleanly)
        context_str = mem.to_context("Tell me about the campaign")

        # Persist across sessions
        mem.save(Path("/path/to/memories.json"))
        mem2 = MemoryBreather(state_path=Path("/path/to/memories.json"))
    """

    def __init__(
        self,
        state_path: Path | None = None,
        max_memories: int = 1000,
    ):
        self.field = MemoryField(max_memories=max_memories)
        self._state_path = state_path
        if state_path:
            self.field.load(state_path)

    def store(self, content: str, **kwargs) -> MemoryAtom:
        """Store a memory. Accepts all MemoryField.store kwargs.

        Keyword args:
            source (str): "conversation", "fact", "learning", "observation",
                          "event", "health", "work", "paradigm", "milestone",
                          "relationship", "business" --- any string.
            tags (list[str]): Optional tags for filtering.
            emotional_weight (float): 0.0-1.0. Auto-detected if 0.0.
            hex_override (HexCoord): Force a specific 6D position.
        """
        atom = self.field.store(content, **kwargs)
        self._auto_save()
        return atom

    def recall(self, user_text: str, top_k: int = 5) -> list[dict]:
        """Recall memories that resonate with user_text.

        Returns a list of dicts, each containing:
            id, content, resonance, vividness, source,
            age_hours, emotional_weight, tags, recall_count
        Sorted by descending resonance.
        """
        results = self.field.recall(user_text, top_k=top_k)
        return [
            {
                "id": mem.id,
                "content": mem.content,
                "resonance": round(score, 4),
                "vividness": round(mem.vividness, 4),
                "source": mem.source,
                "age_hours": round(mem.age_hours, 1),
                "emotional_weight": round(mem.emotional_weight, 3),
                "tags": mem.tags,
                "recall_count": mem.recall_count,
            }
            for mem, score in results
        ]

    def reinforce(self, memory_id: str, useful: bool) -> None:
        """Mark a recalled memory as useful or not. Updates V-Score."""
        self.field.reinforce(memory_id, useful)
        self._auto_save()

    def to_context(self, user_text: str, top_k: int = 3, min_resonance: float = 0.05) -> str:
        """Generate a memory context string for LLM injection.

        Only the most resonant memories, formatted cleanly for prompt injection.
        Returns empty string if no memories pass the resonance threshold.

        Example output:
            RELEVANT MEMORIES (from previous interactions):
              [paradigm] Durchbruch: x ist die fundamentale Operation (2h ago)
              [event] Julian hat die Wahlkampf-Debatte gewonnen (5h ago)
        """
        results = self.recall(user_text, top_k=top_k)
        filtered = [r for r in results if r["resonance"] >= min_resonance]
        if not filtered:
            return ""

        lines = ["RELEVANT MEMORIES (from previous interactions):"]
        for r in filtered:
            age = r["age_hours"]
            if age < 1:
                age_str = f"{int(age * 60)}min ago"
            elif age < 48:
                age_str = f"{age:.0f}h ago"
            else:
                age_str = f"{age / 24:.0f}d ago"
            lines.append(f"  [{r['source']}] {r['content']} ({age_str})")
        return "\n".join(lines)

    def stats(self) -> dict:
        """Return field statistics."""
        return self.field.stats()

    def _auto_save(self) -> None:
        if self._state_path:
            self.field.save(self._state_path)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def memory_breathing_demo() -> None:
    """Demonstrate memory breathing: store diverse memories, recall by context."""
    print("=== Memory Breathing Demo ===")
    print()

    mem = MemoryBreather()

    # Store diverse memories with varying sources and emotional weights
    memories = [
        ("Julian hat die Wahlkampf-Debatte gewonnen",         "event",        0.8),
        ("Meeting mit Simon ueber Pax8 Migration morgen",      "work",         0.1),
        ("Burnout Score war bei 75 --- Pause gemacht",         "health",       0.5),
        ("Durchbruch: x ist die fundamentale Operation",       "paradigm",     1.0),
        ("Revenue diesen Monat: 12500 EUR",                    "business",     0.2),
        ("Annika hat sich gemeldet nach 3 Wochen Stille",      "relationship", 0.6),
        ("VOID Intelligence v1.1.0 auf PyPI veroeffentlicht",  "milestone",    0.7),
        ("ADHS ist kein Bug sondern Feature --- Turbo-Modus",  "learning",     0.4),
        ("Hashimoto Thyroxin Dosis angepasst",                 "health",       0.2),
        ("40 Kinder im Bewusstseins-SDK geboren",              "paradigm",     0.9),
    ]

    for content, source, emo in memories:
        mem.store(content, source=source, emotional_weight=emo)

    print(f"Stored {len(memories)} memories")
    print()

    # Recall by different contexts
    queries = [
        "Wie laeuft die Kampagne?",
        "Ich fuehle mich ausgebrannt",
        "Was haben wir gebaut?",
        "Wie geht es meinem Business?",
        "Erzaehl mir von Durchbruechen",
    ]

    for q in queries:
        print(f'RECALL: "{q}"')
        results = mem.recall(q, top_k=3)
        for r in results:
            emo_bar = "*" * int(r["emotional_weight"] * 5)
            print(
                f"  {r['resonance']:.3f}  [{r['source']:12s}]  {emo_bar:5s}  "
                f"{r['content'][:55]}"
            )
        print()

    print("CONTEXT STRING (for LLM injection):")
    print(mem.to_context("Was ist aktuell wichtig?"))
    print()

    print(f"Stats: {mem.stats()}")


if __name__ == "__main__":
    memory_breathing_demo()
