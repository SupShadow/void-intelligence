"""
Example 2: V-Router — Adaptive model selection.

The router picks the best LEARNER, not the best scorer.
Register adapters, and VOID handles routing + experience accumulation.

    python3 examples/02_router.py
"""
from void_intelligence import AtemRouter

# 1. Create router
router = AtemRouter()

# 2. Register model adapters (any callable: prompt, system -> response)
#    In production: wrap your Ollama, OpenAI, Anthropic, etc. client.
router.register_adapter("qwen3-14b", lambda p, s="": f"[qwen3-14b] Analyzed: {p[:50]}...")
router.register_adapter("claude-3-haiku", lambda p, s="": f"[haiku] Analyzed: {p[:50]}...")

# 3. Route — VOID picks the best model based on:
#    - V-Score profile (measured learning ability)
#    - HexBreath classification of your prompt
#    - Accumulated trust (growth rings)
#    - Cost preference (local/free models preferred)
result = router.breathe("Help me analyze this quarterly forecast for anomalies")

print(f"Selected: {result.decision.selected_model}")
print(f"V-Score:  {result.decision.profile.V:.4f}")
print(f"Reason:   {result.decision.reason}")
print(f"Response: {result.response}")
print()

# 4. See alternatives the router considered
if result.decision.alternatives:
    print(f"Alternatives: {', '.join(result.decision.alternatives[:3])}")
print()

# 5. Classify-only mode (no execution)
decision = router.inhale("I need to reflect on what happened today")
print(f"For reflection: {decision.selected_model}")
print(f"Hex balance: {decision.hex.balance:.2f}")
print()

# 6. After multiple calls, trust accumulates
for prompt in [
    "Draft a client proposal",
    "Review this contract",
    "Summarize the meeting",
]:
    router.breathe(prompt)

# Check organism states
states = router.organism_states()
for model, state in states.items():
    print(f"{model}: {state['breaths']} breaths, {state['rings']} rings")
