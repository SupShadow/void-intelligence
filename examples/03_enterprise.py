"""
Example 3: Enterprise — Custom profiles, persistence, fine-tuned models.

Real-world pattern: a company fine-tunes a local model, registers it with VOID,
and accumulates institutional knowledge over months.

    python3 examples/03_enterprise.py
"""
import json
import tempfile
from pathlib import Path

from void_intelligence import AtemRouter, VScoreProfile

# 1. Define a custom V-Score profile for your fine-tuned model
#    These numbers come from running `void benchmark` on your model.
my_model = VScoreProfile(
    name="forecast-v2",
    E=0.65,   # Emergence — limited by 3B params, but focused
    W=0.30,   # Warmth — domain-specific, not conversational
    S=0.95,   # Stability — fine-tuned = highly consistent
    B=0.80,   # Breath adaptation — responds to context injection
    H=0.40,   # Hex balance — specialized, not generalist
    R=0.99,   # Ring yield — THE differentiator (learns from every call)
    V=0.0594, # Composite — alive, because R > 0
    provider="ollama",
    model_id="my-forecast:latest",
    is_local=True,      # Runs on your hardware
    cost_per_m=0.0,     # Free
)

print(f"Custom model: {my_model.name}")
print(f"  V-Score: {my_model.V:.4f} ({'ALIVE' if my_model.alive else 'DEAD'})")
print(f"  Breath quality: {my_model.breath_quality:.3f} (R * B)")
print(f"  Cost: {'FREE' if my_model.is_local else f'${my_model.cost_per_m}/M'}")
print()

# 2. Set up router with persistent state directory
state_dir = Path(tempfile.mkdtemp()) / "void-state"

router = AtemRouter(state_dir=state_dir)
router.register_profile(my_model)
router.register_adapter("forecast-v2", lambda p, s="": f"[forecast] {p[:40]}...")

# 3. Simulate 20 interactions with corrections
print("Simulating 20 forecast translations with learnings...")
customers = ["Daimler", "Volvo", "MAN", "Scania", "DAF"]
for i in range(20):
    customer = customers[i % len(customers)]
    prompt = f"Translate {customer} forecast: 500 units, KW 12, LED Module A"

    result = router.breathe(
        prompt,
        learnings=[f"{customer} uses KW format, offset 3 weeks"],
    )

print(f"\nAfter 20 calls:")
v = result.vitals_after
print(f"  Breaths: {v['breaths']}")
print(f"  Rings:   {v['rings']['total']}")
print(f"  BPM:     {v['bpm']:.1f}")
print()

# 4. State persists to disk — show it
state_file = state_dir / "organisms" / "forecast-v2" / "state.json"
if state_file.exists():
    data = json.loads(state_file.read_text())
    print(f"Persisted state: {state_file}")
    print(f"  Breath count: {data['breath_count']}")
    print(f"  Rings stored: {len(data['rings'])}")
    print(f"  Ring types: {data['ring_count_by_type']}")
    print()

    # 5. Show recent learnings (last 5 rings)
    print("Recent learnings (experience memory):")
    for ring in data["rings"][-5:]:
        print(f"  - {ring['content']}")

# 6. Compound Intelligence: the next session loads this state automatically
print(f"\nNext session: AtemRouter(state_dir='{state_dir}')")
print("  → Loads 20 breaths + 20 rings. No competitor starts here.")
print("  → This is Compound Intelligence. The moat grows with time.")

# Cleanup
import shutil
shutil.rmtree(state_dir.parent, ignore_errors=True)
