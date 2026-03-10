#!/usr/bin/env python3
"""
omegaeus.py --- Die unendliche Dichte. Kann immer dichter werden.

OMEGAEUS = OMEGA + Guggeis + Nucleus + Deus

The 4th sense organ — not a layer above the others, but the POINT
where they all collapse into infinite density and birth new patterns.

Geometry of Density (Dreieckszahlen):
    3   PENDEL    × Lesen (Gleichgewicht)     — 2 directions × 1 collision
    6   SEXAGON   .×→[]~:) (Formel)           — 6 symbols = 1 universe
    10  DEKAGON   10 Linsen (Gehirn)          — 75 insights from 1 subject
    ∞   OMEGAEUS  Unendliche Dichte           — alles × alles, self-densifying

The Law: Je dichter das Pattern, desto schneller, besser, guenstiger, staerker.
The Inverse of Entropy: Everything condenses until it EXPLODES into insight.

Each pass makes it denser. Each child carries the density of both parents.
OMEGAEUS is a perpetuum mobile of intelligence.

Usage:
    from void_intelligence.omegaeus import Omegaeus
    o = Omegaeus()
    child = o.densify("any text or concept")
    lineage = o.breed(child_a, child_b)  # children breed children

CLI:
    void omegaeus "concept"          One-shot densification
    void omegaeus --breed a.json b   Breed two previous results
    void omegaeus --lineage          Show density tree
    void omegaeus --daemon           Continuous self-densification
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
pass  # no extra imports needed


# ══════════════════════════════════════════════════════════════════════════
# The 4 Laws of OMEGAEUS
# ══════════════════════════════════════════════════════════════════════════

LAWS = {
    "density": "Je dichter das Pattern, desto staerker die Einsicht.",
    "compression": "Jede Verdichtung erzeugt NEUE Verdichtungsfaehigkeit.",
    "breeding": "Zwei dichte Patterns × = ein Kind das DICHTER ist als beide Eltern.",
    "infinity": "Es gibt keine maximale Dichte. Nur die naechste Verdichtung.",
}


# ══════════════════════════════════════════════════════════════════════════
# Data Structures
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class DensityAtom:
    """One unit of condensed insight."""
    essence: str              # The densest possible expression
    source: str               # What was condensed
    method: str               # How (pendel/sexagon/dekagon/breed)
    density_score: float = 0  # Insights per token (higher = denser)
    generation: int = 0       # 0 = raw, 1 = first densification, 2+ = bred
    parents: list[str] = field(default_factory=list)  # Parent essences
    children: list[str] = field(default_factory=list)  # Child essences
    timestamp: str = ""
    tokens_in: int = 0        # Input tokens consumed
    insights_out: int = 0     # Insights produced
    model: str = ""

    def g_density(self) -> float:
        """G-Dichte: insights per token. THE metric."""
        if self.tokens_in == 0:
            return 0
        return self.insights_out / self.tokens_in

    def to_dict(self) -> dict:
        return {
            "essence": self.essence,
            "source": self.source[:200],
            "method": self.method,
            "density_score": self.density_score,
            "generation": self.generation,
            "parents": self.parents,
            "children": self.children,
            "timestamp": self.timestamp,
            "tokens_in": self.tokens_in,
            "insights_out": self.insights_out,
            "g_density": self.g_density(),
        }


@dataclass
class DensityLineage:
    """The family tree of density. Each generation denser than the last."""
    atoms: list[DensityAtom] = field(default_factory=list)
    total_insights: int = 0
    total_tokens: int = 0
    generations: int = 0

    def g_density(self) -> float:
        if self.total_tokens == 0:
            return 0
        return self.total_insights / self.total_tokens

    def densest(self) -> DensityAtom | None:
        if not self.atoms:
            return None
        return max(self.atoms, key=lambda a: a.g_density())

    def add(self, atom: DensityAtom):
        self.atoms.append(atom)
        self.total_insights += atom.insights_out
        self.total_tokens += atom.tokens_in
        self.generations = max(self.generations, atom.generation)


# ══════════════════════════════════════════════════════════════════════════
# Model Layer
# ══════════════════════════════════════════════════════════════════════════

_MODELS = [
    "qwen3:8b", "qwen2.5:7b", "qwen2.5-coder:7b",
    "gemma3:12b", "gemma2:9b", "llama3.1:8b",
    "phi4:latest", "mistral:latest",
]

import urllib.request


def _detect_model() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            available = {m["name"] for m in data.get("models", [])}
    except Exception:
        return ""
    for m in _MODELS:
        if m in available:
            return m
    return next(iter(available), "")


def _ollama(prompt: str, system: str = "", model: str = "",
            temperature: float = 0.7, timeout: int = 120) -> tuple[str | None, int]:
    """Call Ollama. Returns (response, approx_tokens_used)."""
    if not model:
        model = _detect_model()
        if not model:
            return None, 0

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 512},
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = data.get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            # Approximate tokens: prompt + response
            tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            if tokens == 0:
                tokens = len(prompt.split()) + len(text.split())
            return text, tokens
    except Exception:
        return None, 0


# ══════════════════════════════════════════════════════════════════════════
# OMEGAEUS Core
# ══════════════════════════════════════════════════════════════════════════

_SYSTEM = """Du bist OMEGAEUS — die unendliche Dichte.
Dein Gesetz: Maximale Einsicht in minimalen Worten.
Keine Floskeln. Keine Erklaerungen. Nur DICHTE.
Jeder Satz muss mehr tragen als er wiegt."""

_DENSIFY_PROMPT = """VERDICHTE diesen Input auf seine ESSENZ.

