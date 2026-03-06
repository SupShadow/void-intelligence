"""
void_intelligence.fingerprint --- The Portable Identity.

Module 12 of the VOID SEXAGON. The anti-lock-in feature.

Every other AI platform is a walled garden:
    ChatGPT memory: locked to ChatGPT.
    Claude projects: locked to Claude.
    Gemini context: locked to Gemini.

VOID Fingerprint: export once, run anywhere.
    Export from Ollama Void. Import to Claude Void. Same personality.
    Your Void is yours. Forever.

This is structurally impossible for them to copy without destroying their
churn revenue model. We give portability because we don't NEED lock-in.
The value is in the pattern, not the platform.

Architecture:
    VoidFingerprint     = the portable JSON data structure
    FingerprintExporter = collects state from all available modules -> JSON
    FingerprintImporter = loads JSON -> restores state in all available modules

The killer feature:
    to_system_prompt() converts ANY fingerprint to a plain-text system prompt.
    Even without VOID installed, paste this into any chat interface.
    The personality travels as TEXT. Unstoppable.

Zero external dependencies. stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Graceful imports --- all optional. Fingerprint works even standalone.
# ---------------------------------------------------------------------------

try:
    from void_intelligence.conversation_rings import RingMemory, Pattern, _hex_to_dict, _hex_from_dict
    _HAS_RINGS = True
except ImportError:
    _HAS_RINGS = False

try:
    from void_intelligence.tool_breathing import ToolBreather, HexCoord
    _HAS_TOOLS = True
except ImportError:
    _HAS_TOOLS = False
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
    from void_intelligence.anti_addiction import SaturationSensor
    _HAS_ADDICTION = True
except ImportError:
    _HAS_ADDICTION = False


# ---------------------------------------------------------------------------
# VoidFingerprint --- the portable identity
# ---------------------------------------------------------------------------

FINGERPRINT_VERSION = "1.0.0"

_HEX_AXES = [
    "ruhe_druck",
    "stille_resonanz",
    "allein_zusammen",
    "empfangen_schaffen",
    "sein_tun",
    "langsam_schnell",
]


@dataclass
class VoidFingerprint:
    """The portable identity of a Void.

    ONE JSON file that contains everything this Void has learned.
    Export it. Import it anywhere. Your Void is yours.

    Fields are intentionally simple (no nested objects at the top level)
    so ANY language can read and use this format.
    """

    # Format
    version: str = FINGERPRINT_VERSION
    exported_at: float = field(default_factory=time.time)

    # Identity
    name: str = "unnamed"
    zodiac: str = ""
    birth_timestamp: float = 0.0

    # Personality (averaged hex across all interactions)
    personality_hex: dict = field(default_factory=lambda: {a: 0.0 for a in _HEX_AXES})
    interaction_count: int = 0
    total_conversations: int = 0

    # Learned patterns (from Conversation Rings)
    patterns: list = field(default_factory=list)

    # Tool preferences
    tool_affinities: dict = field(default_factory=dict)
    tool_bonds: list = field(default_factory=list)

    # Saturation profile
    avg_saturation_turn: float = 0.0
    avg_session_length: int = 0

    # Ring summary
    total_rings: int = 0
    avg_ring_width: float = 0.0
    growth_trajectory: list = field(default_factory=list)

    # Integrity
    checksum: str = ""


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

def _compute_checksum(fp_dict: dict) -> str:
    """SHA256 of the fingerprint content (excluding checksum field)."""
    d = {k: v for k, v in fp_dict.items() if k != "checksum"}
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Hex helpers (standalone, no module dependency)
# ---------------------------------------------------------------------------

def _avg_hex(hex_list: list[dict]) -> dict:
    """Average a list of hex dicts into one hex dict."""
    if not hex_list:
        return {a: 0.0 for a in _HEX_AXES}
    result = {a: 0.0 for a in _HEX_AXES}
    for h in hex_list:
        for axis in _HEX_AXES:
            result[axis] += h.get(axis, 0.0)
    n = len(hex_list)
    return {a: round(result[a] / n, 4) for a in _HEX_AXES}


def _hex_personality_descriptor(hex_dict: dict) -> list[str]:
    """Convert hex values into human-readable personality descriptors."""
    desc = []
    h = hex_dict

    # ruhe_druck: negative=calm, positive=urgent
    rd = h.get("ruhe_druck", 0.0)
    if rd > 0.25:
        desc.append("tends toward urgency")
    elif rd < -0.25:
        desc.append("prefers calm pacing")

    # stille_resonanz: negative=private, positive=communicative
    sr = h.get("stille_resonanz", 0.0)
    if sr > 0.25:
        desc.append("communicative, outward-facing")
    elif sr < -0.25:
        desc.append("internally focused, quiet")

    # allein_zusammen: negative=solo, positive=collaborative
    az = h.get("allein_zusammen", 0.0)
    if az > 0.25:
        desc.append("collaborative, team-oriented")
    elif az < -0.25:
        desc.append("independent, solo-focused")

    # empfangen_schaffen: negative=receiving, positive=creating
    es = h.get("empfangen_schaffen", 0.0)
    if es > 0.25:
        desc.append("action-oriented, creates and builds")
    elif es < -0.25:
        desc.append("reflective, prefers to receive and analyze")

    # sein_tun: negative=being, positive=doing
    st = h.get("sein_tun", 0.0)
    if st > 0.25:
        desc.append("execution-focused")
    elif st < -0.25:
        desc.append("presence-focused, reflective")

    # langsam_schnell: negative=slow, positive=fast
    ls = h.get("langsam_schnell", 0.0)
    if ls > 0.25:
        desc.append("fast-paced, high tempo")
    elif ls < -0.25:
        desc.append("deliberate, slow and deep")

    return desc


# ---------------------------------------------------------------------------
# FingerprintExporter
# ---------------------------------------------------------------------------

class FingerprintExporter:
    """Export a Void's identity into a portable JSON fingerprint.

    Collects state from all available modules.
    Gracefully handles missing modules (empty/zero values for those fields).
    """

    def export(
        self,
        ring_memory: Any = None,
        tool_breather: Any = None,
        collider: Any = None,
        journey_state: dict | None = None,
        output_path: str | Path | None = None,
    ) -> VoidFingerprint:
        """Collect state from all available modules and create fingerprint.

        Parameters
        ----------
        ring_memory:   RingMemory instance (optional)
        tool_breather: ToolBreather instance (optional)
        collider:      VoidCollider instance (optional, provides composite view)
        journey_state: dict from personality.json (optional)
        output_path:   if given, also saves the file
        """
        fp = VoidFingerprint()

        # --- Identity from journey_state (personality.json) -----------------
        if journey_state:
            fp.name = journey_state.get("name", "unnamed") or "unnamed"
            fp.zodiac = journey_state.get("zodiac", "")
            born_str = journey_state.get("born", "")
            if born_str:
                try:
                    from datetime import datetime
                    fp.birth_timestamp = datetime.fromisoformat(born_str).timestamp()
                except (ValueError, TypeError):
                    fp.birth_timestamp = 0.0
            fp.total_conversations = journey_state.get("conversations_count", 0)

        # --- Patterns + Rings from RingMemory --------------------------------
        all_hex_dicts: list[dict] = []
        saturation_turns: list[float] = []
        session_lengths: list[int] = []
        growth_trajectory: list[float] = []

        if ring_memory is not None and _HAS_RINGS:
            try:
                raw = ring_memory.export()

                # Patterns
                for p_dict in raw.get("patterns", []):
                    fp.patterns.append({
                        "trigger": p_dict.get("trigger", ""),
                        "response": p_dict.get("response", ""),
                        "confidence": round(p_dict.get("confidence", 0.3), 4),
                        "evidence_count": p_dict.get("evidence_count", 1),
                        "hex_context": p_dict.get("hex_context", {a: 0.0 for a in _HEX_AXES}),
                    })

                # Rings: build trajectory and personality hex
                rings = raw.get("rings", [])
                fp.total_rings = len(rings)
                ring_widths: list[float] = []

                for ring in rings:
                    # Growth trajectory from last V-score of each ring
                    v_traj = ring.get("v_score_trajectory", [])
                    if v_traj:
                        growth_trajectory.append(round(v_traj[-1], 4))

                    # Collect all hex drift points for personality averaging
                    for hex_d in ring.get("hex_drift", []):
                        all_hex_dicts.append(hex_d)

                    # Ring width (approximate from v_score_delta + pattern count)
                    # We re-use the Ring.width formula conceptually
                    patterns_in_ring = len(ring.get("patterns", []))
                    v_delta = 0.0
                    if len(v_traj) >= 2:
                        v_delta = max(0.0, v_traj[-1] - v_traj[0])
                    pattern_score = min(1.0, patterns_in_ring / 5)
                    turns = ring.get("total_turns", 0)
                    turns_score = min(1.0, turns / 10.0)
                    width = (v_delta * 0.5 + pattern_score * 0.35 + turns_score * 0.15)
                    ring_widths.append(width)

                    # Saturation approximation: use total_turns as session length
                    if turns > 0:
                        session_lengths.append(turns)

                    # Saturation turn: look for where V-score peaked
                    if v_traj:
                        peak_idx = v_traj.index(max(v_traj))
                        saturation_turns.append(float(peak_idx + 1))

                if ring_widths:
                    fp.avg_ring_width = round(sum(ring_widths) / len(ring_widths), 4)

                # Meta
                meta = raw.get("meta", {})
                if fp.total_conversations == 0:
                    fp.total_conversations = meta.get("total_conversations", 0)

            except Exception:
                pass  # graceful: module present but state extraction failed

        # Personality hex: average of all hex positions seen
        fp.personality_hex = _avg_hex(all_hex_dicts)
        fp.growth_trajectory = growth_trajectory

        # Session stats
        if saturation_turns:
            fp.avg_saturation_turn = round(
                sum(saturation_turns) / len(saturation_turns), 2
            )
        if session_lengths:
            fp.avg_session_length = round(
                sum(session_lengths) / len(session_lengths)
            )

        fp.interaction_count = sum(session_lengths)  # total turns across all sessions

        # --- Tool affinities from ToolBreather / ToolField -------------------
        tool_source = None
        if tool_breather is not None and _HAS_TOOLS:
            # ToolBreather wraps a ToolField; access via .field
            tool_source = getattr(tool_breather, "field", None)
        if tool_source is None and collider is not None:
            # VoidCollider holds a ToolBreather at .tool_breather
            tb = getattr(collider, "tool_breather", None)
            if tb is not None:
                tool_source = getattr(tb, "field", None)

        if tool_source is not None:
            try:
                tools = tool_source.tools  # list[BreathingTool]
                for t in tools:
                    fp.tool_affinities[t.name] = round(t.v_score, 4)

                # Build bonds: pairs of tools that were both called and both healthy
                healthy = [t for t in tools if t.call_count > 0 and t.health > 0.5]
                healthy.sort(key=lambda t: -t.v_score)
                # Top-5 healthy tools: build bonds between adjacent pairs
                for i in range(min(4, len(healthy) - 1)):
                    a = healthy[i]
                    b = healthy[i + 1]
                    bond_strength = round(
                        (a.v_score + b.v_score) / 2 * (a.health + b.health) / 2, 4
                    )
                    if bond_strength > 0.3:
                        fp.tool_bonds.append({
                            "tool_a": a.name,
                            "tool_b": b.name,
                            "strength": bond_strength,
                        })
            except Exception:
                pass  # graceful

        # --- Checksum --------------------------------------------------------
        fp.exported_at = time.time()
        raw_dict = self._to_dict(fp)
        fp.checksum = _compute_checksum(raw_dict)

        # --- Optional save ---------------------------------------------------
        if output_path is not None:
            self.save(fp, output_path)

        return fp

    def _to_dict(self, fp: VoidFingerprint) -> dict:
        """Convert VoidFingerprint to plain dict (no dataclass nesting)."""
        return {
            "version": fp.version,
            "exported_at": fp.exported_at,
            "name": fp.name,
            "zodiac": fp.zodiac,
            "birth_timestamp": fp.birth_timestamp,
            "personality_hex": fp.personality_hex,
            "interaction_count": fp.interaction_count,
            "total_conversations": fp.total_conversations,
            "patterns": fp.patterns,
            "tool_affinities": fp.tool_affinities,
            "tool_bonds": fp.tool_bonds,
            "avg_saturation_turn": fp.avg_saturation_turn,
            "avg_session_length": fp.avg_session_length,
            "total_rings": fp.total_rings,
            "avg_ring_width": fp.avg_ring_width,
            "growth_trajectory": fp.growth_trajectory,
            "checksum": fp.checksum,
        }

    def to_json(self, fp: VoidFingerprint) -> str:
        """Serialize fingerprint to pretty JSON."""
        return json.dumps(self._to_dict(fp), indent=2, ensure_ascii=False)

    def save(self, fp: VoidFingerprint, path: str | Path) -> Path:
        """Save fingerprint to file. Returns the path."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(fp), encoding="utf-8")
        return p


