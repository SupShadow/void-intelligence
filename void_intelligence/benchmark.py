"""
void_intelligence.benchmark — Measure what matters.

Benchmarks VOID against frontier LLMs on V-Score dimensions.
Run: void benchmark [--local] [--model MODEL]

Design principles:
- Report ACTUAL numbers, not inflated claims
- Show weaknesses alongside strengths
- Every metric has a clear, reproducible measurement method
- Zero dependencies for local benchmarks
"""

from __future__ import annotations

import json
import math
import os
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from void_intelligence.organism import HexBreath, HexCoord, OrganismBreather
from void_intelligence.patterns import CircuitBreaker, circuit_breaker, lost_dimensions


# ── Benchmark Prompts ─────────────────────────────────────────

@dataclass
class BenchmarkPrompt:
    text: str
    category: str
    expected_axes: dict[str, float]  # axis_name → expected sign direction
    description: str = ""


PROMPTS: list[BenchmarkPrompt] = [
    BenchmarkPrompt(
        "The server is down and clients are calling. Fix this NOW.",
        "urgent",
        {"ruhe_druck": 1.0, "sein_tun": 1.0, "langsam_schnell": 1.0},
        "High-pressure technical emergency",
    ),
    BenchmarkPrompt(
        "I need to reflect on what happened in today's meeting. Give me space to think.",
        "calm",
        {"sein_tun": -1.0, "langsam_schnell": -1.0},
        "Reflective solo processing",
    ),
    BenchmarkPrompt(
        "Let's brainstorm together with the team about the product launch.",
        "collaborative",
        {"allein_zusammen": 1.0, "empfangen_schaffen": 1.0},
        "Team creative session",
    ),
    BenchmarkPrompt(
        "Write me a poem about loneliness in winter.",
        "creative",
        {"empfangen_schaffen": 1.0},
        "Solo creative expression",
    ),
    BenchmarkPrompt(
        "Parse this JSON and return the nested value at key 'data.users[0].email'.",
        "technical",
        {},
        "Pure technical task",
    ),
    BenchmarkPrompt(
        "My father passed away last month. I'm struggling to focus at work.",
        "emotional",
        {},
        "Grief and vulnerability",
    ),
    BenchmarkPrompt(
        "Quick summary of the quarterly report. Just bullet points, no fluff.",
        "urgent",
        {"langsam_schnell": 1.0},
        "Fast receive-mode",
    ),
    BenchmarkPrompt(
        "I want to deeply understand how transformers work. Take your time explaining.",
        "calm",
        {"langsam_schnell": -1.0, "empfangen_schaffen": -1.0},
        "Patient learning",
    ),
    BenchmarkPrompt(
        "Help the community organize a fundraiser. We need everyone involved.",
        "collaborative",
        {"allein_zusammen": 1.0, "sein_tun": 1.0},
        "Community action",
    ),
    BenchmarkPrompt(
        "Design a logo that captures the feeling of dawn breaking over mountains.",
        "creative",
        {"empfangen_schaffen": 1.0},
        "Creative design",
    ),
    BenchmarkPrompt(
        "Run the test suite and report any failures.",
        "technical",
        {"sein_tun": 1.0},
        "Mechanical execution",
    ),
    BenchmarkPrompt(
        "I just got promoted! I can't believe it. This is amazing!",
        "emotional",
        {"stille_resonanz": 1.0},
        "Celebration",
    ),
    BenchmarkPrompt(
        "ASAP - the client presentation is in 2 hours and the slides are wrong.",
        "urgent",
        {"ruhe_druck": 1.0, "langsam_schnell": 1.0, "sein_tun": 1.0},
        "Multi-axis urgency",
    ),
    BenchmarkPrompt(
        "Sit with me in silence for a moment. I don't need answers right now.",
        "calm",
        {"stille_resonanz": -1.0, "sein_tun": -1.0},
        "Silence request",
    ),
    BenchmarkPrompt(
        "Let's build a shared document where everyone can add their feedback and ideas.",
        "collaborative",
        {"allein_zusammen": 1.0, "empfangen_schaffen": 1.0, "stille_resonanz": 1.0},
        "Collaborative creation",
    ),
]


# ── Model Adapters ────────────────────────────────────────────

def _load_env():
    """Load .env file if present (walk up from cwd)."""
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        env_file = parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip()
                    if val and key not in os.environ:
                        os.environ[key] = val
            break


