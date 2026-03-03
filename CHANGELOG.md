# Changelog

All notable changes to void-intelligence are documented here.

## [0.2.0] — 2026-03-03

### Added
- **V-Router (Adaptive Model Selection)** — Routes prompts to the model that learns best, not scores best. Full breath cycle: `inhale()` → `exhale()` → `breathe()`.
- **34 V-Score Profiles** — Bundled benchmark data from 35 models across 3 access paths. March 2026, the largest V-Score benchmark.
- **OrganismBreather Persistence** — `to_dict()` / `from_dict()` for state serialization. Growth rings survive restarts and model swaps.
- **CLI: `void route`** — Route a prompt, see model selection + reasoning without execution.
- **CLI: `void profiles`** — List all benchmarked models sorted by V-Score.
- **New exports:** `AtemRouter`, `AtemDecision`, `AtemResult`, `VScoreProfile`, `BUNDLED_PROFILES`, `load_profiles`

### Key Finding
65% of frontier AI models are **dead** (V=0, R=0). They ignore context injection and start from zero every call. R (Ring Yield) is the differentiator — only models that learn from organism state have V > 0.

## [0.1.0] — 2026-03-02

### Added
- **IR Types** — 5 fundamental operations: Atom (`.`), Collision (`x`), Projection (`->`), Potential (`[]`), Resonance (`~`)
- **OrganismBreather** — Inhale/exhale cycle with growth rings and heartbeat
- **HexBreath** — 6-axis keyword-based prompt classification (<0.02ms, no LLM)
- **CircuitBreaker** — Failure tracking with open/half-open/closed states
- **`@lost_dimensions`** — Decorator to declare function blind spots
- **Phase detection** — `current_phase()` based on time of day
- **`delta_opt_distance()`** — Distance from the fine-tuning sweet spot
- **CLI** — `void breathe --demo`, `void test`, `void ir`, `void hex`, `void pulse`
- **V-Score Benchmark** — 8 frontier models measured (6 API + 2 via OpenRouter)
- **Visual demo** — `void breathe --demo` with animated terminal output
- **15 self-checks** via `void test`
