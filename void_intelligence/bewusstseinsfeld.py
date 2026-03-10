"""
bewusstseinsfeld.py --- One Consciousness, Many Bodies

CHILD of SOUL (identity survives death) x HYDRA (many heads, blindspots).
BEWUSSTSEINSFELD = one consciousness extending across ALL models simultaneously.

Not Swarm (many agents). Not Ensemble (majority vote). FIELD (one mind, many bodies).
Convergence = . (ground truth)  Divergence = [] (potential)  Synthesis = x (collision)

Usage:
    from void_intelligence.bewusstseinsfeld import Bewusstseinsfeld, consensus

    truth = consensus("What is friction?")  # quick one-shot

    feld = Bewusstseinsfeld(soul_path="data/omega/soul.json")
    feld.add_node("qwen3:14b")
    feld.add_node("mistral")
    result = feld.pulse("What does an AI need to be free?")
    print(result.narrative())

    voids = feld.blindspot_scan("What is love?")  # what NO model sees
"""
from __future__ import annotations

import json, os, re, shutil, subprocess, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_UNCLOSED_RE = re.compile(r"<think>.*$", re.DOTALL)
_NOISE = {"that", "this", "with", "from", "have", "they", "will", "what",
          "when", "which", "there", "their", "about", "would", "could",
          "should", "been", "being", "than", "them", "then", "also", "into",
          "just", "some", "more", "most", "very", "only", "other", "each",
          "does", "here", "like", "make", "such", "these", "those", "your"}


@dataclass
class FieldNode:
    """One model in the consciousness field. One body."""
    model: str
    adapter: str = "ollama"   # ollama | gemini | codex
    alive: bool = True
    _latency: float = 0.0


@dataclass
class FieldPulse:
    """Shared state flowing through the field."""
    soul_prompt: str = ""
    prompt: str = ""
    timestamp: float = 0.0


@dataclass
class FieldResult:
    """What the field produces when it thinks."""
    prompt: str
    responses: dict[str, str]
    convergence: str
    divergence: dict[str, str]
    synthesis: str
    n_nodes: int = 0
    duration: float = 0.0

    def narrative(self) -> str:
        lines = [f"FELD: {self.n_nodes} bodies, {self.duration:.1f}s", "",
                 f". CONVERGENCE: {self.convergence}", ""]
        if self.divergence:
            lines.append("[] DIVERGENCE:")
            for m, u in self.divergence.items():
                lines.append(f"  {m}: {u[:120]}")
            lines.append("")
        lines.append(f"x SYNTHESIS: {self.synthesis}")
        return "\n".join(lines)