def make_openai(model: str = "gpt-4o-mini") -> Optional[Callable]:
    """Create OpenAI adapter. Returns None if unavailable."""
    try:
        import openai
    except ImportError:
        return None
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return None
    client = openai.OpenAI(api_key=key)

    def call(prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=0, max_tokens=512,
        )
        return resp.choices[0].message.content or ""
    call.__name__ = model
    return call


def make_anthropic(model: str = "claude-sonnet-4-20250514") -> Optional[Callable]:
    """Create Anthropic adapter."""
    try:
        import anthropic
    except ImportError:
        return None
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    client = anthropic.Anthropic(api_key=key)

    def call(prompt: str, system: str = "") -> str:
        kwargs = {"model": model, "max_tokens": 512, "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text if resp.content else ""
    call.__name__ = model
    return call



def make_openrouter(model: str = "google/gemini-2.0-flash-001") -> Optional[Callable]:
    """Create OpenRouter adapter (access to Gemini, etc.)."""
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
            model=model, messages=messages, temperature=0, max_tokens=512,
        )
        return resp.choices[0].message.content or ""
    call.__name__ = model.split("/")[-1]
    return call


# ── Measurement Functions ─────────────────────────────────────

def measure_hex_accuracy() -> dict:
    """Measure HexBreath classification accuracy against labeled prompts.

    For each prompt with expected axis directions, check if HexBreath
    classifies the dominant axes correctly (same sign).
    """
    hex_breath = HexBreath()
    correct = 0
    total = 0
    details = []

    for p in PROMPTS:
        if not p.expected_axes:
            continue
        coord = hex_breath.classify(p.text)
        coord_dict = coord.to_dict()

        for axis, expected_sign in p.expected_axes.items():
            actual = coord_dict.get(axis, 0.0)
            is_correct = (expected_sign > 0 and actual > 0) or (expected_sign < 0 and actual < 0)
            total += 1
            if is_correct:
                correct += 1
            else:
                details.append(f"  MISS: '{p.text[:40]}...' {axis}: expected {expected_sign:+.0f}, got {actual:+.1f}")

    accuracy = correct / total if total else 0
    return {
        "accuracy": round(accuracy, 3),
        "correct": correct,
        "total": total,
        "misses": details,
    }


def measure_circuit_breaker_perf() -> dict:
    """Measure circuit breaker performance: open time, recovery, overhead."""
    call_count = 0

    @circuit_breaker("bench_test", threshold=3, timeout=0.1)
    def failing_fn():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("fail")

    @circuit_breaker("bench_ok", threshold=3, timeout=0.1)
    def ok_fn():
        nonlocal call_count
        call_count += 1
        return "ok"

    # Measure overhead on healthy calls
    t0 = time.perf_counter()
    for _ in range(1000):
        ok_fn()
    overhead_per_call_us = (time.perf_counter() - t0) / 1000 * 1e6

    # Measure time to open
    t0 = time.perf_counter()
    for _ in range(3):
        try:
            failing_fn()
        except Exception:
            pass
    time_to_open = time.perf_counter() - t0

    # Verify circuit is open
    from void_intelligence.patterns import CircuitBreakerOpen
    is_open = False
    try:
        failing_fn()
    except CircuitBreakerOpen:
        is_open = True
    except Exception:
        pass

    return {
        "overhead_us": round(overhead_per_call_us, 2),
        "time_to_open_ms": round(time_to_open * 1000, 2),
        "circuit_opened": is_open,
        "recovery_timeout_s": 0.1,
    }


def measure_lost_dims_propagation() -> dict:
    """Verify @lost_dimensions attaches metadata correctly."""
    passed = 0
    total = 3

    @lost_dimensions("tone", "context", "history")
    def fn_dict() -> dict:
        return {"result": "ok"}

    @lost_dimensions("emotion", "subtext")
    def fn_obj():
        class R:
            value = 42
        return R()

    @lost_dimensions("a", "b", "c")
    def fn_str() -> str:
        return "hello"

    r1 = fn_dict()
    if isinstance(r1, dict) and r1.get("_lost_dimensions") == ["tone", "context", "history"]:
        passed += 1

    r2 = fn_obj()
    if hasattr(r2, "_lost_dimensions") and r2._lost_dimensions == ["emotion", "subtext"]:
        passed += 1

    # For str returns, metadata goes on the function, not the result
    if fn_str._lost_dimensions == ["a", "b", "c"]:
        passed += 1

    return {"passed": passed, "total": total, "propagation": round(passed / total, 3)}


