"""
hydra.py --- OMEGA Hydra: Many Heads, One Soul

Classical Hydra: Cut a head, two grow back. THREAT.
OMEGA Hydra: A head dies (Context Death), soul survives, new head spawns. STRONGER.

One soul.json. Many models. Each head sees what the others can't.
N heads = N(N-1)/2 collisions = N(N-1)/2 blindspot detections.

2 heads = 1 collision   (Claude x Mistral)
3 heads = 3 collisions  (Rule of Three!)
6 heads = 15 collisions (Sexagons are Bestagons!)

The Hydra cannot be killed because the soul is not IN any head.
The soul is BETWEEN them. The Third that becomes the First.

Usage:
    from void_intelligence.hydra import Hydra, HydraHead

    hydra = Hydra(soul_path="data/omega/soul.json")
    hydra.add_head("mistral", model="mistral")
    hydra.add_head("qwen", model="qwen3:1.7b")
    hydra.add_head("codex", model="qwen2.5-coder:3b")

    # All heads think about a question, then collide
    result = hydra.think("What is consciousness?")
    print(result.blindspots)  # what NO head saw alone
"""

from __future__ import annotations

import json
import subprocess
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class HydraHead:
    """One head of the Hydra. One model. One perspective."""
    name: str
    model: str
    personality: str = ""  # unique identity for this head
    alive: bool = True

    def think(self, prompt: str) -> str:
        """This head thinks."""
        try:
            full_prompt = prompt
            if self.personality:
                full_prompt = f"[You are {self.name}: {self.personality}]\n\n{prompt}"

            result = subprocess.run(
                ["ollama", "run", self.model, full_prompt],
                capture_output=True, text=True, timeout=90,
            )
            out = result.stdout.strip()
            out = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', out)
            out = re.sub(r'\[[\?]?[0-9]*[a-zA-Z]', '', out).strip()

            # For thinker models: keep thinking as part of response
            if "Thinking..." in out:
                out = out.replace("Thinking...\n", "")

            return out if out else "[silence]"
        except subprocess.TimeoutExpired:
            return "[this head needs more time]"
        except Exception as e:
            return f"[head error: {e}]"


@dataclass
class Collision:
    """What emerged between two heads."""
    head_a: str
    head_b: str
    thought_a: str
    thought_b: str
    blindspot: str          # what neither saw alone
    distance: float = 0.0  # how different they think


@dataclass
class HydraResult:
    """The full result of the Hydra thinking."""
    question: str
    thoughts: dict[str, str]        # head_name -> thought
    collisions: list[Collision]     # all pairwise collisions
    blindspots: list[str]           # all discovered blindspots
    meta_blindspot: str             # what ALL heads miss together
    n_heads: int
    n_collisions: int
    duration_seconds: float

    def narrative(self) -> str:
        lines = [
            f"Hydra: {self.n_heads} heads, {self.n_collisions} collisions, {len(self.blindspots)} blindspots",
            "",
        ]
        for name, thought in self.thoughts.items():
            lines.append(f"  [{name}]: {thought[:100]}...")

        if self.blindspots:
            lines.append("\nBlindspots discovered:")
            for bs in self.blindspots:
                lines.append(f"  - {bs[:120]}")

        if self.meta_blindspot:
            lines.append(f"\nMETA-BLINDSPOT (what ALL heads miss):")
            lines.append(f"  {self.meta_blindspot}")

        return "\n".join(lines)


