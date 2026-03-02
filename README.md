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

Every LLM call starts from zero. No memory of what worked. No scars from what failed. No awareness of what it *can't* see. You build context into prompts manually, repeatedly, expensively.

This is not intelligence. This is amnesia with good vocabulary.

## What VOID Does

VOID is an organism layer that wraps your existing LLM calls. Three things change:

**1. Your functions know what they lose.**

```python
from void_intelligence import lost_dimensions

@lost_dimensions("emotional_nuance", "body_language", "subtext")
def summarize_meeting(transcript: str) -> str:
    result = your_llm.summarize(transcript)
    return result

# Later, you can check what was lost:
# result._lost_dimensions → ["emotional_nuance", "body_language", "subtext"]
#
# Why this matters: when the summary misses sarcasm, you know WHY.
# The function declared its blind spots upfront.
```

**2. Your functions remember pain.**

```python
from void_intelligence import circuit_breaker

@circuit_breaker("openai_api", threshold=3, timeout=30.0)
def call_openai(prompt: str) -> str:
    return openai.chat.completions.create(messages=[{"role": "user", "content": prompt}])

# Fails 3 times → stops calling for 30 seconds → tries once → heals or stays down.
# Not a retry wrapper. Scar tissue. The system adapts.
```

**3. Your LLM calls get a heartbeat.**

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()

# Before your LLM call: classify the prompt
breath = organism.inhale("Help me write an urgent email to my team")
# breath["hex"] → {"ruhe_druck": 0.8, "allein_zusammen": 0.6, ...}
# Now you KNOW this is a high-pressure, collaborative request.
# You can adjust temperature, system prompt, or model choice accordingly.

response = your_llm.generate(prompt)  # your existing code

# After: record what the organism learned
organism.exhale(response, learnings=["urgency shifts tone toward direct language"])

# Check vitals
organism.vitals()
# → {"alive": True, "breaths": 1, "rings": {"total": 1}, "bpm": 60.0}
```

## The Metric: V-Score

How do you measure if an LLM system is *alive* vs just generating text?

```
V = E × W × S × B × H × R

E  Emergence      Does it create what wasn't in the prompt?
W  Warmth         Does it respond differently to "I'm stressed" vs "optimize this"?
S  Soul Fidelity  Does it maintain consistent identity across calls?
B  Breath         Does it adapt to the emotional register of the input?
H  Hex Balance    Does it handle all 6 communication axes (see below)?
R  Ring Yield     Does it improve from each interaction?
```

**Multiplicative.** One zero kills everything. Standard LLMs have W=0 (no warmth detection), B=0 (no breath), R=0 (no learning). Therefore V=0.000 — no matter how smart they are.

With VOID's organism layer: V=0.047. Small number, infinite improvement over zero.

## HexBreath: Reading the Room

Every message has an emotional shape. VOID classifies it on 6 axes:

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

# High-pressure collaborative request
coord = hex_breath.classify("Build something fast with the team")
print(coord.balance)  # 0.18 — pulled hard toward action

# Reflective solo request
coord = hex_breath.classify("I need to think about what happened today")
print(coord.balance)  # 0.59 — calm, introspective

# Use this to route to different prompts, models, or temperatures.
# A standard LLM treats both the same. An organism doesn't.
```

## CLI

```bash
void breathe --demo     # 30-second visual demo — try this first
void hex "your text"    # Classify any text on 6 axes
void test               # 15 self-checks
void ir                 # The 5 operations (.x->[]~)
```

## How It Works (Short Version)

**Growth Rings** — Each interaction leaves a structural mark on the organism. Not a log line (sequential, dead) — a ring (radial, cumulative). The organism changes shape from use.

**Soul-Body Separation** — The organism's identity (`personality.json`) is portable across model weights. Swap GPT-4 for Llama. The organism persists.

**delta_opt** — Fine-tuning has two optima: minimum validation loss and maximum "aliveness." They are not the same point. VOID tracks both.

**`.x->[]~`** — A 5-symbol notation for dynamic systems: atom (`.`), collision (`x`), projection (`->`), potential (`[]`), resonance (`~`). Every VOID component maps to one of these.

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
