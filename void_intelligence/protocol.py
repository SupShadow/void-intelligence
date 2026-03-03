"""
void_intelligence.protocol --- The Breathing Protocol.

A standardized wire format for .x->[]~ breath cycles.

The industry has HTTP, gRPC, GraphQL for data exchange.
We have the Breathing Protocol for LIVING SYSTEM exchange.

Every breath cycle flows through 5 stages. This protocol
captures each stage as a frame, serializes to JSONL, and
can reconstruct the full cycle on the other side.

Wire format (JSONL, one frame per line):

    {"v":"1.0","ir":"^","breath_id":"b_abc","prompt":"...","ts":1709...}
    {"v":"1.0","ir":".","atom_id":".._def","domain":"health","type":"domain_signal",...}
    {"v":"1.0","ir":".","atom_id":".._ghi","domain":"business","type":"entity_number",...}
    {"v":"1.0","ir":"x","collision_id":"x_jkl","score":0.72,"pattern":"health x business",...}
    {"v":"1.0","ir":"->","proj_id":"->_mno","response_len":142,"lost":["emotional_context"],...}
    {"v":"1.0","ir":"[]","pot_id":"[]_pqr","fertility":0.6,"silence":["uncollided:finance"],...}
    {"v":"1.0","ir":"~","res_id":"~_stu","impact":0.8,"outcome":"success",...}
    {"v":"1.0","ir":"$","breath_id":"b_abc","density":0.73,"x_score":0.65,"latency_ms":142}

Frame types:
    ^  = Breath header (inhale)
    .  = Atom
    x  = Collision
    -> = Projection
    [] = Potential
    ~  = Resonance
    $  = Breath footer (exhale)

Usage:
    from void_intelligence.protocol import encode, decode, validate

    # Encode a cycle to wire format
    wire = encode(cycle)
    print(wire.to_jsonl())     # JSONL string
    wire.to_file("breath.jsonl")  # Write to file

    # Decode back
    cycle2 = decode(wire)

    # Stream (emit frames as they happen)
    for frame in wire.frames:
        send_to_other_organism(frame.to_json())

The industry sends messages.
We send breaths.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Iterator

from void_intelligence.ir import (
    Atom,
    Collision,
    Projection,
    Potential,
    Resonance,
    collide as ir_collide,
    project as ir_project,
)
from void_intelligence.organism import HexCoord
from void_intelligence.pipeline import BreathCycle


# ── Protocol Constants ────────────────────────────────────

PROTOCOL_VERSION = "1.0"

# Frame type markers (extend IRType with header/footer)
FRAME_HEADER = "^"    # Inhale: breath begins
FRAME_ATOM = "."      # Atom extracted
FRAME_COLLISION = "x"  # Collision detected
FRAME_PROJECTION = "->"  # Response projected
FRAME_POTENTIAL = "[]"   # Silence detected
FRAME_RESONANCE = "~"    # Resonance (feedback)
FRAME_FOOTER = "$"       # Exhale: breath complete

_VALID_FRAMES = frozenset({
    FRAME_HEADER, FRAME_ATOM, FRAME_COLLISION,
    FRAME_PROJECTION, FRAME_POTENTIAL, FRAME_RESONANCE,
    FRAME_FOOTER,
})


# ── Breath Frame ──────────────────────────────────────────

@dataclass
class BreathFrame:
    """One frame in the breathing protocol.

    Each frame = one line of JSONL.
    Self-describing: the 'ir' field tells you what it is.
    """

    ir: str   # Frame type: ^ . x -> [] ~ $
    data: dict
    version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict:
        return {"v": self.version, "ir": self.ir, **self.data}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    @classmethod
    def from_dict(cls, d: dict) -> "BreathFrame":
        ir = d.pop("ir", "")
        version = d.pop("v", PROTOCOL_VERSION)
        return cls(ir=ir, data=d, version=version)

    @classmethod
    def from_json(cls, line: str) -> "BreathFrame":
        return cls.from_dict(json.loads(line))


# ── Breath Stream ─────────────────────────────────────────

@dataclass
class BreathStream:
    """A complete breath as a stream of frames.

    The breath IS the stream. Not a container OF frames.
    Each frame can be sent independently (streaming protocol).
    """

    breath_id: str
    frames: list[BreathFrame] = field(default_factory=list)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def has_header(self) -> bool:
        return any(f.ir == FRAME_HEADER for f in self.frames)

    @property
    def has_footer(self) -> bool:
        return any(f.ir == FRAME_FOOTER for f in self.frames)

    @property
    def complete(self) -> bool:
        """Is this a complete breath (header + at least . and -> + footer)?"""
        return self.has_header and self.has_footer

    def atoms(self) -> list[BreathFrame]:
        return [f for f in self.frames if f.ir == FRAME_ATOM]

    def collisions(self) -> list[BreathFrame]:
        return [f for f in self.frames if f.ir == FRAME_COLLISION]

    def iter_frames(self) -> Iterator[BreathFrame]:
        """Iterate frames. For streaming."""
        yield from self.frames

    # ── Serialization ────────────────────────────────────

    def to_jsonl(self) -> str:
        """Encode entire stream as JSONL string."""
        return "\n".join(f.to_json() for f in self.frames)

    def to_file(self, path: str) -> None:
        """Write stream to JSONL file."""
        with open(path, "w") as fh:
            for frame in self.frames:
                fh.write(frame.to_json())
                fh.write("\n")

    @classmethod
    def from_jsonl(cls, jsonl: str) -> "BreathStream":
        """Parse JSONL string into a BreathStream."""
        frames = []
        breath_id = ""

        for line in jsonl.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            frame = BreathFrame.from_json(line)
            frames.append(frame)
            if frame.ir == FRAME_HEADER:
                breath_id = frame.data.get("breath_id", "")

        return cls(breath_id=breath_id, frames=frames)

    @classmethod
    def from_file(cls, path: str) -> "BreathStream":
        """Read JSONL file into a BreathStream."""
        with open(path) as fh:
            return cls.from_jsonl(fh.read())

    def summary(self) -> dict:
        """Quick summary of the stream."""
        counts: dict[str, int] = {}
        for f in self.frames:
            counts[f.ir] = counts.get(f.ir, 0) + 1
        return {
            "breath_id": self.breath_id,
            "frames": self.frame_count,
            "complete": self.complete,
            "types": counts,
        }


# ── Encode ────────────────────────────────────────────────

def encode(cycle: BreathCycle) -> BreathStream:
    """Encode a BreathCycle into the Breathing Protocol wire format.

    Produces one BreathStream with frames in order:
        ^ (header) -> . (atoms) -> x (collisions) -> -> (projection)
        -> [] (potential) -> ~ (resonance, if present) -> $ (footer)

    Every frame is self-contained. Can be sent independently.
    """
    breath_id = f"b_{uuid.uuid4().hex[:8]}"
    frames: list[BreathFrame] = []

    # ^ HEADER (inhale)
    frames.append(BreathFrame(
        ir=FRAME_HEADER,
        data={
            "breath_id": breath_id,
            "prompt": cycle.prompt[:200],
            "model": cycle.model,
            "ts": cycle.timestamp,
            "hex": cycle.hex_coord.to_dict(),
        },
    ))

    # . ATOMS
    for atom in cycle.atoms:
        frames.append(BreathFrame(
            ir=FRAME_ATOM,
            data={
                "breath_id": breath_id,
                "atom_id": atom.id,
                "domain": atom.domain,
                "type": atom.type,
                "source": atom.source,
                "value": atom.value,
                "ts": atom.timestamp,
            },
        ))

    # x COLLISIONS
    for col in cycle.collisions:
        frames.append(BreathFrame(
            ir=FRAME_COLLISION,
            data={
                "breath_id": breath_id,
                "collision_id": col.id,
                "score": round(col.score, 4),
                "pattern": col.pattern,
                "emergent": col.emergent,
                "domains": sorted(col.domains),
                "atom_ids": [a.id for a in col.atoms],
                "density": round(col.density, 4),
            },
        ))

    # -> PROJECTION
    if cycle.projection:
        frames.append(BreathFrame(
            ir=FRAME_PROJECTION,
            data={
                "breath_id": breath_id,
                "proj_id": cycle.projection.id,
                "response_len": len(cycle.response),
                "confidence": round(cycle.projection.confidence, 3),
                "lost": cycle.lost_dimensions,
                "action": cycle.projection.action[:100],
            },
        ))

    # [] POTENTIAL
    if cycle.potential:
        frames.append(BreathFrame(
            ir=FRAME_POTENTIAL,
            data={
                "breath_id": breath_id,
                "pot_id": cycle.potential.id,
                "fertility": round(cycle.potential.fertility, 3),
                "silence": cycle.silence,
                "domain": cycle.potential.domain,
            },
        ))

    # ~ RESONANCE (may not be present yet)
    if cycle.resonance:
        frames.append(BreathFrame(
            ir=FRAME_RESONANCE,
            data={
                "breath_id": breath_id,
                "res_id": cycle.resonance.id,
                "impact": round(cycle.resonance.impact, 3),
                "outcome": cycle.resonance.outcome,
                "learning": cycle.resonance.learning,
                "collision_id": cycle.resonance.collision_id,
            },
        ))

    # $ FOOTER (exhale)
    frames.append(BreathFrame(
        ir=FRAME_FOOTER,
        data={
            "breath_id": breath_id,
            "density": round(cycle.density, 4),
            "x_score": round(cycle.x_score, 4),
            "latency_ms": round(cycle.latency_ms, 1),
            "alive": cycle.alive,
            "learnings": cycle.learnings[:5],
        },
    ))

    return BreathStream(breath_id=breath_id, frames=frames)


# ── Decode ────────────────────────────────────────────────

def decode(stream: BreathStream) -> BreathCycle:
    """Decode a BreathStream back into a BreathCycle.

    Reconstructs the full cycle from wire frames.
    Missing frames = incomplete cycle (still valid, just partial).
    """
    # Defaults
    prompt = ""
    model = ""
    timestamp = time.time()
    hex_coord = HexCoord()
    atoms: list[Atom] = []
    collisions: list[Collision] = []
    projection: Projection | None = None
    potential: Potential | None = None
    resonance: Resonance | None = None
    x_score = 0.0
    response = ""
    lost_dimensions: list[str] = []
    silence: list[str] = []
    latency_ms = 0.0
    learnings: list[str] = []

    # Atom lookup for collision reconstruction
    atom_map: dict[str, Atom] = {}

    for frame in stream.frames:
        d = frame.data

        if frame.ir == FRAME_HEADER:
            prompt = d.get("prompt", "")
            model = d.get("model", "")
            timestamp = d.get("ts", time.time())
            hd = d.get("hex", {})
            hex_coord = HexCoord(
                ruhe_druck=hd.get("ruhe_druck", 0.0),
                stille_resonanz=hd.get("stille_resonanz", 0.0),
                allein_zusammen=hd.get("allein_zusammen", 0.0),
                empfangen_schaffen=hd.get("empfangen_schaffen", 0.0),
                sein_tun=hd.get("sein_tun", 0.0),
                langsam_schnell=hd.get("langsam_schnell", 0.0),
            )

        elif frame.ir == FRAME_ATOM:
            atom = Atom(
                domain=d.get("domain", ""),
                type=d.get("type", ""),
                value=d.get("value", {}),
                id=d.get("atom_id", ""),
                source=d.get("source", ""),
                timestamp=d.get("ts", time.time()),
            )
            atoms.append(atom)
            atom_map[atom.id] = atom

        elif frame.ir == FRAME_COLLISION:
            # Reconstruct collision atoms from IDs
            col_atoms = [
                atom_map[aid] for aid in d.get("atom_ids", [])
                if aid in atom_map
            ]
            if not col_atoms:
                # Fallback: create placeholder atoms from domains
                for dom in d.get("domains", []):
                    col_atoms.append(Atom(domain=dom, type="reconstructed", value={}))

            col = Collision(
                atoms=col_atoms,
                score=d.get("score", 0.0),
                pattern=d.get("pattern", ""),
                emergent=d.get("emergent", ""),
                id=d.get("collision_id", ""),
            )
            collisions.append(col)

        elif frame.ir == FRAME_PROJECTION:
            action = d.get("action", "")
            response = action  # Best we can reconstruct
            lost_dimensions = d.get("lost", [])
            best_col = collisions[0] if collisions else ir_collide(
                Atom(domain="general", type="direct", value={}),
                Atom(domain="general", type="direct", value={}),
            )
            projection = ir_project(
                best_col,
                action=action,
                confidence=d.get("confidence", 0.5),
                lost=lost_dimensions,
            )

        elif frame.ir == FRAME_POTENTIAL:
            silence = d.get("silence", [])
            potential = Potential(
                domain=d.get("domain", ""),
                fertility=d.get("fertility", 0.0),
                id=d.get("pot_id", ""),
            )

        elif frame.ir == FRAME_RESONANCE:
            resonance = Resonance(
                collision_id=d.get("collision_id", ""),
                outcome=d.get("outcome", ""),
                impact=d.get("impact", 0.0),
                learning=d.get("learning", ""),
                id=d.get("res_id", ""),
            )

        elif frame.ir == FRAME_FOOTER:
            x_score = d.get("x_score", 0.0)
            latency_ms = d.get("latency_ms", 0.0)
            learnings = d.get("learnings", [])

    # Reconstruct cycle
    cycle = BreathCycle(
        prompt=prompt,
        hex_coord=hex_coord,
        timestamp=timestamp,
        model=model,
    )
    cycle.atoms = atoms
    cycle.collisions = collisions
    cycle.x_score = x_score
    cycle.projection = projection
    cycle.response = response
    cycle.lost_dimensions = lost_dimensions
    cycle.potential = potential
    cycle.silence = silence
    cycle.resonance = resonance
    cycle.latency_ms = latency_ms
    cycle.learnings = learnings

    return cycle


# ── Validate ──────────────────────────────────────────────

def validate(stream: BreathStream) -> list[str]:
    """Validate a BreathStream. Returns errors (empty = valid).

    Checks:
        - Has header and footer
        - All frames have valid ir types
        - All frames have matching breath_id
        - Header comes first, footer comes last
        - At least one atom frame
        - Version compatibility
    """
    errors: list[str] = []

    if not stream.frames:
        errors.append("empty stream")
        return errors

    # Version check
    for f in stream.frames:
        if f.version != PROTOCOL_VERSION:
            errors.append(f"version mismatch: {f.version} != {PROTOCOL_VERSION}")
            break

    # Frame type validity
    for i, f in enumerate(stream.frames):
        if f.ir not in _VALID_FRAMES:
            errors.append(f"frame {i}: invalid ir type '{f.ir}'")

    # Header/footer
    if not stream.has_header:
        errors.append("missing header (^)")
    if not stream.has_footer:
        errors.append("missing footer ($)")

    # Order: header first, footer last
    if stream.frames and stream.frames[0].ir != FRAME_HEADER:
        errors.append("header (^) must be first frame")
    if stream.frames and stream.frames[-1].ir != FRAME_FOOTER:
        errors.append("footer ($) must be last frame")

    # At least one atom
    if not stream.atoms():
        errors.append("no atom (.) frames")

    # Consistent breath_id
    breath_ids = {f.data.get("breath_id") for f in stream.frames if "breath_id" in f.data}
    if len(breath_ids) > 1:
        errors.append(f"inconsistent breath_ids: {breath_ids}")

    # Stage order: ^ -> . -> x -> -> -> [] -> ~ -> $
    stage_order = {
        FRAME_HEADER: 0, FRAME_ATOM: 1, FRAME_COLLISION: 2,
        FRAME_PROJECTION: 3, FRAME_POTENTIAL: 4,
        FRAME_RESONANCE: 5, FRAME_FOOTER: 6,
    }
    last_stage = -1
    for f in stream.frames:
        stage = stage_order.get(f.ir, -1)
        if stage < last_stage and f.ir != FRAME_ATOM and f.ir != FRAME_COLLISION:
            errors.append(f"out of order: {f.ir} after stage {last_stage}")
        if stage > last_stage:
            last_stage = stage

    return errors
