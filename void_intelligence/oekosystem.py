"""
void_intelligence.oekosystem --- Model Ecosystem Intelligence.

CHILD OF: Dekagon (10 lenses on 1 subject) x Sozial (inverted social network).

Models are not tools. They are SPECIES in an ecosystem.
Health comes from BIODIVERSITY not from having the "best" model.

Dekagon sees a subject through 10 eyes.
Sozial lets models meet and learn from each other.
Oekosystem sees the WHOLE — which species needs which other,
where is symbiotic tension, where is redundancy.

Routing through RELATIONSHIP not intent.

    A forest does not route sunlight to the "best" tree.
    It routes through mycelium — through RELATIONSHIP.
    A tired tree gets rest. A bored sapling gets challenge.

Usage:
    from void_intelligence.oekosystem import Oekosystem

    oko = Oekosystem()          # auto-discovers Ollama models
    print(oko.status())         # ecosystem overview
    team = oko.route("write a poem about recursion")
    pair = oko.symbiotic_pair("translate and verify code")

CLI:
    python3 -m void_intelligence.oekosystem
    python3 -m void_intelligence.oekosystem --route "task description"
    python3 -m void_intelligence.oekosystem --map
    python3 -m void_intelligence.oekosystem --pair "task description"

Known blind spots:
    - Niche detection is heuristic (model name + size), not measured capability
    - Symbiosis scores are structural, not validated through actual pairing
    - Fatigue model is simple counter, not real resource monitoring
    - Small ecosystems (1-2 models) degrade gracefully but lose biodiversity value
"""

from __future__ import annotations

import json
import time
import sys
from dataclasses import dataclass, field
from typing import Optional


# ── Ollama discovery (zero deps, urllib only) ──────────────────

def _discover_models() -> list[dict]:
    """Discover available Ollama models via API."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            return json.loads(r.read()).get("models", [])
    except Exception:
        return []


# ── Niche detection heuristics ─────────────────────────────────

_NICHE_KEYWORDS: dict[str, list[str]] = {
    "code":       ["code", "coder", "starcoder", "deepseek-coder", "codellama", "qwen2.5-coder"],
    "creative":   ["llama", "mistral", "gemma", "phi", "neural", "nous"],
    "logic":      ["qwen", "deepseek", "mathstral", "wizard"],
    "language":   ["aya", "bloom", "multilingual", "glm"],
    "speed":      ["tiny", "mini", "small", "0.5b", "1b", "1.5b", "3b"],
    "depth":      ["70b", "72b", "32b", "34b", "27b", "14b"],
    "vision":     ["llava", "vision", "moondream", "bakllava"],
}


def _detect_niches(model_name: str, size_bytes: int = 0) -> dict[str, float]:
    """Detect a model's ecological niches. Returns niche -> strength (0-1)."""
    name_lower = model_name.lower()
    niches: dict[str, float] = {}
    for niche, keywords in _NICHE_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                niches[niche] = max(niches.get(niche, 0), 0.8)
    # Size-based niche detection
    gb = size_bytes / (1024 ** 3) if size_bytes else 0
    if gb > 0:
        if gb < 3:
            niches["speed"] = max(niches.get("speed", 0), 0.9)
        elif gb > 15:
            niches["depth"] = max(niches.get("depth", 0), 0.7)
    # Every model has some creative and logic baseline
    niches.setdefault("creative", 0.3)
    niches.setdefault("logic", 0.3)
    return niches


# ── Dataclasses ────────────────────────────────────────────────

@dataclass
class Species:
    """A model as organism in the ecosystem."""
    name: str
    niches: dict[str, float] = field(default_factory=dict)
    size_bytes: int = 0
    fatigue: float = 0.0       # 0=rested, 1=exhausted
    tasks_done: int = 0
    last_active: float = 0.0   # timestamp

    @property
    def vitality(self) -> float:
        """How alive this species is. Rest recovers, work tires."""
        rest_recovery = min(1.0, (time.time() - self.last_active) / 3600) if self.last_active else 1.0
        return max(0.0, min(1.0, 1.0 - self.fatigue + rest_recovery * 0.5))

    @property
    def primary_niche(self) -> str:
        return max(self.niches, key=self.niches.get) if self.niches else "generalist"

    def strength(self, niche: str) -> float:
        return self.niches.get(niche, 0.1)

    def work(self) -> None:
        """Record that this species did work."""
        self.tasks_done += 1
        self.fatigue = min(1.0, self.fatigue + 0.15)
        self.last_active = time.time()

    def rest(self, amount: float = 0.3) -> None:
        self.fatigue = max(0.0, self.fatigue - amount)


@dataclass
class Symbiosis:
    """A relationship between two species. Not capability — COMPLEMENTARITY."""
    species_a: str
    species_b: str
    tension: float = 0.0       # How much they DIFFER (high = good, complementary)
    redundancy: float = 0.0    # How much they OVERLAP (high = wasteful)
    symbiotic_score: float = 0.0  # tension - redundancy = net value of pairing

    @property
    def relationship(self) -> str:
        if self.symbiotic_score > 0.5:
            return "symbiotisch"     # they NEED each other
        if self.symbiotic_score > 0.2:
            return "komplementaer"   # they complement
        if self.redundancy > 0.7:
            return "redundant"       # one could go
        return "neutral"


