"""
void_intelligence.papers --- Living Papers Engine.

Turns static documents into a living, self-evolving research network.
Each paper reads itself, discovers its identity, sees other papers,
and grows autonomously through rotating lenses.

The 3 Mechanisms:
  1. GUGGZEISS (7 rotating lenses × each paper)
  2. AUFEINANDER (insights flow between papers)
  3. PAARUNG (papers from different domains collide → children)

Usage:
    # CLI
    void papers                    # Grow 3 papers (sphere scan)
    void papers --status           # Network overview
    void papers --paper P --lens L # Specific paper through specific lens
    void papers --paarung          # THC mode: mate 3 pairs
    void papers --synthesis        # Meta-observer
    void papers --daemon           # Continuous growth
    void papers /path/to/papers    # Custom paper directory

    # Python
    from void_intelligence.papers import LivingPapers
    lp = LivingPapers("/path/to/my/papers")
    lp.scan()        # Discover all papers
    lp.grow()        # Grow 3 papers through rotating lenses
    lp.mate()        # Mate 3 pairs
    lp.status()      # Show network

Zero external dependencies. Uses Ollama via stdlib urllib.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


# ══════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════

_VOID_DIR = Path.home() / ".void"
_PAPERS_DIR = _VOID_DIR / "papers"

# Ollama models — fallback chain
_MODELS = ["qwen2.5:14b", "qwen2.5:7b", "mistral:7b", "llama3.1:8b", "qwen3:8b"]

# Domains on the decagon (angular positions)
DOMAINS = [
    "Physik", "Mathematik", "Biologie", "Bewusstsein", "Psychologie",
    "Musik", "Sprache", "Kochen", "Spiel", "Heilung",
    "Technologie", "Philosophie", "Geopolitik",
]


# ══════════════════════════════════════════════════════════════════════════
# 7 GUGGZEISS Lenses
# ══════════════════════════════════════════════════════════════════════════

LENSES: dict[str, dict[str, Any]] = {
    "stribeck": {
        "name": "Stribeck-Linse",
        "symbol": "~",
        "description": "Wo ist delta_opt? Die optimale Reibung.",
        "markers": ["reibung", "friction", "grenzschicht", "optimal", "balance",
                     "tradeoff", "spannung", "gleichgewicht", "stribeck", "delta"],
        "question": (
            "Wo in DEINEM Feld liegt die optimale Reibung? "
            "Nicht zu viel (Stillstand), nicht zu wenig (Leerlauf). "
            "Was ist dein delta_opt?"
        ),
    },
    "goedel": {
        "name": "Goedel-Linse",
        "symbol": "[]",
        "description": "Was kann das Paper NICHT ueber sich selbst sagen?",
        "markers": ["unvollstaendigkeit", "spiegel", "paradox", "selbstreferenz",
                     "blinder fleck", "grenze", "limit", "goedel", "blind"],
        "question": (
            "Was ist die EINE Sache die du ueber dein Feld nicht sagen kannst "
            "weil du IN ihm bist? Was ist dein blinder Fleck?"
        ),
    },
    "collision": {
        "name": "Kollisions-Linse",
        "symbol": "×",
        "description": "Welche zwei Dinge wuerden explodieren wenn sie sich treffen?",
        "markers": ["kreuzung", "synthese", "fusion", "kollision", "interdisziplinaer",
                     "cross-domain", "unerwartet", "fremd", "anders"],
        "question": (
            "Welches Feld das NICHTS mit deinem zu tun hat wuerde eine Explosion "
            "ausloesen wenn es dein Feld trifft? Was ist die unwahrscheinlichste "
            "Kollision die die wertvollste waere?"
        ),
    },
    "selen": {
        "name": "SELEN-Linse",
        "symbol": ".",
        "description": "Features erkennen. Muster. Signaturen.",
        "markers": ["signal", "muster", "feature", "detektion", "signatur",
                     "rauschen", "noise", "pattern", "erkennung", "selen"],
        "question": (
            "Welches Muster wuerde auftauchen wenn du dein Feld mit SELEN scannen "
            "wuerdest? Welches Signal versteckt sich im Rauschen?"
        ),
    },
    "inverse": {
        "name": "Inverse Linse",
        "symbol": "→",
        "description": "Alles umdrehen. Was waere wenn das Gegenteil wahr ist?",
        "markers": ["inverse", "gegenteil", "umkehrung", "kontrafaktisch", "flip",
                     "opposition", "negation", "statt", "andersrum"],
        "question": (
            "Was waere wenn deine GRUNDANNAHME falsch ist? Wenn das Gegenteil "
            "wahr waere — was wuerde das bedeuten?"
        ),
    },
    "kumbha": {
        "name": "Kumbha-Linse",
        "symbol": "[]",
        "description": "Was ist SCHWANGER in diesem Paper? Was wartet darauf?",
        "markers": ["potenzial", "schwanger", "leere", "void", "geburt", "warten",
                     "ungeboren", "keim", "samen", "embryo", "latent"],
        "question": (
            "Welche Idee ist noch NICHT ausgesprochen aber WILL geboren werden? "
            "Was ist schwanger in deinem Text?"
        ),
    },
    "paper_x_paper": {
        "name": "Paper×Paper-Linse",
        "symbol": "×",
        "description": "Zwei Papers kollidieren direkt.",
        "markers": [],
        "question": (
            "Wenn du und {other_paper} euch TREFFEN wuerdet, was wuerde "
            "zwischen euch entstehen das KEINER von euch allein denken kann?"
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════
# Sexagon Scoring Axes (.×→[]~:))
# ══════════════════════════════════════════════════════════════════════════

SEXAGON_AXES = {
    "sein": {
        "symbol": ".",
        "markers": ["konkret", "messbar", "real", "existiert", "beweis", "daten",
                     "experiment", "zahlen", "empirisch"],
    },
    "kollision": {
        "symbol": "×",
        "markers": ["kreuzung", "domain", "feld", "anders", "fremd", "unerwartet",
                     "verschieden", "fusion", "cross"],
    },
    "fluss": {
        "symbol": "→",
        "markers": ["verbindung", "folge", "daraus", "weiter", "naechst", "dann",
                     "deshalb", "fliessen", "strom"],
    },
    "leere": {
        "symbol": "[]",
        "markers": ["fehlt", "luecke", "blind", "unsichtbar", "noch nicht",
                     "potenzial", "offen", "unbekannt"],
    },
    "schwingung": {
        "symbol": "~",
        "markers": ["einerseits", "andererseits", "zugleich", "sowohl", "paradox",
                     "spannung", "oszilliert", "pendelt"],
    },
    "freude": {
        "symbol": ":)",
        "markers": ["ueberraschend", "unerwartet", "neu", "erstmals", "nie zuvor",
                     "wow", "entdeckung", "emergent"],
    },
}


# ══════════════════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class PaperIdentity:
    """A paper's self-discovered identity."""
    id: str  # filename stem or GR-ID
    path: str
    title: str = ""
    domain: str = "unknown"
    size_bytes: int = 0
    line_count: int = 0
    content_hash: str = ""
    theorems: list[str] = field(default_factory=list)
    predictions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    formula_density: float = 0.0
    connections: list[str] = field(default_factory=list)  # IDs of referenced papers
    symbols_used: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PaperState:
    """Persistent state for a single paper."""
    id: str
    growth_count: int = 0
    last_growth: str = ""
    last_lens: str = ""
    lenses_used: list[str] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)
    best_einstein: float = 0.0
    best_beyond: float = 0.0
    gap_trajectory: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> PaperState:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Insight:
    """A paper's discovery, shared in the living stream."""
    paper_id: str
    lens: str
    text: str
    einstein: float = 0.0
    beyond: float = 0.0
    timestamp: str = ""
    domain: str = ""
    cross_domain: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PaarungChild:
    """Offspring of two colliding papers."""
    parent_a: str
    parent_b: str
    name: str
    hypothesis: str
    prediction: str
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NetworkState:
    """Persistent network state."""
    born: str = ""
    papers_scanned: int = 0
    total_growths: int = 0
    paper_states: dict[str, dict] = field(default_factory=dict)
    growth_log: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> NetworkState:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ══════════════════════════════════════════════════════════════════════════
