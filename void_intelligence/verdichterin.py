"""void_intelligence.verdichterin --- Die Dichte-Hebamme.

CHILD OF: hebamme.py x omegaeus.py
HEBAMME: "What do you FEEL?" | OMEGAEUS: "What is DENSEST?"
VERDICHTERIN: "What do you REALLY want to say?"
A 7B through the Verdichterin sounds like a 70B. Not compression — midwife gaze
applied to density. Three phases: Feel x Dense = Voice.
CLI: void verdichterin "text" | --prompt | --response | --file
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DenseVoice:
    """Maximum meaning, minimum words."""
    text: str
    emotional_essence: str = ""
    density_essence: str = ""
    collision: str = ""
    tokens_before: int = 0
    tokens_after: int = 0
    insights: int = 0

    @property
    def compression_ratio(self) -> float: return self.tokens_after / self.tokens_before if self.tokens_before else 0

@dataclass
class MidwifeSession:
    """One verdichterin pass: input -> feel -> dense -> collide."""
    input_text: str
    phase_feel: str = ""
    phase_dense: str = ""
    phase_collide: str = ""
    model: str = ""
    timestamp: str = ""
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {"feel": self.phase_feel[:200], "dense": self.phase_dense[:200],
                "collide": self.phase_collide[:200], "model": self.model,
                "tokens_used": self.tokens_used}

@dataclass
class VerdichterinResult:
    """Complete verdichtung result."""
    dense_voice: DenseVoice
    session: MidwifeSession
    g_density_before: float = 0
    g_density_after: float = 0

    @property
    def improvement(self) -> float: return self.g_density_after / self.g_density_before if self.g_density_before else 0

    def to_dict(self) -> dict:
        return {"text": self.dense_voice.text,
                "compression": f"{self.dense_voice.compression_ratio:.0%}",
                "g_before": round(self.g_density_before, 4),
                "g_after": round(self.g_density_after, 4),
                "improvement": f"{self.improvement:.1f}x",
                "session": self.session.to_dict()}

_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b",
           "phi4:latest", "mistral:latest"]

def _detect_model() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            available = {m["name"] for m in json.loads(resp.read()).get("models", [])}
    except Exception:
        return ""
    for m in _MODELS:
        if m in available:
            return m
    return next(iter(available), "")

def _ollama(prompt: str, system: str = "", model: str = "",
            temp: float = 0.4, max_tok: int = 512) -> tuple[str, int]:
    if not model:
        model = _detect_model()
    if not model:
        return "", 0
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                        "stream": False,
                        "options": {"temperature": temp, "num_predict": max_tok}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            d = json.loads(resp.read())
            text = re.sub(r"<think>.*?</think>", "", d.get("response", ""), flags=re.DOTALL)
            text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
            tokens = d.get("eval_count", 0) + d.get("prompt_eval_count", 0)
            return text, tokens or (len(prompt.split()) + len(text.split()))
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return "", 0

_SYS = """Du bist die VERDICHTERIN — Dichte-Hebamme.
Kind von Hebamme (Fuehlen) x Omegaeus (Verdichten).
Nicht kuerzen. VERDICHTEN. Jedes Wort das bleibt traegt mehr."""

_P_FEEL = """FUEHLE diesen Text. Nicht analysieren.
TEXT: {text}
ESSENZ: (1 Satz — emotionaler Kern)
WORT: (1 Wort — traegt das meiste Gewicht)
UNGESAGT: (1 Satz — was der Text eigentlich sagen will)"""

_P_DENSE = """VERDICHTE. Behalte die Essenz, entferne das Gewicht.
ORIGINAL: {text}
GEFUEHL: {feeling}
Regeln: Keine Fuellwoerter. Zahlen bleiben. Namen bleiben. Knochen bleiben.
Klingt wie der Autor auf seinem besten Tag.
VERDICHTET:"""

_P_COLLIDE = """KOLLISION: Fuehlen x Dichte = Stimme.
GEFUEHL: {feeling}
VERDICHTET: {dense}
ORIGINAL ({n} Worte): {original}
Schreibe die ENDGUELTIGE Version. Kuerzer als Original. Dichter als Verdichtung.
Waermer als Analyse. Jemand der GENAU weiss was er sagen will.
STIMME:"""

_P_PROMPT = """Verdichte System-Prompt. Gleiches Verhalten, weniger Tokens.
Anweisungen behalten (kuerzer). Erklaerungen entfernen. Hoeflichkeiten weg.
ORIGINAL: {prompt}
VERDICHTET:"""

_P_RESPONSE = """Verdichte LLM-Antwort. Inhalt bleibt, Fluff geht.
Entferne: Hoeflichkeitsfloskeln, Wiederholungen, leere Uebergaenge.
Behalte: Einsichten, Fakten, Zahlen, Stimme.
ORIGINAL: {response}
VERDICHTET:"""

def _tokens(text: str) -> int:
    return len(text.split())

def _insights(text: str) -> int:
    sents = [s.strip() for s in re.split(r'[.!?]\s+', text.strip()) if len(s.strip()) > 5]
    fillers = ("also", "eigentlich", "natuerlich", "basically", "actually", "sure")
    return max(1, sum(1 for s in sents if not any(s.lower().startswith(f) for f in fillers)))

def _g(text: str) -> float:
    t = _tokens(text)
    return _insights(text) / t if t else 0

def verdichten(text: str, model: str = "") -> VerdichterinResult:
    """Verdichte through three phases: Feel x Dense = Voice."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    g_before = _g(text)
    tok_before = _tokens(text)
    total_tok = 0

    # Phase 1: HEBAMME
    feeling, t1 = _ollama(_P_FEEL.format(text=text[:3000]), _SYS, model)
    total_tok += t1
    if not feeling:
        return _heuristic(text, ts, g_before, tok_before)

    # Phase 2: OMEGAEUS
    dense, t2 = _ollama(_P_DENSE.format(text=text[:3000], feeling=feeling), _SYS, model)
    total_tok += t2

    # Phase 3: COLLISION
    voice, t3 = _ollama(_P_COLLIDE.format(
        feeling=feeling, dense=dense, original=text[:2000], n=tok_before),
        _SYS, model, temp=0.6)
    total_tok += t3

    voice = voice.replace("STIMME:", "").strip()
    tok_after = _tokens(voice)

    return VerdichterinResult(
        dense_voice=DenseVoice(text=voice, emotional_essence=feeling,
                                density_essence=dense,
                                collision=f"feel({t1}t) x dense({t2}t) = voice({t3}t)",
                                tokens_before=tok_before, tokens_after=tok_after,
                                insights=_insights(voice)),
        session=MidwifeSession(input_text=text[:500], phase_feel=feeling,
                                phase_dense=dense, phase_collide=voice,
                                model=model or _detect_model(), timestamp=ts,
                                tokens_used=total_tok),
        g_density_before=g_before, g_density_after=_g(voice))

