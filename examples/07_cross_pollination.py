#!/usr/bin/env python3
"""Example 07: Cross-Pollination — Knowledge transfer between model organisms.

Lynn Margulis (Endosymbiosis Theory, 1967): Mitochondria were once
free-living bacteria that merged with eukaryotic cells. The merger
made BOTH stronger. This is the most important event in evolutionary history.

Cross-pollination does the same: what Model A learned flows to Model B,
making both more capable. The transferred rings (endosymbionts) are
tracked, measured, and confirmed via immune system feedback.

Zero dependencies. Just run it.
"""

from void_intelligence import CrossPollinator, RingGraph, diagnose

# ── 1. Build two organisms with different expertise ──────────

print("=" * 60)
print("Cross-Pollination: Knowledge flows between organisms")
print("=" * 60)

# Model A: Communication expert
graph_a = RingGraph()
graph_a.add("Urgency in emails requires direct, concise language", ring_type="paradigm")
graph_a.add("Team acknowledgment increases response rate by 40%", ring_type="milestone")
graph_a.add("Stakeholder mapping before any group communication")
graph_a.add("Tone shifts under deadline pressure — less hedging")
graph_a.add("6 hexagonal dimensions capture communication nuance", ring_type="paradigm")
graph_a.add("Response time correlates with perceived importance")
graph_a.add("Meeting follow-ups within 24h increase action completion", ring_type="learning")

# Model B: Technical expert
graph_b = RingGraph()
graph_b.add("Architecture review before code review", ring_type="paradigm")
graph_b.add("Unit tests should cover edge cases, not just happy path")
graph_b.add("Performance profiling before optimization — measure first")
graph_b.add("Database indexes: explain analyze before adding blindly", ring_type="learning")
graph_b.add("CI/CD pipeline runs should complete under 5 minutes")

print(f"\nOrganism A (communication): {graph_a.active_count} rings")
print(f"Organism B (technical):     {graph_b.active_count} rings")

# ── 2. Identify transferable rings ───────────────────────────

print("\n" + "-" * 60)
print("Step 1: Identify transferable knowledge from A")
print("-" * 60)

pollinator = CrossPollinator()
candidates = pollinator.identify_transferable(graph_a, max_rings=10)

for node, score in candidates:
    print(f"  [{node.id}] score={score:.1f} type={node.ring_type:10s} | {node.content[:50]}")

# ── 3. Transfer A → B ───────────────────────────────────────

print("\n" + "-" * 60)
print("Step 2: Pollinate A → B (transfer knowledge)")
print("-" * 60)

event = pollinator.pollinate(
    source_graph=graph_a,
    source_model="comm-expert",
    target_graph=graph_b,
    target_model="tech-expert",
    max_transfer=4,
)

print(f"  Transferred: {event.rings_transferred} rings")
print(f"  B now has:   {graph_b.active_count} rings (was 5)")

symbionts = pollinator.symbionts_for("tech-expert")
print(f"\n  Endosymbionts in B:")
for sym in symbionts:
    status = "confirmed" if sym.confirmed else "pending"
    print(f"    [{sym.ring_id}] {status} | from {sym.source_model}: {sym.content[:45]}")

# ── 4. Measure transfer lift via immune feedback ─────────────

print("\n" + "-" * 60)
print("Step 3: Measure if transfer helped (immune feedback)")
print("-" * 60)

# Set baseline before transfer effect kicks in
pollinator.set_baseline("tech-expert", 0.6)

# Simulate that the tech model now responds better
# (in production, this comes from diagnose() after real responses)
diag = diagnose(
    "Help me write a follow-up email to the team about the code review deadline",
    "I'll send a direct, concise follow-up within 24h covering stakeholder roles.",
)
print(f"  Diagnosis: {'HEALTHY' if diag.healthy else 'SICK'} | composite: {diag.composite_score:.3f}")

# Confirm with the improved score
lift = pollinator.confirm("tech-expert", diag.composite_score)
print(f"  Transfer lift: {lift:+.3f}")

confirmed = pollinator.confirmed_symbionts("tech-expert")
print(f"  Confirmed endosymbionts: {len(confirmed)}/{len(symbionts)}")

# ── 5. Bidirectional pollination ─────────────────────────────

print("\n" + "-" * 60)
print("Step 4: Bidirectional — B also teaches A")
print("-" * 60)

event_ba = pollinator.pollinate(
    source_graph=graph_b,
    source_model="tech-expert",
    target_graph=graph_a,
    target_model="comm-expert",
    max_transfer=3,
)

print(f"  B → A transferred: {event_ba.rings_transferred} rings")
print(f"  A now has:         {graph_a.active_count} rings (was 7)")

# ── 6. Auto-pollination (router-triggered) ───────────────────

print("\n" + "-" * 60)
print("Step 5: Auto-pollination (like the router does)")
print("-" * 60)

# Build a third organism
graph_c = RingGraph()
for i in range(6):
    graph_c.add(f"Design principle {i}: user experience insight")

graphs = {
    "comm-expert": graph_a,
    "tech-expert": graph_b,
    "design-expert": graph_c,
}

auto_pollinator = CrossPollinator()
events = auto_pollinator.auto_pollinate(graphs, min_rings=5, cooldown_sec=0)

print(f"  Auto-pollination events: {len(events)}")
for e in events:
    print(f"    {e.source_model} → {e.target_model}: {e.rings_transferred} rings")

# ── 7. Persistence ───────────────────────────────────────────

print("\n" + "-" * 60)
print("Step 6: Persistence (survives restarts)")
print("-" * 60)

state = pollinator.to_dict()
restored = CrossPollinator.from_dict(state)

print(f"  Events:    {restored.total_events} (original: {pollinator.total_events})")
print(f"  Transfers: {restored.total_transfers} (original: {pollinator.total_transfers})")
print(f"  Pairs:     {restored.unique_pairs} (original: {pollinator.unique_pairs})")

# ── 8. Full report ───────────────────────────────────────────

print("\n" + "-" * 60)
print("Step 7: Full report")
print("-" * 60)

report = pollinator.report()
print(f"  Total events:    {report['total_events']}")
print(f"  Total transfers: {report['total_transfers']}")
print(f"  Unique pairs:    {report['unique_pairs']}")
for model, stats in report["models"].items():
    print(f"  {model}: {stats['total_imports']} imports, {stats['confirmed']} confirmed, lift={stats['avg_lift']:+.3f}")

print("\n" + "=" * 60)
print("Margulis was right: cooperation > competition.")
print("Knowledge shared is knowledge multiplied.")
print("=" * 60)
