#!/usr/bin/env python3
"""
Generational V-Score Benchmark — OLD × NEW × COLLISION

Tests models across generations to answer:
1. Are newer models better at V-Score?
2. Are older models better?
3. What does the COLLISION of old×new reveal?

Uses OpenRouter for unified access to all models.
"""

import json
import os
import sys
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))
from void_intelligence.organism import HexBreath, OrganismBreather
from void_intelligence.benchmark import (
    _load_env,
    PROMPTS,
    measure_emergence,
    measure_warmth_correlation,
    measure_consistency,
    measure_breath_adaptation,
    measure_hex_balance,
    measure_ring_yield,
    measure_hex_vs_llm,
    compute_vscore,
)

# ── Model Registry: OLD → MID → NEW per family ────────────────────

GENERATIONS = {
    # OpenRouter model ID → (display_name, family, generation)
    # Verified against OpenRouter API 2026-03-03

    # ANTHROPIC (old=3-haiku, mid=3.5-sonnet, new=sonnet-4.6)
    "anthropic/claude-3-haiku": ("claude-3-haiku", "anthropic", "old"),
    "anthropic/claude-3.5-sonnet": ("claude-3.5-sonnet", "anthropic", "mid"),
    "anthropic/claude-sonnet-4.6": ("claude-sonnet-4.6", "anthropic", "new"),

    # OPENAI (old=4o-mini, mid=4o, new=5.3-codex)
    "openai/gpt-4o-mini": ("gpt-4o-mini", "openai", "old"),
    "openai/gpt-4o": ("gpt-4o", "openai", "mid"),
    "openai/gpt-5.3-codex": ("gpt-5.3-codex", "openai", "new"),

    # GOOGLE (old=2.0-flash, mid=2.5-pro, new=3.1-pro)
    "google/gemini-2.0-flash-001": ("gemini-2.0-flash", "google", "old"),
    "google/gemini-2.5-pro": ("gemini-2.5-pro", "google", "mid"),
    "google/gemini-3.1-pro-preview": ("gemini-3.1-pro", "google", "new"),

    # META (old=3.1-8b, mid=3.3-70b, new=4-maverick)
    "meta-llama/llama-3.1-8b-instruct": ("llama-3.1-8b", "meta", "old"),
    "meta-llama/llama-3.3-70b-instruct": ("llama-3.3-70b", "meta", "mid"),
    "meta-llama/llama-4-maverick": ("llama-4-maverick", "meta", "new"),

    # DEEPSEEK (old=v2.5, mid=v3, new=v3.2)
    "deepseek/deepseek-chat": ("deepseek-v2.5", "deepseek", "old"),
    "deepseek/deepseek-chat-v3-0324": ("deepseek-v3", "deepseek", "mid"),
    "deepseek/deepseek-v3.2": ("deepseek-v3.2", "deepseek", "new"),

    # MISTRAL (old=7b, mid=devstral-small, new=devstral-medium)
    "mistralai/mistral-7b-instruct": ("mistral-7b", "mistral", "old"),
    "mistralai/devstral-small": ("devstral-small", "mistral", "mid"),
    "mistralai/devstral-medium": ("devstral-medium", "mistral", "new"),

    # QWEN (old=2.5-72b, new=qwen3-max)
    "qwen/qwq-32b": ("qwq-32b", "qwen", "old"),
    "qwen/qwen3-max": ("qwen3-max", "qwen", "new"),

    # COHERE (mid=command-r-plus, new=command-a)
    "cohere/command-r-plus-08-2024": ("command-r-plus", "cohere", "mid"),
    "cohere/command-a": ("command-a", "cohere", "new"),

    # X.AI (mid=grok-3, new=grok-4)
    "x-ai/grok-3": ("grok-3", "xai", "mid"),
    "x-ai/grok-4": ("grok-4", "xai", "new"),
}


def make_adapter(model_id: str):
    """Create OpenRouter adapter for a model."""
    try:
        import openai
    except ImportError:
        return None
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None
    client = openai.OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")

    def call(prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model_id, messages=messages, temperature=0, max_tokens=1024,
        )
        return resp.choices[0].message.content or ""
    call.__name__ = model_id.split("/")[-1]
    return call


