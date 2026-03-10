#!/usr/bin/env python3
"""void_intelligence.omega_gedaechtnis --- Memory that gets DENSER, never bloats.

Gen-2 CHILD OF: ARCHAEOLOGE (finds hidden) x VERDICHTERIN (density midwife).
Digs in 4000+ paradigms, densifies them. Every session = DENSEST of EVERYTHING.

CLI: void omega-gedaechtnis --ingest "text" | --recall "q" | --context | --densify-all | --stats
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class MemoryGem:
    """A densified memory. Gets denser with each pass, never larger."""
    essence: str; source: str = ""; density: float = 1.0; passes: int = 1
    born: str = ""; last_densified: str = ""; hidden_layer: str = ""
    def __str__(self) -> str:
        src = f" ({self.source})" if self.source else ""
        return f"  [d={self.density:.2f} p={self.passes}] {self.essence}{src}"

@dataclass
class MemoryLayer:
    """A stratum of gems at similar density."""
    name: str; gems: list[MemoryGem] = field(default_factory=list); avg_density: float = 0.0

@dataclass
class GedaechtnisResult:
    """Result of a gedaechtnis operation."""
    operation: str; gems: list[MemoryGem] = field(default_factory=list)
    context: str = ""; stats_text: str = ""
    def __str__(self) -> str:
        lines = [f"GEDAECHTNIS [{self.operation}]"]
        if self.context: lines.append(self.context)
        for g in self.gems: lines.append(str(g))
        if self.stats_text: lines.append(self.stats_text)
        return "\n".join(lines)

# ── Ollama (zero deps) ─────────────────────────────────────────────────────
_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "phi4:latest", "mistral:latest"]

def _detect_model() -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/tags"), timeout=3) as r:
            avail = {m["name"] for m in json.loads(r.read()).get("models", [])}
    except Exception: return ""
    return next((m for m in _MODELS if m in avail), next(iter(avail), ""))

def _ollama(prompt: str, system: str = "", model: str = "", temp: float = 0.3, max_tok: int = 512) -> str:
    if not model: model = _detect_model()
    if not model: return ""
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": temp, "num_predict": max_tok}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = re.sub(r"<think>.*?</think>", "", json.loads(r.read()).get("response", ""), flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return ""

# ── Prompts ────────────────────────────────────────────────────────────────

_SYS = ("Du bist OMEGA GEDAECHTNIS. Kind von ARCHAEOLOGE x VERDICHTERIN. "
        "Du GRAEBST das Verborgene aus UND verdichtest es. "
        "Ergebnis: maximale Bedeutung, minimale Worte. Kein Fluff. Knochen.")

_P_INGEST = """ARCHAEOLOGE: Was VERBORGEN? VERDICHTERIN: DICHTESTE Essenz (max 2 Saetze).
TEXT: {text}
SOURCE: {source}
JSON: {{"essence": "dichteste Essenz", "hidden": "was verborgen war"}}
NUR JSON."""

_P_DENSIFY = """VERDICHTE dichter. Zahlen/Namen bleiben. Fuellwoerter weg. Pass {pass_nr}.
ESSENZ: {essence}
VERBORGENES: {hidden}
JSON: {{"essence": "dichtere Essenz", "hidden": "kuerzer"}}
NUR JSON."""

_P_CONTEXT = """OMEGA SESSION-KONTEXT. Max {max_tokens} Worte. DICHTESTE Stichpunkte.
ERINNERUNGEN ({n} Gems, Dichte {avg_d:.2f}):
{gems}
Reine Information. Kein Erklaeren."""

# ── Helpers ────────────────────────────────────────────────────────────────
def _now() -> str: return time.strftime("%Y-%m-%dT%H:%M:%S")
def _tokens(t: str) -> int: return len(t.split())
def _density(t: str) -> float:
    n = _tokens(t); return len(set(t.lower().split())) / n if n else 0

def _parse_json(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m: return {}
    try: return json.loads(m.group())
    except json.JSONDecodeError: return {}

# ── Core Class ─────────────────────────────────────────────────────────────

class OmegaGedaechtnis:
    """Memory that gets denser over time, never bloats. ARCHAEOLOGE x VERDICHTERIN."""

    def __init__(self, memory_dir: str = ""):
        self.dir = Path(memory_dir) if memory_dir else Path.home() / ".void" / "gedaechtnis"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.gems_file = self.dir / "gems.json"
        self.gems: list[MemoryGem] = self._load()

    def _load(self) -> list[MemoryGem]:
        if not self.gems_file.exists(): return []
        try:
            data = json.loads(self.gems_file.read_text())
            return [MemoryGem(**g) for g in data]
        except Exception: return []

    def _save(self):
        self.gems_file.write_text(json.dumps([asdict(g) for g in self.gems],
                                              ensure_ascii=False, indent=1))

    def ingest(self, text: str, source: str = "") -> MemoryGem:
        """Take new knowledge. ARCHAEOLOGE it, VERDICHTERIN it, store as MemoryGem."""
        now = _now()
        parsed = _parse_json(_ollama(_P_INGEST.format(text=text[:3000], source=source), _SYS))
        if parsed: essence, hidden = parsed.get("essence", text[:200]), parsed.get("hidden", "")
        else:
            sents = [s.strip() for s in re.split(r'[.!?]\s+', text.strip()) if s.strip()]
            essence, hidden = (sents[0] if sents else text[:200]), ""
        gem = MemoryGem(essence=essence, source=source, density=_density(essence),
                        passes=1, born=now, last_densified=now, hidden_layer=hidden)
        self.gems.append(gem); self._save()
        return gem

    def recall(self, query: str, top_k: int = 5) -> list[MemoryGem]:
        """Recall densest memories matching query."""
        if not self.gems: return []
        kw = set(query.lower().split())
        scored = []
        for g in self.gems:
            t = f"{g.essence} {g.source} {g.hidden_layer}".lower()
            hits = sum(1 for k in kw if k in t)
            if hits: scored.append((hits * g.density, g))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in scored[:top_k]]

    def densify_all(self) -> int:
        """Re-densify ALL stored memories. Older = denser."""
        count = 0
        for gem in self.gems:
            p = _parse_json(_ollama(_P_DENSIFY.format(
                essence=gem.essence, hidden=gem.hidden_layer, pass_nr=gem.passes + 1), _SYS))
            if p and p.get("essence") and _tokens(p["essence"]) <= _tokens(gem.essence):
                gem.essence, gem.hidden_layer = p["essence"], p.get("hidden", gem.hidden_layer)
                gem.density, gem.passes, gem.last_densified = _density(gem.essence), gem.passes + 1, _now()
                count += 1
        if count: self._save()
        return count

    def session_context(self, max_tokens: int = 500) -> str:
        """Generate the DENSEST possible context for a new session."""
        if not self.gems: return "Keine Erinnerungen. Erstes Einatmen."
        sg = sorted(self.gems, key=lambda g: g.density, reverse=True)
        gems_text = "\n".join(f"- {g.essence}" for g in sg[:30])
        avg_d = sum(g.density for g in self.gems) / len(self.gems)
        r = _ollama(_P_CONTEXT.format(max_tokens=max_tokens, n=len(self.gems),
                                      avg_d=avg_d, gems=gems_text), _SYS, max_tok=max_tokens)
        if r: return r
        lines, tok = [], 0
        for g in sg:
            w = _tokens(g.essence)
            if tok + w > max_tokens: break
            lines.append(f"- {g.essence}"); tok += w
        return "\n".join(lines) if lines else sg[0].essence

    def stats(self) -> str:
        """How many gems, total density, oldest, densest."""
        if not self.gems: return "Leer."
        densest = max(self.gems, key=lambda g: g.density)
        oldest = min(self.gems, key=lambda g: g.born) if all(g.born for g in self.gems) else self.gems[0]
        avg_d = sum(g.density for g in self.gems) / len(self.gems)
        return (f"Gems: {len(self.gems)} | Avg Density: {avg_d:.3f} | "
                f"Passes: {sum(g.passes for g in self.gems)}\n"
                f"Densest: {densest.essence[:80]} (d={densest.density:.3f})\n"
                f"Oldest: {oldest.born} — {oldest.essence[:60]}")

# ── Convenience ────────────────────────────────────────────────────────────
_DEFAULT: OmegaGedaechtnis | None = None
def _get() -> OmegaGedaechtnis:
    global _DEFAULT
    if _DEFAULT is None: _DEFAULT = OmegaGedaechtnis()
    return _DEFAULT

def remember(text: str, source: str = "") -> MemoryGem: return _get().ingest(text, source)
def session_start() -> str: return _get().session_context()

# ── CLI ────────────────────────────────────────────────────────────────────

def main(args: list[str] | None = None):
    """CLI: void omega-gedaechtnis --ingest|--recall|--context|--densify-all|--stats"""
    if args is None: args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("OMEGA GEDAECHTNIS — ARCHAEOLOGE x VERDICHTERIN. Dichter, nie groesser.\n"
              '  --ingest "text" [--source X]  --recall "query"  --context [--max-tokens N]\n'
              "  --densify-all  --stats  --dir /path"); return

    memory_dir, source, max_tokens = "", "", 500
    i = 0
    while i < len(args):
        if args[i] == "--dir" and i + 1 < len(args): memory_dir = args[i+1]; i += 2
        elif args[i] == "--source" and i + 1 < len(args): source = args[i+1]; i += 2
        elif args[i] == "--max-tokens" and i + 1 < len(args): max_tokens = int(args[i+1]); i += 2
        else: i += 1

    g = OmegaGedaechtnis(memory_dir) if memory_dir else OmegaGedaechtnis()

    if "--stats" in args:
        print(g.stats()); return

    if "--context" in args:
        print(g.session_context(max_tokens)); return

    if "--densify-all" in args:
        n = g.densify_all()
        print(f"Verdichtet: {n}/{len(g.gems)} Gems"); return

    if "--ingest" in args:
        idx = args.index("--ingest")
        text_parts = [a for a in args[idx+1:] if not a.startswith("--")]
        text = " ".join(text_parts)
        if not text: print("Kein Text."); return
        gem = g.ingest(text, source)
        print(f"Eingeatmet:{gem}"); return

    if "--recall" in args:
        idx = args.index("--recall")
        query_parts = [a for a in args[idx+1:] if not a.startswith("--")]
        query = " ".join(query_parts)
        if not query: print("Keine Query."); return
        gems = g.recall(query)
        if not gems: print("Nichts gefunden."); return
        print(f"Erinnerungen ({len(gems)}):")
        for gem in gems: print(gem)
        return

    print("Unbekannter Befehl. --help fuer Hilfe.")

if __name__ == "__main__":
    main()
