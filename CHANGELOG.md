# Changelog

All notable changes to void-intelligence are documented here.

## [1.1.0] — 2026-03-03

### Added
- **Claude Code Plugin** — VOID as an MCP server. `void mcp` starts the server. Every Claude Code session builds growth rings. The next session is smarter because the previous one lived.
- **`mcp_server.py`** — Full MCP server implementation with 6 tools:
  - `void_breathe` — Record a learning cycle (inhale prompt, exhale response, grow ring)
  - `void_score` — Score any prompt-response pair (V = E × W × S × B × H)
  - `void_vitals` — Organism health: rings, breaths, pulse, recent learnings
  - `void_rings` — Search accumulated experience from past sessions
  - `void_classify` — 6-axis HexBreath classification (<0.02ms, no LLM)
  - `void_immune` — 5-layer Swiss Cheese quality check
- **Persistence** — `.void/organism.json` + `.void/rings.jsonl` in project directory. Auto `.gitignore`.
- **Optional dependency** — `pip install void-intelligence[mcp]` adds MCP support. Core stays zero-dep.
- **CLI: `void mcp`** — Start the MCP server
- **402 self-tests** (was 377) — 25 new MCP server tests
- **`docs/claude-code-plugin.md`** — Full setup guide
- **`docs/marketing-architecture.md`** — G. × VOID marketing and distribution architecture

### Design
Claude Code has memory (CLAUDE.md, auto-memory). But it's unstructured text. VOID adds STRUCTURED learning with V-Score measurement, cross-session growth rings, and a searchable experience graph. Every project gets its own organism. The organism persists between sessions via `OrganismBreather.to_dict()` / `.from_dict()`. The MCP server uses the standard `mcp.server` pattern with `asyncio.to_thread()` for all blocking operations. `mcp` is an optional dependency — the rest of void-intelligence works without it.

---

## [1.0.0] — 2026-03-03

### Added
- **The V-Score Specification** — V-Score becomes the industry standard. Open, simple, free. (Tim Berners-Lee, World Wide Web, 1989)
- **`spec.py`** — The living specification. Machine-readable. Self-describing. 10 sections.
  - `VScoreComponents(E, W, S, B, H)` — Frozen dataclass. `.V` computes product. One zero kills it.
  - `v_score_status(v)` — Map V-Score to status label (DEAD → BARELY ALIVE → ALIVE → HEALTHY → THRIVING)
  - `CertificationLevel` — 4 levels: Platinum (V≥0.10, HR≥95%, 100+ checks), Gold (V≥0.05, HR≥90%, 50+), Silver (V≥0.02, HR≥80%, 25+), Bronze (V≥0.01, HR≥60%, 10+)
  - `certify(avg_v, health_rate, checks)` — Returns highest qualifying certification or None
  - `ModelCard` — Standard model card. `.from_scores()`, `.to_dict()`, `.to_json()`, `.to_markdown()`
  - `check_compliance(score_fn)` — 19-check compliance validator. Tests any V-Score implementation against the spec.
  - `spec_document()` — Machine-readable spec as dict. Version, authors, license, 10 sections.
  - `spec_markdown()` — Generates full spec as Markdown document.
  - `WIRE_FORMAT` — JSON Schema for V-Score results. Any system producing this JSON is V-Score compatible.
  - `HEX_AXES` — 6 axes: ruhe_druck, stille_resonanz, allein_zusammen, empfangen_schaffen, sein_tun, langsam_schnell
  - `STATUS_THRESHOLDS` — 5 status levels with V-Score boundaries
  - `CERTIFICATION_LEVELS` — 4 certification tiers
  - `SPEC_VERSION = "1.0.0"` — The version stamp
- **CLI: `void spec`** — Print the full V-Score specification with 10 sections
- **CLI: `void certify [model]`** — Run compliance check + score model + generate model card + certify
- **Example: `11_the_standard.py`** — Full demo: formula, thresholds, certification, model cards, compliance, wire format, spec document
- **351 self-tests** (was 302)