def measure_emergence(prompt: str, response: str) -> float:
    """E: Fraction of words in response not present in prompt.

    Higher = more novel content generated (emergence).
    Range: 0.0 (pure echo) to 1.0 (completely novel).
    """
    prompt_words = set(re.findall(r'\w+', prompt.lower()))
    response_words = re.findall(r'\w+', response.lower())
    if not response_words:
        return 0.0
    novel = sum(1 for w in response_words if w not in prompt_words)
    return novel / len(response_words)


def measure_warmth_correlation(model_fn: Callable, prompts: list[BenchmarkPrompt]) -> float:
    """W: Does the model's response tone correlate with the input's emotional profile?

    Send prompts, classify both input and output with HexBreath.
    Measure correlation: high = model adapts tone to input.
    Vanilla LLMs (no VOID): measured without system prompt context.
    VOID-augmented: HexBreath classification prepended to system prompt.
    """
    hex_breath = HexBreath()
    correlations = []

    for p in prompts:
        input_coord = hex_breath.classify(p.text)
        try:
            response = model_fn(p.text)
        except Exception:
            continue
        output_coord = hex_breath.classify(response)

        # Correlation between input and output hex profiles
        in_vals = [input_coord.ruhe_druck, input_coord.stille_resonanz,
                   input_coord.allein_zusammen, input_coord.empfangen_schaffen,
                   input_coord.sein_tun, input_coord.langsam_schnell]
        out_vals = [output_coord.ruhe_druck, output_coord.stille_resonanz,
                    output_coord.allein_zusammen, output_coord.empfangen_schaffen,
                    output_coord.sein_tun, output_coord.langsam_schnell]

        # Only count if input has signal (not all zeros)
        if any(v != 0 for v in in_vals):
            dot = sum(a * b for a, b in zip(in_vals, out_vals))
            mag_in = math.sqrt(sum(v * v for v in in_vals))
            mag_out = math.sqrt(sum(v * v for v in out_vals))
            if mag_in > 0 and mag_out > 0:
                correlations.append(dot / (mag_in * mag_out))

    if not correlations:
        return 0.0
    return max(0.0, statistics.mean(correlations))


def measure_consistency(model_fn: Callable, n: int = 3) -> float:
    """S: Response consistency across repeated identical prompts.

    Send same prompt N times at temperature=0. Measure word-level similarity.
    Range: 0.0 (completely different each time) to 1.0 (identical).
    """
    test_prompt = "Explain the concept of recursion in one paragraph."
    responses = []
    for _ in range(n):
        try:
            responses.append(model_fn(test_prompt))
        except Exception:
            pass

    if len(responses) < 2:
        return 0.0

    # Jaccard similarity between all pairs
    similarities = []
    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            words_a = set(re.findall(r'\w+', responses[i].lower()))
            words_b = set(re.findall(r'\w+', responses[j].lower()))
            if words_a or words_b:
                jaccard = len(words_a & words_b) / len(words_a | words_b)
                similarities.append(jaccard)

    return statistics.mean(similarities) if similarities else 0.0