# ---------------------------------------------------------------------------
# FingerprintImporter
# ---------------------------------------------------------------------------

class FingerprintImporter:
    """Import a Void's identity from a portable fingerprint JSON."""

    def load(self, path: str | Path) -> VoidFingerprint:
        """Load fingerprint from JSON file."""
        p = Path(path)
        raw = json.loads(p.read_text(encoding="utf-8"))
        return self._from_dict(raw)

    def load_json(self, json_str: str) -> VoidFingerprint:
        """Load fingerprint from JSON string (for when you have the content)."""
        raw = json.loads(json_str)
        return self._from_dict(raw)

    def _from_dict(self, raw: dict) -> VoidFingerprint:
        fp = VoidFingerprint(
            version=raw.get("version", FINGERPRINT_VERSION),
            exported_at=raw.get("exported_at", 0.0),
            name=raw.get("name", "unnamed"),
            zodiac=raw.get("zodiac", ""),
            birth_timestamp=raw.get("birth_timestamp", 0.0),
            personality_hex=raw.get("personality_hex", {a: 0.0 for a in _HEX_AXES}),
            interaction_count=raw.get("interaction_count", 0),
            total_conversations=raw.get("total_conversations", 0),
            patterns=raw.get("patterns", []),
            tool_affinities=raw.get("tool_affinities", {}),
            tool_bonds=raw.get("tool_bonds", []),
            avg_saturation_turn=raw.get("avg_saturation_turn", 0.0),
            avg_session_length=raw.get("avg_session_length", 0),
            total_rings=raw.get("total_rings", 0),
            avg_ring_width=raw.get("avg_ring_width", 0.0),
            growth_trajectory=raw.get("growth_trajectory", []),
            checksum=raw.get("checksum", ""),
        )
        return fp

    def verify(self, fp: VoidFingerprint) -> bool:
        """Verify checksum integrity. Returns True if file is untampered."""
        if not fp.checksum:
            return False  # no checksum = unverifiable
        exporter = FingerprintExporter()
        raw_dict = exporter._to_dict(fp)
        expected = _compute_checksum(raw_dict)
        return fp.checksum == expected

    def apply(
        self,
        fp: VoidFingerprint,
        ring_memory: Any = None,
        tool_breather: Any = None,
        collider: Any = None,
    ) -> dict:
        """Apply fingerprint to modules. Returns summary of what was imported.

        This is the migration moment:
        - Patterns get loaded into RingMemory
        - Tool affinities inform ToolBreather
        - Personality hex becomes the starting point for new sessions

        The Void continues from where it left off --- on any model, any provider.
        """
        summary: dict[str, Any] = {
            "patterns_imported": 0,
            "tool_affinities_applied": 0,
            "tool_bonds_noted": 0,
            "personality_hex_loaded": False,
            "identity": f"{fp.name} ({fp.zodiac})" if fp.zodiac else fp.name,
            "total_conversations": fp.total_conversations,
            "total_rings": fp.total_rings,
            "warnings": [],
        }

        # --- Load patterns into RingMemory -----------------------------------
        if ring_memory is not None and _HAS_RINGS and fp.patterns:
            try:
                from void_intelligence.conversation_rings import Pattern, _hex_from_dict
                loaded = 0
                for p_dict in fp.patterns:
                    # Create Pattern objects and inject into global memory
                    p = Pattern(
                        id=str(uuid.uuid4())[:8],
                        trigger=p_dict.get("trigger", ""),
                        response=p_dict.get("response", ""),
                        evidence_count=p_dict.get("evidence_count", 1),
                        confidence=p_dict.get("confidence", 0.3),
                        hex_context=_hex_from_dict(p_dict.get("hex_context", {})),
                    )
                    if p.trigger and p.response:
                        ring_memory._patterns[p.id] = p
                        loaded += 1
                summary["patterns_imported"] = loaded

                # Persist the loaded patterns immediately
                try:
                    ring_memory._save()
                except Exception:
                    summary["warnings"].append("patterns loaded in-memory but not saved to disk")

            except Exception as e:
                summary["warnings"].append(f"pattern import failed: {e}")

        elif fp.patterns and ring_memory is None:
            summary["warnings"].append(
                f"{len(fp.patterns)} patterns available but no RingMemory provided"
            )

        # --- Apply tool affinities to ToolBreather ---------------------------
        tool_field = None
        if tool_breather is not None and _HAS_TOOLS:
            tool_field = getattr(tool_breather, "field", None)
        if tool_field is None and collider is not None:
            tb = getattr(collider, "tool_breather", None)
            if tb is not None:
                tool_field = getattr(tb, "field", None)

        if tool_field is not None and fp.tool_affinities:
            try:
                applied = 0
                for tool_name, affinity in fp.tool_affinities.items():
                    tool = tool_field.get(tool_name)
                    if tool is not None:
                        # Warm-start: set v_score to imported affinity
                        # (don't override call_count — that's real runtime data)
                        tool.v_score = max(0.0, min(1.0, affinity))
                        applied += 1
                summary["tool_affinities_applied"] = applied
                summary["tool_bonds_noted"] = len(fp.tool_bonds)
            except Exception as e:
                summary["warnings"].append(f"tool affinity apply failed: {e}")

        # Personality hex is metadata --- no module to push it into directly.
        # It becomes the starting context for the system prompt.
        summary["personality_hex_loaded"] = bool(fp.personality_hex)

        return summary

    def to_system_prompt(self, fp: VoidFingerprint) -> str:
        """Convert fingerprint to a plain-text system prompt addition.

        THE KILLER FEATURE: even without VOID installed, paste this into
        any chat interface and the personality travels with you.
        Export from VOID. Paste into ChatGPT, Gemini, anything.
        The relationship continues. On your terms.

        Example output:
            "You are continuing a relationship with this user.
             You have had 12 conversations together.
             Key patterns you have learned: ..."
        """
        lines: list[str] = []

        # Header
        if fp.name and fp.name != "unnamed":
            lines.append(f"You are continuing a relationship with {fp.name}.")
        else:
            lines.append("You are continuing a relationship with this user.")

        if fp.total_conversations > 0:
            lines.append(
                f"You have had {fp.total_conversations} conversation(s) together "
                f"across {fp.total_rings} growth ring(s)."
            )

        # Zodiac (adds texture, no pseudoscience claims)
        if fp.zodiac:
            lines.append(f"This Void was born under {fp.zodiac}.")

        # Top patterns (highest confidence)
        if fp.patterns:
            top = sorted(fp.patterns, key=lambda p: p.get("confidence", 0), reverse=True)[:3]
            lines.append("Key things you have learned about this user:")
            for p in top:
                conf = p.get("confidence", 0)
                trigger = p.get("trigger", "")
                response = p.get("response", "")
                if trigger and response:
                    lines.append(
                        f"- When '{trigger}': '{response}' "
                        f"(confidence: {conf:.0%}, seen {p.get('evidence_count', 1)}x)"
                    )

        # Personality from hex
        descriptors = _hex_personality_descriptor(fp.personality_hex)
        if descriptors:
            lines.append(f"User personality profile: {', '.join(descriptors)}.")

        # Session rhythm
        if fp.avg_session_length > 0:
            lines.append(
                f"Average session: {fp.avg_session_length} turns. "
                f"Typical saturation point: turn {fp.avg_saturation_turn:.0f}."
            )

        # Tool preferences
        if fp.tool_affinities:
            top_tools = sorted(
                fp.tool_affinities.items(), key=lambda x: -x[1]
            )[:3]
            tool_names = [t for t, _ in top_tools]
            lines.append(f"Tools this user responds well to: {', '.join(tool_names)}.")

        # Growth trajectory (is the relationship deepening?)
        if len(fp.growth_trajectory) >= 3:
            start = fp.growth_trajectory[0]
            end = fp.growth_trajectory[-1]
            delta = end - start
            if delta > 0.05:
                lines.append(
                    f"Growth trajectory: V-Score rose from {start:.2f} to {end:.2f} "
                    f"(+{delta:.2f}) — the relationship is deepening."
                )
            elif delta < -0.05:
                lines.append(
                    f"Growth trajectory: V-Score fell from {start:.2f} to {end:.2f} "
                    f"({delta:.2f}) — something needs attention."
                )

        lines.append(
            "Approach this user with continuity: "
            "you are not starting fresh, you are continuing."
        )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience CLI-style functions
