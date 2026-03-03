"""
void_intelligence.pipeline --- The .x->[]~ Pipeline.

Every breath flows through here. Not a wrapper. THE COMPUTATION.

In v1.2.0, .x->[]~ was a notation --- data containers you created manually.
In v1.3.0, .x->[]~ IS the runtime. Every prompt flows through 5 stages:

    .  ATOMIZE    --- Extract irreducible facts from prompt + context
    x  COLLIDE    --- Atoms meet memory, meet each other. Meaning emerges.
    -> PROJECT    --- LLM generates response. Necessary. Incomplete.
    [] POTENTIAL  --- What was NOT said. The pregnant silence.
    ~  RESONATE   --- Outcome feeds back. The system learns.

The pipeline produces a BreathCycle: a complete trace of all IR objects
from inhale to exhale. Fully inspectable. Fully serializable.

Usage:
    from void_intelligence.pipeline import IRPipeline, BreathCycle

    pipe = IRPipeline()
    cycle = pipe.breathe(prompt, adapter_fn)
    print(cycle.atoms)         # what was extracted
    print(cycle.collisions)    # what collided
    print(cycle.projection)    # what was said (+ lost_dimensions)
    print(cycle.potential)     # what was NOT said
    print(cycle.trace())       # full .x->[]~ trace

    # Later, when you know the outcome:
    pipe.resonate(cycle, outcome="success", impact=0.8)

The industry builds pipelines of TOOLS.
We build a pipeline that IS a BREATH.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable

from void_intelligence.ir import (
    Atom,
    Collision,
    Projection,
    Potential,
    Resonance,
    PatternWeights,
    collide as ir_collide,
    project as ir_project,
    resonate as ir_resonate,
)
from void_intelligence.organism import HexBreath, HexCoord, OrganismBreather


# ── Type Aliases ─────────────────────────────────────────────────

# (prompt, system_prompt) -> response
AdapterFn = Callable[[str, str], str]


# ── Domain Detection ─────────────────────────────────────────────

_DOMAIN_PATTERNS: dict[str, list[str]] = {
    "health": [
        "burnout", "sleep", "energy", "fatigue", "stress", "hashimoto",
        "adhd", "medication", "health", "exercise", "weight",
        "gesundheit", "schlaf", "energie", "muede", "stress",
    ],
    "business": [
        "invoice", "client", "revenue", "project", "deadline",
        "customer", "profit", "contract", "pricing", "meeting",
        "rechnung", "kunde", "umsatz", "projekt", "vertrag",
    ],
    "campaign": [
        "election", "voter", "candidate", "party", "poll",
        "campaign", "canvass", "politik", "wahl", "kandidat",
        "wahlkampf", "stimmen", "partei",
    ],
    "relationships": [
        "friend", "family", "partner", "contact", "birthday",
        "trust", "connection", "freund", "familie", "beziehung",
        "vertrauen", "kontakt",
    ],
    "finance": [
        "budget", "investment", "savings", "tax", "expense",
        "portfolio", "dividend", "steuer", "investition", "ausgabe",
    ],
    "code": [
        "function", "class", "bug", "test", "deploy", "api",
        "code", "script", "error", "module", "implement",
    ],
    "research": [
        "paradigm", "theorem", "hypothesis", "experiment",
        "discovery", "insight", "pattern", "formula",
    ],
    "creative": [
        "write", "create", "design", "art", "music", "story",
        "compose", "imagine", "schreiben", "gestalten",
    ],
}


def _detect_domains(text: str) -> list[tuple[str, float]]:
    """Detect domains in text with confidence scores.

    Returns (domain, confidence) pairs sorted by confidence descending.
    Multiple domains = cross-domain prompt = high x potential.
    """
    lower = text.lower()
    words = set(lower.split())
    scores: dict[str, int] = {}

    for domain, keywords in _DOMAIN_PATTERNS.items():
        count = 0
        for kw in keywords:
            if kw in words or kw in lower:
                count += 1
        if count > 0:
            scores[domain] = count

    if not scores:
        return [("general", 0.5)]

    max_score = max(scores.values())
    return sorted(
        [(d, min(c / max(max_score, 1), 1.0)) for d, c in scores.items()],
        key=lambda x: x[1],
        reverse=True,
    )


# ── Entity Extraction (lightweight, zero deps) ────────────────────

_ENTITY_RE = re.compile(
    r"""
    (\d{1,2}[./-]\d{1,2}[./-]\d{2,4})     # dates
    | (\d+(?:[.,]\d+)?\s*(?:EUR|€|\$|%|h))  # numbers with units
    | ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)       # proper nouns (multi-word)
    """,
    re.VERBOSE,
)


def _extract_entities(text: str) -> list[dict]:
    """Extract lightweight entities from text. No NLP. Just patterns."""
    entities = []
    for match in _ENTITY_RE.finditer(text):
        value = match.group().strip()
        if match.group(1):
            entities.append({"type": "date", "value": value})
        elif match.group(2):
            entities.append({"type": "number", "value": value})
        elif match.group(3):
            entities.append({"type": "name", "value": value})
    return entities


# ── Breath Cycle (the complete trace) ────────────────────────────

@dataclass
class BreathCycle:
    """Complete trace of one .x->[]~ cycle.

    Every field maps to one IR operation:
        atoms       = . (what was extracted)
        collisions  = x (what collided)
        projection  = -> (what was said, + what was lost)
        potential   = [] (what was NOT said)
        resonance   = ~ (what was learned, filled post-hoc)

    The cycle IS the breath. Inhale to exhale.
    """

    # Input
    prompt: str
    hex_coord: HexCoord
    timestamp: float = field(default_factory=time.time)

    # . Stage
    atoms: list[Atom] = field(default_factory=list)

    # x Stage
    collisions: list[Collision] = field(default_factory=list)
    x_score: float = 0.0  # overall collision intensity

    # -> Stage
    projection: Projection | None = None
    response: str = ""
    lost_dimensions: list[str] = field(default_factory=list)

    # [] Stage
    potential: Potential | None = None
    silence: list[str] = field(default_factory=list)  # what was NOT addressed

    # ~ Stage (filled later when outcome is known)
    resonance: Resonance | None = None

    # Meta
    model: str = ""
    latency_ms: float = 0.0
    learnings: list[str] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        """Did the cycle produce a response?"""
        return len(self.response) > 0

    @property
    def density(self) -> float:
        """How ALIVE was this breath? High x + low [] = dense."""
        if not self.alive:
            return 0.0
        x_part = min(self.x_score, 1.0) * 0.5
        atom_part = min(len(self.atoms) / 5, 1.0) * 0.2
        silence_part = min(len(self.silence) / 3, 1.0) * 0.3  # Silence = rich
        return x_part + atom_part + silence_part

    def trace(self) -> str:
        """Human-readable .x->[]~ trace."""
        lines = [f"=== BREATH CYCLE ({self.model}) ==="]
        lines.append(f"Hex: P={self.hex_coord.ruhe_druck:+.1f} "
                     f"R={self.hex_coord.stille_resonanz:+.1f} "
                     f"T={self.hex_coord.allein_zusammen:+.1f}")

        # .
        lines.append(f"\n. ATOMS ({len(self.atoms)}):")
        for a in self.atoms[:8]:
            lines.append(f"  {a}")

        # x
        lines.append(f"\nx COLLISIONS ({len(self.collisions)}, score={self.x_score:.2f}):")
        for c in self.collisions[:5]:
            lines.append(f"  {c}")

        # ->
        if self.projection:
            lines.append(f"\n-> PROJECTION (conf={self.projection.confidence:.2f}):")
            lines.append(f"  {self.response[:120]}...")
            if self.lost_dimensions:
                lines.append(f"  LOST: {', '.join(self.lost_dimensions[:5])}")

        # []
        if self.silence:
            lines.append(f"\n[] POTENTIAL ({len(self.silence)} silent dimensions):")
            for s in self.silence[:5]:
                lines.append(f"  [{s}]")

        # ~
        if self.resonance:
            lines.append(f"\n~ RESONANCE: {self.resonance}")

        lines.append(f"\nDensity: {self.density:.2f} | Latency: {self.latency_ms:.0f}ms")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize for persistence and analysis."""
        return {
            "ir": ".x->[]~",
            "prompt": self.prompt[:200],
            "model": self.model,
            "timestamp": self.timestamp,
            "hex": self.hex_coord.to_dict(),
            "atoms": [a.to_dict() for a in self.atoms],
            "collisions": [c.to_dict() for c in self.collisions],
            "x_score": self.x_score,
            "projection": self.projection.to_dict() if self.projection else None,
            "response_length": len(self.response),
            "lost_dimensions": self.lost_dimensions,
            "potential": self.potential.to_dict() if self.potential else None,
            "silence": self.silence,
            "resonance": self.resonance.to_dict() if self.resonance else None,
            "density": round(self.density, 4),
            "latency_ms": round(self.latency_ms, 1),
            "learnings": self.learnings,
        }


