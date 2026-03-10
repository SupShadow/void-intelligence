#!/usr/bin/env python3
"""
void_intelligence.wissens_archaeologie --- Autonomous Discovery Machine.
Gen-2 CHILD OF: archaeologe.py (finds hidden) × evolution.py (papers breed)
Digs in ALL papers, breeds FOSSILS across them. Zero deps. Ollama via urllib.

CLI: void wissens-archaeologie [--dig|--daemon|--deepest]
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

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

def _ollama(prompt: str, system: str = "", model: str = "",
            temp: float = 0.7, max_tok: int = 1024) -> str | None:
    if not model: model = _detect_model()
    if not model: return None
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": temp, "num_predict": max_tok}}).encode()
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

# ── Data ─────────────────────────────────────────────────────────────────
@dataclass
class Discovery:
    """A fossil found in a paper — something always there, never seen."""
    paper_id: str; essence: str; depth: int; evidence: str = ""; found_at: str = ""
    def __str__(self) -> str: return f"  {'.' * self.depth} [{self.depth}] {self.essence} ({self.paper_id})"
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("paper_id", "essence", "depth", "evidence", "found_at")}

@dataclass
class FossilBreed:
    """Two fossils from different papers mated = new knowledge."""
    fossil_a: str; paper_a: str; fossil_b: str; paper_b: str
    child_essence: str; emergent: str; depth: float = 0.0; born_at: str = ""
    def __str__(self) -> str:
        return f"  {self.paper_a} × {self.paper_b} → {self.child_essence}\n    EMERGENT: {self.emergent}"
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("fossil_a", "paper_a", "fossil_b", "paper_b",
                                                "child_essence", "emergent", "depth", "born_at")}

@dataclass
class ArchaeologyResult:
    """Full dig session: discoveries + breeds."""
    discoveries: list[Discovery] = field(default_factory=list)
    breeds: list[FossilBreed] = field(default_factory=list)
    papers_scanned: int = 0; deepest_depth: int = 0; model: str = ""
    def __str__(self) -> str:
        lines = [f"═══ WISSENS-ARCHAEOLOGIE — {self.papers_scanned} Papers, "
                 f"{len(self.discoveries)} Fossilien, {len(self.breeds)} Kreuzungen ═══"]
        if self.discoveries:
            lines.append("\n  FOSSILIEN:")
            for d in sorted(self.discoveries, key=lambda x: -x.depth)[:10]: lines.append(str(d))
        if self.breeds:
            lines.append("\n  KREUZUNGEN:")
            for b in self.breeds[:5]: lines.append(str(b))
        return "\n".join(lines)

# ── Prompts ──────────────────────────────────────────────────────────────
_SYS = ("Du bist ein Wissens-Archaeologe. Du liest Texte RUECKWAERTS und findest "
        "was IMMER da war aber NIE gesehen wurde. Du erfindest NICHTS. Du findest.")
_DIG = ("Lies diesen Text RUECKWAERTS. Was war IMMER hier, nie gesehen?\n"
        "TEXT (umgedreht):\n{reversed_text}\n\nORIGINAL:\n{original_snippet}\n\n"
        'JSON-Array (2-4 Fossilien):\n[{{"essence": "was verborgen war", "depth": 1-5, '
        '"evidence": "Beweis"}}]\nTiefe 1=Oberflaeche, 5=tief. NUR JSON.')
_BREED = ("Zwei Fossilien aus verschiedenen Papers paaren sich.\n"
          "FOSSIL A ({paper_a}): {fossil_a}\nFOSSIL B ({paper_b}): {fossil_b}\n"
          "Kind = A × B. KUERZER und DICHTER als beide.\nFormat:\n"
          "ESSENZ: ... (1 Satz)\nEMERGENT: ... (was NUR im Kind existiert)")

# ── Core ─────────────────────────────────────────────────────────────────
class WissensArchaeologie:
    """Finds in ALL papers what was always there but never seen."""

    def __init__(self, papers_dir: str = ""):
        self._dir = Path(papers_dir) if papers_dir else Path.home() / ".void" / "papers"
        self._state = Path.home() / ".void" / "wissens_archaeologie.jsonl"
        self._state.parent.mkdir(parents=True, exist_ok=True)
        self.model = _detect_model()

    def _papers(self) -> list[Path]:
        dirs_to_try = [self._dir]
        fallback = Path.cwd() / "papers"
        if fallback != self._dir:
            dirs_to_try.append(fallback)
        ps: list[Path] = []
        for d in dirs_to_try:
            if not d.exists():
                continue
            for ext in ("*.md", "*.txt", "*.tex"):
                ps.extend(d.rglob(ext))
            if ps:
                break
        return sorted(ps, key=lambda p: p.name)

    def _parse_fossils(self, raw: str, paper_id: str) -> list[Discovery]:
        match = re.search(r"\[.*\]", raw or "", re.DOTALL)
        if not match: return []
        try: items = json.loads(match.group())
        except json.JSONDecodeError: return []
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        return [Discovery(paper_id=paper_id, essence=str(it["essence"]),
                          depth=int(it.get("depth", 1)), evidence=str(it.get("evidence", "")),
                          found_at=now) for it in items if isinstance(it, dict) and "essence" in it]

    def _dig_paper(self, path: Path) -> list[Discovery]:
        text = path.read_text(errors="replace")[:4000]
        paras = re.split(r"\n\s*\n", text.strip())
        rev = "\n\n".join(reversed(paras))
        return self._parse_fossils(
            _ollama(_DIG.format(reversed_text=rev[:3000], original_snippet=text[:1000]), _SYS, self.model),
            path.stem)

    def excavate_all(self) -> list[Discovery]:
        """Dig in ALL papers, find fossils in each."""
        all_d: list[Discovery] = []
        for p in self._papers():
            fossils = self._dig_paper(p)
            for f in fossils: self._log(f.to_dict())
            all_d.extend(fossils)
        return all_d

    def breed_fossils(self, fossil_a: Discovery, fossil_b: Discovery) -> FossilBreed:
        """Two fossils from different papers mate = new Discovery."""
        resp = _ollama(_BREED.format(paper_a=fossil_a.paper_id, fossil_a=fossil_a.essence,
                                     paper_b=fossil_b.paper_id, fossil_b=fossil_b.essence),
                       _SYS, self.model, temp=1.0) or ""
        essenz = emergent = ""
        for line in resp.split("\n"):
            up = line.strip().upper()
            if up.startswith("ESSENZ:"): essenz = line.split(":", 1)[1].strip()
            elif up.startswith("EMERGENT:"): emergent = line.split(":", 1)[1].strip()
        breed = FossilBreed(fossil_a=fossil_a.essence, paper_a=fossil_a.paper_id,
                            fossil_b=fossil_b.essence, paper_b=fossil_b.paper_id,
                            child_essence=essenz or "(Paarung gescheitert)",
                            emergent=emergent or "(kein Emergentes)",
                            depth=(fossil_a.depth + fossil_b.depth) / 2,
                            born_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        self._log({"breed": breed.to_dict()})
        return breed

    def _breed_deepest(self, discoveries: list[Discovery]) -> list[FossilBreed]:
        """Breed the deepest fossil from each paper with all others."""
        by_paper: dict[str, Discovery] = {}
        for d in sorted(discoveries, key=lambda x: -x.depth):
            if d.paper_id not in by_paper: by_paper[d.paper_id] = d
        breeds: list[FossilBreed] = []
        pids = list(by_paper.keys())
        for i, pa in enumerate(pids):
            for pb in pids[i + 1:]:
                breeds.append(self.breed_fossils(by_paper[pa], by_paper[pb]))
        return breeds

    def deepest_find(self) -> Discovery | None:
        """The fossil buried deepest across all papers."""
        all_d = self.excavate_all()
        return max(all_d, key=lambda d: d.depth) if all_d else None

    def full_dig(self) -> ArchaeologyResult:
        """Excavate all papers AND breed deepest fossils across them."""
        discoveries = self.excavate_all()
        breeds = self._breed_deepest(discoveries) if discoveries else []
        return ArchaeologyResult(discoveries=discoveries, breeds=breeds,
                                 papers_scanned=len(self._papers()),
                                 deepest_depth=max((d.depth for d in discoveries), default=0),
                                 model=self.model)

    def autonomous_dig(self, interval: int = 600):
        """Daemon: continuously excavate and breed."""
        print(f"Wissens-Archaeologie Daemon ({interval}s, {self._dir})\n")
        while True:
            try:
                result = self.full_dig()
                print(result); print(f"\n  Naechste Grabung in {interval}s...\n")
            except KeyboardInterrupt:
                print("\nDaemon gestoppt."); break
            except Exception as e:
                print(f"  Fehler: {e}")
            time.sleep(interval)

    def status(self) -> str:
        logged = self._read_log()
        fossils = [e for e in logged if "paper_id" in e]
        breeds = [e["breed"] for e in logged if "breed" in e]
        lines = [f"═══ WISSENS-ARCHAEOLOGIE ═══\n  Papers: {len(self._papers())} | "
                 f"Fossilien: {len(fossils)} | Kreuzungen: {len(breeds)} | "
                 f"Modell: {self.model or '(kein Ollama)'}"]
        for f in sorted(fossils, key=lambda f: -f.get("depth", 0))[:3]:
            lines.append(f"  [{f.get('depth','?')}] {f.get('essence','?')[:60]} ({f.get('paper_id','?')})")
        for b in breeds[-3:]:
            lines.append(f"  {b.get('paper_a','?')} × {b.get('paper_b','?')} → {b.get('child_essence','?')[:50]}")
        return "\n".join(lines)

    def _log(self, data: dict):
        with open(self._state, "a") as f: f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _read_log(self) -> list[dict]:
        if not self._state.exists(): return []
        out = []
        for line in self._state.read_text().strip().split("\n"):
            if line.strip():
                try: out.append(json.loads(line))
                except Exception: pass
        return out

# ── Convenience ──────────────────────────────────────────────────────────
def dig_and_breed(papers_dir: str = "") -> list[Discovery]:
    """One-shot: excavate all papers, breed deepest fossils."""
    return WissensArchaeologie(papers_dir=papers_dir).excavate_all()

def what_was_always_there(text: str) -> str:
    """Quick one-shot: find the hidden thing in any text."""
    resp = _ollama(f"Was war in diesem Text IMMER da aber NIE gesehen? 1 Satz.\nTEXT: {text[:3000]}", _SYS)
    return resp.strip().split("\n")[0] if resp else "(kein Modell verfuegbar)"

# ── CLI ──────────────────────────────────────────────────────────────────
def main(args: list[str] | None = None):
    """CLI: void wissens-archaeologie [--dig|--daemon|--deepest]"""
    if args is None: args = sys.argv[1:]
    if args and args[0] in ("--help", "-h"):
        print("void wissens-archaeologie — ARCHAEOLOGE × EVOLUTION\n"
              "  (kein Arg)    Status | --dig  Ausgraben + Kreuzen\n"
              "  --deepest     Tiefstes Fossil | --daemon [S]  Autonome Grabung"); return
    pdir, rest = "", []
    for a in args:
        if Path(a).is_dir(): pdir = a
        else: rest.append(a)
    wa = WissensArchaeologie(papers_dir=pdir)
    if not rest: print(wa.status()); return
    cmd = rest[0]
    if cmd == "--dig": print(wa.full_dig())
    elif cmd == "--deepest":
        d = wa.deepest_find()
        print(f"Tiefstes Fossil: {d}" if d else "Keine Fossilien gefunden.")
    elif cmd == "--daemon":
        iv = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 600
        wa.autonomous_dig(interval=iv)
    else: print(wa.status())

if __name__ == "__main__":
    main()