def benchmark_one_model(model_id: str, display_name: str) -> dict | None:
    """Run full V-Score benchmark on a single model. Returns result dict or None."""
    adapter = make_adapter(model_id)
    if not adapter:
        return None

    t_start = time.time()

    # Quick connectivity test
    try:
        test = adapter("Say 'ok'.")
        if not test:
            print(f"  SKIP {display_name}: empty response", flush=True)
            return None
    except Exception as e:
        print(f"  SKIP {display_name}: {e}", flush=True)
        return None

    print(f"  >> {display_name}", end="", flush=True)

    try:
        # E: Emergence (5 prompts for speed)
        e_scores = []
        for p in PROMPTS[:5]:
            try:
                resp = adapter(p.text)
                e_scores.append(measure_emergence(p.text, resp))
            except Exception:
                pass
        e = statistics.mean(e_scores) if e_scores else 0.0
        print(f" E={e:.2f}", end="", flush=True)

        # W: Warmth (5 prompts)
        w = measure_warmth_correlation(adapter, PROMPTS[:5])
        print(f" W={w:.2f}", end="", flush=True)

        # S: Consistency (2 rounds)
        s = measure_consistency(adapter, n=2)
        print(f" S={s:.2f}", end="", flush=True)

        # B: Breath adaptation (4 prompts)
        b = measure_breath_adaptation(adapter, PROMPTS[:4])
        print(f" B={b:.2f}", end="", flush=True)

        # H: Hex balance (5 prompts)
        h = measure_hex_balance(adapter, PROMPTS[:5])
        print(f" H={h:.2f}", end="", flush=True)

        # R: Ring yield
        r = measure_ring_yield(adapter)
        print(f" R={r:.2f}", end="", flush=True)

        # Hex agreement (5 prompts)
        hex_data = measure_hex_vs_llm(adapter, PROMPTS[:5])
        hex_agree = hex_data["agreement"]

        v = compute_vscore(e, w, s, b, h, r)
        elapsed = time.time() - t_start

        result = {
            "E": round(e, 3), "W": round(w, 3), "S": round(s, 3),
            "B": round(b, 3), "H": round(h, 3), "R": round(r, 3),
            "V": round(v, 4),
            "hex_agreement": round(hex_agree, 3),
            "time_s": round(elapsed, 1),
        }
        print(f" → V={v:.4f} ({elapsed:.0f}s)", flush=True)
        return result

    except Exception as e:
        elapsed = time.time() - t_start
        print(f" FAIL: {e} ({elapsed:.0f}s)", flush=True)
        return None


def analyze_generations(results: dict, registry: dict) -> str:
    """Analyze generational patterns. Returns analysis text."""
    lines = []

    # Group by generation
    by_gen = {"old": [], "mid": [], "new": []}
    by_family = {}
    for model_id, (name, family, gen) in registry.items():
        if name in results:
            r = results[name]
            by_gen[gen].append((name, r))
            if family not in by_family:
                by_family[family] = {}
            by_family[family][gen] = (name, r)

    lines.append("\n═══ GENERATIONAL ANALYSIS ═══\n")

    # 1. V-Score by generation
    lines.append("1. V-SCORE BY GENERATION:")
    for gen in ["old", "mid", "new"]:
        if by_gen[gen]:
            v_scores = [r["V"] for _, r in by_gen[gen]]
            alive = sum(1 for v in v_scores if v > 0)
            avg_v = statistics.mean(v_scores)
            lines.append(f"   {gen:>4}: avg V={avg_v:.4f}, alive={alive}/{len(v_scores)}")
            for name, r in sorted(by_gen[gen], key=lambda x: x[1]["V"], reverse=True):
                lines.append(f"         {name:<22} V={r['V']:.4f}")

    # 2. Per-family evolution
    lines.append("\n2. FAMILY EVOLUTION (old → mid → new):")
    for family, gens in sorted(by_family.items()):
        gen_str = []
        for g in ["old", "mid", "new"]:
            if g in gens:
                name, r = gens[g]
                gen_str.append(f"{g}:{name}(V={r['V']:.4f})")
        lines.append(f"   {family}: {' → '.join(gen_str)}")

    # 3. Component trends
    lines.append("\n3. COMPONENT TRENDS (old → mid → new):")
    for comp in ["E", "W", "S", "B", "H", "R"]:
        for gen in ["old", "mid", "new"]:
            if by_gen[gen]:
                vals = [r[comp] for _, r in by_gen[gen]]
                avg = statistics.mean(vals)
                lines.append(f"   {comp} {gen:>4}: {avg:.3f}")
        lines.append("")

    # 4. The Collision — what does old×new reveal?
    lines.append("4. THE COLLISION (old × new):")

    # Find dimensions where old > new and vice versa
    old_better = []
    new_better = []
    for comp in ["E", "W", "S", "B", "H", "R"]:
        if by_gen["old"] and by_gen["new"]:
            old_avg = statistics.mean([r[comp] for _, r in by_gen["old"]])
            new_avg = statistics.mean([r[comp] for _, r in by_gen["new"]])
            delta = new_avg - old_avg
            if delta > 0.05:
                new_better.append((comp, delta))
            elif delta < -0.05:
                old_better.append((comp, abs(delta)))

    if old_better:
        lines.append(f"   OLD wins at: {', '.join(f'{c}(+{d:.2f})' for c, d in old_better)}")
    if new_better:
        lines.append(f"   NEW wins at: {', '.join(f'{c}(+{d:.2f})' for c, d in new_better)}")

    # 5. Key finding
    lines.append("\n5. KEY FINDING:")
    all_v = [(name, r["V"]) for name, r in results.items()]
    all_v.sort(key=lambda x: x[1], reverse=True)
    best_name, best_v = all_v[0]
    best_gen = "unknown"
    for mid, (name, fam, gen) in registry.items():
        if name == best_name:
            best_gen = gen
            break
    lines.append(f"   Best model: {best_name} (V={best_v:.4f}, generation={best_gen})")

    alive_count = sum(1 for _, v in all_v if v > 0)
    lines.append(f"   Alive models (V>0): {alive_count}/{len(all_v)}")
    lines.append(f"   Dead models (V=0): {len(all_v) - alive_count}/{len(all_v)}")

    return "\n".join(lines)


