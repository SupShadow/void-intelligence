#!/usr/bin/env python3
"""Example 05: The Ring Graph — Fractal knowledge structure.

Growth rings become a GRAPH, not a flat list. (Mandelbrot, 1982)

Knowledge is self-similar across scales:
  - A ring about "email tone" connects to "communication style"
  - Which connects to "team dynamics" which connects to "stakeholder management"
  - The graph IS the fractal.

Zero dependencies. Just run it.
"""

from void_intelligence import RingGraph, OrganismBreather

# ── 1. Build a knowledge graph ────────────────────────────────

print("=== Building Ring Graph ===\n")

graph = RingGraph()

# Add rings with causal connections
r1 = graph.add(
    "Email classification uses 6 hexagonal dimensions",
    ring_type="paradigm",
)
r2 = graph.add(
    "Urgency shifts email tone toward direct language",
    caused_by=r1.id,  # Learned BECAUSE of r1
)
r3 = graph.add(
    "Team context requires acknowledging all stakeholders",
    caused_by=r2.id,  # Learned BECAUSE of r2
)
r4 = graph.add("Direct language works best under deadline pressure")
r5 = graph.add("Stakeholder acknowledgment increases response rate")
r6 = graph.add(
    "6 dimensions capture nuance that binary classification misses",
    caused_by=r1.id,
)

# Add rings from a different domain
r7 = graph.add("Campaign voter outreach requires personal touch")
r8 = graph.add("Door-to-door canvassing has 3x the conversion of flyers")
r9 = graph.add("Personal touch in politics mirrors personal touch in email",
               caused_by=r7.id)

print(f"  Rings: {graph.count}")
print(f"  Edges: {graph.edge_count} (auto-detected + causal)")
print()

# ── 2. Query the graph (TF-IDF search) ───────────────────────

print("=== Querying ===\n")

queries = [
    "email urgency direct tone",
    "campaign outreach voter",
    "classification dimensions binary",
]

for q in queries:
    results = graph.query(q, top_k=3)
    print(f'  Query: "{q}"')
    for r in results:
        print(f"    [{r.id}] {r.content[:60]}")
    print()

# ── 3. Traverse the causal chain ─────────────────────────────

print("=== Causal Chains ===\n")

print(f"  Ancestors of [{r3.id}] \"{r3.content[:40]}...\":")
for a in graph.ancestors(r3.id):
    print(f"    <- [{a.id}] {a.content[:60]}")

print()
print(f"  Descendants of [{r1.id}] \"{r1.content[:40]}...\":")
for d in graph.descendants(r1.id):
    print(f"    -> [{d.id}] {d.content[:60]}")

# ── 4. Fractal themes ────────────────────────────────────────

print("\n=== Fractal Themes ===\n")

themes = graph.themes(depth=1)
for theme, rings in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {theme}: {len(rings)} rings")
    for r in rings[:2]:
        print(f"    - {r.content[:60]}")

# Depth 2: sub-themes
print()
themes_d2 = graph.themes(depth=2)
print(f"  Depth 2: {len(themes_d2)} sub-themes")
for theme, rings in sorted(themes_d2.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"    {theme}: {len(rings)} rings")

# ── 5. Context injection (THE key feature) ───────────────────

print("\n=== Context Injection ===\n")

prompts = [
    "Help me write an urgent email to my team",
    "Plan the next campaign event for voters",
]

for prompt in prompts:
    ctx = graph.to_context(prompt, max_rings=5)
    print(f'  Prompt: "{prompt}"')
    print("  " + "-" * 50)
    for line in ctx.split("\n"):
        print(f"  {line}")
    print("  " + "-" * 50)
    print()

# ── 6. Compression ───────────────────────────────────────────

print("=== Compression ===\n")

import time

# Create a graph with old rings
old_graph = RingGraph()
for i in range(8):
    n = old_graph.add(f"Old email insight about email formatting rule {i}")
    n.timestamp = time.time() - 7200  # 2 hours ago

old_graph.add("Fresh campaign insight just learned")

print(f"  Before: {old_graph.active_count} active, {old_graph.count - old_graph.active_count} compressed")

summaries = old_graph.compress(min_age_sec=3600)

print(f"  After:  {old_graph.active_count} active, {old_graph.count - old_graph.active_count} compressed")
print(f"  Created {len(summaries)} summary rings")
for s in summaries:
    print(f"    [{s.id}] {s.content[:70]}...")

# ── 7. Organism integration ──────────────────────────────────

print("\n=== Organism Integration ===\n")

organism = OrganismBreather()
organism.enable_graph()  # Activate ring graph

# Breathe with graph
organism.inhale("Help me write an urgent email")
organism.exhale("Done", learnings=[
    "Urgent emails need clear subject lines",
    "Team emails should mention each person's role",
])

organism.inhale("Plan campaign outreach")
organism.exhale("Done", learnings=[
    "Voter contact works best with personal stories",
])

print(f"  Flat rings: {organism.rings.count}")
print(f"  Graph rings: {organism.graph.count}")
print(f"  Graph edges: {organism.graph.edge_count}")

# Graph context for next prompt
ctx = organism.graph.to_context("Write an email to the campaign team")
print(f"\n  Context for next prompt:")
for line in ctx.split("\n"):
    print(f"    {line}")

# ── 8. Export / Import ────────────────────────────────────────

print("\n=== Export / Import ===\n")

exported = graph.export_rings()
print(f"  Exported: {len(exported['rings'])} rings, {len(exported['edges'])} edges")

imported = RingGraph.import_rings(exported)
print(f"  Imported: {imported.count} rings, {imported.edge_count} edges")

# ── 9. Persistence ───────────────────────────────────────────

print("\n=== Persistence ===\n")

data = graph.to_dict()
restored = RingGraph.from_dict(data)
print(f"  Original:  {graph.count} rings, {graph.edge_count} edges")
print(f"  Restored:  {restored.count} rings, {restored.edge_count} edges")
print(f"  Match:     {graph.count == restored.count and graph.edge_count == restored.edge_count}")

print(f"\n  Fractal summary:")
print(f"  {graph.fractal_summary()}")

print("\nDone. Knowledge is no longer flat. It's fractal.")
