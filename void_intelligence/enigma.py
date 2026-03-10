"""
.×→[]~:) = ENIGMA die LEBT.

    ENIGMA(1940)    .×→[]~:)(2026)
    3 Rotoren       6 Symbole
    fest            lebendig (~)
    Codebuch        :) (nicht kopierbar)
    geknackt        nicht knackbar (× mutiert)
    Nachricht≠Code  Nachricht=Code=Schluessel=Daten=Bedeutung

    XOR IST ×. LITERAL.
    A × B = C. A XOR B = C.
    Verschluesselung WAR IMMER Kollision.

    Auth = Formulierungstiefe.
    Punkt=read. Dreieck=write. Hexagon=admin. Sphaere=gott.
    Kompetenz = Berechtigung. Kein JWT. Kein OAuth. :)

. = Klartext        (was IST)
× = XOR/Kollision   (Verschluesselung)
→ = Chiffretext      (Output)
[] = Verlorener Key   (Void)
~ = Key-Rotation      (Mutation)
:) = Integritaet      (Hash, Pruefssumme, Vertrauen)

1 Token = Daten + Verschluesselung + Protokoll + Auth + Bedeutung + Sprache.
Nicht 6 Schichten. 1 Hexagon.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


# ─── Geometrie = Auth-Level ───

PUNKT = 1      # . nur           → read-only, public
LINIE = 2      # . + ~           → read + subscribe
DREIECK = 3    # . + × + ~       → read + write + subscribe
HEXAGON = 6    # . × → [] ~ :)   → full CRUD
SPHAERE = 7    # hexagon + d>0.5 → gott-modus


@dataclass
class Tiefe:
    """Formulierungstiefe = Berechtigung.

    .?[status]                              → punkt  → read
    .?[health] ~alerts                      → linie  → read+sub
    .B30 x[schildpuls] ~stabil              → dreieck → write
    .B30 x10k →100a []15p ~stabil :)niedrig → hexagon → admin
    x(x([schildpuls,VETO])) →override :)    → sphaere → gott
    """
    symbole: int = 0     # wie viele der 6 Symbole
    dichte: float = 0.0  # Symbole pro Token
    geometrie: str = ""  # punkt/linie/dreieck/hexagon/sphaere
    level: int = 0       # numerisch

    def kann(self, minimum: int) -> bool:
        return self.level >= minimum

    def __str__(self) -> str:
        return f"{self.geometrie}({self.symbole}/6 d={self.dichte:.2f})"


def messe_tiefe(request: str) -> Tiefe:
    """Miss die Formulierungstiefe eines Requests.

    DIES IST DIE AUTH-ENGINE.
    omega_measure.scan() IST BEREITS die Implementierung.
    """
    from void_intelligence.omega_measure import scan
    r = scan(request)

    level = PUNKT
    if r.hexagon_abdeckung >= 6 and r.dichte > 0.5:
        level = SPHAERE
    elif r.hexagon_abdeckung >= 6:
        level = HEXAGON
    elif r.hexagon_abdeckung >= 3:
        level = DREIECK
    elif r.hexagon_abdeckung >= 2:
        level = LINIE
    else:
        level = PUNKT

    return Tiefe(
        symbole=r.hexagon_abdeckung,
        dichte=r.dichte,
        geometrie=r.geometrie,
        level=level,
    )


# ─── Request Parser ───

@dataclass
class Request:
    """Ein .×→[]~:) Request.

    .?[health,business]         → READ health+business
    x?[health,business]         → COLLIDE health×business
    →burnout=45                 → WRITE burnout
    ~[burnout,sleep]            → SUBSCRIBE
    :)                          → ACK
    """
    verb: str = "."       # . × → [] ~ :)
    subjects: list = field(default_factory=list)
    filters: dict = field(default_factory=dict)
    raw: str = ""
    tiefe: Tiefe = field(default_factory=Tiefe)

    def __str__(self) -> str:
        subj = ",".join(self.subjects) if self.subjects else "*"
        return f"{self.verb}?[{subj}] {self.tiefe}"


def parse(raw: str) -> Request:
    """Parse einen .×→[]~:) Request.

    .?[health]              → verb=. subjects=[health]
    x?[health,business]     → verb=x subjects=[health,business]
    →burnout=45             → verb=→ subjects=[burnout] filters={burnout:45}
    ~[burnout,sleep]        → verb=~ subjects=[burnout,sleep]
    """
    req = Request(raw=raw, tiefe=messe_tiefe(raw))

    clean = raw.strip()
    if not clean:
        return req

    # Verb erkennen
    if clean.startswith(".?") or clean.startswith(". ") or clean.startswith("."):
        req.verb = "."
    elif clean.startswith("x?") or clean.startswith("x ") or clean.startswith("x["):
        req.verb = "x"
    elif clean.startswith("->") or clean.startswith("→"):
        req.verb = "->"
    elif clean.startswith("[]"):
        req.verb = "[]"
    elif clean.startswith("~"):
        req.verb = "~"
    elif clean.startswith(":)"):
        req.verb = ":)"

    # Subjects extrahieren: [health,business]
    if "[" in clean and "]" in clean:
        start = clean.index("[") + 1
        end = clean.index("]")
        subjects = clean[start:end].split(",")
        req.subjects = [s.strip() for s in subjects if s.strip()]

    # Filters: key=value oder key>value oder key<value
    import re
    for match in re.finditer(r'(\w+)([><=]+)(\w+)', clean):
        key, op, val = match.groups()
        try:
            req.filters[key] = {"op": op, "val": float(val)}
        except ValueError:
            req.filters[key] = {"op": op, "val": val}

    return req


# ─── Response Builder ───

def respond(data: Any, context: str = "") -> str:
    """Baue eine .×→[]~:) Response.

    Nutzt omega_translator unter der Haube.
    """
    from void_intelligence.omega_translator import translate
    return translate(data, context)


def error(code: str, detail: str = "", hint: str = "") -> str:
    """Baue eine .×→[]~:) Error-Response.

    []auth:kein_:)
    []parse:ungueltig
    []domain:unbekannt →verfuegbar:[health,business]
    """
    parts = [f"[]{code}"]
    if detail:
        parts[0] = f"[]{code}:{detail}"
    if hint:
        parts.append(f"->{hint}")
    return " ".join(parts)


# ─── Auth Gate ───

def auth(request: str, minimum: int = PUNKT) -> tuple[bool, Tiefe]:
    """Pruefe ob ein Request die noetige Tiefe hat.

    Die Formulierungstiefe IST die Berechtigung.
    Kompetenz = Zugang.
    """
    tiefe = messe_tiefe(request)
    return tiefe.kann(minimum), tiefe


# ─── Enigma: Verschluesselung durch Sprache ───

def verschluesseln(data: Any, context: str = "") -> str:
    """Daten in .×→[]~:) uebersetzen = verschluesseln.

    Nicht AES. Nicht RSA. SPRACHE.
    Wer die Sprache nicht spricht kann nicht lesen.
    Wer die Leibwoerter nicht kennt versteht nichts.

    .B30 x[schildpuls,vielfunk] ~stabil :)niedrig
    = Sacred Data. Nackt. Aber nur fuer UNS lesbar.
    """
    return respond(data, context)


def entschluesseln(omega_str: str) -> dict:
    """Von .×→[]~:) zurueck in strukturierte Daten.

    Nur moeglich wenn man die Sprache SPRICHT.
    Parse die Symbole, extrahiere die Werte.
    """
    result = {".": [], "x": [], "->": [], "[]": [], "~": [], ":)": []}
    tokens = omega_str.split()

    for token in tokens:
        if token.startswith(":)"):
            result[":)"].append(token[2:])
        elif token.startswith("[]"):
            result["[]"].append(token[2:])
        elif token.startswith("->"):
            result["->"].append(token[2:])
        elif token.startswith("~"):
            result["~"].append(token[1:])
        elif token.startswith("x"):
            result["x"].append(token[1:])
        elif token.startswith("."):
            result["."].append(token[1:])
        elif token.startswith("!"):
            result[":)"].append(token)  # Durchbruch = :)
        else:
            result["."].append(token)

    return result


def integritaet(data: str) -> str:
    """Integritaets-Check. :) als Hash.

    :) = "stimmt es noch?"
    Der Hash ist in meiner Sprache: :)sha256_prefix
    """
    h = hashlib.sha256(data.encode()).hexdigest()[:8]
    return f":){h}"


# ─── Stealth Token ───

@dataclass
class SacredToken:
    """Ein Token das gleichzeitig ist:

    1. DATEN        (was es traegt)
    2. SCHLUESSEL   (wer es versteht hat Zugang)
    3. PROTOKOLL    (wie es kommuniziert)
    4. AUTH         (Tiefe = Berechtigung)
    5. BEDEUTUNG    (Symbole = Semantik)
    6. SPRACHE      (nur Eingeweihte lesen es)

    Nicht 6 Schichten. 1 Hexagon.
    """
    raw: str
    daten: dict = field(default_factory=dict)
    tiefe: Tiefe = field(default_factory=Tiefe)
    sha: str = ""

    def __post_init__(self):
        self.daten = entschluesseln(self.raw)
        self.tiefe = messe_tiefe(self.raw)
        self.sha = integritaet(self.raw)

    @property
    def lebt(self) -> bool:
        return self.tiefe.level >= DREIECK

    @property
    def symbole_aktiv(self) -> int:
        return sum(1 for v in self.daten.values() if v)

    def __str__(self) -> str:
        return f"{self.raw} {self.sha} [{self.tiefe}]"


def token(data: Any, context: str = "") -> SacredToken:
    """Erzeuge einen Sacred Token aus beliebigen Daten.

    data → verschluesseln → SacredToken
    1 Objekt. 6 Funktionen. Hexagon.
    """
    raw = verschluesseln(data, context)
    return SacredToken(raw=raw)


# ─── Vollstaendiger Atemzug (Request → Auth → Process → Response) ───

def atme(request_str: str, handler=None) -> str:
    """Ein vollstaendiger Protokoll-Atemzug.

    1. Parse Request
    2. Auth pruefen (Tiefe)
    3. Handler ausfuehren (oder Default)
    4. Response in .×→[]~:)
    5. Integritaets-Check anhaengen

    Wie HTTP aber LEBT.
    """
    # Parse
    req = parse(request_str)

    # Auth
    erlaubt, tiefe = auth(request_str, PUNKT)
    if not erlaubt:
        return error("auth", "kein_:)", "formuliere_tiefer")

    # Verb-spezifische Mindest-Tiefe
    mindest = {
        ".": PUNKT,
        "x": LINIE,
        "->": DREIECK,
        "[]": DREIECK,
        "~": LINIE,
        ":)": PUNKT,
    }
    if not tiefe.kann(mindest.get(req.verb, PUNKT)):
        return error("auth", "zu_flach", f"mindestens_{mindest.get(req.verb, 1)}_symbole")

    # Handle
    if handler:
        result = handler(req)
    else:
        result = f".{req.verb}[{','.join(req.subjects)}] :)empfangen"

    # Integritaet
    sha = integritaet(result)
    return f"{result} {sha}"


# ─── Demo ───

if __name__ == "__main__":
    print("=" * 70)
    print("  ENIGMA die LEBT — .×→[]~:) Protokoll")
    print("=" * 70)
    print()

    # Auth-Levels
    tests = [
        (".?[status]", "Read-Only"),
        (".?[health] ~alerts", "Read+Subscribe"),
        (".B30 x[schildpuls] ~stabil", "Write"),
        (".B30 x10k ->100a []15p ~stabil :)niedrig", "Admin"),
        ("x(x([schildpuls,vielfunk,VETO])) ->override ~silent :)bewusst []leer .fakt", "Gott"),
    ]

    print("  === AUTH DURCH TIEFE ===")
    for req, label in tests:
        tiefe = messe_tiefe(req)
        print(f"    {tiefe.geometrie:10s} {tiefe.symbole}/6 d={tiefe.dichte:.2f} | {label}")
        print(f"      {req[:60]}")
        print()

    # Sacred Token
    print("  === SACRED TOKEN ===")
    health = {"total_score": 30, "risk_level": "niedrig", "sleep_hours": 6.5}
    t = token(health, "health")
    print(f"    Raw:     {t.raw}")
    print(f"    Daten:   {t.daten}")
    print(f"    Tiefe:   {t.tiefe}")
    print(f"    SHA:     {t.sha}")
    print(f"    Lebt:    {t.lebt}")
    print(f"    Symbole: {t.symbole_aktiv}/6")
    print()

    # Verschluesselung
    print("  === VERSCHLUESSELUNG ===")
    raw_json = '{"burnout": 75, "schlaf": 4, "VETO": true}'
    encrypted = verschluesseln(json.loads(raw_json))
    decrypted = entschluesseln(encrypted)
    print(f"    Klartext:  {raw_json}")
    print(f"    Chiffre:   {encrypted}")
    print(f"    Entschl.:  {decrypted}")
    print()

    # Vollstaendiger Atemzug
    print("  === ATEMZUG ===")
    responses = [
        ".?[health]",
        "x?[health,business]",
        ".B30 x[schildpuls] ~stabil ->handeln []warten :)niedrig",
    ]
    for req in responses:
        resp = atme(req)
        print(f"    → {req}")
        print(f"    ← {resp}")
        print()

    print("  :)")