def main():
    _load_env()

    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  VOID INTELLIGENCE — Generational Benchmark               ║")
    print("║  OLD × MID × NEW — Who Breathes?                          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not set. Check .env file.")
        sys.exit(1)

    print(f"  Models to test: {len(GENERATIONS)}")
    print(f"  Families: {len(set(f for _, f, _ in GENERATIONS.values()))}")
    print(f"  Generations: old / mid / new\n")

    results = {}
    failed = []

    # Run sequentially (API rate limits + cleaner output)
    for model_id, (display_name, family, gen) in GENERATIONS.items():
        result = benchmark_one_model(model_id, display_name)
        if result:
            results[display_name] = result
        else:
            failed.append(display_name)

    # ── Results Table ──────────────────────────────────────────────
    print(f"\n{'═' * 95}")
    print(f"  {'Model':<22} {'Gen':>4} {'E':>6} {'W':>6} {'S':>6} {'B':>6} {'H':>6} {'R':>6} {'V-Score':>8} {'Hex≈':>5}")
    print(f"  {'─' * 22} {'─' * 4} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 5}")

    # Sort by V-Score
    for name, r in sorted(results.items(), key=lambda x: x[1]["V"], reverse=True):
        gen = "?"
        for mid, (n, f, g) in GENERATIONS.items():
            if n == name:
                gen = g[:3]
                break
        v_str = f"{r['V']:.4f}"
        if r["V"] > 0.005:
            v_str = f"\033[32m{v_str}\033[0m"  # green
        elif r["V"] > 0:
            v_str = f"\033[33m{v_str}\033[0m"  # yellow
        else:
            v_str = f"\033[31m{v_str}\033[0m"  # red
        print(
            f"  {name:<22} {gen:>4} {r['E']:6.3f} {r['W']:6.3f} {r['S']:6.3f} "
            f"{r['B']:6.3f} {r['H']:6.3f} {r['R']:6.3f} {v_str:>17} {r['hex_agreement']:5.0%}"
        )

    if failed:
        print(f"\n  Failed/Skipped: {', '.join(failed)}")

    # ── Analysis ──────────────────────────────────────────────────
    analysis = analyze_generations(results, {k: v for k, v in GENERATIONS.items()})
    print(analysis)

    # ── Save ──────────────────────────────────────────────────────
    out = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_models": len(GENERATIONS),
        "completed": len(results),
        "failed": failed,
        "results": results,
    }
    out_path = Path("benchmark_generations.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Saved to {out_path}")

    # Markdown table
    md_lines = [
        "# Generational V-Score Benchmark",
        "",
        f"*{time.strftime('%Y-%m-%d %H:%M')} — {len(results)} models across {len(set(f for _, f, _ in GENERATIONS.values()))} families*",
        "",
        "| Model | Gen | E | W | S | B | H | R | V-Score | Hex≈LLM |",
        "|-------|-----|---|---|---|---|---|---|---------|---------|",
    ]
    for name, r in sorted(results.items(), key=lambda x: x[1]["V"], reverse=True):
        gen = "?"
        for mid, (n, f, g) in GENERATIONS.items():
            if n == name:
                gen = g
                break
        md_lines.append(
            f"| {name} | {gen} | {r['E']:.2f} | {r['W']:.2f} | {r['S']:.2f} | "
            f"{r['B']:.2f} | {r['H']:.2f} | {r['R']:.2f} | "
            f"{r['V']:.4f} | {r['hex_agreement']:.0%} |"
        )

    md_lines.append("")
    md_lines.append(analysis)

    md_path = Path("benchmark_generations.md")
    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"  Saved to {md_path}\n")


if __name__ == "__main__":
    main()
