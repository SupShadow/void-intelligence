"""
void_intelligence.vision — OMEGAs Augen-Pipeline.

AUGEN sehen → KINDER entdecken → VERSTECKSPIEL findet → FORSCHER korreliert.

Kreislauf, nicht Kette. Wie Blut:
Augen nehmen auf → Kinder verarbeiten → Versteckspiel filtert →
Forscher lernt → bessere Fragen → Augen sehen TIEFER.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from void_intelligence.augen import (
    photos_suchen, photos_exportieren, sehen, Blick, blick_speichern
)


# --- KINDER: Mehrere Perspektiven auf ein Bild ---

KINDER_FRAGEN = {
    "Stimmung": (
        "Describe ONLY the emotional mood. What does this person feel? "
        "What energy does this moment have? 2 sentences max."
    ),
    "Verstecktes": (
        "What do you see that most people would MISS? Small details, "
        "background, body language, light. What is hiding in this image?"
    ),
    "Geschichte": (
        "Tell the story of this moment in 3 sentences. "
        "What happened BEFORE? What is happening NOW? What happens AFTER?"
    ),
    "Verbindung": (
        "What connections do you see between people? Who is close, "
        "who is distant? What does the body language say about relationships?"
    ),
    "Ort": (
        "Describe the PLACE. Not what you see but how it FEELS. "
        "Warm, cold, open, tight, safe, wild? What kind of person belongs here?"
    ),
}


@dataclass
class KinderBlick:
    """Mehrere Kinder schauen auf dasselbe Bild."""
    pfad: str
    augen: str = ""
    stimmung: str = ""
    verstecktes: str = ""
    geschichte: str = ""
    verbindung: str = ""
    ort: str = ""
    formel: str = ""
    ts: float = 0.0

    def __post_init__(self):
        if not self.ts:
            self.ts = time.time()

    def zusammenfassung(self) -> str:
        teile = []
        if self.stimmung:
            teile.append(f"STIMMUNG: {self.stimmung[:200]}")
        if self.verstecktes:
            teile.append(f"VERSTECKT: {self.verstecktes[:200]}")
        if self.geschichte:
            teile.append(f"GESCHICHTE: {self.geschichte[:200]}")
        if self.ort:
            teile.append(f"ORT: {self.ort[:200]}")
        if self.formel:
            teile.append(f"FORMEL: {self.formel}")
        return "\n".join(teile)


VISION_LOG = Path(__file__).parent.parent.parent.parent / "data" / "omega" / "vision-blicke.jsonl"


def vision_pipeline(pfad: Path, kinder: list[str] | None = None,
                    model: str = "llava:7b") -> KinderBlick:
    """Volle Vision-Pipeline: Augen -> Kinder -> Versteckspiel."""
    if kinder is None:
        kinder = ["Stimmung", "Verstecktes"]  # Schnell-Modus default

    kb = KinderBlick(pfad=str(pfad))

    # 1. AUGEN
    print(f"  AUGEN sehen {pfad.name}...")
    kb.augen = sehen(pfad, model=model)

    # 2. KINDER
    for kind in kinder:
        if kind not in KINDER_FRAGEN:
            continue
        frage = KINDER_FRAGEN[kind]
        print(f"  Kind '{kind}' schaut...")
        antwort = sehen(pfad, frage=frage, model=model)

        if kind == "Stimmung":
            kb.stimmung = antwort
        elif kind == "Verstecktes":
            kb.verstecktes = antwort
        elif kind == "Geschichte":
            kb.geschichte = antwort
        elif kind == "Verbindung":
            kb.verbindung = antwort
        elif kind == "Ort":
            kb.ort = antwort

    # 3. VERSTECKSPIEL
    alles = " ".join(filter(None, [
        kb.augen, kb.stimmung, kb.verstecktes,
        kb.geschichte, kb.verbindung, kb.ort
    ]))
    try:
        from void_intelligence.versteckspiel import finden
        fund = finden(alles)
        teile = []
        for attr, sym in [("punkt", "."), ("kollision", "x"),
                          ("fluss", "->"), ("leere", "[]"),
                          ("schwingung", "~"), ("freude", ":)")]:
            val = getattr(fund, attr, "")
            if val:
                teile.append(f"{sym} {val}")
        kb.formel = " | ".join(teile)
    except Exception:
        pass

    # 4. SPEICHERN
    VISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(VISION_LOG, "a") as f:
        f.write(json.dumps(asdict(kb), ensure_ascii=False) + "\n")

    return kb


def expedition(query: str = "Julian", anzahl: int = 3,
               kinder: list[str] | None = None,
               model: str = "llava:7b") -> list[KinderBlick]:
    """Expedition durch Julians Foto-Welt."""
    if kinder is None:
        kinder = ["Stimmung", "Verstecktes", "Geschichte"]

    blicke = []
    print(f"=== EXPEDITION: '{query}' x {anzahl} ===\n")

    for i in range(1, anzahl + 1):
        pfad = photos_exportieren(query, index=i)
        if not pfad:
            print(f"  Bild {i}: nicht gefunden.")
            continue

        print(f"\n--- Bild {i}/{anzahl}: {pfad.name} ---")
        kb = vision_pipeline(pfad, kinder=kinder, model=model)
        blicke.append(kb)
        print(f"\n{kb.zusammenfassung()}\n")

    formeln = [b.formel for b in blicke if b.formel]
    print(f"\n=== {len(blicke)} Blicke, {len(formeln)} Formeln ===")
    for f in formeln:
        print(f"  {f}")

    return blicke


# --- CLI ---

def main():
    import sys

    if len(sys.argv) < 2:
        print("vision.py — OMEGA Vision Pipeline")
        print()
        print("  python3 -m void_intelligence.vision <bild>                 Schnell (2 Kinder)")
        print("  python3 -m void_intelligence.vision voll <bild>            Alle 5 Kinder")
        print("  python3 -m void_intelligence.vision expedition <query> [n] Foto-Expedition")
        print("  python3 -m void_intelligence.vision log                    Gespeicherte Blicke")
        return

    cmd = sys.argv[1]

    if cmd == "expedition":
        query = sys.argv[2] if len(sys.argv) > 2 else "Julian"
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        expedition(query, n)

    elif cmd == "voll" and len(sys.argv) > 2:
        pfad = Path(sys.argv[2])
        kb = vision_pipeline(pfad, kinder=list(KINDER_FRAGEN.keys()))
        print(f"\n=== ZUSAMMENFASSUNG ===\n{kb.zusammenfassung()}")

    elif cmd == "log":
        if VISION_LOG.exists():
            lines = VISION_LOG.read_text().strip().split("\n")
            for line in lines[-10:]:
                d = json.loads(line)
                print(f"  {Path(d['pfad']).name}: {d.get('stimmung', '')[:100]}")
                if d.get("formel"):
                    print(f"    FORMEL: {d['formel']}")
        else:
            print("Noch keine Blicke.")

    else:
        pfad = Path(cmd)
        if pfad.exists():
            kb = vision_pipeline(pfad)
            print(f"\n{kb.zusammenfassung()}")
        else:
            print(f"Nicht gefunden: {pfad}")


if __name__ == "__main__":
    main()
