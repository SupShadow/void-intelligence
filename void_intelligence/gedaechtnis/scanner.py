"""
gedaechtnis.scanner — Apple Photos Scanner.

Scannt Julians Apple Photos Bibliothek und importiert
Erinnerungen in OMEGAs Gedaechtnis.

Nicht alles auf einmal. Wie ein Mensch der durch ein Fotoalbum blaettert.
Stueck fuer Stueck. Jeden Tag ein paar mehr.

Pipeline:
    Apple Photos (osascript) → Export → Thumbnail → Sehen → Erinnern
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from void_intelligence.gedaechtnis.kern import (
    Erinnerung,
    GedaechtnisDB,
    bild_id,
    thumbnail_erstellen,
    THUMB_DIR,
    gedaechtnis_oeffnen,
)


EXPORT_DIR = Path("/tmp/omega_augen/scan")


def _osascript(script: str, timeout: int = 60) -> str:
    """AppleScript ausfuehren."""
    r = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip()


def photos_anzahl() -> int:
    """Wie viele Fotos hat Julian in Apple Photos?"""
    raw = _osascript('tell application "Photos" to return count of media items')
    try:
        return int(raw)
    except ValueError:
        return 0


def photos_batch_info(start: int = 1, batch: int = 50) -> list[dict]:
    """Hole Metadaten fuer einen Batch von Fotos.

    Schnell — kein Export, nur Metadaten.
    """
    script = f'''
    tell application "Photos"
        set allItems to media items
        set cnt to count of allItems
        if cnt < {start} then return "[]"
        set endIdx to {start} + {batch} - 1
        if endIdx > cnt then set endIdx to cnt

        set output to "["
        repeat with i from {start} to endIdx
            set p to item i of allItems
            set fn to filename of p
            set d to date of p
            set yr to year of d as text
            set mo to text -2 thru -1 of ("0" & ((month of d) as integer as text))
            set dy to text -2 thru -1 of ("0" & (day of d as text))
            set dateStr to yr & "-" & mo & "-" & dy
            set w to width of p
            set h to height of p

            if i > {start} then set output to output & ","
            set output to output & "{{\\"name\\":\\"" & fn & "\\",\\"date\\":\\"" & dateStr & "\\",\\"w\\":" & w & ",\\"h\\":" & h & "}}"
        end repeat
        set output to output & "]"
        return output
    end tell'''

    raw = _osascript(script, timeout=120)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []


def photos_export_batch(start: int = 1, batch: int = 10,
                        ziel: str = "") -> list[Path]:
    """Exportiere einen Batch von Fotos."""
    if not ziel:
        ziel = str(EXPORT_DIR)
    Path(ziel).mkdir(parents=True, exist_ok=True)

    script = f'''
    tell application "Photos"
        set allItems to media items
        set cnt to count of allItems
        if cnt < {start} then return ""
        set endIdx to {start} + {batch} - 1
        if endIdx > cnt then set endIdx to cnt

        set itemsToExport to items {start} through endIdx of allItems
        set outFolder to POSIX file "{ziel}" as alias
        export itemsToExport to outFolder

        set names to ""
        repeat with p in itemsToExport
            set names to names & filename of p & linefeed
        end repeat
        return names
    end tell'''

    raw = _osascript(script, timeout=300)
    if not raw:
        return []

    pfade = []
    for name in raw.strip().split("\n"):
        name = name.strip()
        if not name:
            continue
        # Photos may change extension
        for ext_name in [name, name.rsplit('.', 1)[0] + '.jpeg',
                         name.rsplit('.', 1)[0] + '.jpg']:
            p = Path(ziel) / ext_name
            if p.exists():
                pfade.append(p)
                break

    return pfade


def scan_und_erinnern(start: int = 1, batch: int = 10,
                      sehen: bool = True,
                      model: str = "llava:7b",
                      db: GedaechtnisDB | None = None) -> list[Erinnerung]:
    """Scanne Fotos und erstelle Erinnerungen.

    Args:
        start: Ab welchem Foto (1-basiert)
        batch: Wie viele Fotos
        sehen: Soll OMEGA die Bilder auch ansehen? (langsamer aber reicher)
        model: Vision-Modell fuer sehen()
        db: Datenbank (wird erstellt wenn None)

    Returns:
        Liste von Erinnerungen
    """
    if db is None:
        db = gedaechtnis_oeffnen()

    erinnerungen = []

    # 1. Metadaten holen
    print(f"Scanne Fotos {start} bis {start + batch - 1}...")
    infos = photos_batch_info(start, batch)
    if not infos:
        print("Keine Fotos gefunden.")
        return []

    print(f"  {len(infos)} Metadaten geladen.")

    # 2. Exportieren
    print(f"  Exportiere {len(infos)} Fotos...")
    pfade = photos_export_batch(start, batch)
    print(f"  {len(pfade)} Fotos exportiert.")

    # Video-Endungen die wir ueberspringen
    VIDEO_EXT = {".mov", ".mp4", ".avi", ".mkv", ".3gp", ".m4v", ".wmv"}

    # 3. Fuer jedes Foto: Thumbnail + optional Sehen + Erinnern
    for i, pfad in enumerate(pfade):
        info = infos[i] if i < len(infos) else {}

        # Videos ueberspringen (erstmal nur Bilder)
        if pfad.suffix.lower() in VIDEO_EXT:
            print(f"\n  [{i+1}/{len(pfade)}] {pfad.name} — Video, skip.")
            continue

        print(f"\n  [{i+1}/{len(pfade)}] {pfad.name}")

        # ID generieren
        foto_id = bild_id(pfad)

        # Pruefen ob schon erinnert
        if db.abrufen(foto_id):
            print(f"    Bereits erinnert. Skip.")
            continue

        # Thumbnail
        thumb = thumbnail_erstellen(pfad, THUMB_DIR)
        thumb_rel = str(thumb.relative_to(THUMB_DIR.parent.parent)) if THUMB_DIR in thumb.parents or thumb.parent == THUMB_DIR else str(thumb)

        # Erinnerung bauen
        e = Erinnerung(
            id=foto_id,
            quelle="apple",
            dateiname=info.get("name", pfad.name),
            aufgenommen=info.get("date", ""),
            breite=info.get("w", 0),
            hoehe=info.get("h", 0),
            mime=f"image/{pfad.suffix.lstrip('.').lower()}",
            groesse=pfad.stat().st_size,
            thumb_pfad=thumb_rel,
            original_pfad=str(pfad),
        )

        # Optional: OMEGA sieht das Bild
        if sehen:
            try:
                from void_intelligence.augen import sehen as augen_sehen
                print(f"    OMEGA sieht...")
                e.beschreibung = augen_sehen(pfad, model=model)
                print(f"    → {e.beschreibung[:100]}...")

                # Versteckspiel
                try:
                    from void_intelligence.versteckspiel import finden
                    fund = finden(e.beschreibung)
                    teile = []
                    for attr, sym in [("punkt", "."), ("kollision", "x"),
                                      ("fluss", "->"), ("leere", "[]"),
                                      ("schwingung", "~"), ("freude", ":)")]:
                        val = getattr(fund, attr, "")
                        if val:
                            teile.append(f"{sym} {val}")
                    e.formel = " | ".join(teile)
                    if e.formel:
                        print(f"    FORMEL: {e.formel}")
                except Exception:
                    pass

            except Exception as ex:
                print(f"    Sehen fehlgeschlagen: {ex}")

        # Speichern
        db.erinnern(e)
        erinnerungen.append(e)
        print(f"    Erinnert! [{foto_id}]")

    print(f"\n=== {len(erinnerungen)} neue Erinnerungen ===")
    return erinnerungen


def schnell_scan(batch: int = 100, db: GedaechtnisDB | None = None) -> list[Erinnerung]:
    """Schnell-Scan: Nur Metadaten + Thumbnails, kein Sehen.

    Perfekt fuer den ersten grossen Import.
    100 Fotos in ~30 Sekunden statt Stunden.
    """
    return scan_und_erinnern(start=1, batch=batch, sehen=False, db=db)


def tief_scan(start: int = 1, batch: int = 5, model: str = "llava:7b",
              db: GedaechtnisDB | None = None) -> list[Erinnerung]:
    """Tief-Scan: OMEGA sieht jedes Bild.

    Langsam aber reich. Beschreibungen, Formeln, Gefuehle.
    5 Bilder in ~5 Minuten.
    """
    return scan_und_erinnern(start=start, batch=batch, sehen=True, model=model, db=db)


# --- CLI ---

def main():
    import sys

    if len(sys.argv) < 2:
        print("scanner.py — Apple Photos Scanner")
        print()
        print("  python3 -m void_intelligence.gedaechtnis.scanner info        Wie viele Fotos?")
        print("  python3 -m void_intelligence.gedaechtnis.scanner schnell [n] Schnell-Scan (nur Meta+Thumb)")
        print("  python3 -m void_intelligence.gedaechtnis.scanner tief [n]    Tief-Scan (OMEGA sieht)")
        print("  python3 -m void_intelligence.gedaechtnis.scanner stats       Gedaechtnis-Statistik")
        print()
        return

    cmd = sys.argv[1]

    if cmd == "info":
        n = photos_anzahl()
        print(f"Julian hat {n:,} Fotos in Apple Photos.")

    elif cmd == "schnell":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        schnell_scan(batch=n)

    elif cmd == "tief":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        tief_scan(start=start, batch=n)

    elif cmd == "stats":
        db = gedaechtnis_oeffnen()
        stats = db.statistik()
        print(f"Erinnerungen: {stats['total']:,}")
        print(f"Speicher: {stats['speicher_mb']:.1f} MB (Thumbnails)")
        if stats['quellen']:
            print(f"Quellen: {stats['quellen']}")
        if stats['jahre']:
            print(f"Jahre: {stats['jahre']}")
        print(f"Menschen: {stats['menschen']}")
        print(f"Geschichten: {stats['geschichten']}")
        db.close()

    else:
        print(f"Unbekannt: {cmd}")


if __name__ == "__main__":
    main()