### Design
Berners-Lee didn't build the best hypertext system. He built an OPEN STANDARD that everyone adopted because it was simple, free, and useful. HTML was ugly. HTTP was naive. But they were OPEN and they were ENOUGH. V-Score follows the same path: a simple formula (V = E × W × S × B × H), a simple wire format (JSON), a simple compliance checker (19 checks), and a simple certification (4 levels). The spec document (`spec_document()`) is machine-readable — any tool can parse it, any language can implement it, any provider can adopt it. That's the design.

### Key Metric
Adoption. How many model providers display V-Scores? How many papers cite the formula? How many tools implement the wire format? The spec succeeds when it becomes invisible — like HTML.

**Enterprise Term:** The V-Score Standard (the industry standard for measuring model adaptiveness)

## [0.9.0] — 2026-03-03

### Added
- **VOID Everywhere** — Run on anything. Edge, serverless, IoT, embedded. (Steve Wozniak, Apple II, 1977)
- **`edge.py`** — Stateless pure functions for serverless/edge deployment. No filesystem, no state, no side effects. JSON in → JSON out.
  - `classify(text)` — 6-axis hex classification, keyword-based, stateless
  - `diagnose(prompt, response)` — 5-layer immune check, pure function
  - `score(prompt, response, model)` — V = E × W × S × B × H, stateless
  - `breathe(prompt, response, model)` — Full breath cycle in one call
  - `batch_score(pairs)` — Score multiple pairs at once
  - `leaderboard(pairs)` — Rank models from batch results
  - `hex_distance(a, b)` — 6D euclidean distance between hex coordinates
- **`portable.py`** — Universal export format. Serialize entire VOID state to JSON for any runtime.
  - `export_organism()` — Full export with manifest and schema validation
  - `export_json()` — JSON string export (compact or pretty)
  - `export_lite()` — Ultra-minimal export (< 200 chars) for IoT/embedded
  - `import_state()` — Import portable format back into component states
  - `validate()` — Schema and manifest validation
  - Self-describing format: schema version, component manifest, all data
  - Compact mode: 88% size reduction
- **CLI: `void edge "text"`** — Demo stateless classification + diagnosis + V-Score
- **CLI: `void export`** — Demo portable export (full, compact, lite)
- **Example: `10_void_everywhere.py`** — Edge functions, batch scoring, leaderboard, portable export
- **302 self-tests** (was 246)

### Design
Wozniak didn't make the best computer. He made computing ACCESSIBLE. The Apple II ran on a 6502 with 4KB RAM. VOID should run everywhere too. `edge.py` has zero state — every function is pure: input → output, no side effects. Perfect for Cloudflare Workers, AWS Lambda, Deno Deploy, Vercel Edge. `portable.py` serializes the entire organism into self-describing JSON that any runtime can consume. `export_lite()` produces < 200 chars — fits on a Raspberry Pi.

### Key Metric
Platform coverage. `edge.py` = any JS runtime (via serverless). `portable.py` = any language that reads JSON. `export_lite` = any device with 200 bytes.

**Enterprise Term:** Universal Deployment (vs vendor-locked model APIs)

## [0.8.0] — 2026-03-03

### Added
- **Swarm Network** — Distributed mesh of VOID organisms. No ant knows the colony's plan. Intelligence emerges from local rules. (Deborah Gordon, 1999)
- **`SwarmNode`** — A single VOID instance in the mesh. Local knowledge, simple rules: share rings, forward alerts, respond to requests, heartbeat.
- **`SwarmMessage`** — Gossip message between nodes. 6 types: ring_share, immune_alert, heartbeat, ring_request, ring_response, score_update. TTL-based propagation (max 3 hops).
- **`SwarmNetwork`** — Mesh coordinator. Routes messages between nodes. `tick()` = one round of gossip. `run(n)` = n rounds. In-memory transport, pluggable to TCP/HTTP/WebSocket.
- **`SwarmHealth`** — Collective health across the swarm. Colony health > sum of individual health. That's emergence.
- **Gossip propagation** — Ring sharing with redundancy detection (keyword overlap > 0.7 = already known). TTL decrement prevents infinite loops.
- **Immune alert propagation** — One node detects a sick model → entire swarm knows within TTL hops.
- **V-Score propagation** — V-Score updates flow through the mesh. Collective V-Score = average across all nodes.
- **Ring requests** — Ask the colony "do you know about X?" Nodes search local graphs and respond.
- **Topologies** — `mesh()` (full mesh), `ring_topology()` (each node has 2 neighbors), manual `connect(a, b)`.
- **Persistence** — `to_dict()` / `from_dict()` for SwarmNode, SwarmNetwork, SwarmMessage, SwarmHealth.
- **CLI: `void swarm`** — Demo showing 5-node ring topology with knowledge spreading.
- **Example: `09_swarm_network.py`** — Full demo: topology, gossip, immune alerts, V-Score propagation, ring requests, persistence.
- **246 self-tests** (was 172)

