#!/usr/bin/env python3
"""
void_intelligence.lebendes_produkt --- A business ecosystem that self-densifies.

CHILD OF: oekosystem.py (model biodiversity) × evolution.py (papers breed autonomously)

A living product is not shipped. It is PLANTED.
Every customer gets an EVOLVING system, not a static product.
The product gets smarter the more it is used. Profinsoft × VOID.

Usage:
    from void_intelligence.lebendes_produkt import LebendesProdukt, create_product
    lp = create_product("profinsoft-crm")
    lp.signal("client-search", feedback="too slow")
    step = lp.evolve()
    print(lp.status())

CLI:
    void lebendes-produkt --create "profinsoft-crm"
    void lebendes-produkt --signal "client-search" --feedback "too slow"
    void lebendes-produkt --evolve
    void lebendes-produkt --status

Zero external deps. Ollama via urllib.
"""
from __future__ import annotations
import json, sys, time, urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

_STATE_ROOT = Path.home() / ".void" / "produkte"
_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "mistral:latest"]
_NEG = {"slow","broken","bug","wrong","bad","error","langsam","fehler","kaputt","falsch","schlecht"}

def _detect_model() -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(
            "http://localhost:11434/api/tags"), timeout=3) as r:
            avail = {m["name"] for m in json.loads(r.read()).get("models", [])}
    except Exception: return ""
    for m in _MODELS:
        if m in avail: return m
    return next(iter(avail), "")

def _ask_ollama(prompt: str, model: str = "") -> str:
    model = model or _detect_model()
    if not model: return ""
    try:
        body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                    data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("response", "")
    except Exception: return ""

# ── Dataclasses ─────────────────────────────────────────────────────────
@dataclass
class UsageSignal:
    usage: str; feedback: str = ""; ts: float = 0.0; positive: bool = True
    def __post_init__(self):
        if not self.ts: self.ts = time.time()
        if self.feedback: self.positive = not any(w in self.feedback.lower() for w in _NEG)
    def to_dict(self) -> dict:
        return {"usage": self.usage, "feedback": self.feedback, "ts": self.ts, "positive": self.positive}
    @classmethod
    def from_dict(cls, d: dict) -> UsageSignal:
        return cls(**{k: d[k] for k in ("usage", "feedback", "ts", "positive") if k in d})

@dataclass
class EvolutionStep:
    generation: int; patterns: list[str] = field(default_factory=list)
    mutations: list[str] = field(default_factory=list)
    fitness_before: float = 0.0; fitness_after: float = 0.0; ts: float = 0.0
    def __post_init__(self):
        if not self.ts: self.ts = time.time()
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
    @classmethod
    def from_dict(cls, d: dict) -> EvolutionStep:
        return cls(**{k: d[k] for k in d if k in cls.__dataclass_fields__})

@dataclass
class ProductOrganism:
    name: str; generation: int = 0; signals: list[UsageSignal] = field(default_factory=list)
    evolutions: list[EvolutionStep] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list); born: float = 0.0
    def __post_init__(self):
        if not self.born: self.born = time.time()
    def to_dict(self) -> dict:
        return {"name": self.name, "generation": self.generation, "born": self.born,
                "signals": [s.to_dict() for s in self.signals],
                "evolutions": [e.to_dict() for e in self.evolutions],
                "capabilities": self.capabilities}
    @classmethod
    def from_dict(cls, d: dict) -> ProductOrganism:
        o = cls(name=d["name"], generation=d.get("generation", 0),
                capabilities=d.get("capabilities", []), born=d.get("born", 0.0))
        o.signals = [UsageSignal.from_dict(s) for s in d.get("signals", [])]
        o.evolutions = [EvolutionStep.from_dict(e) for e in d.get("evolutions", [])]
        return o

@dataclass
class ProduktResult:
    product: str; fitness: float; generation: int; signal_count: int
    mutations: list[str]; summary: str = ""

