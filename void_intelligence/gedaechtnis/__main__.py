"""
python3 -m void_intelligence.gedaechtnis — OMEGAs visuelles Gedaechtnis.

Nicht Speicher. ERINNERUNG.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from void_intelligence.gedaechtnis.kern import gedaechtnis_oeffnen


def main():
    if len(sys.argv) < 2:
        print("gedaechtnis — OMEGAs visuelles Gedaechtnis")
        print()
        print("  Import:")
        print("    ... gedaechtnis apple [n]           Apple Photos scannen (schnell)")
        print("    ... gedaechtnis apple-tief [n]      Apple Photos scannen (OMEGA sieht)")
        print("    ... gedaechtnis takeout <ordner>    Google Takeout importieren")
        print("    ... gedaechtnis takeout-zip <zip>   Google Takeout ZIP importieren")
        print()
        print("  Suche:")
        print("    ... gedaechtnis suchen <text>       Volltextsuche")
        print("    ... gedaechtnis zeit <jahr> [monat] Zeitreise")
        print("    ... gedaechtnis menschen            Alle erkannten Menschen")
        print()
        print("  Info:")
        print("    ... gedaechtnis stats               Statistik")
        print("    ... gedaechtnis info                Apple Photos Anzahl")
        print()
        return

    cmd = sys.argv[1]
    db = gedaechtnis_oeffnen()

    try:
        if cmd == "apple":
            from void_intelligence.gedaechtnis.scanner import schnell_scan
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            schnell_scan(batch=n, db=db)

        elif cmd == "apple-tief":
            from void_intelligence.gedaechtnis.scanner import tief_scan
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            tief_scan(start=start, batch=n, db=db)

        elif cmd == "takeout" and len(sys.argv) > 2:
            from void_intelligence.gedaechtnis.takeout import takeout_scannen
            ordner = Path(sys.argv[2])
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            takeout_scannen(ordner, db=db, limit=limit)

        elif cmd == "takeout-zip" and len(sys.argv) > 2:
            from void_intelligence.gedaechtnis.takeout import takeout_zip_importieren
            zip_pfad = Path(sys.argv[2])
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            takeout_zip_importieren(zip_pfad, db=db, limit=limit)

        elif cmd == "suchen" and len(sys.argv) > 2:
            text = " ".join(sys.argv[2:])
            ergebnisse = db.suchen(text=text)
            if not ergebnisse:
                print(f"Nichts gefunden fuer '{text}'.")
            else:
                print(f"=== {len(ergebnisse)} Erinnerungen fuer '{text}' ===\n")
                for e in ergebnisse:
                    print(f"  {e.kurz()}")
                    if e.beschreibung:
                        print(f"    {e.beschreibung[:120]}...")
                    print()

        elif cmd == "zeit" and len(sys.argv) > 2:
            jahr = int(sys.argv[2])
            monat = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            ergebnisse = db.zeitreise(jahr, monat)
            label = f"{jahr}" + (f"/{monat:02d}" if monat else "")
            if not ergebnisse:
                print(f"Keine Erinnerungen aus {label}.")
            else:
                print(f"=== ZEITREISE: {label} — {len(ergebnisse)} Erinnerungen ===\n")
                for e in ergebnisse:
                    print(f"  {e.kurz()}")
                    if e.beschreibung:
                        print(f"    {e.beschreibung[:120]}...")
                    print()

        elif cmd == "menschen":
            menschen = db.menschen_liste()
            if not menschen:
                print("Noch keine Menschen erkannt.")
            else:
                print(f"=== {len(menschen)} Menschen ===")
                for m in sorted(menschen, key=lambda x: x["anzahl"], reverse=True):
                    print(f"  {m['name']} ({m['anzahl']} Erinnerungen)")

        elif cmd == "stats":
            stats = db.statistik()
            print(f"=== OMEGA Visuelles Gedaechtnis ===")
            print(f"  Erinnerungen: {stats['total']:,}")
            print(f"  Speicher: {stats['speicher_mb']:.1f} MB (Thumbnails)")
            if stats["quellen"]:
                print(f"  Quellen: {', '.join(f'{k}={v}' for k, v in stats['quellen'].items())}")
            if stats["jahre"]:
                print(f"  Jahre:")
                for jahr, n in sorted(stats["jahre"].items()):
                    print(f"    {jahr}: {n:,} Erinnerungen")
            print(f"  Menschen: {stats['menschen']}")
            print(f"  Geschichten: {stats['geschichten']}")

        elif cmd == "info":
            from void_intelligence.gedaechtnis.scanner import photos_anzahl
            n = photos_anzahl()
            print(f"Julian hat {n:,} Fotos in Apple Photos.")
            stats = db.statistik()
            print(f"OMEGA erinnert sich an {stats['total']:,} davon.")

        else:
            print(f"Unbekannt: {cmd}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