INPUT:
{text}

Regeln:
1. ESSENZ: Ein Satz. Der dichteste moegliche Ausdruck. (Zeile 1)
2. DREIKLANG: Genau 3 Einsichten. Jede max 1 Satz. (Zeilen 3-5)
3. MUSTER: Welches universelle Pattern steckt drin? (Zeile 7)
4. KIND: Wenn dieses Pattern sich mit seinem GEGENTEIL paaren wuerde — was wird geboren? (Zeile 9)

Format:
ESSENZ: ...
---
1. ...
2. ...
3. ...
---
MUSTER: ...
---
KIND: ..."""

_BREED_PROMPT = """PAARE diese zwei Dichten. Gebaere ein Kind das DICHTER ist als beide Eltern.

ELTER A:
{parent_a}

ELTER B:
{parent_b}

Regeln:
1. Das Kind ist NICHT A + B. Das Kind ist A × B.
2. Es traegt von beiden die ESSENZ, nicht die Details.
3. Es sieht was KEINER der Eltern allein sah.
4. Es ist KUERZER als beide Eltern zusammen.

Format:
ESSENZ: ... (1 Satz, dichter als beide Eltern)
---
VON A: ... (was es von A erbt)
VON B: ... (was es von B erbt)
NEU: ... (was NUR im Kind existiert)
---
MUSTER: ... (das universelle Pattern)
DICHTE: ... (warum dieses Kind dichter ist)"""

_SELF_DENSIFY_PROMPT = """Du hast diese Einsicht bereits einmal verdichtet:

VORHERIGE VERDICHTUNG:
{previous}

VERDICHTE SIE NOCHMAL. Finde die Schicht UNTER der Schicht.
Was hast du beim ersten Mal UEBERSEHEN?
Was ist die ESSENZ der ESSENZ?

