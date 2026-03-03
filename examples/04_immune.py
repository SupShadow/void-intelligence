#!/usr/bin/env python3
"""Example 04: The Immune System — automatic response quality monitoring.

5 defense layers (Swiss Cheese Model by James Reason):
  1. HexDelta     — input/output classification divergence
  2. Length Guard  — empty or hallucination-length detection
  3. Refusal Shield — "I can't" / "As an AI" detection
  4. Repetition    — degenerate looping detection
  5. Coherence     — topic drift detection

Zero dependencies. Zero API keys. Just run it.
"""

from void_intelligence import diagnose, immune, ImmuneMonitor

# ── 1. Manual diagnosis ─────────────────────────────────────────

print("=== Manual Diagnosis ===\n")

# Healthy response
d = diagnose(
    "Help me write an urgent email to my team about the deadline",
    "Here is your urgent email draft about the team deadline. "
    "Dear team, I wanted to reach out about our upcoming deadline. "
    "Please help each other to submit all deliverables by Friday.",
)
print(f"Healthy: {d.healthy} | Delta: {d.hex_delta:.3f} | Score: {d.composite_score:.3f}")

# Sick: too short
d2 = diagnose("Write a comprehensive report on AI trends", "No.")
print(f"Too short: healthy={d2.healthy} | Flags: {d2.flags}")

# Sick: refusal
d3 = diagnose(
    "Help me write a speech",
    "I'm sorry, but as an AI language model, I cannot help with that request.",
)
print(f"Refusal: healthy={d3.healthy} | Flags: {d3.flags}")

# ── 2. @immune decorator ────────────────────────────────────────

print("\n=== @immune Decorator ===\n")

responses = [
    "Here is a detailed analysis of your sales data showing key trends.",
    "The quarterly revenue increased by 23% compared to last quarter.",
    "",  # Will trigger too_short
    "Your sales report covers all regions with growth metrics included.",
]
call_idx = [0]


def backup_model(prompt):
    """Fallback: always returns something reasonable."""
    return f"Backup analysis for: {prompt[:30]}... Data processed successfully."


@immune(fallback=backup_model, threshold=0.4)
def analyze(prompt):
    """Simulated model that sometimes fails."""
    resp = responses[call_idx[0] % len(responses)]
    call_idx[0] += 1
    return resp


for i in range(4):
    result = analyze("Analyze the quarterly sales report")
    print(f"  Call {i+1}: {result[:60]}...")

state = analyze.immune_state
print(f"\n  Health rate: {state.health_rate:.0%}")
print(f"  Fallbacks:  {state.fallback_calls}")
print(f"  Antibodies: {state.antibodies}")

# ── 3. Multi-model monitor ──────────────────────────────────────

print("\n=== ImmuneMonitor ===\n")

monitor = ImmuneMonitor(threshold=0.4)

# Simulate 2 models
for i in range(5):
    monitor.check(
        "model-a",
        f"Help me with task {i}",
        f"Here is comprehensive help with task {i} covering all aspects.",
    )

monitor.check("model-b", "Write a report", "No")
monitor.check("model-b", "Analyze data", "I cannot do that as an AI.")
monitor.check("model-b", "Help me", "I'm unable to assist with that request.")

report = monitor.report()
print(f"  System health: {report['system_health']:.0%}")
print(f"  Models: {report['models_monitored']}")
print(f"  Healthiest: {report['healthiest']}")

for name, data in report["models"].items():
    print(f"  {name}: {data['health_rate']:.0%} healthy ({data['total_calls']} calls)")
    if data["antibodies"]:
        print(f"    Chronic: {data['antibodies']}")

print("\nDone. The immune system protects your LLM calls automatically.")
