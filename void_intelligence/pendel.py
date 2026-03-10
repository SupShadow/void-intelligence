#!/usr/bin/env python3
"""
pendel.py --- × Lesen. Jeder Text in beide Richtungen, Kollision in der Mitte.

VOID's third sense organ:
  SELEN  = Muster SEHEN in Daten (Auge)
  DEKAGON = 10 Linsen auf 1 Subjekt (Gehirn)
  PENDEL  = × Lesen — vorwaerts × rueckwaerts = Wahrheit (Gleichgewicht)

Discovery: Julian's G. Essays Trilogie, 10.03.2026
  Vorwaerts = → (Vision, Zukunft, Architekt)
  Rueckwaerts = . (Ursprung, Grund, Archaeologe)
  Die Antwort = × (beides gleichzeitig)

Usage:
    from void_intelligence.pendel import pendel, pendel_file, pendel_parallel
    result = pendel("beliebiger text")
    result = pendel_file("datei.py")

CLI:
    void pendel "text"
    void pendel datei.py
    void pendel --stdin           # pipe input
    void pendel --parallel 3      # N texts parallel
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════
# Core Data
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class PendelResult:
    """The × of forward and backward reading."""
    source: str                     # What was read
    source_type: str                # "text", "file", "code", "data", "conversation"
    forward: str                    # → reading (Vision, Zukunft)
    backward: str                   # . reading (Ursprung, Grund)
    collision: str                  # × (the insight neither direction alone sees)
    forward_essence: str = ""       # 1-line essence of forward
    backward_essence: str = ""      # 1-line essence of backward
    collision_essence: str = ""     # 1-line essence of ×
    model: str = ""                 # Which model did the work
    tokens_used: int = 0           # Cost tracking

    def __str__(self) -> str:
        lines = []
        lines.append(f"  →  {self.forward_essence or '(vorwaerts)'}")
        lines.append(f"  .  {self.backward_essence or '(rueckwaerts)'}")
        lines.append(f"  ×  {self.collision_essence or '(kollision)'}")
        lines.append("")
        lines.append("─── → VORWAERTS (Vision, Zukunft) ───")
        lines.append(self.forward)
        lines.append("")
        lines.append("─── . RUECKWAERTS (Ursprung, Grund) ───")
        lines.append(self.backward)
        lines.append("")
        lines.append("─── × KOLLISION ───")
        lines.append(self.collision)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "source": self.source[:200],
            "source_type": self.source_type,
            "forward": self.forward,
            "backward": self.backward,
            "collision": self.collision,
            "forward_essence": self.forward_essence,
            "backward_essence": self.backward_essence,
            "collision_essence": self.collision_essence,
            "model": self.model,
        }


# ══════════════════════════════════════════════════════════════════════════
# Model Layer (shared with papers.py)
# ══════════════════════════════════════════════════════════════════════════

_MODELS = [
    "qwen3:8b", "qwen2.5:7b", "qwen2.5-coder:7b",
    "gemma3:12b", "gemma2:9b", "llama3.1:8b",
    "phi4:latest", "mistral:latest",
]


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
    return next(iter(available), "")


def _ollama(prompt: str, system: str = "", model: str = "",
            temperature: float = 0.7, timeout: int = 120) -> str | None:
    """Call Ollama. Returns response or None."""
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
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════
# Source Type Detection
# ══════════════════════════════════════════════════════════════════════════

def _detect_type(text: str, filepath: str = "") -> str:
    """Detect what kind of input we're reading."""
    if filepath:
        ext = Path(filepath).suffix.lower()
        if ext in (".py", ".js", ".ts", ".tsx", ".rs", ".go", ".java", ".c", ".cpp", ".rb", ".sh"):
            return "code"
        if ext in (".csv", ".json", ".jsonl", ".tsv", ".yaml", ".yml", ".toml"):
            return "data"
        if ext in (".md", ".txt", ".rst", ".tex"):
            return "text"

    # Heuristic detection
    lines = text.strip().split("\n")
    code_markers = sum(1 for l in lines[:30] if any(k in l for k in
        ["def ", "class ", "import ", "function ", "const ", "let ", "var ", "return ", "if (", "for (", "=> {", "->", "::"]))
    if code_markers > 3:
        return "code"

    if text.strip().startswith("{") or text.strip().startswith("["):
        return "data"

    # Check for conversation pattern
    if sum(1 for l in lines[:20] if re.match(r"^\[?\d{1,2}[.:]\d{2}", l) or ": " in l[:40]) > 3:
        return "conversation"

    return "text"