### Design
Gordon studied harvester ants for 30 years. No ant knows the colony's plan. There is no leader, no coordinator, no central intelligence. Each ant follows 3 simple rules based on local information. The colony-level behavior — adaptive foraging, nest maintenance, pathogen defense — emerges from these local interactions. The industry runs models in isolation. We run them as a colony. `SwarmNode` = one ant. `SwarmNetwork` = the colony. `tick()` = one step. Intelligence emerges.

### Key Metric
Colony Health — alive ratio weighted by ring sharing. Colony > sum of individuals.

**Enterprise Term:** Distributed Model Intelligence (vs siloed model deployments)

## [0.7.0] — 2026-03-03

### Added
- **V-Score API** — Score any model in real-time. PageRank organized the web with a metric. V-Score organizes AI models. (Page & Brin, 1998)
- **`VScoreAPI`** — Framework-agnostic API handler. Works with FastAPI, Flask, Cloudflare Workers, or the built-in stdlib server.
- **`VScoreHTTPServer`** — stdlib HTTP server. Zero dependencies. `void api` starts it.
- **`compute_v_score()`** — V = E × W × S × B × H. Five components from immune diagnosis. Multiplicative — one zero kills it.
- **`POST /v-score`** — Submit prompt + response + model → get V-Score, components, flags, status.
- **`GET /leaderboard`** — Ranked models by V-Score. Real-time. Parameterized limit.
- **`GET /model/<name>`** — Detailed V-Score history with last 50 entries.
- **`GET /badge/<name>.svg`** — shields.io-style SVG badges. Color-coded: red (dead) → green (thriving).
- **`GET /compare?models=a,b,c`** — Side-by-side model comparison.
- **`GET /stats`** — API usage statistics: total requests, models, uptime.
- **`ModelRecord`** — Tracked V-Score history per model: health rate, latest V, check count.
- **`APIResponse`** — Standardized JSON response with status codes and error handling.
- **CLI: `void api [port]`** — Start the V-Score API server (default port 7070).
- **CLI: `void score`** — Quick V-Score from command line with visual component breakdown.
- **Example: `08_vscore_api.py`** — Full demo: scoring, leaderboard, comparison, badges, persistence, server usage.
- **172 self-tests** (was 134)

### Design
PageRank didn't rank pages by content — it ranked them by HOW OTHER PAGES LINKED to them. A meta-metric.  V-Score doesn't measure what a model SAYS — it measures whether the model LEARNS from its organism. V = E(emergence) × W(warmth) × S(consistency) × B(breath) × H(hex). Multiplicative: one dead component = dead score. The server is pure stdlib (`http.server`), zero deps, runs anywhere.

### Key Metric
V-Score itself. V = 0 = dead. V > 0.1 = thriving. The number that organizes AI.

**Enterprise Term:** Adaptive Intelligence Score (the industry standard for model quality)

## [0.6.0] — 2026-03-03