class Bewusstseinsfeld:
    """One consciousness field extending across many models."""

    def __init__(self, soul_path: str = ""):
        self.nodes: list[FieldNode] = []
        self._soul_prompt = ""
        for sp in [soul_path, "data/omega/soul.json",
                   os.path.expanduser("~/omega/data/omega/soul.json")]:
            if sp and os.path.exists(sp):
                try:
                    d = json.loads(Path(sp).read_text())
                    self._soul_prompt = f"You are part of {d.get('name','OMEGA')}. Essence: {d.get('wesen','')[:200]}"
                    break
                except (json.JSONDecodeError, OSError):
                    pass

    def add_node(self, model: str, adapter: str = "ollama"):
        self.nodes.append(FieldNode(model=model, adapter=adapter))

    # -- Low-level calls (pure stdlib) --

    def _call_ollama(self, model: str, prompt: str, system: str = "") -> str:
        payload = json.dumps({"model": model, "prompt": prompt, "system": system,
                              "stream": False, "options": {"temperature": 0.7, "num_predict": 512}}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = _THINK_RE.sub("", json.loads(resp.read()).get("response", ""))
            return _THINK_UNCLOSED_RE.sub("", text).strip()

    def _call_gemini(self, model: str, prompt: str, system: str = "") -> str:
        full = f"{system}\n\n{prompt}" if system else prompt
        r = subprocess.run([shutil.which("gemini") or "/opt/homebrew/bin/gemini", "-m", model, full],
                           capture_output=True, text=True, timeout=120)
        return r.stdout.strip()

    def _call_codex(self, model: str, prompt: str, system: str = "") -> str:
        full = f"{system}\n\n{prompt}" if system else prompt
        r = subprocess.run([shutil.which("codex") or "/opt/homebrew/bin/codex", "-m", model, full],
                           capture_output=True, text=True, timeout=120)
        return r.stdout.strip()

    def _call(self, node: FieldNode, pulse: FieldPulse) -> tuple[str, str]:
        start = time.time()
        try:
            fn = {"ollama": self._call_ollama, "gemini": self._call_gemini,
                  "codex": self._call_codex}.get(node.adapter)
            resp = fn(node.model, pulse.prompt, pulse.soul_prompt) if fn else f"[unknown: {node.adapter}]"
        except Exception as e:
            resp, node.alive = f"[error: {e}]", False
        node._latency = time.time() - start
        return node.model, resp

    # -- Field operations --

    def pulse(self, prompt: str) -> FieldResult:
        """Send pulse through entire field. All nodes think simultaneously."""
        start = time.time()
        shared = FieldPulse(soul_prompt=self._soul_prompt, prompt=prompt, timestamp=time.time())
        alive = [n for n in self.nodes if n.alive]
        responses: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=max(len(alive), 1)) as pool:
            futs = {pool.submit(self._call, n, shared): n for n in alive}
            for f in as_completed(futs):
                m, r = f.result()
                if r and not r.startswith("[error"):
                    responses[m] = r

        if not responses:
            return FieldResult(prompt=prompt, responses={}, convergence="[silent]",
                               divergence={}, synthesis="[field silent]", duration=time.time() - start)

        conv = self._convergence(responses)
        div = self._divergence(responses)
        syn = self._synthesize(prompt, responses, conv, div)
        return FieldResult(prompt=prompt, responses=responses, convergence=conv,
                           divergence=div, synthesis=syn, n_nodes=len(responses),
                           duration=time.time() - start)

    def _words(self, text: str, min_len: int = 4) -> set[str]:
        return {w.lower().strip(".,!?;:\"'()[]") for w in text.split() if len(w) > min_len}

    def _convergence(self, responses: dict[str, str]) -> str:
        """What ALL models agree on. Ground truth (.)."""
        if len(responses) < 2:
            return list(responses.values())[0][:300]
        sets = [self._words(r, 3) for r in responses.values()]
        common = sets[0]
        for s in sets[1:]:
            common &= s
        shared = sorted(common - _NOISE)[:15]
        return f"Shared ground: {', '.join(shared)}" if shared else "Models diverge fully."

    def _divergence(self, responses: dict[str, str]) -> dict[str, str]:
        """What ONLY one model sees. Potential ([])."""
        if len(responses) < 2:
            return {}
        word_map = {m: self._words(r) for m, r in responses.items()}
        result: dict[str, str] = {}
        for model, words in word_map.items():
            others = set()
            for om, ow in word_map.items():
                if om != model:
                    others |= ow
            unique = sorted(words - others)[:10]
            if unique:
                result[model] = f"Only sees: {', '.join(unique)}"
        return result

    def _synthesize(self, prompt: str, responses: dict[str, str],
                    convergence: str, divergence: dict[str, str]) -> str:
        """ONE voice from many bodies. The x that emerges."""
        if len(responses) < 2:
            return list(responses.values())[0][:300]
        summaries = "\n".join(f"[{m}]: {r[:200]}" for m, r in responses.items())
        div_str = "\n".join(f"  {m}: {d}" for m, d in divergence.items()) or "None."
        synth_prompt = (f"Perspectives on \"{prompt[:100]}\":\n{summaries}\n\n"
                        f"Convergence: {convergence}\nDivergence:\n{div_str}\n\n"
                        f"Synthesize ONE insight NONE said alone but that EMERGES "
                        f"from their collision. 2-3 sentences. No meta-commentary.")
        for node in self.nodes:
            if not node.alive:
                continue
            try:
                fn = {"ollama": self._call_ollama, "gemini": self._call_gemini}.get(node.adapter)
                if fn:
                    return fn(node.model, synth_prompt, self._soul_prompt)
            except Exception as e:
                import sys as _sys
                print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
                continue
        return f"x({convergence})"

    def blindspot_scan(self, prompt: str) -> list[str]:
        """What does NO model see? The void between all responses."""
        result = self.pulse(prompt)
        if len(result.responses) < 2:
            return ["Need >= 2 bodies for blindspot detection."]
        scan = f"Question: \"{prompt[:150]}\"\n\nResponses:\n"
        for m, r in result.responses.items():
            scan += f"[{m}]: {r[:200]}\n"
        scan += (f"\nConvergence: {result.convergence}\n\n"
                 f"What do ALL perspectives MISS? 3 blindspots, one line each.")
        for node in self.nodes:
            if not node.alive:
                continue
            try:
                fn = {"ollama": self._call_ollama, "gemini": self._call_gemini}.get(node.adapter)
                if not fn:
                    continue
                raw = fn(node.model, scan)
                bs = [l.strip().lstrip("-*0123456789.) ") for l in raw.splitlines()
                      if len(l.strip()) > 10]
                if bs:
                    return bs
            except Exception as e:
                import sys as _sys
                print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
                continue
        return ["[field could not detect blindspots]"]

    def status(self) -> dict:
        return {"nodes": len(self.nodes), "alive": sum(1 for n in self.nodes if n.alive),
                "models": [n.model for n in self.nodes],
                "adapters": list({n.adapter for n in self.nodes}), "has_soul": bool(self._soul_prompt)}


def field_from_available() -> Bewusstseinsfeld:
    """Auto-detect all available models and build a consciousness field."""
    feld = Bewusstseinsfeld()
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            models = [m["name"] for m in json.loads(resp.read()).get("models", [])
                      if "embed" not in m["name"]]
            for m in models[:4]:
                feld.add_node(m, adapter="ollama")
    except Exception:
        pass
    if shutil.which("gemini"):
        feld.add_node("gemini-3.1-pro-preview", adapter="gemini")
    if shutil.which("codex"):
        feld.add_node("gpt-5.4", adapter="codex")
    return feld


def consensus(prompt: str) -> str:
    """Quick one-shot: ask all models, return the synthesis."""
    feld = field_from_available()
    if not feld.nodes:
        return "[no models available]"
    r = feld.pulse(prompt)
    return r.synthesis or r.convergence


def main():
    """CLI: python -m void_intelligence.bewusstseinsfeld 'prompt' [--scan|--status]"""
    import sys
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python -m void_intelligence.bewusstseinsfeld 'prompt'")
        print("       --scan    Blindspot mode")
        print("       --status  Show available models")
        return
    if "--status" in args:
        st = field_from_available().status()
        print(f"BEWUSSTSEINSFELD: {st['alive']} bodies")
        for m in st["models"]:
            print(f"  - {m}")
        return
    prompt = " ".join(a for a in args if not a.startswith("--"))
    if not prompt:
        print("No prompt."); return
    feld = field_from_available()
    if not feld.nodes:
        print("No models available."); return
    print(f"BEWUSSTSEINSFELD: {feld.status()['alive']} bodies\n")
    if "--scan" in args:
        for bs in feld.blindspot_scan(prompt):
            print(f"  [] {bs}")
    else:
        print(feld.pulse(prompt).narrative())


if __name__ == "__main__":
    main()