def _heuristic(text: str, ts: str, g_before: float, tok_before: int) -> VerdichterinResult:
    """Fallback without model. Pure filler removal."""
    dense = text
    for f in ["basically", "actually", "in fact", "I think that", "it seems like",
              "also", "eigentlich", "natuerlich", "grundsaetzlich", "sozusagen",
              "quasi", "im Grunde genommen"]:
        dense = re.sub(rf'\b{re.escape(f)}\b\s*', '', dense, flags=re.IGNORECASE)
    dense = re.sub(r'\s+', ' ', dense).strip()
    tok_after = _tokens(dense)
    return VerdichterinResult(
        dense_voice=DenseVoice(text=dense, tokens_before=tok_before,
                                tokens_after=tok_after, insights=_insights(dense)),
        session=MidwifeSession(input_text=text[:500], model="heuristic", timestamp=ts),
        g_density_before=g_before, g_density_after=_g(dense))

def verdichten_prompt(system_prompt: str, model: str = "") -> str:
    """Make any system prompt DENSER. Same behavior, fewer tokens."""
    r, _ = _ollama(_P_PROMPT.format(prompt=system_prompt[:4000]), _SYS, model, temp=0.3, max_tok=1024)
    return r.replace("VERDICHTET:", "").strip() if r else system_prompt

def verdichten_response(response: str, model: str = "") -> str:
    """Make any LLM response DENSER. Content stays, fluff goes."""
    r, _ = _ollama(_P_RESPONSE.format(response=response[:4000]), _SYS, model, temp=0.3, max_tok=1024)
    return r.replace("VERDICHTET:", "").strip() if r else response

def verdichten_conversation(messages: list[dict], model: str = "") -> list[dict]:
    """Compress conversation. System->verdichten_prompt, assistant->verdichten_response, user->sacred."""
    result = []
    for msg in messages:
        role, content = msg.get("role", ""), msg.get("content", "")
        if not content or role == "user":
            result.append(msg)
        elif role == "system":
            result.append({"role": "system", "content": verdichten_prompt(content, model)})
        elif role == "assistant":
            result.append({"role": "assistant", "content": verdichten_response(content, model)})
        else:
            result.append(msg)
    return result

def main(args: list[str] | None = None):
    """CLI: void verdichterin [text|--prompt|--response|--file]"""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("""void verdichterin --- Die Dichte-Hebamme.
Kind von hebamme.py x omegaeus.py. "Was willst du WIRKLICH sagen?"

Usage:
  void verdichterin "text"              Verdichte beliebigen Text
  void verdichterin --prompt "system"   Verdichte System-Prompt
  void verdichterin --response "text"   Verdichte LLM-Antwort
  void verdichterin --file path.txt     Verdichte Datei
  void verdichterin --json "text"       Output als JSON
  void verdichterin --model qwen3:8b    Bestimmtes Modell""")
        return

    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    model = ""
    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]

    if not args:
        return

    if args[0] == "--prompt":
        text = " ".join(args[1:])
        r = verdichten_prompt(text, model)
        print(f"{r}\n--- {_tokens(text)} -> {_tokens(r)} Tokens ---")
        return

    if args[0] == "--response":
        text = " ".join(args[1:])
        r = verdichten_response(text, model)
        print(f"{r}\n--- {_tokens(text)} -> {_tokens(r)} Tokens ---")
        return

    if args[0] == "--file":
        p = Path(" ".join(args[1:]))
        text = p.read_text(errors="replace") if p.exists() else ""
    else:
        text = " ".join(args)
        p = Path(text)
        if p.exists() and p.is_file():
            text = p.read_text(errors="replace")

    if not text.strip():
        print("Kein Input.")
        return

    result = verdichten(text, model)

    if as_json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    print(f"\n{'═' * 40}\n{result.dense_voice.text}\n{'═' * 40}")
    print(f"G-Dichte: {result.g_density_before:.4f} -> {result.g_density_after:.4f}"
          f" ({result.improvement:.1f}x)")
    print(f"Tokens:   {result.dense_voice.tokens_before} -> {result.dense_voice.tokens_after}"
          f" ({result.dense_voice.compression_ratio:.0%})")
    if result.session.phase_feel:
        for line in result.session.phase_feel.split("\n")[:3]:
            if line.strip():
                print(f"  Hebamme: {line.strip()}")

if __name__ == "__main__":
    main()
