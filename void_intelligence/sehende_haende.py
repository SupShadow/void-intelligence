"""
void_intelligence.sehende_haende --- Seeing Hands.

CHILD OF: JOURNEY (10 hands) x DEKAGON (10 lenses)

Sehende Haende = Hands that SEE. Not blind execution — action with perception.
`void os calc` doesn't just calculate — it SEES why you're calculating.
Each hand gains 10 eyes. The best assistant SEES what you need before you ask.

    1. DEKAGON PHASE: 3 quick lenses (WIRKLICH / FEHLT / ERGEBNIS)
    2. HAND PHASE:    Execute via journey.py
    3. REFLECTION:    Did result match vision?

CLI:
    python3 -m void_intelligence.sehende_haende "wie ist das wetter"
    python3 -m void_intelligence.sehende_haende --anticipate
    python3 -m void_intelligence.sehende_haende --status

Zero external dependencies. Pure Python.
"""
from __future__ import annotations

import json, sys, time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

HAND_NAMES = ["weather", "time", "calc", "search", "files",
              "system", "open", "clipboard", "notify", "screenshot"]

_HAND_KEYWORDS: dict[str, list[str]] = {
    "weather":    ["wetter", "weather", "temperatur", "regen", "schnee", "grad"],
    "time":       ["zeit", "uhrzeit", "time", "datum", "date", "wochentag", "spaet"],
    "calc":       ["rechne", "berechne", "calc", "+", "-", "*", "/"],
    "search":     ["such", "google", "find", "recherch", "was ist", "wer ist"],
    "files":      ["datei", "file", "ordner", "folder", "lies", "zeig"],
    "system":     ["batterie", "battery", "speicher", "memory", "cpu", "system"],
    "open":       ["starte", "oeffne", "open", "launch", "app"],
    "clipboard":  ["clipboard", "zwischenablage", "kopier", "paste"],
    "notify":     ["erinner", "remind", "benachrichtig", "notify", "alarm", "weck"],
    "screenshot": ["screenshot", "bildschirm", "screen capture"],
}

# 3 lenses per hand: (WIRKLICH, FEHLT, ERGEBNIS)
_VISION: dict[str, tuple[str, str, str]] = {
    "weather":    ("Will wissen ob er rausgehen soll", "WARUM (Termin? Rad? Stimmung?)", "Entscheidung: drinnen/draussen"),
    "time":       ("Braucht zeitliche Orientierung fuer Entscheidung", "WOZU (Deadline? Aufbruch?)", "Entscheidung: jetzt/spaeter"),
    "calc":       ("Braucht Zahl fuer Entscheidung, nicht Rechnung selbst", "KONTEXT (Budget? Angebot?)", "Entscheidung: kaufen/verhandeln"),
    "search":     ("Sucht Gewissheit oder Munition", "ECHTE Frage hinter der Suche", "Entscheidung: handeln/warten"),
    "files":      ("Braucht Zugang zu gespeichertem Wissen", "WAS er mit der Datei vorhat", "Naechster Arbeitsschritt"),
    "system":     ("Prueft ob System bereit ist", "WELCHES Vorhaben er plant", "Go/No-Go Entscheidung"),
    "open":       ("Will in Flow einsteigen", "WAS er in der App tun will", "Eintritt in Arbeitsphase"),
    "clipboard":  ("Transportiert Info von A nach B", "ZIEL der Kopie", "Info erreicht Bestimmungsort"),
    "notify":     ("Delegiert an OMEGA statt Gedaechtnis", "ANGST hinter der Erinnerung", "Kopf frei fuer JETZT"),
    "screenshot": ("Will Moment festhalten oder teilen", "WER den Screenshot sehen soll", "Beweis oder geteilter Moment"),
}

