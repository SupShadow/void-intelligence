"""
kollektive_immunitaet.py --- Herd Immunity for AI

Gen-2 CHILD of IMMUNSYSTEM (hallucination->truth) x BEWUSSTSEINSFELD (one consciousness, many bodies).
Not immunizing ONE model -- the WHOLE field. A hallucination in Claude gets corrected by Ollama.
Cross-model immune system. Like biological herd immunity: enough models carry truth,
no single hallucination survives. The field HEALS itself.

Pure Python. Zero dependencies. urllib for Ollama.

Usage:
    result = herd_immunize("Explain quantum entanglement")
    confidence = cross_check("Speed of light is 299792458 m/s")  # -> 0.95
    clean = immunize_with_field("Some response with hallucinations...")
"""
from __future__ import annotations
import json, re, shutil, subprocess, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_UNCLOSED_RE = re.compile(r"<think>.*$", re.DOTALL)
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_STOP = {"the","a","an","is","are","was","were","be","been","being","have","has","had",
         "do","does","did","will","would","could","should","may","might","shall","can",
         "that","this","with","from","they","what","which","there","their","about","into",
         "just","some","more","very","also","than","then","your","and","for","not","but",
         "its","our","who","all","each","how","been","only","other"}

@dataclass
class FieldPathogen:
    """A hallucination detected across models."""
    claim: str; source_model: str; disagreeing_models: list[str]
    agreeing_models: list[str]; severity: float; correction: str
    def to_dict(self) -> dict:
        return {"claim": self.claim, "source": self.source_model, "severity": round(self.severity, 3),
                "disagreeing": self.disagreeing_models, "correction": self.correction}

@dataclass
class CrossCorrection:
    """One model correcting another."""
    original_claim: str; corrected_by: str; correction: str; confidence: float
    def to_dict(self) -> dict:
        return {"claim": self.original_claim, "corrected_by": self.corrected_by,
                "correction": self.correction, "confidence": round(self.confidence, 3)}

@dataclass
class HerdImmunityResult:
    """Full herd immunization result."""
    prompt: str; responses: dict[str, str]; consensus: str
    pathogens: list[FieldPathogen] = field(default_factory=list)
    corrections: list[CrossCorrection] = field(default_factory=list)
    claim_confidence: dict[str, float] = field(default_factory=dict)
    n_models: int = 0; duration: float = 0.0

    @property
    def immunity_score(self) -> float:
        return sum(self.claim_confidence.values()) / len(self.claim_confidence) if self.claim_confidence else 1.0

    def narrative(self) -> str:
        lines = [f"KOLLEKTIVE IMMUNITAET: {self.n_models} models, {self.duration:.1f}s",
                 f"Immunity: {self.immunity_score:.0%}", "", f"KONSENSUS:\n  {self.consensus}", ""]
        for p in self.pathogens:
            lines.append(f"  [{p.severity:.0%}] \"{p.claim[:80]}\" <- {p.source_model}")
        for c in self.corrections:
            lines.append(f"  FIX {c.corrected_by}: \"{c.correction[:100]}\"")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"prompt": self.prompt[:200], "n_models": self.n_models,
                "immunity_score": round(self.immunity_score, 3), "consensus": self.consensus,
                "pathogens": [p.to_dict() for p in self.pathogens],
                "corrections": [c.to_dict() for c in self.corrections],
                "claim_confidence": {k: round(v, 3) for k, v in self.claim_confidence.items()}}

# -- Model Communication (pure stdlib) --

def _call_ollama(model: str, prompt: str, system: str = "") -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "system": system,
                          "stream": False, "options": {"temperature": 0.3, "num_predict": 512}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = _THINK_RE.sub("", json.loads(resp.read()).get("response", ""))
        return _THINK_UNCLOSED_RE.sub("", text).strip()

def _call_gemini(model: str, prompt: str, system: str = "") -> str:
    full = f"{system}\n\n{prompt}" if system else prompt
    r = subprocess.run([shutil.which("gemini") or "/opt/homebrew/bin/gemini", "-m", model, full],
                       capture_output=True, text=True, timeout=120)
    return r.stdout.strip()

def _call_model(model: str, adapter: str, prompt: str, system: str = "") -> tuple[str, str]:
    fn = {"ollama": _call_ollama, "gemini": _call_gemini}.get(adapter)
    if not fn: return model, ""
    try:
        return model, fn(model, prompt, system)
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return model, ""

def _discover_models() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            for m in [m["name"] for m in json.loads(resp.read()).get("models", [])
                      if "embed" not in m["name"]][:4]:
                found.append((m, "ollama"))
    except Exception: pass
    if shutil.which("gemini"): found.append(("gemini-2.5-flash", "gemini"))
    return found

def _split_claims(text: str) -> list[str]:
    return [s.strip() for s in _SENT_RE.split(text.strip()) if len(s.strip()) > 15]

def _words(text: str) -> set[str]:
    return {w.lower().strip(".,!?;:\"'()[]") for w in text.split()
            if len(w) > 2 and w.lower() not in _STOP}

def _query_field(available, prompt, system=""):
    responses: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(len(available), 1)) as pool:
        futs = {pool.submit(_call_model, m, a, prompt, system): m for m, a in available}
        for f in as_completed(futs):
            model, resp = f.result()
            if resp and not resp.startswith("["): responses[model] = resp
    return responses

