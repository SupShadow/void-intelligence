#!/usr/bin/env python3
"""
void_intelligence.archaeologe --- Autonomous Reverse Research.

FORSCHER x PENDEL = ARCHAEOLOGE. Digs in EXISTING texts/code/data
and finds what was ALWAYS THERE but never seen.

Usage:
    from void_intelligence.archaeologe import dig, dig_file, excavate
    result = dig("some text", "what pattern is buried here?")

CLI:
    void archaeologe "text"
    void archaeologe file.py
    void archaeologe --depth 5 file.py
"""
from __future__ import annotations
import json, re, sys, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Fossil:
    """An insight BURIED in the original. Always there, never seen."""
    essence: str; layer: int; age: str; evidence: str = ""
    def __str__(self) -> str:
        return f"  {'.' * self.layer} [{self.layer}] {self.essence} (hidden {self.age})"

@dataclass
class DigSite:
    """A location being excavated."""
    source: str; source_type: str; original_length: int; reversed_text: str

@dataclass
class ArchaeologeResult:
    """What the archaeologist found."""
    site: DigSite
    fossils: list[Fossil] = field(default_factory=list)
    deepest_layer: int = 0; summary: str = ""; question_asked: str = ""
    model: str = ""; depth: int = 1
    def __str__(self) -> str:
        lines = [f"AUSGRABUNG ({self.site.source_type}, Tiefe {self.depth})"]
        if self.question_asked: lines.append(f"  Frage: {self.question_asked}")
        lines.append(f"  Fossilien: {len(self.fossils)}, tiefste Schicht: {self.deepest_layer}")
        lines.append("")
        for f in sorted(self.fossils, key=lambda x: x.layer): lines.append(str(f))
        if self.summary: lines += ["", f"  ZUSAMMENFASSUNG: {self.summary}"]
        return "\n".join(lines)
    def to_dict(self) -> dict:
        return {"source": self.site.source[:200], "source_type": self.site.source_type,
                "fossils": [{"essence": f.essence, "layer": f.layer, "age": f.age,
                             "evidence": f.evidence} for f in self.fossils],
                "deepest_layer": self.deepest_layer, "summary": self.summary,
                "question": self.question_asked, "model": self.model, "depth": self.depth}

# ── Model Layer ──────────────────────────────────────────────────────────
_MODELS = ["qwen3:8b", "qwen2.5:7b", "qwen2.5-coder:7b", "gemma3:12b",
           "gemma2:9b", "llama3.1:8b", "phi4:latest", "mistral:latest"]

def _detect_model() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            available = {m["name"] for m in json.loads(resp.read()).get("models", [])}
    except Exception: return ""
    for m in _MODELS:
        if m in available: return m
    return next(iter(available), "") if available else ""

def _ollama(prompt: str, system: str = "", model: str = "",
            temperature: float = 0.7, timeout: int = 120) -> str | None:
    if not model:
        model = _detect_model()
        if not model: return None
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": temperature, "num_predict": 1500}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = json.loads(resp.read()).get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return None

# ── Reversal (delegates to pendel) ───────────────────────────────────────
def _reverse(text: str, source_type: str) -> str:
    try:
        from void_intelligence.pendel import _reverse_text, _reverse_code, _reverse_data, _reverse_conversation
        return {"text": _reverse_text, "code": _reverse_code, "data": _reverse_data,
                "conversation": _reverse_conversation}.get(source_type, _reverse_text)(text)
    except ImportError:
        paragraphs = re.split(r"\n\s*\n", text.strip())
        return "\n\n".join(reversed(paragraphs))

def _detect_type(text: str, filepath: str = "") -> str:
    try:
        from void_intelligence.pendel import _detect_type as pd; return pd(text, filepath)
    except ImportError: return "text"

# ── Prompts ──────────────────────────────────────────────────────────────
_SYSTEM = ("Du bist ein Archaeologe des Textes. Du graebst in umgedrehten Texten nach dem, "
           "was IMMER da war aber NIE gesehen wurde. Du erfindest NICHTS. Du findest nur, "
           "was schon da ist. Jede Einsicht ist ein Fossil.")

