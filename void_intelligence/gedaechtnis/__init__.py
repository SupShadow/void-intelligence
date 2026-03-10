"""
void_intelligence.gedaechtnis — OMEGAs visuelles Gedaechtnis.

Nicht Speicher. ERINNERUNG.
Ein Mensch speichert nicht Photonen — er speichert Bedeutung.
OMEGA speichert nicht Pixel — OMEGA speichert Blicke.

Architektur:
    ┌─────────────────────────────────────────────┐
    │  gedaechtnis.db (SQLite)                    │
    │  ├─ erinnerungen: thumbnail + beschreibung  │
    │  │                + embedding + formel       │
    │  ├─ menschen: wer ist auf welchem bild      │
    │  ├─ orte: wo wurde das bild gemacht         │
    │  └─ geschichten: bilder die zusammengehoeren│
    │                                             │
    │  Originale: bleiben bei Apple/Google         │
    │  Thumbnails: data/augen/thumbnails/         │
    │  Online: Cloudflare R2 (optional)           │
    │                                             │
    │  Import: Apple Photos | Google Takeout      │
    │  Vision: augen.sehen() → versteckspiel      │
    │  Suche:  ChromaDB embeddings + SQLite       │
    └─────────────────────────────────────────────┘

Pro Erinnerung: ~50KB (Thumbnail) + ~2KB (Metadaten)
100.000 Fotos = ~5GB. Das ist NICHTS.
"""

from void_intelligence.gedaechtnis.kern import (
    Erinnerung,
    GedaechtnisDB,
    gedaechtnis_oeffnen,
)

__all__ = ["Erinnerung", "GedaechtnisDB", "gedaechtnis_oeffnen"]
