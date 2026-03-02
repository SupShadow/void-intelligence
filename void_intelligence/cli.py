#!/usr/bin/env python3
"""
void CLI --- The command line of a living system.

Usage:
    void breathe --demo       # See the organism breathe (30 sec demo)
    void breathe              # Start local breath daemon (watches files)
    void ir                   # Show the 5 fundamental operations
    void test                 # Self-test
    void hex "your prompt"    # Classify a prompt on 6 axes
    void pulse                # Show system pulse
"""

from __future__ import annotations

import sys


def cmd_ir():
    """Show the 5 fundamental operations of reality."""
    from void_intelligence.ir import IRType
    print()
    print("  .x->[]~ --- The 5 fundamental operations")
    print("  " + "=" * 50)
    descriptions = {
        ".": "Atom       | Irreducible fact, event",
        "x": "Collision  | Tensor of two atoms, emergence",
        "->": "Projection | x becomes action (incomplete!)",
        "[]": "Potential  | Pregnant silence between events",
        "~": "Resonance  | Feedback loop, system learns",
    }
    for t in IRType:
        desc = descriptions.get(t.value, "")
        print(f"    {t.value:4s}  {desc}")
    print()
    print("  Universal formula: .x->[]~")
    print("    A x B creates C that exists in neither A nor B.")
    print("    Every -> loses dimensions (Anti-P3122).")
    print("    [] is not empty --- it's pregnant with possibility.")
    print()


def cmd_test():
    """Self-test of the void-intelligence library."""
    from void_intelligence.ir import Atom, collide, project, resonate, SystemPulse, PatternWeights
    from void_intelligence.patterns import CircuitBreaker, current_phase, delta_opt_distance
    from void_intelligence.organism import OrganismBreather, HexBreath

    print()
    print("  void test --- Self-test")
    print("  " + "=" * 50)

    passed = 0
    total = 0

    def check(name, condition):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"    OK   {name}")
        else:
            print(f"    FAIL {name}")

    # IR tests
    a = Atom(domain="test", type="ping", value={"ok": True})
    b = Atom(domain="test2", type="pong", value={"ok": True})
    check("Atom create", a.domain == "test")

    c = collide(a, b, score=0.9)
    check("Collision", c.density > 0)

    p = project(c, "verify", lost=["context"])
    check("Projection + lost_dimensions", p.lost_dimensions == ["context"])

    r = resonate(c.id, "success", 0.8)
    check("Resonance", r.weight_delta > 0)

    sp = SystemPulse(atoms_per_min=5, collisions_per_min=2, potential_ratio=0.4)
    check("SystemPulse alive", sp.alive)
    check("SystemPulse delta_opt=0", sp.delta_opt_distance == 0.0)

    pw = PatternWeights()
    pw.apply_resonance(r, "test")
    check("PatternWeights learns", pw.get("test") > 1.0)

    # Pattern tests
    cb = CircuitBreaker("test")
    check("CircuitBreaker CLOSED", cb.can_execute())
    for _ in range(5):
        cb.record_failure()
    check("CircuitBreaker OPEN", not cb.can_execute())

    check("Phase detection", current_phase() is not None)
    check("delta_opt_distance", delta_opt_distance(0.4, 0.4) == 0.0)

    # Organism tests
    hex_breath = HexBreath()
    coord = hex_breath.classify("urgent deadline team help build fast")
    check("HexBreath classifies", coord.magnitude > 0)

    organism = OrganismBreather()
    breath_in = organism.inhale("test prompt")
    check("Organism inhale", breath_in["breath"] == 1)
    breath_out = organism.exhale("test response", learnings=["learned something"])
    check("Organism exhale + ring", organism.rings.count == 1)
    vitals = organism.vitals()
    check("Organism vitals", vitals["alive"] is True)

    print()
    print(f"    {passed}/{total} tests passed.")
    print()
    return 0 if passed == total else 1


def cmd_hex(text: str):
    """Classify a prompt on 6 hexagonal axes."""
    from void_intelligence.organism import HexBreath

    hex_breath = HexBreath()
    coord = hex_breath.classify(text)

    print()
    print(f"  HexBreath classification:")
    print(f"  " + "=" * 50)
    print(f"    Input: \"{text}\"")
    print()

    axes = [
        ("Calm/Pressure", coord.ruhe_druck),
        ("Silence/Resonance", coord.stille_resonanz),
        ("Alone/Together", coord.allein_zusammen),
        ("Receive/Create", coord.empfangen_schaffen),
        ("Being/Doing", coord.sein_tun),
        ("Slow/Fast", coord.langsam_schnell),
    ]

    for label, val in axes:
        direction = "+" if val > 0 else "-" if val < 0 else "="
        bar_len = int(abs(val) * 20)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"    {label:20s} {direction} [{bar}] {val:+.2f}")

    print()
    print(f"    Magnitude: {coord.magnitude:.3f}")
    print(f"    Balance:   {coord.balance:.3f}")
    print()


def cmd_breathe_demo():
    """Run the visual demo."""
    from void_intelligence.demo import run_demo
    run_demo()


def cmd_version():
    """Show version."""
    from void_intelligence import __version__
    print(f"void-intelligence {__version__}")


def main() -> int:
    """CLI dispatcher."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print()
        print("  void --- The organism layer for LLMs")
        print()
        print("  Commands:")
        print("    void breathe --demo   See the organism breathe")
        print("    void ir               The 5 fundamental operations")
        print("    void test             Self-test")
        print("    void hex \"text\"       Classify text on 6 axes")
        print("    void --version        Show version")
        print()
        print("  pip install void-intelligence")
        print()
        return 0

    cmd = args[0]

    if cmd == "--version" or cmd == "version":
        cmd_version()
        return 0

    if cmd == "ir":
        cmd_ir()
        return 0

    if cmd == "test":
        return cmd_test() or 0

    if cmd == "hex":
        text = " ".join(args[1:]) if len(args) > 1 else "hello world"
        cmd_hex(text)
        return 0

    if cmd == "breathe":
        if "--demo" in args:
            cmd_breathe_demo()
            return 0
        # Full breath daemon needs watchdog
        print()
        print("  void breathe --- Local breath daemon")
        print("  Requires: pip install void-intelligence[watch]")
        print()
        print("  For the demo: void breathe --demo")
        print()
        try:
            import watchdog
        except ImportError:
            print("  Install watchdog first: pip install watchdog")
            return 1
        print("  (Full daemon mode coming in v0.2.0)")
        return 0

    if cmd == "pulse":
        from void_intelligence.organism import OrganismBreather
        o = OrganismBreather()
        o.inhale("pulse check")
        o.heart.beat()
        print()
        print("  void pulse --- System vitals")
        print("  " + "=" * 50)
        v = o.vitals()
        print(f"    Alive:     {v['alive']}")
        print(f"    Breaths:   {v['breaths']}")
        print(f"    Heartbeat: {v['heartbeats']} ({v['bpm']} bpm)")
        print(f"    Rings:     {v['rings']['total']}")
        print()
        return 0

    print(f"  Unknown command: {cmd}")
    print(f"  Run 'void --help' for usage.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
