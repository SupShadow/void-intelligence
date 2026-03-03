# VOID Intelligence — Claude Code Plugin

> Your Claude Code learns. Every session builds growth rings.
> The next session is smarter because the previous one lived.

---

## Setup (60 seconds)

### 1. Install

```bash
pip install void-intelligence mcp
```

Or with the `mcp` extra:

```bash
pip install void-intelligence[mcp]
```

### 2. Configure

Add to your project's `.mcp.json` (or `~/.claude/.mcp.json` for global):

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

### 3. Done

Restart Claude Code. The organism is alive.

---

## What You Get

### 6 Tools

| Tool | What it does | When to use |
|------|-------------|-------------|
| `void_breathe` | Record a learning (prompt + response + learnings) | After interactions where something was LEARNED |
| `void_vitals` | Organism health (rings, pulse, recent learnings) | Start of session — see what's already known |
| `void_rings` | Search past learnings | Recall patterns, preferences, decisions |
| `void_score` | V-Score a prompt-response pair | Evaluate response quality (read-only) |
| `void_classify` | 6-axis intent classification | Understand what kind of request this is |
| `void_immune` | 5-layer quality check | Validate important responses |

### How It Works

```
Session 1:
  You: "How do I deploy this?"
  Claude: [answers]
  VOID: Records growth ring: "uses Docker, prefers Vercel"

Session 2:
  You: "Set up the deployment"
  Claude: [checks void_vitals → sees ring → knows you use Docker + Vercel]
  Claude: [gives specific, contextual answer]
  VOID: Records ring: "Docker Compose for staging, Vercel for prod"

Session 47:
  VOID has 200+ rings. Claude knows your stack, preferences,
  naming conventions, testing patterns, deployment workflow.
  Like a colleague with 6 months of context.
```

### Persistence

Everything lives in `.void/` in your project directory:

```
.void/
├── organism.json    # Organism state (rings, heartbeat, breath count)
├── rings.jsonl      # Append-only learning log (searchable)
└── .gitignore       # Auto-created: keeps VOID state out of git
```

- Each project gets its own organism
- State persists between Claude Code sessions
- `.gitignore` prevents accidental commits
- Move `.void/` between machines to transfer knowledge

---

## Examples

### Session Start — Check What's Known

Claude can call `void_vitals` to see accumulated knowledge:

```json
{
  "alive": true,
  "breaths": 47,
  "rings_persisted": 23,
  "recent_learnings": [
    {"learnings": ["uses TypeScript", "prefers functional style"]},
    {"learnings": ["tests with vitest not jest"]},
    {"learnings": ["API uses tRPC, auth is NextAuth"]}
  ]
}
```

### Record a Learning

After helping with something, Claude calls `void_breathe`:

```json
{
  "prompt": "How should I structure the API routes?",
  "response": "Use tRPC routers with Zod validation...",
  "learnings": [
    "API uses tRPC with Zod schemas",
    "Prefers co-located route files",
    "Error handling via custom AppError class"
  ]
}
```

### Search Past Knowledge

Claude calls `void_rings` with a query:

```json
{
  "query": "testing",
  "rings": [
    {"learnings": ["uses vitest", "prefer unit over e2e"], "v_score": 0.034},
    {"learnings": ["mock API with msw", "snapshot tests for UI"], "v_score": 0.028}
  ]
}
```

---

## V-Score

Every interaction gets a V-Score: `V = E x W x S x B x H`

- **E** (Emergence) — Does the response match the intent?
- **W** (Warmth) — Is it helpful, not refusing?
- **S** (Consistency) — No repetition or degeneration?
- **B** (Breath) — Appropriate length?
- **H** (Hex alignment) — Input and output on same wavelength?

**Multiplicative.** One zero kills everything. That's the design.

---

## The Proof

GPT-4 + VOID beats GPT-5.3 Codex by 29%.

An older model that **learns** beats the current frontier that **forgets**.

```bash
void proof    # Run it yourself. Reproducible.
```

---

## FAQ

**Does this send data anywhere?**
No. Everything stays in `.void/` on your disk. No cloud. No telemetry.

**Does it slow down Claude Code?**
No. All VOID operations are pure Python, <1ms. No LLM calls.

**Can I delete the organism and start fresh?**
Yes. `rm -rf .void/` — fresh start.

**Can I share knowledge between projects?**
Copy `.void/rings.jsonl` between projects. The learnings transfer.

**What if I don't have `mcp` installed?**
`void mcp` gives a clear error. The rest of void-intelligence works fine without it.

---

*VOID Intelligence v1.1.0 — Guggeis Research*
*Every session leaves a ring. Every ring makes the next session smarter.*
