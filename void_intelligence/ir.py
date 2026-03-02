"""
void_intelligence.ir --- .x->[]~ Intermediate Representation.

The language of living systems. Not a data format. A THINKING format.

  .  = Atom (irreducible event, fact)
  x  = Collision (tensor of two atoms, emergence)
  -> = Projection (x becomes action, necessary but incomplete)
  [] = Potential (pregnant void between events)
  ~  = Resonance (feedback loop, system learns from itself)

Usage:
    from void_intelligence import Atom, collide, project, resonate

    a = Atom(domain="health", type="burnout_rising", value={"score": 78})
    b = Atom(domain="business", type="invoice_overdue", value={"days": 14})
    collision = collide(a, b)
    action = project(collision, "delegate_work")
    learning = resonate(collision.id, "success", 0.8)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class IRType(Enum):
    """The 5 fundamental operations of reality."""
    ATOM = "."
    COLLISION = "x"
    PROJECTION = "->"
    POTENTIAL = "[]"
    RESONANCE = "~"


@dataclass
class Atom:
    """A point. Irreducible. Meaningless alone.

    Only through x (collision) with another Atom does meaning emerge.
    A single event IS nothing --- it BECOMES something through collision.
    """
    domain: str
    type: str
    value: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"._{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    source: str = ""

    @property
    def ir_type(self) -> IRType:
        return IRType.ATOM

    def to_dict(self) -> dict:
        return {
            "ir": ".", "id": self.id, "domain": self.domain,
            "type": self.type, "value": self.value,
            "source": self.source, "t": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> Atom:
        return cls(
            domain=d.get("domain", ""), type=d.get("type", ""),
            value=d.get("value", d.get("data", {})),
            id=d.get("id", f"._{uuid.uuid4().hex[:8]}"),
            timestamp=d.get("t", d.get("timestamp", time.time())),
            source=d.get("source", ""),
        )

    def __repr__(self) -> str:
        return f".({self.domain}:{self.type})"


@dataclass
class Collision:
    """Two atoms collide. Meaning emerges.

    x is NOT addition (a + b).
    x is NOT sequence (a -> b).
    x is tensor: the result exists in NEITHER input.
    """
    atoms: list[Atom]
    score: float = 0.0
    pattern: str = ""
    emergent: str = ""
    id: str = field(default_factory=lambda: f"x_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def ir_type(self) -> IRType:
        return IRType.COLLISION

    @property
    def domains(self) -> set[str]:
        return {a.domain for a in self.atoms}

    @property
    def density(self) -> float:
        if not self.atoms:
            return 0.0
        time_spread = max(a.timestamp for a in self.atoms) - min(a.timestamp for a in self.atoms)
        time_factor = 1.0 / (1.0 + time_spread / 60.0)
        return self.score * len(self.domains) * time_factor

    def to_dict(self) -> dict:
        return {
            "ir": "x", "id": self.id,
            "atoms": [a.to_dict() for a in self.atoms],
            "domains": sorted(self.domains),
            "score": self.score, "density": self.density,
            "pattern": self.pattern, "emergent": self.emergent,
            "t": self.timestamp,
        }

    def __repr__(self) -> str:
        parts = " x ".join(repr(a) for a in self.atoms)
        return f"x({parts} | score={self.score:.2f})"


@dataclass
class Projection:
    """x becomes concrete. BUT: every -> is incomplete.

    Every projection loses information. x has infinite dimensions.
    -> projects onto 1D (one action). This is NECESSARY (we must act)
    but NEVER the whole truth.

    Therefore: every -> carries its incompleteness as metadata.
    """
    collision: Collision
    action: str
    template: str = ""
    priority: str = "L3"
    auto_execute: bool = False
    confidence: float = 0.0
    lost_dimensions: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"->_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def ir_type(self) -> IRType:
        return IRType.PROJECTION

    def to_dict(self) -> dict:
        return {
            "ir": "->", "id": self.id,
            "collision_id": self.collision.id,
            "action": self.action, "priority": self.priority,
            "confidence": self.confidence,
            "lost_dimensions": self.lost_dimensions,
            "t": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"->({self.action} | conf={self.confidence:.2f})"


@dataclass
class Potential:
    """The silence between events. Not empty. PREGNANT.

    [] is the most important state: here, EVERYTHING can happen.
    A system without [] is dead (100% -> = machine gun).
    A system with only [] is also dead (0% x = meditation without action).

    delta_opt lies BETWEEN [] and x --- the Stribeck point.
    """
    domain: str = ""
    duration_sec: float = 0.0
    fertility: float = 0.0
    id: str = field(default_factory=lambda: f"[]_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def ir_type(self) -> IRType:
        return IRType.POTENTIAL

    def to_dict(self) -> dict:
        return {
            "ir": "[]", "id": self.id, "domain": self.domain,
            "duration_sec": self.duration_sec,
            "fertility": self.fertility, "t": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"[]({self.domain} {self.duration_sec:.0f}s)"


@dataclass
class Resonance:
    """The system learns from itself.

    When x leads to -> and the result was good/bad,
    that flows BACK into x evaluation.

    ~ is the difference between a dead system (-> -> -> ->)
    and a living one (x ~ x ~ x ~ ...).
    """
    collision_id: str
    projection_id: str = ""
    outcome: str = ""
    impact: float = 0.0
    learning: str = ""
    weight_delta: float = 0.0
    id: str = field(default_factory=lambda: f"~_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def ir_type(self) -> IRType:
        return IRType.RESONANCE

    def to_dict(self) -> dict:
        return {
            "ir": "~", "id": self.id,
            "collision_id": self.collision_id,
            "outcome": self.outcome, "impact": self.impact,
            "weight_delta": self.weight_delta, "t": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"~({self.outcome} impact={self.impact:+.2f})"


# ── Operations ───────────────────────────────────────────────────

def collide(*atoms: Atom, score: float = 0.0, pattern: str = "") -> Collision:
    """x --- Two or more atoms collide. The fundamental operation."""
    return Collision(
        atoms=list(atoms), score=score,
        pattern=pattern or " x ".join(f"{a.domain}:{a.type}" for a in atoms),
    )


def project(
    collision: Collision, action: str,
    priority: str = "L3", confidence: float = 0.5,
    lost: list[str] | None = None,
) -> Projection:
    """-> --- Collision becomes action. Necessary. Incomplete."""
    return Projection(
        collision=collision, action=action, priority=priority,
        auto_execute=priority in ("L1", "L2"), confidence=confidence,
        lost_dimensions=lost or ["temporal_context", "emotional_state"],
    )


def resonate(
    collision_id: str, outcome: str, impact: float,
    learning: str = "",
) -> Resonance:
    """~ --- System learns from outcome. impact: -1.0 to +1.0."""
    return Resonance(
        collision_id=collision_id, outcome=outcome,
        impact=impact, learning=learning,
        weight_delta=impact * 0.1,
    )


# ── System Pulse ─────────────────────────────────────────────────

@dataclass
class SystemPulse:
    """The pulse of the system, measured in IR.

    Not healthy/unhealthy (binary = -> thinking).
    But: how ALIVE is the system? (x density)
    """
    atoms_per_min: float = 0.0
    collisions_per_min: float = 0.0
    potential_ratio: float = 0.0
    resonance_count: int = 0
    density: float = 0.0

    @property
    def alive(self) -> bool:
        return self.collisions_per_min > 0 and self.potential_ratio > 0

    @property
    def delta_opt_distance(self) -> float:
        """Distance from Stribeck minimum. 0.0 = in flow."""
        return abs(self.potential_ratio - 0.4)

    def to_dict(self) -> dict:
        return {
            "pulse": {
                ".": self.atoms_per_min, "x": self.collisions_per_min,
                "[]": self.potential_ratio, "~": self.resonance_count,
            },
            "density": self.density, "alive": self.alive,
            "delta_opt_distance": self.delta_opt_distance,
        }


class PatternWeights:
    """Weights of known collision patterns. ~ shifts them over time."""

    def __init__(self):
        self.weights: dict[str, float] = {}

    def get(self, pattern: str) -> float:
        return self.weights.get(pattern, 1.0)

    def apply_resonance(self, r: Resonance, pattern: str):
        current = self.get(pattern)
        self.weights[pattern] = max(0.0, current + r.weight_delta)
