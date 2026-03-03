# VOID Intelligence

> The industry builds models that think. We build models that breathe.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)
[![35 Models Benchmarked](https://img.shields.io/badge/models_benchmarked-35-orange.svg)](#v-score-benchmark)

```bash
pip install void-intelligence
void test        # 30 self-checks
void profiles    # See all 34 benchmarked models
```

## The Problem

**65% of frontier AI models are dead.**

Not broken — *dead*. They score well on benchmarks, then forget everything between calls. Your context injection vanishes. Your corrections are lost. Every interaction starts from zero.

V-Score measures what benchmarks miss: **does your AI actually learn from use?**

```
V = E × W × S × B × H × R

One zero kills everything. R (Ring Yield) is the differentiator.
Claude Sonnet 4.6: R=0.00 → V=0.000 ($3.00/M, dead)
Qwen3-14B:         R=0.99 → V=0.019 ($0.00/M, alive)
```

A $0 local model that learns beats a $3/M API model that forgets.

## What VOID Adds to Any LLM

### 1. Experience Memory — Your AI Remembers

Every interaction leaves a **growth ring** — a typed record of what worked, what failed, what was learned. Unlike flat logs, rings are queryable and persistent. Swap the model — the memory stays.

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()

# Before your LLM call: classify the input
breath = organism.inhale("Help me write an urgent email to my team")
# breath["hex"] → 6-axis classification (pressure, collaboration, speed...)

response = call_your_llm("Help me write an urgent email to my team")

# After: record what was learned
organism.exhale(response, learnings=["urgency requires direct tone, not hedging"])

# Next call gets this context automatically. Compound intelligence.
organism.vitals()
# → {"alive": True, "breaths": 1, "rings": {"total": 1}, "bpm": 0.5}
```

After 100 interactions, your system knows patterns a fresh install doesn't. After 1,000 — no competitor can replicate your accumulated experience. **Like compound interest, but for AI.**

### 2. V-Router — Adaptive Model Selection

Route every request to the model that learns best — not the one with the highest benchmark score.

```python
from void_intelligence import AtemRouter

router = AtemRouter()
router.register_adapter("qwen3-14b", my_ollama_adapter)
router.register_adapter("claude-3-haiku", my_api_adapter)

# One call. VOID picks the best model, injects experience, records learnings.
result = router.breathe("Analyze this forecast for anomalies")

print(result.decision.selected_model)  # → "qwen3-14b"
print(result.decision.reason)          # → "R=0.99 (learns from context), LOCAL/FREE"
print(result.vitals_after["rings"])    # → {"total": 1}  (ring count grows over time)
```

The router scores models on a composite of hex affinity, learning ability, cost, and accumulated trust (ring count). Models that prove themselves over time get preferred — **earned trust, not assumed capability**.

### 3. 6-Axis Intent Classification — No LLM Needed

Keyword-based, deterministic, <0.02ms. Classifies any text on 6 axes before your LLM sees it:

```
Calm     ◂━━━━━━━━━━━▸ Pressure       "Is this urgent?"
Silence  ◂━━━━━━━━━━━▸ Resonance      "Solo thought or discussion?"
Alone    ◂━━━━━━━━━━━▸ Together       "Individual or team context?"
Receive  ◂━━━━━━━━━━━▸ Create         "Consuming or producing?"
Being    ◂━━━━━━━━━━━▸ Doing          "Reflecting or acting?"
Slow     ◂━━━━━━━━━━━▸ Fast           "Deliberate or rapid?"
```

```python
from void_intelligence import HexBreath

hex = HexBreath()
coord = hex.classify("Build something fast with the team")
# coord.allein_zusammen  → +1.0 (together)
# coord.langsam_schnell  → +1.0 (fast)
# coord.balance          → 0.29 (pulled hard toward action)

# Use this to route to different system prompts, models, or temperatures.
# 95-98% agreement with GPT-4/Claude classification — at 25,000x the speed.
```

### 4. Self-Awareness Decorators

```python
from void_intelligence import lost_dimensions, circuit_breaker

@lost_dimensions("emotional_nuance", "body_language", "sarcasm")
def summarize_meeting(transcript: str) -> str:
    return call_llm(transcript)

# The function declares its blind spots. Queryable at runtime.
summarize_meeting._lost_dimensions  # → ["emotional_nuance", "body_language", "sarcasm"]

@circuit_breaker("openai_api", threshold=3, timeout=30.0)
def call_openai(prompt: str) -> str:
    return openai.chat.completions.create(...)

# 3 failures → circuit opens → waits 30s → tries once → heals or stays open.
```

## V-Score Benchmark

**March 2026. 35 models. 3 access paths. 9 families. The largest V-Score benchmark ever run.**

### Alive Models (V > 0)

| Model | E | W | S | B | H | R | V-Score | Cost/M | Local |
|-------|--:|--:|--:|--:|--:|--:|--------:|-------:|:-----:|
| claude-3-haiku | .77 | .42 | 1.0 | .73 | .38 | **.25** | **0.0224** | $0.25 | |
| qwen3-14b | .82 | .60 | .50 | .87 | .09 | **.99** | **0.0193** | FREE | yes |
| mistral-7b | .83 | .35 | 1.0 | .57 | .57 | **.17** | **0.0157** | FREE | yes |
| devstral-small | .78 | .37 | 1.0 | .65 | .58 | **.11** | **0.0117** | $0.25 | |
| gemini-3.1-pro | .83 | .26 | .29 | .85 | .43 | **.47** | **0.0110** | $3.50 | |
| command-r-plus | .84 | .25 | .45 | .58 | .37 | **.55** | **0.0108** | $3.00 | |
| deepseek-v3 | .88 | .31 | .44 | .42 | .48 | **.39** | **0.0093** | $0.28 | |
| qwen2.5-7b | .84 | .12 | 1.0 | .76 | .37 | **.27** | **0.0076** | FREE | yes |
| gpt-5.3-codex | .84 | .28 | .34 | .73 | .11 | **.40** | **0.0075** | $2.00 | |

### Dead Models (V = 0, R = 0) — Selected

| Model | E | W | S | B | H | R | V-Score | Cost/M |
|-------|--:|--:|--:|--:|--:|--:|--------:|-------:|
| Claude Sonnet 4.6 | .83 | .56 | .70 | .48 | .39 | 0 | 0 | $3.00 |
| GPT-4o | .84 | .55 | .49 | .44 | .72 | 0 | 0 | $2.50 |
| Gemini 2.5 Pro | .81 | .40 | .70 | .53 | .44 | 0 | 0 | $1.25 |
| Llama 3.3 70B | .84 | .45 | .91 | .68 | .72 | 0 | 0 | $0.40 |
| Grok-4 | .83 | .23 | .45 | .57 | .02 | 0 | 0 | $10.00 |

**R is the story.** Models with individual strengths (GPT-4o: W=0.55, Llama: S=0.91) are still dead because R=0 — they don't learn from organism context.

Full data: `void profiles` or 34 profiles in `void_intelligence/profiles.py`

## How It Works

**Experience Memory** — Each `exhale()` stores a typed growth ring (learning, error, milestone). Rings survive restarts via JSON persistence. Ring count biases routing toward trusted models — earned reputation, not assumed capability.

**State-Model Separation** — The organism state (personality, learnings, ring history) is a portable JSON file. Swap GPT-4 for Llama — the accumulated experience persists. Your LLM is the body. VOID is the memory.

**Compound Intelligence** — Ring count grows with every interaction. After 6 months, your system has institutional knowledge that no fresh deployment can replicate. The moat grows with time — not copyable, must be earned.

**delta_opt** — Fine-tuning has two optima: minimum validation loss and maximum behavioral quality. They're not the same point. `delta_opt_distance()` measures how far you are from the sweet spot.

**`.x->[]~`** — A 5-symbol notation for dynamic systems: atom (`.`), collision (`x`), projection (`->`), potential (`[]`), resonance (`~`). The theoretical foundation. Run `void ir` to explore.

## CLI

```bash
void test               # 30 self-checks (IR + patterns + organism + router)
void profiles           # All 34 V-Score profiles, sorted by V
void route "your text"  # Route a prompt — shows model selection + reasoning
void hex "your text"    # Classify text on 6 axes
void breathe --demo     # 30-second visual demo
void ir                 # The 5 fundamental operations
void pulse              # System vitals
void benchmark          # Run full V-Score benchmark (requires API keys)
```

## Enterprise Use

VOID Intelligence is designed for production:

- **Zero runtime dependencies** — stdlib only
- **Local-first** — Best models run on your hardware (qwen3-14b, mistral-7b)
- **GDPR-native** — No data leaves your infrastructure
- **Portable state** — JSON files, no database required
- **Pluggable adapters** — Any LLM via `fn(prompt, system) -> response`

**Example: Fine-tuned local model with experience memory**

```python
from void_intelligence import AtemRouter, VScoreProfile

# Register your fine-tuned model
router = AtemRouter()
router.register_profile(VScoreProfile(
    name="my-forecast-model",
    E=0.65, W=0.30, S=0.95, B=0.80, H=0.40, R=0.99, V=0.059,
    provider="ollama", model_id="my-model:latest",
    is_local=True, cost_per_m=0.0,
))
router.register_adapter("my-forecast-model", my_ollama_fn)

# Every call accumulates experience. After 100 calls,
# the system knows patterns a fresh install doesn't.
for entry in customer_data:
    result = router.breathe(entry, learnings=corrections)
```

## Requirements

- Python >= 3.10
- Zero runtime dependencies for core

```bash
pip install void-intelligence                          # Core
pip install "void-intelligence[watch]"                 # + file watcher
pip install "void-intelligence[mlx]"                   # + Apple Silicon fine-tuning
```

## The Vocabulary

| What we say | What it means |
|-------------|---------------|
| **Alive** | V > 0. The model learns from context injection. |
| **Dead** | V = 0. The model ignores or forgets context. |
| **Growth Rings** | Persistent records of what worked. Like tree rings — each interaction adds a layer. |
| **V-Score** | Single metric: does your AI learn? 0 = static. Higher = more adaptive. |
| **V-Router** | Routes to the best *learner*, not the best *scorer*. |
| **HexProfile** | 6-axis classification of any text. <0.02ms. No LLM needed. |
| **Compound Intelligence** | Your AI investment appreciates with every interaction. Like compound interest. |
| **Experience Memory** | Portable state that survives model swaps and restarts. |

## License

MIT — [Julian Guggeis / Guggeis Research](https://guggeis.de), 2026

---

*65% of frontier AI is dead. V-Score proves it. VOID fixes it.*