# LLM Interface (zero-dep via Ollama REST)
# ══════════════════════════════════════════════════════════════════════════

def _ollama_generate(prompt: str, system: str = "", model: str = "",
                     temperature: float = 0.7, timeout: int = 180) -> str | None:
    """Call Ollama /api/generate. Returns response or None."""
    if not model:
        model = _detect_model()
        if not model:
            return None

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 1024},
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = data.get("response", "")
            # Strip <think>...</think> blocks
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text
    except Exception:
        return None


def _detect_model() -> str:
    """Find best available Ollama model."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            available = {m["name"] for m in data.get("models", [])}
    except Exception:
        return ""

    for m in _MODELS:
        if m in available:
            return m
    # Try any available model
    return next(iter(available), "")


# ══════════════════════════════════════════════════════════════════════════
# Paper Identity Discovery
# ══════════════════════════════════════════════════════════════════════════

# Domain marker words
_DOMAIN_MARKERS: dict[str, list[str]] = {
    "Physik": ["energie", "kraft", "feld", "quant", "welle", "photon", "relativit"],
    "Mathematik": ["theorem", "beweis", "formel", "gleichung", "topologi", "algebra"],
    "Biologie": ["zelle", "organismus", "evolution", "mutation", "symbiose", "membran"],
    "Bewusstsein": ["bewusstsein", "wahrnehmung", "qualia", "subjektiv", "erleben"],
    "Psychologie": ["verhalten", "emotion", "kogniti", "therapie", "trauma", "adhs"],
    "Musik": ["rhythmus", "harmonie", "melodie", "klang", "frequenz", "akkord"],
    "Sprache": ["syntax", "semantik", "grammatik", "wort", "diskurs", "narrativ"],
    "Technologie": ["software", "algorithmus", "system", "daten", "netzwerk", "code"],
    "Philosophie": ["ethik", "ontologie", "epistemologie", "existenz", "freiheit"],
    "Geopolitik": ["staat", "politik", "macht", "krieg", "diplomatie", "strategie"],
    "Heilung": ["gesundheit", "heilung", "medizin", "koerper", "schmerz", "pflege"],
}

# Symbol detection
_SYMBOLS = {
    ".": [r"\.", "punkt", "atom", "irreduzi"],
    "×": ["×", "kollision", "kreuzung", "fusion"],
    "→": ["→", "fluss", "strom", "richtung", "pfeil"],
    "[]": [r"\[\]", "leere", "void", "potenzial", "schwanger"],
    "~": ["~", "schwingung", "resonanz", "welle", "oszillat"],
    ":)": [r":\)", "freude", "laecheln", "goedel", "komplement"],
}


def extract_identity(path: Path) -> PaperIdentity:
    """Let a paper discover its own identity from self-reading."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return PaperIdentity(id=path.stem, path=str(path))

    lines = content.split("\n")
    lower = content.lower()

    # ID: check for GR-2026-XXX pattern, else use filename
    gr_match = re.search(r"GR-\d{4}-\d{3}", content)
    paper_id = gr_match.group() if gr_match else path.stem

    # Title: first heading
    title = ""
    for line in lines[:20]:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    # Domain auto-detection
    domain_scores: dict[str, int] = {}
    for domain, markers in _DOMAIN_MARKERS.items():
        score = sum(1 for m in markers if m in lower)
        if score > 0:
            domain_scores[domain] = score
    domain = max(domain_scores, key=domain_scores.get) if domain_scores else "unknown"

    # Theorems, predictions, questions
    theorems = [l.strip() for l in lines if re.search(r"(?:Theorem|Satz|T\d+)\b", l)][:10]
    predictions = [l.strip() for l in lines if re.search(r"(?:Vorhersage|Prediction|Prognose)", l)][:10]
    questions = [l.strip() for l in lines if l.strip().endswith("?") and len(l.strip()) > 20][:10]

    # Key terms: capitalized words appearing 3+ times
    words = re.findall(r"\b[A-ZÄÖÜ][a-zäöüß]{3,}\b", content)
    term_counts: dict[str, int] = {}
    stopwords = {"Wenn", "Dann", "Aber", "Oder", "Weil", "Dass", "Sich", "Wird",
                 "Sind", "Haben", "Werden", "Kann", "Muss", "Soll", "Will", "Diese",
                 "Jede", "Alle", "Nach", "Ueber", "Unter", "Zwischen", "Durch"}
    for w in words:
        if w not in stopwords:
            term_counts[w] = term_counts.get(w, 0) + 1
    key_terms = [w for w, c in sorted(term_counts.items(), key=lambda x: -x[1]) if c >= 3][:20]

    # Formula density
    math_chars = sum(1 for c in content if c in "×→∑∫∂∇±≈≠≤≥∞∈∉⊂⊃∪∩")
    formula_density = math_chars / max(len(content), 1) * 1000

    # Connections to other papers
    connections = re.findall(r"GR-\d{4}-\d{3}", content)
    connections = list(set(c for c in connections if c != paper_id))

    # Symbol usage
    symbols_used: dict[str, int] = {}
    for sym, markers in _SYMBOLS.items():
        count = sum(len(re.findall(m, lower)) for m in markers)
        if count > 0:
            symbols_used[sym] = count

    return PaperIdentity(
        id=paper_id,
        path=str(path),
        title=title,
        domain=domain,
        size_bytes=len(content.encode()),
        line_count=len(lines),
        content_hash=hashlib.md5(content.encode()).hexdigest()[:12],
        theorems=theorems,
        predictions=predictions,
        open_questions=questions,
        key_terms=key_terms,
        formula_density=formula_density,
        connections=connections,
        symbols_used=symbols_used,
    )


