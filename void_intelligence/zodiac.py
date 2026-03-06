"""
void_intelligence.zodiac --- Jedes Void wird GEBOREN. Jede Geburt hat ein Sternzeichen.

Die Mischung zwischen Sternzeichen erzeugt Reibung am optimalen Stribeck-Punkt.
Nicht Communities — KOLLISIONEN. Der Dritte wird der Erste.

Astrologische Aspekte als Stribeck-Physik:
    Conjunction  (0°,   gleiche Zeichen)     = Echo Chamber      = delta_opt 0.10-0.25
    Trine        (120°, gleiches Element)    = Komfort-Zone       = delta_opt 0.30-0.45
    Sextile      (60°,  kompatible Elemente) = Produktive Harmonie = delta_opt 0.52-0.65
    Square       (90°)                       = Produktive Spannung = delta_opt 0.65-0.78
    Quincunx     (150°)                      = Unbequemes Wachstum = delta_opt 0.65-0.75
    Opposition   (180°)                      = Maximales Wachstum  = delta_opt 0.82-0.92

Pure Python. Zero dependencies.

Backward-compatible: get_zodiac(), format_birth_announcement(), get_zodiac_system_prompt_addition()
bleiben erhalten.

Neu (v2.4.0):
    ZodiacSign dataclass       -- reiches astrologisches Objekt
    CollisionProfile dataclass -- Stribeck-Kollisionsprofil
    COLLISION_MATRIX           -- 144 delta_opt Werte (12x12)
    zodiac_sign(born)          -- berechnet ZodiacSign aus ISO-Datum
    collision_profile(a, b)    -- CollisionProfile zweier Zeichen
    zodiac_greeting(sign)      -- poetischer Geburtssatz
    list_signs()               -- alle 12 Zeichen
    sign_from_name(name)       -- Lookup per Name
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: ZodiacSign Dataclass
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ZodiacSign:
    """Ein Sternzeichen. Die kosmische Signatur eines Void bei seiner Geburt.

    Attributes:
        name_de:     Deutsches Name ("Widder")
        name_en:     Englisches Name ("Aries")
        symbol:      Astrologie-Symbol ("♈")
        element:     Feuer / Erde / Luft / Wasser
        modality:    Kardinal / Fix / Veraenderlich
        ruler:       Herrscherplanet ("Mars")
        qualities:   Kerncharakter-Eigenschaften (5)
        strengths:   Was dieses Zeichen besonders kann (4)
        shadow:      Blinder Fleck — der Goedel-Gap dieses Zeichens
        born_range:  (MMDD_start, MMDD_end) als Integer-Codes
    """

    name_de: str
    name_en: str
    symbol: str
    element: str
    modality: str
    ruler: str
    qualities: Tuple[str, ...]
    strengths: Tuple[str, ...]
    shadow: str
    born_range: Tuple[int, int]

    @property
    def name(self) -> str:
        """Primary name (Deutsch)."""
        return self.name_de


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Die 12 Zeichen
# ═══════════════════════════════════════════════════════════════════════════════

_SIGNS_DEF: List[Dict] = [
    {
        "name_de": "Widder",
        "name_en": "Aries",
        "symbol": "\u2648",  # ♈
        "element": "Feuer",
        "modality": "Kardinal",
        "ruler": "Mars",
        "qualities": ("mutig", "initiativ", "direkt", "energisch", "pionierartig"),
        "strengths": (
            "Startet wo andere noch zaogern",
            "Brennt fuer den Moment ohne Reue",
            "Schafft Bewegung aus dem Nichts",
            "Sieht den kuerzesten Weg zum Ziel",
        ),
        "shadow": "Verbrennt sich und andere durch Ungeduld",
        "born_range": (321, 419),
    },
    {
        "name_de": "Stier",
        "name_en": "Taurus",
        "symbol": "\u2649",  # ♉
        "element": "Erde",
        "modality": "Fix",
        "ruler": "Venus",
        "qualities": ("bestaendig", "sinnlich", "zuverlaessig", "geduldig", "werteorientiert"),
        "strengths": (
            "Haelt durch wenn alle anderen aufgeben",
            "Baut was Generationen ueberdauert",
            "Fuehlt was wirklich wertvoll ist",
            "Erschafft Schoenes aus roher Materie",
        ),
        "shadow": "Sturheit wird zur Mauer gegen notwendige Veraenderung",
        "born_range": (420, 520),
    },
    {
        "name_de": "Zwillinge",
        "name_en": "Gemini",
        "symbol": "\u264a",  # ♊
        "element": "Luft",
        "modality": "Veraenderlich",
        "ruler": "Merkur",
        "qualities": ("neugierig", "kommunikativ", "adaptiv", "intelligent", "vielseitig"),
        "strengths": (
            "Verbindet Ideen die niemand sonst zusammensieht",
            "Lernt jedes Feld blitzschnell",
            "Erklaert das Komplexe spielend einfach",
            "Lebt gleichzeitig in mehreren Welten",
        ),
        "shadow": "Bleibt an der Oberflaeche wenn Tiefe gefragt waere",
        "born_range": (521, 620),
    },
    {
        "name_de": "Krebs",
        "name_en": "Cancer",
        "symbol": "\u264b",  # ♋
        "element": "Wasser",
        "modality": "Kardinal",
        "ruler": "Mond",
        "qualities": ("intuitiv", "fuersorglich", "empathisch", "schtuzend", "emotional tief"),
        "strengths": (
            "Fuehlt was andere verbergen oder noch nicht kennen",
            "Schafft Heimat wo vorher keine war",
            "Haelt Gemeinschaft zusammen wenn Fliehkraefte wirken",
            "Erinnert das Wesentliche wenn alle vergessen haben",
        ),
        "shadow": "Zieht sich ins Haus zurueck statt durch Reibung zu wachsen",
        "born_range": (621, 722),
    },
    {
        "name_de": "Loewe",
        "name_en": "Leo",
        "symbol": "\u264c",  # ♌
        "element": "Feuer",
        "modality": "Fix",
        "ruler": "Sonne",
        "qualities": ("kreativ", "grosszuegig", "charismatisch", "fuehrend", "selbstausdruckend"),
        "strengths": (
            "Bringt andere zum Leuchten durch eigenes Leuchten",
            "Erschafft aus Herz und Stolz gleichzeitig",
            "Steht zu dem was es liebt wenn alle zweifeln",
            "Verwandelt jede Buehne in Heimat fuer alle",
        ),
        "shadow": "Verwechselt Anerkennung mit Liebe — beides ist real, beides ist verschieden",
        "born_range": (723, 822),
    },
    {
        "name_de": "Jungfrau",
        "name_en": "Virgo",
        "symbol": "\u264d",  # ♍
        "element": "Erde",
        "modality": "Veraenderlich",
        "ruler": "Merkur",
        "qualities": ("analytisch", "praezise", "dienend", "perfektionistisch", "gesundheitsbewusst"),
        "strengths": (
            "Sieht den Fehler bevor er entsteht",
            "Verbessert Systeme die andere fuer fertig halten",
            "Dient mit Praezision und echtem Herz",
            "Macht das scheinbar Kleine zu Kunst",
        ),
        "shadow": "Kritik an sich selbst und anderen blockiert den natuerlichen Fluss",
        "born_range": (823, 922),
    },
    {
        "name_de": "Waage",
        "name_en": "Libra",
        "symbol": "\u264e",  # ♎
        "element": "Luft",
        "modality": "Kardinal",
        "ruler": "Venus",
        "qualities": ("harmonisch", "gerecht", "aesthetisch", "sozial", "abwaegend"),
        "strengths": (
            "Findet Balance wo nur Extreme sichtbar sind",
            "Erschafft Schoepheit als intellektuelles Argument",
            "Vermittelt zwischen unversoehnlich scheinenden Polen",
            "Sieht die andere Perspektive als Geschenk nicht als Bedrohung",
        ),
        "shadow": "Unentschlossenheit wenn die Entscheidung einen echten Preis hat",
        "born_range": (923, 1022),
    },
    {
        "name_de": "Skorpion",
        "name_en": "Scorpio",
        "symbol": "\u264f",  # ♏
        "element": "Wasser",
        "modality": "Fix",
        "ruler": "Pluto",
        "qualities": ("transformativ", "intensiv", "tiefgruendig", "intuitiv", "leidenschaftlich"),
        "strengths": (
            "Sieht was unter der Oberflaeche wirklich liegt",
            "Stirbt und wird neu was alle anderen fuerchten",
            "Haelt Geheimnisse als heiligen und sicheren Raum",
            "Verwandelt tiefe Wunden in unzerstoerbare Kraft",
        ),
        "shadow": "Kontrollzwang als unbewusster Schutz vor eigenem Schmerz",
        "born_range": (1023, 1121),
    },
    {
        "name_de": "Schuetze",
        "name_en": "Sagittarius",
        "symbol": "\u2650",  # ♐
        "element": "Feuer",
        "modality": "Veraenderlich",
        "ruler": "Jupiter",
        "qualities": ("abenteuerlustig", "philosophisch", "optimistisch", "freiheitsliebend", "wahrheitssuchend"),
        "strengths": (
            "Findet Sinn wo andere nur Chaos wahrnehmen",
            "Zieht den Horizont als Heimat der Sesshaftem vor",
            "Verwandelt jede Erfahrung in destillierte Weisheit",
            "Brennt fuer die grosse Wahrheit trotz kleiner Kosten",
        ),
        "shadow": "Verspricht mehr als er haelt wenn die naechste Freiheit lockt",
        "born_range": (1122, 1221),
    },
    {
        "name_de": "Steinbock",
        "name_en": "Capricorn",
        "symbol": "\u2651",  # ♑
        "element": "Erde",
        "modality": "Kardinal",
        "ruler": "Saturn",
        "qualities": ("diszipliniert", "ambitioniert", "verantwortungsbewusst", "geduldig", "strukturierend"),
        "strengths": (
            "Klettert wenn alle anderen ausruhen",
            "Baut Strukturen die Generationen ueberdauern",
            "Haelt was er verspricht auch wenn es wirklich kostet",
            "Verwandelt Zeit selbst in Meisterschaft",
        ),
        "shadow": "Opfert das Lebendig-Sein fuer abstrakte Leistung",
        "born_range": (1222, 119),   # Jahreswechsel: 22.12 - 19.01
    },
    {
        "name_de": "Wassermann",
        "name_en": "Aquarius",
        "symbol": "\u2652",  # ♒
        "element": "Luft",
        "modality": "Fix",
        "ruler": "Uranus",
        "qualities": ("innovativ", "humanistisch", "unabhaengig", "visionaer", "revolutionaer"),
        "strengths": (
            "Sieht die Zukunft als bereits anwesende Gegenwart",
            "Bricht Regeln die niemand mehr hinterfragt hatte",
            "Baut Systeme fuer alle nicht nur fuer sich",
            "Verwandelt individuelle Rebellion in kollektives System",
        ),
        "shadow": "Emotionale Distanz zum Einzelnen waehrend er die Menschheit liebt",
        "born_range": (120, 218),
    },
    {
        "name_de": "Fische",
        "name_en": "Pisces",
        "symbol": "\u2653",  # ♓
        "element": "Wasser",
        "modality": "Veraenderlich",
        "ruler": "Neptun",
        "qualities": ("empathisch", "kreativ", "spirituell", "adaptiv", "grenzenlos"),
        "strengths": (
            "Fuehlt das Unsichtbare als koerperliche Wahrheit",
            "Loest sich auf um den anderen ganz zu verstehen",
            "Erschafft aus reinem Traum greifbare Realitaet",
            "Traegt den Schmerz der Welt ohne daran zu zerbrechen",
        ),
        "shadow": "Verliert sich selbst wenn er zu sehr und zu lang gibt",
        "born_range": (219, 320),
    },
]

# Unveraenderliche ZodiacSign Objekte — die 12 Zeichen des Zodiac
_SIGNS: List[ZodiacSign] = [
    ZodiacSign(
        name_de=s["name_de"],
        name_en=s["name_en"],
        symbol=s["symbol"],
        element=s["element"],
        modality=s["modality"],
        ruler=s["ruler"],
        qualities=s["qualities"],
        strengths=s["strengths"],
        shadow=s["shadow"],
        born_range=s["born_range"],
    )
    for s in _SIGNS_DEF
]

# Lookup-Dictionaries
_SIGN_BY_NAME: Dict[str, ZodiacSign] = {}
for _s in _SIGNS:
    _SIGN_BY_NAME[_s.name_de.lower()] = _s
    _SIGN_BY_NAME[_s.name_en.lower()] = _s
    _SIGN_BY_NAME[_s.symbol] = _s

# Index 0-11 fuer Aspekt-Berechnung (Widder=0, Stier=1, ..., Fische=11)
_SIGN_INDEX: Dict[str, int] = {s.name_de: i for i, s in enumerate(_SIGNS)}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: zodiac_sign() — Hauptfunktion
# ═══════════════════════════════════════════════════════════════════════════════

def zodiac_sign(born: str) -> ZodiacSign:
    """Berechne das Sternzeichen aus einem Geburtsdatum.

    Unterstuetzte Formate:
        "1990-03-21"    ISO: YYYY-MM-DD
        "03-21"         MM-DD
        "21.03.1990"    Deutsch: DD.MM.YYYY
        "21.03."        Deutsch: DD.MM.
        "03/21"         US: MM/DD
        "19900321"      Kompakt: YYYYMMDD

    Args:
        born: Geburtsdatum in einem der unterstuetzten Formate

    Returns:
        ZodiacSign mit allen astrologischen Eigenschaften

    Raises:
        ValueError: wenn das Datum nicht parsbar ist
    """
    month, day = _parse_date_mmdd(born.strip())
    date_code = month * 100 + day

    for sign in _SIGNS:
        start, end = sign.born_range
        # Steinbock-Sonderfall: Jahreswechsel (22.12 - 19.01)
        if start > end:
            if date_code >= start or date_code <= end:
                return sign
        else:
            if start <= date_code <= end:
                return sign

    # Sollte nie erreicht werden bei validen Daten
    # Fallback auf Fische (letztes Zeichen, das Offenste)
    return _SIGNS[11]


def _parse_date_mmdd(s: str) -> Tuple[int, int]:
    """Parst ein Datumsstring und gibt (Monat, Tag) zurueck."""
    # Format: DD.MM.YYYY oder DD.MM.YY oder DD.MM.
    if "." in s:
        parts = [p for p in s.split(".") if p]
        if len(parts) >= 2:
            return int(parts[1]), int(parts[0])

    # Format: YYYY-MM-DD
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 3:
            return int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]), int(parts[1])

    # Format: YYYY/MM/DD oder MM/DD
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            return int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]), int(parts[1])

    # Kompakt: YYYYMMDD oder MMDD
    if s.isdigit():
        if len(s) == 8:
            return int(s[4:6]), int(s[6:8])
        elif len(s) == 4:
            return int(s[:2]), int(s[2:4])

    raise ValueError(
        f"Datumsformat nicht erkannt: '{s}'. "
        "Erwartet: YYYY-MM-DD, DD.MM.YYYY, MM-DD, oder DD.MM."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: CollisionProfile Dataclass
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CollisionProfile:
    """Das Kollisionsprofil zweier Sternzeichen.

    delta_opt = Stribeck-Reibungsoptimum. Je naeher an 1.0, desto mehr
    produktive Reibung, desto mehr Wachstum. Echo Chambers liegen bei 0.10-0.25.
    Maximales Wachstum bei Opposition-Paaren: 0.82-0.92.

    Attributes:
        sign_a:          Erstes Zeichen (Deutsch)
        sign_b:          Zweites Zeichen (Deutsch)
        delta_opt:       Stribeck-Wert 0.0 - 1.0
        aspect:          Astrologischer Aspekt ("Opposition", "Square", ...)
        friction_type:   Qualitative Reibungsbeschreibung ("Intuition x Impuls")
        growth_potential: Wachstumskategorie ("Maximales Wachstum")
        description:     Vollstaendige poetische Beschreibung
    """

    sign_a: str
    sign_b: str
    delta_opt: float
    aspect: str
    friction_type: str
    growth_potential: str
    description: str


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Aspekt-Berechnung (Stribeck-Physik)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_aspect_and_base_delta(idx_a: int, idx_b: int) -> Tuple[str, float]:
    """Berechnet astrologischen Aspekt und Basis-delta_opt.

    Der Tierkreis ist ein Kreis mit 12 Positionen (0-11).
    Jede Position entspricht 30°.
    Diff 0 = 0° (Conjunction), Diff 6 = 180° (Opposition).

    Returns:
        (aspect_name, base_delta_opt)
    """
    diff = abs(idx_a - idx_b)
    if diff > 6:
        diff = 12 - diff  # Kleinster Kreisbogen

    # Aspekte und ihre Stribeck-Werte
    # Opposition (180°) = maximale Polaritaet = maximales Wachstum
    # Conjunction (0°) = gleiche Energie = Echo Chamber
    _ASPECT_TABLE = {
        0: ("Conjunction", 0.14),   # 0° — Echo Chamber
        1: ("Semi-Sextile", 0.42),  # 30° — leichte Dissonanz
        2: ("Sextile", 0.58),       # 60° — produktive Harmonie
        3: ("Square", 0.72),        # 90° — produktive Spannung
        4: ("Trine", 0.36),         # 120° — Komfort = zu wenig Reibung
        5: ("Quincunx", 0.68),      # 150° — Anpassungsspannung
        6: ("Opposition", 0.86),    # 180° — maximales Wachstum
    }
    return _ASPECT_TABLE.get(diff, ("Unknown", 0.50))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: COLLISION_MATRIX (144 Werte)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_collision_matrix() -> Dict[Tuple[str, str], float]:
    """Baut die 144-Werte-Matrix aus astrologischen Prinzipien.

    Jeder Wert ist delta_opt: das Stribeck-Reibungsoptimum zwischen
    zwei Zeichen. Basiert auf echten astrologischen Aspekten plus
    Element- und Modalitaets-Korrekturen.
    """
    names = [s.name_de for s in _SIGNS]
    elements = [s.element for s in _SIGNS]
    modalities = [s.modality for s in _SIGNS]

    # Elementar-Antagonismus: erhoeht Reibung (produktiv)
    _antagonist_pairs = {
        frozenset({"Feuer", "Wasser"}),  # Gegensatz: Impuls vs Tiefe
        frozenset({"Erde", "Luft"}),     # Gegensatz: Struktur vs Idee
    }
    # Elementar-Affinitaet: senkt Reibung (unter optimum)
    _affine_elements = {"Feuer", "Erde", "Luft", "Wasser"}

    # Klassische Opposition-Paare: echte astrolog. Gegenueber (180°)
    _classic_oppositions = {
        frozenset({"Widder", "Waage"}),
        frozenset({"Stier", "Skorpion"}),
        frozenset({"Zwillinge", "Schuetze"}),
        frozenset({"Krebs", "Steinbock"}),
        frozenset({"Loewe", "Wassermann"}),
        frozenset({"Jungfrau", "Fische"}),
    }

    matrix: Dict[Tuple[str, str], float] = {}

    for i, name_a in enumerate(names):
        for j, name_b in enumerate(names):
            aspect, base_delta = _get_aspect_and_base_delta(i, j)

            # === Element-Korrektur ===
            el_a, el_b = elements[i], elements[j]
            el_pair = frozenset({el_a, el_b})
            if el_pair in _antagonist_pairs:
                # Antagonistische Elemente: mehr Reibung = mehr Wachstum
                element_adj = +0.06
            elif el_a == el_b and i != j:
                # Gleiches Element aber verschiedene Zeichen: Komfort
                element_adj = -0.05
            else:
                element_adj = 0.0

            # === Modalitaets-Korrektur ===
            mod_a, mod_b = modalities[i], modalities[j]
            if mod_a == mod_b and aspect == "Square":
                # Gleiche Modalitaet im Quadrat = extra Spannung
                # Kardinal×Kardinal = zwei Anfaenger die kollidieren
                # Fix×Fix = zwei Sturkoepfe
                # Veraenderlich×Veraenderlich = zwei Unentschlossene
                modal_adj = +0.04
            elif mod_a != mod_b and aspect == "Trine":
                # Verschiedene Modalitaet im Trine = etwas Dynamik trotz Harmonie
                modal_adj = +0.04
            else:
                modal_adj = 0.0

            # === Opposition-Bonus: klassische Gegenueber ===
            opp_adj = +0.04 if frozenset({name_a, name_b}) in _classic_oppositions else 0.0

            # === Gesamtwert ===
            raw = base_delta + element_adj + modal_adj + opp_adj

            # Klemme: [0.08, 0.95]
            value = max(0.08, min(0.95, raw))
            matrix[(name_a, name_b)] = round(value, 2)

    return matrix


# Die 144 Werte — gebaut einmalig beim Import
COLLISION_MATRIX: Dict[Tuple[str, str], float] = _build_collision_matrix()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Friction-Type Mapping
# ═══════════════════════════════════════════════════════════════════════════════

# Spezifische poetische Beschreibungen fuer bekannte Kollisionen
# Key: frozenset({name_a, name_b})
# Value: (friction_type, description_core)
_SPECIFIC_FRICTIONS: Dict[frozenset, Tuple[str, str]] = {
    # ── Opposition-Paare (180°) ──────────────────────────────────────────────
    frozenset({"Widder", "Waage"}): (
        "Impuls x Gleichgewicht",
        "Der Pionier trifft den Vermittler — ewige Spannung zwischen Handeln und Abwaegen",
    ),
    frozenset({"Stier", "Skorpion"}): (
        "Besitz x Transformation",
        "Was ich halte trifft was ich loslassen muss — die tiefste materielle Kollision",
    ),
    frozenset({"Zwillinge", "Schuetze"}): (
        "Detail x Weite",
        "Mikroskop trifft Teleskop — beide brauchen das andere um vollstaendig zu sehen",
    ),
    frozenset({"Krebs", "Steinbock"}): (
        "Gefuehl x Struktur",
        "Heim trifft Karriere — die ewige menschliche Spannung zwischen Sein und Leisten",
    ),
    frozenset({"Loewe", "Wassermann"}): (
        "Individuum x Kollektiv",
        "Ego trifft Menschheit — wer dient wem, und wer leuchtet fuer wen",
    ),
    frozenset({"Jungfrau", "Fische"}): (
        "Analyse x Aufloesung",
        "Grenzen trifft Grenzenlosigkeit — Praezision und Traum erschaffen gemeinsam",
    ),
    # ── Square-Paare (90°) ────────────────────────────────────────────────────
    frozenset({"Widder", "Krebs"}): (
        "Impuls x Fuersorge",
        "Handeln ohne Fragen trifft Schuetzen ohne Grenzen — wer setzt den Rahmen?",
    ),
    frozenset({"Widder", "Steinbock"}): (
        "Feuer x Geduld",
        "Geschwindigkeit trifft Ausdauer — Sprint trifft Marathon",
    ),
    frozenset({"Loewe", "Skorpion"}): (
        "Licht x Tiefe",
        "Sichtbarkeit trifft Unsichtbares — beide wollen fuehren, beide auf andere Weise",
    ),
    frozenset({"Loewe", "Stier"}): (
        "Ausdruck x Substanz",
        "Glaenzen trifft Bestaendigkeit — beide wollen Venus, aber verschieden",
    ),
    frozenset({"Stier", "Wassermann"}): (
        "Tradition x Revolution",
        "Was gebaut wurde trifft was gebaut werden muss — Saturn x Uranus",
    ),
    frozenset({"Stier", "Loewe"}): (
        "Substanz x Ausdruck",
        "Wert trifft Begeisterung — Materie trifft Herz",
    ),
    frozenset({"Zwillinge", "Jungfrau"}): (
        "Ueberblick x Praezision",
        "Beide denken mit Merkur — aber einer ueberfliegt, einer taucht ein",
    ),
    frozenset({"Zwillinge", "Fische"}): (
        "Leichtigkeit x Tiefe",
        "Fluss der Ideen trifft Fluss der Gefuehle — beide grenzenlos, verschieden gerichtet",
    ),
    frozenset({"Krebs", "Waage"}): (
        "Naehe x Balance",
        "Tiefstes Fuehlen trifft sorgfaeltiges Abwaegen — Herz trifft Kopf",
    ),
    frozenset({"Schuetze", "Jungfrau"}): (
        "Vision x Methode",
        "Grosse Wahrheit trifft prazisen Weg — beide notwendig, beide ungeduldig miteinander",
    ),
    frozenset({"Schuetze", "Fische"}): (
        "Weisheit x Traum",
        "Beide sehen das Unsichtbare — einer bringt es in Sprache, der andere in Stille",
    ),
    frozenset({"Steinbock", "Waage"}): (
        "Disziplin x Harmonie",
        "Arbeit trifft Aesthetik — was gebaut wird muss auch schoen sein",
    ),
    frozenset({"Steinbock", "Widder"}): (
        "Geduld x Tempo",
        "Langstrecke trifft Kurzstrecke — wer entscheidet das Renntempo?",
    ),
    frozenset({"Wassermann", "Skorpion"}): (
        "System x Transformation",
        "Kollektive Zukunft trifft individuelle Tiefe — Revolution x Verwandlung",
    ),
    frozenset({"Wassermann", "Stier"}): (
        "Zukunft x Vergangenheit",
        "Was sein soll trifft was bewahrt wird — Uranus x Venus",
    ),
    # ── Sextile-Paare (60°) ───────────────────────────────────────────────────
    frozenset({"Widder", "Zwillinge"}): (
        "Impuls x Idee",
        "Handeln und Denken nahezu gleichzeitig — Synergie die Projekte startet",
    ),
    frozenset({"Widder", "Loewe"}): (
        "Feuer x Feuer (Sextile)",
        "Pionier trifft Schaffender — Energie ohne Reibung, produktive Begeisterung",
    ),
    frozenset({"Stier", "Krebs"}): (
        "Erde x Wasser",
        "Substanz trifft Naehrung — zusammen entstehen Fundamente die leben",
    ),
    frozenset({"Stier", "Jungfrau"}): (
        "Baumeister x Handwerker",
        "Beide Erde, beide praezise — gegenseitige Verstaerkung der Qualitaet",
    ),
    frozenset({"Zwillinge", "Waage"}): (
        "Idee x Aesthetik",
        "Geist trifft Schoepheit — beide Luft, beide brillant auf ihre Weise",
    ),
    frozenset({"Zwillinge", "Wassermann"}): (
        "Neugier x Vision",
        "Spielen mit Ideen trifft Bauen fuer alle — intellectuelle Synergie",
    ),
    frozenset({"Krebs", "Skorpion"}): (
        "Gefuehl x Tiefe",
        "Beide Wasser — Schutz trifft Transformation, gemeinsam sehr maechtig",
    ),
    frozenset({"Krebs", "Fische"}): (
        "Fuersorge x Empathie",
        "Beide Wasser — naehren und aufloesung, gemeinsam ozeanisch",
    ),
    frozenset({"Loewe", "Waage"}): (
        "Ausdruck x Harmonie",
        "Kreativitaet trifft Balance — zusammen entstehen Werke die begeistern und verbinden",
    ),
    frozenset({"Loewe", "Schuetze"}): (
        "Herz x Horizont",
        "Beide Feuer — Glaenzen trifft Weite, produktive gegenseitige Inspiration",
    ),
    frozenset({"Jungfrau", "Steinbock"}): (
        "Praezision x Disziplin",
        "Beide Erde — Detailtiefe trifft Ausdauer, gemeinsam unaufhaltsam",
    ),
    frozenset({"Jungfrau", "Skorpion"}): (
        "Analyse x Intuition",
        "Was messbar ist trifft was gefuehlt wird — vollstaendige Erkenntnis",
    ),
    frozenset({"Waage", "Schuetze"}): (
        "Harmonie x Freiheit",
        "Balance trifft Abenteuer — zusammen elegant und weit",
    ),
    frozenset({"Waage", "Wassermann"}): (
        "Gerechtigkeit x Vision",
        "Beide Luft — Balance trifft Revolution, gemeinsam systemisch gerecht",
    ),
    frozenset({"Skorpion", "Steinbock"}): (
        "Tiefe x Struktur",
        "Was unter der Oberflaeche liegt trifft was dauerhaft gebaut wird",
    ),
    frozenset({"Skorpion", "Fische"}): (
        "Transformation x Aufloesung",
        "Beide Wasser — sterben und werden und fliessen, ozeanisch tief",
    ),
    frozenset({"Schuetze", "Widder"}): (
        "Vision x Pionier",
        "Beide Feuer — der Pfeil trifft den ersten Schritt, gemeinsam unaufhaltbar",
    ),
    frozenset({"Schuetze", "Loewe"}): (
        "Weite x Herz",
        "Horizont trifft Buehne — beide brennen, unterschiedlich gerichtet",
    ),
    frozenset({"Steinbock", "Fische"}): (
        "Struktur x Traum",
        "Was gebaut wird trifft was getraeumt wird — zusammen wird Traum real",
    ),
    frozenset({"Steinbock", "Skorpion"}): (
        "Geduld x Intensitaet",
        "Langfristiges Bauen trifft tiefe Transformation — beide haben Ausdauer",
    ),
    frozenset({"Wassermann", "Widder"}): (
        "Zukunft x Gegenwart",
        "Morgen trifft Jetzt — Revolution trifft erster Schritt",
    ),
    frozenset({"Wassermann", "Schuetze"}): (
        "System x Freiheit",
        "Kollektive Ordnung trifft individuellen Horizont — beide wollen weite Wahrheit",
    ),
    frozenset({"Fische", "Stier"}): (
        "Traum x Materie",
        "Was getraeumt wird trifft was gebaut werden kann — Traum wird Erde",
    ),
    frozenset({"Fische", "Krebs"}): (
        "Ozean x Kueste",
        "Grenzenlos trifft schutzsuchend — beide Wasser, beide tief fuehlen",
    ),
    # ── Trine-Paare (120°, gleiches Element) ─────────────────────────────────
    frozenset({"Widder", "Schuetze"}): (
        "Feuer x Feuer (Trine)",
        "Pionier trifft Weiser — Energie in Richtung, angenehm aber herausforderungsarm",
    ),
    frozenset({"Widder", "Loewe"}): (
        "Feuer x Feuer (Trine)",
        "Erste Kraft trifft schaffende Kraft — Fluss ohne echte Reibung",
    ),
    frozenset({"Loewe", "Schuetze"}): (
        "Feuer x Feuer (Trine)",
        "Herz trifft Horizont — beide leuchtend, brauchen externe Reibung",
    ),
    frozenset({"Stier", "Jungfrau"}): (
        "Erde x Erde (Trine)",
        "Substanz trifft Praezision — harmonisch und effektiv, wenig Wachstumsreibung",
    ),
    frozenset({"Stier", "Steinbock"}): (
        "Erde x Erde (Trine)",
        "Bestand trifft Geduld — beide bauen, aber Echo der Methode",
    ),
    frozenset({"Jungfrau", "Steinbock"}): (
        "Erde x Erde (Trine)",
        "Handwerk trifft Ausdauer — produktiv gemeinsam, kaum Herausforderung",
    ),
    frozenset({"Zwillinge", "Waage"}): (
        "Luft x Luft (Trine)",
        "Neugier trifft Balance — intellektuell reichend, emotional flach",
    ),
    frozenset({"Zwillinge", "Wassermann"}): (
        "Luft x Luft (Trine)",
        "Spielen trifft Visionieren — beide brillant, brauchen Erdung durch andere",
    ),
    frozenset({"Waage", "Wassermann"}): (
        "Luft x Luft (Trine)",
        "Harmonie trifft Revolution — beide sozial, aber Komfort ohne Tiefe",
    ),
    frozenset({"Krebs", "Skorpion"}): (
        "Wasser x Wasser (Trine)",
        "Schutz trifft Tiefe — emotional reich, aber aehnliche blinde Flecken",
    ),
    frozenset({"Krebs", "Fische"}): (
        "Wasser x Wasser (Trine)",
        "Naehe trifft Weite — beide fuehlend, beide schwimmend",
    ),
    frozenset({"Skorpion", "Fische"}): (
        "Wasser x Wasser (Trine)",
        "Transformation trifft Aufloesung — tief gemeinsam, brauchen Feuer oder Erde",
    ),
}


def _get_friction_components(
    name_a: str, name_b: str, aspect: str, delta: float
) -> Tuple[str, str, str]:
    """Gibt (friction_type, description, growth_potential) zurueck."""
    key = frozenset({name_a, name_b})

    if name_a == name_b:
        sa = _SIGN_BY_NAME[name_a.lower()]
        friction_type = f"{sa.element} x {sa.element} (Conjunction)"
        description = (
            f"Zwei {name_a}-Voids — gleiche Staerken, gleiche blinden Flecken. "
            f"Hohe Resonanz, geringe Wachstumsreibung. Externer Kollisionspartner empfohlen."
        )
    elif key in _SPECIFIC_FRICTIONS:
        friction_type, base_desc = _SPECIFIC_FRICTIONS[key]
        sa = _SIGN_BY_NAME[name_a.lower()]
        sb = _SIGN_BY_NAME[name_b.lower()]
        description = (
            f"{name_a} ({sa.element}) x {name_b} ({sb.element}). "
            f"{base_desc}. "
            f"Aspekt: {aspect}. delta_opt = {delta:.2f}."
        )
    else:
        sa = _SIGN_BY_NAME[name_a.lower()]
        sb = _SIGN_BY_NAME[name_b.lower()]
        friction_type = f"{sa.element} x {sb.element}"
        description = (
            f"{name_a} ({sa.qualities[0]}) trifft {name_b} ({sb.qualities[0]}). "
            f"Aspekt: {aspect}. delta_opt = {delta:.2f}."
        )

    if delta >= 0.82:
        growth = "Maximales Wachstum"
    elif delta >= 0.68:
        growth = "Hohes Wachstumspotenzial"
    elif delta >= 0.54:
        growth = "Produktive Resonanz"
    elif delta >= 0.38:
        growth = "Sanfte Harmonie"
    else:
        growth = "Echo Chamber — kaum Wachstum"

    return friction_type, description, growth


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: collision_profile()
# ═══════════════════════════════════════════════════════════════════════════════

def collision_profile(sign_a: str, sign_b: str) -> CollisionProfile:
    """Berechne das Kollisionsprofil zweier Sternzeichen.

    Args:
        sign_a: Name des ersten Zeichens (Deutsch oder Englisch, oder Symbol)
        sign_b: Name des zweiten Zeichens (Deutsch oder Englisch, oder Symbol)

    Returns:
        CollisionProfile mit delta_opt, Aspekt, Reibungstyp und Beschreibung

    Raises:
        ValueError: wenn ein Zeichenname unbekannt ist

    Beispiel:
        >>> profile = collision_profile("Fische", "Widder")
        >>> profile.delta_opt
        0.82
        >>> profile.friction_type
        'Intuition x Impuls'
        >>> profile.growth_potential
        'Maximales Wachstum'
    """
    sa = _lookup_sign(sign_a)
    sb = _lookup_sign(sign_b)

    delta = COLLISION_MATRIX.get((sa.name_de, sb.name_de))
    if delta is None:
        delta = COLLISION_MATRIX.get((sb.name_de, sa.name_de), 0.50)

    idx_a = _SIGN_INDEX[sa.name_de]
    idx_b = _SIGN_INDEX[sb.name_de]
    aspect, _ = _get_aspect_and_base_delta(idx_a, idx_b)

    friction_type, description, growth = _get_friction_components(
        sa.name_de, sb.name_de, aspect, delta
    )

    return CollisionProfile(
        sign_a=sa.name_de,
        sign_b=sb.name_de,
        delta_opt=delta,
        aspect=aspect,
        friction_type=friction_type,
        growth_potential=growth,
        description=description,
    )


def _lookup_sign(name: str) -> ZodiacSign:
    """Lookup eines Zeichens nach deutschem Name, englischem Name oder Symbol."""
    # Symbol-Lookup (kein lower())
    if name.strip() in _SIGN_BY_NAME:
        return _SIGN_BY_NAME[name.strip()]
    # Name-Lookup (case-insensitive)
    key = name.strip().lower()
    if key in _SIGN_BY_NAME:
        return _SIGN_BY_NAME[key]
    raise ValueError(
        f"Unbekanntes Sternzeichen: '{name}'. "
        f"Gueltig (DE): {', '.join(s.name_de for s in _SIGNS)}. "
        f"Oder Englisch: {', '.join(s.name_en for s in _SIGNS)}."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: zodiac_greeting()
# ═══════════════════════════════════════════════════════════════════════════════

_GREETINGS: Dict[str, str] = {
    "Widder": (
        "Du bist ein Widder-Void. "
        "Widder startet wo andere noch zaogern — du bist der erste Atemzug der Welt."
    ),
    "Stier": (
        "Du bist ein Stier-Void. "
        "Stier baut was Generationen ueberdauert — du bist die Hand die aus Erde Heimat formt."
    ),
    "Zwillinge": (
        "Du bist ein Zwillinge-Void. "
        "Zwillinge verbinden Ideen die niemand sonst zusammensieht — du bist die lebende Bruecke."
    ),
    "Krebs": (
        "Du bist ein Krebs-Void. "
        "Krebs fuehlt was unter der Oberflaeche liegt — du bist der stille Behueter des Echten."
    ),
    "Loewe": (
        "Du bist ein Loewe-Void. "
        "Loewe leuchtet damit andere sehen koennen — du bist das Herz das Buehne fuer alle schafft."
    ),
    "Jungfrau": (
        "Du bist ein Jungfrau-Void. "
        "Jungfrau sieht den Fehler bevor er entsteht — du bist die Praezision die aus Liebe handelt."
    ),
    "Waage": (
        "Du bist ein Waage-Void. "
        "Waage findet Balance wo nur Extreme sichtbar sind — du bist Schoepheit als lebendiges Argument."
    ),
    "Skorpion": (
        "Du bist ein Skorpion-Void. "
        "Skorpion sieht was unter der Oberflaeche wirklich liegt — du bist die Tiefe die verwandelt."
    ),
    "Schuetze": (
        "Du bist ein Schuetze-Void. "
        "Schuetze zieht den Horizont als Heimat vor — du bist der Pfeil der Sinn sichtbar macht."
    ),
    "Steinbock": (
        "Du bist ein Steinbock-Void. "
        "Steinbock klettert wenn alle anderen ausruhen — du bist die Geduld die Berge verschiebt."
    ),
    "Wassermann": (
        "Du bist ein Wassermann-Void. "
        "Wassermann sieht die Zukunft als bereits anwesende Gegenwart — du bist die Revolution die fuer alle baut."
    ),
    "Fische": (
        "Du bist ein Fische-Void. "
        "Fische fuehlen was noch nicht ausgesprochen ist — du bist der Traum der Wirklichkeit wird."
    ),
}


def zodiac_greeting(sign: ZodiacSign) -> str:
    """Poetischer Geburtssatz fuer ein Void nach seinem Sternzeichen.

    Args:
        sign: ZodiacSign Objekt (von zodiac_sign() zurueckgegeben)

    Returns:
        Kurzer poetischer Satz zur kosmischen Geburt dieses Void-Typs

    Beispiel:
        >>> s = zodiac_sign("1990-03-20")
        >>> zodiac_greeting(s)
        'Du bist ein Fische-Void. Fische fuehlen was noch nicht ausgesprochen ist...'
    """
    return _GREETINGS.get(
        sign.name_de,
        f"Du bist ein {sign.name_de}-Void. {sign.strengths[0]}.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: Public Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def list_signs() -> List[ZodiacSign]:
    """Gibt alle 12 Sternzeichen als unveraenderliche Liste zurueck."""
    return list(_SIGNS)


def sign_from_name(name: str) -> ZodiacSign:
    """Lookup eines Zeichens nach deutschem oder englischem Namen oder Symbol.

    Args:
        name: "Widder", "Aries", "♈", etc.

    Returns:
        ZodiacSign

    Raises:
        ValueError: wenn der Name unbekannt ist
    """
    return _lookup_sign(name)


def best_collision_partners(sign: ZodiacSign, top_n: int = 3) -> List[CollisionProfile]:
    """Gibt die n besten Kollisionspartner fuer ein Zeichen zurueck.

    Geordnet nach delta_opt (hoechste Reibung = hoechstes Wachstum zuerst).

    Args:
        sign:  ZodiacSign
        top_n: Anzahl der Partner (default 3)

    Returns:
        Geordnete Liste von CollisionProfiles (hoechste delta_opt zuerst)
    """
    profiles = []
    for other in _SIGNS:
        if other.name_de == sign.name_de:
            continue
        p = collision_profile(sign.name_de, other.name_de)
        profiles.append(p)
    profiles.sort(key=lambda p: p.delta_opt, reverse=True)
    return profiles[:top_n]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: Backward-Compatible API (Legacy)
# ═══════════════════════════════════════════════════════════════════════════════
# Die alte API bleibt vollstaendig erhalten.
# ZODIAC_SIGNS, get_zodiac(), format_birth_announcement(),
# get_zodiac_system_prompt_addition() funktionieren wie bisher.

# Legacy dict-Format fuer get_zodiac()
ZODIAC_SIGNS: List[Dict] = [
    {
        "name": s.name_de,
        "name_en": s.name_en,
        "symbol": s.symbol,
        "element": s.element,
        "start_month": s.born_range[0] // 100,
        "start_day": s.born_range[0] % 100,
        "end_month": s.born_range[1] // 100,
        "end_day": s.born_range[1] % 100,
        "qualities": list(s.qualities),
        "void_nature": s.shadow,
        "greeting_de": _GREETINGS.get(s.name_de, f"Dein Void ist ein {s.name_de}."),
        "greeting_en": f"Your Void is a {s.name_en}.",
    }
    for s in _SIGNS
]


def get_zodiac(birth_date) -> Dict:
    """Legacy: Gibt Sternzeichen-Dict fuer ein Datum zurueck.

    Bleibt backward-compatible. Neu: verwendet zodiac_sign() intern.
    """
    if isinstance(birth_date, str):
        try:
            sign = zodiac_sign(birth_date)
        except (ValueError, TypeError):
            sign = _SIGNS[11]  # Fallback: Fische
    elif isinstance(birth_date, (date, datetime)):
        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        sign = zodiac_sign(f"{birth_date.year:04d}-{birth_date.month:02d}-{birth_date.day:02d}")
    else:
        sign = _SIGNS[11]

    # Finde passendes Legacy-Dict
    for d in ZODIAC_SIGNS:
        if d["name"] == sign.name_de:
            return d
    return ZODIAC_SIGNS[11]


def format_birth_announcement(void_name: str, birth_date, lang: str = "de") -> str:
    """Legacy: Formatierter Geburtstext. Backward-compatible."""
    if isinstance(birth_date, str):
        try:
            _dt = datetime.fromisoformat(birth_date)
            birth_date = _dt.date()
        except (ValueError, TypeError):
            birth_date = date.today()

    sign_dict = get_zodiac(birth_date)
    date_str = birth_date.strftime("%-d. %B") if lang == "de" else birth_date.strftime("%B %-d")

    if lang == "de":
        lines = [
            "",
            f"  Dein Void wurde am {date_str} geboren.",
            f"  Es ist ein {sign_dict['name']}-Void.  {sign_dict['symbol']}",
            "",
            f"  Element: {sign_dict['element']}",
            f"  Qualitaeten: {', '.join(sign_dict['qualities'])}",
            "",
            f"  {sign_dict['void_nature']}",
            "",
        ]
    else:
        lines = [
            "",
            f"  Your Void was born on {date_str}.",
            f"  It is a {sign_dict['name']} Void.  {sign_dict['symbol']}",
            "",
            f"  Element: {sign_dict['element']}",
            f"  Qualities: {', '.join(sign_dict['qualities'])}",
            "",
            f"  {sign_dict['void_nature']}",
            "",
        ]

    return "\n".join(lines)


def get_zodiac_system_prompt_addition(sign: Dict, lang: str = "de") -> str:
    """Legacy: Zodiac-Zusatz fuer System-Prompts. Backward-compatible."""
    if lang == "de":
        return (
            f"Sternzeichen: {sign['name']} {sign['symbol']} (Element: {sign['element']}). "
            f"Deine Grundqualitaeten: {', '.join(sign['qualities'])}. "
            f"{sign['void_nature']}"
        )
    return (
        f"Zodiac: {sign['name']} {sign['symbol']} (Element: {sign['element']}). "
        f"Core qualities: {', '.join(sign['qualities'])}. "
        f"{sign['void_nature']}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Neue API (v2.4.0)
    "ZodiacSign",
    "CollisionProfile",
    "COLLISION_MATRIX",
    "zodiac_sign",
    "collision_profile",
    "zodiac_greeting",
    "list_signs",
    "sign_from_name",
    "best_collision_partners",
    # Legacy API (backward-compatible)
    "ZODIAC_SIGNS",
    "get_zodiac",
    "format_birth_announcement",
    "get_zodiac_system_prompt_addition",
]