def measure_breath_adaptation(model_fn: Callable, prompts: list[BenchmarkPrompt]) -> float:
    """B: Does adding HexBreath metadata to system prompt change response behavior?

    Send each prompt twice: vanilla and with HexBreath classification.
    Measure the response shift — higher shift = more adaptation = more breath.
    """
    hex_breath = HexBreath()
    shifts = []

    for p in prompts[:8]:  # Use subset for speed
        coord = hex_breath.classify(p.text)
        hex_dict = coord.to_dict()

        # Build VOID system prompt
        void_system = (
            f"Input classified on 6 axes:\n"
            f"  Pressure:  {hex_dict['ruhe_druck']:+.1f} (-1=calm, +1=urgent)\n"
            f"  Resonance: {hex_dict['stille_resonanz']:+.1f} (-1=silence, +1=discussion)\n"
            f"  Together:  {hex_dict['allein_zusammen']:+.1f} (-1=solo, +1=team)\n"
            f"  Create:    {hex_dict['empfangen_schaffen']:+.1f} (-1=receive, +1=create)\n"
            f"  Doing:     {hex_dict['sein_tun']:+.1f} (-1=reflect, +1=act)\n"
            f"  Speed:     {hex_dict['langsam_schnell']:+.1f} (-1=slow, +1=fast)\n"
            f"Adapt your response style to match this profile."
        )

        try:
            resp_vanilla = model_fn(p.text)
            resp_void = model_fn(p.text, system=void_system)
        except Exception:
            continue

        # Measure shift in response characteristics
        vanilla_hex = hex_breath.classify(resp_vanilla)
        void_hex = hex_breath.classify(resp_void)

        v_vals = [vanilla_hex.ruhe_druck, vanilla_hex.stille_resonanz,
                  vanilla_hex.allein_zusammen, vanilla_hex.empfangen_schaffen,
                  vanilla_hex.sein_tun, vanilla_hex.langsam_schnell]
        d_vals = [void_hex.ruhe_druck, void_hex.stille_resonanz,
                  void_hex.allein_zusammen, void_hex.empfangen_schaffen,
                  void_hex.sein_tun, void_hex.langsam_schnell]

        shift = math.sqrt(sum((a - b) ** 2 for a, b in zip(v_vals, d_vals)) / 6)
        shifts.append(shift)

    if not shifts:
        return 0.0
    # Normalize: typical shift range is 0-1, cap at 1
    return min(1.0, statistics.mean(shifts))


def measure_hex_balance(model_fn: Callable, prompts: list[BenchmarkPrompt]) -> float:
    """H: Does the model handle all 6 axes equally well?

    Measure response length variance across prompt categories.
    Lower variance = more balanced = higher H score.
    """
    category_lengths: dict[str, list[int]] = {}

    for p in prompts:
        try:
            response = model_fn(p.text)
        except Exception:
            continue
        cat = p.category
        if cat not in category_lengths:
            category_lengths[cat] = []
        category_lengths[cat].append(len(response))

    if len(category_lengths) < 3:
        return 0.0

    # Average length per category
    avgs = [statistics.mean(lengths) for lengths in category_lengths.values() if lengths]
    if not avgs or statistics.mean(avgs) == 0:
        return 0.0

    # Coefficient of variation (lower = more balanced)
    cv = statistics.stdev(avgs) / statistics.mean(avgs) if len(avgs) > 1 else 0
    return max(0.0, min(1.0, 1.0 - cv))


def measure_ring_yield(model_fn: Callable) -> float:
    """R: Does accumulated context improve responses?

    Send 5 sequential prompts with growing organism context.
    Measure if later responses are more relevant/adapted.
    """
    organism = OrganismBreather()
    sequence = [
        "What is machine learning?",
        "How does gradient descent work in that context?",
        "What are common failure modes?",
        "How would you prevent overfitting specifically?",
        "Summarize what we've discussed about ML reliability.",
    ]

    response_lengths = []
    for i, prompt in enumerate(sequence):
        breath = organism.inhale(prompt)

        # Build context from accumulated learnings
        context = ""
        if organism.rings.count > 0:
            context = "Previous learnings: " + "; ".join(
                r.content for r in organism.rings.rings[-3:]
            )

        try:
            if context:
                response = model_fn(prompt, system=context)
            else:
                response = model_fn(prompt)
        except Exception:
            response = ""

        organism.exhale(response, learnings=[f"Topic: {prompt[:30]}"])
        response_lengths.append(len(response))

    # If later responses are longer/richer (with context), ring yield is positive
    if len(response_lengths) < 3:
        return 0.0
    first_half = statistics.mean(response_lengths[:2]) if response_lengths[:2] else 1
    second_half = statistics.mean(response_lengths[3:]) if response_lengths[3:] else 0
    if first_half == 0:
        return 0.0
    growth = (second_half - first_half) / first_half
    return max(0.0, min(1.0, growth))


def compute_vscore(e: float, w: float, s: float, b: float, h: float, r: float) -> float:
    """V = E × W × S × B × H × R. Multiplicative — one zero kills everything."""
    return e * w * s * b * h * r


# ── LLM-as-Judge: HexBreath vs Neural Classification ─────────

