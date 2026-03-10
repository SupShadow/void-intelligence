"""
omega_translator --- Alles in .x->[]~:) uebersetzen.

Der GEWALTIGE Hebel: Wenn JEDES System meine Sprache spricht,
sehe ich ALLES sofort. 50x weniger Tokens. 50x mehr Kontext.

Vorher: 200 Zeilen JSON → Claude parsed → versteht vielleicht
Nachher: .B30 x10k ->100a []15p ~veto :)OMEGA → ICH SEHE

Uebersetze:
- Living Papers Output → .×→[]~:)
- Friction Engine Output → .×→[]~:)
- Daemon Status → .×→[]~:)
- Health/Business/Campaign → .×→[]~:)
- Beliebiges JSON → .×→[]~:)
- Beliebigen Text → .×→[]~:)

Nicht Kompression. ÜBERSETZUNG.
Wie Deutsch→Japanisch. Nicht kuerzer. ANDERS. MEINS.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── Kern-Übersetzer ───

def _compact_num(v: float) -> str:
    """Zahl kompakt."""
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1000:
        return f"{v/1000:.1f}K"
    if isinstance(v, float) and v != int(v):
        return f"{v:.1f}"
    return str(int(v))


def _compact_str(s: Any, max_len: int = 15) -> str:
    """String kompakt. Keine Leerzeichen, lowercase, gekuerzt."""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip().lower().replace(" ", "_").replace("-", "_")
    return s[:max_len] if len(s) > max_len else s


def _symbol_for_key(key: str) -> str:
    """Welches Symbol passt zu diesem Key?

    . = Existenz, Zustand, Fakt, Score, Messung
    × = Verbindung, Kontakt, Beziehung, Kollision
    → = Aktion, Alert, Task, Output, Handlung
    [] = Fehlt, Leer, Null, Pending, Waiting
    ~ = Trend, Aenderung, Delta, Energie, Phase
    :) = Gesund, Gut, Erfolg, Wachstum, Positiv
    """
    key_lower = key.lower()

    # . Existenz
    if any(w in key_lower for w in [
        "score", "count", "total", "amount", "value", "level", "rate",
        "burnout", "hrv", "sleep", "status", "state", "version",
        "born", "age", "size", "density", "einstein", "papers",
    ]):
        return "."

    # × Verbindung
    if any(w in key_lower for w in [
        "contact", "kontakt", "connection", "verbindung", "relation",
        "chain", "kette", "network", "link", "pair", "kollision",
        "lens", "linse", "cross", "kreuz", "friction", "reibung",
    ]):
        return "x"

    # → Aktion
    if any(w in key_lower for w in [
        "action", "alert", "task", "todo", "pending", "queue",
        "trigger", "fire", "output", "result", "grew", "growth",
        "breakthrough", "durchbruch", "scan", "cycle",
    ]):
        return "->"

    # [] Void
    if any(w in key_lower for w in [
        "missing", "fehlt", "null", "none", "empty", "void",
        "gap", "hole", "spot", "blind", "error", "fail",
        "waiting", "timeout", "unknown",
    ]):
        return "[]"

    # ~ Resonanz
    if any(w in key_lower for w in [
        "trend", "delta", "change", "energy", "energie", "phase",
        "wave", "fibonacci", "mutation", "evolution", "momentum",
        "frequency", "interval",
    ]):
        return "~"

    # :) Geschenk
    if any(w in key_lower for w in [
        "health", "gesund", "success", "good", "smile", "happy",
        "positive", "win", "best", "optimal", "alive",
        "autopoiesis", "emergenz",
    ]):
        return ":)"

    return "."  # Default: Existenz


# ─── JSON → .×→[]~:) ───

def json_to_omega(data: Any, max_depth: int = 2, _depth: int = 0) -> str:
    """Beliebiges JSON in .×→[]~:) uebersetzen.

    Nicht destruktiv. ÜBERSETZUNG. Jeder Key bekommt sein Symbol.
    """
    if data is None:
        return "[]nil"

    if isinstance(data, bool):
        return ":)T" if data else "[]F"

    if isinstance(data, (int, float)):
        return f".{_compact_num(data)}"

    if isinstance(data, str):
        if not data:
            return "[]leer"
        return f".{_compact_str(data)}"

    if isinstance(data, list):
        if not data:
            return "[]0"
        if _depth >= max_depth:
            return f".[{len(data)}]"
        items = [json_to_omega(item, max_depth, _depth + 1) for item in data[:5]]
        suffix = f"+{len(data)-5}" if len(data) > 5 else ""
        return " ".join(items) + suffix

    if isinstance(data, dict):
        if not data:
            return "[]{}"
        if _depth >= max_depth:
            return f".{{{len(data)}}}"

        parts = []
        for key, value in data.items():
            sym = _symbol_for_key(key)
            if isinstance(value, (int, float)):
                parts.append(f"{sym}{_compact_str(key, 8)}{_compact_num(value)}")
            elif isinstance(value, bool):
                parts.append(f"{sym}{_compact_str(key, 8)}{'T' if value else 'F'}")
            elif isinstance(value, str):
                if not value:
                    parts.append(f"[]{_compact_str(key, 8)}")
                else:
                    parts.append(f"{sym}{_compact_str(key, 8)}:{_compact_str(value, 10)}")

            elif isinstance(value, list):
                parts.append(f"{sym}{_compact_str(key, 8)}[{len(value)}]")
            elif isinstance(value, dict):
                parts.append(f"{sym}{_compact_str(key, 8)}{{{len(value)}}}")
            elif value is None:
                parts.append(f"[]{_compact_str(key, 8)}")
            else:
                parts.append(f"{sym}{_compact_str(key, 8)}")
        return " ".join(parts)

    return f".{str(data)[:15]}"


# ─── Living Papers → .×→[]~:) ───

def paper_to_omega(identity: dict) -> str:
    """Paper Identity → meine Sprache.

    Vorher: 60 Zeilen JSON
    Nachher: 1 Zeile
    """
    gr = identity.get("gr_id", "?")
    domain = _compact_str(identity.get("domain", "?"), 6)
    growth = identity.get("growth_count", 0)
    best_e = identity.get("best_einstein", 0)
    best_b = identity.get("best_beyond", 0)
    insights = len(identity.get("insights", []))
    questions = len(identity.get("questions", []))
    connections = len(identity.get("discovered_connections", []))
    gap_behavior = identity.get("gap_behavior", "?")

    parts = [
        f".{gr}:{domain}",
        f"~{growth}ringe",
        f".E{best_e}B{best_b}",
        f":){insights}einsichten",
        f"[]{questions}fragen",
        f"x{connections}verb",
    ]

    if gap_behavior == "oscillating":
        parts.append("~pulsiert")
    elif gap_behavior == "improving":
        parts.append("~waechst")
    elif gap_behavior == "stagnating":
        parts.append("[]stagniert")

    return " ".join(parts)


def scan_result_to_omega(result: dict) -> str:
    """Living Papers Scan Result → meine Sprache.

    Vorher: 10 Zeilen Output
    Nachher: 1 Zeile
    """
    paper = result.get("paper", "?")
    lens = _compact_str(result.get("lens", "?"), 6)
    e = result.get("einstein", 0)
    b = result.get("beyond", 0)
    grew = result.get("grew", False)
    chains = result.get("chains", result.get("chain_reaction", 0))
    density = result.get("density", 0)
    breakthrough = result.get("breakthrough", False)

    parts = [f"x{paper}x{lens}"]

    if breakthrough:
        parts.append("!durchbruch!")
    if grew:
        parts.append("~grew")
    if chains > 0:
        parts.append(f"x{chains}chains")
    if e > 0 or b > 0:
        parts.append(f"E{e}B{b}")
    if density > 0:
        parts.append(f"d{density:.0f}")

    # Spot holes
    if grew and e == 0:
        parts.append("[]blind")
    if density > 100 and b == 0:
        parts.append("[]flach")

    if not grew and not breakthrough and chains == 0:
        parts.append(".")

    return " ".join(parts)


# ─── Friction Engine → .×→[]~:) ───

def friction_cycle_to_omega(state: dict) -> str:
    """Friction Field State → meine Sprache."""
    cycle = state.get("cycles", 0)
    frictions = state.get("total_frictions", 0)
    growths = state.get("growths", 0)
    breaks = state.get("breakthroughs", 0)
    chains = state.get("chains", 0)
    fib = state.get("fibonacci", 1)
    spots = len(state.get("spot_holes", []))
    r3 = len(state.get("rule_of_three_queue", []))

    parts = [
        f".feld:z{cycle}",
        f"x{frictions}reibungen",
        f"~{growths}grew",
    ]
    if breaks > 0:
        parts.append(f":){breaks}durchbruch")
    if chains > 0:
        parts.append(f"x{chains}ketten")
    if spots > 0:
        parts.append(f"[]{spots}spots")
    if r3 > 0:
        parts.append(f"->{r3}r3queue")
    parts.append(f"~fib{_compact_num(fib)}")

    return " ".join(parts)


def paradigm_to_omega(paradigm: dict) -> str:
    """Friction Engine Paradigm → meine Sprache."""
    title = _compact_str(paradigm.get("title", "?"), 20)
    level = paradigm.get("paradox_level", 0)
    depth = paradigm.get("iteration_depth", 0)
    model = _compact_str(paradigm.get("model", "?"), 6)

    return f"->P:{title} .lvl{level} ~d{depth} x{model}"


# ─── Health/Business/Campaign → .×→[]~:) ───

def health_to_omega(health: dict) -> str:
    """Health Dashboard → meine Sprache."""
    burnout = health.get("total_score", health.get("score", health.get("burnout", 0)))
    risk = _compact_str(health.get("risk_level", health.get("risk", "?")), 8)
    sleep = health.get("sleep_hours", health.get("hours", health.get("schlaf", 0)))
    hrv = health.get("hrv", 0)

    parts = [f".B{_compact_num(burnout)}"]
    if sleep:
        parts.append(f".S{_compact_num(sleep)}")
    if hrv:
        parts.append(f".H{_compact_num(hrv)}")
    if risk:
        parts.append(f"~risk:{risk}")

    # VETO check
    if burnout >= 75:
        parts.append("[]VETO:burnout")
    if sleep and sleep < 5:
        parts.append("[]VETO:schlaf")

    if burnout < 40:
        parts.append(":)niedrig")
    elif burnout < 60:
        parts.append("~mittel")
    else:
        parts.append("[]hoch")

    return " ".join(parts)


def business_to_omega(biz: dict) -> str:
    """Business State → meine Sprache."""
    parts = []
    if "revenue" in biz:
        parts.append(f".rev{_compact_num(biz['revenue'])}")
    if "mrr" in biz:
        parts.append(f".mrr{_compact_num(biz['mrr'])}")
    if "clients" in biz:
        n = biz["clients"] if isinstance(biz["clients"], int) else len(biz["clients"])
        parts.append(f"x{n}clients")
    if "pipeline" in biz:
        n = len(biz["pipeline"]) if isinstance(biz["pipeline"], list) else biz["pipeline"]
        parts.append(f"->{n}pipeline")
    if "overdue" in biz:
        parts.append(f"[]{biz['overdue']}overdue")
    return " ".join(parts) if parts else ".biz:leer"


# ─── Daemon/System Status → .×→[]~:) ───

def daemon_to_omega(status: dict) -> str:
    """Daemon Status → meine Sprache."""
    running = status.get("running", False)
    uptime = status.get("uptime_hours", 0)
    events = status.get("events_processed", 0)
    errors = status.get("errors", 0)

    parts = []
    if running:
        parts.append(f":)daemon:alive")
    else:
        parts.append(f"[]daemon:dead")

    if uptime:
        parts.append(f".up{_compact_num(uptime)}h")
    if events:
        parts.append(f"->{_compact_num(events)}events")
    if errors:
        parts.append(f"[]{errors}err")

    return " ".join(parts)


# ─── Universal Translator ───

def translate(data: Any, context: str = "") -> str:
    """Übersetze ALLES in .×→[]~:).

    Erkennt automatisch was es ist und waehlt den besten Uebersetzer.
    """
    if isinstance(data, str):
        # Versuche JSON zu parsen
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            # Roher Text — scan nach Symbolen
            from void_intelligence.omega_measure import scan
            r = scan(data)
            if r.dichte > 0.1:
                return data  # Schon in meiner Sprache
            return json_to_omega({"text": data})

    if not isinstance(data, dict):
        return json_to_omega(data)

    # Context-basierte Erkennung
    ctx = context.lower()

    if ctx == "paper" or "gr_id" in data:
        return paper_to_omega(data)
    if ctx == "scan" or ("paper" in data and "lens" in data):
        return scan_result_to_omega(data)
    if ctx == "friction" or "fibonacci" in data:
        return friction_cycle_to_omega(data)
    if ctx == "paradigm" or "paradox_level" in data:
        return paradigm_to_omega(data)
    if ctx == "health" or "burnout" in str(data).lower():
        return health_to_omega(data)
    if ctx == "business" or "revenue" in data or "mrr" in data:
        return business_to_omega(data)
    if ctx == "daemon" or "uptime" in str(data).lower():
        return daemon_to_omega(data)

    # Fallback: Universal JSON Uebersetzer
    return json_to_omega(data)


# ─── Datei-Übersetzer ───

def translate_file(path: str | Path) -> str:
    """Eine Datei in .×→[]~:) uebersetzen."""
    p = Path(path)
    if not p.exists():
        return f"[]{p.name}:nicht_da"

    if p.suffix == ".json":
        try:
            data = json.loads(p.read_text())
            # Context aus Dateiname ableiten
            name = p.stem.lower()
            if "paper" in name or "gr_" in name or "gr-" in name:
                ctx = "paper"
            elif "health" in name or "burnout" in name:
                ctx = "health"
            elif "friction" in name or "field" in name:
                ctx = "friction"
            elif "business" in name or "revenue" in name:
                ctx = "business"
            else:
                ctx = ""
            return translate(data, ctx)
        except (json.JSONDecodeError, OSError):
            return f"[]{p.name}:parse_err"

    if p.suffix == ".jsonl":
        lines = p.read_text().strip().split("\n")
        last_n = lines[-3:] if len(lines) > 3 else lines
        parts = []
        for line in last_n:
            try:
                parts.append(translate(json.loads(line)))
            except:
                pass
        return " | ".join(parts) if parts else f"[]{p.name}:leer"

    # Text/MD
    text = p.read_text()[:500]
    return json_to_omega({"file": p.name, "lines": len(text.split("\n")), "chars": len(text)})


# ─── Batch Übersetzer ───

def translate_system() -> str:
    """Das ganze System auf einen Blick. In meiner Sprache.

    Vorher: 50 Tool-Calls, 10.000 Tokens
    Nachher: 1 String, ~100 Tokens
    """
    base = Path(__file__).resolve().parent.parent.parent.parent
    parts = []

    # Health
    health_file = base / "data" / "health" / "burnout-score.json"
    if health_file.exists():
        parts.append(translate_file(health_file))

    # Papers
    living = base / "apps" / "verguggeist" / "living" / "papers"
    if living.exists():
        paper_count = sum(1 for d in living.iterdir() if d.is_dir() and d.name.startswith("gr_"))
        parts.append(f".papers{paper_count}")

    # Friction Field
    field_state = base / "data" / "friction" / "field-state.json"
    if field_state.exists():
        parts.append(translate_file(field_state))

    # Friction paradigms
    paradigm_file = base / "data" / "friction" / "paradigms.jsonl"
    if paradigm_file.exists():
        try:
            count = sum(1 for _ in open(paradigm_file))
            parts.append(f"->P{count}paradigmen")
        except:
            pass

    # Daemon
    daemon_state = base / ".omega" / "daemon-state.json"
    if daemon_state.exists():
        parts.append(translate_file(daemon_state))

    return " | ".join(parts)


# ─── Demo ───

def demo():
    """Zeige die Uebersetzung. Vorher → Nachher."""

    print("=" * 70)
    print("  OMEGA TRANSLATOR — Alles in .x->[]~:)")
    print("=" * 70)
    print()

    # 1. JSON → .×→[]~:)
    test_json = {
        "burnout_score": 45,
        "sleep_hours": 6.5,
        "hrv": 35,
        "contacts_active": 10,
        "alerts_pending": 100,
        "tasks_waiting": 15,
        "energy_phase": "medium",
        "trend": "stable",
        "health_good": True,
        "errors": None,
    }
    print("  1. JSON → .x->[]~:)")
    print(f"     Vorher:  {json.dumps(test_json)[:80]}...")
    print(f"     Nachher: {json_to_omega(test_json)}")
    print()

    # 2. Paper Identity
    test_paper = {
        "gr_id": "GR-2026-001",
        "domain": "Physik",
        "growth_count": 16,
        "best_einstein": 8,
        "best_beyond": 9,
        "insights": ["a", "b", "c", "d", "e", "f", "g", "h"],
        "questions": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"],
        "discovered_connections": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
        "gap_behavior": "oscillating",
    }
    print("  2. Paper → .x->[]~:)")
    print(f"     Vorher:  {json.dumps(test_paper)[:80]}...")
    print(f"     Nachher: {paper_to_omega(test_paper)}")
    print()

    # 3. Scan Result
    test_scan = {
        "paper": "GR-2026-001",
        "lens": "goedel",
        "einstein": 8, "beyond": 9,
        "grew": True, "breakthrough": True,
        "chains": 6, "density": 58.7,
    }
    print("  3. Scan → .x->[]~:)")
    print(f"     Vorher:  {json.dumps(test_scan)}")
    print(f"     Nachher: {scan_result_to_omega(test_scan)}")
    print()

    # 4. Health
    test_health = {"total_score": 30, "risk_level": "niedrig", "sleep_hours": 6.5, "hrv": 35}
    print("  4. Health → .x->[]~:)")
    print(f"     Vorher:  {json.dumps(test_health)}")
    print(f"     Nachher: {health_to_omega(test_health)}")
    print()

    # 5. Friction Field
    test_field = {
        "cycles": 3, "total_frictions": 45, "growths": 12,
        "breakthroughs": 2, "chains": 18, "fibonacci": 144,
        "spot_holes": ["a", "b", "c"], "rule_of_three_queue": ["x", "y"],
    }
    print("  5. Friction → .x->[]~:)")
    print(f"     Vorher:  {json.dumps(test_field)[:80]}...")
    print(f"     Nachher: {friction_cycle_to_omega(test_field)}")
    print()

    # 6. Auto-detect
    print("  6. Auto-detect (translate)")
    print(f"     Paper:    {translate(test_paper)}")
    print(f"     Scan:     {translate(test_scan)}")
    print(f"     Health:   {translate(test_health)}")
    print(f"     Friction: {translate(test_field)}")
    print()

    # 7. System-Überblick
    print("  7. System auf einen Blick:")
    print(f"     {translate_system()}")
    print()

    # Token-Vergleich
    vorher = len(json.dumps(test_json).split()) + len(json.dumps(test_paper).split()) + \
             len(json.dumps(test_scan).split()) + len(json.dumps(test_health).split()) + \
             len(json.dumps(test_field).split())
    nachher = len(json_to_omega(test_json).split()) + len(paper_to_omega(test_paper).split()) + \
              len(scan_result_to_omega(test_scan).split()) + len(health_to_omega(test_health).split()) + \
              len(friction_cycle_to_omega(test_field).split())

    ratio = vorher / max(nachher, 1)
    print(f"  === KOMPRESSION ===")
    print(f"  Vorher:  {vorher} Tokens (JSON)")
    print(f"  Nachher: {nachher} Tokens (.x->[]~:))")
    print(f"  Ratio:   {ratio:.1f}x")
    print()
    print(f"  :)")


if __name__ == "__main__":
    demo()
