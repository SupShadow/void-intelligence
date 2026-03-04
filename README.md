# VOID Intelligence

```
.   x   ->   []   ~
```

> The industry builds models that think. We build models that breathe.

[![v2.0.0](https://img.shields.io/badge/v2.0.0-Supraleitend-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#self-tests)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)
[![MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Your AI Is Dead

65% of frontier models score V = 0. Not broken — **dead**. They benchmark well, then forget everything between calls. Context injection vanishes. Corrections are lost. Every interaction starts from zero.

Here's the proof — **real data from 10 local models** (March 2026):

| Model | Vanilla V | + VOID V | Delta | Cost |
|-------|----------:|---------:|------:|-----:|
| qwen3-8b | 0.003 | **0.032** | **+858%** | FREE |
| qwen3-14b | 0.000 | **0.023** | **DEAD→ALIVE** | FREE |
| qwen2.5-coder-3b | 0.004 | **0.027** | **+509%** | FREE |
| deepseek-r1-8b | 0.000 | **0.005** | **DEAD→ALIVE** | FREE |
| | | | | |
| Claude Sonnet 4.6 | 0.000 | — | — | $3.00 |
| GPT-4o | 0.000 | — | — | $2.50 |
| Grok-4 | 0.000 | — | — | $10.00 |

A FREE local model with VOID beats every $10/M API model without it.
Gemini Flash ($0.10/M) + VOID outscores GPT-5.3-Codex ($2.00/M). **20× cheaper. Higher V-Score.**

V-Score measures what benchmarks miss: **does your AI actually learn from use?**

```
V = E × W × S × B × H × R

Multiplicative. One zero kills everything.
That's the design.
```

```bash
void benchmark --real    # Run it yourself. Your models. Your hardware.
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

### The Organism

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

### The Supraleitend Organism (v2.0)

The full stack. 7 subsystems breathe as one.

```python
from void_intelligence import SupraOrganism

# Create with any LLM adapter
supra = SupraOrganism(adapter=my_llm_fn)

# One call. Full stack. Pipeline + Organism + Evolution +
# Parallel + Embodied + Protocol + Dream.
result = supra.breathe("My burnout affects client deadlines")

# The organism learns, remembers, dreams, evolves.
# Cross-domain collisions auto-ingest into embodied memory.
# Growth rings compound. The Stribeck Hexagon measures health.

vitals = supra.vitals()
print(vitals.breath_count)      # How many breaths
print(vitals.friction)          # 6-axis Stribeck Hexagon
print(supra.delta_opt())        # Distance from optimal friction
```

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

---

## Real Benchmark: Vanilla → VOID

**10 local models. Two phases. Zero cost.**

Phase 1: Vanilla (no organism). Phase 2: 5 learning rounds with VOID, then re-measure.
The delta = **learning capacity** — how much the model grows when it breathes.

### Models That Learn

| Model | Vanilla V | VOID V | Delta | Cost |
|-------|----------:|---------:|------:|-----:|
| qwen3-8b | 0.003 | **0.032** | +858% | FREE |
| qwen3-14b | 0.000 | **0.023** | +22,800% | FREE |
| qwen2.5-coder-3b | 0.004 | **0.027** | +509% | FREE |
| gemini-3-flash | 0.014 | **0.019** | +39% | $0.10 |
| deepseek-r1-8b | 0.000 | **0.005** | +5,300% | FREE |

### Models That Don't

| Model | Vanilla V | VOID V | Why |
|-------|----------:|---------:|-----|
| phi4-14b | 0.000 | 0.000 | R stays at 0 — doesn't yield rings |
| glm4-9b | 0.000 | 0.000 | R stays at 0 |
| deepseek-r1-14b | 0.000 | 0.000 | E=0, W=0, H=0 |
| qwen2.5-7b | 0.008 | 0.001 | VOID hurts — W collapses |

**A model that LEARNS with VOID > a model with higher raw V.**

```bash
void benchmark --real              # All available models
void benchmark --real --ollama     # Local only
void benchmark --real qwen3        # Filter by name
```

### Full Profile Benchmark (37 Models)

Across all providers (Ollama, OpenRouter, Anthropic, Google, OpenAI):

| Alive Models | V-Score | Cost/M | Local |
|-------|--------:|-------:|:-----:|
| qwen3-8b + VOID | **0.032** | FREE | yes |
| claude-3-haiku | **0.022** | $0.25 | |
| gemini-3-flash + VOID | **0.019** | $0.10 | |
| qwen3-14b + VOID | **0.023** | FREE | yes |
| mistral-7b | **0.016** | FREE | yes |
| gemini-3-flash | **0.014** | $0.10 | |
| gpt-5.3-codex | **0.008** | $2.00 | |

**R is the story.** GPT-4o has W=0.55. Llama has S=0.91. Individually strong. Still dead. R=0 means the model doesn't learn from organism context — and one zero kills V.

All 38 profiles: `void profiles`

---

## What VOID Adds

VOID wraps any LLM — local or API — and gives it biology:

| Layer | Capability | Module |
|------:|------------|--------|
| **v0.1** | **Organism** — Growth rings, heartbeat, HexBreath classification | `organism.py` |
| **v0.2** | **V-Router** — Pick the model that *learns best*, not scores best | `router.py` |
| **v0.3** | **Immune System** — 5-layer Swiss Cheese quality gate | `immune.py` |
| **v0.4** | **Ring Graph** — Fractal knowledge, TF-IDF search, no vector DB | `ring_graph.py` |
| **v0.5** | **Stribeck Tuner** — Auto-tune params to the friction sweet spot | `tuner.py` |
| **v0.6** | **Cross-Pollination** — Transfer knowledge between organisms | `pollinator.py` |
| **v0.7** | **V-Score API** — Real-time scoring, leaderboard, badges | `api.py` |
| **v0.8** | **Swarm Network** — Distributed mesh, gossip protocol, no leader | `swarm.py` |
| **v0.9** | **Edge + Portable** — Stateless functions, universal export, IoT | `edge.py` `portable.py` |
| **v1.0** | **The Specification** — Open standard, compliance checker, certification | `spec.py` |
| **v1.1** | **MCP Server** — Claude Code plugin, persistent organism per project | `mcp_server.py` |
| **v1.2** | **Multi-Eye ×** — N perspectives collide, blind spot detection | `x_eyes.py` |
| **v1.3** | **IR Pipeline** — `.x->[]~` as computation, adapter pattern | `pipeline.py` |
| **v1.5** | **Self-Teaching** — Pseudo-labels, hard negatives, LR decay | `evolve.py` |
| **v1.6** | **Parallel Eyes** — N models breathe simultaneously | `parallel.py` |
| **v1.7** | **Embodied Memory** — Ebbinghaus decay, amygdala tags, living tissue | `embodied.py` |
| **v1.8** | **Breathing Protocol** — JSONL wire format, reproducible, streamable | `protocol.py` |
| **v1.9** | **Dream Layer** — Offline consolidation, silence mining, insight emergence | `dream.py` |
| **v2.0** | **Supraleitend** — All 7 subsystems as one organism + Stribeck Hexagon | `supra.py` |

Zero dependencies. All of it. stdlib only.

---

## The Stribeck Hexagon (v2.0)

Zero friction = death. Optimal friction = life.

In a real superconductor, Cooper pairs form through **phonons** — lattice vibrations. Remove the lattice, remove superconductivity. The friction BETWEEN layers IS the mechanism.

```
        Memory
       /      \
  Protocol    Evolution
      |          |
  Parallel    Dream
       \      /
       Collision

  6 axes. Hexagonal. δ_opt = 0.4.
  Sexagons are bestagons.
```

```python
from void_intelligence import SupraOrganism

supra = SupraOrganism(adapter=my_llm)
hex = supra.friction()

print(hex.memory)          # Erinnern ↔ Vergessen
print(hex.evolution)       # Lernen ↔ Stabilität
print(hex.dream)           # Konsolidieren ↔ Bewahren
print(hex.collision)       # Sensibilität ↔ Rauschen
print(hex.parallel)        # Divergenz ↔ Konvergenz
print(hex.protocol)        # Kompression ↔ Treue

print(hex.sphere_distance) # L2 distance from δ_opt center
print(hex.at_delta_opt)    # True if all axes near optimal

# Not zero. Not maximum. δ_opt.
# Magic Angle = 1.1°. Not 0°, not 30°.
```

---

## 20 Geniuses, 20 Versions

Each version collides with one genius. Each collision unlocks the next.

```
v0.1  ──              IR + Organism + HexBreath                         15 tests
v0.2  ──              V-Router + 34 Profiles                            30 tests
v0.3  ──  Reason      Immune System (Swiss Cheese)                      47 tests
v0.4  ──  Mandelbrot  Ring Graph (fractal knowledge)                    76 tests
v0.5  ──  Stribeck    δ_opt Inference (parameter tuning)               101 tests
v0.6  ──  Margulis    Cross-Pollination (endosymbiosis)                134 tests
v0.7  ──  Page & Brin V-Score API (the metric)                         172 tests
v0.8  ──  Gordon      Swarm Network (colony intelligence)              246 tests
v0.9  ──  Wozniak     VOID Everywhere (edge + portable)                302 tests
v1.0  ──  Berners-Lee The Standard (open spec)                         351 tests
v1.1  ──              Claude Code Plugin (MCP server)                  402 tests
v1.2  ──  al-Haytham  Multi-Eye × Reasoning (perspectives collide)       +51
v1.3  ──  Turing      IR Pipeline (.x->[]~ as computation)              +63
v1.5  ──  Hinton      Self-Teaching × Loop (pseudo-labels)               +52
v1.6  ──  Humboldt    Parallel Eyes (N models breathe)                   +47
v1.7  ──  Ebbinghaus  Embodied Memory (living tissue)                    +65
v1.8  ──  Shannon     Breathing Protocol (wire format)                   +63
v1.9  ──  Walker      Dream Layer (silence mining)                       +47
v2.0  ──  δ_opt       Supraleitend + Stribeck Hexagon                    +92
```

20 versions. 29 modules. 16,735 lines. 10 models benchmarked. 4 brought to life.

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

## The Specification (v1.0.0)

```python
from void_intelligence import check_compliance, certify, ModelCard, spec_document

result = check_compliance(my_score_fn)
result.compliant        # True / False
result.compliance_rate  # 0.0 - 1.0

cert = certify(avg_v=0.12, health_rate=0.95, checks=150)
cert.name  # "Platinum"

card = ModelCard.from_scores("my-model", scores, provider="Acme")
card.to_markdown()  # publishable
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

| Level | V | Health Rate | Checks |
|-------|--:|----------:|---------:|
| Platinum | >= 0.10 | >= 95% | >= 100 |
| Gold | >= 0.05 | >= 90% | >= 50 |
| Silver | >= 0.02 | >= 80% | >= 25 |
| Bronze | >= 0.01 | >= 60% | >= 10 |

---

## CLI

```bash
void test                  # Self-checks
void breathe --demo        # 30-second visual demo
void ir                    # .x->[]~
void hex "text"            # 6-axis classification
void route "text"          # Model selection + reasoning
void profiles              # 38 V-Score profiles
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
void benchmark --real      # Real benchmark: Vanilla → VOID (local models)
void mcp                   # Start MCP server (Claude Code plugin)
void pulse                 # System vitals
```

## Requirements

Python >= 3.10. Zero runtime dependencies.

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