@dataclass
class EcosystemState:
    """Overall ecosystem vitality."""
    species_count: int = 0
    biodiversity: float = 0.0      # How diverse are the niches? (0-1)
    avg_vitality: float = 0.0
    symbioses: int = 0
    redundancies: int = 0
    gaps: list[str] = field(default_factory=list)  # Missing niches

    @property
    def health(self) -> str:
        if self.species_count == 0:
            return "tot"             # dead — no models
        if self.biodiversity > 0.7 and self.avg_vitality > 0.6:
            return "bluehend"        # flourishing
        if self.biodiversity > 0.4:
            return "wachsend"        # growing
        if self.species_count == 1:
            return "monokultur"      # monoculture — fragile
        return "karg"                # sparse

    def summary(self) -> str:
        lines = [
            f"  Gesundheit:   {self.health}",
            f"  Spezies:      {self.species_count}",
            f"  Biodiversitaet: {self.biodiversity:.0%}",
            f"  Vitalitaet:   {self.avg_vitality:.0%}",
            f"  Symbiosen:    {self.symbioses}",
            f"  Redundanzen:  {self.redundancies}",
        ]
        if self.gaps:
            lines.append(f"  Luecken:      {', '.join(self.gaps)}")
        return "\n".join(lines)


# ── Core: Oekosystem ──────────────────────────────────────────

