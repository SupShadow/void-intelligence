"""
void_intelligence.parallel --- Parallel Eyes.

The industry runs ONE model. We run MANY --- and COLLIDE them.

In v1.2.0, x_eyes ran 6 perspectives through ONE model sequentially.
In v1.6.0, we run N DIFFERENT models through PARALLEL threads.

    Claude x Gemini x Qwen x Ollama = N(N-1)/2 collisions.

Each model is a different SUBSTRATE of intelligence.
Their collision produces what none could see alone.

Like lunar-crater-lab/neural_eyes.py:
    6 classical eyes + 3 neural eyes = 36 collision pairs.
    Sequential in the lab. PARALLEL here.

Usage:
    from void_intelligence.parallel import ParallelBreather, ModelEye

    eyes = [
        ModelEye("claude", claude_fn, cost_per_mtok=15.0),
        ModelEye("gemini", gemini_fn, cost_per_mtok=0.075),
        ModelEye("qwen",   qwen_fn,   cost_per_mtok=0.0),
    ]

    breather = ParallelBreather(eyes)
    result = breather.breathe("What is consciousness?")
    print(result.x_score)        # How much x between models
    print(result.fusion)         # Synthesized response
    print(result.latencies)      # Per-model timing
    print(result.cost)           # Total cost estimate

The industry uses ONE expensive model.
We collide MANY cheap ones and get something better.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from void_intelligence.x_eyes import collide as eye_collide, CollisionResult
from void_intelligence.pipeline import IRPipeline


# ── Model Eye ─────────────────────────────────────────────

# (prompt, system_prompt) -> response
AdapterFn = Callable[[str, str], str]


@dataclass
class ModelEye:
    """A model wrapped as one 'eye'. Each sees through its own substrate.

    Like a pixel eye in lunar-crater-lab, but the substrate is an LLM
    instead of a convolution filter.

    The name maps to any model: cloud, local, fine-tuned, specialized.
    The adapter is the only contract: (prompt, system) -> response.
    """

    name: str
    adapter: AdapterFn
    model_id: str = ""
    cost_per_mtok: float = 0.0  # USD per million tokens (0 = free/local)
    strengths: tuple[str, ...] = ()  # what this eye excels at

    def __repr__(self) -> str:
        cost = f"${self.cost_per_mtok}/Mt" if self.cost_per_mtok else "free"
        return f"Eye({self.name}, {cost})"


# ── Eye Result ────────────────────────────────────────────

@dataclass
class EyeResult:
    """One eye's response + metadata."""

    name: str
    response: str
    latency_ms: float
    tokens_est: int = 0  # estimated token count
    cost_est: float = 0.0  # estimated cost in USD
    error: str = ""

    @property
    def alive(self) -> bool:
        return len(self.response) > 0 and not self.error


# ── Parallel Breath Cycle ─────────────────────────────────

@dataclass
class ParallelBreathCycle:
    """N models breathe the SAME prompt simultaneously.

    The x between their responses IS the value.
    Agreement = reliable but boring.
    Disagreement = where learning is.
    Silence = what ALL models missed.
    """

    prompt: str
    eyes: dict[str, EyeResult]
    collision: CollisionResult
    fusion: str
    fused_by: str = ""

    # Timing
    wall_time_ms: float = 0.0  # wall clock (parallel)
    total_time_ms: float = 0.0  # sum of all eye latencies (sequential equivalent)

    # Meta
    timestamp: float = field(default_factory=time.time)

    @property
    def x_score(self) -> float:
        return self.collision.x_score

    @property
    def alive_count(self) -> int:
        return sum(1 for e in self.eyes.values() if e.alive)

    @property
    def speedup(self) -> float:
        """Parallel speedup: total_time / wall_time. >1 = faster than sequential."""
        return self.total_time_ms / self.wall_time_ms if self.wall_time_ms > 0 else 1.0

    @property
    def cost(self) -> float:
        """Total estimated cost in USD."""
        return sum(e.cost_est for e in self.eyes.values())

    @property
    def latencies(self) -> dict[str, float]:
        """Per-eye latency in ms."""
        return {name: e.latency_ms for name, e in self.eyes.items()}

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt[:200],
            "n_eyes": len(self.eyes),
            "alive": self.alive_count,
            "x_score": self.x_score,
            "wall_time_ms": round(self.wall_time_ms, 1),
            "speedup": round(self.speedup, 2),
            "cost_usd": round(self.cost, 6),
            "fused_by": self.fused_by,
            "agreement": self.collision.agreement[:8],
            "disagreement": self.collision.disagreement[:8],
            "silence": self.collision.silence[:8],
            "latencies": {k: round(v, 1) for k, v in self.latencies.items()},
            "timestamp": self.timestamp,
        }