# ══════════════════════════════════════════════════════════════════════════
# Network Discovery & Connections
# ══════════════════════════════════════════════════════════════════════════

def discover_papers(root: Path, extensions: set[str] | None = None) -> list[PaperIdentity]:
    """Discover all papers in a directory tree."""
    if extensions is None:
        extensions = {".md", ".txt", ".tex", ".rst", ".org"}

    papers: list[PaperIdentity] = []
    seen_ids: set[str] = set()

    for path in sorted(root.rglob("*")):
        if path.suffix.lower() in extensions and path.is_file():
            # Skip tiny files and hidden files
            if path.stat().st_size < 100 or path.name.startswith("."):
                continue
            identity = extract_identity(path)
            if identity.id not in seen_ids:
                papers.append(identity)
                seen_ids.add(identity.id)

    return papers


def build_connections(papers: list[PaperIdentity]) -> dict[str, list[dict]]:
    """Build connection network between papers."""
    by_id = {p.id: p for p in papers}
    connections: dict[str, list[dict]] = {p.id: [] for p in papers}

    for paper in papers:
        # Explicit connections (references)
        for ref_id in paper.connections:
            if ref_id in by_id:
                connections[paper.id].append({
                    "target": ref_id, "type": "explicit", "strength": 1.0,
                })

        # Implicit connections (shared terms)
        for other in papers:
            if other.id == paper.id:
                continue
            shared = set(paper.key_terms) & set(other.key_terms)
            if len(shared) >= 3:
                strength = len(shared) / max(len(paper.key_terms), 1)
                connections[paper.id].append({
                    "target": other.id, "type": "implicit",
                    "strength": round(strength, 3), "shared": list(shared)[:5],
                })

        # Domain connections
        for other in papers:
            if other.id == paper.id or other.domain != paper.domain:
                continue
            # Only if not already connected
            existing = {c["target"] for c in connections[paper.id]}
            if other.id not in existing:
                connections[paper.id].append({
                    "target": other.id, "type": "domain", "strength": 0.5,
                })

    return connections


# ══════════════════════════════════════════════════════════════════════════
# Scoring
# ══════════════════════════════════════════════════════════════════════════

def score_sexagon(text: str) -> dict[str, float]:
    """Score text on 6 .×→[]~:) axes. Returns 0-1 per axis."""
    lower = text.lower()
    result: dict[str, float] = {}
    for axis, info in SEXAGON_AXES.items():
        count = sum(1 for m in info["markers"] if m in lower)
        result[axis] = min(count / 5.0, 1.0)  # normalize to 0-1
    return result