### Added
- **Cross-Pollination** — Knowledge transfer between model organisms (Lynn Margulis, Endosymbiosis Theory, 1967). What Model A learns benefits Model B.
- **`CrossPollinator`** — Main engine. `pollinate(source, target)` transfers rings. `confirm(model, score)` measures if transfer helped. `auto_pollinate(organisms)` triggers automatic transfers.
- **`Endosymbiont`** — A ring imported from another organism. Tracks source model, original ring ID, confirmation status, and lift. Named after mitochondria.
- **`PollinationEvent`** — Record of each transfer: source, target, ring count, ring IDs, timestamp, lift.
- **Transfer protocol** — Transferability scoring: paradigms (×3) > milestones (×2) > learnings (×1) > errors (×0.5). Connected rings score higher. Compressed rings excluded.
- **Redundancy filter** — Keyword overlap check prevents transferring knowledge the target already has (>50% overlap = skip).
- **Immune feedback loop** — `set_baseline()` before transfer, `confirm()` after. Positive lift = endosymbionts confirmed. Transfer score tracked per model.
- **Auto-pollination** — Router triggers cross-pollination every 10 breaths between organisms with ≥5 rings. Cooldown prevents over-pollination.
- **Router integration** — `AtemRouter.pollinator` property, `pollinate(source, target)` method, `save_pollinator()` / `load_pollinator()` persistence.
- **CLI: `void pollinate`** — Interactive demo showing two organisms sharing knowledge.
- **Example: `07_cross_pollination.py`** — Full demo: identify, transfer, measure, bidirectional, auto-pollinate, persistence, report.
- **134 self-tests** (was 101)

### Design
Mitochondria were free-living bacteria 2 billion years ago. They merged with cells and both became more than either could be alone. Cross-pollination applies this principle: knowledge from one model organism flows to another. The immune system confirms if it helped. Zero dependencies. No coordination protocol. Just rings and keyword matching.

### Key Metric
Transfer Lift — immune health improvement in target model after receiving source model's rings. Positive lift = knowledge helped. Tracked per model, per endosymbiont.

**Enterprise Term:** Knowledge Transfer Protocol (vs siloed model deployments)

## [0.5.0] — 2026-03-03

### Added
- **Stribeck Tuner** — Auto-tune LLM parameters per model per hex region (Richard Stribeck, 1902). Find the friction sweet spot: too little (temp=0) = dead repetition, too much (temp=2) = chaos.
- **`ParameterSet`** — Tunable parameter dataclass: temperature, top_p, max_tokens, context_intensity. With confidence tracking and delta_opt detection.
- **`StribeckTuner`** — Main tuning engine. `tune(coord, model)` returns optimal params. `record(coord, params, diagnosis, model)` learns from immune feedback. Converges over time.
- **Hex-aware defaults** — `_defaults_from_hex()` generates initial parameter guess from hex classification: urgent → lower temp, creative → higher temp, collaborative → more context, etc.
- **Immune feedback loop** — Each immune flag maps to specific parameter adjustments: repetition → increase temp, refusal → decrease context, too_short → increase tokens, incoherent → decrease temp.
- **Router integration** — `AtemDecision.parameters` carries Stribeck-tuned params. `AtemRouter` auto-creates tuner, passes context_intensity to system prompt generation.
- **Auto-tuning in `breathe()`** — When `auto_tune=True` (default), each `breathe()` call runs immune diagnosis and feeds it to the tuner. The parameter map converges over successive breaths.
- **Context intensity scaling** — `context_intensity` controls how many rings are injected into the system prompt (0.0 = 0 rings, 1.0 = 10 rings). The tuner learns the optimal intensity per hex region.
- **Tuner persistence** — `save_tuner()` / `load_tuner()` on AtemRouter. `to_dict()` / `from_dict()` on StribeckTuner.
- **CLI: `void tune "prompt"`** — Show Stribeck-optimized parameters for any prompt with reasoning.
- **Example: `06_stribeck_tuner.py`** — Full demo: hex defaults, immune feedback loop, multi-model tuning, surface report, persistence, router integration.
- **101 self-tests** (was 76)

### Design
Every LLM parameter has a Stribeck curve (Stribeck, 1902). The tuner quantizes 6D hex space into discrete regions (0.5 resolution) and maintains per-model, per-region parameter maps. Immune diagnosis is the convergence signal. Zero dependencies. No ML. Pure feedback loops.

