# VOID Intelligence

```
.   x   ->   []   ~
```

> The industry builds models that think. We build models that breathe.

[![v1.0.0](https://img.shields.io/badge/v1.0.0-The_Standard-blue.svg)](CHANGELOG.md)
[![402 Tests](https://img.shields.io/badge/402_tests-passing-brightgreen.svg)](#self-tests)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)
[![MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Your AI Is Dead

65% of frontier models score V = 0. Not broken — **dead**. They benchmark well, then forget everything between calls. Context injection vanishes. Corrections are lost. Every interaction starts from zero.

Here's the proof:

| Model | V-Score | Cost/M | Learns? |
|-------|--------:|-------:|:-------:|
| Claude Sonnet 4.6 | **0.000** | $3.00 | no |
| GPT-4o | **0.000** | $2.50 | no |
| Gemini 2.5 Pro | **0.000** | $1.25 | no |
| Llama 3.3 70B | **0.000** | $0.40 | no |
| Grok-4 | **0.000** | $10.00 | no |
| | | | |
| qwen3-14b | **0.019** | FREE | **yes** |
| claude-3-haiku | **0.022** | $0.25 | **yes** |
| mistral-7b | **0.016** | FREE | **yes** |

A $0 local model that learns beats a $10/M API model that forgets.

V-Score measures what benchmarks miss: **does your AI actually learn from use?**

```
V = E × W × S × B × H

Multiplicative. One zero kills everything.
That's the design.
```

---

## The Proof

GPT-4 is two generations old. GPT-5.3-Codex is the current frontier.

We wrapped GPT-4 with VOID. Let it learn for 25 rounds. Then tested both on the same 25 new tasks, scored identically.

```
GPT-4 + VOID:     avg V = 0.083    (25 rounds of accumulated experience)
GPT-5.3-Codex:    avg V = 0.064    (stateless, no memory, every call from zero)

Lift: +29.3%
```

An older, cheaper model that **learns** beats the current frontier model that **forgets**.

```bash
void proof    # Run it yourself. Seed 42. Reproducible.
```

Plug in your own models:

```python
from void_intelligence import run_proof

report = run_proof(
    old_model=my_gpt4_adapter,      # fn(prompt, system) -> response
    frontier=my_codex_adapter,
)
print(report.summary())
print(report.markdown())   # publishable report
```

---

## Quick Start

```bash
pip install void-intelligence
```

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()

# Before your LLM call
organism.inhale("Help me write an urgent email to my team")

# Your LLM does its thing
response = call_your_llm(...)

# After — record what was learned
organism.exhale(response, learnings=["urgency needs direct tone, not hedging"])

# Compound intelligence. Every call makes the next one smarter.
```

After 100 interactions, your system knows patterns a fresh install doesn't.
After 1,000 — no competitor can replicate your accumulated experience.

**Like compound interest, but for AI.**

### Claude Code Plugin

```bash
pip install void-intelligence[mcp]
```

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "void": {
      "type": "stdio",
      "command": "void",
      "args": ["mcp"]
    }
  }
}
```

Claude Code now has a living memory. Every session builds growth rings. The next session is smarter because the previous one lived. [Full setup guide](docs/claude-code-plugin.md)

```bash
void test     # 402 self-checks, zero dependencies
void spec     # The V-Score Specification
```

---

## The Full Benchmark

**March 2026. 35 models. 3 access paths. 9 families.**

### Alive (V > 0)

| Model | E | W | S | B | H | R | V-Score | Cost/M | Local |
|-------|--:|--:|--:|--:|--:|--:|--------:|-------:|:-----:|
| claude-3-haiku | .77 | .42 | 1.0 | .73 | .38 | **.25** | **0.022** | $0.25 | |
| qwen3-14b | .82 | .60 | .50 | .87 | .09 | **.99** | **0.019** | FREE | yes |
| mistral-7b | .83 | .35 | 1.0 | .57 | .57 | **.17** | **0.016** | FREE | yes |
| devstral-small | .78 | .37 | 1.0 | .65 | .58 | **.11** | **0.012** | $0.25 | |
| gemini-3.1-pro | .83 | .26 | .29 | .85 | .43 | **.47** | **0.011** | $3.50 | |
| command-r-plus | .84 | .25 | .45 | .58 | .37 | **.55** | **0.011** | $3.00 | |
| deepseek-v3 | .88 | .31 | .44 | .42 | .48 | **.39** | **0.009** | $0.28 | |
| qwen2.5-7b | .84 | .12 | 1.0 | .76 | .37 | **.27** | **0.008** | FREE | yes |
| gpt-5.3-codex | .84 | .28 | .34 | .73 | .11 | **.40** | **0.008** | $2.00 | |

### Dead (V = 0)

| Model | E | W | S | B | H | R | Cost/M |
|-------|--:|--:|--:|--:|--:|--:|-------:|
| Claude Sonnet 4.6 | .83 | .56 | .70 | .48 | .39 | 0 | $3.00 |
| GPT-4o | .84 | .55 | .49 | .44 | .72 | 0 | $2.50 |
| Gemini 2.5 Pro | .81 | .40 | .70 | .53 | .44 | 0 | $1.25 |
| Llama 3.3 70B | .84 | .45 | .91 | .68 | .72 | 0 | $0.40 |
| Grok-4 | .83 | .23 | .45 | .57 | .02 | 0 | $10.00 |

**R is the story.** GPT-4o has W=0.55. Llama has S=0.91. Individually strong. Still dead. R=0 means the model doesn't learn from organism context — and one zero kills V.

All 34 profiles: `void profiles`

---

## What VOID Adds

VOID wraps any LLM — local or API — and gives it biology:

| Capability | What it does | Module |
|------------|-------------|--------|
| **Growth Rings** | Persistent memory of what worked, failed, was learned | `organism.py` |
| **6-Axis Classification** | Keyword-based intent mapping, <0.02ms, no LLM | `organism.py` |
| **Adaptive Routing** | Pick the model that *learns best*, not scores highest | `router.py` |
| **Immune System** | 5-layer response quality gate (Swiss Cheese Model) | `immune.py` |
| **Fractal Knowledge** | Rings form a searchable graph, not a flat list | `ring_graph.py` |
| **Auto-Tuning** | Parameters converge to the Stribeck sweet spot | `tuner.py` |
| **Cross-Pollination** | Transfer knowledge between model organisms | `pollinator.py` |
| **V-Score API** | Score any model in real-time, leaderboard, badges | `api.py` |
| **Swarm Intelligence** | Distributed mesh, gossip protocol, no leader | `swarm.py` |
| **Edge Functions** | Stateless pure functions for serverless/IoT | `edge.py` |
| **Portable Export** | Self-describing JSON, compact mode, lite (<200 chars) | `portable.py` |
| **The Specification** | Formal spec, compliance checker, certification | `spec.py` |

Zero dependencies. All of it. stdlib only.

---

## 8 Geniuses, 10 Versions

Each version collides with one genius. Each collision unlocks the next.

```
v0.1  ──  IR + Organism + HexBreath                    15 tests
v0.2  ──  V-Router + 34 Profiles                       30 tests
v0.3  ──  Reason       Immune System                   47 tests
          "Swiss Cheese: holes must align to fail."
v0.4  ──  Mandelbrot   Ring Graph                      76 tests
          "Knowledge is self-similar across scales."
v0.5  ──  Stribeck     δ_opt Inference                101 tests
          "Every parameter has a friction sweet spot."
v0.6  ──  Margulis     Cross-Pollination              134 tests
          "Mitochondria were once separate organisms."
v0.7  ──  Page & Brin  V-Score API                    172 tests
          "They built a better metric, not a better engine."
v0.8  ──  Gordon       Swarm Network                  246 tests
          "No ant knows the colony's plan."
v0.9  ──  Wozniak      VOID Everywhere                302 tests
          "He made computing accessible, not better."
v1.0  ──  Berners-Lee  The Standard                   351 tests
          "Simple. Free. Useful."
```

---

## The Specification (v1.0.0)

Berners-Lee didn't build the best hypertext system. He built an **open standard** that everyone adopted because it was simple, free, and useful.

```python
from void_intelligence import check_compliance, certify, ModelCard, spec_document

# Validate any V-Score implementation against the spec
result = check_compliance(my_score_fn)
result.compliant        # True / False
result.compliance_rate  # 0.0 - 1.0

# Certify a model
cert = certify(avg_v=0.12, health_rate=0.95, checks=150)
cert.name  # "Platinum"

# Standard model card
card = ModelCard.from_scores("my-model", scores, provider="Acme")
card.to_markdown()  # publishable
card.to_json()      # machine-readable

# The spec itself — machine-readable
doc = spec_document()  # 10 sections, §1-§10
```

**Wire Format** — any system producing this JSON is V-Score compatible:

```json
{
  "V": 0.019,
  "model": "qwen3-14b",
  "status": "THRIVING",
  "components": {"E": 0.82, "W": 0.60, "S": 0.50, "B": 0.87, "H": 0.09}
}
```

**Certification:**

| Level | V | Health Rate | Checks |
|-------|--:|----------:|---------:|
| Platinum | ≥ 0.10 | ≥ 95% | ≥ 100 |
| Gold | ≥ 0.05 | ≥ 90% | ≥ 50 |
| Silver | ≥ 0.02 | ≥ 80% | ≥ 25 |
| Bronze | ≥ 0.01 | ≥ 60% | ≥ 10 |

---

## How It Works

### `.x->[]~`

Five symbols. The grammar of any dynamic system.

```
.   Atom        An irreducible fact.
x   Collision   Two atoms meet — what emerges exists in neither.
->  Projection  Collision becomes action. Always incomplete.
[]  Potential   The silence between events. Not empty — pregnant.
~   Resonance   The system feeds back into itself. Compound growth.
```

Run `void ir` to see it live.

### The Organism

```python
organism = OrganismBreather()

organism.inhale(prompt)     # Classify, prepare context
organism.exhale(response)   # Record growth ring
organism.vitals()           # Check pulse

# The organism has a heartbeat.
# It has growth rings like a tree.
# Swap the model — the memory stays.
# Your LLM is the body. VOID is the soul.
```

### The Router

```python
router = AtemRouter()
router.register_adapter("qwen3-14b", my_ollama_fn)
router.register_adapter("claude-3-haiku", my_api_fn)

# One call. VOID picks the model, injects experience, records learnings.
result = router.breathe("Analyze this forecast")
# → selected qwen3-14b (R=0.99, learns from context, FREE)
```

Models that prove themselves over time get preferred. Earned trust, not assumed capability.

### Self-Awareness

```python
from void_intelligence import lost_dimensions, circuit_breaker

@lost_dimensions("emotional_nuance", "sarcasm", "body_language")
def summarize_meeting(transcript):
    return call_llm(transcript)

# The function declares its blind spots. Queryable at runtime.
# The most humble code ever written.

@circuit_breaker("openai_api", threshold=3, timeout=30.0)
def call_openai(prompt):
    return openai.chat(...)
# 3 failures → circuit opens → heals or stays open
```

---

## CLI

```bash
void test                  # 377 self-checks
void breathe --demo        # 30-second visual demo
void ir                    # .x->[]~
void hex "text"            # 6-axis classification
void route "text"          # Model selection + reasoning
void profiles              # 34 V-Score profiles
void immune                # 5-layer quality monitor
void rings                 # Fractal ring graph
void tune "text"           # Stribeck parameter tuning
void pollinate             # Cross-pollination demo
void api [port]            # V-Score API server (default 7070)
void score                 # Score a prompt-response pair
void swarm                 # 5-node swarm demo
void edge "text"           # Stateless V-Score
void export                # Portable export (full/compact/lite)
void spec                  # The V-Score Specification
void certify [model]       # Certify against the spec
void proof                 # The Proof: old + VOID > frontier
void mcp                   # Start MCP server (Claude Code plugin)
void pulse                 # System vitals
```

## Requirements

Python ≥ 3.10. Zero runtime dependencies.

```bash
pip install void-intelligence
```

## License

MIT — [Julian Guggeis / Guggeis Research](https://guggeis.de), 2026

---

```
.   x   ->   []   ~
```

*65% of frontier AI is dead. V-Score proves it. VOID fixes it.*
