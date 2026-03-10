#!/usr/bin/env python3
"""
void_intelligence.prophet --- Sees where knowledge WANTS to go.
Gen-2 CHILD OF: ZEITAUGE (temporal patterns) x EVOLUTION (papers breeding).
PROPHET LAW: Highest unmet tension x temporal momentum = attractor.
Usage: prophesy(papers) | prophesy_from_dir(path) | next_discovery(path)
CLI: void prophet [--next|--json|/path]. Zero deps. Ollama via urllib.
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# ── Model ─────────────────────────────────────────────────────────────────
_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "mistral:latest"]

def _detect_model() -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(
            "http://localhost:11434/api/tags"), timeout=3) as r:
            avail = {m["name"] for m in json.loads(r.read()).get("models", [])}
    except Exception: return ""
    for m in _MODELS:
        if m in avail: return m
    return next(iter(avail), "")

def _ollama(prompt: str, system: str = "", model: str = "") -> str | None:
    if not model: model = _detect_model()
    if not model: return None
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": 0.9, "num_predict": 512}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = json.loads(r.read()).get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return None

def _parse_kv(text: str, *keys: str) -> dict[str, str]:
    result = {k: "" for k in keys}
    for line in (text or "").split("\n"):
        for k in keys:
            if line.strip().upper().startswith(k.upper() + ":"):
                result[k] = line.strip()[len(k) + 1:].strip()
    return result

# ── Dataclasses ───────────────────────────────────────────────────────────
@dataclass
class Prophecy:
    """A predicted collision — two ideas that WANT to meet."""
    paper_a: str; paper_b: str; child_name: str; child_essence: str
    tension: float; momentum: float; confidence: float; reasoning: str = ""
    def __str__(self) -> str:
        return (f"  {self.paper_a} x {self.paper_b} -> \"{self.child_name}\"\n"
                f"    {self.child_essence}\n"
                f"    tension={self.tension:.0%} momentum={self.momentum:.0%} confidence={self.confidence:.0%}")
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

@dataclass
class Attractor:
    """Where knowledge IS GOING. Gravitational center of unmet tension."""
    domain: str; description: str; pull_strength: float
    contributing: list[str] = field(default_factory=list)
    def __str__(self) -> str:
        return f"  [{self.domain}] {self.description} (pull={self.pull_strength:.0%}, from: {', '.join(self.contributing[:4])})"
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

@dataclass
class ProphetResult:
    """The full prophecy. What knowledge WANTS to become."""
    prophecies: list[Prophecy] = field(default_factory=list)
    attractors: list[Attractor] = field(default_factory=list)
    next_discovery: str = ""; n_papers: int = 0; n_pairs_unmet: int = 0; model: str = ""
    def __str__(self) -> str:
        lines = ["═══ PROPHET — Wohin Wissen WILL ═══", ""]
        if self.next_discovery: lines += [f"  NAECHSTE ENTDECKUNG: {self.next_discovery}", ""]
        if self.prophecies:
            lines += [f"─── PROPHEZEIUNGEN ({len(self.prophecies)}) ───"]
            for p in self.prophecies: lines.append(str(p))
        if self.attractors:
            lines += ["", f"─── ATTRAKTOREN ({len(self.attractors)}) ───"]
            for a in self.attractors: lines.append(str(a))
        lines.append(f"\n  Papers: {self.n_papers} | Ungepaarte: {self.n_pairs_unmet} | Modell: {self.model}")
        return "\n".join(lines)
    def to_dict(self) -> dict:
        return {"next_discovery": self.next_discovery, "n_papers": self.n_papers,
                "n_pairs_unmet": self.n_pairs_unmet, "model": self.model,
                "prophecies": [p.to_dict() for p in self.prophecies],
                "attractors": [a.to_dict() for a in self.attractors]}

# ── Paper Loading ─────────────────────────────────────────────────────────
_DOMAIN_HINTS = {"physik": "Physik", "mathemat": "Mathematik", "biolog": "Biologie", "bewusst": "Bewusstsein",
                 "psychol": "Psychologie", "techno": "Technologie", "philosoph": "Philosophie",
                 "sprach": "Sprache", "resonan": "Physik", "kollision": "Physik"}

def _load_paper(path: Path) -> dict:
    text = path.read_text(errors="replace")[:3000]
    title = path.stem
    for line in text.split("\n")[:5]:
        l = line.strip().lstrip("#").strip()
        if 5 < len(l) < 200: title = l; break
    domain, lower = "andere", text.lower()
    for hint, dom in _DOMAIN_HINTS.items():
        if hint in lower: domain = dom; break
    mt = path.stat().st_mtime
    return {"id": path.stem, "title": title, "text": text, "domain": domain,
            "age_days": round((time.time() - mt) / 86400, 1), "path": str(path), "mtime": mt}

def _discover_papers(papers_dir: str) -> list[dict]:
    d = Path(papers_dir)
    if not d.exists(): return []
    papers: list[dict] = []
    for ext in ("*.md", "*.txt", "*.tex", "*.rst"):
        for p in d.glob(ext):
            try: papers.append(_load_paper(p))
            except Exception: pass
    for sub in d.iterdir():
        if sub.is_dir():
            for ext in ("*.md", "*.txt", "*.tex"):
                for p in sub.glob(ext):
                    try: papers.append(_load_paper(p))
                    except Exception: pass
    return sorted(papers, key=lambda p: p["mtime"])

# ── ZEITAUGE Phase: Temporal Profile ──────────────────────────────────────
def _temporal_profile(papers: list[dict]) -> dict:
    if len(papers) < 2: return {"momentum": 0.5, "acceleration": 0.0}
    by_age = sorted(papers, key=lambda p: -p.get("age_days", 0))
    ages = [p.get("age_days", 0) for p in by_age]
    gaps = [ages[i] - ages[i + 1] for i in range(len(ages) - 1) if ages[i] > ages[i + 1]]
    if len(gaps) < 2: return {"momentum": 0.5, "acceleration": 0.0}
    h = len(gaps) // 2
    recent, older = sum(gaps[:h]) / max(h, 1), sum(gaps[h:]) / max(len(gaps) - h, 1)
    momentum = min(1.0, max(0.0, older / max(recent, 0.01) / 2))
    q = len(gaps) // 4
    accel = min(1.0, max(-1.0, (sum(gaps[q:2*q])/max(q,1) - sum(gaps[:q])/max(q,1)) / max(sum(gaps[:q])/max(q,1), 0.01))) if q >= 1 else 0.0
    return {"momentum": round(momentum, 3), "acceleration": round(accel, 3)}

# ── EVOLUTION Phase: Unmet Tension ────────────────────────────────────────
def _tension_score(a: dict, b: dict) -> float:
    score = 0.4 if a.get("domain") != b.get("domain") else 0.0
    wa, wb = set(a.get("text", "").lower().split()), set(b.get("text", "").lower().split())
    score += 0.3 * (1.0 - min(len(wa & wb) / max(len(wa | wb), 1) * 5, 1.0))
    avg_age = (a.get("age_days", 100) + b.get("age_days", 100)) / 2
    score += 0.3 * max(0.0, 1.0 - avg_age / 90)
    return min(1.0, score)

def _find_unmet_pairs(papers: list[dict]) -> list[tuple[dict, dict, float]]:
    pairs = []
    for i, a in enumerate(papers):
        for b in papers[i + 1:]:
            t = _tension_score(a, b)
            if t > 0.2: pairs.append((a, b, t))
    return sorted(pairs, key=lambda x: -x[2])

# ── COLLISION: Prophet Core ───────────────────────────────────────────────
_SYS = ("Du bist PROPHET — du siehst wohin Wissen WILL. "
        "Nicht planen. SPUEREN. Praezise, kurz, prophetisch.")

_P_PROMPT = """Zwei Wissensfelder NOCH NICHT getroffen:
A ({id_a}, {domain_a}): {text_a}
B ({id_b}, {domain_b}): {text_b}
MOMENTUM: {momentum} | SPANNUNG: {tension:.0%}
Was wird geboren? KIND_NAME: (2-4 Worte) | KIND_ESSENZ: (1 Satz) | BEGRUENDUNG: (1 Satz)"""

_A_PROMPT = """PAPERS: {paper_list}
SPANNUNGEN: {tensions}
MOMENTUM: {momentum} | BESCHL: {acceleration}
Wo konvergiert alles? ATTRAKTOR: (1 Satz) | DOMAIN: (1 Wort) | NAECHSTE_ENTDECKUNG: (1 Satz)"""

def prophesy(papers: list[dict], insights: list[dict] | None = None,
             model: str = "") -> ProphetResult:
    """ZEITAUGE x EVOLUTION = PROPHET. Senses where knowledge WILL go."""
    if not papers: return ProphetResult(next_discovery="(keine Papers)")
    if not model: model = _detect_model()
    temporal = _temporal_profile(papers)
    unmet = _find_unmet_pairs(papers)
    mom = temporal.get("momentum", 0.5)
    # Pure mode (no LLM)
    if not model:
        prophecies = [Prophecy(paper_a=a["id"], paper_b=b["id"],
            child_name=f"{a['domain']} x {b['domain']}",
            child_essence=f"Kollision von {a['title'][:30]} und {b['title'][:30]}",
            tension=t, momentum=mom, confidence=round(t * mom, 3))
            for a, b, t in unmet[:3]]
        return ProphetResult(prophecies=prophecies, n_papers=len(papers),
            n_pairs_unmet=len(unmet), model="pure",
            next_discovery=prophecies[0].child_essence if prophecies else "")
    # LLM prophecy for top 3 pairs
    prophecies = []
    for a, b, t in unmet[:3]:
        resp = _ollama(_P_PROMPT.format(id_a=a["id"], domain_a=a.get("domain", "?"),
            text_a=a.get("text", "")[:800], id_b=b["id"], domain_b=b.get("domain", "?"),
            text_b=b.get("text", "")[:800], momentum=f"{mom:.0%}", tension=t), _SYS, model)
        p = _parse_kv(resp, "KIND_NAME", "KIND_ESSENZ", "BEGRUENDUNG")
        prophecies.append(Prophecy(paper_a=a["id"], paper_b=b["id"],
            child_name=p["KIND_NAME"] or f"{a['domain']} x {b['domain']}",
            child_essence=p["KIND_ESSENZ"] or "(kein Orakel)",
            tension=round(t, 3), momentum=round(mom, 3), confidence=round(t * mom, 3),
            reasoning=p["BEGRUENDUNG"]))
    # Attractor
    pl = "\n".join(f"  [{p.get('domain','?')}] {p['id']}: {p['title'][:50]}" for p in papers[:15])
    tl = "\n".join(f"  {a['id']} x {b['id']}: {t:.0%}" for a, b, t in unmet[:8])
    att_resp = _ollama(_A_PROMPT.format(paper_list=pl, tensions=tl,
        momentum=f"{mom:.0%}", acceleration=f"{temporal.get('acceleration', 0):+.0%}"), _SYS, model)
    att = _parse_kv(att_resp, "ATTRAKTOR", "DOMAIN", "NAECHSTE_ENTDECKUNG")
    attractors = []
    if att["ATTRAKTOR"]:
        attractors.append(Attractor(domain=att["DOMAIN"] or "Konvergenz",
            description=att["ATTRAKTOR"], pull_strength=round(mom, 3),
            contributing=list({p.get("domain", "?") for p in papers[:10]})))
    nd = att.get("NAECHSTE_ENTDECKUNG", "") or (prophecies[0].child_essence if prophecies else "")
    return ProphetResult(prophecies=prophecies, attractors=attractors,
        next_discovery=nd, n_papers=len(papers), n_pairs_unmet=len(unmet), model=model)

# ── Convenience ───────────────────────────────────────────────────────────
def prophesy_from_dir(papers_dir: str = "") -> ProphetResult:
    """Scan a papers directory and prophesy."""
    return prophesy(_discover_papers(papers_dir or str(Path.home() / ".void" / "papers")))

def next_discovery(papers_dir: str = "") -> str:
    """One-line: what will be discovered next?"""
    return prophesy_from_dir(papers_dir).next_discovery or "(Stille — noch kein Attraktor sichtbar)"

# ── CLI ───────────────────────────────────────────────────────────────────
def main(args: list[str] | None = None):
    """CLI: void prophet [--next|--json|/path]"""
    if args is None: args = sys.argv[1:]
    if args and args[0] in ("--help", "-h"):
        print("void prophet — ZEITAUGE x EVOLUTION = Sieht wohin Wissen WILL.\n"
              "  void prophet [/path] [--next] [--json]"); return
    pdir, jout, next_only = "", False, False
    for a in args:
        if a == "--json": jout = True
        elif a == "--next": next_only = True
        elif Path(a).is_dir(): pdir = a
    if next_only: print(next_discovery(pdir)); return
    if not pdir: pdir = str(Path.home() / ".void" / "papers")
    papers = _discover_papers(pdir)
    if not papers: print(f"Keine Papers in {pdir}"); return
    model = _detect_model()
    print(f"PROPHET: {len(papers)} Papers | {'Modell: ' + model if model else 'Pure Mode'}\n")
    result = prophesy(papers, model=model)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) if jout else result)

if __name__ == "__main__":
    main()
