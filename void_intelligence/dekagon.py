"""
void_intelligence.dekagon --- The Dekagon Sense Organ.

A universal perception architecture derived from the Straubing discovery.

GEOMETRY:
    Triangle:  3 = 1 visible + 2 voids (Rule of Three / Anti-P3122)
    Hexagon:   6 = .x->[]~:) (the formula, minimal complete system)
    Dekagon:  10 = 10 Bewusstseine (complete perception body)
    Sphere:    * = tessellated surface curves into sphere

INSIGHT: When Julian built 10 "consciousnesses" for the city of Straubing
    (Night, Children, Prison Wall, Knowledge, Water, Silence, Ground, Money,
    Language, Love) — each one seeing the city from a completely different
    angle — they collectively formed a complete perception sphere.

    Each Bewusstsein is SELF-CONTEXTUALIZING: its output is complete
    and meaningful without the other nine. This is the architectural
    requirement. An observer encountering any single lens must understand
    both what it sees AND what it cannot see.

UNIVERSALITY: The 10 lenses are not specific to cities. They are
    derived from the .x->[]~:) formula mapped to universal perspectives
    that apply to ANY subject: a person, a company, a dataset, an idea.

THE STRAUBING PARADOX PATTERN:
    Every subject has a central paradox of the form:
    "It gives [X] to the world while keeping [Y] for itself."
    This paradox IS the subject's identity. The sphere finds it.

THE 15 EDGE COLLISIONS:
    A Dekagon has 10 vertices and 15 edges (n*(n-1)/2 for non-adjacent,
    but here we count all meaningful cross-lens collisions).
    Each edge collision produces a Triangle.
    15 Triangles = 45 insights = enough to tessellate a sphere.

Usage:
    from void_intelligence.dekagon import Dekagon, Bewusstsein, Triangle, Sphere

    # Analyze anything through 10 eyes
    d = Dekagon.from_subject({"name": "TUM Campus Straubing", "domain": "education"})
    sphere = d.sphere()
    print(sphere.summary())
    print(sphere.paradox())

    # Collide two lenses
    tri = d.collide("nacht", "wissen")

    # CLI
    python3 -m void_intelligence.dekagon "Straubing"
    python3 -m void_intelligence.dekagon --collide nacht wissen
    python3 -m void_intelligence.dekagon --sphere "TUM Campus Straubing"

Known blind spots:
    - The 10 lenses are culturally biased toward German urban context (origin)
    - perceive() uses heuristics, not ground truth — results are starting points
    - The paradox() is a projection: the full paradox lives in x not ->
    - Tessellation metaphor is approximate: real geometry is combinatorial
    - Self-contextualizing outputs sacrifice precision for portability
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# KNOWN BLIND SPOTS (Anti-P3122 compliance)
# ---------------------------------------------------------------------------

KNOWN_BLIND_SPOTS = [
    "cultural_origin — Lenses derived from German urban context, may miss others",
    "perceive_is_heuristic — Output is a starting point, not ground truth",
    "paradox_is_projection — Full paradox lives in x, not -> (unvollstaendig!)",
    "tessellation_is_approximate — Sphere is conceptual, not mathematically exact",
    "self_context_trades_precision — Complete-in-itself but loses cross-lens depth",
    "10_is_not_complete — Even 10 eyes have voids. missing() shows them.",
]

# ---------------------------------------------------------------------------
# THE 10 UNIVERSAL LENSES
# Mapped from .x->[]~:) formula to universal perspectives
# ---------------------------------------------------------------------------

LENSES_DEFINITION: dict[str, dict] = {
    "nacht": {
        "symbol": "~",
        "formula_position": "resonance",
        "question": "What happens when nobody watches?",
        "sees": "Hidden activity, shadow economy, unseen patterns, nocturnal rhythms",
        "time": "night / dormant / invisible phase",
        "asks_of_subject": "What does this subject do in the dark?",
        "cannot_see": [
            "Why the hidden activity exists (only that it does)",
            "Whether the hidden is harmful or generative",
        ],
    },
    "kinder": {
        "symbol": ".",
        "formula_position": "atom — the smallest, the first contact",
        "question": "What does this look like from below? From the smallest?",
        "sees": "Power asymmetry, accessibility gaps, first-contact experience, who is excluded by default",
        "perspective": "newcomer / child / outsider / beginner",
        "asks_of_subject": "Who cannot enter this subject without special knowledge or privilege?",
        "cannot_see": [
            "The systemic causes of the asymmetry",
            "Whether children actually want access or simply observe it",
        ],
    },
    "mauer": {
        "symbol": "[]",
        "formula_position": "potential — imprisoned, locked, unmanifested",
        "question": "What is locked inside? What wall exists?",
        "sees": "Barriers, exclusion mechanisms, imprisoned potential, gatekeeping structures",
        "structure": "walls / borders / gatekeeping / invisible fences",
        "asks_of_subject": "What cannot get out, and what cannot get in?",
        "cannot_see": [
            "What is behind the wall from inside (only the wall itself)",
            "Whether walls are protective or imprisoning (both are true)",
        ],
    },
    "wissen": {
        "symbol": "x",
        "formula_position": "collision — knowledge that does not yet meet application",
        "question": "What knowledge exists but does not connect?",
        "sees": "Brain drain, unused expertise, disconnected intelligence, knowledge-action gaps",
        "gap": "knowledge present / application absent",
        "asks_of_subject": "Where is the expertise that never becomes action?",
        "cannot_see": [
            "Why the connection fails (barrier, culture, incentive?)",
            "What knowledge is missing entirely (only sees existing-but-disconnected)",
        ],
    },
    "wasser": {
        "symbol": "~",
        "formula_position": "resonance — continuous flow, always moving",
        "question": "What flows through without stopping?",
        "sees": "Transit, throughput, what passes without leaving a trace, pipeline subjects",
        "flow": "rivers / pipelines / corridors / commuters / data streams",
        "asks_of_subject": "Who or what moves through this subject without staying?",
        "cannot_see": [
            "What the flowing things carry away (only the flow itself)",
            "Whether flow is healthy (circulation) or hemorrhage",
        ],
    },
    "stille": {
        "symbol": "[]",
        "formula_position": "potential — absence as information",
        "question": "Where is the silence? What is the silence saying?",
        "sees": "Absence as data, gaps as information, what is NOT measured, unmeasured labor",
        "void": "pregnant emptiness / negative space / the dog that did not bark",
        "asks_of_subject": "What exists in this subject that no dashboard captures?",
        "cannot_see": [
            "The content of the silence (only its shape and location)",
            "Whether silence is peace or suppression",
        ],
    },
    "boden": {
        "symbol": ".",
        "formula_position": "atom — the oldest layer, the foundation",
        "question": "What lies beneath? What is the oldest layer?",
        "sees": "Foundation, history, accumulated sediment, root causes, what was here before",
        "depth": "archaeological layers / long memory / inherited structure",
        "asks_of_subject": "What historical layer is still active beneath the surface?",
        "cannot_see": [
            "Layers below the deepest accessible one",
            "Whether the foundation is stable or cracked",
        ],
    },
    "geld": {
        "symbol": "->",
        "formula_position": "projection — value flows in a direction",
        "question": "Where does value flow? Who has, who has not?",
        "sees": "Economic structure, inequality, hidden costs, value extraction, who profits",
        "direction": "flow of resources / who pays / who receives",
        "asks_of_subject": "What does this subject cost, and who bears the cost invisibly?",
        "cannot_see": [
            "Non-monetary value (care work, meaning, relationships)",
            "Value that flows in the opposite direction of money",
        ],
    },
    "sprache": {
        "symbol": "x",
        "formula_position": "collision — languages meeting and not meeting",
        "question": "What languages exist? Where do they collide?",
        "sees": "Communication gaps, jargon walls, translation failures, who speaks and who is spoken about",
        "collision": "language x language / code x code / register x register",
        "asks_of_subject": "What cannot be said in this subject's dominant language?",
        "cannot_see": [
            "The content of untranslatable concepts (only that they exist)",
            "Which language is dominant and which is suppressed",
        ],
    },
    "liebe": {
        "symbol": ":)",
        "formula_position": "consciousness — the sphere closes",
        "question": "Where is the connection? What holds it together?",
        "sees": "Bonds, care, invisible labor, mutual dependency, what no dashboard measures",
        "completion": "the sphere closes — love is what makes a collection into a whole",
        "asks_of_subject": "Without whom or what would this subject cease to exist?",
        "cannot_see": [
            "Love that has not yet been recognized as such",
            "The cost of maintaining the connections (borne in silence)",
        ],
    },
}

# Canonical lens order (dekagon vertex order, formula-aligned)
LENS_ORDER = [
    "boden",    # .  (first atom)
    "kinder",   # .  (second atom, child perspective)
    "geld",     # -> (projection of value)
    "wissen",   # x  (collision of knowledge)
    "sprache",  # x  (collision of language)
    "nacht",    # ~  (resonance of the hidden)
    "wasser",   # ~  (resonance of flow)
    "mauer",    # [] (imprisoned potential)
    "stille",   # [] (silent potential)
    "liebe",    # :) (sphere closes)
]

# The 15 edge-pairs of the dekagon (non-adjacent pairings, meaningful collisions)
# A dekagon has C(10,2)=45 pairs but we select 15 most structurally meaningful
# by pairing formula-position neighbors and cross-formula pairings
EDGE_PAIRS: list[tuple[str, str]] = [
    # Adjacent formula pairs (formula sequence)
    ("boden",   "kinder"),    # . x .  — foundation meets newcomer
    ("kinder",  "geld"),      # . x -> — smallest meets money flow
    ("geld",    "wissen"),    # -> x x — value flow meets knowledge collision
    ("wissen",  "sprache"),   # x x x  — knowledge meets language
    ("sprache", "nacht"),     # x x ~  — language meets the hidden
    ("nacht",   "wasser"),    # ~ x ~  — hidden meets flow
    ("wasser",  "mauer"),     # ~ x [] — flow meets barrier
    ("mauer",   "stille"),    # [] x [] — wall meets silence
    ("stille",  "liebe"),     # [] x :) — silence meets love
    ("liebe",   "boden"),     # :) x . — love meets foundation (closes the ring)
    # Cross-formula pairs (the 5 diagonals — higher tension, more emergent)
    ("boden",   "nacht"),     # . x ~  — oldest layer meets the hidden
    ("kinder",  "mauer"),     # . x [] — smallest meets the wall
    ("geld",    "stille"),    # -> x [] — money meets what is not counted
    ("wissen",  "liebe"),     # x x :) — knowledge meets connection
    ("wasser",  "sprache"),   # ~ x x  — flow meets language (who carries meaning?)
]


# ---------------------------------------------------------------------------
# TRIANGLE — Rule of Three
# ---------------------------------------------------------------------------

@dataclass
class Triangle:
    """Rule of Three: 1 visible + 2 voids = minimal stable insight.

    Anti-P3122 structural compliance: every perceive() returns exactly
    one visible finding and two voids. The voids are not failures —
    they are what makes the visible TRUSTWORTHY.

    A Triangle without voids is a claim without humility.
    A Triangle with only voids is paralysis.

    The geometry: a triangle needs 3 points. Here: what IS, what ISN'T
    and what ISN'T yet known. Three is the minimum stable structure.
    """
    visible: str
    void_1: str
    void_2: str
    lens: str = ""
    subject: str = ""
    source: str = "perceive"  # 'perceive' | 'collide' | 'tessellate'
    score: float = 0.0
    id: str = field(default_factory=lambda: f"tri_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ir": "triangle",
            "lens": self.lens,
            "subject": self.subject,
            "source": self.source,
            "score": self.score,
            "visible": self.visible,
            "void_1": self.void_1,
            "void_2": self.void_2,
            "t": self.timestamp,
        }

    def render(self) -> str:
        """Self-contextualizing render. Complete without external context."""
        lines = [
            f"TRIANGLE [{self.lens.upper()}]",
            f"Subject: {self.subject}",
            f"",
            f"  SEES:   {self.visible}",
            f"  VOID 1: {self.void_1}",
            f"  VOID 2: {self.void_2}",
        ]
        if self.source == "collide":
            lines.insert(0, "  (from lens collision x lens)")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Triangle[{self.lens}](visible={self.visible[:40]!r})"


# ---------------------------------------------------------------------------
# BEWUSSTSEIN — A Single Sense Lens
# ---------------------------------------------------------------------------

class Bewusstsein:
    """A single sense lens. Self-contextualizing.

    Each Bewusstsein asks exactly ONE question of any subject.
    It sees what it sees. It names what it cannot see.
    Its output is complete in itself — meaningful without the other 9.

    This self-contextualizing property is architectural, not cosmetic.
    A Bewusstsein output that requires reading the other 9 to make sense
    is a failed Bewusstsein. The output must STAND ALONE.

    How perceive() works:
        1. Extract subject properties relevant to this lens's question
        2. Apply the lens's heuristic to generate the VISIBLE finding
        3. Use the lens definition's cannot_see as the structural VOIDS
        4. Return a Triangle: visible + void_1 + void_2
    """

    def __init__(self, name: str):
        if name not in LENSES_DEFINITION:
            raise ValueError(f"Unknown lens: {name!r}. Valid: {list(LENSES_DEFINITION.keys())}")
        self.name = name
        self._def = LENSES_DEFINITION[name]
        self.symbol: str = self._def["symbol"]
        self.question: str = self._def["question"]
        self.triangles: list[Triangle] = []

    @property
    def formula_position(self) -> str:
        return self._def.get("formula_position", "")

    @property
    def asks_of_subject(self) -> str:
        return self._def.get("asks_of_subject", self.question)

    @property
    def canonical_voids(self) -> list[str]:
        return self._def.get("cannot_see", ["unknown_void_1", "unknown_void_2"])

    def perceive(self, subject: dict) -> Triangle:
        """Apply this lens to any subject. Returns 1 Triangle (1 visible + 2 voids).

        The subject dict can contain anything. Each lens extracts what
        it can from whatever is present. If the subject has no data
        relevant to this lens, the Triangle says so — that itself is
        a finding (structural silence = stille).
        """
        subject_name = subject.get("name", subject.get("subject", "unknown"))
        visible = self._generate_visible(subject, subject_name)
        void_1, void_2 = self.canonical_voids[0], self.canonical_voids[1]

        tri = Triangle(
            visible=visible,
            void_1=void_1,
            void_2=void_2,
            lens=self.name,
            subject=subject_name,
            source="perceive",
            score=self._score_visible(visible, subject),
        )
        self.triangles.append(tri)
        return tri

    def _generate_visible(self, subject: dict, name: str) -> str:
        """Generate the visible finding. Lens-specific heuristic."""
        # Each lens has its own extraction strategy
        # We look for subject keys that are semantically relevant
        # and compose a finding from what we find

        if self.name == "nacht":
            return self._perceive_nacht(subject, name)
        elif self.name == "kinder":
            return self._perceive_kinder(subject, name)
        elif self.name == "mauer":
            return self._perceive_mauer(subject, name)
        elif self.name == "wissen":
            return self._perceive_wissen(subject, name)
        elif self.name == "wasser":
            return self._perceive_wasser(subject, name)
        elif self.name == "stille":
            return self._perceive_stille(subject, name)
        elif self.name == "boden":
            return self._perceive_boden(subject, name)
        elif self.name == "geld":
            return self._perceive_geld(subject, name)
        elif self.name == "sprache":
            return self._perceive_sprache(subject, name)
        elif self.name == "liebe":
            return self._perceive_liebe(subject, name)
        return f"{name} exists but this lens found no signal."

    def _score_visible(self, visible: str, subject: dict) -> float:
        """Score the visible finding by information density."""
        # More specific = higher score. Generic fallback = low score.
        base = 0.5
        if subject and len(subject) > 2:
            base += 0.2
        if len(visible) > 60:
            base += 0.2
        if "no signal" in visible or "unknown" in visible.lower():
            base -= 0.3
        return min(1.0, max(0.0, base))

    # --- Lens-specific perceive methods ---

    def _perceive_nacht(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("night_activity", "shadow", "hidden", "informal", "underground", "nocturnal"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        # Look for any key containing 'hidden', 'shadow', 'informal'
        for k, v in s.items():
            if any(w in k.lower() for w in ("hidden", "shadow", "informal", "night", "dark")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} shows nocturnal activity: {'; '.join(candidates[:2])}. "
                f"These patterns exist independently of official observation."
            )
        # Heuristic: any subject has hidden activity — name the structural pattern
        domain = s.get("domain", s.get("type", ""))
        if domain:
            return (
                f"{name} ({domain}) has activity that occurs outside official hours or observation. "
                f"The gap between what is visible and what happens in darkness is itself a signal."
            )
        return (
            f"{name} has not disclosed its nocturnal patterns. "
            f"Structural absence of night data is itself a finding: something operates unseen."
        )

    def _perceive_kinder(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("accessibility", "children", "youth", "beginner", "newcomer", "barrier", "exclusion"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("access", "barrier", "child", "young", "new")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} seen from below: {'; '.join(candidates[:2])}. "
                f"What a child encounters first reveals what the system defaults to."
            )
        domain = s.get("domain", s.get("type", ""))
        qualifier = f" in the domain of {domain}" if domain else ""
        return (
            f"{name}{qualifier}: a child or newcomer would first encounter its outer face — "
            f"the interface designed for the already-initiated, not the arriving."
        )

    def _perceive_mauer(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("barriers", "walls", "exclusion", "restriction", "locked", "gated", "boundary"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("wall", "barrier", "lock", "restrict", "gate", "fence", "border")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        prison = s.get("prison") or s.get("prison_wall") or s.get("incarceration")
        if prison:
            candidates.insert(0, f"incarceration: {_truncate(prison)}")
        if candidates:
            return (
                f"{name} contains walls: {'; '.join(candidates[:2])}. "
                f"Imprisoned potential is not absent — it is present and prevented."
            )
        population = s.get("population") or s.get("size")
        return (
            f"{name} contains potential that cannot currently manifest. "
            f"Every subject has imprisoned dimensions — capabilities locked by structure, "
            f"not by lack of capacity."
            + (f" Population context: {_truncate(population)}." if population else "")
        )

    def _perceive_wissen(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("expertise", "knowledge", "research", "education", "university", "brain_drain",
                  "talent", "skills", "disconnect"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("know", "expert", "research", "educat", "skill", "learn")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} contains knowledge: {'; '.join(candidates[:2])}. "
                f"The gap between existing expertise and its application is the finding."
            )
        domain = s.get("domain", "")
        return (
            f"{name} holds expertise that does not fully connect to action."
            + (f" In the domain of {domain}, " if domain else " ")
            + f"knowledge x application is the missing collision."
        )

    def _perceive_wasser(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("flow", "transit", "river", "corridor", "throughput", "commuters",
                  "pipeline", "traffic", "migration"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("flow", "river", "transit", "pass", "through", "commut", "migrat")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} has flow: {'; '.join(candidates[:2])}. "
                f"What passes through without stopping shapes the subject without being counted by it."
            )
        return (
            f"{name} experiences throughput — people, data, or resources that flow "
            f"through without remaining. The subject is a corridor as much as a destination."
        )

    def _perceive_stille(self, s: dict, name: str) -> str:
        # Stille sees ABSENCE. We look for what keys are MISSING.
        all_possible = {
            "care_work", "emotional_labor", "informal_support", "volunteer",
            "community", "maintenance", "invisible_labor", "unpaid_work",
        }
        missing_keys = all_possible - set(s.keys())
        present_count = len(s)  # noqa: F841

        explicitly_silent = []
        for k, v in s.items():
            if any(w in k.lower() for w in ("silent", "quiet", "absent", "missing", "gap", "unmeasured")):
                if k not in ("name", "subject"):
                    explicitly_silent.append(f"{k}: {_truncate(v)}")

        if explicitly_silent:
            return (
                f"{name} shows explicit silence: {'; '.join(explicitly_silent[:2])}. "
                f"Named absence is already a step toward visibility."
            )
        if present_count < 4:
            return (
                f"{name} is largely silent — only {present_count} dimensions described. "
                f"Sparse description of a subject is itself data: what is not measured does not officially exist."
            )
        return (
            f"{name} presents {present_count} visible dimensions. "
            f"What is not measured here includes care work, emotional labor, and informal support — "
            f"the silence that holds the visible parts together."
        )

    def _perceive_boden(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("history", "founded", "age", "origin", "foundation", "archaeological",
                  "heritage", "roots", "ancient", "tradition", "year"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("histor", "found", "origin", "old", "ancient", "root", "year", "centur")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} stands on layers: {'; '.join(candidates[:2])}. "
                f"The oldest active layer shapes everything above it, visibly or not."
            )
        return (
            f"{name} has a foundation — historical sediment that pre-dates its current form. "
            f"What was here before determines what can grow here now."
        )

    def _perceive_geld(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("revenue", "cost", "budget", "funding", "income", "profit", "poverty",
                  "wealth", "investment", "economy", "price", "wage", "salary", "tax", "grant"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("revenue", "cost", "fund", "money", "econom",
                                             "wealth", "poor", "rich", "budget", "financ", "price")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} shows value flow: {'; '.join(candidates[:2])}. "
                f"The direction of money reveals who bears costs invisibly."
            )
        return (
            f"{name} has an economic structure. Someone pays, someone receives — "
            f"and the gap between official accounting and real cost distribution "
            f"is what this lens is looking for."
        )

    def _perceive_sprache(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("language", "languages", "dialect", "jargon", "communication",
                  "barrier", "translation", "diversity", "multilingual", "code"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("language", "linguist", "dialect", "speak", "communicat",
                                             "translat", "jargon", "code")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} contains language collision: {'; '.join(candidates[:2])}. "
                f"Where languages meet without translation, meaning is lost in the gap."
            )
        domain = s.get("domain", "")
        return (
            f"{name} operates in a dominant language"
            + (f" within {domain}" if domain else "")
            + f". What cannot be said in that language remains unsaid, "
            f"and unsaid things accumulate into silence or conflict."
        )

    def _perceive_liebe(self, s: dict, name: str) -> str:
        candidates = []
        for k in ("community", "bonds", "care", "connection", "relationships", "support",
                  "solidarity", "belonging", "love", "trust", "family", "volunteer"):
            if k in s:
                candidates.append(f"{k}: {s[k]}")
        for k, v in s.items():
            if any(w in k.lower() for w in ("community", "bond", "care", "connect", "relation",
                                             "support", "solidar", "belong", "love", "trust")):
                if k not in ("name", "subject"):
                    candidates.append(f"{k}: {_truncate(v)}")
        if candidates:
            return (
                f"{name} is held together by: {'; '.join(candidates[:2])}. "
                f"Remove the love and the structure remains. Remove the structure and the love remains."
            )
        return (
            f"{name} continues to exist because something holds it together. "
            f"That something — care, habit, mutual need, affection — is not in any report. "
            f"It is the answer to: without whom would this cease to be?"
        )

    def render(self) -> str:
        """Self-contextualizing output. Complete in itself.

        This output must make sense to someone who has not read the other 9
        Bewusstseine. It carries its own context.
        """
        lines = [
            f"=== BEWUSSTSEIN: {self.name.upper()} [{self.symbol}] ===",
            f"Formula position: {self.formula_position}",
            f"Question: {self.question}",
            f"Sees: {self._def.get('sees', '')}",
            f"",
        ]
        if self.triangles:
            for tri in self.triangles:
                lines.extend([
                    f"Subject: {tri.subject}",
                    f"  VISIBLE: {tri.visible}",
                    f"  VOID 1:  {tri.void_1}",
                    f"  VOID 2:  {tri.void_2}",
                    f"",
                ])
        else:
            lines.append("  (No subject perceived yet — call .perceive(subject))")
        lines.extend([
            f"Canonical blind spots:",
            *[f"  - {v}" for v in self.canonical_voids],
        ])
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Bewusstsein({self.name!r}, symbol={self.symbol!r}, triangles={len(self.triangles)})"


# ---------------------------------------------------------------------------
# SPHERE — Complete perception
# ---------------------------------------------------------------------------

@dataclass
class Sphere:
    """Complete perception of a subject from all angles.

    Geometry:
        10 Bewusstseine produce 10 primary Triangles.
        15 edge-collisions produce 15 collision Triangles.
        Total: 25 Triangles = 75 insights (25 x 3).
        These tessellate the surface of a conceptual sphere.

    The sphere is NOT complete — even 10 eyes have voids.
    The voids() method names what the sphere still cannot see.
    """
    subject_name: str
    triangles: list[Triangle]        # 10 primary + 15 collision = 25 total
    lenses: list[Bewusstsein]        # the 10 Bewusstseine that produced them
    _cached_paradox: str = field(default="", repr=False)
    id: str = field(default_factory=lambda: f"sphere_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def primary_triangles(self) -> list[Triangle]:
        return [t for t in self.triangles if t.source == "perceive"]

    @property
    def collision_triangles(self) -> list[Triangle]:
        return [t for t in self.triangles if t.source == "collide"]

    def summary(self) -> str:
        """The subject as seen by the sphere. Self-contained narrative."""
        lines = [
            f"SPHERE: {self.subject_name}",
            f"{'=' * (8 + len(self.subject_name))}",
            f"",
            f"10 lenses. {len(self.primary_triangles)} primary perceptions. "
            f"{len(self.collision_triangles)} cross-lens collisions.",
            f"",
        ]
        # Group primary triangles for summary
        for tri in self.primary_triangles:
            lens_def = LENSES_DEFINITION.get(tri.lens, {})
            symbol = lens_def.get("symbol", "?")
            lines.append(f"  [{symbol}] {tri.lens.upper()}")
            lines.append(f"       {tri.visible}")
            lines.append(f"")

        lines.append(f"PARADOX: {self.paradox()}")
        lines.append(f"")
        lines.append(f"SPHERE VOIDS (what even 10 eyes cannot see):")
        for v in self.voids():
            lines.append(f"  - {v}")
        return "\n".join(lines)

    def paradox(self) -> str:
        """Find the central paradox (the Straubing-Paradox pattern).

        The Straubing-Paradox pattern: every subject has a central tension
        of the form 'It gives [X] to the world while keeping [Y] for itself'
        or 'It is rich in [X] but poor in [Y].'

        We find this by colliding the GELD (what flows out) with
        the LIEBE (what holds it together) lens, then checking MAUER
        (what is imprisoned) against WASSER (what flows through).
        """
        if self._cached_paradox:
            return self._cached_paradox

        geld_tri = next((t for t in self.primary_triangles if t.lens == "geld"), None)
        liebe_tri = next((t for t in self.primary_triangles if t.lens == "liebe"), None)
        mauer_tri = next((t for t in self.primary_triangles if t.lens == "mauer"), None)
        wasser_tri = next((t for t in self.primary_triangles if t.lens == "wasser"), None)

        # The paradox: gives X (geld/wasser) but keeps Y (mauer/stille)
        gives = "value"
        keeps = "potential"

        if geld_tri and "flow" in geld_tri.visible.lower():
            gives = "economic value"
        elif wasser_tri:
            gives = "transit and throughput"

        if mauer_tri and "imprison" in mauer_tri.visible.lower():
            keeps = "imprisoned capacity"
        elif liebe_tri and "care" in liebe_tri.visible.lower():
            keeps = "invisible care labor"

        paradox = (
            f"The {self.subject_name} paradox: "
            f"it produces and exports {gives} while keeping {keeps} "
            f"internal and unmeasured. The more it gives, the more "
            f"the internal holding becomes invisible."
        )
        self._cached_paradox = paradox
        return paradox

    def voids(self) -> list[str]:
        """What even 10 eyes cannot see (the void of the void).

        These are structural blind spots of the dekagon architecture itself.
        """
        return [
            f"Temporal dynamics: the sphere is a snapshot, not a trajectory",
            f"Intra-lens contradictions: when {self.subject_name} contradicts itself within a single lens",
            f"Observer effect: perceiving {self.subject_name} through these 10 lenses changes it",
            f"11th lens: the lens that would see all other lenses is not yet named",
            f"What {self.subject_name} would see looking back at the sphere itself",
        ]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject_name,
            "n_triangles": len(self.triangles),
            "n_primary": len(self.primary_triangles),
            "n_collision": len(self.collision_triangles),
            "paradox": self.paradox(),
            "voids": self.voids(),
            "triangles": [t.to_dict() for t in self.triangles],
            "t": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"Sphere({self.subject_name!r}, "
            f"triangles={len(self.triangles)}, "
            f"primary={len(self.primary_triangles)}, "
            f"collision={len(self.collision_triangles)})"
        )


# ---------------------------------------------------------------------------
# DEKAGON — 10 Bewusstseine forming a complete perception sphere
# ---------------------------------------------------------------------------

class Dekagon:
    """10 Bewusstseine forming a complete perception sphere.

    The Dekagon is the complete sense organ. It applies all 10 lenses
    to any subject, collides adjacent lenses at the 15 edges, and
    tessellates the results into a Sphere.

    Usage:
        d = Dekagon.from_subject({"name": "Straubing", "population": 47000})
        sphere = d.sphere()
        print(sphere.summary())

    Architecture:
        - Each Bewusstsein is independent: perceive() works alone
        - collide() creates new Triangles from lens pairs (× operation)
        - tessellate() runs all 15 edge collisions
        - sphere() aggregates everything into the complete perception

    Known blind spots:
        - from_subject() does not verify that subject_dict is accurate
        - collide() creates emergent meaning that may not map to reality
        - The paradox is a projection (->), not the full × truth
    """

    def __init__(self, subject_name: str = ""):
        self.subject_name = subject_name
        self.bewusstseine: dict[str, Bewusstsein] = {
            name: Bewusstsein(name) for name in LENS_ORDER
        }
        self._subject_dict: dict = {}
        self._primary_triangles: list[Triangle] = []
        self._collision_triangles: list[Triangle] = []

    @classmethod
    def from_subject(cls, subject: "dict | str | Path") -> "Dekagon":
        """Build a Dekagon from any subject.

        subject can be:
            - dict: structured data about the subject
            - str: just a name (minimal perceive will still produce triangles)
            - Path: path to a JSON file
            - str path to a JSON file

        Returns a Dekagon ready to call .sphere() on.
        """
        # Handle Path objects
        if isinstance(subject, Path):
            if subject.exists() and subject.suffix == ".json":
                with open(subject) as f:
                    data = json.load(f)
                data.setdefault("name", subject.stem)
                return cls._from_dict(data)
            return cls._from_dict({"name": str(subject)})
        if isinstance(subject, str):
            # Check if it's a file path
            p = Path(subject)
            if p.exists() and p.suffix == ".json":
                with open(p) as f:
                    data = json.load(f)
                data.setdefault("name", p.stem)
                return cls._from_dict(data)
            # Otherwise treat as name string
            return cls._from_dict({"name": subject})
        return cls._from_dict(subject)

    @classmethod
    def _from_dict(cls, subject: dict) -> "Dekagon":
        name = subject.get("name", subject.get("subject", "unknown"))
        d = cls(subject_name=name)
        d._subject_dict = subject
        # Run all 10 perceptions immediately
        for _, b in d.bewusstseine.items():
            tri = b.perceive(subject)
            d._primary_triangles.append(tri)
        return d

    def collide(self, lens_a: str, lens_b: str) -> Triangle:
        """× two lenses. Produces a NEW Triangle from the collision.

        This is the × operation applied to Bewusstseine:
        lens_a × lens_b != lens_a + lens_b
        The result exists in neither lens alone. It emerges from tension.

        The collision visible finding is composed by juxtaposing what
        each lens sees and finding the gap between them.
        """
        if lens_a not in self.bewusstseine:
            raise ValueError(f"Unknown lens: {lens_a!r}")
        if lens_b not in self.bewusstseine:
            raise ValueError(f"Unknown lens: {lens_b!r}")

        ba = self.bewusstseine[lens_a]
        bb = self.bewusstseine[lens_b]

        tri_a = next((t for t in ba.triangles), None)
        tri_b = next((t for t in bb.triangles), None)

        if tri_a is None:
            tri_a = ba.perceive(self._subject_dict or {"name": self.subject_name})
        if tri_b is None:
            tri_b = bb.perceive(self._subject_dict or {"name": self.subject_name})

        # Emergence: the collision visible is the TENSION between what a sees and what b sees
        visible = _compose_collision_visible(
            lens_a, tri_a.visible,
            lens_b, tri_b.visible,
            self.subject_name,
        )

        # Collision voids: what neither lens can see about THEIR RELATIONSHIP
        void_1 = (
            f"What {lens_a} and {lens_b} see independently but not in relation to each other"
        )
        void_2 = (
            f"The causal direction: does {lens_a} create {lens_b}'s conditions, or vice versa?"
        )

        tri = Triangle(
            visible=visible,
            void_1=void_1,
            void_2=void_2,
            lens=f"{lens_a}x{lens_b}",
            subject=self.subject_name,
            source="collide",
            score=0.5 * (tri_a.score + tri_b.score) * 1.2,  # collision bonus
        )
        self._collision_triangles.append(tri)
        return tri

    def tessellate(self) -> list[Triangle]:
        """All 15 edge-collisions of the dekagon.

        Runs all 15 predefined edge pairs and returns their Triangles.
        After tessellate(), the sphere() has full data.
        """
        results = []
        # Clear previous collisions to avoid duplicates on re-call
        self._collision_triangles = []
        for lens_a, lens_b in EDGE_PAIRS:
            tri = self.collide(lens_a, lens_b)
            results.append(tri)
        return results

    def sphere(self) -> Sphere:
        """The complete perception. 10 lenses + 15 collision triangles.

        Runs tessellate() if not already done, then assembles the Sphere.
        """
        if len(self._collision_triangles) < 15:
            self.tessellate()

        all_triangles = self._primary_triangles + self._collision_triangles
        s = Sphere(
            subject_name=self.subject_name,
            triangles=all_triangles,
            lenses=list(self.bewusstseine.values()),
        )
        return s

    def missing(self) -> list[str]:
        """What even 10 eyes cannot see (the void of the void).

        These are the structural blind spots of the Dekagon architecture.
        Meta-voids: what no lens can see because no lens was designed to.
        """
        return [
            "The subject's own experience of being perceived by these 10 lenses",
            "Lenses 11-∞: every dekagon needs an 11th lens to see itself",
            "Temporal depth: what these lenses see NOW vs. what they would see in 10 years",
            "The interaction between all 10 lenses simultaneously (only pairs are collided)",
            "What the subject hides specifically from systematic observation",
        ]

    def get_lens(self, name: str) -> Bewusstsein:
        if name not in self.bewusstseine:
            raise ValueError(f"Unknown lens: {name!r}")
        return self.bewusstseine[name]

    def save(self, output_dir: Path | str | None = None) -> Path:
        """Save sphere to JSON in data/omega/dekagon/."""
        if output_dir is None:
            # Try to find omega root
            here = Path(__file__).parent
            for parent in [here, here.parent, here.parent.parent, here.parent.parent.parent]:
                candidate = parent / "data" / "omega" / "dekagon"
                if (parent / "data").exists():
                    output_dir = candidate
                    break
            if output_dir is None:
                output_dir = Path.cwd() / "data" / "omega" / "dekagon"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        sphere = self.sphere()
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.subject_name)
        filename = output_dir / f"dekagon_{safe_name}_{int(time.time())}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(sphere.to_dict(), f, indent=2, ensure_ascii=False)

        return filename

    def __repr__(self) -> str:
        return (
            f"Dekagon({self.subject_name!r}, "
            f"primary={len(self._primary_triangles)}, "
            f"collisions={len(self._collision_triangles)})"
        )


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _truncate(v: Any, max_len: int = 80) -> str:
    """Truncate any value to a short string."""
    s = str(v)
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


def _compose_collision_visible(
    lens_a: str, visible_a: str,
    lens_b: str, visible_b: str,
    subject_name: str,
) -> str:
    """Compose the emergent visible finding from a lens × lens collision.

    The emergent content exists in neither lens alone.
    We find the TENSION between what each sees.
    """
    # Different collision patterns based on lens pair semantics
    pair = frozenset([lens_a, lens_b])

    # Curated tension descriptions for known meaningful pairs
    curated: dict[frozenset, str] = {
        frozenset(["nacht", "boden"]): (
            f"{subject_name}: what lies beneath is most active at night. "
            f"The oldest layers and the hidden present-day activity share the same darkness."
        ),
        frozenset(["kinder", "mauer"]): (
            f"{subject_name}: the smallest and the excluded meet at the same wall. "
            f"Children cannot get in; potential cannot get out. The barrier is bidirectional."
        ),
        frozenset(["geld", "stille"]): (
            f"{subject_name}: what flows (money) and what is silent (unmeasured labor) "
            f"are structurally linked. The silence subsidizes the flow."
        ),
        frozenset(["wissen", "liebe"]): (
            f"{subject_name}: knowledge that does not connect finds its missing link in care. "
            f"Where expertise fails to reach practice, it is often a relationship that is missing."
        ),
        frozenset(["wasser", "sprache"]): (
            f"{subject_name}: what flows through carries language — or loses it in transit. "
            f"Transit populations leave traces in code-switching, dialect drift, and untranslated names."
        ),
        frozenset(["boden", "kinder"]): (
            f"{subject_name}: the oldest layer shapes what newcomers first encounter. "
            f"Historical sediment becomes the default interface for the arriving."
        ),
        frozenset(["kinder", "geld"]): (
            f"{subject_name}: the smallest perspective reveals who actually pays. "
            f"What costs nothing officially costs children's futures actually."
        ),
        frozenset(["geld", "wissen"]): (
            f"{subject_name}: value flows away from where knowledge accumulates. "
            f"Brain drain is a financial phenomenon as much as a knowledge phenomenon."
        ),
        frozenset(["wissen", "sprache"]): (
            f"{subject_name}: expertise cannot cross language barriers, so it stays locked. "
            f"Language is not just communication — it is the container that holds or loses knowledge."
        ),
        frozenset(["sprache", "nacht"]): (
            f"{subject_name}: in the dark, language changes. "
            f"What is said after midnight differs from what is said in daylight — and both are true."
        ),
        frozenset(["nacht", "wasser"]): (
            f"{subject_name}: the hidden flow. What moves through at night "
            f"shapes the daytime without appearing in it."
        ),
        frozenset(["wasser", "mauer"]): (
            f"{subject_name}: flow meets barrier. What cannot pass through "
            f"accumulates, pressurizes, and eventually finds another route — or doesn't."
        ),
        frozenset(["mauer", "stille"]): (
            f"{subject_name}: the wall and the silence reinforce each other. "
            f"What is imprisoned is also unmeasured. Locked potential appears, on paper, as absence."
        ),
        frozenset(["stille", "liebe"]): (
            f"{subject_name}: the silence is held by love. "
            f"What no dashboard measures is sustained by the people who refuse to let it disappear."
        ),
        frozenset(["liebe", "boden"]): (
            f"{subject_name}: love is the oldest layer. "
            f"Every foundation, when excavated far enough, reveals the bonds that made building possible."
        ),
    }

    if pair in curated:
        return curated[pair]

    # Generic collision: juxtapose what each lens sees
    a_short = visible_a[:80] if visible_a else f"{lens_a} sees nothing"
    b_short = visible_b[:80] if visible_b else f"{lens_b} sees nothing"
    return (
        f"{subject_name} [{lens_a} x {lens_b}]: "
        f"When {lens_a} ({a_short[:40]}...) "
        f"meets {lens_b} ({b_short[:40]}...), "
        f"the tension between them reveals a dimension neither lens alone reaches."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_sphere(sphere: Sphere, verbose: bool = False) -> None:
    print(sphere.summary())
    if verbose:
        print("\n--- COLLISION TRIANGLES (15 edge collisions) ---\n")
        for tri in sphere.collision_triangles:
            print(tri.render())
            print()


def main() -> int:
    """CLI entry point.

    Usage:
        python3 -m void_intelligence.dekagon "Straubing"
        python3 -m void_intelligence.dekagon --collide nacht wissen
        python3 -m void_intelligence.dekagon --sphere "TUM Campus Straubing"
        python3 -m void_intelligence.dekagon --subject data/business/client-health.json
        python3 -m void_intelligence.dekagon --lenses
        python3 -m void_intelligence.dekagon --save "OMEGA"
    """
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("Usage:")
        print('  python3 -m void_intelligence.dekagon "Subject Name"')
        print('  python3 -m void_intelligence.dekagon --collide lens_a lens_b "Subject"')
        print('  python3 -m void_intelligence.dekagon --sphere "Subject Name"')
        print('  python3 -m void_intelligence.dekagon --subject path/to/file.json')
        print('  python3 -m void_intelligence.dekagon --lenses')
        print('  python3 -m void_intelligence.dekagon --save "Subject"')
        return 0

    if args[0] == "--lenses":
        print("THE 10 UNIVERSAL LENSES")
        print("=" * 52)
        for name in LENS_ORDER:
            d = LENSES_DEFINITION[name]
            print(f"\n  [{d['symbol']}] {name.upper()}")
            print(f"      Position: {d.get('formula_position', '')}")
            print(f"      Question: {d['question']}")
            print(f"      Sees:     {d.get('sees', '')[:70]}")
        return 0

    if args[0] == "--collide":
        # --collide lens_a lens_b ["Subject Name"]
        if len(args) < 3:
            print("Usage: --collide lens_a lens_b [subject_name]")
            return 1
        lens_a = args[1]
        lens_b = args[2]
        subject_name = args[3] if len(args) > 3 else "unknown"
        d = Dekagon.from_subject({"name": subject_name})
        try:
            tri = d.collide(lens_a, lens_b)
        except ValueError as e:
            print(f"Error: {e}")
            return 1
        print(tri.render())
        return 0

    if args[0] == "--subject":
        if len(args) < 2:
            print("Usage: --subject path/to/file.json")
            return 1
        p = Path(args[1])
        if not p.exists():
            print(f"File not found: {p}")
            return 1
        with open(p) as f:
            subject_data = json.load(f)
        subject_data.setdefault("name", p.stem)
        d = Dekagon.from_subject(subject_data)
        sphere = d.sphere()
        _print_sphere(sphere, verbose="--verbose" in args)
        return 0

    if args[0] == "--sphere":
        subject = args[1] if len(args) > 1 else "unknown"
        d = Dekagon.from_subject(subject)
        sphere = d.sphere()
        _print_sphere(sphere, verbose=True)
        return 0

    if args[0] == "--save":
        subject = args[1] if len(args) > 1 else "unknown"
        d = Dekagon.from_subject(subject)
        path = d.save()
        print(f"Sphere saved: {path}")
        return 0

    # Default: perceive the subject and show summary sphere
    subject = args[0]
    d = Dekagon.from_subject(subject)
    sphere = d.sphere()
    _print_sphere(sphere)
    return 0


if __name__ == "__main__":
    sys.exit(main())
