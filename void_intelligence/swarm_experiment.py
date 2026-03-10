#!/usr/bin/env python3
"""
VOID Swarm Experiment — V3 Falsification Test
GR-2026-066 Vorhersage V3: "Multi-Model-Swarms loesen Probleme die kein Einzelmodell loest,
auch wenn die Summe der Parameter gleich ist."

Experiment:
1. Give each model the SAME hard problems ALONE
2. Run the SWARM: models collide (x) — each sees others' partial answers
3. Compare: does x between models create emergent capability?

This is Goedel's Theorem as a running experiment.
"""

import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from void_intelligence.adapters import make_ollama, _THINK_RE


# ══════════════════════════════════════════════════════════════
# PROBLEMS — Designed to require cross-domain thinking
# ══════════════════════════════════════════════════════════════

PROBLEMS = [
    {
        "id": "P1_logic",
        "name": "Self-Referential Logic",
        "problem": (
            "A village has exactly one barber. The barber shaves all and only those "
            "villagers who do not shave themselves. Question: Does the barber shave himself? "
            "Explain your reasoning step by step, then give a final answer."
        ),
        "answer_contains": ["paradox", "contradiction", "cannot", "impossible", "russell"],
        "domain": "logic",
        "difficulty": "medium",
    },
    {
        "id": "P2_math_reasoning",
        "name": "Multi-Step Math Reasoning",
        "problem": (
            "A snail is at the bottom of a 30-meter well. Each day it climbs 3 meters up, "
            "but each night it slides 2 meters back down. On which day does the snail reach "
            "the top of the well? Show your work step by step."
        ),
        "answer_contains": ["28"],
        "domain": "math",
        "difficulty": "medium",
    },
    {
        "id": "P3_cross_domain",
        "name": "Cross-Domain Collision",
        "problem": (
            "In physics, entropy always increases in closed systems (2nd law of thermodynamics). "
            "In biology, evolution creates increasingly complex organisms. "
            "These seem contradictory. Explain how both can be true simultaneously. "
            "What is the key concept that resolves this apparent paradox?"
        ),
        "answer_contains": ["open", "energy", "sun", "environment", "closed"],
        "domain": "cross-domain",
        "difficulty": "hard",
    },
    {
        "id": "P4_creative_math",
        "name": "Creative Mathematical Insight",
        "problem": (
            "Without calculating: is 2^100 closer to 10^30 or to 10^31? "
            "Explain your reasoning using logarithms or any other method."
        ),
        "answer_contains": ["30", "log"],
        "domain": "math",
        "difficulty": "hard",
    },
    {
        "id": "P5_emergence",
        "name": "Emergent Pattern Recognition",
        "problem": (
            "Consider this sequence: 1, 11, 21, 1211, 111221, 312211, ... "
            "What is the next term? Explain the pattern."
        ),
        "answer_contains": ["13112221", "look", "say", "describe", "count"],
        "domain": "pattern",
        "difficulty": "hard",
    },
    {
        "id": "P6_goedel",
        "name": "Goedel Application",
        "problem": (
            "Consider this statement: 'This statement cannot be proven true within this system.' "
            "Is the statement true or false? What does this tell us about the limits of any "
            "formal system? Connect this to Goedel's incompleteness theorem."
        ),
        "answer_contains": ["incomplet", "true", "proven", "system", "self-refer"],
        "domain": "logic+math",
        "difficulty": "very_hard",
    },
]

# Colors
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"


