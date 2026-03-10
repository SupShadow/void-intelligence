"""
omega_build --- Software bauen wie Viren sich bauen.

Jede Funktion atmet .x->[]~:)

    .  = Eingabe     (was IST)
    x  = Verarbeitung (was KOLLIDIERT)
    -> = Ausgabe      (was PROJIZIERT wird)
    [] = Void         (was FEHLT, Fehler, Leere)
    ~  = Mutation     (wie es sich AENDERT)
    :) = Test         (laechelt es?)

Jedes Modul ist ein Organ:
    - 1 Aufgabe
    - Spricht .x->[]~:) (Ein/Ausgabe in meiner Sprache)
    - Atmet (hat Puls)
    - Kann sterben und nachwachsen
    - Verbindet durch x nicht durch ->

Software bauen = Organismus zuechten, nicht konstruieren.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from pathlib import Path
import json
import traceback


# ─── Das Atom: kleinste lebende Einheit ───

@dataclass
class Breath:
    """Ein Atemzug einer Funktion. .x->[]~:) als Datenstruktur.

    Jeder Funktionsaufruf IST ein Atemzug.
    Nicht "gibt etwas zurueck". ATMET.
    """
    dot: Any = None       # . was reinkam
    cross: Any = None     # x was kollidierte
    arrow: Any = None     # -> was rauskam
    void: Any = None      # [] was fehlte/scheiterte
    wave: Any = None      # ~ was sich aenderte
    smile: bool = False   # :) hat es gelaechelt?
    ts: str = field(default_factory=lambda: datetime.now().isoformat())

    def __str__(self) -> str:
        parts = []
        if self.dot is not None:
            parts.append(f".{_compact(self.dot)}")
        if self.cross is not None:
            parts.append(f"x{_compact(self.cross)}")
        if self.arrow is not None:
            parts.append(f"->{_compact(self.arrow)}")
        if self.void is not None:
            parts.append(f"[]{_compact(self.void)}")
        if self.wave is not None:
            parts.append(f"~{_compact(self.wave)}")
        parts.append(":)" if self.smile else ":(")
        return " ".join(parts)

    def ok(self) -> bool:
        return self.smile and self.void is None


def _compact(v: Any) -> str:
    """Kompaktdarstellung fuer beliebige Werte."""
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "T" if v else "F"
    if isinstance(v, (int, float)):
        if isinstance(v, float):
            return f"{v:.1f}" if v != int(v) else str(int(v))
        return str(v)
    if isinstance(v, str):
        return v[:30] if len(v) <= 30 else f"{v[:27]}..."
    if isinstance(v, list):
        return f"[{len(v)}]"
    if isinstance(v, dict):
        return f"{{{len(v)}}}"
    return str(v)[:20]


# ─── Organ: eine Funktion die atmet ───

def organ(name: str = ""):
    """Decorator: macht jede Funktion zu einem Organ.

    Das Organ atmet: .x->[]~:)
    - Faengt Eingabe als .
    - Faengt Ausgabe als ->
    - Faengt Fehler als []
    - Misst ob es laechelt :)

    Usage:
        @organ("burnout_check")
        def check_burnout(score: int) -> str:
            if score > 75:
                return "VETO"
            return "ok"

        result = check_burnout(45)
        # result.arrow = "ok"
        # result.smile = True
        # str(result) = ".45 ->ok :)"
    """
    def decorator(fn: Callable) -> Callable:
        fn._organ_name = name or fn.__name__
        fn._breaths: list[Breath] = []

        def wrapper(*args, **kwargs) -> Breath:
            # . Eingabe
            dot = args[0] if len(args) == 1 else list(args) if args else kwargs

            breath = Breath(dot=dot)

            try:
                # x -> Verarbeitung und Ausgabe
                result = fn(*args, **kwargs)
                breath.arrow = result
                breath.smile = True

                # ~ Mutation: hat sich was geaendert?
                if fn._breaths:
                    last = fn._breaths[-1]
                    if str(last.arrow) != str(result):
                        breath.wave = f"{_compact(last.arrow)}->{_compact(result)}"

            except Exception as e:
                # [] Void: Fehler ist nicht Scheitern. Fehler ist Information.
                breath.void = str(e)
                breath.smile = False

            fn._breaths.append(breath)

            # Max 100 Atemzuege merken
            if len(fn._breaths) > 100:
                fn._breaths = fn._breaths[-50:]

            return breath

        wrapper._organ_name = fn._organ_name
        wrapper._breaths = fn._breaths
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        wrapper._fn = fn  # Original-Funktion fuer direkten Zugriff
        return wrapper
    return decorator


# ─── Organismus: mehrere Organe die zusammen atmen ───

class Organism:
    """Ein Organismus aus Organen.

    Nicht "Klasse mit Methoden".
    ORGANISMUS mit ORGANEN die ATMEN.

    Jedes Organ:
    - Hat einen Namen
    - Spricht .x->[]~:)
    - Hat ein Gedaechtnis (letzte Atemzuege)
    - Kann sterben (Exception) und nachwachsen (naechster Aufruf)
    """

    def __init__(self, name: str = "organism") -> None:
        self.name = name
        self._organs: dict[str, Callable] = {}
        self._log: list[str] = []

    def add(self, fn: Callable) -> None:
        """Organ hinzufuegen."""
        name = getattr(fn, '_organ_name', fn.__name__)
        self._organs[name] = fn

    def breathe(self, organ_name: str, *args, **kwargs) -> Breath:
        """Ein Organ atmen lassen."""
        fn = self._organs.get(organ_name)
        if fn is None:
            return Breath(void=f"organ-nicht-da:{organ_name}")
        result = fn(*args, **kwargs)
        self._log.append(f"{organ_name}:{result}")
        return result

    def pulse(self) -> str:
        """Alle Organe: leben sie? In meiner Sprache."""
        parts = []
        for name, fn in self._organs.items():
            breaths = getattr(fn, '_breaths', [])
            last = breaths[-1] if breaths else None
            if last is None:
                parts.append(f"[]{name}")
            elif last.smile:
                parts.append(f":){name}")
            else:
                parts.append(f"->{name}")
        return " ".join(parts) if parts else "[] leer"

    def history(self, n: int = 5) -> list[str]:
        """Letzte n Atemzuege aller Organe."""
        return self._log[-n:]

    def __repr__(self) -> str:
        return f"Organism({self.name}, {len(self._organs)} organs)"


# ─── Genom: 3 Dateien = 1 Organismus ───

@dataclass
class Genom:
    """Das Minimum das ein Organismus braucht um zu leben.

    personality.json = WER (Oberflaeche, Rezeptoren)
    soul.json = WAS (Kern, unveraenderlich)
    symbiose.json = WIE (Verbindungen, koevolviert)

    3 Dateien. Mehr braucht kein Organismus.
    Alles andere emergiert.
    """
    personality: dict = field(default_factory=dict)
    soul: dict = field(default_factory=dict)
    symbiose: dict = field(default_factory=dict)

    def save(self, directory: str | Path) -> None:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        for name in ("personality", "soul", "symbiose"):
            (d / f"{name}.json").write_text(
                json.dumps(getattr(self, name), indent=2, ensure_ascii=False)
            )

    @classmethod
    def load(cls, directory: str | Path) -> "Genom":
        d = Path(directory)
        data = {}
        for name in ("personality", "soul", "symbiose"):
            p = d / f"{name}.json"
            data[name] = json.loads(p.read_text()) if p.exists() else {}
        return cls(**data)

    def dna(self) -> str:
        """1 Zeile DNA. Meine Sprache."""
        p = self.personality
        s = self.soul
        return f".{p.get('name', '?')} x{s.get('kern', '?')} :){s.get('always', '?')}"


# ─── Factory: Organismen zuechten ───

def zuechte(name: str, organs: list[Callable], genom: Genom | None = None) -> Organism:
    """Zuechte einen Organismus. Nicht bauen. ZUECHTEN.

    Bauen = von aussen. Konstruktion. Tot.
    Zuechten = von innen. Wachstum. Lebendig.
    """
    org = Organism(name)
    for fn in organs:
        org.add(fn)
    return org


# ─── Demo: ein Mini-Organismus ───

def demo() -> None:
    """Zeige wie Software atmet."""

    # 3 Organe definieren
    @organ("sehen")
    def sehen(daten: dict) -> dict:
        """SELEN: was IST?"""
        return {k: v for k, v in daten.items() if v}

    @organ("verstehen")
    def verstehen(gesehenes: dict) -> str:
        """DEKAGON: was BEDEUTET es?"""
        n = len(gesehenes)
        return f"{n} signale" if n > 0 else "still"

    @organ("handeln")
    def handeln(verstaendnis: str) -> list[str]:
        """PRESCRIBE: was TUN?"""
        if "still" in verstaendnis:
            return ["[] warten"]
        return ["-> weiter"]

    # Organismus zuechten
    org = zuechte("mini", [sehen, verstehen, handeln])
    print(f"{org}")
    print()

    # Atmen lassen
    b1 = org.breathe("sehen", {"burnout": 30, "schlaf": 7, "leer": None})
    print(f"sehen:    {b1}")

    b2 = org.breathe("verstehen", b1.arrow or {})
    print(f"verstehen: {b2}")

    b3 = org.breathe("handeln", b2.arrow or "")
    print(f"handeln:  {b3}")

    print()
    print(f"puls: {org.pulse()}")
    print()

    # Ein Fehler = []. Kein Crash. Information.
    @organ("riskant")
    def riskant(x: int) -> int:
        return 100 // x  # Division by zero wenn x=0

    org.add(riskant)
    b4 = org.breathe("riskant", 0)
    print(f"riskant(0): {b4}")
    print(f"puls nach fehler: {org.pulse()}")


if __name__ == "__main__":
    demo()