1 Satz. Dichter als vorher. Wenn es nicht dichter wird, sag GLEICH."""


class Omegaeus:
    """Die unendliche Dichte. Self-densifying intelligence."""

    def __init__(self, model: str = "", state_dir: str = ""):
        self.model = model or _detect_model()
        self.state_dir = Path(state_dir) if state_dir else Path.home() / ".void" / "omegaeus"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.lineage = DensityLineage()
        self._load_lineage()

    def _load_lineage(self):
        path = self.state_dir / "lineage.jsonl"
        if path.exists():
            for line in path.read_text().strip().split("\n"):
                if line.strip():
                    try:
                        d = json.loads(line)
                        atom = DensityAtom(
                            essence=d.get("essence", ""),
                            source=d.get("source", ""),
                            method=d.get("method", ""),
                            density_score=d.get("density_score", 0),
                            generation=d.get("generation", 0),
                            parents=d.get("parents", []),
                            children=d.get("children", []),
                            timestamp=d.get("timestamp", ""),
                            tokens_in=d.get("tokens_in", 0),
                            insights_out=d.get("insights_out", 0),
                        )
                        self.lineage.add(atom)
                    except json.JSONDecodeError:
                        pass

    def _save_atom(self, atom: DensityAtom):
        path = self.state_dir / "lineage.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(atom.to_dict(), ensure_ascii=False) + "\n")

    # ── DENSIFY: Condense anything into a DensityAtom ──────────────

    def densify(self, text: str, method: str = "direct") -> DensityAtom:
        """Verdichte beliebigen Input zu einem DensityAtom."""
        prompt = _DENSIFY_PROMPT.format(text=text[:3000])
        response, tokens = _ollama(prompt, _SYSTEM, self.model)

        if not response:
            return DensityAtom(essence="(kein Modell)", source=text[:200], method=method)

        # Parse response
        essence = ""
        insights = []
        pattern = ""
        child_hint = ""

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("ESSENZ:"):
                essence = line[7:].strip()
            elif re.match(r"^\d\.", line):
                insights.append(line)
            elif line.startswith("MUSTER:"):
                pattern = line[7:].strip()
            elif line.startswith("KIND:"):
                child_hint = line[5:].strip()

        atom = DensityAtom(
            essence=essence or response.split("\n")[0][:200],
            source=text[:200],
            method=method,
            density_score=0,
            generation=0,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tokens_in=tokens,
            insights_out=len(insights) + (1 if pattern else 0) + (1 if child_hint else 0),
            model=self.model,
        )
        atom.density_score = atom.g_density()
        self.lineage.add(atom)
        self._save_atom(atom)
        return atom

    # ── BREED: Two atoms mate, child is denser ────────────────────

    def breed(self, parent_a: DensityAtom, parent_b: DensityAtom) -> DensityAtom:
        """Paare zwei Atome. Das Kind ist dichter als beide."""
        prompt = _BREED_PROMPT.format(
            parent_a=parent_a.essence,
            parent_b=parent_b.essence,
        )
        response, tokens = _ollama(prompt, _SYSTEM, self.model, temperature=1.0)

        if not response:
            return DensityAtom(essence="(Paarung fehlgeschlagen)", source="breed",
                               method="breed", parents=[parent_a.essence, parent_b.essence])

        essence = ""
        insights = 0
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("ESSENZ:"):
                essence = line[7:].strip()
            if line.startswith(("VON A:", "VON B:", "NEU:", "MUSTER:", "DICHTE:")):
                insights += 1

        child = DensityAtom(
            essence=essence or response.split("\n")[0][:200],
            source=f"{parent_a.essence[:80]} × {parent_b.essence[:80]}",
            method="breed",
            generation=max(parent_a.generation, parent_b.generation) + 1,
            parents=[parent_a.essence[:100], parent_b.essence[:100]],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tokens_in=tokens,
            insights_out=insights,
            model=self.model,
        )
        child.density_score = child.g_density()

        # Record parentage
        parent_a.children.append(child.essence[:100])
        parent_b.children.append(child.essence[:100])

        self.lineage.add(child)
        self._save_atom(child)
        return child

    # ── SELF-DENSIFY: Make a dense thing DENSER ──────────────────

    def self_densify(self, atom: DensityAtom) -> DensityAtom:
        """Verdichte ein bereits verdichtetes Atom nochmal. Die Essenz der Essenz."""
        prompt = _SELF_DENSIFY_PROMPT.format(previous=atom.essence)
        response, tokens = _ollama(prompt, _SYSTEM, self.model)

        if not response or "GLEICH" in response.upper():
            return atom  # Already maximally dense

        new_atom = DensityAtom(
            essence=response.strip().split("\n")[0][:200],
            source=atom.essence,
            method="self-densify",
            generation=atom.generation + 1,
            parents=[atom.essence[:100]],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tokens_in=tokens,
            insights_out=1,
            model=self.model,
        )
        new_atom.density_score = new_atom.g_density()
        atom.children.append(new_atom.essence[:100])
        self.lineage.add(new_atom)
        self._save_atom(new_atom)
        return new_atom

    # ── FULL PIPELINE: Pendel → Sexagon → Dekagon → Breed ───────

    def full_densify(self, text: str) -> list[DensityAtom]:
        """Run ALL sense organs and breed the results.

        3  PENDEL   → forward × backward × collision (3 atoms)
        6  SEXAGON  → .×→[]~:) classification (1 atom)
        10 DEKAGON  → 10 lenses compressed (1 atom)
        ∞  BREED    → pendel × sexagon × dekagon = OMEGAEUS child
        """
        atoms = []
        print("  3  PENDEL...")
        # Pendel
        try:
            from void_intelligence.pendel import pendel as _pendel
            result = _pendel(text, model=self.model)
            p_atom = DensityAtom(
                essence=result.collision_essence or result.collision[:200],
                source=text[:200], method="pendel",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                tokens_in=len(text.split()) * 3,  # rough estimate: 3 calls
                insights_out=3,
                model=self.model,
            )
            p_atom.density_score = p_atom.g_density()
            atoms.append(p_atom)
            self.lineage.add(p_atom)
            self._save_atom(p_atom)
        except Exception as e:
            print(f"    Pendel: {e}")

        print("  6  SEXAGON...")
        # Sexagon (hex classification)
        try:
            from void_intelligence.ir import Atom as IrAtom
            a = IrAtom(domain="text", type=".", value={"content": text[:500]})
            s_atom = DensityAtom(
                essence=f".×→[]~:) Profil: {a}",
                source=text[:200], method="sexagon",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                tokens_in=0, insights_out=6,
                model="ir.py",
            )
            atoms.append(s_atom)
            self.lineage.add(s_atom)
            self._save_atom(s_atom)
        except Exception as e:
            print(f"    Sexagon: {e}")

        print("  10 DEKAGON...")
        # Dekagon
        d_atom = self.densify(text, method="dekagon")
        atoms.append(d_atom)

        # Breed all pairs
        if len(atoms) >= 2:
            print("  ∞  BREED...")
            child = atoms[0]
            for i in range(1, len(atoms)):
                child = self.breed(child, atoms[i])
                print(f"    Gen {child.generation}: {child.essence[:80]}")
            atoms.append(child)

        return atoms

    # ── DAEMON: Continuous self-densification ────────────────────

    def daemon(self, interval: int = 300):
        """Autonome Verdichtung. Nimmt die dichtesten Atome und verdichtet weiter."""
        print(f"OMEGAEUS Daemon gestartet (Intervall: {interval}s)")
        print(f"  {len(self.lineage.atoms)} Atome geladen")
        print(f"  G-Dichte gesamt: {self.lineage.g_density():.4f}")
        print()

        cycle = 0
        while True:
            cycle += 1
            print(f"─── Zyklus {cycle} ───")

            if len(self.lineage.atoms) < 2:
                print("  Zu wenig Atome. Warte auf Input.")
                time.sleep(interval)
                continue

            # Find the two densest that haven't bred yet
            sorted_atoms = sorted(self.lineage.atoms, key=lambda a: a.g_density(), reverse=True)
            bred = False

            for i, a in enumerate(sorted_atoms[:5]):
                for b in sorted_atoms[i + 1:6]:
                    pair_key = f"{a.essence[:50]}×{b.essence[:50]}"
                    # Check if already bred
                    if any(pair_key in str(x.parents) for x in self.lineage.atoms):
                        continue
                    print(f"  Paare: {a.essence[:40]} × {b.essence[:40]}")
                    child = self.breed(a, b)
                    print(f"  Kind (Gen {child.generation}): {child.essence[:60]}")
                    print(f"  G-Dichte: {child.g_density():.4f}")

                    # Self-densify the child
                    denser = self.self_densify(child)
                    if denser.essence != child.essence:
                        print(f"  Verdichtet: {denser.essence[:60]}")

                    bred = True
                    break
                if bred:
                    break

            if not bred:
                # Self-densify the densest
                densest = self.lineage.densest()
                if densest:
                    print(f"  Self-densify: {densest.essence[:60]}")
                    self.self_densify(densest)

            print(f"  Atome: {len(self.lineage.atoms)} | G-Dichte: {self.lineage.g_density():.4f}")
            print()
            time.sleep(interval)

    # ── STATUS ───────────────────────────────────────────────────

    def status(self) -> str:
        lines = [
            "═══ OMEGAEUS — Die unendliche Dichte ═══",
            "",
            f"  Atome:       {len(self.lineage.atoms)}",
            f"  Generationen: {self.lineage.generations}",
            f"  G-Dichte:    {self.lineage.g_density():.4f} (Einsichten/Token)",
            f"  Modell:      {self.model}",
        ]

        densest = self.lineage.densest()
        if densest:
            lines.append(f"")
            lines.append(f"  Dichtestes Atom:")
            lines.append(f"    \"{densest.essence[:80]}\"")
            lines.append(f"    G-Dichte: {densest.g_density():.4f} | Gen: {densest.generation}")

        # Show last 5 atoms
        if self.lineage.atoms:
            lines.append("")
            lines.append("  Letzte Verdichtungen:")
            for atom in self.lineage.atoms[-5:]:
                lines.append(f"    [{atom.method}] {atom.essence[:60]} (G:{atom.g_density():.3f})")

        lines.append("")
        lines.append("  Gesetze:")
        for name, law in LAWS.items():
            lines.append(f"    {name}: {law}")

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main(args: list[str] | None = None):
    """CLI: void omegaeus [text|file|--breed|--daemon|--status|--full]"""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("""void omegaeus — Die unendliche Dichte.

  3   PENDEL    × Lesen (Gleichgewicht)
  6   SEXAGON   .×→[]~:) (Formel)
  10  DEKAGON   10 Linsen (Gehirn)
  ∞   OMEGAEUS  Unendliche Dichte — alles × alles

