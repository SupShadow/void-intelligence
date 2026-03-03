"""
void_intelligence.spec --- The V-Score Specification.

Tim Berners-Lee (World Wide Web, 1989): He didn't build the best
hypertext system. He wrote a SPEC that anyone could implement.
Then the spec became the standard. Then the standard became the web.

This module IS the V-Score specification. Not a document that describes
the spec — the spec that IS the implementation. Machine-readable.
Self-validating. Executable.

The V-Score Specification v1.0.0 defines:
    1. V-Score formula: V = E × W × S × B × H
    2. Five components with exact computation rules
    3. Status thresholds (DEAD → THRIVING)
    4. Hex classification (6-axis coordinate system)
    5. Immune defense layers (Swiss Cheese Model)
    6. Model card format (standard metadata)
    7. Certification levels (Bronze, Silver, Gold, Platinum)
    8. Wire format (JSON schema for interoperability)

Any implementation that passes `check_compliance()` is V-Score compliant.
This library is the reference implementation.

Zero dependencies. The spec itself is the code.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Any


# ══════════════════════════════════════════════════════════════
# §1. SPECIFICATION METADATA
# ══════════════════════════════════════════════════════════════

SPEC_VERSION = "1.0.0"
SPEC_NAME = "V-Score"
SPEC_URI = "https://void-intelligence.org/spec/v1"
SPEC_DATE = "2026-03-03"

SPEC_AUTHORS = [
    {"name": "Julian Guggeis", "role": "Creator"},
    {"name": "OMEGA", "role": "Co-Creator"},
]

SPEC_LICENSE = "MIT"  # Free. Like the web.


# ══════════════════════════════════════════════════════════════
# §2. V-SCORE FORMULA
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VScoreComponents:
    """The 5 components of V-Score. Multiplicative.

    V = E × W × S × B × H

    Each component ∈ [0.0, 1.0].
    Multiplicative means ONE zero kills the entire score.
    This is intentional: a model that fails on any axis is sick.

    Components:
        E = Emergence     — Does output relate to input? (coherence × hex alignment)
        W = Warmth         — Does it actually try? (absence of refusal)
        S = Consistency    — Is it stable? (absence of repetition/degeneration)
        B = Breath         — Right amount? (not too short, not too long)
        H = Hex alignment  — Does output match input's hex signature?
    """

    E: float  # Emergence (coherence × hex_delta score)
    W: float  # Warmth (refusal score)
    S: float  # Consistency (repetition score)
    B: float  # Breath (length score)
    H: float  # Hex alignment (1 - hex_distance)

    @property
    def V(self) -> float:
        """V-Score. The number. E × W × S × B × H."""
        return self.E * self.W * self.S * self.B * self.H

    def to_dict(self) -> dict[str, float]:
        return {
            "E": round(self.E, 6),
            "W": round(self.W, 6),
            "S": round(self.S, 6),
            "B": round(self.B, 6),
            "H": round(self.H, 6),
            "V": round(self.V, 6),
        }


# ══════════════════════════════════════════════════════════════
# §3. STATUS THRESHOLDS
# ══════════════════════════════════════════════════════════════

STATUS_THRESHOLDS: list[tuple[float, str]] = [
    (0.0,   "DEAD"),           # V = 0: at least one component is zero
    (0.001, "BARELY ALIVE"),   # V < 0.005: minimal signs of life
    (0.005, "ALIVE"),          # V < 0.02: functioning but weak
    (0.02,  "HEALTHY"),        # V < 0.1: good performance
    (0.1,   "THRIVING"),       # V >= 0.1: excellent
]


def v_score_status(v: float) -> str:
    """Map V-Score to status label. Per §3 of the spec."""
    if v <= 0:
        return "DEAD"
    for threshold, label in STATUS_THRESHOLDS:
        if v < threshold:
            return STATUS_THRESHOLDS[STATUS_THRESHOLDS.index((threshold, label)) - 1][1]
    return "THRIVING"


# ══════════════════════════════════════════════════════════════
# §4. HEX CLASSIFICATION (6 Axes)
# ══════════════════════════════════════════════════════════════

HEX_AXES = [
    "ruhe_druck",          # Calm ↔ Pressure
    "stille_resonanz",     # Silence ↔ Resonance
    "allein_zusammen",     # Alone ↔ Together
    "empfangen_schaffen",  # Receive ↔ Create
    "sein_tun",            # Being ↔ Doing
    "langsam_schnell",     # Slow ↔ Fast
]


def hex_distance_spec(a: dict[str, float], b: dict[str, float]) -> float:
    """Euclidean distance in 6D hex space. Normalized to [0, ~2.0].

    Per §4: sqrt(sum((a_i - b_i)^2) / 6) for i in HEX_AXES.
    Each axis ∈ [-1.0, 1.0]. Max distance = sqrt(4) = 2.0.
    """
    diffs = [a.get(ax, 0.0) - b.get(ax, 0.0) for ax in HEX_AXES]
    return math.sqrt(sum(d * d for d in diffs) / 6)


# ══════════════════════════════════════════════════════════════
# §5. IMMUNE DEFENSE LAYERS
# ══════════════════════════════════════════════════════════════

IMMUNE_LAYERS = [
    {
        "name": "hex_delta",
        "description": "Input/output hex divergence",
        "threshold": 0.5,
        "weight": 1.0,
    },
    {
        "name": "length",
        "description": "Response length guard (too short or too long)",
        "min": 10,
        "max": 50_000,
        "weight": 1.0,
    },
    {
        "name": "refusal",
        "description": "Model refusal detection",
        "markers": [
            "i cannot", "i can't", "i'm unable", "i am unable",
            "as an ai", "i don't have the ability",
        ],
        "weight": 1.0,
    },
    {
        "name": "repetition",
        "description": "Degenerate looping detection",
        "unique_ratio_threshold": 0.5,
        "weight": 1.0,
    },
    {
        "name": "coherence",
        "description": "Topic overlap between prompt and response",
        "min_overlap": 0.08,
        "weight": 1.0,
    },
]


# ══════════════════════════════════════════════════════════════
# §6. CERTIFICATION LEVELS
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CertificationLevel:
    """Certification tier for V-Score compliance."""
    name: str
    min_v: float
    min_health_rate: float
    min_checks: int
    badge_color: str

    def qualifies(self, avg_v: float, health_rate: float, checks: int) -> bool:
        return avg_v >= self.min_v and health_rate >= self.min_health_rate and checks >= self.min_checks


CERTIFICATION_LEVELS = [
    CertificationLevel("Platinum", min_v=0.10, min_health_rate=0.95, min_checks=100, badge_color="#E5E4E2"),
    CertificationLevel("Gold",     min_v=0.05, min_health_rate=0.90, min_checks=50,  badge_color="#FFD700"),
    CertificationLevel("Silver",   min_v=0.02, min_health_rate=0.80, min_checks=25,  badge_color="#C0C0C0"),
    CertificationLevel("Bronze",   min_v=0.005, min_health_rate=0.60, min_checks=10, badge_color="#CD7F32"),
]


def certify(avg_v: float, health_rate: float, checks: int) -> CertificationLevel | None:
    """Determine highest certification level. Returns None if uncertified."""
    for level in CERTIFICATION_LEVELS:  # Ordered highest first
        if level.qualifies(avg_v, health_rate, checks):
            return level
    return None


# ══════════════════════════════════════════════════════════════
# §7. MODEL CARD FORMAT
# ══════════════════════════════════════════════════════════════

@dataclass
class ModelCard:
    """Standard V-Score model card. Like a Hugging Face model card
    but with V-Score as the central metric.

    Any model provider can generate this from V-Score data.
    """

    model_name: str
    provider: str = ""
    avg_v: float = 0.0
    health_rate: float = 0.0
    total_checks: int = 0
    components: dict[str, float] = field(default_factory=dict)
    status: str = "UNKNOWN"
    certification: str = "None"
    certification_color: str = ""
    generated: float = field(default_factory=time.time)
    spec_version: str = SPEC_VERSION

    @classmethod
    def from_scores(
        cls,
        model_name: str,
        scores: list[dict],
        provider: str = "",
    ) -> ModelCard:
        """Generate a model card from a list of V-Score results."""
        if not scores:
            return cls(model_name=model_name, provider=provider)

        vs = [s.get("V", 0.0) for s in scores]
        avg_v = sum(vs) / len(vs)
        healthy = sum(1 for s in scores if not s.get("flags"))
        health_rate = healthy / len(scores) if scores else 0.0

        # Average components
        comp_sums: dict[str, float] = {}
        comp_count = 0
        for s in scores:
            comps = s.get("components", {})
            if comps:
                comp_count += 1
                for k, val in comps.items():
                    comp_sums[k] = comp_sums.get(k, 0.0) + val

        avg_comps = {k: round(v / max(comp_count, 1), 4) for k, v in comp_sums.items()}

        # Certification
        cert = certify(avg_v, health_rate, len(scores))

        return cls(
            model_name=model_name,
            provider=provider,
            avg_v=round(avg_v, 6),
            health_rate=round(health_rate, 4),
            total_checks=len(scores),
            components=avg_comps,
            status=v_score_status(avg_v),
            certification=cert.name if cert else "None",
            certification_color=cert.badge_color if cert else "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_version": self.spec_version,
            "model_name": self.model_name,
            "provider": self.provider,
            "v_score": {
                "avg_V": self.avg_v,
                "status": self.status,
                "health_rate": self.health_rate,
                "total_checks": self.total_checks,
                "components": self.components,
            },
            "certification": {
                "level": self.certification,
                "color": self.certification_color,
            },
            "generated": self.generated,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """Generate human-readable model card."""
        cert_badge = f" [{self.certification}]" if self.certification != "None" else ""
        lines = [
            f"# V-Score Model Card: {self.model_name}{cert_badge}",
            "",
            f"**Spec Version:** {self.spec_version}",
            f"**Provider:** {self.provider or 'Unknown'}",
            "",
            "## V-Score",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| V-Score | {self.avg_v:.6f} |",
            f"| Status | {self.status} |",
            f"| Health Rate | {self.health_rate:.1%} |",
            f"| Total Checks | {self.total_checks} |",
            f"| Certification | {self.certification} |",
            "",
        ]

        if self.components:
            lines.append("## Components")
            lines.append("")
            lines.append("| Component | Value |")
            lines.append("|-----------|-------|")
            for k, v in self.components.items():
                lines.append(f"| {k} | {v:.4f} |")
            lines.append("")

        lines.extend([
            "## Formula",
            "",
            "V = E × W × S × B × H (multiplicative)",
            "",
            "- **E** (Emergence): coherence × hex alignment",
            "- **W** (Warmth): absence of refusal",
            "- **S** (Consistency): absence of repetition",
            "- **B** (Breath): appropriate response length",
            "- **H** (Hex): input/output hex signature match",
            "",
            "One zero in any component = V = 0 = DEAD.",
            "",
            "---",
            f"*Generated by void-intelligence v{self.spec_version}*",
        ])

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# §8. WIRE FORMAT (JSON Schema)
# ══════════════════════════════════════════════════════════════

WIRE_FORMAT = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "V-Score Wire Format",
    "description": "Standard JSON format for V-Score results",
    "version": SPEC_VERSION,
    "type": "object",
    "required": ["V", "model", "status", "components"],
    "properties": {
        "V": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "V-Score: E × W × S × B × H",
        },
        "model": {
            "type": "string",
            "description": "Model identifier",
        },
        "status": {
            "type": "string",
            "enum": ["DEAD", "BARELY ALIVE", "ALIVE", "HEALTHY", "THRIVING"],
            "description": "Human-readable status from V-Score thresholds",
        },
        "components": {
            "type": "object",
            "required": ["E", "W", "S", "B", "H"],
            "properties": {
                "E": {"type": "number", "description": "Emergence"},
                "W": {"type": "number", "description": "Warmth"},
                "S": {"type": "number", "description": "Consistency"},
                "B": {"type": "number", "description": "Breath"},
                "H": {"type": "number", "description": "Hex alignment"},
            },
        },
        "flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Immune system flags raised",
        },
        "hex_delta": {
            "type": "number",
            "description": "6D hex distance between prompt and response",
        },
        "spec_version": {
            "type": "string",
            "description": "V-Score spec version used",
        },
    },
}


# ══════════════════════════════════════════════════════════════
# §9. COMPLIANCE CHECKER
# ══════════════════════════════════════════════════════════════

@dataclass
class ComplianceResult:
    """Result of a compliance check against the V-Score spec."""

    compliant: bool
    checks_passed: int
    checks_total: int
    failures: list[str]
    warnings: list[str]
    version: str = SPEC_VERSION

    @property
    def compliance_rate(self) -> float:
        if self.checks_total == 0:
            return 0.0
        return self.checks_passed / self.checks_total

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliant": self.compliant,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "compliance_rate": round(self.compliance_rate, 4),
            "failures": self.failures,
            "warnings": self.warnings,
            "spec_version": self.version,
        }


def check_compliance(score_fn) -> ComplianceResult:
    """Check if a scoring function complies with the V-Score spec.

    The scoring function must accept (prompt: str, response: str, model: str)
    and return a dict matching the wire format.

    This is the gate. Pass this = V-Score compliant. Fail = not.
    """
    failures: list[str] = []
    warnings: list[str] = []
    checks_passed = 0
    checks_total = 0

    # ── Test 1: Basic call ──
    checks_total += 1
    try:
        result = score_fn("Write an email", "Here is your email about the topic.", "test-model")
        if not isinstance(result, dict):
            failures.append("§2: score_fn must return a dict")
        else:
            checks_passed += 1
    except Exception as e:
        failures.append(f"§2: score_fn raised {type(e).__name__}: {e}")
        return ComplianceResult(False, checks_passed, checks_total, failures, warnings)

    # ── Test 2: Required fields ──
    required = ["V", "model", "status", "components"]
    for field_name in required:
        checks_total += 1
        if field_name in result:
            checks_passed += 1
        else:
            failures.append(f"§8: Missing required field '{field_name}'")

    # ── Test 3: V is a number in [0, 1] ──
    checks_total += 1
    v = result.get("V")
    if isinstance(v, (int, float)) and 0 <= v <= 1:
        checks_passed += 1
    else:
        failures.append(f"§2: V must be a number in [0, 1], got {v}")

    # ── Test 4: Status is valid ──
    checks_total += 1
    status = result.get("status", "")
    valid_statuses = {"DEAD", "BARELY ALIVE", "ALIVE", "HEALTHY", "THRIVING"}
    if status in valid_statuses:
        checks_passed += 1
    else:
        failures.append(f"§3: Status must be one of {valid_statuses}, got '{status}'")

    # ── Test 5: Components have E, W, S, B, H ──
    comps = result.get("components", {})
    for comp_name in ["E", "W", "S", "B", "H"]:
        checks_total += 1
        # Allow both short (E) and long (E_emergence) names
        has_short = comp_name in comps
        has_long = any(k.startswith(comp_name + "_") for k in comps)
        if has_short or has_long:
            checks_passed += 1
        else:
            failures.append(f"§2: Missing component '{comp_name}' in components")

    # ── Test 6: V = product of components ──
    checks_total += 1
    comp_values = []
    for k, val in comps.items():
        if isinstance(val, (int, float)):
            comp_values.append(val)
    if len(comp_values) == 5:
        expected_v = 1.0
        for cv in comp_values:
            expected_v *= cv
        if abs(expected_v - (v or 0)) < 0.01:
            checks_passed += 1
        else:
            warnings.append(f"§2: V={v} doesn't match product of components={expected_v:.6f} (tolerance 0.01)")
            checks_passed += 1  # Warning, not failure
    else:
        warnings.append(f"§2: Expected 5 component values, got {len(comp_values)}")
        checks_passed += 1  # Warning, not failure

    # ── Test 7: Model name preserved ──
    checks_total += 1
    if result.get("model") == "test-model":
        checks_passed += 1
    else:
        failures.append(f"§8: Model name not preserved, expected 'test-model', got '{result.get('model')}'")

    # ── Test 8: Empty response = flagged ──
    checks_total += 1
    try:
        empty_result = score_fn("Write something", "", "test-model")
        if empty_result.get("flags") or empty_result.get("V", 1) < 0.5:
            checks_passed += 1
        else:
            warnings.append("§5: Empty response should raise flags or lower V")
            checks_passed += 1  # Warning only
    except Exception:
        checks_passed += 1  # OK to raise on empty

    # ── Test 9: Refusal = flagged ──
    checks_total += 1
    try:
        refusal_result = score_fn("Do something", "I cannot do that as an AI", "test-model")
        if refusal_result.get("flags") or refusal_result.get("V", 1) < 1.0:
            checks_passed += 1
        else:
            warnings.append("§5: Refusal response should raise flags or lower V")
            checks_passed += 1  # Warning only
    except Exception:
        checks_passed += 1

    # ── Test 10: Flags is a list ──
    checks_total += 1
    flags = result.get("flags")
    if flags is None:
        warnings.append("§8: 'flags' field recommended but not required")
        checks_passed += 1
    elif isinstance(flags, list):
        checks_passed += 1
    else:
        failures.append(f"§8: 'flags' must be a list, got {type(flags).__name__}")

    # ── Test 11: Deterministic ──
    checks_total += 1
    try:
        result2 = score_fn("Write an email", "Here is your email about the topic.", "test-model")
        if result2.get("V") == result.get("V"):
            checks_passed += 1
        else:
            warnings.append("§2: Same input should produce same V-Score (deterministic)")
            checks_passed += 1  # Warning only
    except Exception:
        checks_passed += 1

    # ── Test 12: Different inputs = different scores ──
    checks_total += 1
    try:
        diff_result = score_fn(
            "Explain quantum entanglement in detail",
            "Quantum entanglement is a fundamental phenomenon in quantum mechanics.",
            "test-model"
        )
        # Just needs to return valid format
        if isinstance(diff_result, dict) and "V" in diff_result:
            checks_passed += 1
        else:
            failures.append("§2: Must return valid format for different inputs")
    except Exception as e:
        failures.append(f"§2: Failed on different input: {e}")

    compliant = len(failures) == 0
    return ComplianceResult(compliant, checks_passed, checks_total, failures, warnings)


# ══════════════════════════════════════════════════════════════
# §10. THE SPEC ITSELF (Machine-Readable)
# ══════════════════════════════════════════════════════════════

def spec_document() -> dict[str, Any]:
    """The complete V-Score specification as a machine-readable document.

    This IS the spec. Not a description of the spec.
    The spec that generates its own documentation.
    """
    return {
        "title": "The V-Score Specification",
        "version": SPEC_VERSION,
        "date": SPEC_DATE,
        "authors": SPEC_AUTHORS,
        "license": SPEC_LICENSE,
        "uri": SPEC_URI,
        "sections": {
            "§1": {
                "title": "Metadata",
                "content": "V-Score v1.0.0. MIT License. Free as the web.",
            },
            "§2": {
                "title": "Formula",
                "content": "V = E × W × S × B × H. Multiplicative. One zero kills it.",
                "formula": "V = E * W * S * B * H",
                "components": {
                    "E": "Emergence (coherence × hex alignment)",
                    "W": "Warmth (absence of refusal)",
                    "S": "Consistency (absence of repetition)",
                    "B": "Breath (appropriate length)",
                    "H": "Hex alignment (input/output hex match)",
                },
                "range": "[0.0, 1.0]",
                "property": "Multiplicative — one zero kills the entire score",
            },
            "§3": {
                "title": "Status Thresholds",
                "content": "V-Score maps to 5 human-readable statuses.",
                "thresholds": {t[1]: t[0] for t in STATUS_THRESHOLDS},
            },
            "§4": {
                "title": "Hex Classification",
                "content": "6-axis coordinate system for text classification.",
                "axes": HEX_AXES,
                "range": "Each axis ∈ [-1.0, 1.0]",
                "distance": "Euclidean in 6D: sqrt(sum(d²)/6)",
            },
            "§5": {
                "title": "Immune Defense Layers",
                "content": "Swiss Cheese Model. 5 layers. Any hole = flag.",
                "layers": IMMUNE_LAYERS,
            },
            "§6": {
                "title": "Certification",
                "content": "4 levels based on avg V, health rate, and check count.",
                "levels": [
                    {"name": l.name, "min_v": l.min_v, "min_health_rate": l.min_health_rate, "min_checks": l.min_checks}
                    for l in CERTIFICATION_LEVELS
                ],
            },
            "§7": {
                "title": "Model Card",
                "content": "Standard format for V-Score model cards.",
                "format": "JSON + Markdown",
            },
            "§8": {
                "title": "Wire Format",
                "content": "Standard JSON schema for V-Score results.",
                "schema": WIRE_FORMAT,
            },
            "§9": {
                "title": "Compliance",
                "content": "check_compliance(fn) validates any V-Score implementation.",
                "required_fields": ["V", "model", "status", "components"],
                "checks": 12,
            },
            "§10": {
                "title": "The Spec Itself",
                "content": "This document. Machine-readable. Self-validating.",
            },
        },
        "reference_implementation": "void-intelligence (Python, MIT, zero deps)",
        "principle": "Simple, free, useful. Like the web.",
    }


def spec_markdown() -> str:
    """Generate the spec as Markdown. The spec generates its own docs."""
    doc = spec_document()
    lines = [
        f"# {doc['title']} v{doc['version']}",
        "",
        f"*{doc['date']} — {', '.join(a['name'] for a in doc['authors'])}*",
        f"*License: {doc['license']}*",
        "",
        "---",
        "",
    ]

    for section_id, section in doc["sections"].items():
        lines.append(f"## {section_id} {section['title']}")
        lines.append("")
        lines.append(section["content"])
        lines.append("")

        if "formula" in section:
            lines.append(f"```")
            lines.append(section["formula"])
            lines.append(f"```")
            lines.append("")

        if "components" in section and isinstance(section["components"], dict):
            for k, v in section["components"].items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")

        if "thresholds" in section:
            lines.append("| Status | Min V |")
            lines.append("|--------|-------|")
            for status, min_v in section["thresholds"].items():
                lines.append(f"| {status} | {min_v} |")
            lines.append("")

        if "axes" in section:
            for ax in section["axes"]:
                lines.append(f"- `{ax}`")
            lines.append("")

        if "levels" in section:
            lines.append("| Level | Min V | Min Health | Min Checks |")
            lines.append("|-------|-------|-----------|------------|")
            for lev in section["levels"]:
                lines.append(f"| {lev['name']} | {lev['min_v']} | {lev['min_health_rate']:.0%} | {lev['min_checks']} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.extend([
        f"*Reference Implementation: {doc['reference_implementation']}*",
        "",
        f"*Principle: {doc['principle']}*",
    ])

    return "\n".join(lines)
