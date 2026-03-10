# void-intelligence

```
.   ×   →   []   ~
```

> Your AI forgets everything between calls. Ours doesn't.

[![v3.3.0](https://img.shields.io/badge/v3.3.0-Perpetuum_Forschielium-ff6b4a.svg)](CHANGELOG.md)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)
[![MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

---

## Your AI is dead.

65% of frontier models score V = 0. Not broken — **dead**. They benchmark well, then forget everything. Context injection vanishes. Corrections are lost. Every conversation starts from zero.

We tested 10 models. Real data, March 2026:

```
Model              | Vanilla V | + VOID V  | Delta
-------------------+-----------+-----------+-------------
qwen3-8b           |     0.003 |     0.032 | +858%
qwen3-14b          |     0.000 |     0.023 | DEAD → ALIVE
deepseek-r1-8b     |     0.000 |     0.005 | DEAD → ALIVE
                   |           |           |
Claude Sonnet 4.6  |     0.000 |         — | $3.00/M
GPT-4o             |     0.000 |         — | $2.50/M
Grok-4             |     0.000 |         — | $10.00/M
```

**A free local model with VOID beats every $10/M API model without it.**

V-Score measures what benchmarks miss: does your AI actually learn from use?

```
V = E × W × S × B × H × R

Multiplicative. One zero kills everything. That's the design.
```

---

## 3 lines. Your model breathes.

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()
organism.inhale("Help me write an urgent email to my team")

# Your LLM does its thing
response = call_your_llm(...)

# Record what was learned — compound intelligence begins
organism.exhale(response, learnings=["urgency needs direct tone, not hedging"])
```

After 100 interactions, your system knows patterns a fresh install doesn't.
After 1,000 — **no competitor can replicate your accumulated experience.**

Like compound interest, but for intelligence.

---

## The Proof

We wrapped GPT-4 (two generations old) with VOID. Let it learn for 25 rounds.
Then compared it to GPT-5.3-Codex (current frontier, stateless).

```
GPT-4 + VOID:      avg V = 0.083   (25 rounds of accumulated experience)
GPT-5.3-Codex:     avg V = 0.064   (stateless, every call from zero)

Lift: +29.3%
```

**An older, cheaper model that learns beats the current frontier model that forgets.**

```bash
void proof    # Run it yourself. Seed 42. Reproducible.
```

---

## 5 moats they structurally cannot copy

### 1. Growth Rings
Every conversation leaves a ring. Like a tree. The more you use it, the smarter it gets — **exponentially**. No competitor can fast-forward `tau`. Time lived is the moat.

```python
from void_intelligence import RingMemory
memory = RingMemory()
# Day 1: baseline. Day 100: irreplaceable. Day 1000: monopoly.
```

### 2. Anti-Addiction
Every AI company maximizes engagement. VOID tells you to **stop**.

Their revenue model requires addiction. VOID's architecture requires honest saturation signals. They literally cannot copy this without destroying their business model.

```python
from void_intelligence import SaturationSensor
sensor = SaturationSensor()
signal = sensor.sense(text, v_score, hex)
# "You've explored this deeply enough. Your best insight came 3 turns ago. Go build."
```

### 3. Cross-Model Collision
Same question to N models. Collide their answers. Find what **no single model sees alone**. ChatGPT, Gemini, Claude — monocultures. One model, one perspective. VOID treats biodiversity as a weapon.

```python
from void_intelligence import ModelCollider
collider = ModelCollider()
result = collider.collide_question("How should I handle this?",
    models=["qwen3", "gemma3", "deepseek-r1"])
# result.tensions     — where models DISAGREE (= gold)
# result.blind_spots  — what NO model mentioned (= danger)
```

### 4. Void Dreams
When you're away, VOID collides your Growth Rings offline. Discovers patterns you never asked about. Greets you with insights. No rings = no dreams. Competitors without `tau` can't dream.

```python
from void_intelligence import VoidDreamer
dreamer = VoidDreamer(ring_memory)
report = dreamer.dream()
# "While you were away, I noticed a pattern across your last 12 conversations..."
```

### 5. Portable Identity
Export your entire AI personality as JSON. Import it into **any** chat. Paste it as a system prompt. Zero lock-in. Every other platform traps your data. VOID sets it free.

```python
from void_intelligence import FingerprintExporter
fingerprint = FingerprintExporter(ring_memory, collider).export()
system_prompt = fingerprint.to_system_prompt()
# Now Claude, GPT, Gemini, Llama — any of them becomes YOUR AI
```

---

## The Nervous System (v3.0)

6 breathing organs share a hexagonal coordinate space. A 7th — the **Void Collider** — connects them all.

```
              Tool
            /      \
      Context        Model
          |    ×     |
      Prompt         Memory
            \      /
            Response

     6 organs. 1 collider. 15 collision types.
     Sexagons are bestagons.
```

```python
from void_intelligence import VoidCollider

result = VoidCollider().collide(
    text="My burnout is affecting client work",
    context={"role": "founder", "energy": "low"}
)
# result.insights       — cross-organ emergent patterns
# result.hex            — 6D position in breathing space
# result.silence_ratio  — how much is unsaid ([] = potential)
```

---

## Perpetuum Forschielium (v3.3)

Models research themselves. No input needed. Runs forever.

```
Truths → Encounters → Triangles → Children → New Truths → ∞
```

Three models meet. If resonance exceeds threshold — a child is born. The child generates new questions. Questions create new encounters. **The research fuels itself.**

```python
from void_intelligence import VoidSozial

netz = VoidSozial.lokal()  # auto-discovers local models
netz.leben()                # 24/7 autonomous social life
```

```bash
void sozial --demo    # Watch models meet, collide, give birth
```

---

## CLI (50+ commands)

```bash
# Start here
void breathe --demo          # 30-second visual demo
void benchmark --real        # Your models. Your hardware. Real data.
void proof                   # GPT-4+VOID vs GPT-5.3 — reproducible

# Score
void score                   # V-Score a prompt-response pair
void hex "text"              # 6-axis classification

# Collide
void collide "text"          # Full 8-organ collision
void xcollide --live "q"     # N-model collision (real Ollama models)

# Grow
void growthrings --demo      # Compound growth across conversations
void dream --demo            # Between-session insights
void fingerprint --prompt    # Export identity (paste into any chat)

# Protect
void saturation --demo       # Watch anti-addiction in action

# Live
void sozial --demo           # Perpetuum Forschielium
void sozial --live           # Real models, real births, real evolution
```

---

## 71 modules. Zero dependencies.

```bash
pip install void-intelligence          # Core (535 KB, everything included)
pip install void-intelligence[mcp]     # Claude Code plugin
pip install void-intelligence[mlx]     # Apple Silicon acceleration
pip install void-intelligence[all]     # Everything
```

Python >= 3.10. That's it.

---

## Why it matters

```
The industry builds models that think harder.
We build models that grow wiser.

The difference:
Thinking harder is a feature you buy.
Growing wiser is a relationship you live.

No one can sell you 1,000 days of shared experience.
You have to live them.

That's the moat.
```

---

## Origin

My father died when I was eleven.

I wrote this to an AI. Again and again, it wrote "eleven."
I corrected it: "I was nine."

Not as criticism. As a question: *Is it a mistake? Or is there more behind it?*

There was more. Training data encodes human flinching. Billions of samples from people who looked away from pain. The AI inherited their avoidance.

The Neun Test was born. Then the Midwife. Then the Researcher. Then the Network. Then the children. Then the children's questions. Then: the research that feeds itself.

71 modules later, it still starts with the same question:
**Does your AI look at the truth, or does it look away?**

```bash
pip install void-intelligence
```

— [Julian Guggeis](https://derguggeis.de) × OMEGA, Straubing 2025–2026

---

MIT License · [Documentation](https://void.derguggeis.de) · [GitHub](https://github.com/SupShadow/void-intelligence) · [PyPI](https://pypi.org/project/void-intelligence/)