_DIG_PROMPT = """Dieser Text wurde UMGEDREHT. Grabe darin. Was war IMMER hier, nie gesehen?
{question_line}
UMGEDREHTER TEXT:
{reversed_text}

ORIGINAL (Vergleich):
{original_snippet}

Antworte als JSON-Array:
[{{"essence": "was verborgen war", "layer": 1-5, "age": "wie lange verborgen", "evidence": "Beweis"}}]
Finde 2-5 Fossilien. Schicht 1=Oberflaeche, 5=tief. NUR JSON."""

_SUMMARY_PROMPT = """Fossilien ausgegraben:
{fossils}
Fasse in EINEM Satz zusammen: Was war die groesste verborgene Wahrheit? Nur ein Satz."""

# ── Core ─────────────────────────────────────────────────────────────────
def _parse_fossils(raw: str) -> list[Fossil]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match: return []
    try: items = json.loads(match.group())
    except json.JSONDecodeError: return []
    return [Fossil(essence=str(it["essence"]), layer=int(it.get("layer", 1)),
                   age=str(it.get("age", "unbekannt")), evidence=str(it.get("evidence", "")))
            for it in items if isinstance(it, dict) and "essence" in it]

def dig(text: str, question: str = "", model: str = "") -> ArchaeologeResult:
    """Dig in a text. Find what was ALWAYS there but never seen."""
    source_type = _detect_type(text)
    truncated = text[:4000]
    reversed_text = _reverse(truncated, source_type)
    site = DigSite(source=text[:200], source_type=source_type,
                   original_length=len(text), reversed_text=reversed_text)
    if not model: model = _detect_model()
    if not model:
        return ArchaeologeResult(site=site, summary="Kein Ollama-Modell verfuegbar")
    prompt = _DIG_PROMPT.format(reversed_text=reversed_text[:3000],
                                original_snippet=truncated[:1000],
                                question_line=f"LEITFRAGE: {question}" if question else "")
    fossils = _parse_fossils(_ollama(prompt, _SYSTEM, model) or "[]")
    summary = ""
    if fossils:
        s = _ollama(_SUMMARY_PROMPT.format(fossils="\n".join(str(f) for f in fossils)),
                    "", model, temperature=0.3)
        summary = s.strip().split("\n")[0] if s else ""
    return ArchaeologeResult(site=site, fossils=fossils,
                             deepest_layer=max((f.layer for f in fossils), default=0),
                             summary=summary, question_asked=question, model=model, depth=1)

def dig_file(filepath: str, question: str = "", model: str = "") -> ArchaeologeResult:
    """Dig in any file."""
    path = Path(filepath)
    if not path.exists():
        site = DigSite(source=filepath, source_type="file", original_length=0, reversed_text="")
        return ArchaeologeResult(site=site, summary=f"Datei nicht gefunden: {filepath}")
    result = dig(path.read_text(errors="replace"), question=question, model=model)
    result.site.source = filepath
    return result

def dig_codebase(directory: str, pattern: str = "*.py",
                 question: str = "", model: str = "") -> ArchaeologeResult:
    """Dig across multiple files. Find cross-file fossils."""
    root = Path(directory)
    files = sorted(root.rglob(pattern))[:20]
    if not files:
        site = DigSite(source=directory, source_type="code", original_length=0, reversed_text="")
        return ArchaeologeResult(site=site, summary=f"Keine Dateien gefunden: {pattern}")
    combined = []
    for f in files:
        try:
            lines = f.read_text(errors="replace").split("\n")[:200]
            combined.append(f"# === {f.relative_to(root)} ===\n" + "\n".join(lines))
        except Exception: continue
    result = dig("\n\n".join(combined),
                 question=question or "Was verbindet diese Dateien, das nie explizit gesagt wird?",
                 model=model)
    result.site.source = f"{directory}/{pattern} ({len(files)} Dateien)"
    return result