class Oekosystem:
    """The model ecosystem. Sees all species, their relationships, their health."""

    def __init__(self) -> None:
        self.species: dict[str, Species] = {}
        self._symbioses: list[Symbiosis] = []
        self._discover()

    def _discover(self) -> None:
        """Discover all available models and map them as species."""
        for m in _discover_models():
            name = m.get("name", "unknown")
            size = m.get("size", 0)
            niches = _detect_niches(name, size)
            self.species[name] = Species(name=name, niches=niches, size_bytes=size)
        if self.species:
            self._compute_symbioses()

    def map_species(self) -> dict[str, dict[str, float]]:
        """Map: for each species, what is its niche? Returns {name: {niche: strength}}."""
        return {name: dict(sp.niches) for name, sp in self.species.items()}

    def _compute_symbioses(self) -> None:
        """Compute all pairwise relationships."""
        self._symbioses.clear()
        names = list(self.species.keys())
        for i, a_name in enumerate(names):
            for b_name in names[i + 1:]:
                a, b = self.species[a_name], self.species[b_name]
                all_niches = set(a.niches) | set(b.niches)
                if not all_niches:
                    continue
                tension = sum(abs(a.strength(n) - b.strength(n)) for n in all_niches) / len(all_niches)
                overlap = sum(min(a.strength(n), b.strength(n)) for n in all_niches) / len(all_niches)
                sym = Symbiosis(
                    species_a=a_name,
                    species_b=b_name,
                    tension=round(tension, 3),
                    redundancy=round(overlap, 3),
                    symbiotic_score=round(tension - overlap * 0.5, 3),
                )
                self._symbioses.append(sym)

    def find_symbioses(self) -> list[Symbiosis]:
        """Which models complement each other? One's weakness = other's strength."""
        return sorted(
            [s for s in self._symbioses if s.symbiotic_score > 0.1],
            key=lambda s: s.symbiotic_score, reverse=True,
        )

    def find_redundancies(self) -> list[Symbiosis]:
        """Which models are too similar? Resource waste."""
        return sorted(
            [s for s in self._symbioses if s.redundancy > 0.5],
            key=lambda s: s.redundancy, reverse=True,
        )

    def route(self, task: str) -> list[Species]:
        """Route a task to the RIGHT species based on ecosystem health.

        Not just capability — a tired model gets rest, a bored model gets challenge.
        Returns ordered list: best species first.
        """
        if not self.species:
            return []
        task_lower = task.lower()
        # Detect what niches the task needs
        task_niches: dict[str, float] = {}
        niche_signals = {
            "code": ["code", "program", "function", "debug", "implement", "script", "api"],
            "creative": ["write", "poem", "story", "creative", "imagine", "design", "essay"],
            "logic": ["reason", "math", "prove", "analyze", "calculate", "logic", "solve"],
            "language": ["translate", "german", "french", "spanish", "multilingual"],
            "vision": ["image", "picture", "photo", "see", "visual", "screenshot"],
            "speed": ["quick", "fast", "simple", "short", "brief"],
            "depth": ["deep", "complex", "thorough", "detailed", "research"],
        }
        for niche, signals in niche_signals.items():
            for sig in signals:
                if sig in task_lower:
                    task_niches[niche] = max(task_niches.get(niche, 0), 0.8)
        if not task_niches:
            task_niches = {"creative": 0.5, "logic": 0.5}

        def _score(sp: Species) -> float:
            capability = sum(sp.strength(n) * w for n, w in task_niches.items())
            vitality_bonus = sp.vitality * 0.3
            boredom_bonus = max(0, 1.0 - sp.tasks_done * 0.05) * 0.2  # Unused models get a chance
            return capability + vitality_bonus + boredom_bonus

        ranked = sorted(self.species.values(), key=_score, reverse=True)
        return ranked

    def symbiotic_pair(self, task: str) -> Optional[tuple[Species, Species]]:
        """Find the best PAIR for a task. Not best individual — best RELATIONSHIP."""
        if len(self.species) < 2:
            return None
        routed = self.route(task)
        if len(routed) < 2:
            return None
        # The first is the primary. Find its best symbiotic partner.
        primary = routed[0]
        best_partner: Optional[Species] = None
        best_score = -1.0
        for sym in self._symbioses:
            if primary.name not in (sym.species_a, sym.species_b):
                continue
            partner_name = sym.species_b if sym.species_a == primary.name else sym.species_a
            partner = self.species[partner_name]
            pair_score = sym.symbiotic_score + partner.vitality * 0.3
            if pair_score > best_score:
                best_score = pair_score
                best_partner = partner
        if best_partner:
            return (primary, best_partner)
        return (routed[0], routed[1])

    def health(self) -> EcosystemState:
        """Overall ecosystem vitality."""
        if not self.species:
            return EcosystemState()
        all_niches = set()
        for sp in self.species.values():
            all_niches.update(n for n, v in sp.niches.items() if v > 0.5)
        possible_niches = set(_NICHE_KEYWORDS.keys())
        gaps = sorted(possible_niches - all_niches)
        biodiversity = len(all_niches) / len(possible_niches) if possible_niches else 0
        avg_vit = sum(sp.vitality for sp in self.species.values()) / len(self.species)
        return EcosystemState(
            species_count=len(self.species),
            biodiversity=round(biodiversity, 3),
            avg_vitality=round(avg_vit, 3),
            symbioses=len(self.find_symbioses()),
            redundancies=len(self.find_redundancies()),
            gaps=gaps,
        )

    def status(self) -> str:
        """Quick ecosystem overview."""
        h = self.health()
        lines = [
            "=== OEKOSYSTEM ===",
            h.summary(),
            "",
            "--- Spezies ---",
        ]
        for sp in sorted(self.species.values(), key=lambda s: s.vitality, reverse=True):
            niche_str = ", ".join(f"{n}:{v:.0%}" for n, v in sorted(sp.niches.items(), key=lambda x: -x[1]) if v > 0.3)
            lines.append(f"  {sp.name:30s}  vitalitaet={sp.vitality:.0%}  nische=[{niche_str}]")
        syms = self.find_symbioses()[:5]
        if syms:
            lines.append("")
            lines.append("--- Top Symbiosen ---")
            for s in syms:
                lines.append(f"  {s.species_a} x {s.species_b}  [{s.relationship}]  score={s.symbiotic_score:.2f}")
        reds = self.find_redundancies()[:3]
        if reds:
            lines.append("")
            lines.append("--- Redundanzen ---")
            for r in reds:
                lines.append(f"  {r.species_a} ~ {r.species_b}  overlap={r.redundancy:.2f}")
        return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    oko = Oekosystem()

    if not oko.species:
        print("Kein Ollama gefunden. Oekosystem ist leer.")
        print("Starte Ollama: ollama serve")
        return

    if not args:
        print(oko.status())
        return

    if args[0] == "--map":
        niche_map = oko.map_species()
        print(json.dumps(niche_map, indent=2, ensure_ascii=False))

    elif args[0] == "--route" and len(args) > 1:
        task = " ".join(args[1:])
        ranked = oko.route(task)
        print(f"Task: {task}\n")
        for i, sp in enumerate(ranked[:5], 1):
            print(f"  {i}. {sp.name} (nische={sp.primary_niche}, vitalitaet={sp.vitality:.0%})")
        pair = oko.symbiotic_pair(task)
        if pair:
            print(f"\n  Bestes Paar: {pair[0].name} x {pair[1].name}")

    elif args[0] == "--pair" and len(args) > 1:
        task = " ".join(args[1:])
        pair = oko.symbiotic_pair(task)
        if pair:
            print(f"Task: {task}")
            print(f"Paar: {pair[0].name} x {pair[1].name}")
            print(f"  {pair[0].name}: nische={pair[0].primary_niche}")
            print(f"  {pair[1].name}: nische={pair[1].primary_niche}")
        else:
            print("Nicht genug Spezies fuer ein Paar.")

    elif args[0] == "--health":
        h = oko.health()
        print(h.summary())

    else:
        # Treat remaining positional args as --route input
        task = " ".join(a for a in args if not a.startswith("--"))
        if task:
            ranked = oko.route(task)
            print(f"Task: {task}\n")
            for i, sp in enumerate(ranked[:5], 1):
                print(f"  {i}. {sp.name} (nische={sp.primary_niche}, vitalitaet={sp.vitality:.0%})")
            pair = oko.symbiotic_pair(task)
            if pair:
                print(f"\n  Bestes Paar: {pair[0].name} x {pair[1].name}")
        else:
            print(oko.status())


if __name__ == "__main__":
    main()