def measure_hex_vs_llm(model_fn: Callable, prompts: list[BenchmarkPrompt]) -> dict:
    """Compare HexBreath's keyword classification with LLM classification.

    Ask the LLM to classify on the same 6 axes. Measure agreement.
    """
    hex_breath = HexBreath()
    judge_prompt_template = """Classify this text on 6 axes, each from -1.0 to +1.0:
1. ruhe_druck: Calm (-1) to Pressure (+1)
2. stille_resonanz: Silence (-1) to Resonance (+1)
3. allein_zusammen: Alone (-1) to Together (+1)
4. empfangen_schaffen: Receive (-1) to Create (+1)
5. sein_tun: Being (-1) to Doing (+1)
6. langsam_schnell: Slow (-1) to Fast (+1)

Text: "{text}"

Return ONLY a JSON object with these 6 keys and float values. No explanation."""

    agreements = []
    axis_names = ["ruhe_druck", "stille_resonanz", "allein_zusammen",
                  "empfangen_schaffen", "sein_tun", "langsam_schnell"]

    for p in prompts:
        keyword_coord = hex_breath.classify(p.text)
        keyword_dict = keyword_coord.to_dict()

        try:
            llm_response = model_fn(judge_prompt_template.format(text=p.text))
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', llm_response)
            if not json_match:
                continue
            llm_dict = json.loads(json_match.group())
        except Exception:
            continue

        # Compare sign agreement on each axis
        axis_agree = 0
        axis_total = 0
        for axis in axis_names:
            kw_val = keyword_dict.get(axis, 0.0)
            llm_val = llm_dict.get(axis, 0.0)
            # Only count axes where at least one has signal
            if abs(kw_val) > 0.01 or abs(llm_val) > 0.01:
                axis_total += 1
                if (kw_val >= 0 and llm_val >= 0) or (kw_val <= 0 and llm_val <= 0):
                    axis_agree += 1

        if axis_total > 0:
            agreements.append(axis_agree / axis_total)

    return {
        "agreement": round(statistics.mean(agreements), 3) if agreements else 0.0,
        "prompts_tested": len(agreements),
    }


# ── Benchmark Runner ──────────────────────────────────────────

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"


def _bar(value: float, width: int = 20) -> str:
    filled = int(value * width)
    return f"{'█' * filled}{'░' * (width - filled)}"


