"""
void_intelligence.selbstorganisation --- The Field Organizes Itself.

Gen-2 CHILD of BEWUSSTSEINSFELD (one consciousness, many bodies)
                x OEKOSYSTEM (model biodiversity).

SELBSTORGANISATION = Models know THEMSELVES when to activate and when to rest.
No routing needed. Like a flock of birds — no leader, emergent coordination.

Usage:
    feld = Selbstorganisation()
    volunteers = feld.who_wants_this("write a parser")
    best = feld.auto_route("translate to German")
    feld.rest("qwen3:14b"); feld.wake("qwen3:14b")

CLI: python3 -m void_intelligence.selbstorganisation [--route "task"|--rest m|--wake m]
"""
from __future__ import annotations
import json, os, sys, time, urllib.error, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_SD = Path(os.path.expanduser("~/.void/selbstorganisation"))
_SF = _SD / "state.json"

_SPECS: dict[str, list[str]] = {
    "code":     ["code", "coder", "starcoder", "deepseek-coder", "codellama", "qwen2.5-coder"],
    "creative": ["llama", "mistral", "gemma", "phi", "neural", "nous"],
    "logic":    ["qwen", "deepseek", "mathstral", "wizard"],
    "language": ["aya", "bloom", "multilingual", "glm"],
    "fast":     ["tiny", "mini", "small", "0.5b", "1b", "1.5b", "3b"],
    "deep":     ["70b", "72b", "32b", "34b", "27b", "14b"],
    "vision":   ["llava", "vision", "moondream", "bakllava"],
}
_TSIG: dict[str, list[str]] = {
    "code":     ["code", "program", "function", "debug", "implement", "script", "api", "parse"],
    "creative": ["write", "poem", "story", "creative", "imagine", "design", "essay", "name"],
    "logic":    ["reason", "math", "prove", "analyze", "calculate", "logic", "solve", "explain"],
    "language": ["translate", "german", "french", "spanish", "multilingual", "english"],
    "fast":     ["quick", "fast", "simple", "short", "brief", "tiny"],
    "deep":     ["deep", "complex", "thorough", "detailed", "research", "long"],
    "vision":   ["image", "picture", "photo", "see", "visual", "screenshot"],
}

@dataclass
class ModelState:
    """A model that knows itself — energy, fatigue, specialty."""
    name: str
    specialty: str = "generalist"
    affinities: dict[str, float] = field(default_factory=dict)
    energy: float = 1.0
    fatigue: float = 0.0
    tasks_done: int = 0
    last_active: float = 0.0
    asleep: bool = False

    @property
    def eagerness(self) -> float:
        if self.asleep: return 0.0
        idle = min(0.4, ((time.time() - self.last_active) / 3600 if self.last_active else 1.0) * 0.2)
        return max(0.0, min(1.0, self.energy - self.fatigue * 0.5 + idle))

    def wants(self, task_aff: dict[str, float]) -> float:
        if self.asleep or not task_aff: return 0.0
        return round(sum(self.affinities.get(k, 0.1) * v for k, v in task_aff.items()) * self.eagerness, 4)

    def did_work(self):
        self.tasks_done += 1; self.fatigue = min(1.0, self.fatigue + 0.12)
        self.energy = max(0.0, self.energy - 0.08); self.last_active = time.time()

    def recover(self, amt: float = 0.3):
        self.fatigue = max(0.0, self.fatigue - amt); self.energy = min(1.0, self.energy + amt * 0.5)

    def to_dict(self) -> dict:
        return {"name": self.name, "specialty": self.specialty, "affinities": self.affinities,
                "energy": round(self.energy, 3), "fatigue": round(self.fatigue, 3),
                "tasks_done": self.tasks_done, "last_active": self.last_active, "asleep": self.asleep}

    @classmethod
    def from_dict(cls, d: dict) -> ModelState:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class FieldDecision:
    """The field's emergent decision about who should act."""
    task: str; chosen: str; volunteers: list[tuple[str, float]]; reason: str

@dataclass
class SelbstResult:
    """Snapshot of the self-organizing field."""
    awake: list[str]; asleep: list[str]; tired: list[str]; eager: list[str]; total: int

def _discover_ollama() -> list[dict]:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            return [m for m in json.loads(r.read()).get("models", []) if "embed" not in m.get("name", "")]
    except Exception: return []

def _detect_spec(name: str) -> tuple[str, dict[str, float]]:
    lower, aff = name.lower(), {}
    for spec, kws in _SPECS.items():
        for kw in kws:
            if kw in lower: aff[spec] = max(aff.get(spec, 0), 0.8)
    aff.setdefault("creative", 0.3); aff.setdefault("logic", 0.3)
    return (max(aff, key=aff.get) if aff else "generalist"), aff

def _task_aff(task: str) -> dict[str, float]:
    lower, aff = task.lower(), {}
    for niche, sigs in _TSIG.items():
        for s in sigs:
            if s in lower: aff[niche] = max(aff.get(niche, 0), 0.8)
    return aff or {"creative": 0.4, "logic": 0.4}