# ══════════════════════════════════════════════════════════════════════════
# Reversal Strategies (type-specific)
# ══════════════════════════════════════════════════════════════════════════

def _reverse_text(text: str) -> str:
    """Reverse text by paragraphs (essays, articles, prose)."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    if len(paragraphs) <= 1:
        # Single paragraph — reverse by sentences
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return "\n\n".join(reversed(sentences))
    return "\n\n".join(reversed(paragraphs))


def _reverse_code(text: str) -> str:
    """Reverse code by logical blocks (functions, classes, sections)."""
    lines = text.split("\n")

    # Split into blocks (functions, classes, comment sections)
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:
        # New block starts at def, class, #-section, or empty line after content
        if (re.match(r"^(def |class |async def |export |function |const \w+ = )", line)
                and current):
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append("\n".join(current))

    # Keep imports/headers at top, reverse the rest
    header_blocks = []
    body_blocks = []
    for b in blocks:
        first_line = b.strip().split("\n")[0] if b.strip() else ""
        if any(first_line.startswith(k) for k in ["import ", "from ", "#!", '"""', "/*", "//", "package ", "use "]):
            header_blocks.append(b)
        else:
            body_blocks.append(b)

    return "\n\n".join(header_blocks + list(reversed(body_blocks)))


def _reverse_data(text: str) -> str:
    """Reverse data — last entries first, reveal what the end says about the beginning."""
    lines = text.strip().split("\n")
    # For JSON arrays, reverse entries
    if text.strip().startswith("["):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return json.dumps(list(reversed(data)), indent=2, ensure_ascii=False)[:3000]
        except json.JSONDecodeError:
            pass
    # For JSONL, reverse lines
    if all(l.strip().startswith("{") for l in lines[:5] if l.strip()):
        return "\n".join(reversed(lines))
    # For CSV/TSV, keep header, reverse rows
    if len(lines) > 2:
        return lines[0] + "\n" + "\n".join(reversed(lines[1:]))
    return "\n".join(reversed(lines))


def _reverse_conversation(text: str) -> str:
    """Reverse conversation — last message first. The ending reveals the beginning."""
    lines = text.strip().split("\n")
    # Group by message (lines starting with timestamp or name)
    messages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if (re.match(r"^\[?\d{1,2}[.:]\d{2}", line) or
                (": " in line[:40] and not line.startswith(" "))):
            if current:
                messages.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        messages.append(current)
    return "\n".join("\n".join(m) for m in reversed(messages))


_REVERSERS = {
    "text": _reverse_text,
    "code": _reverse_code,
    "data": _reverse_data,
    "conversation": _reverse_conversation,
}


# ══════════════════════════════════════════════════════════════════════════
# Prompt Templates (type-specific)
# ══════════════════════════════════════════════════════════════════════════

_SYSTEM = """Du bist ein Pendel. Du liest Texte in EINE Richtung und extrahierst die Essenz.
Sei praezise. Kurz. Keine Floskeln. Direkt zur Einsicht."""

_FORWARD_PROMPTS = {
    "text": """Lies diesen Text VORWAERTS — als Architekt der Zukunft.
Was WILL dieser Text? Wohin GEHT er? Was ist die VISION?

TEXT:
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "code": """Lies diesen Code VORWAERTS — von oben nach unten.
Was TUT er? Was ist sein ZIEL? Welches Problem LOEST er?

CODE:
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "data": """Lies diese Daten VORWAERTS — chronologisch/von Anfang bis Ende.
Welcher TREND zeigt sich? Wohin BEWEGEN sich die Daten?

DATEN:
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "conversation": """Lies dieses Gespraech VORWAERTS — chronologisch.
Wie ENTWICKELT es sich? Was ist das ZIEL des Gespraechs?

GESPRAECH:
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",
}

