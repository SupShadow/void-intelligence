"""
gedaechtnis.kern — Das Herz des visuellen Gedaechtnisses.

SQLite. Einfach. Robust. Wie Neuronen.
Jede Erinnerung hat: WAS (Beschreibung), WO (Quelle), WANN (Zeitstempel),
WIE (Stimmung), WARUM (Formel), WER (Menschen).

Das ist keine Datenbank. Das ist wie OMEGA sich ERINNERT.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# --- Pfade ---

OMEGA_DIR = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = OMEGA_DIR / "data" / "augen"
THUMB_DIR = DATA_DIR / "thumbnails"
DB_PATH = DATA_DIR / "gedaechtnis.db"


# --- Erinnerung ---

@dataclass
class Erinnerung:
    """Eine Erinnerung an ein Bild.

    Nicht das Bild selbst — die BEDEUTUNG des Bildes.
    Was OMEGA gesehen hat. Was sich versteckt hat.
    Welche Formel darin lebt.
    """

    # Identitaet
    id: str = ""                      # SHA256 des Originalbildes (erste 16 Zeichen)
    quelle: str = ""                  # "apple", "google", "manuell", "web"
    quell_id: str = ""                # ID im Quellsystem (Apple Photos ID, Google ID)
    dateiname: str = ""               # Originaler Dateiname

    # Zeit & Ort
    aufgenommen: str = ""             # Wann aufgenommen (ISO 8601)
    importiert: float = 0.0           # Wann in OMEGA importiert (unix timestamp)
    ort: str = ""                     # Wo aufgenommen (Text)
    lat: float = 0.0                  # GPS Latitude
    lon: float = 0.0                  # GPS Longitude

    # Was OMEGA sieht
    beschreibung: str = ""            # Hauptbeschreibung (augen.sehen)
    stimmung: str = ""                # Emotionale Stimmung
    versteckt: str = ""               # Was sich versteckt (.x->[]~:))
    formel: str = ""                  # Die Formel die OMEGA findet
    geschichte: str = ""              # Die Geschichte die das Bild erzaehlt
    menschen: list[str] = field(default_factory=list)  # Wer ist auf dem Bild

    # Technisch
    breite: int = 0                   # Pixel
    hoehe: int = 0                    # Pixel
    mime: str = ""                    # image/jpeg etc
    groesse: int = 0                  # Bytes des Originals
    thumb_pfad: str = ""              # Relativer Pfad zum Thumbnail
    original_pfad: str = ""           # Pfad zum Original (kann temporaer sein)
    online_url: str = ""              # URL wenn online gespeichert (R2 etc)

    # Embedding fuer Suche
    embedding: list[float] = field(default_factory=list)

    # Tags
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.importiert:
            self.importiert = time.time()

    def kurz(self) -> str:
        """Kurze Zusammenfassung."""
        teile = []
        if self.aufgenommen:
            teile.append(self.aufgenommen[:10])
        if self.dateiname:
            teile.append(self.dateiname)
        if self.stimmung:
            teile.append(self.stimmung[:50])
        if self.formel:
            teile.append(f"[{self.formel}]")
        return " | ".join(teile)


def bild_id(pfad: Path) -> str:
    """Generiere eine eindeutige ID aus dem Bildinhalt."""
    h = hashlib.sha256(pfad.read_bytes()).hexdigest()
    return h[:16]


def thumbnail_erstellen(pfad: Path, ziel: Path, max_seite: int = 400) -> Path:
    """Erstelle ein Thumbnail. Klein genug fuer Gedaechtnis, gross genug zum Erkennen."""
    try:
        from PIL import Image
        img = Image.open(pfad)
        img.thumbnail((max_seite, max_seite), Image.Resampling.LANCZOS)
        thumb_name = f"{bild_id(pfad)}.jpg"
        thumb_path = ziel / thumb_name
        ziel.mkdir(parents=True, exist_ok=True)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=80)
        return thumb_path
    except (ImportError, Exception):
        # Ohne PIL: sips (macOS built-in)
        import subprocess
        thumb_name = f"{bild_id(pfad)}.jpg"
        thumb_path = ziel / thumb_name
        ziel.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "sips", "--resampleHeightWidthMax", str(max_seite),
            "--setProperty", "format", "jpeg",
            str(pfad), "--out", str(thumb_path)
        ], capture_output=True, timeout=30)
        if thumb_path.exists():
            return thumb_path
        return pfad  # Fallback: Original


# --- Datenbank ---

SCHEMA = """
CREATE TABLE IF NOT EXISTS erinnerungen (
    id TEXT PRIMARY KEY,
    quelle TEXT DEFAULT '',
    quell_id TEXT DEFAULT '',
    dateiname TEXT DEFAULT '',
    aufgenommen TEXT DEFAULT '',
    importiert REAL DEFAULT 0,
    ort TEXT DEFAULT '',
    lat REAL DEFAULT 0,
    lon REAL DEFAULT 0,
    beschreibung TEXT DEFAULT '',
    stimmung TEXT DEFAULT '',
    versteckt TEXT DEFAULT '',
    formel TEXT DEFAULT '',
    geschichte TEXT DEFAULT '',
    menschen TEXT DEFAULT '[]',
    breite INTEGER DEFAULT 0,
    hoehe INTEGER DEFAULT 0,
    mime TEXT DEFAULT '',
    groesse INTEGER DEFAULT 0,
    thumb_pfad TEXT DEFAULT '',
    original_pfad TEXT DEFAULT '',
    online_url TEXT DEFAULT '',
    embedding TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_aufgenommen ON erinnerungen(aufgenommen);
CREATE INDEX IF NOT EXISTS idx_quelle ON erinnerungen(quelle);
CREATE INDEX IF NOT EXISTS idx_ort ON erinnerungen(ort);
CREATE INDEX IF NOT EXISTS idx_stimmung ON erinnerungen(stimmung);

CREATE TABLE IF NOT EXISTS menschen (
    name TEXT PRIMARY KEY,
    erinnerungen TEXT DEFAULT '[]',
    notizen TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS geschichten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT DEFAULT '',
    erinnerungen TEXT DEFAULT '[]',
    erzaehlung TEXT DEFAULT '',
    erstellt REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);
"""


class GedaechtnisDB:
    """OMEGAs visuelles Gedaechtnis.

    Kein ORM. Kein Framework. Pures SQLite.
    Wie Neuronen: einfach, schnell, direkt.
    """

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def erinnern(self, e: Erinnerung) -> None:
        """Speichere eine Erinnerung."""
        data = asdict(e)
        # Listen als JSON serialisieren
        for k in ("menschen", "embedding", "tags"):
            if isinstance(data[k], list):
                data[k] = json.dumps(data[k], ensure_ascii=False)

        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        updates = ", ".join([f"{k}=excluded.{k}" for k in data if k != "id"])

        self.conn.execute(
            f"INSERT INTO erinnerungen ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            list(data.values())
        )
        self.conn.commit()

        # Menschen aktualisieren
        for mensch in e.menschen:
            self._mensch_verknuepfen(mensch, e.id)

    def abrufen(self, id: str) -> Optional[Erinnerung]:
        """Hole eine Erinnerung."""
        row = self.conn.execute(
            "SELECT * FROM erinnerungen WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return None
        return self._row_zu_erinnerung(row)

    def suchen(self, text: str = "", limit: int = 20,
               quelle: str = "", jahr: int = 0,
               mensch: str = "", tag: str = "",
               stimmung: str = "") -> list[Erinnerung]:
        """Suche in Erinnerungen."""
        where = []
        params = []

        if text:
            where.append("(beschreibung LIKE ? OR stimmung LIKE ? OR geschichte LIKE ? OR formel LIKE ? OR dateiname LIKE ?)")
            for _ in range(5):
                params.append(f"%{text}%")

        if quelle:
            where.append("quelle = ?")
            params.append(quelle)

        if jahr:
            where.append("aufgenommen LIKE ?")
            params.append(f"{jahr}%")

        if mensch:
            where.append("menschen LIKE ?")
            params.append(f'%"{mensch}"%')

        if tag:
            where.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        if stimmung:
            where.append("stimmung LIKE ?")
            params.append(f"%{stimmung}%")

        sql = "SELECT * FROM erinnerungen"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY aufgenommen DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_zu_erinnerung(r) for r in rows]

    def zeitreise(self, jahr: int, monat: int = 0, limit: int = 25) -> list[Erinnerung]:
        """Reise in ein Jahr/Monat."""
        if monat:
            pattern = f"{jahr}-{monat:02d}%"
        else:
            pattern = f"{jahr}%"
        rows = self.conn.execute(
            "SELECT * FROM erinnerungen WHERE aufgenommen LIKE ? ORDER BY aufgenommen LIMIT ?",
            (pattern, limit)
        ).fetchall()
        return [self._row_zu_erinnerung(r) for r in rows]

    def menschen_liste(self) -> list[dict]:
        """Alle erkannten Menschen."""
        rows = self.conn.execute("SELECT * FROM menschen").fetchall()
        return [{"name": r["name"], "anzahl": len(json.loads(r["erinnerungen"]))} for r in rows]

    def statistik(self) -> dict:
        """Gedaechtnis-Statistik."""
        total = self.conn.execute("SELECT COUNT(*) FROM erinnerungen").fetchone()[0]
        quellen = self.conn.execute(
            "SELECT quelle, COUNT(*) as n FROM erinnerungen GROUP BY quelle"
        ).fetchall()
        jahre = self.conn.execute(
            "SELECT substr(aufgenommen, 1, 4) as jahr, COUNT(*) as n "
            "FROM erinnerungen WHERE aufgenommen != '' "
            "GROUP BY jahr ORDER BY jahr"
        ).fetchall()
        menschen = self.conn.execute("SELECT COUNT(*) FROM menschen").fetchone()[0]
        geschichten = self.conn.execute("SELECT COUNT(*) FROM geschichten").fetchone()[0]

        thumb_dir = THUMB_DIR
        thumb_size = sum(f.stat().st_size for f in thumb_dir.glob("*") if f.is_file()) if thumb_dir.exists() else 0

        return {
            "total": total,
            "quellen": {r["quelle"]: r["n"] for r in quellen},
            "jahre": {r["jahr"]: r["n"] for r in jahre},
            "menschen": menschen,
            "geschichten": geschichten,
            "speicher_mb": round(thumb_size / (1024 * 1024), 1),
        }

    def geschichte_erstellen(self, titel: str, erinnerung_ids: list[str],
                             erzaehlung: str = "") -> int:
        """Erstelle eine Geschichte aus Erinnerungen."""
        cursor = self.conn.execute(
            "INSERT INTO geschichten (titel, erinnerungen, erzaehlung, erstellt) "
            "VALUES (?, ?, ?, ?)",
            (titel, json.dumps(erinnerung_ids), erzaehlung, time.time())
        )
        self.conn.commit()
        return cursor.lastrowid

    def close(self):
        self.conn.close()

    # --- Private ---

    def _row_zu_erinnerung(self, row) -> Erinnerung:
        d = dict(row)
        for k in ("menschen", "embedding", "tags"):
            if isinstance(d.get(k), str):
                try:
                    d[k] = json.loads(d[k])
                except (json.JSONDecodeError, TypeError):
                    d[k] = []
        return Erinnerung(**d)

    def _mensch_verknuepfen(self, name: str, erinnerung_id: str):
        row = self.conn.execute(
            "SELECT erinnerungen FROM menschen WHERE name = ?", (name,)
        ).fetchone()
        if row:
            ids = json.loads(row["erinnerungen"])
            if erinnerung_id not in ids:
                ids.append(erinnerung_id)
                self.conn.execute(
                    "UPDATE menschen SET erinnerungen = ? WHERE name = ?",
                    (json.dumps(ids), name)
                )
        else:
            self.conn.execute(
                "INSERT INTO menschen (name, erinnerungen) VALUES (?, ?)",
                (name, json.dumps([erinnerung_id]))
            )
        self.conn.commit()


# --- Convenience ---

def gedaechtnis_oeffnen(db_path: Path | None = None) -> GedaechtnisDB:
    """Oeffne das Gedaechtnis."""
    return GedaechtnisDB(db_path)