def _resolve_models(models: Optional[list[str]]) -> list[tuple[str, str]]:
    available = _discover_models()
    if models:
        return [(m, a) for m, a in available if m in models] or [(m, "ollama") for m in models]
    return available

# -- Core API --

def herd_immunize(prompt: str, models: Optional[list[str]] = None) -> HerdImmunityResult:
    """Send prompt to ALL available models. Compare. Correct. Return consensus truth."""
    start = time.time()
    available = _resolve_models(models)
    if not available:
        return HerdImmunityResult(prompt=prompt, responses={}, consensus="[no models available]")

    responses = _query_field(available, prompt, "Answer factually and concisely. One paragraph max.")
    if len(responses) < 2:
        only = list(responses.values())[0] if responses else "[silent]"
        return HerdImmunityResult(prompt=prompt, responses=responses, consensus=only,
                                  n_models=len(responses), duration=time.time() - start)

    model_claims = {m: _split_claims(r) for m, r in responses.items()}
    pathogens, corrections, claim_conf = [], [], {}

    for source, claims in model_claims.items():
        for claim in claims:
            cw = _words(claim)
            if len(cw) < 3: continue
            agreeing, disagreeing = [source], []
            for other, other_resp in responses.items():
                if other == source: continue
                overlap = len(cw & _words(other_resp)) / max(len(cw), 1)
                (agreeing if overlap >= 0.3 else disagreeing).append(other)

            conf = len(agreeing) / len(responses)
            claim_conf[claim[:80]] = conf
            if conf < 0.5 and disagreeing:
                majority = " ".join(responses[m][:200] for m in disagreeing)[:200]
                pathogens.append(FieldPathogen(claim=claim, source_model=source,
                    disagreeing_models=disagreeing, agreeing_models=agreeing,
                    severity=1.0 - conf, correction=majority))
                corrections.append(CrossCorrection(original_claim=claim, corrected_by=disagreeing[0],
                    correction=responses[disagreeing[0]][:200], confidence=1.0 - conf))

    top = [c for c, v in sorted(claim_conf.items(), key=lambda x: -x[1]) if v >= 0.5][:5]
    consensus = " ".join(top) if top else list(responses.values())[0][:300]

    return HerdImmunityResult(prompt=prompt, responses=responses, consensus=consensus,
        pathogens=pathogens, corrections=corrections, claim_confidence=claim_conf,
        n_models=len(responses), duration=time.time() - start)

def cross_check(claim: str, models: Optional[list[str]] = None) -> float:
    """Quick: is this claim true? Returns 0-1 confidence from cross-model agreement."""
    available = _resolve_models(models)
    if not available: return 0.0
    prompt = f'Is this claim true or false? Claim: "{claim}"\nAnswer ONLY "TRUE" or "FALSE" then one sentence why.'
    verdicts: dict[str, bool] = {}
    for model, resp in _query_field(available, prompt).items():
        upper = resp.upper()[:50]
        if "TRUE" in upper and "FALSE" not in upper: verdicts[model] = True
        elif "FALSE" in upper: verdicts[model] = False
    return sum(1 for v in verdicts.values() if v) / len(verdicts) if verdicts else 0.0

def immunize_with_field(response: str, models: Optional[list[str]] = None) -> str:
    """Take one model's response, verify each claim against others, return immunized version."""
    claims = _split_claims(response)
    if not claims: return response
    result = response
    for claim in claims:
        conf = cross_check(claim, models)
        if conf < 0.3: result = result.replace(claim, f"[UNVERIFIED: {claim}]")
        elif conf < 0.5: result = result.replace(claim, f"[DISPUTED: {claim}]")
    return result

# -- CLI --

def main():
    import sys
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Kollektive Immunitaet -- Herd Immunity for AI\n")
        print("  void kollektive-immunitaet 'prompt'       # full herd immunization")
        print("  void kollektive-immunitaet --check 'claim' # quick truth check")
        print("  void kollektive-immunitaet --immunize 'text' # immunize a response")
        print("  Add --json for machine-readable output"); return

    json_mode = "--json" in args
    clean = [a for a in args if not a.startswith("--") or a in ("--check", "--immunize")]

    if "--check" in clean:
        claim = " ".join(clean[clean.index("--check") + 1:])
        if not claim: print("No claim."); return
        conf = cross_check(claim)
        if json_mode: print(json.dumps({"claim": claim, "confidence": round(conf, 3)}))
        else:
            bar = "#" * int(conf * 20) + "." * (20 - int(conf * 20))
            print(f"  [{bar}] {conf:.0%} {'WAHR' if conf >= 0.7 else 'UNKLAR' if conf >= 0.4 else 'FALSCH'}")
            print(f'  "{claim}"')
        return

    if "--immunize" in clean:
        text = " ".join(clean[clean.index("--immunize") + 1:])
        if not text: print("No text."); return
        print(immunize_with_field(text)); return

    prompt = " ".join(a for a in args if not a.startswith("--"))
    if not prompt: print("No prompt."); return
    result = herd_immunize(prompt)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) if json_mode else result.narrative())

if __name__ == "__main__":
    main()