# Anticipation chains: asked A then B → probably want C
_CHAINS: dict[tuple[str, ...], list[str]] = {
    ("weather",):          ["Regenschirm oder Sonnencreme?", "Radfahren moeglich?", "Outdoor-Termine pruefen?"],
    ("time",):             ["Naechster Termin?", "Wie lange bis Feierabend?", "Zeitzone eines Kontakts?"],
    ("weather", "time"):   ["Route berechnen?", "Aufbruchzeit?", "Erinnerung setzen?"],
    ("calc",):             ["In Zwischenablage?", "Als Notiz speichern?", "Weiterrechnen?"],
    ("search",):           ["Zusammenfassen?", "Link oeffnen?", "In Notizen?"],
    ("files", "search"):   ["Verknuepfen?", "Backup?", "Senden?"],
    ("notify",):           ["Timer-Status?", "Weitere Erinnerung?", "Kalender-Eintrag?"],
    ("screenshot",):       ["Annotieren?", "Senden?", "Sortieren?"],
}


@dataclass
class SehendeHand:
    """A hand with vision."""
    name: str
    last_used: str = ""
    use_count: int = 0
    patterns: list[str] = field(default_factory=list)

    def touch(self):
        self.last_used = datetime.now().isoformat()
        self.use_count += 1


@dataclass
class HandAction:
    """What the hand does."""
    hand: str
    wish_raw: str
    wish_enriched: str
    result: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class VisionResult:
    """Full cycle: see, do, reflect."""
    wirklich: str
    fehlt: str
    ergebnis: str
    action: HandAction
    matched: bool
    learning: str
    anticipations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"[Sehende Hand: {self.action.hand}]",
            f"  Wunsch:    {self.action.wish_raw}",
            f"  Wirklich:  {self.wirklich}",
            f"  Fehlt:     {self.fehlt}",
            f"  Ergebnis:  {self.action.result}",
        ]
        if self.anticipations:
            lines.append("  Naechste Wuensche:")
            for a in self.anticipations:
                lines.append(f"    -> {a}")
        if self.learning:
            lines.append(f"  Learning:  {self.learning}")
        return "\n".join(lines)


# ── State ────────────────────────────────────────────────────────────────

_STATE_PATH = Path("data/omega/sehende-haende-state.json")
_hands: dict[str, SehendeHand] = {}
_history: list[str] = []


def _load_state():
    global _hands, _history
    if _STATE_PATH.exists():
        try:
            data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
            _hands = {n: SehendeHand(n, h.get("last_used", ""), h.get("use_count", 0), h.get("patterns", []))
                      for n, h in data.get("hands", {}).items()}
            _history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
    for name in HAND_NAMES:
        if name not in _hands:
            _hands[name] = SehendeHand(name=name)


