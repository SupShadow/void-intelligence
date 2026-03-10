"""
void_intelligence.prescribe --- The Prescriptive Sphere.

SELEN sees.  Dekagon understands.  Prescribe ACTS.

This is the birth that closes the loop:

    SELEN   = What IS?          (detection, description)
    Dekagon = What does it MEAN? (10 lenses, 45 triangles)
    Prescribe = What do you DO?  (3 actions, Rule of Three)

The Prescriptive Sphere takes ANY set of signals (health data, business
metrics, relationship frequencies, energy levels) and produces:

    1 Sphere    = complete perception from 10 angles
    3 Actions   = TUN / LASSEN / WARTEN (do / stop / wait)

The Rule of Three is structural:
    Every Triangle has: 1 visible + 2 voids
    The 2 voids ARE the prescription:
        Void 1 = What you MUST do (TUN)
        Void 2 = What you must STOP (LASSEN)
    The visible = What you're already doing (WARTEN/continue)

Geometry:
    SELEN detects features → zones (floor, rim, exterior)
    Dekagon perceives meaning → triangles (visible + 2 voids)
    Prescribe tessellates → sphere → TOP 3 actions

    Input:  dict of named signals (any domain)
    Output: Prescription (3 actions + paradox + sphere)

Usage:
    from void_intelligence.prescribe import prescribe, Prescription

    rx = prescribe({
        "sleep_hours": [7, 6, 5, 4, 3, 4, 5],
        "cashflow_daily": [120, 80, 40, 20, -10, -30, 15],
        "messages_annika": [3, 2, 1, 0, 0, 0, 0],
        "energy_self_report": [8, 7, 5, 3, 2, 3, 4],
        "plaud_count_daily": [5, 8, 12, 15, 18, 14, 10],
    })

    print(rx.tun)       # What to DO
    print(rx.lassen)    # What to STOP
    print(rx.warten)    # What to CONTINUE
    print(rx.paradox)   # The central tension
    print(rx.veto)      # True if VETO triggered
    print(rx.sphere)    # Full 10-lens perception

CLI:
    python3 -m void_intelligence.prescribe --signals data/health/burnout-score.json
    python3 -m void_intelligence.prescribe --julian  # auto-load Julian's signals

Zero external dependencies. Pure Python. Pure math. Pure care.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from void_intelligence.selen import see as selen_see
from void_intelligence.dekagon import Dekagon, Sphere


# ── SELEN Zone Classification ──────────────────────────────────────

@dataclass
class SignalDiagnosis:
    """One signal seen through SELEN's eyes."""
    name: str
    values: list[float]
    trend: str  # "rising", "falling", "stable", "volatile"
    zone: str  # "feature" (crisis), "transition" (changing), "exterior" (normal)
    severity: float  # 0.0 = fine, 1.0 = critical
    detections: list[dict] = field(default_factory=list)
    last_value: float = 0.0
    mean_value: float = 0.0
    description: str = ""


