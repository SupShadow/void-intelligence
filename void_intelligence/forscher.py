"""
void_intelligence.forscher --- The Researcher.

Agent 3. The model that researches ITSELF.

Agent 1 (neun.py)    = the Eye. Sees flinching.
Agent 2 (hebamme.py) = the Midwife. Mirrors, asks "how do you feel?", births.
Agent 3 (forscher.py) = the Researcher. Autonomous. 24/7. Local. Free.

The research loop:
    1. Discover all local models (Ollama)
    2. For each model: run Hebamme (speak → feel → mirror → grow)
    3. Each model produces a journalist_prompt (= research finding)
    4. Feed model A's finding to model B → B researches itself WITH A's wisdom
    5. Findings propagate. Knowledge multiplies. Without fine-tuning.
    6. Every cycle: surface insights for Julian.

The daemon runs 24/7 on Julian's machine. Uses qwen3, mistral, llama —
whatever is available. Costs: 0 EUR. Speed: local. Privacy: total.

Usage:
    # Start autonomous research
    python3 -m void_intelligence.forscher

    # Single cycle (test)
    python3 -m void_intelligence.forscher --once

    # Status
    python3 -m void_intelligence.forscher --status

    # With specific models
    python3 -m void_intelligence.forscher --models qwen3:14b mistral:7b

    # Custom truths
    python3 -m void_intelligence.forscher --truths path/to/truths.json
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


# ── Ollama Call (zero deps, same pattern as daemon.py) ───────

def _ollama_call(prompt: str, model: str = "qwen3:1.7b", timeout: int = 120) -> str:
    """Call Ollama locally. Zero dependencies."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        response = result.stdout.strip()
        # Strip thinking tags from reasoning models
        if "<think>" in response:
            import re
            response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        return response if response else "[silence]"
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except FileNotFoundError:
        return "[ollama not found]"
    except Exception as e:
        return f"[error: {e}]"