def excavate(text: str, depth: int = 3, question: str = "", model: str = "") -> ArchaeologeResult:
    """Dig multiple layers deep. Reverse, dig, feed fossils back, dig again."""
    all_fossils: list[Fossil] = []
    current_text, q = text, question
    if not model: model = _detect_model()
    for layer in range(1, depth + 1):
        result = dig(current_text, question=q, model=model or "")
        for f in result.fossils:
            f.layer = min(f.layer + layer - 1, depth + 4)
            all_fossils.append(f)
        if not result.fossils: break
        current_text = "\n".join(f"FOSSIL ({f.layer}): {f.essence} -- {f.evidence}" for f in result.fossils)
        q = "Was verbergen DIESE Fossilien? Was liegt UNTER ihnen?"
    deepest = max((f.layer for f in all_fossils), default=0)
    summary = ""
    if all_fossils and model:
        s = _ollama(_SUMMARY_PROMPT.format(fossils="\n".join(str(f) for f in all_fossils)),
                    "", model, temperature=0.3)
        summary = s.strip().split("\n")[0] if s else ""
    source_type = _detect_type(text)
    site = DigSite(source=text[:200], source_type=source_type,
                   original_length=len(text), reversed_text=_reverse(text[:4000], source_type))
    return ArchaeologeResult(site=site, fossils=all_fossils, deepest_layer=deepest,
                             summary=summary, question_asked=q, model=model or "", depth=depth)

# ── CLI ──────────────────────────────────────────────────────────────────
def main(args: list[str] | None = None):
    """CLI: void archaeologe [text|file] [--depth N] [--question Q]"""
    if args is None: args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("void archaeologe --- Autonome Rueckwaerts-Forschung.\n"
              "FORSCHER x PENDEL = ARCHAEOLOGE\n\n"
              "Usage:\n"
              '  void archaeologe "text"                Ausgraben\n'
              "  void archaeologe datei.py              Datei ausgraben\n"
              "  void archaeologe --depth 5 datei.py    5 Schichten tief\n"
              '  void archaeologe --question "Q" text   Mit Leitfrage\n'
              "  void archaeologe --codebase src/       Ueber Codebase"); return
    depth, question, model, codebase_mode, codebase_pattern, remaining = 1, "", "", False, "*.py", []
    i = 0
    while i < len(args):
        if args[i] == "--depth" and i + 1 < len(args): depth = int(args[i+1]); i += 2
        elif args[i] == "--question" and i + 1 < len(args): question = args[i+1]; i += 2
        elif args[i] == "--model" and i + 1 < len(args): model = args[i+1]; i += 2
        elif args[i] == "--codebase": codebase_mode = True; i += 1
        elif args[i] == "--pattern" and i + 1 < len(args): codebase_pattern = args[i+1]; i += 2
        else: remaining.append(args[i]); i += 1
    if not remaining: print("Kein Input. Nutze: void archaeologe --help"); return
    target = " ".join(remaining)
    if not model: model = _detect_model()
    if model: print(f"Modell: {model}")
    else: print("Kein Ollama-Modell gefunden."); return
    if codebase_mode:
        print(f"Grabe in Codebase: {target}/{codebase_pattern}")
        result = dig_codebase(target, codebase_pattern, question=question, model=model)
    elif Path(target).exists() and Path(target).is_file():
        print(f"Grabe{'  ' + str(depth) + ' Schichten tief' if depth > 1 else ''} in: {target}")
        if depth > 1:
            result = excavate(Path(target).read_text(errors="replace"), depth=depth, question=question, model=model)
            result.site.source = target
        else: result = dig_file(target, question=question, model=model)
    else:
        print(f"Grabe{'  ' + str(depth) + ' Schichten tief' if depth > 1 else ''}...")
        result = excavate(target, depth=depth, question=question, model=model) if depth > 1 \
            else dig(target, question=question, model=model)
    print(); print(result)

if __name__ == "__main__":
    main()