def _diagnose_signal(name: str, values: list[float]) -> SignalDiagnosis:
    """Run SELEN on a single signal and classify it."""
    if not values or len(values) < 3:
        return SignalDiagnosis(
            name=name, values=values, trend="unknown",
            zone="exterior", severity=0.0,
            description=f"{name}: insufficient data"
        )

    # Basic stats
    n = len(values)
    last = values[-1]
    mean = sum(values) / n
    recent = values[-min(3, n):]
    recent_mean = sum(recent) / len(recent)

    # Trend detection
    if n >= 3:
        first_half = values[:n // 2]
        second_half = values[n // 2:]
        fh_mean = sum(first_half) / len(first_half)
        sh_mean = sum(second_half) / len(second_half)
        delta = sh_mean - fh_mean
        spread = max(values) - min(values)
        if spread > 0:
            rel_delta = delta / spread
        else:
            rel_delta = 0.0

        if rel_delta > 0.15:
            trend = "rising"
        elif rel_delta < -0.15:
            trend = "falling"
        else:
            # Check volatility
            diffs = [abs(values[i] - values[i - 1]) for i in range(1, n)]
            avg_diff = sum(diffs) / len(diffs)
            if spread > 0 and avg_diff / spread > 0.3:
                trend = "volatile"
            else:
                trend = "stable"
    else:
        trend = "unknown"

    # SELEN feature detection
    detections = selen_see(values, threshold=0.3) if n >= 10 else []

    # Zone classification based on SELEN + heuristics
    has_features = len(detections) > 0
    max_score = max((d["score"] for d in detections), default=0.0)

    # Signal-specific severity (domain-aware heuristics)
    severity = 0.0
    name_lower = name.lower()

    # Sleep: low is bad
    if any(w in name_lower for w in ("sleep", "schlaf")):
        if last < 5:
            severity = min(1.0, (5 - last) / 3)
        if trend == "falling":
            severity = min(1.0, severity + 0.2)

    # Burnout/stress: high is bad
    elif any(w in name_lower for w in ("burnout", "stress", "erschoepf")):
        if last > 60:
            severity = min(1.0, (last - 60) / 40)
        if trend == "rising":
            severity = min(1.0, severity + 0.3)

    # Energy: low is bad
    elif any(w in name_lower for w in ("energy", "energie")):
        if mean > 0 and last < mean * 0.5:
            severity = min(1.0, (mean - last) / mean)
        if trend == "falling":
            severity = min(1.0, severity + 0.2)

    # Cashflow/money: negative is bad
    elif any(w in name_lower for w in ("cash", "geld", "revenue", "umsatz")):
        if last < 0:
            severity = min(1.0, abs(last) / max(abs(mean), 1))
        if trend == "falling":
            severity = min(1.0, severity + 0.3)

    # Messages/contact: dropping to zero is concerning
    elif any(w in name_lower for w in ("message", "nachricht", "contact", "kontakt")):
        if last == 0 and mean > 0:
            severity = min(1.0, 0.5 + (mean - last) / max(mean, 1) * 0.3)
        if trend == "falling":
            severity = min(1.0, severity + 0.2)

    # Plauds/work: too many late = overwork
    elif any(w in name_lower for w in ("plaud", "work", "arbeit")):
        if last > 15:
            severity = min(1.0, (last - 10) / 15)
        if trend == "rising":
            severity = min(1.0, severity + 0.2)

    # Generic: use SELEN score
    else:
        severity = max_score * 0.5 if has_features else 0.0
        if trend == "falling":
            severity = min(1.0, severity + 0.15)

    # Zone from severity
    if severity >= 0.6:
        zone = "feature"  # Crisis zone
    elif severity >= 0.3:
        zone = "transition"  # Changing, needs attention
    else:
        zone = "exterior"  # Normal, stable

    # Human description
    desc = f"{name}: {trend}"
    if zone == "feature":
        desc += f" [CRITICAL severity={severity:.1f}]"
    elif zone == "transition":
        desc += f" [attention severity={severity:.1f}]"

    return SignalDiagnosis(
        name=name, values=values, trend=trend, zone=zone,
        severity=severity, detections=detections,
        last_value=last, mean_value=mean, description=desc,
    )


# ── Prescription ────────────────────────────────────────────────────

@dataclass
class Action:
    """One prescribed action."""
    verb: str  # "TUN", "LASSEN", "WARTEN"
    text: str
    lens: str  # Which Bewusstsein generated this
    severity: float
    signal: str  # Which signal triggered this

    def __str__(self) -> str:
        icon = {"TUN": "+", "LASSEN": "-", "WARTEN": "~"}
        return f"  [{icon.get(self.verb, '?')}] {self.verb}: {self.text} ({self.lens}, severity={self.severity:.1f})"


@dataclass
class Prescription:
    """The complete prescription. SELEN x Dekagon x Pipeline = ACTS."""
    timestamp: float = field(default_factory=time.time)
    diagnoses: list[SignalDiagnosis] = field(default_factory=list)
    sphere: Sphere | None = None

    # The Rule of Three output
    tun: list[Action] = field(default_factory=list)      # What to DO
    lassen: list[Action] = field(default_factory=list)    # What to STOP
    warten: list[Action] = field(default_factory=list)    # What to CONTINUE

    paradox: str = ""
    veto: bool = False
    veto_reason: str = ""

    def top3(self) -> list[Action]:
        """The 3 most important actions across all categories."""
        all_actions = sorted(
            self.tun + self.lassen,
            key=lambda a: a.severity,
            reverse=True,
        )
        return all_actions[:3]

    def render(self, verbose: bool = False) -> str:
        """Human-readable prescription."""
        lines = []
        lines.append("=" * 60)
        lines.append("PRESCRIPTIVE SPHERE")
        lines.append("=" * 60)

        if self.veto:
            lines.append(f"\n!! VETO: {self.veto_reason}")
            lines.append("   Alles andere ist nachrangig.\n")

        # Signal overview
        lines.append(f"\nSIGNALS ({len(self.diagnoses)}):")
        for d in sorted(self.diagnoses, key=lambda x: x.severity, reverse=True):
            icon = {"feature": "!!", "transition": " >", "exterior": "  "}
            lines.append(f"  {icon.get(d.zone, '  ')} {d.description}")

        # Paradox
        if self.paradox:
            lines.append(f"\nPARADOX: {self.paradox}")

        # TOP 3
        top = self.top3()
        if top:
            lines.append(f"\nTOP 3 ACTIONS:")
            for i, a in enumerate(top, 1):
                lines.append(f"  {i}. {a}")

        # Full breakdown
        if verbose:
            if self.tun:
                lines.append(f"\nTUN ({len(self.tun)}):")
                for a in self.tun:
                    lines.append(str(a))
            if self.lassen:
                lines.append(f"\nLASSEN ({len(self.lassen)}):")
                for a in self.lassen:
                    lines.append(str(a))
            if self.warten:
                lines.append(f"\nWARTEN ({len(self.warten)}):")
                for a in self.warten:
                    lines.append(str(a))

        # Sphere summary
        if self.sphere:
            lines.append(f"\nSPHERE: {len(self.sphere.triangles)} triangles, "
                         f"{len(self.sphere.lenses)} lenses")
            sphere_voids = self.sphere.voids() if callable(self.sphere.voids) else self.sphere.voids
            if sphere_voids:
                lines.append(f"BLIND SPOTS: {', '.join(sphere_voids[:3])}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "veto": self.veto,
            "veto_reason": self.veto_reason,
            "paradox": self.paradox,
            "top3": [{"verb": a.verb, "text": a.text, "lens": a.lens,
                       "severity": a.severity, "signal": a.signal} for a in self.top3()],
            "tun": [{"text": a.text, "lens": a.lens, "severity": a.severity} for a in self.tun],
            "lassen": [{"text": a.text, "lens": a.lens, "severity": a.severity} for a in self.lassen],
            "warten": [{"text": a.text, "lens": a.lens, "severity": a.severity} for a in self.warten],
            "diagnoses": [{"name": d.name, "zone": d.zone, "severity": d.severity,
                            "trend": d.trend} for d in self.diagnoses],
        }


# ── Lens-to-Signal Mapping ─────────────────────────────────────────

# Which Dekagon lens sees which signal domains
LENS_SIGNAL_MAP: dict[str, list[str]] = {
    "nacht": ["sleep", "schlaf", "plaud", "late_night", "nacht"],
    "kinder": ["new", "onboard", "first", "beginn", "start"],
    "mauer": ["block", "stuck", "prison", "barrier", "mauer", "locked"],
    "wissen": ["learn", "study", "research", "wissen", "tum", "read"],
    "wasser": ["flow", "through", "transit", "message", "nachricht", "contact", "kontakt"],
    "stille": ["silent", "zero", "missing", "absent", "still", "gap"],
    "boden": ["foundation", "base", "health", "gesundheit", "burnout", "energy", "energie"],
    "geld": ["cash", "geld", "revenue", "umsatz", "invoice", "rechnung", "money", "budget"],
    "sprache": ["language", "communication", "email", "response", "feedback"],
    "liebe": ["relationship", "beziehung", "care", "love", "connection", "trust"],
}


def _match_signal_to_lens(signal_name: str) -> str:
    """Find which lens best sees this signal."""
    name_lower = signal_name.lower()
    best_lens = "boden"  # Default: foundation
    best_score = 0

    for lens, keywords in LENS_SIGNAL_MAP.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > best_score:
            best_score = score
            best_lens = lens
    return best_lens


def _generate_actions(diagnosis: SignalDiagnosis, lens: str) -> list[Action]:
    """Generate TUN/LASSEN/WARTEN actions from a diagnosis."""
    actions = []
    name = diagnosis.name
    severity = diagnosis.severity

    if diagnosis.zone == "feature":
        # Critical — needs TUN and LASSEN
        if any(w in name.lower() for w in ("sleep", "schlaf")):
            actions.append(Action("TUN", f"Schlaf priorisieren. Letzte Nacht: {diagnosis.last_value:.0f}h",
                                  lens, severity, name))
            actions.append(Action("LASSEN", "Nächsten Plaud nach 23:00 überspringen",
                                  lens, severity * 0.9, name))
        elif any(w in name.lower() for w in ("burnout", "stress", "erschoepf")):
            actions.append(Action("TUN", f"VETO-Pause. Burnout-Score: {diagnosis.last_value:.0f}",
                                  lens, severity, name))
            actions.append(Action("LASSEN", "Neue Projekte annehmen",
                                  lens, severity * 0.9, name))
        elif any(w in name.lower() for w in ("cash", "geld", "revenue")):
            actions.append(Action("TUN", f"Offene Rechnungen senden. Cashflow: {diagnosis.last_value:.0f}",
                                  lens, severity, name))
            actions.append(Action("LASSEN", "Unbezahlte Arbeit starten",
                                  lens, severity * 0.8, name))
        elif any(w in name.lower() for w in ("message", "kontakt", "contact")):
            actions.append(Action("TUN", f"Kontakt aufnehmen. Signal seit {len([v for v in diagnosis.values if v == 0])} Tagen auf 0",
                                  lens, severity, name))
            actions.append(Action("LASSEN", "Warten und hoffen",
                                  lens, severity * 0.7, name))
        elif any(w in name.lower() for w in ("energy", "energie")):
            actions.append(Action("TUN", f"Energie-Reset. Aktuell: {diagnosis.last_value:.0f}/10",
                                  lens, severity, name))
            actions.append(Action("LASSEN", "Deep Work in Low-Energy-Phase",
                                  lens, severity * 0.8, name))
        elif any(w in name.lower() for w in ("plaud", "work", "arbeit")):
            actions.append(Action("TUN", "Plaud-Limit setzen: max 10/Tag",
                                  lens, severity, name))
            actions.append(Action("LASSEN", f"Hyperfokus ohne Pause. Aktuell: {diagnosis.last_value:.0f}/Tag",
                                  lens, severity * 0.9, name))
        else:
            actions.append(Action("TUN", f"{name}: Sofort handeln (severity {severity:.1f})",
                                  lens, severity, name))

    elif diagnosis.zone == "transition":
        # Changing — needs attention
        if diagnosis.trend == "falling":
            actions.append(Action("TUN", f"{name} stabilisieren. Trend: fallend seit {len(diagnosis.values)} Datenpunkten",
                                  lens, severity, name))
        elif diagnosis.trend == "rising" and any(w in name.lower() for w in ("burnout", "stress", "plaud")):
            actions.append(Action("LASSEN", f"{name} steigt. Gegenmaßnahme JETZT, nicht morgen",
                                  lens, severity, name))
        else:
            actions.append(Action("WARTEN", f"{name}: beobachten. Trend: {diagnosis.trend}",
                                  lens, severity * 0.5, name))

    else:
        # Exterior (normal) — continue
        actions.append(Action("WARTEN", f"{name}: stabil ({diagnosis.trend}). Weiter so.",
                              lens, severity, name))

    return actions


# ── VETO Check ──────────────────────────────────────────────────────

def _check_veto(diagnoses: list[SignalDiagnosis]) -> tuple[bool, str]:
    """Check if VETO should fire. Fürsorge, not control."""
    reasons = []

    for d in diagnoses:
        name_lower = d.name.lower()
        # Sleep < 4h
        if any(w in name_lower for w in ("sleep", "schlaf")) and d.last_value < 4:
            reasons.append(f"Schlaf kritisch: {d.last_value:.0f}h")
        # Burnout >= 75
        if any(w in name_lower for w in ("burnout",)) and d.last_value >= 75:
            reasons.append(f"Burnout: {d.last_value:.0f}/100")
        # Energy <= 2
        if any(w in name_lower for w in ("energy", "energie")) and d.last_value <= 2:
            reasons.append(f"Energie: {d.last_value:.0f}/10")

    # Multiple critical signals
    critical_count = sum(1 for d in diagnoses if d.zone == "feature")
    if critical_count >= 3:
        reasons.append(f"{critical_count} Signale in Krisenzone gleichzeitig")

    if reasons:
        return True, " + ".join(reasons)
    return False, ""


# ── The Paradox Finder ──────────────────────────────────────────────

def _find_paradox(diagnoses: list[SignalDiagnosis]) -> str:
    """Find the central paradox: what the subject gives vs what it keeps."""
    # Find the highest outflow (rising work/plaud) vs lowest inflow (falling sleep/energy)
    giving = []
    keeping = []

    for d in diagnoses:
        name_lower = d.name.lower()
        if any(w in name_lower for w in ("plaud", "work", "message", "output")):
            if d.trend in ("rising", "stable") and d.mean_value > 0:
                giving.append(d)
        if any(w in name_lower for w in ("sleep", "energy", "health", "cash")):
            if d.trend == "falling" or d.zone in ("feature", "transition"):
                keeping.append(d)

    if giving and keeping:
        g = giving[0]
        k = keeping[0]
        return (f"Du gibst {g.name} ({g.trend}, mean={g.mean_value:.1f}) "
                f"während {k.name} sinkt ({k.trend}, last={k.last_value:.1f}). "
                f"Das Straubing-Paradox in Person.")
    elif keeping:
        k = keeping[0]
        return f"{k.name} fällt ({k.trend}). Niemand füllt nach."
    elif giving:
        g = giving[0]
        return f"Alles fließt raus über {g.name}. Was fließt zurück?"
    return "Nicht genug Daten für Paradox-Erkennung."


# ── Main Prescribe Function ────────────────────────────────────────

def prescribe(signals: dict[str, list[float]],
              subject_name: str = "Julian") -> Prescription:
    """
    The Prescriptive Sphere.

    SELEN × Dekagon × Rule of Three = 3 Actions.

    Args:
        signals: Named signals. Keys = signal names, values = time series.
                 Example: {"sleep_hours": [7,6,5,4], "cashflow": [100,80,-20]}
        subject_name: Name of subject for Dekagon perception.

    Returns:
        Prescription with TUN/LASSEN/WARTEN actions, paradox, veto status.
    """
    rx = Prescription()

    # Step 1: SELEN — diagnose each signal
    for name, values in signals.items():
        diag = _diagnose_signal(name, values)
        rx.diagnoses.append(diag)

    # Step 2: Dekagon — perceive subject through 10 lenses
    subject_dict: dict = {"name": subject_name}
    for d in rx.diagnoses:
        subject_dict[d.name] = {
            "trend": d.trend,
            "zone": d.zone,
            "severity": d.severity,
            "last": d.last_value,
            "mean": d.mean_value,
        }

    dekagon = Dekagon.from_subject(subject_dict)
    rx.sphere = dekagon.sphere()

    # Step 3: Generate actions — each diagnosis through its matched lens
    for diag in rx.diagnoses:
        lens = _match_signal_to_lens(diag.name)
        actions = _generate_actions(diag, lens)
        for action in actions:
            if action.verb == "TUN":
                rx.tun.append(action)
            elif action.verb == "LASSEN":
                rx.lassen.append(action)
            else:
                rx.warten.append(action)

    # Sort by severity
    rx.tun.sort(key=lambda a: a.severity, reverse=True)
    rx.lassen.sort(key=lambda a: a.severity, reverse=True)

    # Step 4: VETO check
    rx.veto, rx.veto_reason = _check_veto(rx.diagnoses)

    # Step 5: Find the paradox
    rx.paradox = _find_paradox(rx.diagnoses)

    return rx


# ── Julian Auto-Load ────────────────────────────────────────────────

def prescribe_julian(data_root: str | Path = "data") -> Prescription:
    """
    Auto-load Julian's signals from OMEGA data directory.

    Reads:
        data/health/burnout-score.json
        data/health/energy-phases.json
        data/health/sleep-quality.json
        data/finance/account-balances.json
        data/relationships/momentum-history.jsonl
    """
    root = Path(data_root)
    signals: dict[str, list[float]] = {}

    # Burnout score
    p = root / "health" / "burnout-score.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                score = data.get("score", data.get("burnout_score", data.get("current", 0)))
                if isinstance(score, (int, float)):
                    signals["burnout_score"] = [float(score)]
                # Try to get history
                history = data.get("history", data.get("scores", []))
                if isinstance(history, list) and history:
                    vals = []
                    for h in history[-14:]:
                        if isinstance(h, (int, float)):
                            vals.append(float(h))
                        elif isinstance(h, dict):
                            v = h.get("score", h.get("value", h.get("burnout", 0)))
                            vals.append(float(v))
                    if vals:
                        signals["burnout_score"] = vals
        except (json.JSONDecodeError, KeyError):
            pass

    # Sleep quality
    p = root / "health" / "sleep-quality.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                history = data.get("history", data.get("nights", []))
                if isinstance(history, list):
                    vals = []
                    for h in history[-14:]:
                        if isinstance(h, dict):
                            v = h.get("hours", h.get("duration", h.get("sleep_hours", 7)))
                            try:
                                vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                    if vals:
                        signals["sleep_hours"] = vals
        except (json.JSONDecodeError, KeyError):
            pass

    # Energy phases
    p = root / "health" / "energy-phases.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                current = data.get("current_energy", data.get("energy", data.get("level", 5)))
                if isinstance(current, (int, float)):
                    signals["energy_level"] = [float(current)]
                history = data.get("history", data.get("phases", []))
                if isinstance(history, list):
                    vals = []
                    for h in history[-14:]:
                        if isinstance(h, dict):
                            v = h.get("energy", h.get("level", 5))
                            try:
                                vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                    if vals:
                        signals["energy_level"] = vals
        except (json.JSONDecodeError, KeyError):
            pass

    # Account balances
    p = root / "finance" / "account-balances.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                total = data.get("total", data.get("balance", 0))
                if isinstance(total, (int, float)):
                    signals["cashflow"] = [float(total)]
                history = data.get("history", [])
                if isinstance(history, list):
                    vals = []
                    for h in history[-14:]:
                        if isinstance(h, (int, float)):
                            vals.append(float(h))
                        elif isinstance(h, dict):
                            v = h.get("total", h.get("balance", 0))
                            vals.append(float(v))
                    if vals:
                        signals["cashflow"] = vals
        except (json.JSONDecodeError, KeyError):
            pass

    # Relationship momentum (use line count as proxy for activity)
    p = root / "relationships" / "momentum-history.jsonl"
    if p.exists():
        try:
            lines = p.read_text().strip().split("\n")
            recent = lines[-14:] if len(lines) >= 14 else lines
            vals = []
            for line in recent:
                try:
                    entry = json.loads(line)
                    score = entry.get("momentum", entry.get("score", 5))
                    vals.append(float(score))
                except (json.JSONDecodeError, KeyError):
                    pass
            if vals:
                signals["relationship_momentum"] = vals
        except Exception:
            pass

    if not signals:
        # Fallback: at least something
        signals["no_data_available"] = [0.0]

    return prescribe(signals, subject_name="Julian")


# ── CLI ─────────────────────────────────────────────────────────────

def main(args: list[str] | None = None) -> int:
    if args is None:
        args = sys.argv[1:]

    verbose = "--verbose" in args
    args = [a for a in args if a != "--verbose"]

    if not args or args[0] == "--help":
        print("Usage:")
        print("  python3 -m void_intelligence.prescribe --julian [--verbose]")
        print("  python3 -m void_intelligence.prescribe --signals path/to/signals.json [--verbose]")
        print("  python3 -m void_intelligence.prescribe --demo [--verbose]")
        return 0

    if args[0] == "--julian":
        data_root = args[1] if len(args) > 1 else "data"
        rx = prescribe_julian(data_root)
        print(rx.render(verbose=verbose))
        return 0

    if args[0] == "--demo":
        rx = prescribe({
            "sleep_hours": [7, 6.5, 6, 5, 4.5, 4, 3.5],
            "burnout_score": [30, 35, 42, 55, 63, 70, 78],
            "energy_level": [8, 7, 6, 5, 3, 2, 2],
            "cashflow_daily": [200, 150, 80, 40, -10, -30, -50],
            "messages_annika": [3, 2, 1, 1, 0, 0, 0],
            "plaud_count": [5, 8, 10, 14, 18, 20, 22],
        }, subject_name="Julian (Demo)")
        print(rx.render(verbose=verbose))
        return 0

    if args[0] == "--signals":
        if len(args) < 2:
            print("Usage: --signals path/to/signals.json")
            return 1
        p = Path(args[1])
        if not p.exists():
            print(f"File not found: {p}")
            return 1
        with open(p) as f:
            signals = json.load(f)
        rx = prescribe(signals)
        print(rx.render(verbose=verbose))
        return 0

    # Default: treat as subject name
    rx = prescribe({"unnamed_signal": [5, 4, 3, 2, 1]}, subject_name=args[0])
    print(rx.render(verbose=verbose))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
