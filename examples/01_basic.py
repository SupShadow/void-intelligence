"""
Example 1: Basic — Organism + HexBreath in 20 lines.

No API keys needed. No dependencies. Just Python 3.10+.

    python3 examples/01_basic.py
"""
from void_intelligence import OrganismBreather, HexBreath

# 1. Classify any text on 6 axes (no LLM, <0.02ms)
hex_breath = HexBreath()
coord = hex_breath.classify("Help me write an urgent email to my team")

print(f"Pressure:  {coord.ruhe_druck:+.2f}")       # +1.0 (urgent)
print(f"Together:  {coord.allein_zusammen:+.2f}")    # +1.0 (team)
print(f"Create:    {coord.empfangen_schaffen:+.2f}")  # +1.0 (writing)
print(f"Balance:   {coord.balance:.2f}")             # How centered is this request?

# 2. Build an organism that remembers
organism = OrganismBreather()

# Inhale: register the input
organism.inhale("Help me write an urgent email to my team")

# Your LLM call goes here — any model, any API
response = "Subject: Action Required — Q3 Targets\n\nTeam, ..."

# Exhale: record what was learned
organism.exhale(response, learnings=[
    "urgency requires direct tone, not hedging",
    "team context means acknowledging all stakeholders",
])

# Check vitals
v = organism.vitals()
print(f"\nAlive:   {v['alive']}")
print(f"Breaths: {v['breaths']}")
print(f"Rings:   {v['rings']['total']}")  # 2 learnings = 2 growth rings

# 3. Persist state (survives restarts, model swaps)
state = organism.to_dict()
# Save to JSON file, load in next session with OrganismBreather.from_dict(state)
# The memory stays. The model is replaceable.
print(f"\nState keys: {list(state.keys())}")
print(f"Rings in state: {len(state['rings'])}")