# ── Core ────────────────────────────────────────────────────────────────
class LebendesProdukt:
    """A living product that evolves through usage."""

    def __init__(self, product_name: str, state_dir: str = ""):
        self._dir = Path(state_dir) if state_dir else _STATE_ROOT / product_name
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "organism.json"
        if self._path.exists():
            self._org = ProductOrganism.from_dict(json.loads(self._path.read_text()))
        else:
            self._org = ProductOrganism(name=product_name); self._save()

    def _save(self):
        self._path.write_text(json.dumps(self._org.to_dict(), indent=2, ensure_ascii=False))

    def signal(self, usage: str, feedback: str = ""):
        """Record usage signal — what the user did, optional feedback."""
        self._org.signals.append(UsageSignal(usage=usage, feedback=feedback)); self._save()

    def fitness(self) -> float:
        """Signal diversity x positive feedback ratio. 0.0 to 1.0."""
        sigs = self._org.signals
        if not sigs: return 0.0
        diversity = min(len(set(s.usage for s in sigs)) / max(len(sigs) * 0.5, 1.0), 1.0)
        ratio = sum(1 for s in sigs if s.positive) / len(sigs)
        return round(diversity * ratio, 4)

    def evolve(self) -> EvolutionStep:
        """Evolve based on accumulated signals. Returns the evolution step."""
        fit_before = self.fitness()
        patterns, mutations = self._find_patterns(), self.suggest_mutations()
        llm_m = self._llm_evolve(patterns, mutations)
        if llm_m: mutations = llm_m
        self._org.generation += 1
        for m in mutations:
            if m not in self._org.capabilities: self._org.capabilities.append(m)
        step = EvolutionStep(generation=self._org.generation, patterns=patterns,
                             mutations=mutations, fitness_before=fit_before,
                             fitness_after=self.fitness())
        self._org.evolutions.append(step); self._save()
        return step

    def suggest_mutations(self) -> list[str]:
        """What should change next? Usage gaps and pain patterns."""
        sigs = self._org.signals
        if not sigs: return ["awaiting first usage signals"]
        mutations: list[str] = []
        pain_areas = Counter(s.usage for s in sigs if not s.positive)
        for area, n in pain_areas.most_common(3):
            mutations.append(f"fix: {area} ({n} pain signals)")
        used = set(s.usage for s in sigs)
        for cap in self._org.capabilities:
            if cap not in used and not cap.startswith("fix:"): mutations.append(f"unused: {cap}")
        freq = Counter(s.usage for s in sigs)
        for area, n in freq.most_common(3):
            if n >= 3 and area not in pain_areas: mutations.append(f"deepen: {area} ({n} uses)")
        return mutations or ["product is stable, monitor for new signals"]

    def status(self) -> str:
        """Product health, evolution count, fitness trend."""
        o, fit = self._org, self.fitness()
        age = (time.time() - o.born) / 86400
        trend = ""
        if len(o.evolutions) >= 2:
            d = fit - o.evolutions[-2].fitness_after
            trend = f" ({'+'if d>=0 else ''}{d:.3f})"
        lines = [f"=== {o.name} === Gen {o.generation}", f"Fitness: {fit:.4f}{trend}",
                 f"Signals: {len(o.signals)} | Capabilities: {len(o.capabilities)}",
                 f"Evolutions: {len(o.evolutions)} | Age: {age:.1f}d"]
        if o.capabilities: lines.append(f"Recent: {', '.join(o.capabilities[-5:])}")
        return "\n".join(lines)

    def _find_patterns(self) -> list[str]:
        sigs = self._org.signals
        if not sigs: return []
        patterns = [f"{u} x{n}" for u, n in Counter(s.usage for s in sigs).most_common(5) if n >= 2]
        if len(sigs) >= 3:
            gaps = [sigs[i+1].ts - sigs[i].ts for i in range(len(sigs)-1)]
            avg = sum(gaps) / len(gaps)
            if avg < 60: patterns.append("burst-usage")
            elif avg > 86400: patterns.append("sparse-usage")
        return patterns

    def _llm_evolve(self, patterns: list[str], mutations: list[str]) -> list[str]:
        if not _detect_model() or not patterns: return []
        prompt = (f"Product: {self._org.name}, Gen {self._org.generation}\n"
                  f"Patterns: {', '.join(patterns)}\nMutations: {', '.join(mutations)}\n"
                  f"Capabilities: {', '.join(self._org.capabilities[-10:])}\n\n"
                  "Suggest 3 concrete product improvements. One line each. No numbering.")
        resp = _ask_ollama(prompt)
        if not resp: return []
        return [l.strip().lstrip("0123456789.-) ") for l in resp.strip().split("\n")
                if l.strip() and len(l.strip()) > 5][:3]

def create_product(name: str) -> LebendesProdukt:
    """Create or load a living product."""
    return LebendesProdukt(name)

# ── CLI ─────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(prog="void lebendes-produkt",
                                description="Living Product — evolves through usage")
    p.add_argument("--create", metavar="NAME", help="Create a new living product")
    p.add_argument("--name", metavar="NAME", default="", help="Product name")
    p.add_argument("--signal", metavar="USAGE", help="Record usage signal")
    p.add_argument("--feedback", default="", help="Feedback for signal")
    p.add_argument("--evolve", action="store_true", help="Evolve the product")
    p.add_argument("--status", action="store_true", help="Show product status")
    p.add_argument("--fitness", action="store_true", help="Show fitness score")
    p.add_argument("--mutations", action="store_true", help="Suggest mutations")
    args = p.parse_args()
    name = args.create or args.name
    if not name:
        if _STATE_ROOT.exists():
            prods = [d.name for d in _STATE_ROOT.iterdir() if d.is_dir()]
            if len(prods) == 1: name = prods[0]
            elif prods: print(f"Products: {', '.join(prods)}\nUse --name to select."); return
            else: print("No products. Use --create NAME."); return
        else: print("No products. Use --create NAME."); return
    lp = LebendesProdukt(name)
    if args.create:
        print(f"Created: {name}\n{lp.status()}")
    elif args.signal:
        lp.signal(args.signal, feedback=args.feedback)
        print(f"Signal: {args.signal}" + (f" [{args.feedback}]" if args.feedback else ""))
    elif args.evolve:
        s = lp.evolve()
        print(f"Gen {s.generation} | Patterns: {', '.join(s.patterns) or '-'}")
        print(f"Mutations: {', '.join(s.mutations) or '-'}")
        print(f"Fitness: {s.fitness_before:.4f} -> {s.fitness_after:.4f}")
    elif args.fitness: print(f"{lp.fitness():.4f}")
    elif args.mutations:
        for m in lp.suggest_mutations(): print(f"  {m}")
    else: print(lp.status())

if __name__ == "__main__":
    main()