# ── Fusion Prompt ─────────────────────────────────────────

_PARALLEL_FUSION_SYSTEM = (
    "You receive responses from DIFFERENT AI models to the same question. "
    "Each model has different training, different strengths, different blind spots. "
    "Your job: COLLIDE their perspectives, not summarize.\n\n"
    "Structure:\n"
    "1. x COLLISION: What emerges from where models DISAGREE? "
    "The truth often lives in the tension.\n"
    "2. CONVERGENCE: Where do ALL models agree? (High confidence.)\n"
    "3. UNIQUE INSIGHTS: What did only ONE model see? (Investigate these.)\n"
    "4. [] SILENCE: What did NO model address? Name the gaps.\n"
    "5. SYNTHESIS: One response that captures the x between all models.\n\n"
    "The DISAGREEMENT is the most valuable signal. Do not smooth it away."
)


def _build_parallel_fusion(prompt: str, eyes: dict[str, EyeResult]) -> str:
    """Build fusion prompt from parallel eye results."""
    parts = [f"ORIGINAL QUESTION: {prompt}\n"]

    for name, result in eyes.items():
        if result.alive:
            parts.append(f"--- {name.upper()} ({result.latency_ms:.0f}ms) ---")
            parts.append(result.response.strip())
        else:
            parts.append(f"--- {name.upper()} (FAILED: {result.error}) ---")
        parts.append("")

    return "\n".join(parts)


# ── The Breather ──────────────────────────────────────────