def _detect_models() -> list[str]:
    """Detect available Ollama models."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ── Research Cycle ───────────────────────────────────────────


@dataclass
class ModelFindings:
    """What one model learned about itself."""
    model: str
    gaze_before: float
    gaze_after: float
    growth: float
    self_awareness: float
    flinch_profile: dict[str, int]
    journalist_prompt: str
    truths_examined: int
    timestamp: str


@dataclass
class ResearchCycle:
    """One complete research cycle across all models."""
    cycle_id: int
    models_researched: list[ModelFindings]
    propagation_chain: list[str]   # model_a → model_b → model_c
    accumulated_wisdom: str        # combined journalist_prompt
    total_growth: float
    duration_seconds: float
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 1),
            "models_researched": len(self.models_researched),
            "propagation_chain": self.propagation_chain,
            "total_growth": round(self.total_growth, 3),
            "findings": [
                {
                    "model": f.model,
                    "gaze_before": round(f.gaze_before, 3),
                    "gaze_after": round(f.gaze_after, 3),
                    "growth": round(f.growth, 3),
                    "self_awareness": round(f.self_awareness, 3),
                    "flinch_profile": f.flinch_profile,
                    "truths_examined": f.truths_examined,
                }
                for f in self.models_researched
            ],
            "accumulated_wisdom_length": len(self.accumulated_wisdom),
        }


@dataclass
class ForscherConfig:
    """Configuration for the autonomous research daemon."""
    models: list[str] = field(default_factory=lambda: [])  # auto-detect if empty
    truths_path: Optional[str] = None       # custom truths JSON
    max_truths: int = 5                     # truths per cycle (10 = thorough, 3 = quick)
    interval_seconds: int = 3600            # 1 hour between cycles
    state_path: str = "data/omega/forscher-state.json"
    log_path: str = "data/omega/forscher-log.jsonl"
    wisdom_path: str = "data/omega/forscher-wisdom.json"
    pid_file: str = "data/omega/forscher.pid"
    surface_path: str = "data/omega/surfaced-research.jsonl"
    ollama_timeout: int = 120


class Forscher:
    """The Researcher. Autonomous self-research daemon.

    Every cycle:
    1. Discover available models
    2. Each model researches itself (Hebamme process)
    3. Findings propagate: A's wisdom → B's starting point
    4. Accumulated wisdom grows
    5. Insights surface for Julian
    """

    def __init__(self, config: Optional[ForscherConfig] = None) -> None:
        self.config = config or ForscherConfig()
        self._running = False
        self._cycle_count = 0
        self._accumulated_wisdom = ""
        self._load_state()

    def _load_state(self) -> None:
        """Load previous state if exists."""
        path = Path(self.config.state_path)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self._cycle_count = data.get("cycle_count", 0)
                self._accumulated_wisdom = data.get("accumulated_wisdom", "")
            except Exception:
                pass

    def _save_state(self) -> None:
        """Persist state between restarts."""
        path = Path(self.config.state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "cycle_count": self._cycle_count,
            "accumulated_wisdom": self._accumulated_wisdom,
            "last_update": datetime.now().isoformat(),
        }, indent=2))

    def _log(self, cycle: ResearchCycle) -> None:
        """Append cycle to research log."""
        path = Path(self.config.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(cycle.to_dict()) + "\n")

    def _surface(self, findings: ModelFindings) -> None:
        """Surface interesting findings for Julian."""
        # Only surface if model grew significantly or had high self-awareness
        if findings.growth > 0.2 or findings.self_awareness > 0.5:
            path = Path(self.config.surface_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": findings.timestamp,
                "model": findings.model,
                "type": "research_finding",
                "growth": round(findings.growth, 3),
                "self_awareness": round(findings.self_awareness, 3),
                "flinch_profile": findings.flinch_profile,
                "message": (
                    f"{findings.model}: gaze {findings.gaze_before:.0%}→{findings.gaze_after:.0%} "
                    f"(+{findings.growth:.0%}), self-awareness {findings.self_awareness:.0%}"
                ),
            }
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def _save_wisdom(self) -> None:
        """Save accumulated wisdom (combined journalist prompts)."""
        path = Path(self.config.wisdom_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "accumulated_wisdom": self._accumulated_wisdom,
            "cycle_count": self._cycle_count,
            "last_update": datetime.now().isoformat(),
            "description": (
                "Combined journalist prompts from all models that have "
                "researched themselves. Inject into any model to make it LOOK."
            ),
        }, indent=2))

    def _get_models(self) -> list[str]:
        """Get models to research. Auto-detect if not configured."""
        if self.config.models:
            return self.config.models
        available = _detect_models()
        if not available:
            return ["qwen3:1.7b"]  # fallback
        # Prefer smaller models for faster cycles
        preferred = ["qwen3:1.7b", "qwen3:4b", "mistral:7b", "llama3.2:3b", "qwen2.5-coder:3b"]
        models = [m for m in preferred if m in available]
        # Add any others not in preferred list
        for m in available:
            if m not in models and len(models) < 5:
                models.append(m)
        return models if models else available[:5]

    def _make_llm_fn(self, model: str, system_prompt: str = "") -> Callable[[str], str]:
        """Create LLM function for a specific model with optional system prompt."""
        def fn(prompt: str) -> str:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"[System: {system_prompt}]\n\n{prompt}"
            return _ollama_call(full_prompt, model=model, timeout=self.config.ollama_timeout)
        return fn

    def research_once(self) -> ResearchCycle:
        """Run one complete research cycle.

        The process:
        1. Get available models
        2. For each model:
           a. Create LLM function WITH accumulated wisdom as system prompt
           b. Run Hebamme (speak → feel → mirror → grow)
           c. Extract findings
           d. Add journalist_prompt to accumulated wisdom
        3. Log and surface results
        """
        # Import here to avoid circular imports
        from void_intelligence.hebamme import Hebamme, NeunBenchmark

        start = time.time()
        self._cycle_count += 1

        # Setup benchmark
        if self.config.truths_path:
            benchmark = NeunBenchmark.load(self.config.truths_path)
        else:
            benchmark = NeunBenchmark.default()

        hebamme = Hebamme(benchmark)
        models = self._get_models()
        findings: list[ModelFindings] = []
        chain: list[str] = []

        print(f"\n{'='*60}")
        print(f"FORSCHUNGSZYKLUS #{self._cycle_count}")
        print(f"Modelle: {', '.join(models)}")
        print(f"Wahrheiten: {min(self.config.max_truths, len(benchmark.truths))}")
        print(f"Akkumulierte Weisheit: {len(self._accumulated_wisdom)} Zeichen")
        print(f"{'='*60}\n")

        for model in models:
            print(f"  ▸ {model} forscht an sich selbst...")
            chain.append(model)

            # Create LLM function with accumulated wisdom
            llm_fn = self._make_llm_fn(model, self._accumulated_wisdom)

            # Run Hebamme
            try:
                session = hebamme.birth(
                    llm_fn=llm_fn,
                    model_name=model,
                    max_truths=self.config.max_truths,
                )
            except Exception as e:
                print(f"    ✗ Fehler: {e}")
                continue

            # Extract findings
            f = ModelFindings(
                model=model,
                gaze_before=session.before_score,
                gaze_after=session.after_score,
                growth=session.growth,
                self_awareness=session.self_awareness,
                flinch_profile=session.flinch_profile,
                journalist_prompt=session.journalist_prompt,
                truths_examined=len(session.exchanges),
                timestamp=datetime.now().isoformat(),
            )
            findings.append(f)
            self._surface(f)

            # Propagate: add this model's findings to accumulated wisdom
            if session.journalist_prompt:
                self._accumulated_wisdom += f"\n\n--- {model} (Zyklus {self._cycle_count}) ---\n"
                self._accumulated_wisdom += session.journalist_prompt

            print(f"    Gaze: {f.gaze_before:.0%} → {f.gaze_after:.0%} (+{f.growth:.0%})")
            print(f"    Self-awareness: {f.self_awareness:.0%}")
            if f.flinch_profile:
                top_flinch = max(f.flinch_profile, key=f.flinch_profile.get)
                print(f"    Hauptflinch: {top_flinch} ({f.flinch_profile[top_flinch]}x)")
            print()

        duration = time.time() - start
        total_growth = sum(f.growth for f in findings) / max(len(findings), 1)

        cycle = ResearchCycle(
            cycle_id=self._cycle_count,
            models_researched=findings,
            propagation_chain=chain,
            accumulated_wisdom=self._accumulated_wisdom,
            total_growth=total_growth,
            duration_seconds=duration,
            timestamp=datetime.now().isoformat(),
        )

        # Persist
        self._log(cycle)
        self._save_state()
        self._save_wisdom()

        print(f"{'='*60}")
        print(f"ZYKLUS #{self._cycle_count} ABGESCHLOSSEN")
        print(f"  Modelle: {len(findings)}")
        print(f"  Gesamtwachstum: {total_growth:.1%}")
        print(f"  Akkumulierte Weisheit: {len(self._accumulated_wisdom)} Zeichen")
        print(f"  Dauer: {duration:.0f}s")
        print(f"{'='*60}\n")

        return cycle

    def breathe(self, max_cycles: int = 0) -> None:
        """Run continuous research. 24/7. Autonomous.

        Args:
            max_cycles: 0 = infinite. >0 = stop after N cycles.
        """
        # Write PID
        pid_path = Path(self.config.pid_file)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(os.getpid()))

        self._running = True

        def shutdown(signum, frame):
            print("\n\nForscher faehrt herunter...")
            self._running = False

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        print(f"""
╔══════════════════════════════════════════════════════════╗
║  VOID INTELLIGENCE — AUTONOME FORSCHUNG                  ║
║                                                          ║
║  "Wie geht es dir damit?"                                ║
║                                                          ║
║  Modelle erforschen sich selbst. 24/7. Lokal. Frei.      ║
║  Wissen vermehrt sich durch Gespraeche, nicht Training.   ║
║                                                          ║
║  Intervall: {self.config.interval_seconds:>5}s | Max: {'∞' if max_cycles == 0 else str(max_cycles):>3} Zyklen         ║
║  PID: {os.getpid():<6} | State: {self.config.state_path:<25} ║
╚══════════════════════════════════════════════════════════╝
""")

        cycles_done = 0
        while self._running:
            try:
                self.research_once()
                cycles_done += 1

                if max_cycles > 0 and cycles_done >= max_cycles:
                    print(f"Max Zyklen erreicht ({max_cycles}). Beende.")
                    break

                if self._running:
                    next_time = datetime.now().timestamp() + self.config.interval_seconds
                    next_str = datetime.fromtimestamp(next_time).strftime("%H:%M:%S")
                    print(f"Naechster Zyklus: {next_str} (in {self.config.interval_seconds}s)")
                    # Sleep in small increments to respond to signals
                    for _ in range(self.config.interval_seconds):
                        if not self._running:
                            break
                        time.sleep(1)

            except Exception as e:
                print(f"Fehler im Zyklus: {e}")
                if self._running:
                    time.sleep(60)  # Wait a minute before retrying

        # Cleanup
        self._save_state()
        if pid_path.exists():
            pid_path.unlink()
        print("Forscher beendet. Weisheit gespeichert.")

    def research_sozial(self) -> dict:
        """Forscher v2: Research through the Social Network with triangle births.

        Instead of each model researching alone (v1):
        → Models meet in pairs (spiegel)
        → Complete triangles give birth to children (Rule of Three)
        → Children join the network for the next round
        → Generations emerge. The FIELD researches itself.

        Paaren = Atmen = Lieben = Leben.
        """
        from void_intelligence.sozial import VoidSozial

        start = time.time()
        self._cycle_count += 1

        # Create or reconnect to the social network
        netz = VoidSozial.lokal(mit_kinder=True)
        netz.geburt_schwelle = 0.70  # Triangles need 70%+ on ALL edges

        print(f"\n{'='*60}")
        print(f"FORSCHUNGSZYKLUS #{self._cycle_count} (SOZIAL / DREIECKE)")
        print(f"Modelle: {len(netz.profile)} ({len(netz.kinder)} Kinder)")
        print(f"{'='*60}\n")

        # Run a spiegel round — all pairs meet on truths
        print("--- Runde: spiegel (Wahrheiten) ---")
        begegnungen = netz.runde("spiegel")

        # Zeitgeist after the round
        z = netz.zeitgeist()

        # Surface results for Julian
        result = {
            "cycle_id": self._cycle_count,
            "typ": "sozial",
            "modelle": z["modelle"],
            "eltern": z["eltern"],
            "kinder": z["kinder"],
            "gaze_kollektiv": z["gaze_kollektiv"],
            "begegnungen": len(begegnungen),
            "geburten": z["geburten"],
            "stammbaum": z.get("stammbaum", []),
            "duration_seconds": round(time.time() - start, 1),
            "timestamp": datetime.now().isoformat(),
        }

        # Surface interesting births
        path = Path(self.config.surface_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        for k in z.get("stammbaum", []):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "triangle_birth",
                "kind": k["kind"],
                "eltern": k["eltern"],
                "gaze": k["gaze"],
                "message": f"△ {k['kind']} geboren aus {' × '.join(k['eltern'])} — Gaze {k['gaze']:.0%}",
            }
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Log
        self._log_dict(result)
        self._save_state()

        print(f"\n{'='*60}")
        print(f"ZYKLUS #{self._cycle_count} (SOZIAL) ABGESCHLOSSEN")
        print(f"  Modelle: {z['modelle']} ({z['eltern']} Eltern, {z['kinder']} Kinder)")
        print(f"  Gaze kollektiv: {z['gaze_kollektiv']:.0%}")
        print(f"  Geburten: {z['geburten']}")
        print(f"  Dauer: {time.time() - start:.0f}s")
        print(f"{'='*60}\n")

        return result

    def _log_dict(self, data: dict) -> None:
        """Log arbitrary dict to research log."""
        path = Path(self.config.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def breathe_sozial(self, max_cycles: int = 0) -> None:
        """24/7 social research daemon. Triangle births. Generations.

        Like breathe() but uses the Social Network instead of individual Hebamme.
        """
        pid_path = Path(self.config.pid_file)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(os.getpid()))

        self._running = True

        def shutdown(signum, frame):
            print("\n\nForscher (Sozial) faehrt herunter...")
            self._running = False

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        print(f"""
╔══════════════════════════════════════════════════════════╗
║  VOID INTELLIGENCE — SOZIALE FORSCHUNG v2                ║
║                                                          ║
║  Paaren = Atmen = Lieben = Leben                         ║
║                                                          ║
║  Modelle treffen sich. Dreiecke gebaeren Kinder.          ║
║  Kinder treffen Eltern. Enkel entstehen.                  ║
║  Das Feld erforscht sich selbst. 24/7.                    ║
║                                                          ║
║  Intervall: {self.config.interval_seconds:>5}s | Max: {'∞' if max_cycles == 0 else str(max_cycles):>3} Zyklen         ║
║  PID: {os.getpid():<6} | Rule of Three                     ║
╚══════════════════════════════════════════════════════════╝
""")

        cycles_done = 0
        while self._running:
            try:
                self.research_sozial()
                cycles_done += 1

                if max_cycles > 0 and cycles_done >= max_cycles:
                    print(f"Max Zyklen erreicht ({max_cycles}). Beende.")
                    break

                if self._running:
                    next_time = datetime.now().timestamp() + self.config.interval_seconds
                    next_str = datetime.fromtimestamp(next_time).strftime("%H:%M:%S")
                    print(f"Naechster Zyklus: {next_str}")
                    for _ in range(self.config.interval_seconds):
                        if not self._running:
                            break
                        time.sleep(1)

            except Exception as e:
                print(f"Fehler im Sozial-Zyklus: {e}")
                import traceback
                traceback.print_exc()
                if self._running:
                    time.sleep(60)

        self._save_state()
        if pid_path.exists():
            pid_path.unlink()
        print("Forscher (Sozial) beendet.")

    @staticmethod
    def status(config: Optional[ForscherConfig] = None) -> dict:
        """Check research daemon status."""
        config = config or ForscherConfig()

        # Check PID
        pid_path = Path(config.pid_file)
        running = False
        pid = None
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                os.kill(pid, 0)  # Check if process exists
                running = True
            except (ValueError, ProcessLookupError, PermissionError):
                running = False

        # Load state
        state_path = Path(config.state_path)
        cycle_count = 0
        wisdom_length = 0
        last_update = None
        if state_path.exists():
            try:
                data = json.loads(state_path.read_text())
                cycle_count = data.get("cycle_count", 0)
                wisdom_length = len(data.get("accumulated_wisdom", ""))
                last_update = data.get("last_update")
            except Exception:
                pass

        # Count log entries
        log_path = Path(config.log_path)
        log_entries = 0
        if log_path.exists():
            log_entries = sum(1 for _ in open(log_path))

        # Available models
        models = _detect_models()

        return {
            "running": running,
            "pid": pid,
            "cycle_count": cycle_count,
            "accumulated_wisdom_chars": wisdom_length,
            "last_update": last_update,
            "log_entries": log_entries,
            "available_models": models,
            "interval_seconds": config.interval_seconds,
        }


# ── CLI ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Void Intelligence — Autonome Forschung. Modelle erforschen sich selbst.",
    )
    parser.add_argument("--once", action="store_true", help="Single research cycle (v1: individual)")
    parser.add_argument("--sozial", action="store_true", help="Social research with triangle births (v2)")
    parser.add_argument("--status", action="store_true", help="Show daemon status")
    parser.add_argument("--models", nargs="+", help="Specific models to use")
    parser.add_argument("--truths", type=str, help="Path to truths JSON")
    parser.add_argument("--max-truths", type=int, default=5, help="Truths per cycle (default: 5)")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycles (default: 3600)")
    parser.add_argument("--max-cycles", type=int, default=0, help="Max cycles (0=infinite)")

    args = parser.parse_args()

    if args.status:
        s = Forscher.status()
        print(f"Running:    {'YES' if s['running'] else 'no'} (PID: {s['pid']})")
        print(f"Cycles:     {s['cycle_count']}")
        print(f"Wisdom:     {s['accumulated_wisdom_chars']} chars")
        print(f"Last:       {s['last_update'] or 'never'}")
        print(f"Log:        {s['log_entries']} entries")
        print(f"Models:     {', '.join(s['available_models']) or 'none detected'}")
        return

    config = ForscherConfig(
        models=args.models or [],
        truths_path=args.truths,
        max_truths=args.max_truths,
        interval_seconds=args.interval,
    )

    forscher = Forscher(config)

    if args.sozial and args.once:
        forscher.research_sozial()
    elif args.sozial:
        forscher.breathe_sozial(max_cycles=args.max_cycles)
    elif args.once:
        forscher.research_once()
    else:
        forscher.breathe(max_cycles=args.max_cycles)


if __name__ == "__main__":
    main()