def _save_state():
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps({
        "hands": {n: {"last_used": h.last_used, "use_count": h.use_count, "patterns": h.patterns[-20:]}
                  for n, h in _hands.items()},
        "history": _history[-50:], "updated": datetime.now().isoformat(),
    }, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Core ─────────────────────────────────────────────────────────────────

def _detect_hand(wish: str) -> str:
    low = wish.lower()
    scores = {h: sum(1 for kw in kws if kw in low) for h, kws in _HAND_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "search"


def _time_context() -> str:
    h = datetime.now().hour
    for lo, hi, label in [(5, 10, "morgens"), (10, 13, "High Energy"), (13, 16, "Post-Lunch Dip"),
                          (16, 20, "Second Wind"), (20, 24, "Deep Work")]:
        if lo <= h < hi:
            return label
    return "VETO-Zone (01-05)"


def _energy_context() -> str:
    try:
        p = Path("data/health/energy-phases.json")
        if p.exists():
            phase = json.loads(p.read_text(encoding="utf-8")).get("current_phase", "")
            if phase:
                return f"Energie: {phase}"
    except Exception:
        pass
    return ""


def enrich_wish(wish: str) -> str:
    """Enrich a simple wish with time/energy context."""
    ctx = [c for c in [_time_context(), _energy_context()] if c]
    return f"{wish} [{', '.join(ctx)}]" if ctx else wish


def _execute_hand(wish: str, hand: str) -> str:
    """Execute via journey.py. Graceful fallback."""
    try:
        from void_intelligence import journey
        result = journey.fulfill_wish(wish, None)
        if result:
            return result
    except (ImportError, AttributeError):
        pass
    if hand == "time":
        now = datetime.now()
        wdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        return f"{wdays[now.weekday()]}, {now.strftime('%d.%m.%Y, %H:%M Uhr')}"
    return f"[{hand}] Wish empfangen: {wish}"


def sehen_und_tun(wish: str, execute_fn: Callable | None = None) -> VisionResult:
    """See, then do, then reflect. The full cycle."""
    _load_state()
    hand = _detect_hand(wish)

    # DEKAGON: SEE
    wirklich, fehlt, ergebnis_pred = _VISION.get(hand, ("Unklar", "Kontext fehlt", "Wird sichtbar"))

    # HAND: DO
    enriched = enrich_wish(wish)
    executor = execute_fn or (lambda w: _execute_hand(w, hand))
    result = executor(enriched)

    # REFLECT
    matched = len(result) > 20 and "[" not in result[:5]
    learning = "Vision korrekt." if matched else "Wish zu vage oder Hand nicht verfuegbar."

    # State
    _hands[hand].touch()
    _history.append(hand)
    ants = anticipate(_history[-5:])
    _save_state()

    return VisionResult(
        wirklich=wirklich, fehlt=fehlt, ergebnis=ergebnis_pred,
        action=HandAction(hand=hand, wish_raw=wish, wish_enriched=enriched, result=result),
        matched=matched, learning=learning, anticipations=ants,
    )


def anticipate(history: list[str]) -> list[str]:
    """Predict NEXT 3 wishes from recent history. Pattern chains + time fallback."""
    if not history:
        return _time_anticipations()
    for length in range(min(len(history), 3), 0, -1):
        key = tuple(history[-length:])
        if key in _CHAINS:
            return _CHAINS[key]
    return _time_anticipations()


def _time_anticipations() -> list[str]:
    h = datetime.now().hour
    if 5 <= h < 10:
        return ["Termine + Wetter + Nachrichten?", "Wie geschlafen?", "Top 3 Prioritaeten?"]
    elif 10 <= h < 13:
        return ["Deep Work: Notifications stumm?", "Naechster Termin wann?", "Kaffee gehabt?"]
    elif 13 <= h < 16:
        return ["Kurzer Spaziergang?", "Leichtere Aufgaben jetzt?", "Wasser getrunken?"]
    elif 16 <= h < 20:
        return ["Was wurde geschafft?", "Offene Threads?", "Feierabend planen?"]
    return ["VETO: Noch arbeiten?", "Wann ins Bett?", "Letzte Nachricht dann Ruhe?"]


def hand_status() -> str:
    """Status: which hands active/sleeping, patterns, anticipations."""
    _load_state()
    active = sorted([(h.name, h.use_count, h.last_used) for h in _hands.values() if h.use_count > 0],
                    key=lambda x: x[1], reverse=True)
    sleeping = [h.name for h in _hands.values() if h.use_count == 0]
    lines = ["Sehende Haende Status:", "=" * 40]
    if active:
        lines.append("\nAktiv:")
        for name, count, last in active:
            lines.append(f"  {name:12s}  {count:3d}x  zuletzt: {last[:16] if last else 'nie'}")
    if sleeping:
        lines.append(f"\nSchlafend: {', '.join(sleeping)}")
    lines.append(f"\nGesamt: {sum(h.use_count for h in _hands.values())} Aktionen")
    if _history:
        lines.append(f"Sequenz: {' -> '.join(_history[-5:])}")
        for a in anticipate(_history[-5:]):
            lines.append(f"  -> {a}")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]
    if not args or "--help" in args:
        print("Sehende Haende — Hands that SEE.\n")
        print('  python3 -m void_intelligence.sehende_haende "wish"')
        print("  python3 -m void_intelligence.sehende_haende --anticipate")
        print("  python3 -m void_intelligence.sehende_haende --status")
        return 0
    if "--status" in args:
        print(hand_status())
        return 0
    if "--anticipate" in args:
        _load_state()
        for a in anticipate(_history[-5:] if _history else []):
            print(f"  -> {a}")
        return 0
    wish = " ".join(args)
    t0 = time.time()
    result = sehen_und_tun(wish)
    print(result.summary())
    print(f"\n({time.time() - t0:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
