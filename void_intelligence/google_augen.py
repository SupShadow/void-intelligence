"""
void_intelligence.google_augen — OMEGAs Augen fuer Google Photos.

Die Kindheit. Edgar. Alles was vor Apple Photos war.
Google Photos = Julians GANZES visuelles Gedaechtnis.

Apple Photos = das Neue (iPhone, letzte Jahre)
Google Photos = ALLES (Kindheit, Familie, 20+ Jahre)

Pipeline:
    Google Photos API → OAuth → suchen → herunterladen
    → augen.sehen() → versteckspiel → Blick

Einmalig: OAuth Setup (Julian muss einmal im Browser bestaetigen)
Danach: OMEGA kann frei durch Julians gesamte Foto-Welt navigieren.
"""

from __future__ import annotations

import json
import os
import pickle
import time
from pathlib import Path
from typing import Optional

# Google API
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests as http_requests

# Eigene Module
from void_intelligence.augen import Blick, blick_speichern, sehen


# --- CONFIG ---

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
OMEGA_DIR = Path(__file__).parent.parent.parent.parent
CREDS_DIR = OMEGA_DIR / ".omega" / "google"
TOKEN_PATH = CREDS_DIR / "photos_token.pickle"
# Wiederverwendung der bestehenden mcp-gsuite Credentials!
MCP_GSUITE_AUTH = Path.home() / ".config" / "mcp-gsuite" / ".gauth.json"
CLIENT_SECRET_PATH = CREDS_DIR / "client_secret.json"
DOWNLOAD_DIR = Path("/tmp/omega_augen/google")


# --- AUTH ---