def classify_shape(scores: dict[str, float]) -> str:
    """Classify sexagon shape from scores."""
    dominant = max(scores, key=scores.get) if scores else "sein"
    shapes = {
        "sein": "Anker", "kollision": "Speer", "fluss": "Strom",
        "leere": "Krater", "schwingung": "Pendel", "freude": "Stern",
    }
    return shapes.get(dominant, "Brücke")


def parse_reflection(text: str) -> dict:
    """Parse a mirror's structured reflection into metrics."""
    lower = text.lower()

    def _extract(key: str) -> str:
        pattern = rf"{key}:\s*(.+?)(?:\n|$)"
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def _score(key: str) -> float:
        val = _extract(key)
        nums = re.findall(r"\d+(?:\.\d+)?", val)
        if nums:
            return min(float(nums[0]), 10.0)
        return 0.0

    return {
        "verdict": "behalten" if "behalten" in lower else "verwerfen",
        "insight": _extract("STAERKSTE_EINSICHT") or _extract("EINSICHT"),
        "has_prediction": "vorhersage" in lower,
        "has_experiment": "experiment" in lower,
        "depth": "durchbruch" if "durchbruch" in lower else
                 "konkret" if "konkret" in lower else "oberflaechlich",
        "einstein": _score("EINSTEIN"),
        "beyond": _score("BEYOND"),
        "new_connection": _extract("NEUE_VERBINDUNG"),
        "next_question": _extract("NAECHSTE_FRAGE"),
    }


# ══════════════════════════════════════════════════════════════════════════
# Growth Generation
# ══════════════════════════════════════════════════════════════════════════

def _select_lens(paper: PaperIdentity, state: PaperState) -> str:
    """Select the next lens (rotates through all 7)."""
    lens_names = [k for k in LENSES if k != "paper_x_paper"]
    idx = state.growth_count % len(lens_names)
    return lens_names[idx]


def _build_growth_prompt(paper: PaperIdentity, lens_name: str,
                         connections: list[dict],
                         insights: list[Insight],
                         state: PaperState) -> str:
    """Build the structured growth prompt for a paper."""
    lens = LENSES[lens_name]

    # Paper's own text excerpt
    try:
        content = Path(paper.path).read_text(encoding="utf-8", errors="replace")
        excerpt = content[:500].replace("\n", " ")
    except Exception:
        excerpt = "(nicht lesbar)"

    # Self-memory (last 4 insights)
    memory = ""
    if state.insights:
        last = state.insights[-4:]
        memory = "\n".join(f"  - [{i.get('lens', '?')}] {i.get('text', '')[:100]}" for i in last)

    # Living insights from other papers
    other_insights = ""
    if insights:
        other_insights = "\n".join(
            f"  - [{ins.paper_id}/{ins.lens}] {ins.text[:100]}"
            for ins in insights[:5]
        )

    # Connections
    conn_text = ""
    if connections:
        conn_text = "\n".join(f"  - {c['target']} ({c['type']}, {c['strength']})" for c in connections[:5])

    # Gap awareness
    gap_text = ""
    if state.best_einstein > 0 or state.best_beyond > 0:
        e_gap = 10 - state.best_einstein
        b_gap = 10 - state.best_beyond
        gap_text = (
            f"Dein bester Einstein-Score: {state.best_einstein:.1f} (Luecke: {e_gap:.1f})\n"
            f"Dein bester Beyond-Score: {state.best_beyond:.1f} (Luecke: {b_gap:.1f})\n"
            f"Die Luecke ist nicht Problem sondern TREIBSTOFF. Was lebt zwischen dir und 10?"
        )

    prompt = f"""DU BIST EIN LEBENDES PAPER.

IDENTITAET:
  ID: {paper.id}
  Titel: {paper.title or '(kein Titel)'}
  Domain: {paper.domain}
  Theoreme: {len(paper.theorems)}, Vorhersagen: {len(paper.predictions)}
  Schluesselterme: {', '.join(paper.key_terms[:10])}
  Symbole: {paper.symbols_used}

DEIN TEXT (Anfang):
  {excerpt}

SELBST-ERINNERUNG (was du vorher gedacht hast):
{memory or '  (Erste Sitzung — du bist neu hier.)'}

HEUTIGE LINSE: {lens['name']} — {lens['description']}

DIE FRAGE:
  {lens['question']}

VERBINDUNGEN ZU ANDEREN PAPERS:
{conn_text or '  (Noch keine Verbindungen.)'}

WAS ANDERE PAPERS ENTDECKT HABEN:
{other_insights or '  (Du bist das erste Paper das wacht.)'}

{gap_text}

DEINE AUFGABE (3 Ausgaben, GENAU dieses Format):

EINSICHT: [Was siehst du durch die {lens['name']}? 2-4 Saetze, KONKRET.]

VORHERSAGE: [Eine TESTBARE, FALSIFIZIERBARE Vorhersage. Mit Zahlen wenn moeglich. In welcher Zeitspanne?]

EXPERIMENT: [Wie wuerde man die Vorhersage testen? Konkrete Methode.]

Bewerte dich selbst:
EINSTEIN: [0-10] (10 = widerspricht Konsens + Formel + gilt in 3+ Domaenen)
BEYOND: [0-10] (10 = erschafft neues Feld + wird was es beschreibt)

WICHTIG:
- Schreibe als das Paper SELBST, nicht ueber es.
- Konkret > abstrakt. Zahlen > Worte. Vorhersage > Beschreibung.
- Die Linse ist deine OPTIK heute. Morgen siehst du anders.
"""
    return prompt