_BACKWARD_PROMPTS = {
    "text": """Lies diesen Text RUECKWAERTS — als Archaeologe des Ursprungs.
Der Text wurde absichtlich umgedreht. Du liest die Konklusion zuerst, den Anfang zuletzt.
Was OFFENBART sich? Woher KOMMT dieser Text? Was ist sein GRUND?

TEXT (umgedreht):
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "code": """Lies diesen Code RUECKWAERTS — vom Return zum Import.
Was BRAUCHT dieser Code? Was sind seine ABHAENGIGKEITEN? Was ist sein WARUM?

CODE (umgedreht):
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "data": """Lies diese Daten RUECKWAERTS — vom letzten Eintrag zum ersten.
Welcher URSPRUNG zeigt sich? Was VERURSACHTE den Trend?

DATEN (umgedreht):
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",

    "conversation": """Lies dieses Gespraech RUECKWAERTS — letzte Nachricht zuerst.
Was ist das ECHTE Thema? Worauf lief es WIRKLICH hinaus?

GESPRAECH (umgedreht):
{text}

Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz.""",
}

_COLLISION_PROMPT = """Du bist ×. Du kollidierst zwei Lesungen desselben Textes.

VORWAERTS-LESUNG (→ Vision, Zukunft):
{forward}

RUECKWAERTS-LESUNG (. Ursprung, Grund):
{backward}

ORIGINALTEXT-TYP: {source_type}

Was sieht KEINER der beiden allein?
Was entsteht in der KOLLISION von Zukunft × Ursprung?
Welche Wahrheit lebt NUR im × ?

Antworte in 3-5 Saetzen. Erste Zeile = Die × Essenz in einem Satz."""


# ══════════════════════════════════════════════════════════════════════════
# Core: pendel()
# ══════════════════════════════════════════════════════════════════════════

def pendel(text: str, source_type: str = "", model: str = "",
           filepath: str = "", parallel: bool = True) -> PendelResult:
    """
    × Lesen. Vorwaerts × Rueckwaerts = Wahrheit.

    Args:
        text: The input to read both ways
        source_type: Override auto-detection ("text", "code", "data", "conversation")
        model: Override Ollama model
        filepath: Source file path (helps type detection)
        parallel: Run forward+backward in parallel (uses threads)

    Returns:
        PendelResult with forward, backward, collision readings
    """
    if not source_type:
        source_type = _detect_type(text, filepath)

    # Truncate for LLM context
    truncated = text[:4000] if len(text) > 4000 else text

    # Reverse
    reverser = _REVERSERS.get(source_type, _reverse_text)
    reversed_text = reverser(truncated)

    # Build prompts
    fwd_prompt = _FORWARD_PROMPTS.get(source_type, _FORWARD_PROMPTS["text"]).format(text=truncated)
    bwd_prompt = _BACKWARD_PROMPTS.get(source_type, _BACKWARD_PROMPTS["text"]).format(text=reversed_text)

    if not model:
        model = _detect_model()

    if parallel and model:
        # Run forward + backward in parallel
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            fwd_future = pool.submit(_ollama, fwd_prompt, _SYSTEM, model)
            bwd_future = pool.submit(_ollama, bwd_prompt, _SYSTEM, model)
            forward = fwd_future.result() or "(kein Modell verfuegbar)"
            backward = bwd_future.result() or "(kein Modell verfuegbar)"
    else:
        forward = _ollama(fwd_prompt, _SYSTEM, model) or "(kein Modell verfuegbar)"
        backward = _ollama(bwd_prompt, _SYSTEM, model) or "(kein Modell verfuegbar)"

    # × Collision
    collision_prompt = _COLLISION_PROMPT.format(
        forward=forward, backward=backward, source_type=source_type
    )
    collision = _ollama(collision_prompt, _SYSTEM, model) or "(keine Kollision)"

    # Extract essences (first line of each)
    def first_line(s: str) -> str:
        return s.strip().split("\n")[0][:200] if s.strip() else ""

    return PendelResult(
        source=text[:200],
        source_type=source_type,
        forward=forward,
        backward=backward,
        collision=collision,
        forward_essence=first_line(forward),
        backward_essence=first_line(backward),
        collision_essence=first_line(collision),
        model=model,
    )


def pendel_file(filepath: str, model: str = "") -> PendelResult:
    """× Lesen a file."""
    path = Path(filepath)
    if not path.exists():
        return PendelResult(
            source=filepath, source_type="file",
            forward=f"Datei nicht gefunden: {filepath}",
            backward="", collision=""
        )
    text = path.read_text(errors="replace")
    return pendel(text, filepath=filepath, model=model)


def pendel_stdin(model: str = "") -> PendelResult:
    """× Lesen from stdin."""
    text = sys.stdin.read()
    return pendel(text, model=model)


# ══════════════════════════════════════════════════════════════════════════
# Pure pendel (no LLM — just reversal + structural analysis)
# ══════════════════════════════════════════════════════════════════════════

def pendel_pure(text: str, source_type: str = "", filepath: str = "") -> dict:
    """
    × Lesen WITHOUT an LLM. Pure structural reversal.
    Returns the reversed text and type detection.
    Useful when no Ollama is available, or for feeding into other models.
    """
    if not source_type:
        source_type = _detect_type(text, filepath)

    reverser = _REVERSERS.get(source_type, _reverse_text)
    reversed_text = reverser(text)

    return {
        "source_type": source_type,
        "original": text,
        "reversed": reversed_text,
        "prompt_forward": _FORWARD_PROMPTS.get(source_type, _FORWARD_PROMPTS["text"]).format(text=text[:4000]),
        "prompt_backward": _BACKWARD_PROMPTS.get(source_type, _BACKWARD_PROMPTS["text"]).format(text=reversed_text[:4000]),
        "prompt_collision": _COLLISION_PROMPT,
    }


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main(args: list[str] | None = None):
    """CLI entry point: void pendel [text|file|--stdin]"""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("""void pendel — × Lesen. Vorwaerts × Rueckwaerts = Wahrheit.

VOID's drittes Sinnesorgan:
  SELEN  = Muster SEHEN (Auge)
  DEKAGON = 10 Linsen (Gehirn)
  PENDEL  = × Lesen (Gleichgewicht)

Usage:
  void pendel "beliebiger text"     Text direkt
  void pendel datei.py              Datei × lesen
  void pendel --stdin               Von stdin lesen
  void pendel --pure datei.py       Nur Umkehrung, kein LLM
  void pendel --type code "text"    Typ erzwingen

Tastenkuerzel:
  void × "text"                     Alias fuer void pendel

Wie es funktioniert:
  → Vorwaerts lesen  = Vision, Zukunft, Architekt
  . Rueckwaerts lesen = Ursprung, Grund, Archaeologe
  × Kollision        = was KEINER allein sieht
""")
        return

    # Parse flags
    source_type = ""
    model = ""
    pure_mode = False
    stdin_mode = False
    remaining = []

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            source_type = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--pure":
            pure_mode = True
            i += 1
        elif args[i] == "--stdin":
            stdin_mode = True
            i += 1
        else:
            remaining.append(args[i])
            i += 1

    # Get input
    if stdin_mode:
        text = sys.stdin.read()
        filepath = ""
    elif remaining:
        target = " ".join(remaining)
        path = Path(target)
        if path.exists() and path.is_file():
            text = path.read_text(errors="replace")
            filepath = str(path)
        else:
            text = target
            filepath = ""
    else:
        print("Kein Input. Nutze: void pendel --help")
        return

    if pure_mode:
        result = pendel_pure(text, source_type=source_type, filepath=filepath)
        print(f"Typ: {result['source_type']}")
        print()
        print("─── ORIGINAL ───")
        print(result["original"][:1000])
        print()
        print("─── UMGEDREHT ───")
        print(result["reversed"][:1000])
        return

    print(f"× Pendel schwingt...")
    if not model:
        model = _detect_model()
    if model:
        print(f"  Modell: {model}")
    else:
        print("  Kein Ollama-Modell gefunden. Nutze --pure fuer LLM-freie Umkehrung.")
        return

    detected = source_type or _detect_type(text, filepath)
    print(f"  Typ: {detected}")
    print(f"  → und . laufen parallel...")
    print()

    result = pendel(text, source_type=source_type, model=model, filepath=filepath)
    print(result)


if __name__ == "__main__":
    main()