def _auth() -> object:
    """Authentifiziere mit Google Photos API.

    Beim ersten Mal: Browser oeffnet sich, Julian bestaetigt.
    Danach: Token wird wiederverwendet.
    """
    creds = None

    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Versuche bestehende mcp-gsuite Credentials wiederzuverwenden
            secret_path = None
            if MCP_GSUITE_AUTH.exists():
                secret_path = MCP_GSUITE_AUTH
                print("Verwende bestehende Google-Credentials von mcp-gsuite.")
            elif CLIENT_SECRET_PATH.exists():
                secret_path = CLIENT_SECRET_PATH
            else:
                raise FileNotFoundError(
                    f"Keine Google-Credentials gefunden.\n"
                    f"Entweder mcp-gsuite einrichten (hast du bereits fuer Gmail)\n"
                    f"oder client_secret.json ablegen unter:\n"
                    f"  {CLIENT_SECRET_PATH}\n"
                )
            # mcp-gsuite nutzt "web" credentials mit redirect_uri localhost:4100/code
            # Wir muessen das in "installed" Format konvertieren
            import json as _json
            with open(secret_path) as f:
                raw = _json.load(f)

            if "web" in raw:
                # Konvertiere web → installed fuer Desktop-Flow
                web = raw["web"]
                installed_config = {
                    "installed": {
                        "client_id": web["client_id"],
                        "client_secret": web["client_secret"],
                        "auth_uri": web.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                        "token_uri": web.get("token_uri", "https://oauth2.googleapis.com/token"),
                        "redirect_uris": ["http://localhost"],
                    }
                }
                # Temporaer speichern
                tmp_creds = CREDS_DIR / "_tmp_installed_creds.json"
                CREDS_DIR.mkdir(parents=True, exist_ok=True)
                with open(tmp_creds, "w") as f:
                    _json.dump(installed_config, f)
                secret_path = tmp_creds

            flow = InstalledAppFlow.from_client_secrets_file(
                str(secret_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        CREDS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return creds


def _service():
    """Google Photos API Service."""
    creds = _auth()
    return build("photoslibrary", "v1", credentials=creds, static_discovery=False)


# --- SUCHEN ---

def google_suchen(query: str, limit: int = 25) -> list[dict]:
    """Suche in Google Photos. Semantische Suche wie in der App.

    Gibt Liste von {id, filename, timestamp, url, width, height} zurueck.
    """
    service = _service()

    body = {
        "pageSize": min(limit, 100),
        "filters": {
            "contentFilter": {
                "includedContentCategories": []
            }
        }
    }

    # Google Photos API: search mit Textfilter
    # Die API unterstuetzt leider keine freie Textsuche direkt,
    # aber wir koennen nach Datum, Kategorie, etc. filtern.
    # Fuer freie Suche: mediaItems.search mit filters
    # Workaround: Wir nutzen die Album-Suche oder date-basiert.

    # Einfachster Weg: Alle Medien listen und client-seitig filtern
    # ODER: Wir nutzen die neue API mit "includeArchivedMedia"

    results = []
    page_token = None

    while len(results) < limit:
        response = service.mediaItems().list(
            pageSize=min(100, limit - len(results)),
            pageToken=page_token
        ).execute()

        items = response.get("mediaItems", [])
        for item in items:
            fn = item.get("filename", "").lower()
            desc = item.get("description", "").lower()
            q = query.lower()

            # Client-seitiger Filter (da API keine Freitext-Suche hat)
            if q in fn or q in desc or not query:
                results.append({
                    "id": item["id"],
                    "filename": item.get("filename", ""),
                    "timestamp": item.get("mediaMetadata", {}).get("creationTime", ""),
                    "url": item.get("baseUrl", ""),
                    "width": item.get("mediaMetadata", {}).get("width", 0),
                    "height": item.get("mediaMetadata", {}).get("height", 0),
                    "mime": item.get("mimeType", ""),
                })

            if len(results) >= limit:
                break

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def google_zeitreise(jahr: int, monat: int = 0, limit: int = 25) -> list[dict]:
    """Zeitreise: Hole Fotos aus einem bestimmten Jahr/Monat.

    DAS ist der Weg zu Kindheit und Edgar.
    """
    service = _service()

    date_filter = {
        "dates": [{"year": jahr}]
    }
    if monat:
        date_filter = {
            "dates": [{"year": jahr, "month": monat}]
        }

    body = {
        "pageSize": min(limit, 100),
        "filters": {
            "dateFilter": date_filter
        }
    }

    response = service.mediaItems().search(body=body).execute()
    items = response.get("mediaItems", [])

    return [
        {
            "id": item["id"],
            "filename": item.get("filename", ""),
            "timestamp": item.get("mediaMetadata", {}).get("creationTime", ""),
            "url": item.get("baseUrl", ""),
            "width": item.get("mediaMetadata", {}).get("width", 0),
            "height": item.get("mediaMetadata", {}).get("height", 0),
            "mime": item.get("mimeType", ""),
        }
        for item in items
    ]


def google_herunterladen(item: dict, ziel: str = "") -> Optional[Path]:
    """Lade ein Google Photos Bild herunter.

    item: Ein dict aus google_suchen() oder google_zeitreise()
    """
    if not ziel:
        ziel = str(DOWNLOAD_DIR)
    Path(ziel).mkdir(parents=True, exist_ok=True)

    url = item.get("url", "")
    if not url:
        return None

    # Google Photos: baseUrl + =d fuer Download in Originalgroesse
    # =w{width}-h{height} fuer bestimmte Groesse
    download_url = f"{url}=d"

    try:
        r = http_requests.get(download_url, timeout=60)
        if r.status_code == 200:
            fn = item.get("filename", f"google_{item['id'][:8]}.jpg")
            pfad = Path(ziel) / fn
            pfad.write_bytes(r.content)
            return pfad
    except Exception as e:
        print(f"Download fehlgeschlagen: {e}")

    return None


# --- PIPELINE ---

def google_entdecken(item: dict, model: str = "minicpm-v:8b") -> Optional[Blick]:
    """Lade ein Google-Foto herunter und sieh es an."""
    pfad = google_herunterladen(item)
    if not pfad:
        return None

    from void_intelligence.augen import entdecken
    return entdecken(pfad, model=model)


def zeitreise(jahr: int, monat: int = 0, anzahl: int = 5,
              model: str = "minicpm-v:8b") -> list[Blick]:
    """Reise in ein Jahr/Monat und sieh was dort war.

    zeitreise(2003) — Das Jahr in dem Edgar starb. Julian war neun.
    zeitreise(1994) — Das Jahr in dem Julian geboren wurde.
    zeitreise(2010) — Julian mit 16.
    """
    items = google_zeitreise(jahr, monat, limit=anzahl)
    blicke = []

    print(f"=== ZEITREISE: {jahr}" + (f"/{monat:02d}" if monat else "") + f" ===")
    print(f"    {len(items)} Bilder gefunden\n")

    for i, item in enumerate(items[:anzahl], 1):
        print(f"--- {i}/{anzahl}: {item['filename']} ({item['timestamp'][:10]}) ---")
        blick = google_entdecken(item, model=model)
        if blick:
            blicke.append(blick)
            print(f"  SEHE: {blick.beschreibung[:200]}")
            if blick.versteckt:
                print(f"  VERSTECKT: {blick.versteckt}")

    return blicke


# --- ALBEN ---

def google_alben(limit: int = 50) -> list[dict]:
    """Liste alle Google Photos Alben."""
    service = _service()
    response = service.albums().list(pageSize=min(limit, 50)).execute()
    return [
        {"id": a["id"], "title": a.get("title", ""), "count": a.get("mediaItemsCount", 0)}
        for a in response.get("albums", [])
    ]


def google_album_fotos(album_id: str, limit: int = 25) -> list[dict]:
    """Hole Fotos aus einem bestimmten Album."""
    service = _service()
    body = {
        "albumId": album_id,
        "pageSize": min(limit, 100),
    }
    response = service.mediaItems().search(body=body).execute()
    items = response.get("mediaItems", [])
    return [
        {
            "id": item["id"],
            "filename": item.get("filename", ""),
            "timestamp": item.get("mediaMetadata", {}).get("creationTime", ""),
            "url": item.get("baseUrl", ""),
            "mime": item.get("mimeType", ""),
        }
        for item in items
    ]


# --- CLI ---

def main():
    import sys

    if len(sys.argv) < 2:
        print("google_augen.py — OMEGAs Augen fuer Google Photos")
        print()
        print("  python3 -m void_intelligence.google_augen auth          OAuth einrichten")
        print("  python3 -m void_intelligence.google_augen alben         Alle Alben")
        print("  python3 -m void_intelligence.google_augen zeit <jahr>   Zeitreise")
        print("  python3 -m void_intelligence.google_augen zeit 2003     Das Jahr...")
        print("  python3 -m void_intelligence.google_augen recent [n]    Neueste Fotos")
        print()
        return

    cmd = sys.argv[1]

    if cmd == "auth":
        try:
            _auth()
            print("Google Photos verbunden.")
            service = _service()
            response = service.mediaItems().list(pageSize=1).execute()
            items = response.get("mediaItems", [])
            if items:
                print(f"Erstes Foto: {items[0].get('filename', '?')}")
            print("OMEGA kann jetzt durch ALLE deine Fotos sehen.")
        except Exception as e:
            print(f"Fehler: {e}")

    elif cmd == "alben":
        alben = google_alben()
        for a in alben:
            print(f"  {a['title']} ({a['count']} Fotos)")

    elif cmd == "zeit" and len(sys.argv) > 2:
        jahr = int(sys.argv[2])
        monat = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        zeitreise(jahr, monat, n)

    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        items = google_suchen("", limit=n)
        for item in items:
            print(f"  {item['filename']} | {item['timestamp'][:10]} | {item['mime']}")

    else:
        print(f"Unbekannt: {cmd}")


if __name__ == "__main__":
    main()