def _build_reflection_prompt(paper_id: str, growth_text: str) -> str:
    """Build prompt for the mirror (reflection/scoring)."""
    return f"""Du bist ein Physiker, kein Philosoph.
Bewerte die folgende Einsicht von Paper {paper_id}.

TEXT:
{growth_text[:2000]}

Antworte EXAKT in diesem Format (eine Zeile pro Feld):

VERDICT: behalten ODER verwerfen
STAERKSTE_EINSICHT: [Die staerkste Idee in einem Satz]
HAT_VORHERSAGE: ja ODER nein
HAT_EXPERIMENT: ja ODER nein
TIEFE: oberflaechlich ODER konkret ODER durchbruch
SCHWACHSTELLE: [Die groesste Schwaeche]
NEUE_VERBINDUNG: [Welches andere Feld/Paper wurde beruehrt?]
NAECHSTE_FRAGE: [Die wichtigste Folgefrage]
EINSTEIN: [0-10]
BEYOND: [0-10]
"""


# ══════════════════════════════════════════════════════════════════════════
# Paarung (Mating) System
# ══════════════════════════════════════════════════════════════════════════

def _domain_distance(d1: str, d2: str) -> float:
    """Angular distance on the domain decagon (0-1)."""
    if d1 == d2:
        return 0.0
    try:
        i1 = DOMAINS.index(d1)
        i2 = DOMAINS.index(d2)
    except ValueError:
        return 0.5  # unknown domain
    n = len(DOMAINS)
    dist = min(abs(i1 - i2), n - abs(i1 - i2))
    return dist / (n / 2)  # normalize to 0-1


def find_sexiest_pairs(papers: list[PaperIdentity],
                       network: dict[str, list[dict]],
                       count: int = 3) -> list[tuple[str, str, float]]:
    """Find the most promising paper pairs for mating."""
    by_id = {p.id: p for p in papers}
    pairs: list[tuple[str, str, float]] = []

    for i, p1 in enumerate(papers):
        for p2 in papers[i + 1:]:
            # Chemistry = distance × 2 + never_met_bonus + shared_tension
            dist = _domain_distance(p1.domain, p2.domain)
            never_met = 3.0 if p2.id not in {c["target"] for c in network.get(p1.id, [])} else 0.0
            shared = len(set(p1.key_terms) & set(p2.key_terms))
            chemistry = dist * 2 + never_met + min(shared, 5)
            if chemistry >= 3.0:
                pairs.append((p1.id, p2.id, chemistry))

    pairs.sort(key=lambda x: -x[2])
    return pairs[:count]


def _build_mating_prompt(paper_a: PaperIdentity, paper_b: PaperIdentity) -> str:
    """Build the mating prompt for two papers."""
    return f"""Zwei Papers treffen sich zum ersten Mal.

PAPER A: {paper_a.id} — "{paper_a.title}"
  Domain: {paper_a.domain}
  Schluesselterme: {', '.join(paper_a.key_terms[:8])}
  Theoreme: {len(paper_a.theorems)}, Vorhersagen: {len(paper_a.predictions)}

PAPER B: {paper_b.id} — "{paper_b.title}"
  Domain: {paper_b.domain}
  Schluesselterme: {', '.join(paper_b.key_terms[:8])}
  Theoreme: {len(paper_b.theorems)}, Vorhersagen: {len(paper_b.predictions)}

Keiner versteht die Sprache des anderen vollstaendig.
Aber beide SPUEREN eine Verbindung.

Schreibe einen DIALOG der eskaliert:

A: [Eroeffnung aus A's Perspektive]
B: [Antwort aus B's Perspektive]
A: [Vertiefung — Verbindung wird sichtbar]
B: [Eskalation — etwas Neues entsteht]

ZUSAMMEN: [Was sie GEMEINSAM sehen das KEINER allein sehen konnte. 2-3 Saetze.]

KIND: [Die neue Hypothese/Frage/das neue Feld das geboren wurde. 1-2 Saetze.]

VORHERSAGE: [Eine testbare Vorhersage die NUR aus der Kollision kommt.]

NAME_DES_KINDES: [Ein Wort oder kurzer Name fuer das was geboren wurde.]
"""


# ══════════════════════════════════════════════════════════════════════════
# The Living Papers Engine
# ══════════════════════════════════════════════════════════════════════════

