#!/usr/bin/env python3
"""Example 06: The Stribeck Tuner — Auto-tuning LLM parameters.

Richard Stribeck (Stribeck Curve, 1902): Every parameter has a sweet spot.
Too little friction (temp=0) = dead repetition. Too much (temp=2) = chaos.
The MINIMUM between these extremes is the sweet spot = delta_opt.

The Stribeck Tuner finds this minimum for ALL parameters
(temperature, top_p, max_tokens, context_intensity) across ALL hex regions,
using immune system feedback as the convergence signal.

Zero dependencies. Just run it.
"""

from void_intelligence import StribeckTuner, ParameterSet, HexBreath, diagnose
from void_intelligence.organism import HexCoord
from void_intelligence.tuner import _defaults_from_hex

# ── 1. Hex-aware defaults ───────────────────────────────────────

print("=== Hex-Aware Defaults ===\n")

hex_breath = HexBreath()

prompts = [
    "Help me write an urgent email to my team about the deadline",
    "Write a creative poem about the ocean at sunset",
    "Summarize this long report in 3 bullet points quickly",
    "Let me reflect on my career choices and personal growth",
    "Collaborate with the team to design a new feature",
]

for prompt in prompts:
    coord = hex_breath.classify(prompt)
    defaults = _defaults_from_hex(coord)
    print(f'  "{prompt[:55]}..."')
    print(f"    temp={defaults.temperature:.2f}  top_p={defaults.top_p:.2f}  "
          f"tokens={defaults.max_tokens}  context={defaults.context_intensity:.2f}")
    print()

# ── 2. Immune feedback loop ────────────────────────────────────

print("=== Immune Feedback Loop ===\n")

tuner = StribeckTuner(learning_rate=0.1)
coord = HexCoord(ruhe_druck=0.5, empfangen_schaffen=0.3, langsam_schnell=-0.2)

# Simulate 10 healthy responses -> confidence grows
params = tuner.tune(coord, model="qwen3-14b")
print(f"  Initial: temp={params.temperature:.2f}, confidence={params.confidence:.2f}")

class FakeDiag:
    def __init__(self, healthy, flags=None):
        self.healthy = healthy
        self.flags = flags or []

for i in range(10):
    tuner.record(coord, params, FakeDiag(True), model="qwen3-14b")
    params = tuner.tune(coord, model="qwen3-14b")

print(f"  After 10 healthy: temp={params.temperature:.3f}, confidence={params.confidence:.2f}")
print(f"  At delta_opt: {params.at_delta_opt}")

# Simulate a repetition failure -> temperature increases
tuner.record(coord, params, FakeDiag(False, ["repetition(25%unique)"]), model="qwen3-14b")
params = tuner.tune(coord, model="qwen3-14b")
print(f"  After repetition: temp={params.temperature:.3f} (increased to break static friction)")

# Simulate a refusal -> context intensity decreases
tuner.record(coord, params, FakeDiag(False, ["refusal(I cannot)"]), model="qwen3-14b")
params = tuner.tune(coord, model="qwen3-14b")
print(f"  After refusal: context={params.context_intensity:.3f} (reduced to not overwhelm)")
print()

# ── 3. Multi-model tuning ──────────────────────────────────────

print("=== Multi-Model Tuning ===\n")

tuner2 = StribeckTuner(learning_rate=0.08)
models = ["qwen3-14b", "claude-3-haiku", "mistral-7b"]
coord2 = HexCoord(ruhe_druck=0.3, allein_zusammen=0.5)

for model in models:
    for _ in range(8):
        p = tuner2.tune(coord2, model=model)
        tuner2.record(coord2, p, FakeDiag(True), model=model)

    p = tuner2.tune(coord2, model=model)
    d_opt = tuner2.delta_opt_distance(coord2, model=model)
    print(f"  {model:20s}: temp={p.temperature:.3f}, delta_opt={d_opt:.3f}, obs={p.observations}")

print()

# ── 4. Stribeck surface report ─────────────────────────────────

print("=== Stribeck Surface Report ===\n")

report = tuner.stribeck_report()
print(f"  Mapped regions:     {report['mapped_regions']}")
print(f"  Total observations: {report['total_observations']}")
print(f"  Avg confidence:     {report['avg_confidence']:.3f}")
print(f"  At delta_opt:       {report['at_delta_opt']}")

for key, params_data in report["regions"].items():
    model_region = key.split(":")
    model = model_region[0] if len(model_region) > 1 else "generic"
    region = model_region[-1]
    print(f"\n    [{model}] region {region}:")
    print(f"      temp={params_data['temperature']:.3f}  top_p={params_data['top_p']:.3f}  "
          f"tokens={params_data['max_tokens']}  ctx={params_data['context_intensity']:.3f}")
    print(f"      confidence={params_data['confidence']:.3f}  observations={params_data['observations']}")

# ── 5. Persistence ──────────────────────────────────────────────

print("\n\n=== Persistence ===\n")

data = tuner.to_dict()
restored = StribeckTuner.from_dict(data)
print(f"  Original:  {tuner.mapped_regions} regions, {tuner.total_observations} observations")
print(f"  Restored:  {restored.mapped_regions} regions, {restored.total_observations} observations")
print(f"  Match:     {tuner.mapped_regions == restored.mapped_regions}")

# ── 6. Router integration ──────────────────────────────────────

print("\n=== Router Integration ===\n")

from void_intelligence import AtemRouter

router = AtemRouter(tuner=tuner)
router.register_adapter("qwen3-14b", lambda p, s="": f"Response about: {p[:40]}")

decision = router.inhale("Help me write an urgent email")
print(f"  Model:     {decision.selected_model}")
print(f"  Params:    temp={decision.parameters.temperature:.3f}  "
      f"top_p={decision.parameters.top_p:.3f}  "
      f"tokens={decision.parameters.max_tokens}  "
      f"ctx={decision.parameters.context_intensity:.3f}")
print(f"  Reason:    {decision.reason}")

print(f"\n  Tuner summary: {tuner.summary()}")

print("\nDone. Parameters are no longer static. They breathe.")
