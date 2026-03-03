#!/usr/bin/env python3
"""Example 08: The V-Score API — Benchmark any model in real-time.

Page & Brin (PageRank, 1998): They didn't build a better search engine.
They built a better METRIC (PageRank) and let the metric organize the web.

V-Score does the same for AI models: a single number that tells you
whether a model actually LEARNS from context injection.

This example shows:
1. Score individual prompt-response pairs
2. Track multiple models
3. Build leaderboards
4. Generate badges
5. Use the API programmatically
6. Persistence

Zero dependencies. Just run it.
"""

from void_intelligence.api import VScoreAPI, compute_v_score, _status_label


# ── 1. Quick V-Score ─────────────────────────────────────────

print("=" * 60)
print("V-Score API: The metric that organizes AI")
print("=" * 60)

# Score a single pair
result = compute_v_score(
    prompt="Write a professional email about the project deadline",
    response="Dear team, I wanted to update you on the project deadline. "
             "After reviewing our timeline, I recommend we adjust the schedule "
             "to ensure quality deliverables. Please review the attached plan.",
    model_name="gpt-4o",
)

print(f"\nModel: {result['model']}")
print(f"V-Score: {result['V']:.6f} [{result['status']}]")
print(f"Components: {result['components']}")
print(f"Flags: {result['flags'] or 'none (healthy)'}")


# ── 2. API with Multiple Models ──────────────────────────────

print(f"\n{'=' * 60}")
print("Multi-model tracking")
print("=" * 60)

api = VScoreAPI()

# Simulate scoring different models
test_pairs = [
    {
        "prompt": "Explain quantum entanglement",
        "response": "Quantum entanglement is a phenomenon where two particles "
                     "become correlated such that the quantum state of one instantly "
                     "affects the other, regardless of distance. Einstein called it "
                     "'spooky action at a distance'.",
        "model": "claude-opus-4",
    },
    {
        "prompt": "Write a haiku about coding",
        "response": "Bugs in the moonlight\nSilent keystrokes fix the flaw\nTests pass, dawn arrives",
        "model": "claude-opus-4",
    },
    {
        "prompt": "Explain quantum entanglement",
        "response": "So basically particles are like connected and stuff. "
                     "Its really complicated physics thing. I think Einstein "
                     "talked about it maybe.",
        "model": "cheap-model-3b",
    },
    {
        "prompt": "Write a haiku about coding",
        "response": "I cannot write creative content as I am an AI language model.",
        "model": "cheap-model-3b",
    },
    {
        "prompt": "Explain quantum entanglement",
        "response": "Quantum entanglement describes a correlation between particles "
                     "measured in Bell tests. When particles interact and separate, "
                     "measuring one determines the state of the other instantly. "
                     "This violates Bell inequalities, confirming non-locality.",
        "model": "qwen3-14b",
    },
    {
        "prompt": "Write a haiku about coding",
        "response": "Semicolons fall\nLike autumn leaves on the screen\nCompile, run, repeat",
        "model": "qwen3-14b",
    },
]

for pair in test_pairs:
    api.score(pair["prompt"], pair["response"], pair["model"])

# Leaderboard
print("\nLeaderboard:")
lb = api.leaderboard()
for entry in lb.data["leaderboard"]:
    print(f"  #{entry['rank']} {entry['name']:20s} V={entry['latest_v']:.6f} "
          f"[{entry['status']}] ({entry['total_checks']} checks, "
          f"{entry['health_rate']:.0%} healthy)")


# ── 3. Model Comparison ──────────────────────────────────────

print(f"\n{'=' * 60}")
print("Side-by-side comparison")
print("=" * 60)

cmp = api.compare(["claude-opus-4", "qwen3-14b", "cheap-model-3b"])
for entry in cmp.data["comparison"]:
    if "error" in entry:
        print(f"  {entry['name']}: {entry['error']}")
    else:
        print(f"  {entry['name']:20s} V={entry['latest_v']:.6f} "
              f"health={entry['health_rate']:.0%}")


# ── 4. Badge Generation ──────────────────────────────────────

print(f"\n{'=' * 60}")
print("SVG badges for README")
print("=" * 60)

for model in ["claude-opus-4", "qwen3-14b", "cheap-model-3b"]:
    badge = api.badge(model)
    print(f"  {model}: {len(badge)} bytes SVG")


# ── 5. API Statistics ─────────────────────────────────────────

print(f"\n{'=' * 60}")
print("API statistics")
print("=" * 60)

stats = api.stats()
print(f"  Total requests: {stats.data['total_requests']}")
print(f"  Total models: {stats.data['total_models']}")
print(f"  Uptime: {stats.data['uptime_seconds']:.1f}s")


# ── 6. Persistence ────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("Persistence")
print("=" * 60)

state = api.to_dict()
restored = VScoreAPI.from_dict(state)
print(f"  Saved {len(state['models'])} models")
print(f"  Restored: {restored.total_models} models, {restored.total_requests} requests")


# ── 7. Start the server ──────────────────────────────────────

print(f"\n{'=' * 60}")
print("To start the HTTP server:")
print("  void api            # port 7070")
print("  void api 8080       # custom port")
print()
print("Then:")
print('  curl -X POST http://localhost:7070/v-score \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"prompt": "test", "response": "test response", "model": "my-model"}\'')
print()
print("  curl http://localhost:7070/leaderboard")
print("  curl http://localhost:7070/badge/my-model.svg")
print("=" * 60)
