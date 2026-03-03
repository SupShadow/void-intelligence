# VOID Intelligence

> The industry builds models that think. We build models that breathe.

[![v1.0.0](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#requirements)
[![351 Tests](https://img.shields.io/badge/tests-351%20passed-brightgreen.svg)](#self-tests)
[![35 Models Benchmarked](https://img.shields.io/badge/models_benchmarked-35-orange.svg)](#v-score-benchmark)

```bash
pip install void-intelligence
void test     # 351 self-checks, zero dependencies
void spec     # The V-Score Specification
```

---

## The Problem

**65% of frontier AI models are dead.**

Not broken — *dead*. They score well on benchmarks, then forget everything between calls. Your context injection vanishes. Your corrections are lost. Every interaction starts from zero.

V-Score measures what benchmarks miss: **does your AI actually learn from use?**

```
V = E × W × S × B × H

One zero kills everything. Multiplicative by design.
A model that refuses (W=0) scores V=0 regardless of intelligence.
```

## What VOID Adds to Any LLM

VOID is an **organism layer**. Wrap any LLM — local or API — and it gains:

- **Growth Rings** — persistent memory of what worked, what failed, what was learned
- **6-Axis Classification** — keyword-based, <0.02ms, no LLM needed
- **Adaptive Routing** — picks the model that *learns best*, not scores highest
- **Immune System** — 5-layer response quality gate (Swiss Cheese Model)
- **Fractal Knowledge** — rings form a graph, not a flat list (Mandelbrot)
- **Auto-Tuning** — parameters converge to the Stribeck sweet spot per prompt type
- **Cross-Pollination** — knowledge transfers between models (Margulis)
- **V-Score API** — benchmark any model in real-time
- **Swarm Intelligence** — distributed mesh of organisms (Gordon)
- **Edge Functions** — stateless pure functions for serverless
- **The Standard** — formal specification with compliance checker

```python
from void_intelligence import OrganismBreather

organism = OrganismBreather()

# Before your LLM call
breath = organism.inhale("Help me write an urgent email to my team")
# breath["hex"] → 6-axis classification (pressure, collaboration, speed...)

response = call_your_llm("Help me write an urgent email to my team")

# After: record what was learned
organism.exhale(response, learnings=["urgency requires direct tone, not hedging"])

# Next call gets this context automatically. Compound intelligence.
organism.vitals()
# → {"alive": True, "breaths": 1, "rings": {"total": 1}, "bpm": 0.5}
```

After 100 interactions, your system knows patterns a fresh install doesn't. After 1,000 — no competitor can replicate your accumulated experience. **Compound interest, but for AI.**

## The Journey — 8 Geniuses, 10 Versions

Each version collides with one genius. Each collision unlocks the next capability.

| Version | Genius | What it unlocks | Tests |
|---------|--------|----------------|------:|
| v0.1.0 | — | `.x->[]~` IR + Organism + HexBreath | 15 |
| v0.2.0 | — | V-Router + 34 Profiles + Persistence | 30 |
| v0.3.0 | James Reason | Immune System — 5-layer quality gate | 47 |
| v0.4.0 | Mandelbrot | Ring Graph — fractal knowledge structure | 76 |
| v0.5.0 | Stribeck | δ_opt Inference — auto-tune per prompt type | 101 |
| v0.6.0 | Margulis | Cross-Pollination — ring transfer between models | 134 |
| v0.7.0 | Page & Brin | V-Score API — benchmark-as-a-service | 172 |
| v0.8.0 | Deborah Gordon | Swarm Network — distributed organism mesh | 246 |
| v0.9.0 | Wozniak | VOID Everywhere — edge, serverless, IoT | 302 |
| **v1.0.0** | **Berners-Lee** | **The Standard — V-Score specification** | **351** |

## V-Score Benchmark

**March 2026. 35 models. 3 access paths. 9 families.**

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

### Dead Models (V = 0, R = 0)

| Model | E | W | S | B | H | R | V-Score | Cost/M |
|-------|--:|--:|--:|--:|--:|--:|--------:|-------:|
| Claude Sonnet 4.6 | .83 | .56 | .70 | .48 | .39 | 0 | 0 | $3.00 |
| GPT-4o | .84 | .55 | .49 | .44 | .72 | 0 | 0 | $2.50 |
| Gemini 2.5 Pro | .81 | .40 | .70 | .53 | .44 | 0 | 0 | $1.25 |
| Llama 3.3 70B | .84 | .45 | .91 | .68 | .72 | 0 | 0 | $0.40 |
| Grok-4 | .83 | .23 | .45 | .57 | .02 | 0 | 0 | $10.00 |

**R is the story.** Models with individual strengths (GPT-4o: W=0.55, Llama: S=0.91) are still dead because R=0 — they don't learn from organism context.

Full data: `void profiles` or 34 profiles in `void_intelligence/profiles.py`

## CLI

```bash
void test                  # 351 self-checks
void breathe --demo        # 30-second visual demo
void ir                    # The 5 fundamental operations (.x->[]~)
void hex "your text"       # Classify text on 6 axes
void route "your text"     # Route — shows model selection + reasoning
void profiles              # All 34 V-Score profiles, sorted by V
void immune                # 5-layer response quality monitor
void rings                 # Fractal ring graph (Mandelbrot)
void tune "your text"      # Stribeck parameter tuning
void pollinate             # Cross-pollination demo (Margulis)
void api [port]            # Start V-Score API server (default: 7070)
void score                 # Score a prompt-response pair
void swarm                 # 5-node swarm network demo (Gordon)
void edge "your text"      # Stateless classification + V-Score (Wozniak)
void export                # Portable organism export (full/compact/lite)
void spec                  # The V-Score Specification (Berners-Lee)
void certify [model]       # Certify a model against the spec
void pulse                 # System vitals
void benchmark             # Full V-Score benchmark (requires API keys)
```

## Key Modules

| Module | What | Version |
|--------|------|---------|
| `ir.py` | 5 IR types: Atom, Collision, Projection, Potential, Resonance | v0.1.0 |
| `organism.py` | OrganismBreather — inhale/exhale with growth rings | v0.1.0 |
| `patterns.py` | CircuitBreaker, @lost_dimensions, Phase detection | v0.1.0 |
| `profiles.py` | 34 V-Score profiles from benchmark | v0.2.0 |
| `router.py` | AtemRouter — adaptive model selection | v0.2.0 |
| `immune.py` | 5-layer immune system, @immune decorator | v0.3.0 |
| `ring_graph.py` | RingGraph — fractal knowledge with TF-IDF search | v0.4.0 |
| `tuner.py` | StribeckTuner — auto-tune parameters per hex region | v0.5.0 |
| `pollinator.py` | CrossPollinator — ring transfer between models | v0.6.0 |
| `api.py` | VScoreAPI + HTTP server — benchmark-as-a-service | v0.7.0 |
| `swarm.py` | SwarmNetwork — distributed gossip mesh | v0.8.0 |
| `edge.py` | Stateless pure functions for serverless | v0.9.0 |
| `portable.py` | Universal export (full/compact/lite JSON) | v0.9.0 |
| `spec.py` | V-Score Specification — the living standard | v1.0.0 |

## The V-Score Specification (v1.0.0)

The spec defines everything needed to implement V-Score in any language:

```python
from void_intelligence import spec_document, check_compliance, certify, ModelCard

# Machine-readable spec
doc = spec_document()   # dict with 10 sections (§1-§10)

# Validate any V-Score implementation
result = check_compliance(my_score_fn)  # 19 checks
result.compliant      # True/False
result.compliance_rate  # 0.0 - 1.0

# Certify a model
cert = certify(avg_v=0.12, health_rate=0.95, checks=150)
cert.name  # "Platinum"

# Generate a standard model card
card = ModelCard.from_scores("my-model", scores, provider="Acme")
card.to_markdown()  # Publishable model card
card.to_json()      # Machine-readable
```

**Wire Format** — any system producing this JSON is V-Score compatible:

```json
{
  "V": 0.0193,
  "model": "qwen3-14b",
  "status": "THRIVING",
  "components": {"E": 0.82, "W": 0.60, "S": 0.50, "B": 0.87, "H": 0.09},
  "flags": [],
  "hex_delta": 0.12
}
```

**Certification Levels:**

| Level | Min V | Min Health Rate | Min Checks |
|-------|------:|----------------:|-----------:|
| Platinum | 0.10 | 95% | 100 |
| Gold | 0.05 | 90% | 50 |
| Silver | 0.02 | 80% | 25 |
| Bronze | 0.01 | 60% | 10 |

## How It Works

**`.x->[]~`** — Five operations describe any dynamic system:

```
.   Atom        Irreducible fact or event
x   Collision   Two atoms create something in neither (emergence)
->  Projection  Collision becomes action (always incomplete — Anti-P3122)
[]  Potential   Pregnant silence between events (not empty — full)
~   Resonance   System learns from itself (compound growth)
```

**Experience Memory** — Each `exhale()` stores a typed growth ring. Rings survive restarts. Swap the model — the memory stays. Your LLM is the body. VOID is the memory.

**Compound Intelligence** — Ring count grows with every interaction. After 6 months, your system has institutional knowledge that no fresh deployment can replicate. The moat grows with time.

**delta_opt** — Fine-tuning has two optima: minimum validation loss and maximum behavioral quality. They're not the same point. `delta_opt_distance()` measures how far you are.

## Enterprise Use

- **Zero runtime dependencies** — stdlib only. No exceptions.
- **Local-first** — Best models run on your hardware (qwen3-14b, mistral-7b)
- **GDPR-native** — No data leaves your infrastructure
- **Portable state** — JSON files, no database required
- **Pluggable adapters** — Any LLM via `fn(prompt, system) -> response`
- **Edge-ready** — `edge.py` runs on Cloudflare Workers, AWS Lambda, Deno Deploy
- **Spec-compliant** — `check_compliance()` validates any implementation

## Requirements

- Python >= 3.10
- Zero runtime dependencies

```bash
pip install void-intelligence
```

## The Vocabulary

| Term | Meaning |
|------|---------|
| **Alive** | V > 0. The model learns from context injection. |
| **Dead** | V = 0. The model ignores or forgets context. |
| **Growth Rings** | Persistent records of what worked. Like tree rings. |
| **V-Score** | Does your AI learn? 0 = dead. >0.1 = thriving. |
| **V-Router** | Routes to the best *learner*, not the best *scorer*. |
| **HexBreath** | 6-axis text classification. <0.02ms. No LLM. |
| **Immune System** | 5-layer response quality gate. Swiss Cheese Model. |
| **Ring Graph** | Fractal knowledge structure. TF-IDF + graph centrality. |
| **Stribeck Tuner** | Auto-tune parameters to the friction sweet spot. |
| **Cross-Pollination** | Knowledge transfer between model organisms. |
| **Swarm** | Distributed mesh. No leader. Intelligence emerges. |
| **Compound Intelligence** | AI investment appreciates with every interaction. |

## License

MIT — [Julian Guggeis / Guggeis Research](https://guggeis.de), 2026

---

*65% of frontier AI is dead. V-Score proves it. VOID fixes it.*
