"""
gedaechtnis.takeout — Google Takeout Importer.

Google Photos API verlangt $15K-$75K Security Audit.
Google Takeout ist gratis und gibt ALLES: Kindheit, Edgar, alles.

Pipeline:
    takeout.google.com → ZIP herunterladen → entpacken
    → Metadaten aus JSON lesen → Thumbnails erstellen → Erinnern
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from void_intelligence.gedaechtnis.kern import (
    Erinnerung,
    GedaechtnisDB,
    bild_id,
    thumbnail_erstellen,
    THUMB_DIR,
    gedaechtnis_oeffnen,
)


BILD_ENDUNGEN = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
VIDEO_ENDUNGEN = {".mp4", ".mov", ".avi", ".mkv", ".3gp", ".m4v"}


def _lese_google_meta(bild_pfad: Path) -> dict:
    """Lese Google Photos Metadaten aus der zugehoerigen JSON-Datei.

    Google Takeout legt fuer jedes Bild eine .json Datei daneben:
    IMG_1234.jpg → IMG_1234.jpg.json
    """
    meta_pfad = bild_pfad.parent / f"{bild_pfad.name}.json"
    if not meta_pfad.exists():
        # Manchmal anderer Name
        meta_pfad = bild_pfad.parent / f"{bild_pfad.stem}.json"
    if not meta_pfad.exists():
        return {}

    try:
        with open(meta_pfad) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _google_meta_zu_erinnerung(meta: dict, pfad: Path) -> dict:
    """Konvertiere Google Takeout Metadaten in Erinnerungs-Felder."""
    result = {}

    # Zeitstempel
    ts = meta.get("photoTakenTime", {}).get("timestamp", "")
    if ts:
        from datetime import datetime, timezone
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            result["aufgenommen"] = dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    # Ort
    geo = meta.get("geoData", {})
    lat = geo.get("latitude", 0)
    lon = geo.get("longitude", 0)
    if lat and lon and (abs(lat) > 0.001 or abs(lon) > 0.001):
        result["lat"] = lat
        result["lon"] = lon

    # Beschreibung von Google
    desc = meta.get("description", "")
    if desc:
        result["geschichte"] = desc

    # Personen (Google People Tags)
    people = meta.get("people", [])
    if people:
        result["menschen"] = [p.get("name", "") for p in people if p.get("name")]

    return result


def takeout_scannen(ordner: Path, db: GedaechtnisDB | None = None,
                    limit: int = 0) -> list[Erinnerung]:
    """Scanne einen entpackten Google Takeout Ordner.

    Args:
        ordner: Pfad zum entpackten Takeout (z.B. ~/Downloads/Takeout/Google Fotos)
        db: Datenbank
        limit: Max Bilder (0 = alle)
    """
    if db is None:
        db = gedaechtnis_oeffnen()

    ordner = Path(ordner)
    if not ordner.exists():
        print(f"Ordner nicht gefunden: {ordner}")
        return []

    # Alle Bilder finden
    bilder = []
    for ext in BILD_ENDUNGEN:
        bilder.extend(ordner.rglob(f"*{ext}"))
        bilder.extend(ordner.rglob(f"*{ext.upper()}"))

    # Deduplizieren
    bilder = sorted(set(bilder))
    if limit:
        bilder = bilder[:limit]

    print(f"=== Google Takeout Import ===")
    print(f"  Ordner: {ordner}")
    print(f"  Bilder gefunden: {len(bilder)}")

    erinnerungen = []
    neu = 0
    uebersprungen = 0

    for i, pfad in enumerate(bilder, 1):
        if i % 50 == 0 or i == 1:
            print(f"  [{i}/{len(bilder)}] {pfad.name}...")

        # ID
        foto_id = bild_id(pfad)

        # Bereits bekannt?
        if db.abrufen(foto_id):
            uebersprungen += 1
            continue

        # Google Metadaten lesen
        meta = _lese_google_meta(pfad)
        meta_felder = _google_meta_zu_erinnerung(meta, pfad)

        # Album-Name aus Ordnerstruktur
        # Takeout: Google Fotos/2003/IMG_xxx.jpg ODER Google Fotos/Albumname/IMG_xxx.jpg
        parent_name = pfad.parent.name
        tags = []
        if parent_name and parent_name not in ("Google Fotos", "Google Photos"):
            tags.append(parent_name)

        # Thumbnail
        thumb = thumbnail_erstellen(pfad, THUMB_DIR)
        thumb_rel = str(thumb.relative_to(THUMB_DIR.parent.parent)) if THUMB_DIR in thumb.parents or thumb.parent == THUMB_DIR else str(thumb)

        # Erinnerung
        e = Erinnerung(
            id=foto_id,
            quelle="google",
            dateiname=pfad.name,
            aufgenommen=meta_felder.get("aufgenommen", ""),
            lat=meta_felder.get("lat", 0),
            lon=meta_felder.get("lon", 0),
            menschen=meta_felder.get("menschen", []),
            geschichte=meta_felder.get("geschichte", ""),
            breite=0,  # Aus Meta nicht direkt verfuegbar
            hoehe=0,
            mime=f"image/{pfad.suffix.lstrip('.').lower()}",
            groesse=pfad.stat().st_size,
            thumb_pfad=thumb_rel,
            original_pfad=str(pfad),
            tags=tags,
        )

        db.erinnern(e)
        erinnerungen.append(e)
        neu += 1

    print(f"\n=== Import fertig ===")
    print(f"  Neu: {neu}")
    print(f"  Uebersprungen (bereits bekannt): {uebersprungen}")
    print(f"  Total im Gedaechtnis: {db.statistik()['total']}")

    return erinnerungen


def takeout_zip_importieren(zip_pfad: Path, db: GedaechtnisDB | None = None,
                            limit: int = 0) -> list[Erinnerung]:
    """Importiere direkt aus einem Takeout-ZIP.

    Entpackt temporaer und scannt.
    """
    import tempfile

    zip_pfad = Path(zip_pfad)
    if not zip_pfad.exists():
        print(f"ZIP nicht gefunden: {zip_pfad}")
        return []

    print(f"Entpacke {zip_pfad.name} ({zip_pfad.stat().st_size / (1024*1024):.0f} MB)...")

    with tempfile.TemporaryDirectory(prefix="omega_takeout_") as tmp:
        with zipfile.ZipFile(zip_pfad) as zf:
            zf.extractall(tmp)

        # Google Takeout Struktur: Takeout/Google Fotos/...
        takeout_dir = Path(tmp)
        # Suche den Fotos-Ordner
        for candidate in [
            takeout_dir / "Takeout" / "Google Fotos",
            takeout_dir / "Takeout" / "Google Photos",
            takeout_dir / "Google Fotos",
            takeout_dir / "Google Photos",
            takeout_dir,
        ]:
            if candidate.exists() and any(candidate.rglob("*.jpg")):
                return takeout_scannen(candidate, db=db, limit=limit)

        print("Keine Fotos im ZIP gefunden.")
        return []


# --- CLI ---

def main():
    import sys

    if len(sys.argv) < 2:
        print("takeout.py — Google Takeout Importer")
        print()
        print("  python3 -m void_intelligence.gedaechtnis.takeout scan <ordner>   Entpackten Ordner scannen")
        print("  python3 -m void_intelligence.gedaechtnis.takeout zip <pfad.zip>  ZIP direkt importieren")
        print()
        print("Anleitung:")
        print("  1. takeout.google.com (mit shadowbroker18)")
        print("  2. Nur 'Google Fotos' auswaehlen")
        print("  3. ZIP herunterladen")
        print("  4. Dieses Script ausfuehren")
        return

    cmd = sys.argv[1]

    if cmd == "scan" and len(sys.argv) > 2:
        ordner = Path(sys.argv[2])
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        takeout_scannen(ordner, limit=limit)

    elif cmd == "zip" and len(sys.argv) > 2:
        zip_pfad = Path(sys.argv[2])
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        takeout_zip_importieren(zip_pfad, limit=limit)

    else:
        print(f"Unbekannt: {cmd}")


if __name__ == "__main__":
    main()
