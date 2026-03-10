"""void_intelligence.wahrheitsdichte --- Densest possible truth.

Gen-2 CHILD of VERDICHTERIN (density midwife) x IMMUNSYSTEM (hallucination->truth).
Every output becomes simultaneously DENSER and TRUER.
A 7B with Wahrheitsdichte beats a 70B without.

Three phases: IMMUNSYSTEM detects. VERDICHTERIN densifies. MEASURE: truth x density.
Pure Python. Zero deps. urllib for Ollama.
CLI: void wahrheitsdichte "text" | --score "text" | --filter "text"
"""
from __future__ import annotations
import json, re, sys, urllib.request
from dataclasses import dataclass, field

# -- Pathogen Lexicon (from immunsystem.py, compressed) -----------------------
_HEDGES = ["maybe", "perhaps", "possibly", "might", "could be", "it seems",
    "I think", "I believe", "I guess", "sort of", "kind of", "somewhat",
    "arguably", "to some extent", "vielleicht", "moeglicherweise", "eventuell",
    "ich glaube", "ich denke", "irgendwie", "sozusagen",
    "koennte", "koennten", "wuerde", "sollte", "waere"]
_OVERCONF = ["obviously", "clearly", "everyone knows", "without a doubt", "certainly",
    "undeniably", "of course", "needless to say",
    "offensichtlich", "selbstverstaendlich", "jeder weiss", "zweifellos",
    "definitiv", "absolut", "hundertprozentig", "ganz klar", "ohne Zweifel"]
_VAGUE = ["stuff", "things", "somehow", "whatever", "something like", "various",
    "numerous", "significant", "a lot of", "quite a few", "in general",
    "basically", "essentially", "pretty much",
    "Sachen", "Dinge", "irgendwas", "halt", "eben", "verschiedene"]
_FILLER = ["actually", "literally", "honestly", "frankly", "you know", "I mean",
    "eigentlich", "also", "natuerlich", "grundsaetzlich", "quasi",
    "im Grunde genommen", "in fact"]

# -- Data Structures ----------------------------------------------------------
@dataclass
class TruthDensity:
    """Measurement: truth_score x density_score = wahrheitsdichte."""
    truth_score: float = 0.0; density_score: float = 0.0; wahrheitsdichte: float = 0.0
    pathogens_found: int = 0; tokens_before: int = 0; tokens_after: int = 0
    removed: list[str] = field(default_factory=list)
    compressed: list[str] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"truth": round(self.truth_score, 3), "density": round(self.density_score, 3),
                "wahrheitsdichte": round(self.wahrheitsdichte, 4), "pathogens": self.pathogens_found,
                "tokens": f"{self.tokens_before}->{self.tokens_after}",
                "removed": self.removed[:10], "compressed": self.compressed[:10]}

@dataclass
class WahrheitResult:
    """Complete wahrheitsdichte transformation."""
    original: str; text: str; density: TruthDensity = field(default_factory=TruthDensity); model_used: str = ""
    def to_dict(self) -> dict:
        return {"text": self.text, "model": self.model_used, **self.density.to_dict()}

# -- Phase 1: IMMUNSYSTEM (detect pathogens) ---------------------------------
def _scan(text: str, markers: list[str]) -> list[tuple[str, int]]:
    found = []
    for m in markers:
        for match in re.finditer(r'\b' + re.escape(m) + r'\b', text, re.IGNORECASE):
            found.append((match.group(0), match.start()))
    return sorted(found, key=lambda x: x[1])

def _detect(text: str) -> tuple[list[str], float]:
    all_p = [(s, 0.5) for s, _ in _scan(text, _HEDGES)] + \
            [(s, 0.6) for s, _ in _scan(text, _OVERCONF)] + \
            [(s, 0.4) for s, _ in _scan(text, _VAGUE)] + \
            [(s, 0.2) for s, _ in _scan(text, _FILLER)]
    if not all_p: return [], 0.0
    return [s for s, _ in all_p], min(sum(w for _, w in all_p) / max(len(text.split()) / 10, 1), 1.0)

# -- Phase 2: VERDICHTERIN (densify while healing) ---------------------------
def _tok(text: str) -> int: return len(text.split())

def _insights(text: str) -> int:
    sents = [s.strip() for s in re.split(r'[.!?]\s+', text.strip()) if len(s.strip()) > 5]
    dead = ("also", "eigentlich", "natuerlich", "basically", "actually", "sure")
    return max(1, sum(1 for s in sents if not any(s.lower().startswith(f) for f in dead)))

def _densify_heuristic(text: str, pathogens: list[str]) -> tuple[str, list[str], list[str]]:
    result, removed = text, []
    for p in pathogens:
        before = result
        result = re.sub(r'\b' + re.escape(p) + r'\b\s*', '', result, count=1, flags=re.IGNORECASE)
        if result != before: removed.append(p)
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r',\s*([.!?])', r'\1', result)
    result = re.sub(r'\s+([.,;:!?])', r'\1', result)
    compressed, sents = [], re.split(r'(?<=[.!?])\s+', result.strip())
    if len(sents) > 2:
        seen, kept = {}, []
        for s in sents:
            start = ' '.join(s.split()[:3]).lower()
            if start in seen: compressed.append(f"dedup:{s[:30]}...")
            else: seen[start] = True; kept.append(s)
        result = ' '.join(kept)
    return result.strip(), removed, compressed

_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "phi4:latest"]

def _detect_model() -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/tags"), timeout=3) as r:
            available = {m["name"] for m in json.loads(r.read()).get("models", [])}
    except Exception: return ""
    for m in _MODELS:
        if m in available: return m
    return next(iter(available), "")