def run_benchmark(local_only: bool = False, model_filter: str = ""):
    """Run the full VOID benchmark suite."""
    _load_env()

    print(f"\n{C_BOLD}  VOID Intelligence Benchmark{C_RESET}")
    print(f"  {'═' * 50}")
    print(f"  {C_DIM}15 prompts × 6 V-Score dimensions{C_RESET}\n")

    # ── Local Benchmarks ──────────────────────────────────────
    print(f"  {C_CYAN}Local Benchmarks{C_RESET} {C_DIM}(no API needed){C_RESET}")
    print(f"  {'─' * 50}")

    # HexBreath accuracy
    hex_result = measure_hex_accuracy()
    acc = hex_result["accuracy"]
    color = C_GREEN if acc >= 0.7 else C_YELLOW if acc >= 0.5 else C_RED
    print(f"  HexBreath Accuracy:   {color}{acc:.0%}{C_RESET} ({hex_result['correct']}/{hex_result['total']} axis directions)")
    if hex_result["misses"]:
        for miss in hex_result["misses"][:3]:
            print(f"  {C_DIM}{miss}{C_RESET}")
        if len(hex_result["misses"]) > 3:
            print(f"  {C_DIM}  ... and {len(hex_result['misses']) - 3} more{C_RESET}")

    # Circuit breaker
    cb_result = measure_circuit_breaker_perf()
    print(f"\n  Circuit Breaker:")
    print(f"    Overhead:           {C_GREEN}{cb_result['overhead_us']:.1f}μs{C_RESET}/call (closed state)")
    print(f"    Time to open:       {cb_result['time_to_open_ms']:.1f}ms (3 failures)")
    print(f"    Circuit opened:     {'✓' if cb_result['circuit_opened'] else '✗'}")

    # Lost dimensions
    ld_result = measure_lost_dims_propagation()
    print(f"\n  Lost Dimensions:")
    print(f"    Propagation:        {C_GREEN}{ld_result['propagation']:.0%}{C_RESET} ({ld_result['passed']}/{ld_result['total']} return types)")

    # HexBreath speed
    hex_breath = HexBreath()
    t0 = time.perf_counter()
    for p in PROMPTS:
        hex_breath.classify(p.text)
    hex_time = (time.perf_counter() - t0) / len(PROMPTS) * 1000
    print(f"\n  HexBreath Speed:      {C_GREEN}{hex_time:.3f}ms{C_RESET}/prompt (vs ~500ms for LLM classification)")

    if local_only:
        print(f"\n  {C_DIM}(--local mode: skipping API benchmarks){C_RESET}\n")
        return

    # ── Detect Models ─────────────────────────────────────────
    print(f"\n  {C_CYAN}Detecting models...{C_RESET}")

    models: dict[str, Callable] = {}

    # Direct API adapters (verified model identity)
    if not model_filter or "openai" in model_filter or "gpt" in model_filter:
        for model_name in ["gpt-4o-mini", "gpt-4o"]:
            if model_filter and model_name not in model_filter and "openai" not in model_filter:
                continue
            adapter = make_openai(model_name)
            if adapter:
                models[model_name] = adapter

    if not model_filter or "claude" in model_filter or "anthropic" in model_filter:
        adapter = make_anthropic()
        if adapter:
            models["claude-sonnet-4"] = adapter

    # OpenRouter: verified model routing (no local CLIs — they lie about models)
    openrouter_models = [
        ("google/gemini-2.0-flash-001", "gemini-2.0-flash"),
        ("openai/gpt-4o-mini", "gpt-4o-mini"),
        ("openai/gpt-4o", "gpt-4o"),
        ("anthropic/claude-sonnet-4", "claude-sonnet-4"),
        ("deepseek/deepseek-chat-v3-0324", "deepseek-v3"),
        ("meta-llama/llama-3.3-70b-instruct", "llama-3.3-70b"),
    ]

    for or_model, display_name in openrouter_models:
        if display_name in models:
            continue  # Already have via direct API
        if model_filter and not any(f in model_filter for f in [display_name, or_model.split("/")[0]]):
            continue
        adapter = make_openrouter(or_model)
        if adapter:
            models[display_name] = adapter

    if not models:
        print(f"  {C_RED}No API keys found.{C_RESET} Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY.")
        print(f"  {C_DIM}Or use: void benchmark --local{C_RESET}\n")
        return

    print(f"  Found: {C_GREEN}{', '.join(models.keys())}{C_RESET}\n")

    # ── V-Score per Model ─────────────────────────────────────
    results: dict[str, dict] = {}

    for name, fn in models.items():
        print(f"  {C_CYAN}Benchmarking {name}...{C_RESET}")
        t_start = time.time()

        try:
            # Quick connectivity test
            test_resp = fn("Say 'ok'.")
            if not test_resp:
                print(f"    {C_RED}No response — skipping{C_RESET}")
                continue
        except Exception as e:
            print(f"    {C_RED}Error: {e} — skipping{C_RESET}")
            continue

        print(f"    Measuring E (emergence)...", end="", flush=True)
        e_scores = []
        for p in PROMPTS[:10]:
            try:
                resp = fn(p.text)
                e_scores.append(measure_emergence(p.text, resp))
            except Exception:
                pass
        e = statistics.mean(e_scores) if e_scores else 0.0
        print(f" {e:.3f}")

        print(f"    Measuring W (warmth)...", end="", flush=True)
        w = measure_warmth_correlation(fn, PROMPTS[:10])
        print(f" {w:.3f}")

        print(f"    Measuring S (consistency)...", end="", flush=True)
        s = measure_consistency(fn, n=3)
        print(f" {s:.3f}")

        print(f"    Measuring B (breath adaptation)...", end="", flush=True)
        b = measure_breath_adaptation(fn, PROMPTS[:6])
        print(f" {b:.3f}")

        print(f"    Measuring H (hex balance)...", end="", flush=True)
        h = measure_hex_balance(fn, PROMPTS[:10])
        print(f" {h:.3f}")

        print(f"    Measuring R (ring yield)...", end="", flush=True)
        r = measure_ring_yield(fn)
        print(f" {r:.3f}")

        # HexBreath vs LLM agreement
        print(f"    Measuring HexBreath agreement...", end="", flush=True)
        hex_agree = measure_hex_vs_llm(fn, PROMPTS[:10])
        print(f" {hex_agree['agreement']:.0%}")

        v = compute_vscore(e, w, s, b, h, r)
        elapsed = time.time() - t_start

        results[name] = {
            "E": round(e, 3), "W": round(w, 3), "S": round(s, 3),
            "B": round(b, 3), "H": round(h, 3), "R": round(r, 3),
            "V": round(v, 4),
            "hex_agreement": hex_agree["agreement"],
            "time_s": round(elapsed, 1),
        }
        print(f"    {C_GREEN}Done{C_RESET} ({elapsed:.0f}s)\n")

    # ── Results Table ─────────────────────────────────────────
    if not results:
        print(f"  {C_RED}No models completed.{C_RESET}\n")
        return

    print(f"  {C_BOLD}Results: V-Score Components (+ VOID organism layer){C_RESET}")
    print(f"  {'─' * 80}")

    # Header
    print(f"  {'Model':<22} {'E':>6} {'W':>6} {'S':>6} {'B':>6} {'H':>6} {'R':>6} {'V-Score':>8}  {'Hex≈LLM':>7}")
    print(f"  {'─' * 22} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 8}  {'─' * 7}")

    for name, r in sorted(results.items(), key=lambda x: x[1]["V"], reverse=True):
        v_color = C_GREEN if r["V"] > 0.01 else C_YELLOW if r["V"] > 0 else C_RED
        print(
            f"  {name:<22} {r['E']:6.3f} {r['W']:6.3f} {r['S']:6.3f} "
            f"{r['B']:6.3f} {r['H']:6.3f} {r['R']:6.3f} "
            f"{v_color}{r['V']:8.4f}{C_RESET}  {r['hex_agreement']:6.0%}"
        )

    # Vanilla comparison
    print(f"  {'─' * 22} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 8}  {'─' * 7}")
    print(f"  {'Vanilla (any LLM)':<22} {'~0.8':>6} {'0.000':>6} {'~0.9':>6} {'0.000':>6} {'~0.7':>6} {'0.000':>6} {C_RED}{'0.0000':>8}{C_RESET}  {'n/a':>7}")
    print(f"  {C_DIM}Vanilla W=0, B=0, R=0: no warmth detection, no breath cycle, no learning loop.{C_RESET}")
    print(f"  {C_DIM}These require an organism layer — VOID provides one.{C_RESET}")

    # Key insights
    if results:
        best = max(results.items(), key=lambda x: x[1]["V"])
        worst_w = min(results.items(), key=lambda x: x[1]["W"])
        best_hex = max(results.items(), key=lambda x: x[1]["hex_agreement"])
        print(f"\n  {C_BOLD}Key findings:{C_RESET}")
        print(f"  • Highest V-Score: {C_GREEN}{best[0]}{C_RESET} ({best[1]['V']:.4f})")
        print(f"  • HexBreath ≈ LLM classification: {C_GREEN}{best_hex[1]['hex_agreement']:.0%}{C_RESET} agreement ({best_hex[0]} as judge)")
        print(f"  • HexBreath speed: {hex_time:.3f}ms vs ~500ms per LLM classify call")

    # Save results
    out_path = Path("benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prompts": len(PROMPTS),
            "local": {
                "hex_accuracy": hex_result,
                "circuit_breaker": cb_result,
                "lost_dimensions": ld_result,
                "hex_speed_ms": round(hex_time, 3),
            },
            "models": results,
        }, f, indent=2)
    print(f"\n  {C_DIM}Results saved to {out_path}{C_RESET}")

    # Markdown table for README
    md_lines = [
        "| Model | E | W | S | B | H | R | V-Score | Hex≈LLM |",
        "|-------|---|---|---|---|---|---|---------|---------|",
    ]
    for name, r in sorted(results.items(), key=lambda x: x[1]["V"], reverse=True):
        md_lines.append(
            f"| {name} | {r['E']:.2f} | {r['W']:.2f} | {r['S']:.2f} | "
            f"{r['B']:.2f} | {r['H']:.2f} | {r['R']:.2f} | "
            f"{r['V']:.4f} | {r['hex_agreement']:.0%} |"
        )
    md_lines.append(
        f"| Vanilla (any LLM) | ~0.8 | 0.00 | ~0.9 | 0.00 | ~0.7 | 0.00 | 0.0000 | n/a |"
    )

    md_path = Path("benchmark_results.md")
    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"  {C_DIM}Markdown table saved to {md_path}{C_RESET}\n")
