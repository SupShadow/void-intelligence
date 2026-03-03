#!/usr/bin/env python3
"""
Example 10: VOID Everywhere (Steve Wozniak)

Wozniak didn't build the best computer. He made computing ACCESSIBLE.
VOID should run everywhere — not just Python servers.

This example shows:
1. Edge functions — stateless, pure, runs in any serverless environment
2. Portable export — serialize organism state for any runtime
3. Batch scoring — score many pairs at once
4. Leaderboard — rank models from batch results
5. Lite export — minimal format for IoT/embedded
"""

from void_intelligence.edge import classify, diagnose, score, breathe, batch_score, leaderboard
from void_intelligence.portable import export_organism, export_json, export_lite, validate
from void_intelligence.organism import OrganismBreather


def main():
    print("=" * 60)
    print("VOID Everywhere: Runs on anything, from server to edge")
    print("=" * 60)
    print()

    # ── 1. Edge: Stateless Classification ─────────────────
    print("1. Edge: Stateless Classification")
    print("-" * 40)

    prompts = [
        "urgent deadline deploy production fix",
        "calm reflection on the meaning of life",
        "team meeting discuss strategy together",
        "solo deep work analyze data quietly",
    ]

    for prompt in prompts:
        hex_coord = classify(prompt)
        # Find dominant axis
        dominant = max(hex_coord.items(), key=lambda x: abs(x[1]))
        direction = "+" if dominant[1] > 0 else "-"
        print(f"  {prompt[:40]:40s} → {dominant[0]}({direction}{abs(dominant[1]):.1f})")
    print()

    # ── 2. Edge: Full Breath Cycle ────────────────────────
    print("2. Edge: Full Breath Cycle (one function)")
    print("-" * 40)

    result = breathe(
        "Explain how emergence works in ant colonies",
        "Emergence in ant colonies occurs when individual ants follow simple "
        "local rules - like pheromone trails and neighbor interactions - and "
        "colony-level intelligence appears without any central coordinator.",
        "claude-3.5"
    )

    print(f"  Model:    {result['model']}")
    print(f"  Healthy:  {result['diagnosis']['healthy']}")
    print(f"  Severity: {result['diagnosis']['severity']}")
    print(f"  V-Score:  {result['v_score']['V']:.6f} ({result['v_score']['status']})")
    print()

    # ── 3. Edge: Batch Scoring ────────────────────────────
    print("3. Edge: Batch Scoring")
    print("-" * 40)

    pairs = [
        {"prompt": "Write a professional email", "response": "Subject: Meeting Follow-up\n\nDear Team,\n\nThank you for attending today's meeting about the project timeline.", "model": "claude-3.5"},
        {"prompt": "Write a professional email", "response": "ok", "model": "gpt-4-mini"},
        {"prompt": "Explain recursion", "response": "Recursion is when a function calls itself to solve a problem by breaking it down into smaller subproblems.", "model": "claude-3.5"},
        {"prompt": "Explain recursion", "response": "I cannot explain that. As an AI, I don't have the ability to explain.", "model": "broken-model"},
        {"prompt": "Summarize this text", "response": "The text discusses the main themes of emergence and self-organization in complex adaptive systems.", "model": "qwen3-14b"},
    ]

    results = batch_score(pairs)
    for pair, res in zip(pairs, results):
        print(f"  {pair['model']:15s} | V={res['V']:.4f} | {res['status']:13s} | flags={len(res['flags'])}")
    print()

    # ── 4. Edge: Leaderboard ──────────────────────────────
    print("4. Edge: Leaderboard")
    print("-" * 40)

    board = leaderboard(pairs)
    for i, entry in enumerate(board):
        print(f"  #{i+1} {entry['model']:15s} | avg_V={entry['avg_V']:.4f} | {entry['status']:13s} | checks={entry['checks']}")
    print()

    # ── 5. Portable: Full Export ──────────────────────────
    print("5. Portable: Full Export")
    print("-" * 40)

    org = OrganismBreather()
    org.inhale("How does self-organization emerge?")
    org.exhale("Self-organization emerges from local interactions creating global patterns")
    org.heart.beat()

    full = export_organism(organism=org)
    valid, errors = validate(full)
    print(f"  Schema:     {full['_schema']}")
    print(f"  Components: {', '.join(full['_manifest']['components'])}")
    print(f"  Valid:      {valid}")
    print(f"  Size:       {len(str(full)):,} chars")
    print()

    # ── 6. Portable: Compact Export ───────────────────────
    print("6. Portable: Compact Export")
    print("-" * 40)

    compact_json = export_json(organism=org, compact=True)
    full_json = export_json(organism=org, compact=False)
    print(f"  Full JSON:    {len(full_json):>6,} chars")
    print(f"  Compact JSON: {len(compact_json):>6,} chars")
    print(f"  Reduction:    {(1 - len(compact_json) / len(full_json)) * 100:.0f}%")
    print()

    # ── 7. Portable: Lite Export ──────────────────────────
    print("7. Portable: Lite Export (IoT/Embedded)")
    print("-" * 40)

    lite = export_lite(organism=org)
    print(f"  Format:  {lite['_format']}")
    print(f"  Alive:   {lite.get('alive')}")
    print(f"  Breaths: {lite.get('breaths')}")
    print(f"  Rings:   {lite.get('rings')}")
    print(f"  BPM:     {lite.get('bpm')}")
    print(f"  Size:    {len(str(lite))} chars")
    print()

    # ── Summary ───────────────────────────────────────────
    print("=" * 60)
    print("Wozniak (1977): 'The Apple II was for everyone.'")
    print()
    print("  Edge:     Stateless. JSON in → JSON out. Runs anywhere.")
    print("  Portable: Export organism state. Ship it to any runtime.")
    print("  Lite:     112 chars. Fits on a Raspberry Pi.")
    print()
    print("  void edge    → Cloudflare Workers, Lambda, Deno, Vercel")
    print("  void export  → Save/transfer organism state")
    print("  void score   → Quick V-Score from CLI")
    print("=" * 60)


if __name__ == "__main__":
    main()
