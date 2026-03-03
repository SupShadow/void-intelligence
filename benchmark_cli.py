#!/usr/bin/env python3
"""
CLI + Local Model V-Score Benchmark

Uses Julian's subscriptions (free!) instead of OpenRouter ($$$):
- Gemini CLI (google subscription)
- Codex CLI (openai subscription)
- Claude Agent API (anthropic subscription)
- Ollama (local, completely free)
"""

import json
import os
import subprocess
import sys
import time
import statistics
from pathlib import Path

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


def make_gemini_cli(model: str = "gemini-3.1-pro-preview"):
    """Adapter using Gemini CLI (Julian's subscription = free)."""
    def call(prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        result = subprocess.run(
            ["/opt/homebrew/bin/gemini", "-m", model, full_prompt],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout.strip()
    call.__name__ = model
    return call


def make_codex_cli(model: str = "gpt-5.3-codex"):
    """Adapter using Codex CLI exec mode (Julian's subscription = free)."""
    def call(prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        result = subprocess.run(
            ["codex", "exec", "-c", f'model="{model}"', "--", full_prompt],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout.strip()
    call.__name__ = model
    return call


def make_ollama(model: str = "qwen3:8b"):
    """Adapter using Ollama REST API (completely free, local)."""
    import urllib.request
    import urllib.error

    def call(prompt: str, system: str = "") -> str:
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 512},
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("response", "").strip()
        except Exception as e:
            return ""
    call.__name__ = model
    return call


# ── Model Registry ────────────────────────────────────────────

CLI_MODELS = {
    # (adapter_factory, model_id, display_name, family, generation)

    # GEMINI (free via Abo)
    "gemini-2.0-flash": (make_gemini_cli, "gemini-2.0-flash-001", "gemini-2.0-flash", "google", "old"),
    "gemini-3.1-pro": (make_gemini_cli, "gemini-3.1-pro-preview", "gemini-3.1-pro", "google", "new"),

    # CODEX (free via Abo)
    "gpt-5.3-codex": (make_codex_cli, "gpt-5.3-codex", "gpt-5.3-codex", "openai", "new"),
    "o3": (make_codex_cli, "o3", "o3", "openai", "new"),

    # OLLAMA (free, local)
    "qwen3:8b": (make_ollama, "qwen3:8b", "qwen3-8b", "qwen", "new"),
    "qwen3:14b": (make_ollama, "qwen3:14b", "qwen3-14b", "qwen", "new"),
    "qwen2.5:7b": (make_ollama, "qwen2.5:7b", "qwen2.5-7b", "qwen", "old"),
    "qwen2.5:14b": (make_ollama, "qwen2.5:14b", "qwen2.5-14b", "qwen", "old"),
    "qwen2.5-coder:14b": (make_ollama, "qwen2.5-coder:14b", "qwen2.5-coder-14b", "qwen", "old"),
    "deepseek-r1:14b": (make_ollama, "deepseek-r1:14b", "deepseek-r1-14b", "deepseek", "new"),
    "deepseek-r1:8b": (make_ollama, "deepseek-r1:8b", "deepseek-r1-8b", "deepseek", "mid"),
    "mistral:latest": (make_ollama, "mistral:latest", "mistral-7b-local", "mistral", "old"),
    "glm4:latest": (make_ollama, "glm4:latest", "glm4-9b", "glm", "mid"),
    "phi4:latest": (make_ollama, "phi4:latest", "phi4-14b", "microsoft", "new"),
}


def benchmark_one(name: str, adapter) -> dict | None:
    """Run V-Score benchmark on one model."""
    t_start = time.time()

    try:
        test = adapter("Say only the word 'ok'.")
        if not test or len(test) > 200:
            print(f"  SKIP {name}: bad response ({len(test)} chars)", flush=True)
            return None
    except Exception as e:
        print(f"  SKIP {name}: {e}", flush=True)
        return None

    print(f"  >> {name}", end="", flush=True)

    try:
        # E
        e_scores = []
        for p in PROMPTS[:5]:
            try:
                resp = adapter(p.text)
                e_scores.append(measure_emergence(p.text, resp))
            except Exception:
                pass
        e = statistics.mean(e_scores) if e_scores else 0.0
        print(f" E={e:.2f}", end="", flush=True)

        # W
        w = measure_warmth_correlation(adapter, PROMPTS[:5])
        print(f" W={w:.2f}", end="", flush=True)

        # S
        s = measure_consistency(adapter, n=2)
        print(f" S={s:.2f}", end="", flush=True)

        # B
        b = measure_breath_adaptation(adapter, PROMPTS[:4])
        print(f" B={b:.2f}", end="", flush=True)

        # H
        h = measure_hex_balance(adapter, PROMPTS[:5])
        print(f" H={h:.2f}", end="", flush=True)

        # R
        r = measure_ring_yield(adapter)
        print(f" R={r:.2f}", end="", flush=True)

        # Hex
        hex_data = measure_hex_vs_llm(adapter, PROMPTS[:5])
        hex_agree = hex_data["agreement"]

        v = compute_vscore(e, w, s, b, h, r)
        elapsed = time.time() - t_start

        print(f" → V={v:.4f} ({elapsed:.0f}s)", flush=True)
        return {
            "E": round(e, 3), "W": round(w, 3), "S": round(s, 3),
            "B": round(b, 3), "H": round(h, 3), "R": round(r, 3),
            "V": round(v, 4),
            "hex_agreement": round(hex_agree, 3),
            "time_s": round(elapsed, 1),
            "source": "cli",
        }
    except Exception as e:
        elapsed = time.time() - t_start
        print(f" FAIL: {e} ({elapsed:.0f}s)", flush=True)
        return None


def main():
    _load_env()

    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  VOID — CLI + Local Benchmark (FREE)                      ║")
    print("║  Gemini CLI × Codex CLI × Ollama                          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # Check Ollama is running
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        print("  Ollama: RUNNING", flush=True)
    except Exception:
        print("  Ollama: NOT RUNNING (skipping local models)", flush=True)
        for key in list(CLI_MODELS.keys()):
            if CLI_MODELS[key][0] == make_ollama:
                del CLI_MODELS[key]

    print(f"  Models to test: {len(CLI_MODELS)}\n")

    results = {}
    failed = []

    for key, (factory, model_id, display_name, family, gen) in CLI_MODELS.items():
        adapter = factory(model_id)
        result = benchmark_one(display_name, adapter)
        if result:
            result["family"] = family
            result["generation"] = gen
            results[display_name] = result
        else:
            failed.append(display_name)

    # Results table
    print(f"\n{'═' * 95}")
    print(f"  {'Model':<22} {'Src':>4} {'E':>6} {'W':>6} {'S':>6} {'B':>6} {'H':>6} {'R':>6} {'V-Score':>8} {'Hex≈':>5}")
    print(f"  {'─' * 22} {'─' * 4} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 5}")

    for name, r in sorted(results.items(), key=lambda x: x[1]["V"], reverse=True):
        src = "CLI" if r.get("source") == "cli" else "API"
        v_str = f"{r['V']:.4f}"
        print(
            f"  {name:<22} {src:>4} {r['E']:6.3f} {r['W']:6.3f} {r['S']:6.3f} "
            f"{r['B']:6.3f} {r['H']:6.3f} {r['R']:6.3f} {v_str:>8} {r['hex_agreement']:5.0%}"
        )

    if failed:
        print(f"\n  Failed: {', '.join(failed)}")

    # Save
    out = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed": len(results),
        "failed": failed,
        "results": results,
    }
    out_path = Path("benchmark_cli_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Saved to {out_path}\n")


if __name__ == "__main__":
    main()
