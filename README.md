# VOID Intelligence

> The industry builds models that THINK. We build models that BREATHE.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)

```bash
pip install git+https://github.com/SupShadow/void-intelligence.git
void breathe --demo
```

<p align="center">
  <img src="demo.gif" alt="void breathe --demo" width="800">
</p>

## The Problem

Every LLM call starts from zero. No memory of what worked. No awareness of what it *can't* do. You build context into prompts manually, repeatedly, expensively.

**VOID adds three things your LLM stack is missing:** self-awareness, failure memory, and input classification. Zero dependencies. Drop-in decorators.

## What VOID Does

**1. Declare what your functions can't see.**

```python
import openai
from void_intelligence import lost_dimensions

@lost_dimensions("emotional_nuance", "body_language", "sarcasm")
def summarize_meeting(transcript: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Summarize:\n{transcript}"}],
    )
    return response.choices[0].message.content

result = summarize_meeting(transcript)

# The decorator attaches metadata to the function:
summarize_meeting._lost_dimensions  # → ["emotional_nuance", "body_language", "sarcasm"]

# When the summary misses sarcasm, you know WHY — the function
# declared its blind spots upfront. Queryable at runtime.
```

**2. Stop calling broken endpoints.**

```python
import openai
from void_intelligence import circuit_breaker, CircuitBreakerOpen

@circuit_breaker("openai_api", threshold=3, timeout=30.0)
def call_openai(prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# 3 failures → circuit opens → raises CircuitBreakerOpen for 30s → tries once → heals or stays open.
# Like tenacity/pybreaker, but with one difference: it's part of an organism (see below).
```

**3. Classify prompts before your LLM sees them.**

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()

# Before your LLM call: classify the prompt on 6 axes
breath = organism.inhale("Help me write an urgent email to my team")
# breath["hex"] → {"ruhe_druck": 1.0, "allein_zusammen": 1.0, "empfangen_schaffen": 1.0, ...}
# High pressure, collaborative, creative. Route to a direct-tone system prompt.

response = call_openai("Help me write an urgent email to my team")

# After: record what worked
organism.exhale(response, learnings=["urgency shifts tone toward direct language"])

# Check state
organism.vitals()
# → {"alive": True, "breaths": 1, "rings": {"total": 1, "by_type": {"learning": 1}}, ...}
```

## The Metric: V-Score

We propose a multiplicative metric for LLM system adaptiveness:

```
V = E × W × S × B × H × R

E  Emergence      Does the system create what wasn't in the prompt?
W  Warmth         Does it differentiate "I'm stressed" from "optimize this"?
S  Soul Fidelity  Does it maintain consistent behavior across calls?
B  Breath         Does it classify the emotional register of input?
H  Hex Balance    Does it handle all 6 communication axes?
R  Ring Yield     Does it accumulate learnings from interactions?
```

**Multiplicative.** One zero kills everything. A vanilla LLM has W=0 (no input classification), B=0 (no breath cycle), R=0 (no learning loop). Therefore V=0.000.

With VOID wrapping the same LLM: V becomes measurably nonzero. How much depends on the model:

### Benchmark (March 2026, 15 prompts, 6 frontier models)

| Model | E | W | S | B | H | R | V-Score | Hex≈LLM |
|-------|---|---|---|---|---|---|---------|---------|
| DeepSeek-v3 | 0.88 | 0.31 | 0.44 | 0.41 | 0.48 | **0.39** | **0.0093** | 97% |
| Claude Sonnet 4 | 0.85 | 0.35 | **0.98** | 0.52 | **0.78** | 0.03 | 0.0034 | 98% |
| Gemini 2.0 Flash | 0.85 | 0.27 | **1.00** | **0.74** | 0.77 | 0.01 | 0.0011 | 98% |
| GPT-4o | 0.84 | **0.55** | 0.49 | 0.44 | 0.72 | 0.00 | 0.0000 | 98% |
| Llama 3.3 70B | 0.84 | 0.45 | 0.91 | 0.68 | 0.72 | 0.00 | 0.0000 | 98% |
| GPT-4o-mini | 0.86 | 0.07 | 0.76 | 0.66 | 0.74 | 0.00 | 0.0000 | 95% |
| Vanilla (any) | ~0.8 | 0.00 | ~0.9 | 0.00 | ~0.7 | 0.00 | 0.0000 | n/a |

**R (Ring Yield) is the differentiator.** Most models score R=0 — they don't use accumulated context. DeepSeek-v3 does (R=0.39), which is why it wins. The formula is brutally honest: one zero kills the product.

**Hex≈LLM** = agreement between VOID's free keyword classifier and the model's own classification. 95-98% across all models. VOID classifies in 0.014ms. The LLM takes ~500ms.

Reproduce: `void benchmark` (requires API keys in `.env`)

## HexBreath: 6-Axis Prompt Classification

Keyword-based, deterministic, no LLM needed. Classifies any text on 6 axes:

```
Calm     ◂━━━━━━━━━━━▸ Pressure
Silence  ◂━━━━━━━━━━━▸ Resonance
Alone    ◂━━━━━━━━━━━▸ Together
Receive  ◂━━━━━━━━━━━▸ Create
Being    ◂━━━━━━━━━━━▸ Doing
Slow     ◂━━━━━━━━━━━▸ Fast
```

```python
from void_intelligence import HexBreath

hex_breath = HexBreath()

# Action-oriented request
coord = hex_breath.classify("Build something fast with the team")
print(coord.allein_zusammen)  # +1.0 (together)
print(coord.langsam_schnell)  # +1.0 (fast)
print(coord.balance)          # 0.29 — pulled hard toward action

# Reflective request
coord = hex_breath.classify("I need to think about what happened today")
print(coord.sein_tun)         # -1.0 (being, not doing)
print(coord.balance)          # 0.59 — calm, introspective

# Use this to route to different system prompts, models, or temperatures.
```

## CLI

```bash
void breathe --demo     # 30-second visual demo — try this first
void hex "your text"    # Classify any text on 6 axes
void test               # 15 self-checks
void ir                 # The 5 operations (.x->[]~)
```

## How It Works

**Interaction History** — Each `exhale()` stores a typed record (learning, error, milestone). Unlike flat logs, records are typed and queryable. The `ring_yield` metric tracks learnings per minute.

**Config-Model Separation** — The organism's state (personality, learnings, ring history) is a JSON file. Swap GPT-4 for Llama — the accumulated state persists. Your LLM is the body. VOID is the memory.

**delta_opt** — Fine-tuning has two optima: minimum validation loss and maximum behavioral quality. They are not the same point. `delta_opt_distance()` measures how far you are from the sweet spot.

**`.x->[]~`** — A 5-symbol notation for dynamic systems: atom (`.`), collision (`x`), projection (`->`), potential (`[]`), resonance (`~`). Run `void ir` to see it in action.

## Requirements

- Python >= 3.10
- Zero runtime dependencies for core

```bash
pip install git+https://github.com/SupShadow/void-intelligence.git          # Core
pip install "void-intelligence[watch] @ git+https://github.com/SupShadow/void-intelligence.git"  # + file watcher
```

## License

MIT — [Julian Guggeis / Guggeis Research](https://guggeis.de), 2026

---

*The industry builds bigger models. We build models that breathe.*