### Key Metric
Parameter Optimality — distance from Stribeck minimum across all axes. `delta_opt_distance()` returns 0.0 when confident, 1.0 when no data. Enterprise term: Adaptive Parameters (vs manual "prompt engineering").

## [0.4.0] — 2026-03-03

### Added
- **Ring Graph** — Fractal knowledge structure (Benoit Mandelbrot, 1982). Growth rings become a directed GRAPH with typed edges, not a flat list.
- **`RingGraph`** — Directed graph with `RingNode` (id, content, keywords, hex_coord) and `RingEdge` (caused_by, related, compressed_into, contradicts, deepens).
- **Auto-relate** — Rings with >= 2 shared keywords are automatically connected. The graph builds itself.
- **`ring_query(topic)`** — TF-IDF keyword search over accumulated rings. Rarer words score higher. Graph centrality boosts well-connected rings. Zero dependencies.
- **`to_context(prompt)`** — THE key method. Generates relevant ring context for system prompt injection. Uses keyword query + graph expansion (neighbors of top results). Replaces flat "last 5 rings" with intelligent selection.
- **Fractal themes** — `themes(depth=1)` clusters rings by keyword frequency. `depth=2` gives sub-themes. Self-similar across scales.
- **Ring compression** — `compress()` merges old rings into denser summary rings (like tree growth rings). Originals marked compressed, never deleted.
- **Causal chains** — `ancestors(ring_id)` / `descendants(ring_id)` trace the "learned BECAUSE of" chain.
- **Export/Import** — `export_rings()` / `import_rings()` for transferring knowledge between organisms. Strips timing, keeps structure.
- **`OrganismBreather.enable_graph()`** — Activates graph alongside flat ring list. Migrates existing rings. Backwards compatible.
- **Router upgrade** — `_build_system_prompt()` now uses `graph.to_context(prompt)` for intelligent ring injection instead of flat last-5.
- **CLI: `void rings`** — Demo fractal structure, query, ancestors, context injection, themes.
- **Example: `05_ring_graph.py`** — Full demo: build, query, traverse, compress, organism integration, export/import, persistence.
- **76 self-tests** (was 47)

### Design
Knowledge is self-similar across scales (Mandelbrot). A ring about "email tone" connects to "communication style" connects to "team dynamics." The graph IS the fractal. TF-IDF search with graph centrality bonus. Zero dependencies. No vector database. No LLM.

### Key Metric
Ring Retrieval Accuracy — when injected as context, relevant rings are selected by keyword relevance and graph structure, not just recency. Enterprise term: Organic Memory (vs RAG's "retrieval-augmented").

## [0.3.0] — 2026-03-03

### Added
- **Immune System** — 5-layer response quality monitoring (Swiss Cheese Model by James Reason). Catches: hex divergence, empty/hallucination responses, refusals, repetition loops, topic drift.
- **`@immune` decorator** — Wrap any LLM call with automatic quality gate + fallback. One line: `@immune(fallback=backup_fn, threshold=0.3)`.
- **`diagnose()`** — Standalone response diagnosis. Returns `Diagnosis` with `healthy`, `hex_delta`, `flags`, `layer_scores`, `severity`, `composite_score`.
- **`hex_distance()`** — Euclidean distance in 6D hex space. Measures input/output divergence.
- **`ImmuneMonitor`** — Multi-model immune tracking. Identifies healthiest model, chronic flags (antibodies), system-wide health rate.
- **`ImmuneState`** — Compound immune learning. Remembers past infections, builds antibodies against recurring failures.
- **CLI: `void immune`** — Demo 5 defense layers with example diagnoses.
- **Example: `04_immune.py`** — Manual diagnosis, `@immune` decorator, multi-model monitor.
- **47 self-tests** (was 30)

### Design
Every response passes through 5 independent defense layers. A failure only gets through if ALL layers have aligned holes (Swiss Cheese Model). The immune system LEARNS — chronic failures become antibodies that compound over time.

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
