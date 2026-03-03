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

    # Organism persistence tests
    state = organism.to_dict()
    check("Organism to_dict", state["breath_count"] == 1 and len(state["rings"]) == 1)
    restored = OrganismBreather.from_dict(state)
    check("Organism from_dict roundtrip", restored._breath_count == 1 and restored.rings.count == 1)
    check("Organism from_dict rings", restored.rings.rings[0].content == "learned something")
    bad_restore = OrganismBreather.from_dict({"garbage": True})
    check("Organism from_dict bad data", bad_restore._breath_count == 0)

    # Profile tests
    from void_intelligence.profiles import VScoreProfile, BUNDLED_PROFILES
    check("Profiles loaded", len(BUNDLED_PROFILES) >= 30)
    alive_count = sum(1 for p in BUNDLED_PROFILES.values() if p.alive)
    check("Profiles alive", alive_count >= 10)

    prof = BUNDLED_PROFILES.get("qwen3-14b")
    if prof:
        check("Profile qwen3-14b R=0.99", prof.R > 0.9)
        check("Profile breath quality", prof.breath_quality > 0.5)
        aff = prof.hex_affinity(coord)
        check("Profile hex_affinity", 0.0 <= aff <= 1.0)

    # Router tests
    from void_intelligence.router import AtemRouter
    import tempfile
    from pathlib import Path
    tmpdir = Path(tempfile.mkdtemp())
    router = AtemRouter(state_dir=tmpdir)
    decision = router.inhale("urgent deadline team help build fast")
    check("Router inhale returns decision", decision.selected_model != "")
    check("Router system prompt", "Input classified" in decision.system_prompt)
    check("Router has alternatives", isinstance(decision.alternatives, list))

    # Router with adapter
    router.register_adapter(decision.selected_model, lambda p, s="": "test response")
    result = router.breathe("urgent deadline team help")
    check("Router breathe executes", result.response == "test response")
    check("Router vitals after", result.vitals_after["alive"] is True)

    # State persistence
    state_file = tmpdir / "organisms" / decision.selected_model.replace("/", "_").replace(":", "_") / "state.json"
    check("Router persists state", state_file.exists())

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

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


def cmd_route(text: str):
    """Route a prompt through the Atem-Router. Shows decision without execution."""
    from void_intelligence.router import AtemRouter

    router = AtemRouter()
    decision = router.inhale(text)

    print()
    print("  Atem-Router --- Breath-based model routing")
    print("  " + "=" * 55)
    print(f'  Input: "{text}"')
    print()

    # Hex classification
    coord = decision.hex
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
        bar_len = int(abs(val) * 15)
        bar = "#" * bar_len + "." * (15 - bar_len)
        print(f"    {label:20s} {direction} [{bar}] {val:+.2f}")

    print()
    p = decision.profile
    alive_str = "ALIVE" if p.alive else "DEAD"
    local_str = "LOCAL/FREE" if p.is_local else f"${p.cost_per_m:.2f}/M"
    print(f"  Selected: {decision.selected_model} ({alive_str}, {local_str})")
    print(f"  V-Score:  {p.V:.4f}  (E={p.E:.2f} W={p.W:.2f} S={p.S:.2f} B={p.B:.2f} H={p.H:.2f} R={p.R:.2f})")
    print(f"  Reason:   {decision.reason}")

    if decision.alternatives:
        print(f"  Runners:  {', '.join(decision.alternatives[:5])}")

    print()
    print("  System prompt injection:")
    print("  " + "-" * 55)
    for line in decision.system_prompt.split("\n"):
        print(f"    {line}")
    print("  " + "-" * 55)
    print()


def cmd_profiles():
    """List all bundled V-Score profiles."""
    from void_intelligence.profiles import BUNDLED_PROFILES

    alive = [(n, p) for n, p in BUNDLED_PROFILES.items() if p.alive]
    dead = [(n, p) for n, p in BUNDLED_PROFILES.items() if not p.alive]

    print()
    print("  V-Score Profiles --- 35 models benchmarked March 2026")
    print("  " + "=" * 85)
    print(f"  {'Model':<22} {'E':>5} {'W':>5} {'S':>5} {'B':>5} {'H':>5} {'R':>5} {'V-Score':>8} {'Cost':>8}")
    print(f"  {'─' * 22} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 8} {'─' * 8}")

    for name, p in sorted(alive, key=lambda x: x[1].V, reverse=True):
        cost_str = "FREE" if p.is_local else f"${p.cost_per_m:.2f}"
        print(
            f"  {name:<22} {p.E:5.2f} {p.W:5.2f} {p.S:5.2f} "
            f"{p.B:5.2f} {p.H:5.2f} {p.R:5.2f} {p.V:8.4f} {cost_str:>8}"
        )

    print(f"  {'─' * 22} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 8} {'─' * 8}")
    print(f"  + {len(dead)} dead models (V=0, R=0) --- per-dimension data available")
    print(f"  Total: {len(BUNDLED_PROFILES)} models | {len(alive)} alive | {len(dead)} dead")
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
        print("    void route \"text\"     Route a prompt (Atem-Router)")
        print("    void profiles         List V-Score profiles")
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

    if cmd == "route":
        text = " ".join(args[1:]) if len(args) > 1 else "hello world"
        cmd_route(text)
        return 0

    if cmd == "profiles":
        cmd_profiles()
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

    if cmd == "benchmark":
        from void_intelligence.benchmark import run_benchmark
        local_only = "--local" in args
        model_filter = ""
        for a in args[1:]:
            if not a.startswith("--"):
                model_filter = a
        run_benchmark(local_only=local_only, model_filter=model_filter)
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
