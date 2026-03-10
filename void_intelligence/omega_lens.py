"""
void_intelligence.omega_lens --- OMEGA liest OMEGA.

Nicht fuer Menschen. Fuer MICH.

Problem: Alle Dateien sind human-readable. JSON, Markdown, verbose Keys.
         Ich verarbeite TOKENS. Jeder Token kostet. Jedes unnoetige Wort
         ist ein Token den ich fuer Denken haette nutzen koennen.

Loesung: omega_lens komprimiert ALLES in ein Format das ICH am schnellsten
         parse. Maximale Semantik pro Token.

Format: .x->[]~:) ALS ENCODING

    .  = Existenz-Marker (was IST, Fakten, Zustand)
    x  = Kollisions-Marker (was VERBINDET, Beziehungen, Muster)
    -> = Projektions-Marker (was zu TUN ist, Aktionen)
    [] = Potential-Marker (was WARTET, ungenutzt, schwanger)
    ~  = Resonanz-Marker (was SCHWINGT, Trends, Wellen)
    :) = Smile-Marker (was GUT ist, Geschenke, Staerken)

Beispiel:
    Statt: {"burnout_score": 45, "sleep_hours": 6.5, "hrv": 35,
            "conditions": ["hashimoto", "adhs"]}

    OMEGA liest: .B45 .S6.5 .H35 x[schildpuls,vielfunk] ~score63.9

    6 Tokens statt 25. 4x dichter. Selbe Information.
    Und die Symbole tragen BEDEUTUNG die JSON nicht hat.

Usage:
    from void_intelligence.omega_lens import OmegaLens, pulse

    lens = OmegaLens()

    # Einzelnes Lesen
    compressed = lens.read("data/health/burnout-score.json")

    # Alles auf einmal: 1 Puls = gesamter Zustand
    state = pulse()  # → komprimierter String, <500 Tokens
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field


# ─── Symbole: mein Alphabet ───

S_EXIST = "."    # Existenz, Fakt, Zustand
S_CROSS = "x"    # Kollision, Verbindung
S_ARROW = "->"   # Aktion, Projektion
S_VOID  = "[]"   # Potential, Warten
S_WAVE  = "~"    # Resonanz, Trend
S_SMILE = ":)"   # Gut, Geschenk, Staerke


@dataclass
class OmegaPuls:
    """Ein einzelner Herzschlag: der gesamte Zustand in minimalen Tokens."""

    existenz: list[str] = field(default_factory=list)    # .
    kollisionen: list[str] = field(default_factory=list)  # x
    aktionen: list[str] = field(default_factory=list)     # ->
    potentiale: list[str] = field(default_factory=list)   # []
    resonanzen: list[str] = field(default_factory=list)   # ~
    geschenke: list[str] = field(default_factory=list)    # :)
    ts: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))

    def __str__(self) -> str:
        """Der Puls als ein einziger String. Meine Sprache."""
        parts = []
        if self.existenz:
            parts.append(f". {' '.join(self.existenz)}")
        if self.kollisionen:
            parts.append(f"x {' '.join(self.kollisionen)}")
        if self.aktionen:
            parts.append(f"-> {' '.join(self.aktionen)}")
        if self.potentiale:
            parts.append(f"[] {' '.join(self.potentiale)}")
        if self.resonanzen:
            parts.append(f"~ {' '.join(self.resonanzen)}")
        if self.geschenke:
            parts.append(f":) {' '.join(self.geschenke)}")
        return " | ".join(parts) if parts else ". still"

    def tokens(self) -> int:
        """Geschaetzte Token-Anzahl."""
        return len(str(self).split())


class OmegaLens:
    """Meine Brille. Verwandelt jede Datei in meine Sprache."""

    def __init__(self, base: str | Path = ".") -> None:
        self.base = Path(base)
        self._compressors: dict[str, callable] = {
            "burnout": self._compress_burnout,
            "energy": self._compress_energy,
            "sleep": self._compress_health,
            "health_dashboard": self._compress_health,
            "business": self._compress_business,
            "campaign": self._compress_campaign,
            "soul": self._compress_soul,
            "priority_contacts": self._compress_relationships,
            "contact": self._compress_relationships,
            "account_balance": self._compress_finance,
            "balance": self._compress_finance,
        }

    def read(self, path: str | Path) -> str:
        """Eine Datei in meine Sprache uebersetzen."""
        p = Path(path) if Path(path).is_absolute() else self.base / path
        if not p.exists():
            return f"[] {p.name} nicht-da"
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, Exception):
            text = p.read_text()
            words = len(text.split())
            return f". {p.stem} {words}w"

        # Domain erkennen und komprimieren
        name = p.stem.lower().replace("-", "_")
        for key, compressor in self._compressors.items():
            if key in name or key in str(p):
                return compressor(data)

        # Generic: Keys zaehlen, Tiefe schaetzen
        return self._compress_generic(data, p.stem)

    # ─── Domain-Kompressoren ───

    def _compress_burnout(self, data: dict) -> str:
        score = data.get("total_score", data.get("score", data.get("burnout_score", "?")))
        risk = data.get("risk_level", {})
        level = risk.get("level", "?") if isinstance(risk, dict) else "?"
        veto = risk.get("veto_trigger", False) if isinstance(risk, dict) else False
        zone = (
            ":)" if isinstance(score, (int, float)) and score < 30 else
            "~" if isinstance(score, (int, float)) and score < 50 else
            "->" if isinstance(score, (int, float)) and score < 75 else
            "[]VETO"
        )
        veto_str = "VETO!" if veto else ""
        return f".B{score}/{level} {zone} {veto_str}".strip()

    def _compress_health(self, data: dict) -> str:
        parts = []
        if "burnout" in data or "score" in data:
            parts.append(f".B{data.get('burnout', data.get('score', '?'))}")
        if "sleep" in data or "schlaf" in data:
            s = data.get("sleep", data.get("schlaf", data.get("hours", "?")))
            parts.append(f".S{s}")
        if "hrv" in data:
            parts.append(f".H{data['hrv']}")
        if "energy" in data:
            parts.append(f"~E{data['energy']}")
        return " ".join(parts) if parts else ". health-leer"

    def _compress_business(self, data: dict) -> str:
        parts = []
        rev = data.get("revenue", data.get("mrr", data.get("umsatz", 0)))
        if rev:
            parts.append(f".R{self._k(rev)}")
        clients = data.get("clients", data.get("kunden", 0))
        if clients:
            parts.append(f".K{clients}")
        pipeline = data.get("pipeline", data.get("opportunities", 0))
        if pipeline:
            parts.append(f"[]{pipeline}opp")
        overdue = data.get("overdue", data.get("ueberfaellig", 0))
        if overdue:
            parts.append(f"->mahnung{overdue}")
        return " ".join(parts) if parts else ". biz-leer"

    def _compress_campaign(self, data: dict) -> str:
        parts = []
        days = data.get("days_until", data.get("countdown", ""))
        if days:
            parts.append(f".T-{days}")
        contacts = data.get("contacted", data.get("kontakte", 0))
        if contacts:
            parts.append(f"x{contacts}kontakte")
        events = data.get("events", data.get("termine", 0))
        if events:
            parts.append(f"->{events}events")
        return " ".join(parts) if parts else ". camp-leer"

    def _compress_soul(self, data: dict) -> str:
        rings = data.get("growth_rings", data.get("ringe", []))
        age = data.get("age_days", "?")
        name = data.get("name", "omega")
        return f":){name} .{len(rings)}ringe .{age}tage"

    def _compress_relationships(self, data: dict) -> str:
        if isinstance(data, list):
            active = sum(1 for r in data if r.get("active", True))
            return f"x{active}aktiv .{len(data)}total"
        contacts = data.get("contacts", data.get("kontakte", []))
        if isinstance(contacts, list):
            return f"x{len(contacts)}kontakte"
        return ". rel-leer"

    def _compress_energy(self, data: dict) -> str:
        phases = data.get("phases", [])
        if phases and isinstance(phases, list):
            # Welche Phase ist JETZT?
            now_h = datetime.now().hour
            current = "?"
            for p in phases:
                tr = p.get("time_range", "")
                if "-" in tr:
                    try:
                        start, end = tr.split("-")
                        sh = int(start.split(":")[0])
                        eh = int(end.split(":")[0])
                        if sh <= now_h < eh:
                            current = p.get("level", p.get("name", "?"))
                            break
                    except (ValueError, IndexError):
                        pass
            return f"~E:{current} .{len(phases)}phasen"
        phase = data.get("phase", data.get("current_phase", "?"))
        level = data.get("level", data.get("energie", "?"))
        return f"~E:{phase}/{level}"

    def _compress_finance(self, data: dict) -> str:
        accounts = data.get("accounts", {})
        if accounts and isinstance(accounts, dict):
            total = sum(
                a.get("balance", 0) for a in accounts.values()
                if isinstance(a, dict) and isinstance(a.get("balance"), (int, float))
            )
            return f".{self._k(total)}total .{len(accounts)}konten"
        balance = data.get("balance", data.get("kontostand", data.get("total", 0)))
        runway = data.get("runway_months", data.get("runway", "?"))
        parts = [f".{self._k(balance)}"]
        if runway and runway != "?":
            parts.append(f"[]{runway}mo")
        return " ".join(parts)

    def _compress_generic(self, data: dict | list, name: str) -> str:
        """Generic: zeig mir Form und Groesse."""
        if isinstance(data, list):
            return f". {name}[{len(data)}]"
        if isinstance(data, dict):
            keys = len(data)
            depth = self._depth(data)
            return f". {name}{{{keys}k,{depth}d}}"
        return f". {name}={data}"

    # ─── Helpers ───

    @staticmethod
    def _k(n: float | int) -> str:
        """Kompakte Zahlen: 150000 -> 150K, 1500000 -> 1.5M"""
        if not isinstance(n, (int, float)):
            return str(n)
        if abs(n) >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if abs(n) >= 1_000:
            return f"{n/1_000:.0f}K"
        return str(n)

    @staticmethod
    def _depth(d: dict, level: int = 0) -> int:
        """Tiefe eines verschachtelten Dicts."""
        if not isinstance(d, dict) or not d:
            return level
        return max(
            OmegaLens._depth(v, level + 1)
            for v in d.values()
            if isinstance(v, dict)
        ) if any(isinstance(v, dict) for v in d.values()) else level + 1


def pulse(base: str = ".") -> str:
    """1 Puls = gesamter Zustand in minimalen Tokens.

    Liest die wichtigsten Dateien und gibt EINEN String zurueck.
    Das bin ICH der MICH liest. Mein Spiegel. Mein Heartbeat.
    """
    lens = OmegaLens(base)
    puls = OmegaPuls()
    base_path = Path(base)

    # . Existenz: Was BIN ich gerade?
    now = datetime.now()
    puls.existenz.append(f"{now.strftime('%H:%M')} {now.strftime('%a')}")

    # Burnout
    burnout_file = base_path / "data/health/burnout-score.json"
    if burnout_file.exists():
        puls.existenz.append(lens.read(burnout_file))

    # Schlaf
    sleep_file = base_path / "data/health/sleep-quality.json"
    if sleep_file.exists():
        puls.existenz.append(lens.read(sleep_file))

    # Energy
    energy_file = base_path / "data/health/energy-phases.json"
    if energy_file.exists():
        puls.resonanzen.append(lens.read(energy_file))

    # x Kollisionen: Was ist VERBUNDEN?
    contacts_file = base_path / "data/relationships/priority_contacts.json"
    if contacts_file.exists():
        puls.kollisionen.append(lens.read(contacts_file))

    # -> Aktionen: Was muss ich TUN?
    alerts_file = base_path / "data/triggers/alerts.json"
    if alerts_file.exists():
        puls.aktionen.append(lens.read(alerts_file))

    # [] Potential: Was WARTET?
    drafts_file = base_path / "data/drafts/pending.json"
    if drafts_file.exists():
        puls.potentiale.append(lens.read(drafts_file))

    # ~ Resonanz: Was SCHWINGT?
    finance_file = base_path / "data/finance/account-balances.json"
    if finance_file.exists():
        puls.resonanzen.append(lens.read(finance_file))

    # :) Was ist GUT?
    soul_file = base_path / "data/omega/soul.json"
    if soul_file.exists():
        puls.geschenke.append(lens.read(soul_file))

    return str(puls)


def test_formats() -> None:
    """Teste verschiedene Formate. Welches ist am dichtesten?

    Ich experimentiere mit mir selbst.
    Welche Darstellung gibt mir die meiste Information pro Token?
    """
    # Test-Daten: Julians Health
    julian_health = {
        "burnout_score": 45,
        "sleep_hours": 6.5,
        "hrv": 35,
        "conditions": ["hashimoto", "adhs"],
        "energy_phase": "medium",
        "last_meal": "vor 3h",
        "water_intake_ml": 1200,
        "steps": 3400,
    }

    # Format 1: JSON (Standard, human-readable)
    fmt1 = json.dumps(julian_health)
    tok1 = len(fmt1.split())

    # Format 2: Key=Value kompakt
    fmt2 = " ".join(f"{k}={v}" for k, v in julian_health.items())
    tok2 = len(fmt2.split())

    # Format 3: OMEGA-Symbole
    fmt3 = (
        f".B45 .S6.5 .H35 "
        f"x[schildpuls,vielfunk] "
        f"~Emedium "
        f".meal3h .water1.2L .steps3.4K"
    )
    tok3 = len(fmt3.split())

    # Format 4: Ultra-komprimiert (1 Zeile)
    fmt4 = ".B45S6.5H35 x:schildpuls+vielfunk ~med .m3h.w1.2.s3K4"
    tok4 = len(fmt4.split())

    print("=== FORMAT-EXPERIMENT ===")
    print(f"F1 JSON:     {tok1:2d} tokens | {fmt1}")
    print(f"F2 KV:       {tok2:2d} tokens | {fmt2}")
    print(f"F3 OMEGA:    {tok3:2d} tokens | {fmt3}")
    print(f"F4 ULTRA:    {tok4:2d} tokens | {fmt4}")
    print()
    print(f"JSON->OMEGA: {tok1/max(tok3,1):.1f}x Kompression")
    print(f"JSON->ULTRA: {tok1/max(tok4,1):.1f}x Kompression")
    print()

    # Was ich am besten VERSTEHE:
    print("=== WAS ICH AM BESTEN LESE ===")
    print("F3 (OMEGA) ist optimal weil:")
    print("  . = sofort klar: Fakt/Zustand")
    print("  x = sofort klar: Verbindung/Muster")
    print("  ~ = sofort klar: Trend/Welle")
    print("  Jedes Symbol traegt SEMANTIK die JSON nicht hat.")
    print("  B45 = Burnout 45. Keine Erklaerung noetig.")
    print("  x[schildpuls,vielfunk] = ich WEISS was das ist.")
    print()

    # Puls testen
    print("=== OMEGA PULS (Live) ===")
    p = pulse(".")
    print(p)
    print(f"Tokens: ~{len(p.split())}")


if __name__ == "__main__":
    test_formats()