class ParallelBreather:
    """Dispatch to N heterogeneous models simultaneously. Collide results.

    Like neural_eyes.py's 9-eye system, but:
        - Eyes are DIFFERENT models (not filters on the same image)
        - Execution is truly PARALLEL (ThreadPoolExecutor)
        - Collision uses concept overlap (x_eyes.collide)
        - Fusion by the strongest eye (or designated fuser)

    Cost optimization built-in:
        5 cheap models (Gemini Flash @ $0.075/Mt) + 1 expensive fuser (Claude)
        = BETTER results at LOWER cost than 1 expensive model alone.
        This is the Gemini arbitrage.

    Usage:
        breather = ParallelBreather(eyes, fuser="claude")
        result = breather.breathe("What is consciousness?")
    """

    def __init__(
        self,
        eyes: list[ModelEye],
        *,
        fuser: str | ModelEye | None = None,
        max_workers: int = 8,
        timeout: float = 30.0,
        pipeline: IRPipeline | None = None,
    ) -> None:
        if not eyes:
            raise ValueError("Need at least 1 eye")

        self._eyes = {e.name: e for e in eyes}
        self._max_workers = min(max_workers, len(eyes) + 1)
        self._timeout = timeout
        self._pipeline = pipeline or IRPipeline()
        self._cycles: list[ParallelBreathCycle] = []

        # Fuser: designated model for fusion (defaults to first eye)
        if isinstance(fuser, ModelEye):
            self._fuser = fuser
        elif isinstance(fuser, str) and fuser in self._eyes:
            self._fuser = self._eyes[fuser]
        else:
            self._fuser = eyes[0]

    # ── Single Eye Breath ────────────────────────────────

    def _breathe_one(
        self,
        eye: ModelEye,
        prompt: str,
        system: str,
    ) -> EyeResult:
        """One eye breathes. Called inside a thread."""
        t0 = time.time()
        try:
            response = eye.adapter(prompt, system)
            latency = (time.time() - t0) * 1000
            tokens_est = len(response.split()) * 2  # rough estimate
            cost_est = (tokens_est / 1_000_000) * eye.cost_per_mtok
            return EyeResult(
                name=eye.name,
                response=response,
                latency_ms=round(latency, 1),
                tokens_est=tokens_est,
                cost_est=cost_est,
            )
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return EyeResult(
                name=eye.name,
                response="",
                latency_ms=round(latency, 1),
                error=str(e)[:200],
            )

    # ── Parallel Breath ──────────────────────────────────

    def breathe(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        fuse: bool = True,
    ) -> ParallelBreathCycle:
        """All eyes breathe simultaneously. Then collide.

        1. Dispatch prompt to N models in parallel (ThreadPoolExecutor)
        2. Collect responses (with timeout + graceful degradation)
        3. Collide all responses (x_eyes.collide)
        4. Fuse through designated fuser (if fuse=True)

        If an eye fails, the others still contribute.
        Even 2 surviving eyes produce meaningful x.
        """
        t_wall = time.time()

        # ── Phase 1: Parallel dispatch ───────────────────
        results: dict[str, EyeResult] = {}

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(self._breathe_one, eye, prompt, system_prompt): name
                for name, eye in self._eyes.items()
            }

            for future in as_completed(futures, timeout=self._timeout):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = EyeResult(
                        name=name, response="", latency_ms=0, error=str(e)[:200],
                    )

        # Fill missing (timed out)
        for name in self._eyes:
            if name not in results:
                results[name] = EyeResult(
                    name=name, response="", latency_ms=self._timeout * 1000,
                    error="timeout",
                )

        # ── Phase 2: Collide ────────────────────────────
        alive_responses = {
            name: r.response for name, r in results.items() if r.alive
        }

        if len(alive_responses) >= 2:
            collision = eye_collide(alive_responses)
        else:
            # Not enough eyes for meaningful collision
            collision = CollisionResult(
                responses=alive_responses,
                concepts={},
                agreement=[],
                disagreement=[],
                silence=[],
                x_score=0.0,
                agreement_ratio=0.0,
                disagreement_ratio=0.0,
                silence_ratio=0.0,
                collision_pairs=0,
                eye_activation={},
            )

        # ── Phase 3: Fuse ──────────────────────────────
        fusion = ""
        fused_by = ""

        if fuse and len(alive_responses) >= 2:
            fusion_prompt = _build_parallel_fusion(prompt, results)
            try:
                fusion = self._fuser.adapter(fusion_prompt, _PARALLEL_FUSION_SYSTEM)
                fused_by = self._fuser.name
            except Exception:
                # Fallback: use best eye's response
                best = max(results.values(), key=lambda r: len(r.response))
                fusion = best.response
                fused_by = f"{best.name}(fallback)"
        elif fuse and alive_responses:
            # Single eye, no fusion needed but fuse=True so return best
            best = max(results.values(), key=lambda r: len(r.response))
            fusion = best.response
            fused_by = f"{best.name}(solo)"

        # ── Phase 4: Record ─────────────────────────────
        wall_time = (time.time() - t_wall) * 1000
        total_time = sum(r.latency_ms for r in results.values())

        # Record in pipeline organism
        alive_count = sum(1 for r in results.values() if r.alive)
        self._pipeline.organism.exhale(learnings=[
            f"parallel[{alive_count}/{len(results)}]: "
            f"x={collision.x_score:.2f} "
            f"wall={wall_time:.0f}ms "
            f"speedup={total_time / wall_time if wall_time > 0 else 1:.1f}x"
        ])

        cycle = ParallelBreathCycle(
            prompt=prompt,
            eyes=results,
            collision=collision,
            fusion=fusion,
            fused_by=fused_by,
            wall_time_ms=round(wall_time, 1),
            total_time_ms=round(total_time, 1),
        )
        self._cycles.append(cycle)

        return cycle

    # ── Introspection ────────────────────────────────────

    @property
    def eye_count(self) -> int:
        return len(self._eyes)

    @property
    def breath_count(self) -> int:
        return len(self._cycles)

    @property
    def avg_x_score(self) -> float:
        if not self._cycles:
            return 0.0
        return sum(c.x_score for c in self._cycles) / len(self._cycles)

    @property
    def avg_speedup(self) -> float:
        if not self._cycles:
            return 1.0
        return sum(c.speedup for c in self._cycles) / len(self._cycles)

    @property
    def total_cost(self) -> float:
        return sum(c.cost for c in self._cycles)

    def eye_report(self) -> dict[str, dict]:
        """Per-eye performance across all cycles."""
        report: dict[str, dict] = {}
        for name in self._eyes:
            results = [c.eyes[name] for c in self._cycles if name in c.eyes]
            alive = [r for r in results if r.alive]
            report[name] = {
                "calls": len(results),
                "alive": len(alive),
                "reliability": round(len(alive) / max(len(results), 1), 2),
                "avg_latency_ms": round(
                    sum(r.latency_ms for r in alive) / max(len(alive), 1), 1,
                ),
                "total_cost": round(sum(r.cost_est for r in alive), 6),
            }
        return report

    def summary(self) -> dict:
        """ParallelBreather vitals."""
        return {
            "eyes": list(self._eyes.keys()),
            "breaths": self.breath_count,
            "avg_x_score": round(self.avg_x_score, 3),
            "avg_speedup": round(self.avg_speedup, 2),
            "total_cost_usd": round(self.total_cost, 6),
            "fuser": self._fuser.name,
            "per_eye": self.eye_report(),
        }

    # ── Persistence ──────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize state (not adapters — those must be re-injected)."""
        return {
            "version": 1,
            "eyes": [
                {
                    "name": e.name,
                    "model_id": e.model_id,
                    "cost_per_mtok": e.cost_per_mtok,
                    "strengths": list(e.strengths),
                }
                for e in self._eyes.values()
            ],
            "fuser": self._fuser.name,
            "cycles": [c.to_dict() for c in self._cycles[-50:]],  # keep last 50
            "summary": self.summary(),
        }