# ── The Pipeline ─────────────────────────────────────────────────

class IRPipeline:
    """The .x->[]~ Pipeline. The computation that IS a breath.

    Every breathe() call flows through 5 stages, each producing
    IR objects. The full cycle is captured in a BreathCycle.

    The pipeline does NOT replace the router. The router USES the pipeline.
    The pipeline does NOT call LLMs directly. It orchestrates the flow.

    Usage:
        pipe = IRPipeline()

        # Full cycle
        cycle = pipe.breathe(prompt, adapter_fn)

        # Or stage by stage
        atoms = pipe.atomize(prompt)
        collisions = pipe.collide(atoms, memory_atoms)
        projection = pipe.project(best_collision, adapter_fn, system_prompt)
        potential = pipe.rest(projection, prompt)
        # Later: pipe.resonate(cycle, outcome, impact)
    """

    def __init__(
        self,
        organism: OrganismBreather | None = None,
        weights: PatternWeights | None = None,
    ) -> None:
        self._hex = HexBreath()
        self._organism = organism or OrganismBreather()
        self._weights = weights or PatternWeights()
        self._cycles: list[BreathCycle] = []

    # ── Stage 1: . (Atomize) ─────────────────────────────────────

    def atomize(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> list[Atom]:
        """Extract atoms from prompt + context.

        An atom is an irreducible fact. Meaningless alone.
        Only through x (collision) does meaning emerge.

        Extracts:
        - Domain atoms (what domains does this prompt touch?)
        - Entity atoms (dates, numbers, names)
        - Context atoms (from organism memory, if available)
        """
        atoms: list[Atom] = []

        # Domain atoms
        domains = _detect_domains(prompt)
        for domain, confidence in domains:
            atoms.append(Atom(
                domain=domain,
                type="domain_signal",
                value={"confidence": round(confidence, 2), "prompt_fragment": prompt[:80]},
                source="prompt",
            ))

        # Entity atoms
        entities = _extract_entities(prompt)
        for ent in entities:
            atoms.append(Atom(
                domain=domains[0][0] if domains else "general",
                type=f"entity_{ent['type']}",
                value=ent,
                source="prompt",
            ))

        # Context atoms (from organism memory)
        if self._organism.graph is not None and self._organism.graph.count > 0:
            relevant = self._organism.graph.query(prompt, top_k=3)
            for ring in relevant:
                atoms.append(Atom(
                    domain=ring.ring_type,
                    type="memory_ring",
                    value={"content": ring.content[:120], "ring_id": ring.id},
                    source="memory",
                ))

        # External context atoms
        if context:
            for key, value in context.items():
                atoms.append(Atom(
                    domain="context",
                    type=key,
                    value=value if isinstance(value, dict) else {"raw": str(value)[:120]},
                    source="external",
                ))

        return atoms

    # ── Stage 2: x (Collide) ─────────────────────────────────────

    def collide(
        self,
        atoms: list[Atom],
        *,
        min_score: float = 0.1,
    ) -> list[Collision]:
        """Collide atoms with each other. Meaning emerges.

        x is NOT addition. x is tensor.
        The result exists in NEITHER input alone.

        Cross-domain collisions score higher (different domains = more x).
        Same-domain collisions still produce meaning but less surprise.
        Memory atoms colliding with prompt atoms = context resonance.
        """
        if len(atoms) < 2:
            return []

        collisions: list[Collision] = []

        for i, a in enumerate(atoms):
            for b in atoms[i + 1:]:
                score = self._collision_score(a, b)
                if score < min_score:
                    continue

                collision = ir_collide(
                    a, b,
                    score=score,
                    pattern=f"{a.domain}:{a.type} x {b.domain}:{b.type}",
                )

                # Emergent meaning detection
                collision.emergent = self._detect_emergent(a, b, score)

                # Apply learned weights
                weight = self._weights.get(collision.pattern)
                collision.score *= weight

                collisions.append(collision)

        # Sort by density (highest x first)
        collisions.sort(key=lambda c: c.density, reverse=True)
        return collisions

    def _collision_score(self, a: Atom, b: Atom) -> float:
        """Score a collision between two atoms.

        Cross-domain = high x (different worlds colliding).
        Prompt x Memory = resonance (past meets present).
        Same source + same domain = low x (redundant).
        """
        score = 0.2  # base

        # Cross-domain bonus (the core of x thinking)
        if a.domain != b.domain:
            score += 0.4

        # Cross-source bonus (prompt x memory = resonance)
        if a.source != b.source:
            score += 0.3

        # Time proximity bonus (close events collide harder)
        time_delta = abs(a.timestamp - b.timestamp)
        time_factor = 1.0 / (1.0 + time_delta / 60.0)
        score *= (0.7 + 0.3 * time_factor)

        return min(score, 1.0)

    def _detect_emergent(self, a: Atom, b: Atom, score: float) -> str:
        """Detect what EMERGES from a collision that exists in neither input.

        This is the magic: the third that becomes the first.
        """
        if a.domain != b.domain and score > 0.5:
            return f"cross_domain({a.domain} x {b.domain})"
        if a.source == "memory" or b.source == "memory":
            return "memory_resonance"
        if score > 0.7:
            return "high_density"
        return ""

    # ── Stage 3: -> (Project) ─────────────────────────────────────

    def project(
        self,
        prompt: str,
        response: str,
        collisions: list[Collision],
        *,
        confidence: float = 0.5,
    ) -> tuple[Projection, list[str]]:
        """Build projection from a response. Necessary. INCOMPLETE.

        Every projection loses information. x has infinite dimensions.
        -> projects onto 1D (one response). This is NECESSARY
        but NEVER the whole truth.

        The projection KNOWS what it loses (lost_dimensions).

        NOTE: This does NOT call the adapter. The adapter call happens
        in breathe() or by the caller. project() ANALYZES the result.
        Separation of concerns: execute vs. analyze.
        """
        # Detect lost dimensions
        lost = self._detect_lost_dimensions(prompt, response, collisions)

        # Build projection from best collision
        best = collisions[0] if collisions else ir_collide(
            Atom(domain="general", type="prompt", value={}),
            Atom(domain="general", type="direct", value={}),
            score=0.1,
        )

        projection = ir_project(
            best,
            action=response[:80],
            confidence=confidence,
            lost=lost,
        )

        return projection, lost

    def _enrich_system_prompt(
        self,
        base_prompt: str,
        collisions: list[Collision],
    ) -> str:
        """Inject collision awareness into system prompt.

        Not just context. COLLISION AWARENESS.
        The model learns what collided and what emerged.
        """
        if not collisions:
            return base_prompt

        lines = [base_prompt] if base_prompt else []

        # Top collisions as context
        top = collisions[:3]
        if top:
            lines.append("")
            lines.append("Active collisions (x) in this prompt:")
            for c in top:
                domains = " x ".join(sorted(c.domains))
                emergent = f" -> {c.emergent}" if c.emergent else ""
                lines.append(f"  x({domains}, score={c.score:.2f}){emergent}")

            if any(c.emergent == "memory_resonance" for c in top):
                lines.append("Memory is resonating. Build on what was learned.")

        return "\n".join(lines)

    def _detect_lost_dimensions(
        self,
        prompt: str,
        response: str,
        collisions: list[Collision],
    ) -> list[str]:
        """Detect what the projection LOST.

        Every -> is incomplete. This method makes the incompleteness EXPLICIT.
        Named after the lost_dimensions pattern (patterns.py).
        """
        lost: list[str] = []

        # Domains in prompt but not in response
        prompt_domains = {d for d, _ in _detect_domains(prompt)}
        response_domains = {d for d, _ in _detect_domains(response)}
        for d in prompt_domains - response_domains:
            lost.append(f"domain:{d}")

        # High-scoring collisions not reflected in response
        response_lower = response.lower()
        for c in collisions[:5]:
            if c.score > 0.5 and c.emergent:
                # Check if any domain words from the collision appear in response
                domains_in_response = sum(
                    1 for d in c.domains if d in response_lower
                )
                if domains_in_response < len(c.domains):
                    lost.append(f"collision:{c.pattern}")

        # Always lost: emotional nuance, body language, timing
        if "emotion" not in response_lower and "feel" not in response_lower:
            lost.append("emotional_context")

        return lost[:8]  # cap at 8

    # ── Stage 4: [] (Rest / Potential) ────────────────────────────

    def rest(
        self,
        prompt: str,
        response: str,
        atoms: list[Atom],
        collisions: list[Collision],
    ) -> tuple[Potential, list[str]]:
        """What was NOT said. The pregnant silence.

        [] is the most important state: here, EVERYTHING can happen.
        A system without [] is dead (100% -> = machine gun).
        A system with only [] is also dead (0% x = meditation without action).

        Returns (Potential, silence_list).
        """
        silence: list[str] = []

        # Atoms that had zero collisions
        collided_atoms = set()
        for c in collisions:
            for a in c.atoms:
                collided_atoms.add(a.id)

        for a in atoms:
            if a.id not in collided_atoms:
                silence.append(f"uncollided:{a.domain}:{a.type}")

        # Domains detected but with no high-scoring collision
        high_domains = set()
        for c in collisions:
            if c.score > 0.4:
                high_domains.update(c.domains)

        for a in atoms:
            if a.domain not in high_domains and a.domain != "context":
                if f"weak_signal:{a.domain}" not in silence:
                    silence.append(f"weak_signal:{a.domain}")

        # Questions implied but not asked
        prompt_lower = prompt.lower()
        if "?" not in prompt_lower and len(prompt_lower) > 50:
            silence.append("unasked_questions")

        # Response gaps
        if len(response) < 100 and len(prompt) > 200:
            silence.append("compressed_response")

        # Fertility: how much potential for future x?
        fertility = min(len(silence) / 5, 1.0)

        potential = Potential(
            domain=atoms[0].domain if atoms else "general",
            duration_sec=0.0,  # filled by caller if measuring actual rest
            fertility=fertility,
        )

        return potential, silence

    # ── Stage 5: ~ (Resonate) ────────────────────────────────────

    def resonate(
        self,
        cycle: BreathCycle,
        outcome: str,
        impact: float,
        learning: str = "",
    ) -> Resonance:
        """The system learns from itself.

        ~ is the difference between a dead system (-> -> -> ->)
        and a living one (x ~ x ~ x ~ ...).

        Impact: -1.0 (catastrophic) to +1.0 (breakthrough).
        """
        collision_id = (
            cycle.collisions[0].id if cycle.collisions
            else cycle.projection.collision.id if cycle.projection
            else ""
        )

        resonance = ir_resonate(
            collision_id=collision_id,
            outcome=outcome,
            impact=impact,
            learning=learning,
        )

        # Update pattern weights based on outcome
        for c in cycle.collisions:
            self._weights.apply_resonance(resonance, c.pattern)

        # Record in organism
        if learning:
            self._organism.exhale(learnings=[learning])

        # Store back in cycle
        cycle.resonance = resonance

        return resonance

    # ── Full Breath Cycle ─────────────────────────────────────────

    def breathe(
        self,
        prompt: str,
        adapter: AdapterFn,
        *,
        system_prompt: str = "",
        context: dict | None = None,
        model_name: str = "",
        learnings: list[str] | None = None,
    ) -> BreathCycle:
        """Complete .x->[]~ cycle.

        This is THE method. The full breath.
        Every stage produces IR objects. The cycle captures everything.
        """
        t_start = time.time()

        # Inhale
        coord = self._hex.classify(prompt)
        self._organism.inhale(prompt)

        cycle = BreathCycle(
            prompt=prompt,
            hex_coord=coord,
            model=model_name,
        )

        # . ATOMIZE
        cycle.atoms = self.atomize(prompt, context)

        # x COLLIDE
        cycle.collisions = self.collide(cycle.atoms)
        if cycle.collisions:
            cycle.x_score = sum(c.score for c in cycle.collisions) / len(cycle.collisions)

        # -> PROJECT (single adapter call, then analyze)
        enriched = self._enrich_system_prompt(system_prompt, cycle.collisions)
        response = adapter(prompt, enriched)
        cycle.projection, cycle.lost_dimensions = self.project(
            prompt, response, cycle.collisions,
        )
        cycle.response = response

        # [] REST
        cycle.potential, cycle.silence = self.rest(
            prompt, response, cycle.atoms, cycle.collisions,
        )

        # Record learnings
        all_learnings = list(learnings or [])
        if cycle.x_score > 0.5:
            all_learnings.append(
                f"x_score={cycle.x_score:.2f}, "
                f"collisions={len(cycle.collisions)}, "
                f"silence={len(cycle.silence)}"
            )
        cycle.learnings = all_learnings

        # Exhale
        self._organism.exhale(response, all_learnings or None)

        cycle.latency_ms = (time.time() - t_start) * 1000

        # Store cycle
        self._cycles.append(cycle)
        if len(self._cycles) > 100:
            self._cycles = self._cycles[-100:]

        return cycle

    # ── Introspection ────────────────────────────────────────────

    @property
    def breath_count(self) -> int:
        return len(self._cycles)

    @property
    def avg_density(self) -> float:
        """Average breath density across all cycles."""
        if not self._cycles:
            return 0.0
        return sum(c.density for c in self._cycles) / len(self._cycles)

    @property
    def avg_x_score(self) -> float:
        """Average collision intensity."""
        if not self._cycles:
            return 0.0
        return sum(c.x_score for c in self._cycles) / len(self._cycles)

    def pattern_report(self) -> dict:
        """Which collision patterns are strongest?"""
        pattern_scores: dict[str, list[float]] = {}
        for cycle in self._cycles:
            for c in cycle.collisions:
                if c.pattern not in pattern_scores:
                    pattern_scores[c.pattern] = []
                pattern_scores[c.pattern].append(c.score)

        return {
            pattern: {
                "count": len(scores),
                "avg_score": sum(scores) / len(scores),
                "weight": self._weights.get(pattern),
            }
            for pattern, scores in sorted(
                pattern_scores.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
                reverse=True,
            )[:20]
        }

    def silence_report(self) -> dict:
        """What keeps being silent? Persistent [] = exploration opportunity."""
        silence_counts: dict[str, int] = {}
        for cycle in self._cycles:
            for s in cycle.silence:
                silence_counts[s] = silence_counts.get(s, 0) + 1

        return dict(sorted(
            silence_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:15])

    @property
    def organism(self) -> OrganismBreather:
        return self._organism

    @property
    def weights(self) -> PatternWeights:
        return self._weights

    def summary(self) -> dict:
        """Pipeline vitals."""
        return {
            "breaths": self.breath_count,
            "avg_density": round(self.avg_density, 4),
            "avg_x_score": round(self.avg_x_score, 4),
            "organism": self._organism.vitals(),
            "patterns": len(self._weights.weights),
            "top_silence": list(self.silence_report().keys())[:5],
        }