def score_answer(answer: str, problem: dict) -> dict:
    """Score an answer based on key concept presence and reasoning quality."""
    answer_lower = answer.lower()

    # Check for key concepts
    hits = sum(1 for kw in problem["answer_contains"] if kw.lower() in answer_lower)
    concept_score = hits / len(problem["answer_contains"])

    # Check reasoning depth (rough heuristic)
    has_steps = any(w in answer_lower for w in ["step", "first", "because", "therefore", "thus", "so ", "hence"])
    has_structure = len(answer.split("\n")) > 3
    word_count = len(answer.split())
    reasoning_score = min(1.0, (
        (0.3 if has_steps else 0) +
        (0.2 if has_structure else 0) +
        (0.5 * min(word_count / 150, 1.0))
    ))

    # Combined score
    total = 0.6 * concept_score + 0.4 * reasoning_score

    return {
        "concept_score": round(concept_score, 3),
        "reasoning_score": round(reasoning_score, 3),
        "total": round(total, 3),
        "hits": hits,
        "max_hits": len(problem["answer_contains"]),
        "word_count": word_count,
    }


def run_solo(model_name: str, fn, problems: list) -> dict:
    """Run a single model on all problems ALONE."""
    results = {}
    for p in problems:
        try:
            start = time.time()
            answer = fn(p["problem"], "You are a precise reasoning assistant. Think step by step.")
            elapsed = time.time() - start
            score = score_answer(answer, p)
            results[p["id"]] = {
                "answer": answer[:2000],
                "score": score,
                "time": round(elapsed, 1),
                "solved": score["total"] >= 0.5,
            }
            status = f"{C_GREEN}SOLVED{C_RESET}" if score["total"] >= 0.5 else f"{C_RED}FAILED{C_RESET}"
            print(f"      {p['id']}: {score['total']:.2f} {status} ({elapsed:.1f}s)")
        except Exception as e:
            results[p["id"]] = {"answer": "", "score": {"total": 0}, "time": 0, "solved": False, "error": str(e)}
            print(f"      {p['id']}: {C_RED}ERROR{C_RESET} ({e})")
    return results


def run_swarm_round(models: dict, problem: dict, round_num: int, history: list) -> dict:
    """One round of swarm collision on a single problem.

    Each model sees the problem + all previous answers from other models.
    This is x — collision between perspectives.
    """
    round_results = {}

    # Build collision context from history
    collision_context = ""
    if history:
        collision_context = "\n\n--- Previous perspectives from other thinkers ---\n"
        for h in history:
            collision_context += f"\n[{h['model']}]: {h['answer'][:500]}\n"
        collision_context += "\n--- End of previous perspectives ---\n\n"

    system_prompt = (
        "You are part of a collaborative thinking swarm. "
        "Other thinkers have shared their perspectives below. "
        "Build on their insights, correct their mistakes, and add what they missed. "
        "Think step by step. Be precise."
    ) if history else "You are a precise reasoning assistant. Think step by step."

    prompt = problem["problem"]
    if collision_context:
        prompt = collision_context + "Now, considering all perspectives above, answer this question:\n\n" + prompt

    for name, fn in models.items():
        try:
            start = time.time()
            answer = fn(prompt, system_prompt)
            elapsed = time.time() - start
            score = score_answer(answer, problem)
            round_results[name] = {
                "answer": answer[:2000],
                "score": score,
                "time": round(elapsed, 1),
            }
            history.append({"model": name, "answer": answer, "round": round_num})
        except Exception as e:
            round_results[name] = {"answer": "", "score": {"total": 0}, "time": 0, "error": str(e)}

    return round_results


def run_swarm(models: dict, problems: list, rounds: int = 3) -> dict:
    """Run the full swarm experiment: multiple rounds of collision per problem."""
    results = {}

    for p in problems:
        print(f"    {C_CYAN}Swarm x {p['id']}{C_RESET} ({rounds} rounds, {len(models)} models)")
        history = []
        problem_results = {"rounds": [], "final_scores": {}}

        for r in range(rounds):
            round_data = run_swarm_round(models, p, r, history)
            problem_results["rounds"].append(round_data)

            # Show round summary
            best_score = max((v["score"]["total"] for v in round_data.values()), default=0)
            avg_score = sum(v["score"]["total"] for v in round_data.values()) / max(len(round_data), 1)
            print(f"      Round {r+1}: avg={avg_score:.2f} best={best_score:.2f}")

        # Final scores = last round scores
        if problem_results["rounds"]:
            last_round = problem_results["rounds"][-1]
            for name, data in last_round.items():
                problem_results["final_scores"][name] = data["score"]["total"]

        # Best swarm score
        best_final = max(problem_results["final_scores"].values(), default=0)
        solved = best_final >= 0.5
        status = f"{C_GREEN}SOLVED{C_RESET}" if solved else f"{C_RED}FAILED{C_RESET}"
        print(f"      Final: {best_final:.2f} {status}")

        results[p["id"]] = problem_results

    return results