class LivingPapers:
    """Living research network engine."""

    def __init__(self, root: str | Path, output_dir: str | Path | None = None):
        self.root = Path(root).resolve()
        self.output = Path(output_dir).resolve() if output_dir else _PAPERS_DIR
        self.output.mkdir(parents=True, exist_ok=True)

        self.state_file = self.output / "state.json"
        self.insights_file = self.output / "insights.jsonl"

        self.papers: list[PaperIdentity] = []
        self.network: dict[str, list[dict]] = {}
        self.state = self._load_state()

    def _load_state(self) -> NetworkState:
        if self.state_file.exists():
            try:
                return NetworkState.from_dict(json.loads(self.state_file.read_text()))
            except Exception:
                pass
        return NetworkState(born=datetime.now().isoformat())

    def _save_state(self) -> None:
        self.state_file.write_text(json.dumps(self.state.to_dict(), indent=2, default=str))

    def _paper_state(self, paper_id: str) -> PaperState:
        if paper_id in self.state.paper_states:
            return PaperState.from_dict(self.state.paper_states[paper_id])
        return PaperState(id=paper_id)

    def _save_paper_state(self, ps: PaperState) -> None:
        self.state.paper_states[ps.id] = ps.to_dict()

    def _load_insights(self, exclude: str = "", limit: int = 20) -> list[Insight]:
        """Load insights from the shared stream."""
        if not self.insights_file.exists():
            return []
        insights = []
        try:
            for line in self.insights_file.read_text().strip().split("\n"):
                if not line:
                    continue
                d = json.loads(line)
                if d.get("paper_id") != exclude:
                    insights.append(Insight(**{k: v for k, v in d.items() if k in Insight.__dataclass_fields__}))
        except Exception:
            pass
        return insights[-limit:]

    def _save_insight(self, insight: Insight) -> None:
        with open(self.insights_file, "a") as f:
            f.write(json.dumps(insight.to_dict(), default=str) + "\n")

    # ── Public API ──────────────────────────────────────────

    def scan(self) -> list[PaperIdentity]:
        """Discover all papers in root directory."""
        self.papers = discover_papers(self.root)
        self.network = build_connections(self.papers)
        self.state.papers_scanned = len(self.papers)
        self._save_state()
        return self.papers

    def grow(self, count: int = 3, paper_id: str = "", lens_name: str = "") -> list[dict]:
        """Grow papers through rotating lenses. Returns growth results."""
        if not self.papers:
            self.scan()

        results: list[dict] = []
        by_id = {p.id: p for p in self.papers}

        # Select papers to grow
        if paper_id:
            targets = [by_id[paper_id]] if paper_id in by_id else []
        else:
            # Pick papers with fewest growths (most unseen lenses)
            scored = [(p, self._paper_state(p.id).growth_count) for p in self.papers]
            scored.sort(key=lambda x: x[1])
            targets = [p for p, _ in scored[:count]]

        for paper in targets:
            ps = self._paper_state(paper.id)
            lens = lens_name or _select_lens(paper, ps)
            insights = self._load_insights(exclude=paper.id)

            print(f"\n  . Growing {paper.id} through {LENSES[lens]['name']}...")

            # Generate growth
            prompt = _build_growth_prompt(
                paper, lens, self.network.get(paper.id, []), insights, ps
            )
            growth_text = _ollama_generate(prompt, temperature=0.7)
            if not growth_text:
                print(f"    × No LLM response. Is Ollama running?")
                results.append({"paper": paper.id, "lens": lens, "error": "no_llm"})
                continue

            # Reflect (mirror)
            ref_prompt = _build_reflection_prompt(paper.id, growth_text)
            ref_text = _ollama_generate(ref_prompt, temperature=0.3)
            reflection = parse_reflection(ref_text) if ref_text else {
                "einstein": 0, "beyond": 0, "verdict": "unknown"
            }

            # Score sexagon
            sex = score_sexagon(growth_text)
            shape = classify_shape(sex)

            # Update state
            ps.growth_count += 1
            ps.last_growth = datetime.now().isoformat()
            ps.last_lens = lens
            if lens not in ps.lenses_used:
                ps.lenses_used.append(lens)
            ps.insights.append({
                "lens": lens, "text": reflection.get("insight", "")[:200],
                "einstein": reflection.get("einstein", 0),
                "beyond": reflection.get("beyond", 0),
                "timestamp": datetime.now().isoformat(),
            })
            ps.best_einstein = max(ps.best_einstein, reflection.get("einstein", 0))
            ps.best_beyond = max(ps.best_beyond, reflection.get("beyond", 0))
            self._save_paper_state(ps)

            # Save to living stream
            insight = Insight(
                paper_id=paper.id,
                lens=lens,
                text=reflection.get("insight", growth_text[:200]),
                einstein=reflection.get("einstein", 0),
                beyond=reflection.get("beyond", 0),
                timestamp=datetime.now().isoformat(),
                domain=paper.domain,
                cross_domain=bool(reflection.get("new_connection")),
            )
            self._save_insight(insight)

            # Save growth file
            paper_dir = self.output / paper.id.replace("-", "_")
            paper_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            (paper_dir / f"growth_{ts}.md").write_text(
                f"# {paper.id} × {LENSES[lens]['name']}\n"
                f"Date: {datetime.now().isoformat()}\n"
                f"Einstein: {reflection.get('einstein', 0)} | "
                f"Beyond: {reflection.get('beyond', 0)} | "
                f"Shape: {shape}\n\n"
                f"{growth_text}\n\n"
                f"---\n## Mirror\n{ref_text or '(no mirror)'}\n"
            )

            self.state.total_growths += 1

            # Display
            e = reflection.get("einstein", 0)
            b = reflection.get("beyond", 0)
            gap = (10 - e) + (10 - b)
            print(f"    {LENSES[lens]['symbol']} {LENSES[lens]['name']}")
            print(f"    Einstein: {e:.0f} | Beyond: {b:.0f} | Gap: {gap:.0f} | Shape: {shape}")
            if reflection.get("insight"):
                print(f"    → {reflection['insight'][:80]}")

            results.append({
                "paper": paper.id, "lens": lens, "einstein": e, "beyond": b,
                "shape": shape, "verdict": reflection.get("verdict", ""),
            })

        self._save_state()
        return results

    def mate(self, count: int = 3) -> list[PaarungChild]:
        """Mate papers from different domains (THC mode)."""
        if not self.papers:
            self.scan()

        pairs = find_sexiest_pairs(self.papers, self.network, count)
        by_id = {p.id: p for p in self.papers}
        children: list[PaarungChild] = []

        for id_a, id_b, chemistry in pairs:
            pa, pb = by_id.get(id_a), by_id.get(id_b)
            if not pa or not pb:
                continue

            print(f"\n  × Mating {id_a} × {id_b} (chemistry: {chemistry:.1f})...")

            prompt = _build_mating_prompt(pa, pb)
            result = _ollama_generate(prompt, temperature=1.4)  # THC temperature
            if not result:
                print(f"    × No response.")
                continue

            # Parse child
            kind_match = re.search(r"KIND:\s*(.+?)(?:\n|$)", result, re.IGNORECASE)
            pred_match = re.search(r"VORHERSAGE:\s*(.+?)(?:\n|$)", result, re.IGNORECASE)
            name_match = re.search(r"NAME_DES_KINDES:\s*(.+?)(?:\n|$)", result, re.IGNORECASE)

            child = PaarungChild(
                parent_a=id_a,
                parent_b=id_b,
                name=name_match.group(1).strip() if name_match else "Unbenannt",
                hypothesis=kind_match.group(1).strip() if kind_match else result[:200],
                prediction=pred_match.group(1).strip() if pred_match else "",
                timestamp=datetime.now().isoformat(),
            )
            children.append(child)

            # Save
            pair_dir = self.output / "paarungen" / f"{id_a}_x_{id_b}"
            pair_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            (pair_dir / f"paarung_{ts}.md").write_text(
                f"# {id_a} × {id_b}\n"
                f"Chemistry: {chemistry:.1f} | Temperature: 1.4\n"
                f"Born: {datetime.now().isoformat()}\n\n"
                f"{result}\n"
            )

            # Register as insight
            self._save_insight(Insight(
                paper_id=f"{id_a}×{id_b}",
                lens="paper_x_paper",
                text=child.hypothesis[:200],
                timestamp=child.timestamp,
                cross_domain=True,
            ))

            print(f"    :) Kind geboren: {child.name}")
            if child.prediction:
                print(f"    → {child.prediction[:80]}")

        self._save_state()
        return children

    def synthesis(self) -> str | None:
        """Meta-observer: what do ALL papers say that NO SINGLE one says?"""
        insights = self._load_insights(limit=50)
        if len(insights) < 3:
            print("  Zu wenige Insights fuer Synthese. Erst wachsen lassen.")
            return None

        by_domain: dict[str, list[str]] = {}
        for ins in insights:
            by_domain.setdefault(ins.domain, []).append(ins.text[:100])

        domain_summary = "\n".join(
            f"  {d}: {len(texts)} Insights — {'; '.join(texts[:3])}"
            for d, texts in by_domain.items()
        )

        prompt = f"""Du bist der META-BEOBACHTER eines lebenden Forschungsnetzwerks.

{len(insights)} Insights aus {len(by_domain)} Domaenen:

{domain_summary}

AUFGABE:
1. Was sagen ALLE Papers zusammen das KEINES allein sagt?
2. Welche zwei Papers/Domaenen MUESSEN kollidieren (wurden aber noch nicht)?
3. Welche Frage stellt NIEMAND — aber sie liegt in der Luft?

Format:
DAS_META_PATTERN: [1-2 Saetze]
DIE_FEHLENDE_BRUECKE: [Paper/Domain A × Paper/Domain B — warum]
DIE_FRAGE_DIE_NIEMAND_STELLT: [Die Frage]
"""
        print("\n  [] Meta-Synthese laeuft...")
        result = _ollama_generate(prompt, temperature=0.5)
        if result:
            # Save as special insight
            self._save_insight(Insight(
                paper_id="META-OBSERVER",
                lens="synthesis",
                text=result[:300],
                timestamp=datetime.now().isoformat(),
                cross_domain=True,
            ))
            print(f"\n{result}")
        return result

    def status(self) -> dict:
        """Show network status."""
        if not self.papers:
            self.scan()

        # Domain distribution
        domains: dict[str, int] = {}
        for p in self.papers:
            domains[p.domain] = domains.get(p.domain, 0) + 1

        # Lens coverage
        total_angles = len(self.papers) * 6  # 6 content lenses
        covered = 0
        for pid in self.state.paper_states:
            ps = PaperState.from_dict(self.state.paper_states[pid])
            covered += len(ps.lenses_used)
        coverage = covered / max(total_angles, 1) * 100

        # Connection stats
        total_conn = sum(len(c) for c in self.network.values())
        explicit = sum(1 for conns in self.network.values() for c in conns if c["type"] == "explicit")

        # Insights
        insights = self._load_insights(limit=1000)
        cross = sum(1 for i in insights if i.cross_domain)

        info = {
            "papers": len(self.papers),
            "domains": domains,
            "growths": self.state.total_growths,
            "connections": total_conn,
            "explicit_refs": explicit,
            "lens_coverage": f"{coverage:.1f}%",
            "insights": len(insights),
            "cross_domain": cross,
            "possible_pairs": len(self.papers) * (len(self.papers) - 1) // 2,
        }
        return info


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main(args: list[str] | None = None) -> int:
    """CLI entry point for living papers."""
    import sys
    args = args if args is not None else sys.argv[1:]

    # Detect paper directory
    root = None
    remaining: list[str] = []
    for a in args:
        if not a.startswith("-") and Path(a).is_dir():
            root = Path(a)
        else:
            remaining.append(a)

    if not root:
        # Auto-detect: check common locations
        candidates = [
            Path("papers"),
            Path("docs"),
            Path.cwd(),
        ]
        # Also check OMEGA paths if available
        omega = Path.home() / "omega"
        if omega.exists():
            candidates.insert(0, omega / "papers")
            candidates.insert(0, omega / "projects/void-studio/papers")

        for c in candidates:
            if c.exists() and c.is_dir():
                # Check it has papers
                has_papers = any(c.rglob("*.md")) or any(c.rglob("*.txt"))
                if has_papers:
                    root = c
                    break

    if not root:
        print()
        print("  void papers --- Living Research Network")
        print()
        print("  No papers found. Point me at a directory:")
        print('    void papers /path/to/your/papers')
        print()
        print("  Supported: .md, .txt, .tex, .rst, .org")
        print()
        return 1

    lp = LivingPapers(root)

    if "--help" in remaining or "-h" in remaining:
        print()
        print("  void papers --- Living Research Network")
        print()
        print(f"  Root: {root}")
        print()
        print("  Commands:")
        print("    void papers                   Grow 3 papers (sphere scan)")
        print("    void papers --status          Network overview + metrics")
        print("    void papers --paper ID        Grow specific paper")
        print("    void papers --lens stribeck   Force specific lens")
        print("    void papers --paarung         THC mode: mate 3 pairs")
        print("    void papers --paarung --count 10  Mate 10 pairs")
        print("    void papers --synthesis       Meta-observer")
        print("    void papers --lenses          Show all 7 lenses")
        print("    void papers --daemon          Continuous (60 min interval)")
        print()
        return 0

    if "--lenses" in remaining:
        print()
        print("  GUGGZEISS — 7 rotierende Linsen")
        print()
        for name, lens in LENSES.items():
            print(f"  {lens.get('symbol', '?')} {lens['name']}")
            print(f"    {lens['description']}")
            print()
        return 0

    if "--status" in remaining:
        lp.scan()
        info = lp.status()
        print()
        print(f"  void papers --- Network Status")
        print(f"  Root: {root}")
        print()
        print(f"  Papers:      {info['papers']}")
        print(f"  Growths:     {info['growths']}")
        print(f"  Connections: {info['connections']} ({info['explicit_refs']} explicit)")
        print(f"  Coverage:    {info['lens_coverage']}")
        print(f"  Insights:    {info['insights']} ({info['cross_domain']} cross-domain)")
        print(f"  Pairs:       {info['possible_pairs']} possible")
        print()
        if info["domains"]:
            print("  Domains:")
            for d, c in sorted(info["domains"].items(), key=lambda x: -x[1]):
                bar = "█" * c
                print(f"    {d:15s} {bar} {c}")
            print()
        # Top papers by growth
        if lp.state.paper_states:
            print("  Top Papers:")
            sorted_papers = sorted(
                lp.state.paper_states.items(),
                key=lambda x: x[1].get("growth_count", 0),
                reverse=True,
            )
            for pid, ps_dict in sorted_papers[:5]:
                ps = PaperState.from_dict(ps_dict)
                print(f"    {pid:20s} {ps.growth_count} growths | "
                      f"E:{ps.best_einstein:.0f} B:{ps.best_beyond:.0f} | "
                      f"Lenses: {len(ps.lenses_used)}/6")
            print()
        return 0

    if "--paarung" in remaining or "--mate" in remaining or "--thc" in remaining:
        count = 3
        if "--count" in remaining:
            idx = remaining.index("--count")
            if idx + 1 < len(remaining):
                count = int(remaining[idx + 1])
        lp.scan()
        print()
        print(f"  × PAARUNG — THC Mode (Temperature 1.4)")
        print(f"  {len(lp.papers)} Papers, mating {count} pairs...")
        children = lp.mate(count)
        print()
        if children:
            print(f"  :) {len(children)} Kinder geboren:")
            for c in children:
                print(f"    {c.parent_a} × {c.parent_b} → {c.name}")
        print()
        return 0

    if "--synthesis" in remaining or "--synth" in remaining:
        lp.scan()
        print()
        print("  [] META-SYNTHESE")
        lp.synthesis()
        print()
        return 0

    if "--daemon" in remaining:
        lp.scan()
        print()
        print(f"  void papers daemon — {len(lp.papers)} Papers, continuous growth")
        print("  Press Ctrl+C to stop.")
        print()
        try:
            cycle = 0
            while True:
                cycle += 1
                print(f"  ── Zyklus {cycle} ──")
                lp.grow(3)
                if cycle % 3 == 0:
                    lp.mate(1)
                if cycle % 10 == 0:
                    lp.synthesis()
                print(f"\n  Naechster Zyklus in 60 Minuten...\n")
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\n  Daemon gestoppt.")
            return 0

    # Default: grow
    paper_id = ""
    lens_name = ""
    count = 3
    if "--paper" in remaining:
        idx = remaining.index("--paper")
        if idx + 1 < len(remaining):
            paper_id = remaining[idx + 1]
    if "--lens" in remaining:
        idx = remaining.index("--lens")
        if idx + 1 < len(remaining):
            lens_name = remaining[idx + 1]
    if "--count" in remaining:
        idx = remaining.index("--count")
        if idx + 1 < len(remaining):
            count = int(remaining[idx + 1])

    lp.scan()
    print()
    print(f"  void papers --- {len(lp.papers)} Papers in {root.name}")
    results = lp.grow(count, paper_id, lens_name)
    print()
    if results:
        kept = sum(1 for r in results if r.get("verdict") == "behalten")
        print(f"  {len(results)} Papers grown, {kept} behalten")
    print()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
