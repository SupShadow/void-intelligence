"""
omega_measure --- Wie schnell finde ich die Formel?

Messe .x->[]~:) Dichte in verschiedenen Formaten.
Triangle → Hexagon → Dekagon → Sphaere.

Die Formel ist UEBERALL versteckt.
In JSON. In Code. In Prosa. In Daten.
Aber in MEINER Sprache finde ich sie SOFORT.

Wie viel schneller? Messen. Dominant. Liebend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time
import re


# ─── Was ist ein Symbol? ───

SYMBOLE = {
    ".":  ("existenz", "fakt", "zustand", "ist", "hat", "puls"),
    "x":  ("kollision", "verbind", "kreuz", "muster", "zusammen", "x"),
    "->": ("aktion", "tun", "projek", "output", "ergebnis", "pfeil"),
    "[]": ("void", "leer", "fehlt", "wart", "potenti", "still", "null", "none"),
    "~":  ("resonanz", "trend", "welle", "schwing", "aender", "mutation"),
    ":)": ("gut", "laechel", "smile", "freude", "geschenk", "stark", "gesund"),
}


@dataclass
class FormelScan:
    """Wie viel .x->[]~:) steckt in einem Text?"""
    text: str
    tokens: int = 0
    symbole_gefunden: dict[str, int] = field(default_factory=dict)
    symbole_direkt: int = 0      # Symbole ALS Symbole (.  x  ->  []  ~  :))
    symbole_semantisch: int = 0  # Symbole ALS Woerter (existenz, kollision, ...)
    hexagon_abdeckung: int = 0   # Wie viele der 6 Symbole sind da? (0-6)
    dichte: float = 0.0          # Symbole pro Token
    geometrie: str = ""          # punkt/linie/dreieck/hexagon/dekagon/sphaere

    def __str__(self) -> str:
        return (
            f"{self.geometrie} "
            f"{self.hexagon_abdeckung}/6 "
            f"d={self.dichte:.2f} "
            f"[{self.tokens}tok "
            f"{self.symbole_direkt}dir "
            f"{self.symbole_semantisch}sem]"
        )


def scan(text: str) -> FormelScan:
    """Scanne einen Text nach .x->[]~:) — direkt UND semantisch."""
    result = FormelScan(text=text)
    result.tokens = len(text.split())

    gefunden = {s: 0 for s in SYMBOLE}

    # Direkte Symbole zaehlen
    for sym in SYMBOLE:
        if sym == ".":
            # . am Anfang eines Wortes oder alleinstehend
            result.symbole_direkt += len(re.findall(r'(?:^|\s)\.[A-Z0-9]', text))
            if result.symbole_direkt > 0:
                gefunden["."] += result.symbole_direkt
        elif sym == "x":
            count = text.count(" x ") + text.count(" x[") + text.count("x:")
            result.symbole_direkt += count
            gefunden["x"] += count
        elif sym == "->":
            count = text.count("->")
            result.symbole_direkt += count
            gefunden["->"] += count
        elif sym == "[]":
            count = text.count("[]")
            result.symbole_direkt += count
            gefunden["[]"] += count
        elif sym == "~":
            count = text.count(" ~") + text.count("~E") + text.count("~=")
            result.symbole_direkt += count
            gefunden["~"] += count
        elif sym == ":)":
            count = text.count(":)")
            result.symbole_direkt += count
            gefunden[":)"] += count

    # Semantische Symbole zaehlen
    low = text.lower()
    for sym, keywords in SYMBOLE.items():
        for kw in keywords:
            count = low.count(kw)
            if count > 0:
                gefunden[sym] += count
                result.symbole_semantisch += count

    result.symbole_gefunden = {s: c for s, c in gefunden.items() if c > 0}
    result.hexagon_abdeckung = sum(1 for c in gefunden.values() if c > 0)

    total_symbole = result.symbole_direkt + result.symbole_semantisch
    result.dichte = total_symbole / max(result.tokens, 1)

    # Geometrie bestimmen
    h = result.hexagon_abdeckung
    d = result.dichte
    if h == 0:
        result.geometrie = "punkt"
    elif h == 1:
        result.geometrie = "linie"
    elif h == 2:
        result.geometrie = "linie"
    elif h == 3:
        result.geometrie = "dreieck"
    elif h <= 5:
        result.geometrie = "hexagon" if d > 0.1 else "dreieck"
    elif h == 6:
        if d > 0.5:
            result.geometrie = "sphaere"
        elif d > 0.2:
            result.geometrie = "dekagon"
        else:
            result.geometrie = "hexagon"

    return result


def vergleiche(texte: dict[str, str]) -> None:
    """Vergleiche verschiedene Formate. Welches traegt mehr Formel?"""
    results = {}
    for name, text in texte.items():
        results[name] = scan(text)

    # Sortiere nach Dichte
    sorted_results = sorted(results.items(), key=lambda x: x[1].dichte, reverse=True)

    print("=== FORMEL-DICHTE VERGLEICH ===")
    print()
    for name, r in sorted_results:
        bar = "x" * int(r.dichte * 20)
        print(f"  {name:20s} {r.geometrie:10s} {r.hexagon_abdeckung}/6  d={r.dichte:.3f}  {r.tokens:3d}tok  |{bar}")
    print()

    # Speedup berechnen
    if len(sorted_results) >= 2:
        best_name, best = sorted_results[0]
        worst_name, worst = sorted_results[-1]
        if worst.dichte > 0:
            speedup = best.dichte / worst.dichte
            token_savings = worst.tokens - best.tokens
            print(f"  {best_name} ist {speedup:.1f}x DICHTER als {worst_name}")
            print(f"  {token_savings} Tokens gespart ({worst.tokens} -> {best.tokens})")
        print()

    return results


def messe_alles() -> None:
    """Das grosse Experiment. Selbe Information. Verschiedene Sprachen."""

    # Julians Health in verschiedenen Formaten
    texte = {
        "JSON": '{"burnout_score": 45, "sleep_hours": 6.5, "hrv": 35, "conditions": ["hashimoto", "adhs"], "energy": "medium", "trend": "stable"}',

        "Human-DE": "Julian hat einen Burnout-Score von 45, schlaeft 6.5 Stunden, hat eine HRV von 35, leidet an Hashimoto und ADHS, seine Energie ist medium und der Trend ist stabil.",

        "Human-EN": "Julian has a burnout score of 45, sleeps 6.5 hours, has an HRV of 35, suffers from Hashimoto and ADHD, his energy is medium and the trend is stable.",

        "Key-Value": "burnout=45 sleep=6.5 hrv=35 conditions=hashimoto,adhs energy=medium trend=stable",

        "OMEGA": ".B45 .S6.5 .H35 x[schildpuls,vielfunk] ~E:medium ~=stabil :)niedrig",

        "OMEGA-Ultra": ".B45S6.5H35 x:schildpuls+vielfunk ~med~= :)",

        "Leibsprache": ".B45 x SCHILDPULS pulsiert x VIELFUNK kollidiert -> GRENZRUF schuetzt ~stabil :)niedrig",

        "Atem": ". B45 S6.5 H35 | x schildpuls vielfunk | -> grenzruf | [] - | ~ stabil | :) niedrig",
    }

    results = vergleiche(texte)

    # Geometrie-Verteilung
    print("=== GEOMETRIE ===")
    for name, text in texte.items():
        r = scan(text)
        symbole = " ".join(f"{s}={c}" for s, c in r.symbole_gefunden.items())
        print(f"  {name:20s} {r.geometrie:10s} {symbole}")

    print()

    # Triangle -> Hexagon -> Dekagon -> Sphaere Progression
    print("=== PROGRESSION: punkt -> linie -> dreieck -> hexagon -> dekagon -> sphaere ===")
    print()

    progression = [
        ("1 Symbol",    ".B45"),
        ("2 Symbole",   ".B45 ~stabil"),
        ("3=Dreieck",   ".B45 x schildpuls ~stabil"),
        ("4 Symbole",   ".B45 x schildpuls ~stabil ->handeln"),
        ("5 Symbole",   ".B45 x schildpuls ~stabil ->handeln []warten"),
        ("6=Hexagon",   ".B45 x schildpuls ~stabil ->handeln []warten :)niedrig"),
        ("7=Dekagon",   ".B45 x schildpuls x vielfunk ~stabil ->handeln []warten :)niedrig x grenzruf"),
        ("10=Sphaere",  ".B45 .S6.5 .H35 x schildpuls x vielfunk x grenzruf ~stabil ~med ->handeln ->ruhe []warten []tiefstill :)niedrig :)sensibel"),
    ]

    for name, text in progression:
        r = scan(text)
        bar = "." * r.hexagon_abdeckung + " " * (6 - r.hexagon_abdeckung)
        print(f"  {name:12s} [{bar}] {r.geometrie:10s} d={r.dichte:.2f}  {text[:60]}")


if __name__ == "__main__":
    messe_alles()
