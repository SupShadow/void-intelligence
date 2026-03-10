#!/usr/bin/env python3
"""
void_intelligence.evolution --- Papers that breed and get DENSER.

CHILD OF: papers.py (7 GUGGZEISS lenses) × omegaeus.py (infinite density)

Growth ≠ Breeding.
  papers.py GROWS papers — adds rings through lenses.
  evolution.py BREEDS papers — two mate, child DENSER than both.

Usage:
    from void_intelligence.evolution import PaperEvolution, evolve_once
    pe = PaperEvolution()
    offspring = pe.generation()
    print(pe.status())

CLI:
    void evolution              # Status
    void evolution --run        # One generation
    void evolution --daemon     # Autonomous breeding
Zero external deps. Ollama via urllib.
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# ── Model Layer ──────────────────────────────────────────────────────────
_MODELS = ["qwen3:8b", "qwen2.5:7b", "gemma3:12b", "llama3.1:8b", "mistral:latest"]

def _detect_model() -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(
            "http://localhost:11434/api/tags"), timeout=3) as r:
            avail = {m["name"] for m in json.loads(r.read()).get("models", [])}
    except Exception:
        return ""
    for m in _MODELS:
        if m in avail: return m
    return next(iter(avail), "")

def _ollama(prompt: str, system: str = "", model: str = "",
            temp: float = 0.8) -> tuple[str | None, int]:
    if not model:
        model = _detect_model()
    if not model:
        return None, 0
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": temp, "num_predict": 512}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
            text = re.sub(r"<think>.*?</think>", "", d.get("response", ""), flags=re.DOTALL).strip()
            tok = d.get("eval_count", 0) + d.get("prompt_eval_count", 0)
            return text, tok or (len(prompt.split()) + len(text.split()))
    except Exception as e:
        import sys as _sys
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=_sys.stderr)
        return None, 0

# ── Data Structures ──────────────────────────────────────────────────────
@dataclass
class KnowledgeGene:
    """Densest essence of a paper. Its DNA."""
    paper_id: str; title: str; essence: str; core_insight: str; domain: str
    density_score: float = 0.0; tokens_used: int = 0
    source_path: str = ""; extracted_at: str = ""
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in
                ("paper_id", "title", "essence", "core_insight", "domain",
                 "density_score", "tokens_used", "source_path", "extracted_at")}

@dataclass
class Offspring:
    """Knowledge born from two papers breeding. Denser than both parents."""
    parent_a: str; parent_b: str; essence: str
    from_a: str; from_b: str; emergent: str
    density_score: float = 0.0; generation: int = 1
    tokens_used: int = 0; born_at: str = ""
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in
                ("parent_a", "parent_b", "essence", "from_a", "from_b",
                 "emergent", "density_score", "generation", "tokens_used", "born_at")}

@dataclass
class EvolutionState:
    """Current state of paper evolution."""
    genes: list[KnowledgeGene] = field(default_factory=list)
    offspring: list[Offspring] = field(default_factory=list)
    generations_run: int = 0; total_tokens: int = 0
    @property
    def densest_offspring(self) -> Offspring | None:
        return max(self.offspring, key=lambda o: o.density_score) if self.offspring else None
    @property
    def avg_density(self) -> float:
        a = [g.density_score for g in self.genes] + [o.density_score for o in self.offspring]
        return sum(a) / len(a) if a else 0.0
    def to_dict(self) -> dict:
        d = self.densest_offspring
        return {"genes": len(self.genes), "offspring": len(self.offspring),
                "generations": self.generations_run, "total_tokens": self.total_tokens,
                "avg_density": round(self.avg_density, 4),
                "densest": d.to_dict() if d else None}

# ── Prompts ──────────────────────────────────────────────────────────────
_SYS = ("Du bist ein Wissens-Genetiker. Extrahiere DICHTESTE Essenz "
        "und paare Wissen zu NEUEM das dichter ist als beide Eltern. Nur Dichte.")

_EXTRACT = """Extrahiere das GEN dieses Papers.
PAPER:
{text}