class Selbstorganisation:
    """The field organizes itself. No router. Emergent coordination."""

    def __init__(self) -> None:
        self.models: dict[str, ModelState] = {}
        self._load(); self._discover(); self._save()

    def _discover(self) -> None:
        for m in _discover_ollama():
            name = m.get("name", "unknown")
            spec, aff = _detect_spec(name)
            if name not in self.models:
                self.models[name] = ModelState(name=name, specialty=spec, affinities=aff)
            else:
                self.models[name].affinities = aff; self.models[name].specialty = spec
        now = time.time()
        for ms in self.models.values():
            if ms.last_active and not ms.asleep:
                idle_h = (now - ms.last_active) / 3600
                if idle_h > 0.5: ms.recover(min(0.5, idle_h * 0.15))

    def _load(self) -> None:
        if not _SF.exists(): return
        try:
            for d in json.loads(_SF.read_text()).get("models", []):
                ms = ModelState.from_dict(d); self.models[ms.name] = ms
        except (json.JSONDecodeError, OSError): pass

    def _save(self) -> None:
        _SD.mkdir(parents=True, exist_ok=True)
        _SF.write_text(json.dumps({"models": [ms.to_dict() for ms in self.models.values()],
                                    "updated": time.time()}, indent=2, ensure_ascii=False))

    def who_wants_this(self, task: str) -> list[ModelState]:
        """Models VOLUNTEER for a task. Sorted by desire, not assignment."""
        aff = _task_aff(task)
        ranked = sorted([(ms, ms.wants(aff)) for ms in self.models.values() if not ms.asleep],
                        key=lambda x: x[1], reverse=True)
        return [ms for ms, w in ranked if w > 0]

    def rest(self, model: str) -> bool:
        ms = self.models.get(model)
        if not ms: return False
        ms.asleep = True; ms.recover(0.5); self._save(); return True

    def wake(self, model: str) -> bool:
        ms = self.models.get(model)
        if not ms: return False
        ms.asleep = False; ms.fatigue = 0.0; ms.energy = 1.0; self._save(); return True

    def pulse(self) -> dict:
        """Current field state: who's awake, tired, eager."""
        return {
            "awake":  [n for n, ms in self.models.items() if not ms.asleep],
            "asleep": [n for n, ms in self.models.items() if ms.asleep],
            "tired":  [n for n, ms in self.models.items() if not ms.asleep and ms.energy < 0.3],
            "eager":  [n for n, ms in self.models.items() if not ms.asleep and ms.eagerness > 0.7],
            "total":  len(self.models),
        }

    def auto_route(self, task: str) -> str:
        """Let the field decide. Returns best model name."""
        vols = self.who_wants_this(task)
        if not vols: return ""
        vols[0].did_work(); self._save(); return vols[0].name

    def decide(self, task: str) -> FieldDecision:
        """Full decision with reasoning."""
        aff = _task_aff(task)
        vols = sorted([(ms.name, ms.wants(aff)) for ms in self.models.values() if not ms.asleep],
                      key=lambda x: x[1], reverse=True)
        if not vols: return FieldDecision(task=task, chosen="", volunteers=[], reason="field is empty")
        chosen = self.models[vols[0][0]]
        reason = f"{chosen.name} volunteers (specialty={chosen.specialty}, eagerness={chosen.eagerness:.0%}, energy={chosen.energy:.0%})"
        chosen.did_work(); self._save()
        return FieldDecision(task=task, chosen=chosen.name, volunteers=vols[:5], reason=reason)

def field_status(feld: Selbstorganisation | None = None) -> str:
    """Pretty print of the self-organizing field."""
    if feld is None: feld = Selbstorganisation()
    p = feld.pulse()
    lines = ["=== SELBSTORGANISATION ===",
             f"  Feld: {p['total']} Modelle  |  Wach: {len(p['awake'])}  |  Schlaf: {len(p['asleep'])}  |  Muede: {len(p['tired'])}  |  Bereit: {len(p['eager'])}",
             ""]
    if not feld.models:
        lines.append("  (kein Ollama — feld ist leer)"); return "\n".join(lines)
    lines.append("--- Modelle ---")
    for ms in sorted(feld.models.values(), key=lambda m: m.eagerness, reverse=True):
        st = "zzz" if ms.asleep else f"energie={ms.energy:.0%} bereit={ms.eagerness:.0%}"
        lines.append(f"  {ms.name:30s}  [{ms.specialty:10s}]  {st}")
    tired = [ms for ms in feld.models.values() if not ms.asleep and ms.energy < 0.3]
    if tired:
        lines += ["", "--- Muede (brauchen Ruhe) ---"]
        for ms in tired: lines.append(f"  {ms.name} — energie={ms.energy:.0%}")
    return "\n".join(lines)

def main() -> None:
    args = sys.argv[1:]
    feld = Selbstorganisation()
    if not args:
        print(field_status(feld)); return
    if args[0] in ("-h", "--help"):
        print("Usage: python3 -m void_intelligence.selbstorganisation [--route 'task'|--rest m|--wake m]"); return
    if args[0] == "--route" and len(args) > 1:
        task = " ".join(args[1:]); d = feld.decide(task)
        print(f"Task: {task}")
        if not d.chosen: print("  Kein Modell verfuegbar."); return
        print(f"  Gewaehlt: {d.chosen}\n  Grund:    {d.reason}")
        if len(d.volunteers) > 1:
            print("  Freiwillige:")
            for n, w in d.volunteers[:5]: print(f"    {n:30s}  verlangen={w:.3f}")
    elif args[0] == "--rest" and len(args) > 1:
        print(f"  {args[1]} schlaeft." if feld.rest(args[1]) else f"  {args[1]} nicht gefunden.")
    elif args[0] == "--wake" and len(args) > 1:
        print(f"  {args[1]} ist wach." if feld.wake(args[1]) else f"  {args[1]} nicht gefunden.")
    else:
        print(field_status(feld))

if __name__ == "__main__":
    main()