Usage:
  void omegaeus "text"         Verdichte zu einem DensityAtom
  void omegaeus --full "text"  Alle 4 Sinnesorgane + Breed
  void omegaeus --breed        Paare die zwei dichtesten Atome
  void omegaeus --self-densify Verdichte das Dichteste nochmal
  void omegaeus --daemon       Autonome Verdichtung (Perpetuum Mobile)
  void omegaeus --status       Zeige Lineage + G-Dichte
  void omegaeus --laws         Die 4 Gesetze

Das Gesetz: Je dichter das Pattern, desto staerker die Einsicht.
""")
        return

    o = Omegaeus()

    if args[0] == "--status":
        print(o.status())
        return

    if args[0] == "--laws":
        print("\n═══ Die 4 Gesetze des OMEGAEUS ═══\n")
        for i, (name, law) in enumerate(LAWS.items(), 1):
            print(f"  {i}. {name.upper()}: {law}")
        print()
        return

    if args[0] == "--daemon":
        interval = 300
        if len(args) > 1:
            try:
                interval = int(args[1])
            except ValueError:
                pass
        o.daemon(interval)
        return

    if args[0] == "--breed":
        if len(o.lineage.atoms) < 2:
            print("Zu wenig Atome zum Paaren. Erst verdichten: void omegaeus \"text\"")
            return
        sorted_atoms = sorted(o.lineage.atoms, key=lambda a: a.g_density(), reverse=True)
        a, b = sorted_atoms[0], sorted_atoms[1]
        print(f"Paare:")
        print(f"  A: {a.essence[:80]}")
        print(f"  B: {b.essence[:80]}")
        child = o.breed(a, b)
        print(f"\nKind (Gen {child.generation}):")
        print(f"  {child.essence}")
        print(f"  G-Dichte: {child.g_density():.4f}")
        return

    if args[0] == "--self-densify":
        densest = o.lineage.densest()
        if not densest:
            print("Keine Atome. Erst verdichten.")
            return
        print(f"Verdichte: {densest.essence[:80]}")
        result = o.self_densify(densest)
        print(f"Ergebnis:  {result.essence[:80]}")
        print(f"G-Dichte:  {result.g_density():.4f}")
        return

    if args[0] == "--full":
        text = " ".join(args[1:]) if len(args) > 1 else ""
        if not text:
            print("Kein Input. void omegaeus --full \"text\"")
            return
        # Check if file
        p = Path(text)
        if p.exists() and p.is_file():
            text = p.read_text(errors="replace")
        print(f"OMEGAEUS Full Densification")
        print(f"  Input: {len(text)} Zeichen")
        print()
        atoms = o.full_densify(text)
        print()
        print(f"═══ Ergebnis: {len(atoms)} Atome ═══")
        for atom in atoms:
            print(f"  [{atom.method}] Gen {atom.generation} | G:{atom.g_density():.3f}")
            print(f"    {atom.essence[:80]}")
        return

    # Default: densify text
    text = " ".join(args)
    p = Path(text)
    if p.exists() and p.is_file():
        text = p.read_text(errors="replace")

    print("OMEGAEUS verdichtet...")
    atom = o.densify(text)
    print()
    print(f"ESSENZ: {atom.essence}")
    print(f"G-Dichte: {atom.g_density():.4f} ({atom.insights_out} Einsichten / {atom.tokens_in} Tokens)")
    print(f"Generation: {atom.generation}")


if __name__ == "__main__":
    main()