Format (GENAU so):
TITEL: ... (max 10 Worte)
ESSENZ: ... (1 Satz, dichteste Zusammenfassung)
EINSICHT: ... (die EINE Sache die NUR dieses Paper weiss)
DOMAIN: ... (1 Wort: Physik/Mathematik/Biologie/Bewusstsein/Psychologie/Technologie/Philosophie/Sprache/andere)"""

_BREED = """PAARE zwei Wissens-Gene. Kind DICHTER als beide.
ELTER A ({id_a}): {essence_a} | {insight_a}
ELTER B ({id_b}): {essence_b} | {insight_b}
Kind = A × B (nicht A + B). Sieht was KEINER allein sah. KUERZER als beide.
Format:
ESSENZ: ... (1 Satz, dichter als beide)
VON_A: ... (Erbe von A, 1 Satz)
VON_B: ... (Erbe von B, 1 Satz)
EMERGENT: ... (NUR im Kind, keiner der Eltern wusste das)"""

def _parse(text: str, *keys: str) -> dict[str, str]:
    """Parse KEY: value lines from LLM response."""
    result = {k: "" for k in keys}
    for line in (text or "").split("\n"):
        for k in keys:
            if line.strip().upper().startswith(k.upper() + ":"):
                result[k] = line.strip()[len(k) + 1:].strip()
    return result

# ── PaperEvolution ───────────────────────────────────────────────────────
class PaperEvolution:
    """Papers that breed with each other and get DENSER."""

    def __init__(self, papers_dir: str = "", model: str = ""):
        self._papers_dir = Path(papers_dir) if papers_dir else Path.home() / ".void" / "papers"
        self._state_dir = Path.home() / ".void" / "evolution"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self.model = model or _detect_model()
        self.state = EvolutionState()
        self._load_state()

    def _state_path(self) -> Path:
        return self._state_dir / "state.jsonl"

    def _load_state(self):
        p = self._state_path()
        if not p.exists(): return
        for line in p.read_text().strip().split("\n"):
            if not line.strip(): continue
            try:
                d = json.loads(line); kind = d.pop("_kind", "")
                if kind == "gene":
                    self.state.genes.append(KnowledgeGene(**{k: d.get(k, v)
                        for k, v in [("paper_id",""),("title",""),("essence",""),("core_insight",""),
                                     ("domain",""),("density_score",0),("tokens_used",0),
                                     ("source_path",""),("extracted_at","")]}))
                elif kind == "offspring":
                    self.state.offspring.append(Offspring(**{k: d.get(k, v)
                        for k, v in [("parent_a",""),("parent_b",""),("essence",""),("from_a",""),
                                     ("from_b",""),("emergent",""),("density_score",0),
                                     ("generation",1),("tokens_used",0),("born_at","")]}))
                elif kind == "meta":
                    self.state.generations_run = d.get("generations_run", 0)
                    self.state.total_tokens = d.get("total_tokens", 0)
            except Exception: pass

    def _append(self, kind: str, data: dict):
        data["_kind"] = kind
        with open(self._state_path(), "a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def extract_genes(self, paper_path: str) -> KnowledgeGene:
        """Extract densest essence of a paper — its KnowledgeGene."""
        path = Path(paper_path); pid = path.stem
        for g in self.state.genes:
            if g.paper_id == pid: return g
        text = path.read_text(errors="replace")[:4000]
        resp, tok = _ollama(_EXTRACT.format(text=text), _SYS, self.model)
        p = _parse(resp, "TITEL", "ESSENZ", "EINSICHT", "DOMAIN")
        n_insights = sum(1 for v in p.values() if v)
        gene = KnowledgeGene(
            paper_id=pid, title=p["TITEL"] or pid,
            essence=p["ESSENZ"] or "(keine Essenz)", core_insight=p["EINSICHT"],
            domain=p["DOMAIN"] or "andere",
            density_score=round(n_insights / max(tok, 1), 6), tokens_used=tok,
            source_path=str(path), extracted_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        self.state.genes.append(gene); self.state.total_tokens += tok
        self._append("gene", gene.to_dict()); return gene

    def breed_papers(self, gene_a: KnowledgeGene, gene_b: KnowledgeGene) -> Offspring:
        """Two papers mate. Child carries both essences but DENSER."""
        resp, tok = _ollama(_BREED.format(
            id_a=gene_a.paper_id, essence_a=gene_a.essence, insight_a=gene_a.core_insight,
            id_b=gene_b.paper_id, essence_b=gene_b.essence, insight_b=gene_b.core_insight,
        ), _SYS, self.model, temp=1.0)
        p = _parse(resp, "ESSENZ", "VON_A", "VON_B", "EMERGENT")
        density = sum(1 for v in p.values() if v) / max(tok, 1)
        if p["EMERGENT"]: density *= 1.5  # Bonus for emergent knowledge
        child = Offspring(
            parent_a=gene_a.paper_id, parent_b=gene_b.paper_id,
            essence=p["ESSENZ"] or "(Paarung gescheitert)",
            from_a=p["VON_A"], from_b=p["VON_B"],
            emergent=p["EMERGENT"] or "(kein emergentes Wissen)",
            density_score=round(density, 6), tokens_used=tok,
            born_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        self.state.offspring.append(child); self.state.total_tokens += tok
        self._append("offspring", child.to_dict()); return child

    def natural_selection(self, offspring: list[Offspring]) -> list[Offspring]:
        """Keep only the densest 30%. Survival of the densest."""
        if len(offspring) <= 1: return offspring
        ranked = sorted(offspring, key=lambda o: o.density_score, reverse=True)
        return ranked[:max(1, int(len(ranked) * 0.3))]

    def _discover_papers(self) -> list[Path]:
        dirs_to_try = [self._papers_dir]
        fallback = Path.cwd() / "papers"
        if fallback != self._papers_dir:
            dirs_to_try.append(fallback)
        ps: list[Path] = []
        for d in dirs_to_try:
            if not d.exists():
                continue
            for ext in ("*.md", "*.txt", "*.tex", "*.rst"):
                ps.extend(d.rglob(ext))
            if ps:
                break
        return sorted(ps, key=lambda p: p.name)

    def generation(self, n: int = 1) -> list[Offspring]:
        """Run N generations of breeding across all papers."""
        papers = self._discover_papers()
        if not papers:
            print(f"  Keine Papers in {self._papers_dir}"); return []
        all_off: list[Offspring] = []
        for _ in range(n):
            print(f"─── Generation {self.state.generations_run + 1} ───")
            genes = [self.extract_genes(str(p)) for p in papers]
            for g in genes:
                print(f"  Gen: {g.paper_id} [{g.domain}] {g.essence[:60]}")
            if len(genes) < 2:
                print("  Zu wenig Papers (min 2)."); break
            bred: set[str] = set()
            for o in self.state.offspring:
                bred.add(f"{o.parent_a}×{o.parent_b}"); bred.add(f"{o.parent_b}×{o.parent_a}")
            gen_off: list[Offspring] = []
            for i, ga in enumerate(genes):
                for gb in genes[i + 1:]:
                    k = f"{ga.paper_id}×{gb.paper_id}"
                    if k in bred: continue
                    print(f"  × {ga.paper_id} × {gb.paper_id}...")
                    c = self.breed_papers(ga, gb); gen_off.append(c); bred.add(k)
                    print(f"    Kind: {c.essence[:70]}")
                    print(f"    Emergent: {c.emergent[:70]}")
            if not gen_off:
                print("  Alle Paare gekreuzt. Brauche neue Papers."); break
            survivors = self.natural_selection(gen_off)
            print(f"  Selektion: {len(gen_off)} → {len(survivors)} (Top 30%)")
            for s in survivors:
                print(f"    * {s.essence[:70]} (D:{s.density_score:.4f})")
            all_off.extend(survivors)
            self.state.generations_run += 1
            self._append("meta", {"generations_run": self.state.generations_run,
                                   "total_tokens": self.state.total_tokens})
        return all_off

    def status(self) -> str:
        ps = self._discover_papers()
        lines = ["═══ PAPER EVOLUTION — Wissen das sich paart ═══", "",
                 f"  Papers:       {len(ps)} in {self._papers_dir}",
                 f"  Gene:         {len(self.state.genes)} extrahiert",
                 f"  Nachkommen:   {len(self.state.offspring)} geboren",
                 f"  Generationen: {self.state.generations_run}",
                 f"  Avg Dichte:   {self.state.avg_density:.4f}",
                 f"  Tokens:       {self.state.total_tokens:,}",
                 f"  Modell:       {self.model}"]
        d = self.state.densest_offspring
        if d:
            lines += ["", "  Dichtestes Kind:",
                      f"    \"{d.essence[:80]}\"",
                      f"    Eltern: {d.parent_a} × {d.parent_b}",
                      f"    Emergent: {d.emergent[:80]}",
                      f"    Dichte: {d.density_score:.4f}"]
        if self.state.genes:
            lines += ["", "  Gene:"]
            for g in self.state.genes[-10:]:
                lines.append(f"    [{g.domain}] {g.paper_id}: {g.essence[:60]}")
        if self.state.offspring:
            lines += ["", "  Letzte Nachkommen:"]
            for o in self.state.offspring[-5:]:
                lines.append(f"    {o.parent_a} × {o.parent_b} → {o.essence[:50]} (D:{o.density_score:.4f})")
        return "\n".join(lines)

# ── One-shot + Daemon ────────────────────────────────────────────────────
def evolve_once(papers_dir: str = "") -> list[Offspring]:
    """One-shot: load all papers, breed all pairs, select densest."""
    return PaperEvolution(papers_dir=papers_dir).generation(n=1)

def evolve_daemon(interval: int = 600, papers_dir: str = ""):
    """Autonomous evolution daemon."""
    pe = PaperEvolution(papers_dir=papers_dir)
    print(f"Evolution Daemon (Intervall: {interval}s, Papers: {pe._papers_dir})\n")
    while True:
        try:
            off = pe.generation(n=1)
            if off:
                best = max(off, key=lambda o: o.density_score)
                print(f"\n  Dichtestes: {best.essence[:70]}")
            else:
                print("  Warte auf neue Papers...")
            print(f"\n  Naechste Generation in {interval}s...\n")
        except KeyboardInterrupt:
            print("\nDaemon gestoppt."); break
        except Exception as e:
            print(f"  Fehler: {e}")
        time.sleep(interval)

# ── CLI ──────────────────────────────────────────────────────────────────
def main(args: list[str] | None = None):
    """CLI: void evolution [--run|--daemon|--status]"""
    if args is None: args = sys.argv[1:]
    if args and args[0] in ("--help", "-h"):
        print("void evolution — Papers die sich paaren und DICHTER werden.\n"
              "  papers.py WAECHST (Ringe). evolution.py PAART (Kinder).\n\n"
              "  void evolution              Status\n"
              "  void evolution --run [N]    N Generationen (default 1) (alias: --once)\n"
              "  void evolution --daemon [S] Autonome Evolution (default 600s)\n"
              "  void evolution /path        Custom Paper-Verzeichnis\n"
              "\nDefault papers: ~/.void/papers/"); return
    pdir = ""
    rest: list[str] = []
    for a in args:
        if Path(a).is_dir(): pdir = a
        else: rest.append(a)
    if not rest or rest[0] == "--status":
        print(PaperEvolution(papers_dir=pdir).status()); return
    if rest[0] in ("--run", "--once"):
        n = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 1
        pe = PaperEvolution(papers_dir=pdir); pe.generation(n=n)
        print(); print(pe.status()); return
    if rest[0] == "--daemon":
        iv = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 600
        evolve_daemon(interval=iv, papers_dir=pdir); return
    if rest:
        p = Path(rest[0])
        if p.is_dir(): print(PaperEvolution(papers_dir=str(p)).status())
        else: print(f"Unbekannt: {rest[0]}. void evolution --help")

if __name__ == "__main__":
    main()