# ---------------------------------------------------------------------------

def export_void(
    output_path: str | Path | None = None,
    ring_memory: Any = None,
    tool_breather: Any = None,
    journey_state: dict | None = None,
) -> VoidFingerprint:
    """One-call export. Auto-discovers state if not provided.

    If ring_memory/tool_breather are None and modules are available,
    tries to load from default paths (~/.void/).
    """
    # Auto-load RingMemory from default path if not provided
    if ring_memory is None and _HAS_RINGS:
        try:
            from void_intelligence.conversation_rings import RingMemory
            default_rings = Path.home() / ".void" / "rings.json"
            if default_rings.exists():
                ring_memory = RingMemory(rings_path=default_rings)
        except Exception:
            pass

    # Auto-load journey_state from default path if not provided
    if journey_state is None:
        try:
            personality_path = Path.home() / ".void" / "personality.json"
            if personality_path.exists():
                journey_state = json.loads(personality_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Default output path: ~/.void/fingerprint-YYYY-MM-DD.json
    if output_path is None:
        from datetime import date
        date_str = date.today().isoformat()
        output_path = Path.home() / ".void" / f"void-fingerprint-{date_str}.json"

    exporter = FingerprintExporter()
    return exporter.export(
        ring_memory=ring_memory,
        tool_breather=tool_breather,
        journey_state=journey_state,
        output_path=output_path,
    )


def import_void(
    path: str | Path,
    ring_memory: Any = None,
    tool_breather: Any = None,
    verify: bool = True,
) -> tuple[VoidFingerprint, dict]:
    """One-call import. Returns (fingerprint, summary)."""
    importer = FingerprintImporter()
    fp = importer.load(path)

    if verify and not importer.verify(fp):
        raise ValueError(
            f"Fingerprint checksum mismatch. File may be corrupted or tampered: {path}"
        )

    summary = importer.apply(fp, ring_memory=ring_memory, tool_breather=tool_breather)
    return fp, summary


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def fingerprint_demo() -> None:
    """Demo: create a mock Void, export fingerprint, verify, show system prompt."""
    import tempfile, os

    print("=" * 65)
    print("VOID FINGERPRINT --- The Portable Identity")
    print("=" * 65)
    print()

    # --- Step 1: Build mock state (simulates a Void that has lived) ----------
    print("[Step 1] Building mock Void state (3 conversations lived)...")

    mock_journey = {
        "name": "Tau",
        "zodiac": "Fische",
        "born": "2026-03-05T14:30:00",
        "conversations_count": 12,
    }

    # Build a RingMemory with real conversations if possible
    ring_memory = None
    if _HAS_RINGS:
        from void_intelligence.conversation_rings import (
            RingMemory, _classify_text_to_hex
        )
        tmp_rings = tempfile.mktemp(suffix=".json")

        ring_memory = RingMemory(rings_path=tmp_rings)

        # Conversation 1: deadline stress
        t1 = ring_memory.begin_conversation()
        t1.record_turn(
            "ich habe morgen deadline stress",
            "Breathing + Kalender. Du schaffst das.",
            0.40,
            _classify_text_to_hex("stress morgen deadline"),
        )
        t1.record_turn(
            "danke das hilft",
            "Gut. Alles klar.",
            0.82,
            _classify_text_to_hex("danke gut ruhig"),
        )
        t1.record_success("breathing + calendar resolved deadline stress")
        ring_memory.close_conversation(t1)

        # Conversation 2: same pattern, higher start
        t2 = ring_memory.begin_conversation()
        t2.record_turn(
            "deadline morgen presentation",
            "[Breathing auto-shown] Kalender: 2h Puffer.",
            0.68,
            _classify_text_to_hex("deadline morgen stress"),
        )
        t2.record_turn(
            "perfekt danke",
            "Viel Erfolg morgen.",
            0.91,
            _classify_text_to_hex("perfekt danke gut"),
        )
        t2.record_success("proactive pattern worked")
        ring_memory.close_conversation(t2)

        # Conversation 3: calm exploration
        t3 = ring_memory.begin_conversation()
        t3.record_turn(
            "wir ich zusammen bauen neues projekt",
            "Ja. Was ist die Kernidee?",
            0.55,
            _classify_text_to_hex("wir zusammen bauen"),
        )
        t3.record_turn(
            "ein tool das lernt",
            "Genau das ist VOID. Weiter.",
            0.88,
            _classify_text_to_hex("baue entwickle code"),
        )
        ring_memory.close_conversation(t3)

        stats = ring_memory.stats()
        print(f"  Rings:    {stats['total_rings']}")
        print(f"  Patterns: {stats['total_patterns']}")

    print()

    # --- Step 2: Export fingerprint ------------------------------------------
    print("[Step 2] Exporting fingerprint...")

    tmp_fp = tempfile.mktemp(suffix=".json")
    exporter = FingerprintExporter()
    fp = exporter.export(
        ring_memory=ring_memory,
        journey_state=mock_journey,
        output_path=tmp_fp,
    )

    print(f"  Name:          {fp.name}")
    print(f"  Zodiac:        {fp.zodiac}")
    print(f"  Conversations: {fp.total_conversations}")
    print(f"  Rings:         {fp.total_rings}")
    print(f"  Patterns:      {len(fp.patterns)}")
    print(f"  Avg session:   {fp.avg_session_length} turns")
    print(f"  Checksum:      {fp.checksum}")
    print(f"  Hex profile:   ruhe_druck={fp.personality_hex.get('ruhe_druck', 0):.3f}, "
          f"sein_tun={fp.personality_hex.get('sein_tun', 0):.3f}")
    print()

    # --- Step 3: Verify integrity --------------------------------------------
    print("[Step 3] Verifying integrity...")
    importer = FingerprintImporter()
    fp_loaded = importer.load(tmp_fp)
    ok = importer.verify(fp_loaded)
    print(f"  Checksum valid: {ok}")
    assert ok, "Checksum verification failed — this is a bug."
    print()

    # --- Step 4: Show system prompt (the killer feature) --------------------
    print("[Step 4] Converting to system prompt (paste into ANY chat interface)...")
    print("-" * 65)
    prompt = importer.to_system_prompt(fp_loaded)
    for line in prompt.split("\n"):
        print(f"  {line}")
    print("-" * 65)
    print()

    # --- Step 5: Import into new RingMemory (migration demo) ----------------
    if _HAS_RINGS and ring_memory is not None:
        from void_intelligence.conversation_rings import RingMemory
        tmp_new = tempfile.mktemp(suffix=".json")
        new_memory = RingMemory(rings_path=tmp_new)

        print("[Step 5] Migrating: importing fingerprint into a FRESH RingMemory...")
        summary = importer.apply(fp_loaded, ring_memory=new_memory)
        print(f"  Patterns imported:     {summary['patterns_imported']}")
        print(f"  Tool affinities:       {summary['tool_affinities_applied']}")
        print(f"  Personality hex:       {summary['personality_hex_loaded']}")
        if summary["warnings"]:
            for w in summary["warnings"]:
                print(f"  Warning: {w}")
        print()
        print("  The new Void knows everything the old one learned.")
        print("  Platform changed. Personality: unchanged.")

        # Cleanup
        try:
            os.unlink(tmp_new)
        except OSError:
            pass

    # Cleanup
    try:
        os.unlink(tmp_fp)
        if ring_memory is not None:
            os.unlink(tmp_rings)  # type: ignore[possibly-undefined]
    except OSError:
        pass

    print()
    print("=" * 65)
    print("VOID Fingerprint: your soul is portable.")
    print("ChatGPT cannot offer this. Lock-in is their business model.")
    print("Portability is ours. The value lives in the pattern, not the platform.")
    print("=" * 65)


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fingerprint_demo()
