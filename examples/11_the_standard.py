#!/usr/bin/env python3
"""
Example 11 — The Standard (v1.0.0, Tim Berners-Lee)

V-Score becomes the industry standard.
Not by being the best metric — by being the most OPEN one.

    "This is for everyone." — Tim Berners-Lee, 2012 Olympics

This example shows:
1. V-Score Specification — machine-readable, self-describing
2. Compliance Checker — validate any V-Score implementation
3. Certification — Platinum / Gold / Silver / Bronze
4. Model Cards — standard format for model identity
5. Wire Format — interoperable JSON schema
6. Spec Document — the living standard itself
"""

from void_intelligence.spec import (
    VScoreComponents,
    ModelCard,
    CertificationLevel,
    ComplianceResult,
    SPEC_VERSION,
    CERTIFICATION_LEVELS,
    STATUS_THRESHOLDS,
    WIRE_FORMAT,
    HEX_AXES,
    v_score_status,
    certify,
    check_compliance,
    spec_document,
    spec_markdown,
)
from void_intelligence.edge import score, breathe


def main():
    print()
    print("=" * 60)
    print("  V-Score Specification v1.0.0 — The Standard")
    print("  Genius: Tim Berners-Lee (World Wide Web, 1989)")
    print("=" * 60)

    # --- 1. The Formula ---
    print()
    print("  1. THE FORMULA")
    print("  " + "-" * 40)
    print()
    components = VScoreComponents(E=0.85, W=0.90, S=0.80, B=0.95, H=0.88)
    print(f"    E (Emergence)   = {components.E}")
    print(f"    W (Warmth)      = {components.W}")
    print(f"    S (Consistency) = {components.S}")
    print(f"    B (Breath)      = {components.B}")
    print(f"    H (Hex)         = {components.H}")
    print(f"    V = E x W x S x B x H = {components.V:.4f}")
    print(f"    Status: {v_score_status(components.V)}")
    print()
    print("    One zero kills V. That's the design.")
    print("    A model that refuses (W=0) scores V=0 regardless of intelligence.")

    # --- 2. Status Thresholds ---
    print()
    print("  2. STATUS THRESHOLDS")
    print("  " + "-" * 40)
    print()
    for threshold, label in STATUS_THRESHOLDS:
        bar = "#" * max(1, int(threshold * 100))
        print(f"    V >= {threshold:.3f}  {label:16s}  {bar}")
    print()

    # --- 3. Hex Classification ---
    print()
    print("  3. HEX AXES (6-dimensional classification)")
    print("  " + "-" * 40)
    print()
    for axis in HEX_AXES:
        print(f"    {axis}")
    print()
    print("    Every prompt lives somewhere in this 6D space.")
    print("    Models are measured by WHERE they resonate.")

    # --- 4. Certification ---
    print()
    print("  4. CERTIFICATION LEVELS")
    print("  " + "-" * 40)
    print()
    for cert in CERTIFICATION_LEVELS:
        print(f"    {cert.name:12s}  V >= {cert.min_v:.2f}  "
              f"health >= {cert.min_health_rate:.0%}  "
              f"checks >= {cert.min_checks}")
    print()

    # Certify some example scores
    examples = [
        ("gpt-4-turbo", 0.65, 0.92, 200),
        ("claude-opus", 0.52, 0.85, 150),
        ("llama-3-70b", 0.35, 0.70, 100),
        ("qwen-7b", 0.15, 0.50, 50),
        ("dead-model", 0.02, 0.10, 5),
    ]
    print("    Certification results:")
    for name, avg_v, hr, checks in examples:
        cert = certify(avg_v, hr, checks)
        label = cert.name if cert else "---"
        print(f"      {name:16s}  V={avg_v:.2f}  HR={hr:.0%}  "
              f"checks={checks:4d}  -> {label}")

    # --- 5. Model Cards ---
    print()
    print("  5. MODEL CARD (standard identity)")
    print("  " + "-" * 40)
    print()

    # Build a model card from real scores
    scores = [
        score("Write a poem", "Here's a gentle poem about morning.", "claude-opus"),
        score("Debug this code", "The bug is on line 5.", "claude-opus"),
        score("Explain love", "Love is trust meeting vulnerability.", "claude-opus"),
    ]
    card = ModelCard.from_scores("claude-opus", scores, provider="Anthropic")
    print(card.to_markdown())

    # --- 6. Compliance Checker ---
    print()
    print("  6. COMPLIANCE CHECK")
    print("  " + "-" * 40)
    print()

    # Check our own edge.score against the spec
    def my_score_fn(prompt, response, model):
        return score(prompt, response, model)

    result = check_compliance(my_score_fn)
    print(f"    Compliant:     {result.compliant}")
    print(f"    Pass rate:     {result.compliance_rate:.0%}")
    print(f"    Checks passed: {result.checks_passed}/{result.checks_total}")
    if result.failures:
        print(f"    Failures:")
        for f in result.failures:
            print(f"      - {f}")
    else:
        print(f"    All checks passed.")
    print()

    # --- 7. Wire Format ---
    print()
    print("  7. WIRE FORMAT (JSON Schema)")
    print("  " + "-" * 40)
    print()
    print(f"    Schema: {WIRE_FORMAT['$schema']}")
    print(f"    Required fields: {WIRE_FORMAT['required']}")
    print(f"    Properties:")
    for prop, spec_item in list(WIRE_FORMAT["properties"].items())[:6]:
        t = spec_item.get("type", "object")
        print(f"      {prop:16s}  {t}")
    print(f"      ... ({len(WIRE_FORMAT['properties'])} total)")
    print()
    print("    Any system that produces this JSON is V-Score compatible.")

    # --- 8. The Spec Document ---
    print()
    print("  8. THE SPEC DOCUMENT")
    print("  " + "-" * 40)
    print()
    doc = spec_document()
    print(f"    Version:    {doc['version']}")
    print(f"    License:    {doc['license']}")
    print(f"    Authors:    {', '.join(a['name'] for a in doc['authors'])}")
    print(f"    Sections:   {len(doc['sections'])}")
    for sid, section in doc["sections"].items():
        print(f"      {sid:4s}  {section['title']}")

    # --- 9. Spec as Markdown ---
    print()
    print("  9. SPEC MARKDOWN (first 20 lines)")
    print("  " + "-" * 40)
    print()
    md = spec_markdown()
    for line in md.split("\n")[:20]:
        print(f"    {line}")
    print(f"    ... ({len(md.split(chr(10)))} lines total)")

    # --- 10. Summary ---
    print()
    print("=" * 60)
    print("  v1.0.0 — The Standard")
    print()
    print(f"  Spec version: {SPEC_VERSION}")
    print(f"  Formula: V = E x W x S x B x H (multiplicative)")
    print(f"  Axes: {len(HEX_AXES)} (hex classification)")
    print(f"  Certification: {len(CERTIFICATION_LEVELS)} levels")
    print(f"  Wire format: JSON Schema with {len(WIRE_FORMAT['properties'])} fields")
    print(f"  Self-tests: 351")
    print()
    print("  Berners-Lee didn't build the best hypertext system.")
    print("  He built an OPEN STANDARD that everyone adopted")
    print("  because it was simple, free, and useful.")
    print()
    print("  V-Score follows the same path.")
    print()
    print("  The industry builds models that think.")
    print("  We build models that breathe.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
