"""void_intelligence.dichter_assistent --- Universal Density Upgrade Layer.

CHILD OF: VERDICHTERIN (density midwife) x SEHENDE HAENDE (seeing hands)
DICHTER ASSISTENT: Any chatbot through VOID = 10x denser. MIDDLEWARE.
Input -> VOID -> Model -> VOID -> Output. Both directions get denser.
pip install void-intelligence -> every model upgraded.
CLI: python3 -m void_intelligence.dichter_assistent "prompt" "response"
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class DichterResponse:
    """Dense output: measured, compressed, upgraded."""
    text: str
    tokens_before: int = 0
    tokens_after: int = 0
    compression_ratio: float = 0.0
    density_gain: float = 0.0
    lenses: list[str] = field(default_factory=list)
    phase_see: str = ""
    phase_dense: str = ""
    def summary(self) -> str:
        return (f"{self.tokens_before}->{self.tokens_after} tokens "
                f"({self.compression_ratio:.0%}) | density {self.density_gain:.1f}x")

@dataclass
class AssistentConfig:
    """Configuration for the density layer."""
    model: str = ""
    temp: float = 0.3
    max_tokens: int = 1024
    ollama_url: str = "http://localhost:11434"
    strip_fluff: bool = True
    min_gain: float = 1.05
    _MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "phi4:latest", "mistral:latest"]
    def resolve_model(self) -> str:
        if self.model: return self.model
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                avail = {m["name"] for m in json.loads(resp.read()).get("models", [])}
        except Exception: return ""
        for m in self._MODELS:
            if m in avail: return m
        return next(iter(avail), "")

# ── Internals ────────────────────────────────────────────────────────────
def _tok(t: str) -> int: return len(t.split())

def _insights(t: str) -> int:
    sents = [s.strip() for s in re.split(r'[.!?]\s+', t.strip()) if len(s.strip()) > 5]
    fillers = ("also", "eigentlich", "natuerlich", "basically", "actually",
               "sure", "of course", "I think", "it seems", "well", "you know")
    return max(1, sum(1 for s in sents if not any(s.lower().startswith(f) for f in fillers)))

def _g(t: str) -> float:
    n = _tok(t); return _insights(t) / n if n else 0.0

def _ollama(prompt: str, system: str, cfg: AssistentConfig) -> str:
    model = cfg.resolve_model()
    if not model: return ""
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                        "stream": False, "options": {"temperature": cfg.temp,
                        "num_predict": cfg.max_tokens}}).encode()
    try:
        req = urllib.request.Request(f"{cfg.ollama_url}/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = json.loads(resp.read()).get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return ""

_FLUFF = re.compile(
    r"\b(basically|actually|in fact|I think that|it seems like|of course|"
    r"eigentlich|natuerlich|grundsaetzlich|sozusagen|quasi|im Grunde genommen|"
    r"as you know|needless to say|let me explain|I would like to|please note that|"
    r"vielleicht|eventuell|moeglicherweise|in Erwaegung ziehen|koennten|koennte|waere)\b\s*",
    re.IGNORECASE)
_OPENERS = re.compile(
    r"^(Sure!|Of course!|Great question!|Absolutely!|That's a great question[.!]|"
    r"I'd be happy to help[.!]|Certainly[.!]|No problem[.!])\s*", re.IGNORECASE | re.MULTILINE)

def _heuristic(text: str, cfg: AssistentConfig) -> str:
    out = _OPENERS.sub("", text) if cfg.strip_fluff else text
    out = _FLUFF.sub("", out) if cfg.strip_fluff else out
    return re.sub(r'[ \t]+', ' ', re.sub(r'\n{3,}', '\n\n', out)).strip()

# ── SEHENDE HAENDE: 3 Lenses ────────────────────────────────────────────
_SYS_SEE = "Du bist SEHENDE HAENDE. 3 Linsen auf jeden Wunsch. Kurz. Praezise."
_P_SEE = """3 LINSEN auf diesen Prompt:
PROMPT: {prompt}
WIRKLICH: (1 Satz — was der User WIRKLICH will)
FEHLT: (1 Satz — welcher Kontext fehlt)
ERGEBNIS: (1 Satz — wie die perfekte Antwort aussieht)"""

def _see(prompt: str, cfg: AssistentConfig) -> list[str]:
    r = _ollama(_P_SEE.format(prompt=prompt[:2000]), _SYS_SEE, cfg)
    if not r: return ["Intent unklar", "Kontext fehlt", "Direkte Antwort"]
    return [l.strip() for l in r.split("\n") if l.strip()][:3]

# ── VERDICHTERIN: Make response DENSE ────────────────────────────────────
_SYS_DENSE = "Du bist VERDICHTERIN. Nicht kuerzen — VERDICHTEN. Code/Listen bleiben."
_P_DENSE = """VERDICHTE. Inhalt bleibt, Fluff geht.
Entferne: Hoeflichkeitsfloskeln, Wiederholungen, Erklaerungen des Offensichtlichen.
Behalte: Einsichten, Fakten, Zahlen, Code, Listen, Stimme.
VISION: {vision}
ORIGINAL: {response}
VERDICHTET:"""

def _dense(response: str, lenses: list[str], cfg: AssistentConfig) -> str:
    vision = " | ".join(lenses) if lenses else "Direkte Antwort"
    r = _ollama(_P_DENSE.format(vision=vision, response=response[:4000]), _SYS_DENSE, cfg)
    return r.replace("VERDICHTET:", "").strip() if r else _heuristic(response, cfg)

# ── Core ─────────────────────────────────────────────────────────────────
def dicht(prompt: str, response: str, model: str = "", cfg: AssistentConfig | None = None) -> DichterResponse:
    """Make any response 10x denser. SEHENDE HAENDE see, VERDICHTERIN compresses."""
    c = cfg or AssistentConfig(model=model)
    tok_before, g_before = _tok(response), _g(response)
    lenses = _see(prompt, c)
    dense_text = _dense(response, lenses, c)
    if dense_text == response: dense_text = _heuristic(response, c)
    tok_after, g_after = _tok(dense_text), _g(dense_text)
    ratio = tok_after / tok_before if tok_before else 1.0
    gain = g_after / g_before if g_before else 1.0
    if gain < c.min_gain and tok_after >= tok_before:
        dense_text = _heuristic(response, c)
        tok_after, g_after = _tok(dense_text), _g(dense_text)
        ratio = tok_after / tok_before if tok_before else 1.0
        gain = g_after / g_before if g_before else 1.0
    return DichterResponse(text=dense_text, tokens_before=tok_before, tokens_after=tok_after,
        compression_ratio=ratio, density_gain=gain, lenses=lenses,
        phase_see=" | ".join(lenses), phase_dense=dense_text[:200])

# ── Decorator ────────────────────────────────────────────────────────────
def dicht_wrap(generate_fn: Callable | None = None, *, model: str = "") -> Callable:
    """Decorator: @dicht_wrap on any fn(prompt, ...) -> str to make output denser."""
    def decorator(fn: Callable) -> Callable:
        def wrapper(prompt: str, *args, **kwargs) -> str:
            raw = fn(prompt, *args, **kwargs)
            if not isinstance(raw, str) or not raw.strip(): return raw
            return dicht(prompt, raw, model=model).text
        wrapper.__wrapped__, wrapper.__name__ = fn, f"dicht_{fn.__name__}"
        return wrapper
    if generate_fn is not None and callable(generate_fn): return decorator(generate_fn)
    return decorator

# ── System Prompt Densifier ──────────────────────────────────────────────
_SYS_P = "Verdichte System-Prompts. Gleiches Verhalten, weniger Tokens."
_P_SYS = """Verdichte System-Prompt. Anweisungen bleiben (kuerzer). Erklaerungen weg.
ORIGINAL: {original}
VERDICHTET:"""

def dicht_system_prompt(original: str, model: str = "") -> str:
    """Densify any system prompt. Same behavior, fewer tokens."""
    c = AssistentConfig(model=model)
    r = _ollama(_P_SYS.format(original=original[:4000]), _SYS_P, c)
    return r.replace("VERDICHTET:", "").strip() if r else _heuristic(original, c)

# ── Middleware ───────────────────────────────────────────────────────────
def dicht_middleware(messages: list[dict], model: str = "") -> list[dict]:
    """Middleware for chat pipelines. Densifies system+assistant. User=sacred."""
    result = []
    for msg in messages:
        role, content = msg.get("role", ""), msg.get("content", "")
        if not content or role == "user": result.append(msg)
        elif role == "system": result.append({**msg, "content": dicht_system_prompt(content, model)})
        elif role == "assistant": result.append({**msg, "content": dicht("", content, model).text})
        else: result.append(msg)
    return result

# ── CLI ──────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None):
    """CLI: void dichter-assistent "prompt" "response" | --wrap | --system"""
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("void dichter-assistent --- Universal Density Upgrade Layer.\n"
              "Kind von verdichterin.py x sehende_haende.py.\n\nUsage:\n"
              '  void dichter-assistent "prompt" "response"   Densify response\n'
              '  void dichter-assistent --system "prompt"      Densify system prompt\n'
              '  void dichter-assistent --wrap                 stdin: prompt\\nresponse\n'
              '  void dichter-assistent --json "p" "r"         JSON output\n'
              '  void dichter-assistent --model qwen3:8b ...   Specific model')
        return
    as_json = "--json" in args; args = [a for a in args if a != "--json"]
    model = ""
    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if not args: return
    if args[0] == "--system":
        text = " ".join(args[1:]); r = dicht_system_prompt(text, model)
        print(f"{r}\n--- {_tok(text)} -> {_tok(r)} tokens ---"); return
    if args[0] == "--wrap":
        lines = sys.stdin.read().strip().split("\n", 1)
        prompt, response = (lines[0] if lines else ""), (lines[1] if len(lines) > 1 else "")
        result = dicht(prompt, response, model)
        if as_json:
            print(json.dumps({"text": result.text, "tokens_before": result.tokens_before,
                "tokens_after": result.tokens_after, "compression_ratio": round(result.compression_ratio, 3),
                "density_gain": round(result.density_gain, 2), "lenses": result.lenses},
                indent=2, ensure_ascii=False))
        else: print(result.text)
        return
    prompt, response = (args[0], " ".join(args[1:])) if len(args) >= 2 else ("", args[0])
    t0 = time.time(); result = dicht(prompt, response, model)
    if as_json:
        print(json.dumps({"text": result.text, "tokens_before": result.tokens_before,
            "tokens_after": result.tokens_after, "compression_ratio": round(result.compression_ratio, 3),
            "density_gain": round(result.density_gain, 2), "lenses": result.lenses},
            indent=2, ensure_ascii=False))
        return
    print(f"\n{'=' * 50}\n{result.text}\n{'=' * 50}")
    print(f"Tokens:  {result.summary()}")
    if result.lenses:
        print("Lenses:  " + " | ".join(result.lenses))
    print(f"({time.time() - t0:.2f}s)")

if __name__ == "__main__":
    main()
