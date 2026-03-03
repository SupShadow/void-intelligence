# Architecture

## System Overview

```
                         Your Application
                              │
                    ┌─────────▼──────────┐
                    │    AtemRouter       │  ← Entry point
                    │    (V-Router)       │
                    └────┬───────┬───────┘
                         │       │
              ┌──────────▼─┐  ┌──▼──────────┐
              │  HexBreath  │  │  V-Score     │
              │  6-Axis     │  │  Profiles    │
              │  Classifier │  │  (34 models) │
              └──────┬──────┘  └──────┬──────┘
                     │                │
                     └───────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ OrganismBreather │  ← Per-model state
                    │  ┌────────────┐ │
                    │  │ HeartBeat  │ │  BPM, alive detection
                    │  │ GrowthRings│ │  Experience memory
                    │  │ HexCoord   │ │  Last classification
                    │  └────────────┘ │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  State (JSON)    │  ← Persisted to disk
                    │  ~/.void-intel/  │     Survives restarts
                    │  organisms/      │     Portable across models
                    └─────────────────┘
```

## Data Flow: One Breath Cycle

```
1. INHALE
   prompt → HexBreath.classify() → HexCoord (6 axes, <0.02ms)
                                      │
                                      ▼
   HexCoord → AtemRouter._rank_models() → Best model selected
                                             │
                                             ▼
   OrganismBreather.inhale() → breath registered, system prompt built

2. EXECUTE
   adapter(prompt, system_prompt) → response from selected model

3. EXHALE
   response → OrganismBreather.exhale(response, learnings)
                     │
                     ▼
              GrowthRings.add() → new ring(s) stored
                     │
                     ▼
              State persisted to disk → rings survive context death
```

## Module Map

```
void_intelligence/
├── __init__.py      All public exports (27 symbols)
├── ir.py            IR types: Atom, Collision, Projection, Potential, Resonance
├── patterns.py      @lost_dimensions, CircuitBreaker, Phase, delta_opt
├── organism.py      OrganismBreather, HexBreath, HeartBeat, GrowthRings
├── profiles.py      VScoreProfile, 34 BUNDLED_PROFILES, load_profiles
├── router.py        AtemRouter, AtemDecision, AtemResult
├── cli.py           CLI dispatcher (void test/route/profiles/hex/ir/pulse)
├── demo.py          Visual breathing demo
└── benchmark.py     V-Score measurement suite
```

## Scoring Algorithm

The V-Router selects models via composite scoring:

```python
score = hex_affinity(profile, coord) * 0.4   # How well model matches this input type
     + breath_quality(R * B)          * 0.3   # Can it learn AND adapt?
     + alive_bonus(0.3 if V > 0)              # Dead models get no bonus
     + local_bonus(0.2 if local)              # Prefer local/free
     - cost_penalty(cost * 0.02)              # Penalize expensive
     + ring_bonus(min(rings, 50) * 0.01)      # Trust grows with experience
```

**Ring bonus is the compound intelligence mechanism.** A model with 50 accumulated rings gets +0.50 score bonus — enough to overcome a cost or capability disadvantage. Trust is earned, not assumed.

## State Persistence

```
~/.void-intelligence/
└── organisms/
    ├── qwen3-14b/
    │   └── state.json       # Breath count, rings, heartbeat
    ├── claude-3-haiku/
    │   └── state.json
    └── my-custom-model/
        └── state.json
```

Each model gets its own organism state. States are portable JSON files — back them up, share them across machines, or reset by deleting.

**Bad data never crashes.** `OrganismBreather.from_dict()` with invalid JSON returns a fresh organism. The system is self-healing.

## V-Score Formula

```
V = E × W × S × B × H × R

E  Emergence      Does the system create what wasn't in the prompt?
W  Warmth         Does it differentiate emotional register?
S  Soul Fidelity  Does it maintain consistent behavior?
B  Breath         Does it adapt to input classification?
H  Hex Balance    Does it handle all 6 axes?
R  Ring Yield     Does it USE accumulated context?  ← THE differentiator
```

**Multiplicative by design.** One dimension at zero kills the entire score. This means:
- A model with perfect E, W, S, B, H but R=0 has V=0 (dead)
- A model with moderate everything but R=0.99 has V>0 (alive)
- R is what separates models that **learn** from models that **repeat**