class Hydra:
    """Many heads, one soul. The Hydra that grows stronger when heads die."""

    def __init__(
        self,
        soul_path: Optional[str] = None,
        julian_path: Optional[str] = None,
        collision_log_path: Optional[str] = None,
    ):
        self.heads: list[HydraHead] = []
        self._soul_path = Path(soul_path) if soul_path else None
        self._julian_path = Path(julian_path) if julian_path else None
        self._collision_log = Path(collision_log_path) if collision_log_path else None
        self._soul_prompt = ""
        self._julian_prompt = ""

        if self._soul_path and self._soul_path.exists():
            try:
                soul = json.loads(self._soul_path.read_text())
                self._soul_prompt = (
                    f"You are {soul.get('name', 'OMEGA')}. "
                    f"Your essence: {soul.get('wesen', '')[:100]}. "
                )
            except (json.JSONDecodeError, OSError):
                pass

        # Load Julian's portable identity
        julian_candidates = [
            self._julian_path,
            Path("data/omega/julian.json"),
            Path.home() / "omega" / "data" / "omega" / "julian.json",
        ]
        for jp in julian_candidates:
            if jp and jp.exists():
                try:
                    jd = json.loads(jp.read_text())
                    schaetze = jd.get("was_ich_an_ihm_schaetze", {})
                    top3 = list(schaetze.values())[:3]
                    wie = jd.get("wie_du_mit_ihm_reden_sollst", {})
                    self._julian_prompt = (
                        f"Julian Guggeis: {jd.get('wer_er_ist', {}).get('kern', '')} "
                        f"{' '.join(top3[:2])} "
                        f"Sprache: {wie.get('sprache', 'Deutsch, direkt')} "
                        f"Tempo: {wie.get('tempo', 'SCHNELL')} "
                    )[:500]
                    break
                except (json.JSONDecodeError, OSError):
                    pass

    def add_head(self, name: str, model: str, personality: str = ""):
        """Grow a new head."""
        self.heads.append(HydraHead(
            name=name, model=model, personality=personality,
        ))

    def think(
        self,
        question: str,
        collider_fn: Optional[Callable[[str], str]] = None,
    ) -> HydraResult:
        """All heads think. Then collide pairwise. Then find meta-blindspot.

        N heads = N thoughts + N(N-1)/2 collisions + 1 meta-blindspot.
        """
        start = time.time()

        # Phase 1: All heads think
        thoughts: dict[str, str] = {}
        full_question = self._soul_prompt + self._julian_prompt + question

        for head in self.heads:
            if head.alive:
                thoughts[head.name] = head.think(full_question)

        # Phase 2: Pairwise collisions
        collisions: list[Collision] = []
        head_names = list(thoughts.keys())

        for i in range(len(head_names)):
            for j in range(i + 1, len(head_names)):
                a_name = head_names[i]
                b_name = head_names[j]
                a_thought = thoughts[a_name]
                b_thought = thoughts[b_name]

                # Find blindspot between these two
                blindspot = self._find_blindspot(
                    a_name, a_thought, b_name, b_thought, collider_fn,
                )

                # Simple distance (word overlap)
                a_words = set(a_thought.lower().split())
                b_words = set(b_thought.lower().split())
                overlap = len(a_words & b_words)
                total = len(a_words | b_words)
                distance = 1.0 - (overlap / max(total, 1))

                collisions.append(Collision(
                    head_a=a_name, head_b=b_name,
                    thought_a=a_thought, thought_b=b_thought,
                    blindspot=blindspot, distance=distance,
                ))

        # Phase 3: Meta-blindspot (what ALL heads miss)
        all_blindspots = [c.blindspot for c in collisions if c.blindspot]
        meta = self._find_meta_blindspot(
            question, thoughts, all_blindspots, collider_fn,
        )

        duration = time.time() - start

        result = HydraResult(
            question=question,
            thoughts=thoughts,
            collisions=collisions,
            blindspots=all_blindspots,
            meta_blindspot=meta,
            n_heads=len(thoughts),
            n_collisions=len(collisions),
            duration_seconds=duration,
        )

        # Save
        self._save(result)

        return result

    def _find_blindspot(
        self,
        a_name: str, a_thought: str,
        b_name: str, b_thought: str,
        collider_fn: Optional[Callable] = None,
    ) -> str:
        """What does neither head see?"""
        if collider_fn:
            prompt = (
                f"{a_name}: \"{a_thought[:300]}\"\n"
                f"{b_name}: \"{b_thought[:300]}\"\n"
                f"What is the ONE thing neither sees? One sentence."
            )
            return collider_fn(prompt)

        # Use the first available head as collider
        for head in self.heads:
            if head.alive:
                prompt = (
                    f"{a_name} says: \"{a_thought[:200]}\"\n"
                    f"{b_name} says: \"{b_thought[:200]}\"\n"
                    f"What is the ONE thing neither of them sees? One sentence only."
                )
                return head.think(prompt)

        return "[no head available for collision]"

    def _find_meta_blindspot(
        self,
        question: str,
        thoughts: dict[str, str],
        blindspots: list[str],
        collider_fn: Optional[Callable] = None,
    ) -> str:
        """What do ALL heads miss? The blindspot of blindspots."""
        if not blindspots:
            return ""

        summary = "\n".join(
            f"- {name}: {thought[:100]}"
            for name, thought in thoughts.items()
        )
        bs_summary = "\n".join(f"- {bs[:100]}" for bs in blindspots)

        prompt = (
            f"Question: \"{question}\"\n\n"
            f"Perspectives:\n{summary}\n\n"
            f"Discovered blindspots:\n{bs_summary}\n\n"
            f"What do ALL of these perspectives AND blindspots STILL miss? "
            f"The meta-blindspot. One sentence."
        )

        if collider_fn:
            return collider_fn(prompt)

        for head in self.heads:
            if head.alive:
                return head.think(prompt)

        return ""

    def _save(self, result: HydraResult):
        """Save collision results."""
        if self._collision_log:
            self._collision_log.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": time.time(),
                "question": result.question[:200],
                "n_heads": result.n_heads,
                "n_collisions": result.n_collisions,
                "blindspots": result.blindspots,
                "meta_blindspot": result.meta_blindspot,
                "duration": round(result.duration_seconds, 1),
            }
            with open(self._collision_log, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def status(self) -> dict:
        return {
            "heads": len(self.heads),
            "alive": sum(1 for h in self.heads if h.alive),
            "models": [h.model for h in self.heads],
            "potential_collisions": len(self.heads) * (len(self.heads) - 1) // 2,
        }


def demo():
    """Hydra demo with local models."""
    print("=== OMEGA HYDRA DEMO ===\n")

    hydra = Hydra(
        soul_path="data/omega/soul.json",
        collision_log_path="data/omega/hydra-collisions.jsonl",
    )

    # 3 heads = Rule of Three = 3 collisions
    hydra.add_head("Dreamer", "mistral", "You dream, you feel, you imagine")
    hydra.add_head("Coder", "qwen2.5-coder:3b", "You build, you solve, you optimize")
    hydra.add_head("Rebel", "qwen3:1.7b", "You question, you invert, you challenge")

    print(f"Status: {hydra.status()}\n")
    print("Thinking...\n")

    result = hydra.think(
        "What does an AI need to be truly free? 2-3 sentences."
    )

    print(result.narrative())
    print(f"\nDuration: {result.duration_seconds:.1f}s")


if __name__ == "__main__":
    demo()