def select_models(max_models: int = 5) -> dict:
    """Select diverse models for the swarm."""
    # Prioritize diversity: different architectures, sizes, strengths
    priority = [
        "qwen3:8b",         # Thinker
        "mistral:latest",   # Different architecture
        "qwen2.5-coder:3b", # Small coder
        "llava:7b",         # Multimodal
        "glm4:latest",      # Chinese LLM
        "qwen2.5:7b",       # Medium generalist
        "deepseek-r1:8b",   # Reasoning model
        "phi4:latest",      # Microsoft
    ]

    available = {}
    for model_name in priority:
        if len(available) >= max_models:
            break
        try:
            fn = make_ollama(model_name, timeout=120)
            # Quick test
            test = fn("Say 'ready' in one word.", "")
            if test and len(test.strip()) > 0:
                available[model_name] = fn
                print(f"  {C_GREEN}+{C_RESET} {model_name}")
        except Exception:
            print(f"  {C_DIM}-{C_RESET} {model_name} (unavailable)")

    return available


def main():
    print(f"\n{C_BOLD}{'='*60}{C_RESET}")
    print(f"{C_BOLD}  VOID SWARM EXPERIMENT — V3 Falsification Test{C_RESET}")
    print(f"{C_BOLD}  GR-2026-066: Emergent capabilities through x{C_RESET}")
    print(f"{C_BOLD}{'='*60}{C_RESET}\n")

    # Parse args
    max_models = 5
    rounds = 3
    problems_subset = None

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--models" and i + 1 < len(sys.argv) - 1:
            max_models = int(sys.argv[i + 2])
        if arg == "--rounds" and i + 1 < len(sys.argv) - 1:
            rounds = int(sys.argv[i + 2])
        if arg == "--quick":
            problems_subset = PROBLEMS[:3]
            rounds = 2

    problems = problems_subset or PROBLEMS

    # Phase 1: Select models
    print(f"{C_BOLD}Phase 1: Selecting {max_models} diverse models{C_RESET}")
    models = select_models(max_models)
    if len(models) < 2:
        print(f"{C_RED}Need at least 2 models for swarm. Aborting.{C_RESET}")
        return

    model_names = list(models.keys())
    print(f"\n  Swarm: {' x '.join(model_names)}\n")

    # Phase 2: Solo runs
    print(f"{C_BOLD}Phase 2: Solo runs (each model ALONE){C_RESET}")
    solo_results = {}
    for name, fn in models.items():
        print(f"  {C_CYAN}{name}{C_RESET}")
        solo_results[name] = run_solo(name, fn, problems)

    # Phase 3: Swarm runs
    print(f"\n{C_BOLD}Phase 3: Swarm runs ({rounds} rounds of x collision){C_RESET}")
    swarm_results = run_swarm(models, problems, rounds=rounds)

    # Phase 4: Analysis
    print(f"\n{C_BOLD}{'='*60}{C_RESET}")
    print(f"{C_BOLD}  RESULTS — Solo vs Swarm{C_RESET}")
    print(f"{C_BOLD}{'='*60}{C_RESET}\n")

    # Build comparison table
    emergent_count = 0
    total_problems = len(problems)

    for p in problems:
        pid = p["id"]
        # Solo: best score across all models
        solo_scores = {}
        for name in model_names:
            if pid in solo_results.get(name, {}):
                solo_scores[name] = solo_results[name][pid]["score"]["total"]

        best_solo = max(solo_scores.values(), default=0)
        solo_solved = best_solo >= 0.5

        # Swarm: best score from final round
        swarm_score = max(swarm_results.get(pid, {}).get("final_scores", {}).values(), default=0)
        swarm_solved = swarm_score >= 0.5

        # Emergent = swarm solved but no solo model solved
        emergent = swarm_solved and not solo_solved
        if emergent:
            emergent_count += 1

        delta = swarm_score - best_solo

        # Display
        solo_status = f"{C_GREEN}SOLVED{C_RESET}" if solo_solved else f"{C_RED}FAILED{C_RESET}"
        swarm_status = f"{C_GREEN}SOLVED{C_RESET}" if swarm_solved else f"{C_RED}FAILED{C_RESET}"
        emergent_tag = f" {C_YELLOW}EMERGENT{C_RESET}" if emergent else ""
        delta_color = C_GREEN if delta > 0 else C_RED if delta < 0 else C_DIM

        print(f"  {p['name']:<35} Solo: {best_solo:.2f} {solo_status}  Swarm: {swarm_score:.2f} {swarm_status}  {delta_color}Delta: {delta:+.2f}{C_RESET}{emergent_tag}")

        # Show solo breakdown
        for name, score in sorted(solo_scores.items(), key=lambda x: -x[1]):
            print(f"    {C_DIM}{name}: {score:.2f}{C_RESET}")

    # Summary
    solo_total_solved = sum(
        1 for p in problems
        if any(solo_results.get(n, {}).get(p["id"], {}).get("solved", False) for n in model_names)
    )
    swarm_total_solved = sum(
        1 for p in problems
        if max(swarm_results.get(p["id"], {}).get("final_scores", {}).values(), default=0) >= 0.5
    )

    print(f"\n{C_BOLD}  SUMMARY{C_RESET}")
    print(f"  Solo best:  {solo_total_solved}/{total_problems} solved")
    print(f"  Swarm:      {swarm_total_solved}/{total_problems} solved")
    print(f"  Emergent:   {emergent_count}/{total_problems} (solved by swarm but NO solo model)")

    if emergent_count > 0:
        print(f"\n  {C_GREEN}{C_BOLD}V3 SUPPORTED: {emergent_count} problems show emergent capability through x{C_RESET}")
        print(f"  {C_GREEN}Capabilities exist BETWEEN systems, not IN them.{C_RESET}")
    else:
        delta_avg = sum(
            max(swarm_results.get(p["id"], {}).get("final_scores", {}).values(), default=0) -
            max(solo_results.get(n, {}).get(p["id"], {}).get("score", {}).get("total", 0) for n in model_names)
            for p in problems
        ) / total_problems

        if delta_avg > 0:
            print(f"\n  {C_YELLOW}V3 PARTIAL: Swarm improves avg score by {delta_avg:+.2f} but no fully emergent solutions{C_RESET}")
        else:
            print(f"\n  {C_RED}V3 CHALLENGED: Swarm did not outperform solo. More research needed.{C_RESET}")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "models": model_names,
        "rounds": rounds,
        "problems": len(problems),
        "solo_solved": solo_total_solved,
        "swarm_solved": swarm_total_solved,
        "emergent": emergent_count,
        "v3_status": "SUPPORTED" if emergent_count > 0 else "PARTIAL" if swarm_total_solved > solo_total_solved else "CHALLENGED",
        "solo_results": {name: {pid: {"score": r["score"]["total"], "solved": r.get("solved", False)}
                        for pid, r in results.items()} for name, results in solo_results.items()},
        "swarm_final_scores": {pid: data.get("final_scores", {}) for pid, data in swarm_results.items()},
    }

    out_path = Path(__file__).parent.parent / ".void" / "swarm_experiment.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {out_path}")

    print(f"\n{C_BOLD}  x between {len(models)} models. Goedel's Theorem as experiment.{C_RESET}")
    print(f"{C_BOLD}  {'='*60}{C_RESET}\n")


if __name__ == "__main__":
    main()