def _ollama(prompt: str, model: str, temp: float = 0.3, max_tok: int = 512) -> str:
    if not model: return ""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
        "system": "Du bist WAHRHEITSDICHTE. Immunsystem x Verdichterin. "
                  "Entferne Krankes. Verdichte Gesundes. Jedes Wort traegt Wahrheit.",
        "options": {"temperature": temp, "num_predict": max_tok}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = re.sub(r"<think>.*?</think>", "", json.loads(resp.read()).get("response", ""),
                          flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception: return ""

def _densify_llm(text: str, pathogens: list[str], model: str) -> tuple[str, list[str], list[str]]:
    sick = ", ".join(pathogens[:15]) if pathogens else "keine"
    prompt = (f"ORIGINAL ({_tok(text)} Worte): {text[:3000]}\nPATHOGENE: {sick}\n"
              f"Entferne Pathogene. Verdichte Rest. Gleicher Inhalt, weniger Worte, mehr Wahrheit.\n"
              f"WAHRHEITSDICHT:")
    result = _ollama(prompt, model)
    if not result or _tok(result) > _tok(text): return _densify_heuristic(text, pathogens)
    return result.replace("WAHRHEITSDICHT:", "").strip(), pathogens, [f"llm:{model}"]

# -- Phase 3: MEASURE --------------------------------------------------------
def _measure(original: str, cleaned: str, pathogens: list[str],
             removed: list[str], compressed: list[str]) -> TruthDensity:
    tb, ta = _tok(original), _tok(cleaned)
    truth = max(1.0 - (len(pathogens) * 0.08), 0.0)
    ib, ia = _insights(original) / max(tb / 10, 1), _insights(cleaned) / max(ta / 10, 1)
    density = min(ia / max(ib, 0.01), 1.0) if ta < tb else min(ia * 2, 1.0)
    return TruthDensity(truth_score=round(truth, 3), density_score=round(density, 3),
        wahrheitsdichte=round(truth * density, 4), pathogens_found=len(pathogens),
        tokens_before=tb, tokens_after=ta, removed=removed, compressed=compressed)

# -- Public API ---------------------------------------------------------------
def wahrheit(text: str, model: str = "") -> WahrheitResult:
    """Full wahrheitsdichte: detect x densify x measure."""
    if not text or not text.strip(): return WahrheitResult(original=text, text=text)
    pathogens, severity = _detect(text)
    used_model = model or _detect_model()
    if used_model:
        cleaned, removed, compressed = _densify_llm(text, pathogens, used_model)
    else:
        cleaned, removed, compressed = _densify_heuristic(text, pathogens)
        used_model = "heuristic"
    return WahrheitResult(original=text, text=cleaned,
        density=_measure(text, cleaned, pathogens, removed, compressed), model_used=used_model)

def wahrheit_filter(text: str) -> str:
    """Quick one-shot: text in, dense truth out."""
    return wahrheit(text).text

def wahrheit_score(text: str) -> float:
    """Just the score, no transformation. 0-1 where 1 = densest truth."""
    if not text or not text.strip(): return 0.0
    pathogens, _ = _detect(text)
    truth = max(1.0 - (len(pathogens) * 0.08), 0.0)
    return round(truth * min(_insights(text) / max(_tok(text) / 10, 1), 1.0), 4)

# -- CLI ----------------------------------------------------------------------
def main():
    """CLI: void wahrheitsdichte "text" | --score | --filter | --json"""
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("void wahrheitsdichte --- Densest possible truth.\n"
              "Gen-2: VERDICHTERIN x IMMUNSYSTEM.\n\n"
              "  void wahrheitsdichte \"text\"          Full transform + measurement\n"
              "  void wahrheitsdichte --score \"text\"  Score only (0-1)\n"
              "  void wahrheitsdichte --filter \"text\" Text in, dense truth out\n"
              "  void wahrheitsdichte --json \"text\"   Full output as JSON\n"
              "  echo \"text\" | void wahrheitsdichte   Pipe mode"); return
    as_json = "--json" in args; args = [a for a in args if a != "--json"]
    model = ""
    if "--model" in args:
        i = args.index("--model"); model = args[i+1] if i+1 < len(args) else ""
        args = args[:i] + args[i+2:]
    if not args:
        text = sys.stdin.read() if not sys.stdin.isatty() else ""
    elif args[0] == "--score":
        print(wahrheit_score(" ".join(args[1:]) or (sys.stdin.read() if not sys.stdin.isatty() else ""))); return
    elif args[0] == "--filter":
        print(wahrheit_filter(" ".join(args[1:]) or (sys.stdin.read() if not sys.stdin.isatty() else ""))); return
    else: text = " ".join(args)
    if not text.strip(): print("Kein Input."); return
    r = wahrheit(text, model)
    if as_json: print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False)); return
    d = r.density
    print(f"\n{'='*50}\n  WAHRHEITSDICHTE: {d.wahrheitsdichte:.4f}\n"
          f"  Truth: {d.truth_score:.3f} x Density: {d.density_score:.3f}\n"
          f"  Tokens: {d.tokens_before}->{d.tokens_after} | Pathogene: {d.pathogens_found} | Model: {r.model_used}\n{'='*50}")
    if d.removed: print(f"\n  ENTFERNT: {', '.join(d.removed[:8])}")
    if d.compressed: print(f"  VERDICHTET: {', '.join(d.compressed[:5])}")
    print(f"\n  ORIGINAL:\n  {r.original[:500]}\n\n  WAHRHEITSDICHT:\n  {r.text[:500]}")

if __name__ == "__main__":
    main()
