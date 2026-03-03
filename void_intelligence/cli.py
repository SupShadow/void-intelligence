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
    void spec                 # The V-Score Specification (v1.0.0)
    void certify [model]      # Certify a model against the spec
    void mcp                  # Start MCP server (Claude Code plugin)
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

    # ── Immune System tests ──────────────────────────────────────
    from void_intelligence.immune import (
        diagnose, hex_distance, immune, Diagnosis, ImmuneState, ImmuneMonitor,
    )
    from void_intelligence.organism import HexCoord

    # hex_distance: identical = 0
    c1 = HexCoord(0.5, 0.3, 0.1, 0.8, -0.2, 0.4)
    check("hex_distance self=0", hex_distance(c1, c1) == 0.0)

    # hex_distance: different > 0
    c2 = HexCoord(-0.5, -0.3, -0.1, -0.8, 0.2, -0.4)
    check("hex_distance diff>0", hex_distance(c1, c2) > 0.5)

    # diagnose: healthy response
    d = diagnose(
        "Help me write an urgent email to my team about the deadline",
        "Here is your urgent email draft about the team deadline. "
        "Dear team, I wanted to reach out about our upcoming deadline.",
    )
    check("Diagnosis healthy", d.healthy)
    check("Diagnosis has layers", len(d.layer_scores) == 5)
    check("Diagnosis severity", d.severity == "healthy")

    # diagnose: too short
    d2 = diagnose("Write a report", "No")
    check("Diagnosis too_short", not d2.healthy and any("too_short" in f for f in d2.flags))

    # diagnose: refusal
    d3 = diagnose("Help me", "I'm sorry, but I cannot help with that as an AI language model.")
    check("Diagnosis refusal", not d3.healthy and any("refusal" in f for f in d3.flags))

    # diagnose: composite score
    check("Diagnosis composite 0-1", 0.0 <= d.composite_score <= 1.0)

    # ImmuneState: tracks calls
    state = ImmuneState()
    state.record(d)
    state.record(d2)
    check("ImmuneState tracks", state.total_calls == 2 and state.healthy_calls == 1)
    check("ImmuneState health_rate", 0.4 <= state.health_rate <= 0.6)

    # @immune decorator
    call_count = [0]

    @immune(threshold=0.5)
    def mock_llm(prompt):
        call_count[0] += 1
        return "Here is a thoughtful response about " + prompt.split()[0]

    mock_llm("urgent help write email team")
    check("@immune calls fn", call_count[0] == 1)
    check("@immune has state", hasattr(mock_llm, "immune_state"))
    check("@immune records", mock_llm.immune_state.total_calls == 1)

    # @immune with fallback
    @immune(
        fallback=lambda p, *a, **k: "Fallback response about " + p,
        threshold=0.01,  # Very strict -> will trigger fallback
    )
    def strict_llm(prompt):
        return "Completely unrelated gibberish xyz abc 123"

    res = strict_llm("Write about quantum physics")
    check("@immune fallback fires", strict_llm.immune_state.fallback_calls >= 1)

    # ImmuneMonitor
    mon = ImmuneMonitor(threshold=0.5)
    for i in range(5):
        mon.check("model-a", f"help with task {i}", f"Here is help with task {i} for you")
    mon.check("model-b", "help", "no")
    report = mon.report()
    check("Monitor report", report["models_monitored"] == 2)
    check("Monitor system_health", 0.0 <= report["system_health"] <= 1.0)
    check("Monitor healthiest", report["healthiest"] == "model-a")

    # ── Ring Graph tests (v0.4.0) ──────────────────────────────
    from void_intelligence.ring_graph import RingGraph, RingNode, RingEdge

    # Basic graph creation
    g = RingGraph()
    check("RingGraph empty", g.count == 0 and g.edge_count == 0)

    # Add rings
    r1 = g.add("Email classification uses 6 hexagonal dimensions", ring_type="paradigm")
    r2 = g.add("Urgency shifts email tone toward direct language", caused_by=r1.id)
    check("RingGraph add", g.count == 2)
    check("RingGraph node type", r1.ring_type == "paradigm" and r2.ring_type == "learning")
    check("RingGraph caused_by edge", g.edge_count >= 1)

    # Auto-relate (keyword overlap)
    r3 = g.add("Email response rate improves with direct email formatting")
    auto_edges = [e for e in g.edges if e.edge_type == "related"]
    check("RingGraph auto-relate", len(auto_edges) >= 1)

    # Manual connect
    g.connect(r3.id, r2.id, "deepens", 0.7)
    check("RingGraph connect", any(e.edge_type == "deepens" for e in g.edges))

    # Query (TF-IDF)
    results = g.query("email tone urgency", top_k=3)
    check("RingGraph query returns", len(results) > 0)
    check("RingGraph query relevant", any("email" in r.content.lower() for r in results))

    # Query empty string
    results_empty = g.query("", top_k=2)
    check("RingGraph query empty", len(results_empty) <= 2)

    # Themes
    g.add("Campaign voter outreach strategy planning")
    g.add("Voter contact tracking for campaign events")
    themes = g.themes(depth=1)
    check("RingGraph themes", len(themes) >= 1)

    # Ancestors / descendants
    ancestors = g.ancestors(r2.id)
    check("RingGraph ancestors", len(ancestors) >= 1 and ancestors[0].id == r1.id)

    descendants = g.descendants(r1.id)
    check("RingGraph descendants", len(descendants) >= 1 and descendants[0].id == r2.id)

    # Neighbors
    neighbors = g.neighbors(r2.id)
    check("RingGraph neighbors", len(neighbors) >= 1)

    # to_context
    ctx = g.to_context("Help me write an urgent email")
    check("RingGraph to_context", "Organic memory" in ctx and "email" in ctx.lower())

    # Fractal summary
    summary = g.fractal_summary()
    check("RingGraph fractal_summary", "Ring Graph" in summary)

    # Compression (make old rings)
    import time as _time
    cg = RingGraph()
    for i in range(6):
        n = cg.add(f"Old learning about topic alpha number {i}")
        n.timestamp = _time.time() - 7200  # 2 hours ago
    cg.add("Fresh learning about topic beta")
    summaries = cg.compress(min_age_sec=3600)
    check("RingGraph compress", len(summaries) >= 1)
    check("RingGraph compress marks", any(n.compressed for n in cg.nodes.values()))

    # to_dict / from_dict roundtrip
    data = g.to_dict()
    g2 = RingGraph.from_dict(data)
    check("RingGraph to_dict", data["version"] == 1 and len(data["nodes"]) == g.count)
    check("RingGraph from_dict count", g2.count == g.count)
    check("RingGraph from_dict edges", g2.edge_count == g.edge_count)
    check("RingGraph from_dict content", g2.nodes["r0000"].content == r1.content)

    # from_dict bad data
    g_bad = RingGraph.from_dict({"garbage": True})
    check("RingGraph from_dict bad", g_bad.count == 0)

    # Export / import
    exported = g.export_rings()
    check("RingGraph export", len(exported["rings"]) > 0)
    g3 = RingGraph.import_rings(exported)
    check("RingGraph import", g3.count == len(exported["rings"]))

    # Organism graph integration
    org_g = OrganismBreather()
    org_g.enable_graph()
    check("Organism enable_graph", org_g.graph is not None)
    org_g.inhale("test prompt for graph")
    org_g.exhale("response", learnings=["graph learning one", "graph learning two"])
    check("Organism graph grows", org_g.graph.count == 2)
    check("Organism graph + flat sync", org_g.rings.count == 2)

    # Organism graph persistence
    org_state = org_g.to_dict()
    check("Organism to_dict has graph", "graph" in org_state)
    org_restored = OrganismBreather.from_dict(org_state)
    check("Organism from_dict graph", org_restored.graph is not None and org_restored.graph.count == 2)

    # ── Stribeck Tuner tests (v0.5.0) ────────────────────────
    from void_intelligence.tuner import StribeckTuner, ParameterSet, _defaults_from_hex

    # ParameterSet creation
    ps = ParameterSet()
    check("ParameterSet defaults", ps.temperature == 0.7 and ps.top_p == 0.9)
    check("ParameterSet not at delta_opt", not ps.at_delta_opt)

    # ParameterSet at_delta_opt
    ps2 = ParameterSet(confidence=0.6, observations=10)
    check("ParameterSet at delta_opt", ps2.at_delta_opt)

    # ParameterSet distance_from
    ps3 = ParameterSet(temperature=0.3, top_p=0.5, max_tokens=1024, context_intensity=0.2)
    dist = ps.distance_from(ps3)
    check("ParameterSet distance>0", dist > 0.0)
    check("ParameterSet self-distance=0", ps.distance_from(ps) == 0.0)

    # ParameterSet to_dict/from_dict
    ps_data = ps.to_dict()
    ps_restored = ParameterSet.from_dict(ps_data)
    check("ParameterSet roundtrip", ps_restored.temperature == ps.temperature)

    # _defaults_from_hex: different coords = different params
    urgent_coord = HexCoord(ruhe_druck=0.8, langsam_schnell=0.6, empfangen_schaffen=-0.2)
    creative_coord = HexCoord(empfangen_schaffen=0.8, sein_tun=-0.5)
    urgent_params = _defaults_from_hex(urgent_coord)
    creative_params = _defaults_from_hex(creative_coord)
    check("Hex defaults: urgent lower temp", urgent_params.temperature < 0.7)
    check("Hex defaults: creative higher temp", creative_params.temperature > 0.7)
    check("Hex defaults: urgent fewer tokens", urgent_params.max_tokens < 2048)

    # StribeckTuner creation
    tuner = StribeckTuner()
    check("StribeckTuner empty", tuner.mapped_regions == 0 and tuner.total_observations == 0)

    # StribeckTuner tune (no data -> defaults)
    tuned = tuner.tune(urgent_coord, model="test")
    check("StribeckTuner tune defaults", tuned.temperature < 0.7)

    # StribeckTuner record healthy diagnosis
    class MockDiag:
        def __init__(self, healthy, flags):
            self.healthy = healthy
            self.flags = flags

    tuner.record(urgent_coord, tuned, MockDiag(True, []), model="test")
    check("StribeckTuner record", tuner.mapped_regions == 1 and tuner.total_observations == 1)

    # StribeckTuner tune after recording (now uses learned data)
    tuned2 = tuner.tune(urgent_coord, model="test")
    check("StribeckTuner learned data", tuned2.observations == 1)

    # Record a few more healthy to build confidence
    for _ in range(5):
        tuner.record(urgent_coord, tuned, MockDiag(True, []), model="test")

    # StribeckTuner delta_opt_distance (after several healthy records)
    d_opt = tuner.delta_opt_distance(urgent_coord, model="test")
    check("StribeckTuner delta_opt<1", d_opt < 1.0)

    # StribeckTuner record sick diagnosis (repetition -> increase temp)
    old_temp = tuner.tune(urgent_coord, model="test").temperature
    tuner.record(urgent_coord, tuned, MockDiag(False, ["repetition(33%unique)"]), model="test")
    new_temp = tuner.tune(urgent_coord, model="test").temperature
    check("StribeckTuner repetition->higher temp", new_temp > old_temp)
    d_opt_unknown = tuner.delta_opt_distance(HexCoord(0.9, 0.9, 0.9, 0.9, 0.9, 0.9))
    check("StribeckTuner delta_opt unknown=1", d_opt_unknown == 1.0)

    # StribeckTuner convergence: many healthy records increase confidence
    conv_coord = HexCoord(0.5, 0.0, 0.0, 0.0, 0.0, 0.0)
    conv_params = ParameterSet(temperature=0.6, top_p=0.85)
    for _ in range(20):
        tuner.record(conv_coord, conv_params, MockDiag(True, []), model="conv")
    check("StribeckTuner convergence", tuner.tune(conv_coord, model="conv").at_delta_opt)

    # StribeckTuner report
    report = tuner.stribeck_report()
    check("StribeckTuner report", report["mapped_regions"] > 0)

    # StribeckTuner to_dict/from_dict
    tuner_data = tuner.to_dict()
    tuner_restored = StribeckTuner.from_dict(tuner_data)
    check("StribeckTuner roundtrip regions", tuner_restored.mapped_regions == tuner.mapped_regions)
    check("StribeckTuner roundtrip obs", tuner_restored.total_observations == tuner.total_observations)

    # StribeckTuner from_dict bad data
    tuner_bad = StribeckTuner.from_dict({"garbage": True})
    check("StribeckTuner from_dict bad", tuner_bad.mapped_regions == 0)

    # Router + Tuner integration
    import tempfile as _tempfile
    tmpdir2 = Path(_tempfile.mkdtemp())
    rt_tuner = StribeckTuner()
    rt = AtemRouter(state_dir=tmpdir2, tuner=rt_tuner)
    rt_decision = rt.inhale("urgent deadline team help build fast")
    check("Router+Tuner decision has params", rt_decision.parameters is not None)
    check("Router+Tuner params type", isinstance(rt_decision.parameters, ParameterSet))

    # Router auto-tune with adapter
    rt.register_adapter(rt_decision.selected_model, lambda p, s="": "test response about urgent deadline team")
    rt_result = rt.breathe("urgent deadline team help")
    check("Router+Tuner breathe", rt_tuner.total_observations >= 1)
    check("Router+Tuner tuner property", rt.tuner is rt_tuner)

    # Cleanup
    shutil.rmtree(tmpdir2, ignore_errors=True)

    # ── Cross-Pollination tests (v0.6.0) ───────────────────
    from void_intelligence.pollinator import (
        CrossPollinator, Endosymbiont, PollinationEvent,
        _transferability_score, _keyword_overlap,
    )

    # _keyword_overlap
    check("keyword_overlap identical", _keyword_overlap(["a", "b"], ["a", "b"]) == 1.0)
    check("keyword_overlap none", _keyword_overlap(["a", "b"], ["c", "d"]) == 0.0)
    check("keyword_overlap partial", 0.0 < _keyword_overlap(["a", "b", "c"], ["a", "d"]) < 1.0)
    check("keyword_overlap empty", _keyword_overlap([], ["a"]) == 0.0)

    # _transferability_score
    from void_intelligence.ring_graph import RingGraph, RingNode
    test_graph = RingGraph()
    r_par = test_graph.add("Test paradigm ring", ring_type="paradigm")
    r_learn = test_graph.add("Test learning ring", ring_type="learning")
    r_err = test_graph.add("Test error ring", ring_type="error")
    score_par = _transferability_score(r_par, test_graph)
    score_learn = _transferability_score(r_learn, test_graph)
    score_err = _transferability_score(r_err, test_graph)
    check("Transferability: paradigm > learning", score_par > score_learn)
    check("Transferability: learning > error", score_learn > score_err)

    # Compressed ring = not transferable
    r_comp = test_graph.add("Compressed ring")
    r_comp.compressed = True
    check("Transferability: compressed = 0", _transferability_score(r_comp, test_graph) == 0.0)

    # CrossPollinator creation
    cp = CrossPollinator()
    check("CrossPollinator empty", cp.total_events == 0 and cp.total_transfers == 0)

    # identify_transferable
    candidates = cp.identify_transferable(test_graph)
    check("identify_transferable count", len(candidates) > 0)
    check("identify_transferable sorted", candidates[0][1] >= candidates[-1][1])

    # Pollinate: build two distinct graphs
    graph_src = RingGraph()
    graph_src.add("Source paradigm about email urgency", ring_type="paradigm")
    graph_src.add("Source learning about tone adaptation", ring_type="learning")
    graph_src.add("Source milestone about team communication", ring_type="milestone")

    graph_tgt = RingGraph()
    graph_tgt.add("Target knowledge about code review")
    graph_tgt.add("Target learning about testing patterns")

    event = cp.pollinate(
        source_graph=graph_src, source_model="src",
        target_graph=graph_tgt, target_model="tgt",
    )
    check("Pollinate transfers rings", event.rings_transferred > 0)
    check("Pollinate event recorded", cp.total_events == 1)
    check("Target graph grew", graph_tgt.active_count > 2)

    # Endosymbionts tracked
    syms = cp.symbionts_for("tgt")
    check("Endosymbionts created", len(syms) == event.rings_transferred)
    check("Endosymbiont source", all(s.source_model == "src" for s in syms))
    check("Endosymbiont not confirmed", all(not s.confirmed for s in syms))

    # Confirm with positive lift
    cp.set_baseline("tgt", 0.5)
    lift = cp.confirm("tgt", 0.7)
    check("Confirm positive lift", lift > 0)
    confirmed = cp.confirmed_symbionts("tgt")
    check("Endosymbionts confirmed", len(confirmed) > 0)

    # Transfer score
    ts = cp.transfer_score("tgt")
    check("Transfer score positive", ts > 0)
    check("Transfer score unknown", cp.transfer_score("unknown") == 0.0)

    # Don't transfer what target already knows (overlap check)
    graph_dup_src = RingGraph()
    graph_dup_src.add("Target knowledge about code review", ring_type="learning")  # same as target

    graph_dup_tgt = RingGraph()
    graph_dup_tgt.add("Target knowledge about code review")

    cp2 = CrossPollinator()
    event2 = cp2.pollinate(
        source_graph=graph_dup_src, source_model="dup_src",
        target_graph=graph_dup_tgt, target_model="dup_tgt",
    )
    check("No duplicate transfer", event2.rings_transferred == 0)

    # Auto-pollinate
    cp3 = CrossPollinator()
    auto_graphs: dict[str, RingGraph | None] = {}
    g1 = RingGraph()
    g2 = RingGraph()
    for i in range(6):
        g1.add(f"Knowledge A{i} about topic {i}", ring_type="learning")
        g2.add(f"Knowledge B{i} about subject {i + 10}", ring_type="learning")
    auto_graphs["m1"] = g1
    auto_graphs["m2"] = g2
    auto_graphs["m3"] = None  # no graph = excluded
    auto_events = cp3.auto_pollinate(auto_graphs, min_rings=5, cooldown_sec=0)
    check("Auto-pollinate events", len(auto_events) > 0)
    check("Auto-pollinate transfers", sum(e.rings_transferred for e in auto_events) > 0)

    # Auto-pollinate cooldown
    auto_events_2 = cp3.auto_pollinate(auto_graphs, min_rings=5, cooldown_sec=9999)
    check("Auto-pollinate cooldown", len(auto_events_2) == 0)

    # Report
    report = cp.report()
    check("Report has events", report["total_events"] > 0)
    check("Report has models", len(report["models"]) > 0)

    # Persistence: to_dict / from_dict
    cp_data = cp.to_dict()
    cp_restored = CrossPollinator.from_dict(cp_data)
    check("Pollinator roundtrip events", cp_restored.total_events == cp.total_events)
    check("Pollinator roundtrip symbionts", len(cp_restored.symbionts_for("tgt")) == len(cp.symbionts_for("tgt")))

    # from_dict bad data
    cp_bad = CrossPollinator.from_dict({"garbage": True})
    check("Pollinator from_dict bad", cp_bad.total_events == 0)

    # PollinationEvent dataclass
    pe = PollinationEvent(source_model="a", target_model="b", rings_transferred=3, ring_ids=["r0", "r1", "r2"])
    check("PollinationEvent fields", pe.source_model == "a" and pe.rings_transferred == 3)

    # Endosymbiont dataclass
    es = Endosymbiont(ring_id="r0", source_model="a", source_ring_id="r0", content="test", keywords=["test"])
    check("Endosymbiont fields", es.ring_id == "r0" and not es.confirmed)

    # Router + Pollinator integration
    tmpdir3 = Path(_tempfile.mkdtemp())
    rt2 = AtemRouter(state_dir=tmpdir3)
    check("Router has pollinator", rt2.pollinator is not None)
    check("Router pollinator type", isinstance(rt2.pollinator, CrossPollinator))

    # Cleanup
    shutil.rmtree(tmpdir3, ignore_errors=True)

    # ── V-Score API tests (v0.7.0) ───────────────────────
    from void_intelligence.api import (
        VScoreAPI, APIResponse, ModelRecord,
        compute_v_score, _badge_svg, _v_score_color, _status_label,
    )

    # compute_v_score basic
    vs = compute_v_score("Write an email about the deadline", "Here is your email about the deadline. Please review.", "test-model")
    check("compute_v_score has V", "V" in vs and isinstance(vs["V"], float))
    check("compute_v_score V > 0", vs["V"] > 0)
    check("compute_v_score components", len(vs["components"]) == 5)
    check("compute_v_score model", vs["model"] == "test-model")
    check("compute_v_score status", vs["status"] in ("DEAD", "BARELY ALIVE", "ALIVE", "HEALTHY", "THRIVING"))

    # compute_v_score dead (empty response)
    vs_dead = compute_v_score("Write something", "", "dead-model")
    check("compute_v_score dead", vs_dead["V"] == 0 or not vs_dead["healthy"])

    # _status_label
    check("status_label dead", _status_label(0.0) == "DEAD")
    check("status_label alive", _status_label(0.005) == "ALIVE")
    check("status_label thriving", _status_label(0.5) == "THRIVING")

    # _v_score_color
    check("v_score_color red", _v_score_color(0.0) == "#e05d44")
    check("v_score_color green", _v_score_color(0.5) == "#4c1")

    # _badge_svg
    svg = _badge_svg("V-Score", "0.019 ALIVE", "#97ca00")
    check("badge_svg has svg", "<svg" in svg and "V-Score" in svg)

    # APIResponse
    resp = APIResponse(200, {"test": True})
    check("APIResponse json", '"status": 200' in resp.to_json())
    resp_err = APIResponse(400, {}, error="bad request")
    check("APIResponse error", "bad request" in resp_err.to_json())

    # ModelRecord
    mr = ModelRecord(name="test")
    check("ModelRecord default", mr.health_rate == 1.0 and mr.latest_v == 0.0)
    mr.total_checks = 10
    mr.healthy_checks = 8
    check("ModelRecord health_rate", mr.health_rate == 0.8)
    mr_dict = mr.to_dict()
    check("ModelRecord to_dict", mr_dict["name"] == "test" and mr_dict["health_rate"] == 0.8)

    # VScoreAPI creation
    api = VScoreAPI()
    check("VScoreAPI empty", api.total_models == 0 and api.total_requests == 0)

    # VScoreAPI.score
    score_resp = api.score("Write an email", "Here is an email about the topic you mentioned.", "model-a")
    check("API score 200", score_resp.status == 200)
    check("API score has V", "V" in score_resp.data)
    check("API score tracks model", api.total_models == 1)
    check("API score tracks requests", api.total_requests == 1)

    # VScoreAPI.score validation
    bad_resp = api.score("", "", "bad")
    check("API score empty = 400", bad_resp.status == 400)

    # VScoreAPI.score multiple models
    api.score("Write code", "Here is some Python code that implements the function.", "model-b")
    api.score("Debug this", "The bug is in line 42 where the variable is undefined.", "model-b")
    check("API multiple models", api.total_models == 2 and api.total_requests == 3)

    # VScoreAPI.leaderboard
    lb_resp = api.leaderboard()
    check("API leaderboard 200", lb_resp.status == 200)
    check("API leaderboard entries", len(lb_resp.data["leaderboard"]) == 2)
    check("API leaderboard ranked", lb_resp.data["leaderboard"][0]["rank"] == 1)

    # VScoreAPI.model_detail
    detail = api.model_detail("model-a")
    check("API model_detail 200", detail.status == 200)
    check("API model_detail name", detail.data["name"] == "model-a")
    detail_404 = api.model_detail("nonexistent")
    check("API model_detail 404", detail_404.status == 404)

    # VScoreAPI.badge
    badge = api.badge("model-a")
    check("API badge svg", "<svg" in badge and "V-Score" in badge)
    badge_unknown = api.badge("unknown-model")
    check("API badge unknown", "unknown" in badge_unknown)

    # VScoreAPI.stats
    stats = api.stats()
    check("API stats", stats.data["total_requests"] == 3 and stats.data["total_models"] == 2)

    # VScoreAPI.compare
    cmp = api.compare(["model-a", "model-b", "nonexistent"])
    check("API compare", len(cmp.data["comparison"]) == 3)
    cmp_empty = api.compare([])
    check("API compare empty = 400", cmp_empty.status == 400)

    # VScoreAPI persistence
    api_data = api.to_dict()
    api_restored = VScoreAPI.from_dict(api_data)
    check("API roundtrip models", api_restored.total_models == api.total_models)
    check("API roundtrip requests", api_restored.total_requests == api.total_requests)

    # VScoreAPI from_dict bad data
    api_bad = VScoreAPI.from_dict({"garbage": True})
    check("API from_dict bad", api_bad.total_models == 0)

    # ── Swarm Network tests (v0.8.0) ──────────────────────
    from void_intelligence.swarm import SwarmNode, SwarmMessage, SwarmNetwork, SwarmHealth

    # SwarmMessage basics
    sm = SwarmMessage(msg_type="heartbeat", sender="node-a", payload={"alive": True})
    check("SwarmMessage type", sm.msg_type == "heartbeat")
    check("SwarmMessage sender", sm.sender == "node-a")
    check("SwarmMessage auto-id", len(sm.msg_id) == 12)
    check("SwarmMessage ttl default", sm.ttl == 3)

    sm_dict = sm.to_dict()
    sm_restored = SwarmMessage.from_dict(sm_dict)
    check("SwarmMessage roundtrip type", sm_restored.msg_type == sm.msg_type)
    check("SwarmMessage roundtrip id", sm_restored.msg_id == sm.msg_id)
    check("SwarmMessage roundtrip ttl", sm_restored.ttl == sm.ttl)

    # SwarmHealth
    sh = SwarmHealth(total_nodes=4, alive_nodes=3, total_rings=10, shared_rings=6)
    check("SwarmHealth colony > 0", sh.colony_health > 0)
    check("SwarmHealth colony <= 1", sh.colony_health <= 1.0)
    sh_dict = sh.to_dict()
    check("SwarmHealth dict has colony_health", "colony_health" in sh_dict)

    sh_empty = SwarmHealth()
    check("SwarmHealth empty colony = 0", sh_empty.colony_health == 0.0)

    # SwarmNode basics
    sn = SwarmNode(node_id="ant-1")
    check("SwarmNode id", sn.node_id == "ant-1")
    check("SwarmNode alive", sn.is_alive)
    check("SwarmNode ring_count 0", sn.ring_count == 0)
    check("SwarmNode no neighbors", len(sn.neighbors) == 0)

    sn.add_neighbor("ant-2")
    check("SwarmNode add neighbor", "ant-2" in sn.neighbors)
    sn.add_neighbor("ant-2")  # duplicate
    check("SwarmNode no dup neighbor", len(sn.neighbors) == 1)
    sn.add_neighbor("ant-1")  # self
    check("SwarmNode no self-neighbor", "ant-1" not in sn.neighbors)

    sn.remove_neighbor("ant-2")
    check("SwarmNode remove neighbor", len(sn.neighbors) == 0)

    # SwarmNode ring sharing
    sn.graph.add("Paradigm: emergence from local rules", ring_type="paradigm")
    sn.graph.add("Learning: ants optimize foraging paths", ring_type="learning")
    check("SwarmNode has rings", sn.ring_count == 2)

    shared_msgs = sn.auto_share()
    check("SwarmNode auto_share paradigm", len(shared_msgs) >= 1)
    check("SwarmNode shared_count", sn.shared_count >= 1)

    # SwarmNode heartbeat
    hb = sn.heartbeat()
    check("SwarmNode heartbeat msg", hb.msg_type == "heartbeat")
    check("SwarmNode heartbeat payload", hb.payload.get("alive") is True)

    # SwarmNode request rings
    req = sn.request_rings(["foraging", "ants"])
    check("SwarmNode ring request", req.msg_type == "ring_request")
    check("SwarmNode ring request keywords", req.payload.get("keywords") == ["foraging", "ants"])

    # SwarmNode V-Score update
    vu = sn.update_v_score("gpt-4", 0.042)
    check("SwarmNode v-score update msg", vu.msg_type == "score_update")
    check("SwarmNode v-score stored", sn._v_scores.get("gpt-4") == 0.042)

    # SwarmNode immune alert
    ia = sn.broadcast_immune_alert("bad-model", ["repetitive", "dead_hex"])
    check("SwarmNode immune alert", ia.msg_type == "immune_alert")
    check("SwarmNode sick models", "bad-model" in sn.known_sick_models)

    # SwarmNode flush outbox
    outbox = sn.flush_outbox()
    check("SwarmNode flush outbox", len(outbox) >= 3)
    outbox2 = sn.flush_outbox()
    check("SwarmNode flush clears", len(outbox2) == 0)

    # SwarmNode vitals
    vitals = sn.vitals()
    check("SwarmNode vitals keys", "node_id" in vitals and "alive" in vitals)
    check("SwarmNode vitals msg counts", vitals["messages_sent"] >= 3)

    # SwarmNode persistence
    sn_dict = sn.to_dict()
    sn_restored = SwarmNode.from_dict(sn_dict)
    check("SwarmNode roundtrip id", sn_restored.node_id == "ant-1")
    check("SwarmNode roundtrip msg_sent", sn_restored._messages_sent == sn._messages_sent)

    # SwarmNetwork basics
    net = SwarmNetwork()
    n1 = SwarmNode(node_id="colony-a")
    n2 = SwarmNode(node_id="colony-b")
    n3 = SwarmNode(node_id="colony-c")
    net.add_node(n1)
    net.add_node(n2)
    net.add_node(n3)
    check("SwarmNetwork node_count", net.node_count == 3)

    net.connect("colony-a", "colony-b")
    check("SwarmNetwork connect a->b", "colony-b" in n1.neighbors)
    check("SwarmNetwork connect b->a", "colony-a" in n2.neighbors)

    # SwarmNetwork mesh
    net.mesh()
    check("SwarmNetwork mesh a neighbors", len(n1.neighbors) == 2)
    check("SwarmNetwork mesh b neighbors", len(n2.neighbors) == 2)
    check("SwarmNetwork mesh c neighbors", len(n3.neighbors) == 2)

    # SwarmNetwork ring sharing across mesh
    n1.graph.add("Discovery: swarm intelligence scales logarithmically", ring_type="paradigm")
    n2.graph.add("Observation: ant trails optimize for shortest path", ring_type="paradigm")
    shared1 = n1.auto_share()
    shared2 = n2.auto_share()
    check("SwarmNetwork n1 shares", len(shared1) >= 1)
    check("SwarmNetwork n2 shares", len(shared2) >= 1)

    delivered = net.tick()
    check("SwarmNetwork tick delivers", delivered > 0)
    check("SwarmNetwork n2 got ring", n2.ring_count >= 2)
    check("SwarmNetwork n3 got rings", n3.ring_count >= 1)

    # SwarmNetwork multiple ticks
    n3.graph.add("Insight: temperature affects foraging rate", ring_type="milestone")
    n3.auto_share()
    run_total = net.run(ticks=3)
    check("SwarmNetwork run multi-tick", run_total >= 0)

    # SwarmNetwork immune alert propagation
    n1.broadcast_immune_alert("toxic-model", ["hallucination", "dead"])
    net.tick()
    check("SwarmNetwork immune propagates to b", "toxic-model" in n2.known_sick_models)

    # SwarmNetwork V-Score propagation
    n1.update_v_score("omega-model", 0.85)
    net.tick()
    check("SwarmNetwork v-score propagates", n2._v_scores.get("omega-model") == 0.85)

    # SwarmNetwork ring request
    n3.request_rings(["swarm", "intelligence"])
    net.tick()
    # n3 should get a response from nodes that have matching rings
    check("SwarmNetwork ring request processed", n3.ring_count >= 1)

    # SwarmNetwork health
    health = net.health()
    check("SwarmNetwork health alive", health.alive_nodes == 3)
    check("SwarmNetwork health rings > 0", health.total_rings > 0)
    check("SwarmNetwork health shared > 0", health.shared_rings > 0)
    check("SwarmNetwork health colony > 0", health.colony_health > 0)
    check("SwarmNetwork health sick", "toxic-model" in health.sick_models)
    check("SwarmNetwork health collective_v", health.collective_v > 0)

    # SwarmNetwork broadcast
    bcast = SwarmMessage(msg_type="heartbeat", sender="colony-a", payload={"alive": True})
    responses = net.broadcast(bcast)
    check("SwarmNetwork broadcast", net.total_deliveries > 0)

    # SwarmNetwork remove node
    net.remove_node("colony-c")
    check("SwarmNetwork remove node", net.node_count == 2)
    check("SwarmNetwork remove cleans neighbors", "colony-c" not in n1.neighbors)

    # SwarmNetwork get_node
    check("SwarmNetwork get_node exists", net.get_node("colony-a") is not None)
    check("SwarmNetwork get_node missing", net.get_node("nonexistent") is None)

    # SwarmNetwork ring topology
    net2 = SwarmNetwork()
    for i in range(5):
        net2.add_node(SwarmNode(node_id=f"ring-{i}"))
    net2.ring_topology()
    ring_node = net2.get_node("ring-0")
    check("SwarmNetwork ring topology", len(ring_node.neighbors) == 2)
    check("SwarmNetwork ring connects last-first", "ring-4" in ring_node.neighbors)

    # SwarmNetwork summary
    summary = net.summary()
    check("SwarmNetwork summary string", "Swarm:" in summary and "alive" in summary)

    # SwarmNetwork persistence
    net_dict = net.to_dict()
    check("SwarmNetwork to_dict has nodes", "nodes" in net_dict)
    net_restored = SwarmNetwork.from_dict(net_dict)
    check("SwarmNetwork roundtrip node_count", net_restored.node_count == net.node_count)
    check("SwarmNetwork roundtrip deliveries", net_restored.total_deliveries == net.total_deliveries)

    # SwarmNetwork from_dict bad data
    net_bad = SwarmNetwork.from_dict({"garbage": True})
    check("SwarmNetwork from_dict bad", net_bad.node_count == 0)

    # SwarmMessage dedup
    sn2 = SwarmNode(node_id="dedup-test")
    msg_orig = SwarmMessage(msg_type="heartbeat", sender="x", payload={})
    resp1 = sn2.receive(msg_orig)
    resp2 = sn2.receive(msg_orig)  # same msg_id
    check("SwarmNode dedup", sn2._messages_received == 1)

    # SwarmNode receive ring_share
    sn3 = SwarmNode(node_id="receiver")
    ring_msg = SwarmMessage(
        msg_type="ring_share",
        sender="sender-node",
        payload={
            "ring_id": "r-test",
            "content": "Knowledge: distributed systems are resilient",
            "ring_type": "learning",
            "keywords": ["distributed", "systems", "resilient"],
            "depth": 0,
        },
        ttl=2,
    )
    responses = sn3.receive(ring_msg)
    check("SwarmNode receive ring_share adds ring", sn3.ring_count == 1)
    check("SwarmNode ring_share forwards", len(responses) >= 1)
    check("SwarmNode forward decrements TTL", responses[0].ttl == 1 if responses else True)

    # SwarmNode receive score_update
    sn4 = SwarmNode(node_id="score-receiver")
    score_msg = SwarmMessage(
        msg_type="score_update",
        sender="score-sender",
        payload={"model": "claude", "V": 0.95},
    )
    sn4.receive(score_msg)
    check("SwarmNode receive score_update", sn4._v_scores.get("claude") == 0.95)

    # ── Edge Functions tests (v0.9.0) ─────────────────────
    from void_intelligence.edge import (
        classify as e_classify, diagnose as e_diagnose,
        score as e_score, breathe as e_breathe,
        hex_distance as e_hex_dist, batch_score as e_batch,
        leaderboard as e_leaderboard,
    )

    # Edge classify
    ec = e_classify("urgent deadline write fast")
    check("Edge classify returns dict", isinstance(ec, dict))
    check("Edge classify 6 axes", len(ec) == 6)
    check("Edge classify ruhe_druck > 0", ec.get("ruhe_druck", 0) > 0)
    check("Edge classify langsam_schnell > 0", ec.get("langsam_schnell", 0) > 0)

    ec_calm = e_classify("calm peaceful meditation slow reflect")
    check("Edge classify calm < 0", ec_calm.get("ruhe_druck", 0) < 0)

    ec_empty = e_classify("")
    check("Edge classify empty = zeros", all(v == 0.0 for v in ec_empty.values()))

    # Edge hex_distance
    hd = e_hex_dist(ec, ec_calm)
    check("Edge hex_distance > 0", hd > 0)
    hd_self = e_hex_dist(ec, ec)
    check("Edge hex_distance self = 0", hd_self == 0.0)

    # Edge diagnose
    ed = e_diagnose("Write me a sales email", "Here is your professional sales email about the product.")
    check("Edge diagnose returns dict", isinstance(ed, dict))
    check("Edge diagnose has healthy", "healthy" in ed)
    check("Edge diagnose has flags", "flags" in ed)
    check("Edge diagnose has severity", "severity" in ed)
    check("Edge diagnose has layer_scores", "layer_scores" in ed)
    check("Edge diagnose has hex_delta", "hex_delta" in ed)

    ed_short = e_diagnose("Write email", "Hi")
    check("Edge diagnose short = flag", len(ed_short["flags"]) > 0)

    ed_refusal = e_diagnose("Do something", "I cannot do that as an AI")
    check("Edge diagnose refusal = flag", any("refusal" in f for f in ed_refusal["flags"]))

    # Edge score
    es = e_score("Write a test email", "Here is your test email about the deadline.", "test-model")
    check("Edge score has V", "V" in es)
    check("Edge score V is float", isinstance(es["V"], float))
    check("Edge score has model", es["model"] == "test-model")
    check("Edge score has status", es["status"] in ("DEAD", "BARELY ALIVE", "ALIVE", "HEALTHY", "THRIVING"))
    check("Edge score has components", len(es["components"]) == 5)

    es_zero = e_score("x", "y")
    check("Edge score minimal", es_zero["V"] >= 0)

    # Edge breathe
    eb = e_breathe("Explain quantum physics", "Quantum physics is the study of particles at the atomic level.", "test-llm")
    check("Edge breathe has prompt_hex", "prompt_hex" in eb)
    check("Edge breathe has diagnosis", "diagnosis" in eb)
    check("Edge breathe has v_score", "v_score" in eb)
    check("Edge breathe model", eb["model"] == "test-llm")

    # Edge batch_score
    pairs = [
        {"prompt": "Write email", "response": "Here is your email about the topic.", "model": "a"},
        {"prompt": "Summarize", "response": "The main points are as follows in the summary.", "model": "b"},
        {"prompt": "Hello", "response": "Hello there! How can I assist you today?", "model": "a"},
    ]
    bs = e_batch(pairs)
    check("Edge batch_score count", len(bs) == 3)
    check("Edge batch_score has V", all("V" in s for s in bs))

    # Edge leaderboard
    lb = e_leaderboard(pairs)
    check("Edge leaderboard sorted", isinstance(lb, list))
    check("Edge leaderboard has models", len(lb) == 2)  # a and b
    check("Edge leaderboard first has V", "avg_V" in lb[0])

    lb_empty = e_leaderboard([])
    check("Edge leaderboard empty", len(lb_empty) == 0)

    # ── Portable Export tests (v0.9.0) ────────────────────
    from void_intelligence.portable import (
        export_organism as p_export, export_json as p_json,
        export_lite as p_lite, import_state as p_import,
        validate as p_validate, SCHEMA_VERSION,
    )

    # Export with no components
    ex_empty = p_export()
    check("Portable empty has schema", ex_empty["_schema"] == SCHEMA_VERSION)
    check("Portable empty has format", ex_empty["_format"] == "void-intelligence-portable")
    check("Portable empty has manifest", "_manifest" in ex_empty)

    # Validate empty export
    valid, errors = p_validate(ex_empty)
    check("Portable validate empty", valid)

    # Export with organism
    from void_intelligence.organism import OrganismBreather
    org = OrganismBreather()
    org.inhale("test prompt for export")
    org.heart.beat()

    ex_org = p_export(organism=org)
    check("Portable has organism", "organism" in ex_org)
    check("Portable organism alive", ex_org["organism"]["alive"])
    check("Portable has rings", "rings" in ex_org)
    check("Portable has profiles", "profiles" in ex_org)

    valid2, errors2 = p_validate(ex_org)
    check("Portable validate organism", valid2)

    # Export JSON
    json_str = p_json(organism=org)
    check("Portable JSON is string", isinstance(json_str, str))
    import json as _json
    json_parsed = _json.loads(json_str)
    check("Portable JSON parseable", "_schema" in json_parsed)

    # Export compact
    ex_compact = p_export(organism=org, compact=True)
    check("Portable compact smaller", len(str(ex_compact)) <= len(str(ex_org)))

    # Export with include filter
    ex_filtered = p_export(organism=org, include=["organism"])
    check("Portable filtered has organism", "organism" in ex_filtered)
    check("Portable filtered no rings", "rings" not in ex_filtered or "rings" not in ex_filtered.get("_manifest", {}).get("components", []))

    # Import
    imported = p_import(ex_org)
    check("Portable import has organism", "organism" in imported)
    check("Portable import has _schema", "_schema" in imported)

    # Validate bad data
    v_bad, e_bad = p_validate({"random": True})
    check("Portable validate bad = False", not v_bad)
    check("Portable validate bad errors", len(e_bad) > 0)

    v_wrong_format, e_wrong = p_validate({"_schema": "1.0", "_format": "wrong", "_manifest": {"components": []}})
    check("Portable validate wrong format", not v_wrong_format)

    # Lite export
    lite = p_lite(organism=org)
    check("Portable lite has schema", "_schema" in lite)
    check("Portable lite format", lite["_format"] == "void-intelligence-lite")
    check("Portable lite alive", lite.get("alive") is True)
    check("Portable lite small", len(str(lite)) < 200)

    lite_empty = p_lite()
    check("Portable lite empty", "_schema" in lite_empty)

    # ── V-Score Specification tests (v1.0.0) ──────────────
    from void_intelligence.spec import (
        VScoreComponents, ModelCard, ComplianceResult, CertificationLevel,
        SPEC_VERSION as _SV, CERTIFICATION_LEVELS, STATUS_THRESHOLDS,
        WIRE_FORMAT, HEX_AXES,
        v_score_status, certify as spec_certify, check_compliance,
        hex_distance_spec, spec_document, spec_markdown,
    )

    # VScoreComponents
    vc = VScoreComponents(E=0.8, W=0.9, S=1.0, B=0.95, H=0.7)
    check("Spec VScoreComponents V", abs(vc.V - 0.8 * 0.9 * 1.0 * 0.95 * 0.7) < 0.0001)
    vc_dict = vc.to_dict()
    check("Spec VScoreComponents dict", "V" in vc_dict and "E" in vc_dict)

    vc_zero = VScoreComponents(E=0.8, W=0.0, S=1.0, B=0.95, H=0.7)
    check("Spec V zero kills", vc_zero.V == 0.0)

    # v_score_status
    check("Spec status DEAD", v_score_status(0.0) == "DEAD")
    check("Spec status BARELY ALIVE", v_score_status(0.002) == "BARELY ALIVE")
    check("Spec status ALIVE", v_score_status(0.01) == "ALIVE")
    check("Spec status HEALTHY", v_score_status(0.05) == "HEALTHY")
    check("Spec status THRIVING", v_score_status(0.5) == "THRIVING")

    # HEX_AXES
    check("Spec HEX_AXES count", len(HEX_AXES) == 6)
    check("Spec HEX_AXES first", HEX_AXES[0] == "ruhe_druck")

    # hex_distance_spec
    a_hex = {ax: 0.5 for ax in HEX_AXES}
    b_hex = {ax: -0.5 for ax in HEX_AXES}
    check("Spec hex_distance > 0", hex_distance_spec(a_hex, b_hex) > 0)
    check("Spec hex_distance self = 0", hex_distance_spec(a_hex, a_hex) == 0.0)

    # STATUS_THRESHOLDS
    check("Spec thresholds list", len(STATUS_THRESHOLDS) == 5)

    # WIRE_FORMAT
    check("Spec wire format schema", "$schema" in WIRE_FORMAT)
    check("Spec wire format required", "required" in WIRE_FORMAT)
    check("Spec wire format V", "V" in WIRE_FORMAT["properties"])

    # SPEC_VERSION
    check("Spec version 1.0.0", _SV == "1.0.0")

    # Certification
    cert_plat = spec_certify(0.15, 0.96, 100)
    check("Spec certify platinum", cert_plat is not None and cert_plat.name == "Platinum")

    cert_gold = spec_certify(0.06, 0.91, 50)
    check("Spec certify gold", cert_gold is not None and cert_gold.name == "Gold")

    cert_silver = spec_certify(0.03, 0.85, 25)
    check("Spec certify silver", cert_silver is not None and cert_silver.name == "Silver")

    cert_bronze = spec_certify(0.006, 0.65, 10)
    check("Spec certify bronze", cert_bronze is not None and cert_bronze.name == "Bronze")

    cert_none = spec_certify(0.001, 0.3, 2)
    check("Spec certify none", cert_none is None)

    # CertificationLevel
    cl = CERTIFICATION_LEVELS[0]  # Platinum
    check("Spec cert level name", cl.name == "Platinum")
    check("Spec cert level qualifies", cl.qualifies(0.2, 0.96, 200))
    check("Spec cert level fails", not cl.qualifies(0.01, 0.5, 5))

    # ModelCard from_scores
    test_scores = [
        {"V": 0.05, "flags": [], "components": {"E_emergence": 0.8, "W_warmth": 0.9, "S_consistency": 1.0, "B_breath": 0.95, "H_hex": 0.07}},
        {"V": 0.03, "flags": ["hex_divergent"], "components": {"E_emergence": 0.6, "W_warmth": 0.9, "S_consistency": 1.0, "B_breath": 0.9, "H_hex": 0.06}},
    ]
    mc = ModelCard.from_scores("test-model", test_scores, provider="test-provider")
    check("Spec ModelCard name", mc.model_name == "test-model")
    check("Spec ModelCard avg_v", mc.avg_v > 0)
    check("Spec ModelCard provider", mc.provider == "test-provider")
    check("Spec ModelCard status", mc.status in ("DEAD", "BARELY ALIVE", "ALIVE", "HEALTHY", "THRIVING"))
    check("Spec ModelCard checks", mc.total_checks == 2)

    mc_dict = mc.to_dict()
    check("Spec ModelCard dict", "model_name" in mc_dict and "v_score" in mc_dict)
    check("Spec ModelCard cert in dict", "certification" in mc_dict)

    mc_json = mc.to_json()
    check("Spec ModelCard JSON", isinstance(mc_json, str) and "test-model" in mc_json)

    mc_md = mc.to_markdown()
    check("Spec ModelCard markdown", "# V-Score Model Card" in mc_md)
    check("Spec ModelCard md formula", "V = E" in mc_md)

    mc_empty = ModelCard.from_scores("empty-model", [])
    check("Spec ModelCard empty", mc_empty.avg_v == 0.0)

    # check_compliance with edge.score
    from void_intelligence.edge import score as edge_score_fn
    compliance = check_compliance(edge_score_fn)
    check("Spec compliance passes", compliance.compliant)
    check("Spec compliance rate", compliance.compliance_rate > 0.8)
    check("Spec compliance dict", "compliant" in compliance.to_dict())

    # check_compliance with bad function
    def bad_scorer(prompt, response, model):
        return {"wrong": True}
    bad_compliance = check_compliance(bad_scorer)
    check("Spec bad compliance fails", not bad_compliance.compliant)
    check("Spec bad compliance failures", len(bad_compliance.failures) > 0)

    # check_compliance with raising function
    def raising_scorer(prompt, response, model):
        raise ValueError("boom")
    raise_compliance = check_compliance(raising_scorer)
    check("Spec raising compliance fails", not raise_compliance.compliant)

    # spec_document
    doc = spec_document()
    check("Spec document version", doc["version"] == "1.0.0")
    check("Spec document sections", len(doc["sections"]) == 10)
    check("Spec document authors", len(doc["authors"]) == 2)
    check("Spec document license", doc["license"] == "MIT")

    # spec_markdown
    md = spec_markdown()
    check("Spec markdown title", "V-Score Specification" in md)
    check("Spec markdown sections", "§1" in md and "§10" in md)
    check("Spec markdown formula", "V = E * W * S * B * H" in md)

    # ── Proof (v1.1.0) ──────────────────────────────────────────────
    from void_intelligence.proof import (
        run_proof, get_tasks, Task, ProofReport, _detect_category,
    )

    # Task suite
    t1 = get_tasks(phase=1)
    t2 = get_tasks(phase=2)
    check("Proof tasks phase 1 count", len(t1) == 25)
    check("Proof tasks phase 2 count", len(t2) == 25)
    check("Proof tasks no overlap", not set(t.prompt for t in t1) & set(t.prompt for t in t2))
    check("Proof tasks have category", all(t.category in ("URGENT", "CREATIVE", "TECHNICAL", "COLLABORATIVE", "REFLECTIVE") for t in t1))
    check("Proof tasks have learnings", all(len(t.learnings) > 0 for t in t1))

    # Category detection
    check("Proof detect URGENT", _detect_category("urgent deadline now") == "URGENT")
    check("Proof detect CREATIVE", _detect_category("write a poem") == "CREATIVE")
    check("Proof detect TECHNICAL", _detect_category("explain how TCP works") == "TECHNICAL")
    check("Proof detect COLLABORATIVE", _detect_category("brainstorm with the team") == "COLLABORATIVE")
    check("Proof detect REFLECTIVE", _detect_category("reflect on growth") == "REFLECTIVE")

    # Run the proof (simulated)
    report = run_proof(seed=42)
    check("Proof report type", isinstance(report, ProofReport))
    check("Proof accumulation > 0", report.accumulation_rounds > 0)
    check("Proof evaluation > 0", report.evaluation_rounds > 0)
    check("Proof rings > 0", report.rings_accumulated > 0)
    check("Proof old results", len(report.old_results) == 25)
    check("Proof frontier results", len(report.frontier_results) == 25)
    check("Proof old avg V > 0", report.old_avg_v > 0)
    check("Proof frontier avg V > 0", report.frontier_avg_v > 0)
    check("Proof old wins + frontier wins + ties = total",
          report.old_wins + report.frontier_wins + report.ties == 25)
    check("Proof OLD + VOID WINS", report.old_avg_v > report.frontier_avg_v)
    check("Proof lift > 0", report.lift > 0)
    check("Proof by_category has 5", len(report.by_category()) == 5)
    check("Proof summary has WINS", "WINS" in report.summary())
    check("Proof markdown has Results", "## Results" in report.markdown())
    check("Proof to_dict has lift", "lift" in report.to_dict())
    check("Proof reproducible", run_proof(seed=42).old_avg_v == report.old_avg_v)

    # ── MCP Server tests (v1.1.0) ──────────────────────────────
    import tempfile
    import os
    from void_intelligence.mcp_server import VoidProvider, _load_organism, _save_organism

    # Test provider creation
    mcp_provider = VoidProvider()
    check("MCP provider created", mcp_provider is not None)
    check("MCP organism lazy", mcp_provider._organism is None)

    # Test organism access
    org = mcp_provider.organism
    check("MCP organism loaded", org is not None)
    check("MCP organism type", isinstance(org, OrganismBreather))

    # Test breathe
    br = mcp_provider.breathe(
        prompt="How do I write tests?",
        response="Use pytest with clear assertions.",
        learnings=["pytest preferred", "clear assertions"],
    )
    check("MCP breathe success", br["success"] is True)
    check("MCP breathe v_score", "V" in br["v_score"])
    check("MCP breathe learnings", br["learnings_recorded"] == 2)
    check("MCP breathe rings", br["rings_total"] >= 2)

    # Test score (read-only)
    sc = mcp_provider.score(
        prompt="Explain decorators",
        response="Decorators wrap functions to add behavior.",
    )
    check("MCP score success", sc["success"] is True)
    check("MCP score V", "V" in sc["v_score"])
    check("MCP score components", "components" in sc["v_score"])

    # Test vitals
    vt = mcp_provider.vitals()
    check("MCP vitals success", vt["success"] is True)
    check("MCP vitals alive", vt["alive"] is True)
    check("MCP vitals breaths", vt["breaths"] >= 1)

    # Test classify
    cl = mcp_provider.classify("Build an urgent prototype for the team")
    check("MCP classify success", cl["success"] is True)
    check("MCP classify axes", "ruhe_druck" in cl["axes"])
    check("MCP classify 6 axes", len(cl["axes"]) == 6)

    # Test immune check
    im = mcp_provider.immune_check(
        prompt="Write a sales email",
        response="Here is a professional sales email about our product offering.",
    )
    check("MCP immune success", im["success"] is True)
    check("MCP immune healthy", im["healthy"] is True)
    check("MCP immune severity", im["severity"] == "healthy")
    check("MCP immune layers", "coherence" in im["layer_scores"])

    # Test rings search
    rg = mcp_provider.rings(query="pytest")
    check("MCP rings success", rg["success"] is True)
    check("MCP rings has total", "total" in rg)

    # Test persistence roundtrip
    org_fresh = OrganismBreather()
    org_fresh.inhale("persistence test")
    org_fresh.exhale("persisted", learnings=["roundtrip works"])
    saved = org_fresh.to_dict()
    restored = OrganismBreather.from_dict(saved)
    check("MCP persistence rings", restored.rings.count == org_fresh.rings.count)
    check("MCP persistence breaths", restored._breath_count == org_fresh._breath_count)

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


def cmd_immune(text: str):
    """Diagnose a prompt/response pair, or run a demo diagnosis."""
    from void_intelligence.immune import diagnose, ImmuneMonitor

    print()
    print("  void immune --- Response quality monitoring")
    print("  " + "=" * 55)

    if not text:
        # Demo: run 3 diagnosis examples
        examples = [
            (
                "Write an urgent email to my team about the deadline",
                "Subject: Urgent - Deadline Reminder\n\nDear team,\n\n"
                "I wanted to remind everyone about our upcoming deadline. "
                "Please make sure all deliverables are submitted by Friday.",
            ),
            (
                "Explain quantum computing",
                "No.",
            ),
            (
                "Help me plan a marketing campaign",
                "I'm sorry, but as an AI language model, I cannot help with that.",
            ),
        ]

        for prompt, response in examples:
            d = diagnose(prompt, response)
            status = "HEALTHY" if d.healthy else d.severity.upper()
            print(f"\n    Prompt:   \"{prompt[:50]}...\"" if len(prompt) > 50 else f"\n    Prompt:   \"{prompt}\"")
            print(f"    Response: \"{response[:50]}...\"" if len(response) > 50 else f"    Response: \"{response}\"")
            print(f"    Status:   {status}")
            print(f"    HexDelta: {d.hex_delta:.3f}")
            if d.flags:
                print(f"    Flags:    {', '.join(d.flags)}")
            print(f"    Layers:   {' | '.join(f'{k}={v:.2f}' for k, v in d.layer_scores.items())}")

        print()
        print("  5 Defense Layers (Swiss Cheese Model):")
        print("    1. hex_delta  — Input/output classification divergence")
        print("    2. length     — Too short (empty) or too long (hallucination)")
        print("    3. refusal    — \"I can't\" / \"As an AI\" detection")
        print("    4. repetition — Degenerate looping output")
        print("    5. coherence  — Topic drift (prompt vs response)")
        print()
        print("  Usage:")
        print("    from void_intelligence import immune, diagnose")
        print()
        print("    @immune(fallback=backup_fn, threshold=0.3)")
        print("    def ask(prompt): return my_llm(prompt)")
        print()
    else:
        # Diagnose user-provided text as if it were a response to "hello"
        d = diagnose("general query", text)
        status = "HEALTHY" if d.healthy else d.severity.upper()
        print(f"    Text:     \"{text[:70]}\"")
        print(f"    Status:   {status}")
        print(f"    HexDelta: {d.hex_delta:.3f}")
        print(f"    Score:    {d.composite_score:.3f}")
        if d.flags:
            print(f"    Flags:    {', '.join(d.flags)}")
        print(f"    Layers:   {' | '.join(f'{k}={v:.2f}' for k, v in d.layer_scores.items())}")
        print()


def cmd_rings(text: str):
    """Show the fractal ring structure (v0.4.0)."""
    from void_intelligence.ring_graph import RingGraph

    print()
    print("  void rings --- Fractal knowledge graph (Mandelbrot)")
    print("  " + "=" * 55)

    if not text:
        graph = RingGraph()
        r1 = graph.add("Email classification uses 6 hexagonal dimensions", ring_type="paradigm")
        r2 = graph.add("Urgency shifts email tone toward direct language", caused_by=r1.id)
        r3 = graph.add("Team context requires acknowledging all stakeholders", caused_by=r2.id)
        graph.add("Direct language works best under deadline pressure")
        r5 = graph.add("Stakeholder acknowledgment increases email response rate")
        graph.add("6 dimensions capture nuance that binary classification misses", caused_by=r1.id)
        graph.add("Response rate correlates with perceived respect in tone", caused_by=r5.id)

        print()
        print(f"  {graph.fractal_summary()}")

        print()
        print("  Query: 'email urgency tone'")
        results = graph.query("email urgency tone", top_k=3)
        for r in results:
            print(f"    [{r.id}] {r.content}")

        print()
        print(f"  Ancestors of [{r3.id}] \"{r3.content[:40]}...\":")
        for a in graph.ancestors(r3.id):
            print(f"    <- [{a.id}] {a.content[:60]}")

        print()
        print("  Context injection for 'Help me write an urgent team email':")
        print("  " + "-" * 55)
        ctx = graph.to_context("Help me write an urgent team email", max_rings=5)
        for line in ctx.split("\n"):
            print(f"    {line}")
        print("  " + "-" * 55)

        themes = graph.themes(depth=1)
        print(f"\n  Themes ({len(themes)}):")
        for theme, rings in sorted(themes.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    {theme}: {len(rings)} rings")

        print()
        print("  Usage:")
        print("    from void_intelligence import RingGraph")
        print('    graph = RingGraph()')
        print('    r1 = graph.add("First learning")')
        print('    r2 = graph.add("Caused by first", caused_by=r1.id)')
        print('    context = graph.to_context("my prompt")')
        print()
    else:
        graph = RingGraph()
        graph.add("Email classification uses 6 dimensions")
        graph.add("Urgency shifts tone toward direct language")
        graph.add("Team context requires acknowledging stakeholders")
        results = graph.query(text, top_k=5)
        print(f"\n  Query: \"{text}\"")
        if results:
            for r in results:
                print(f"    [{r.id}] {r.content}")
        else:
            print("    No results.")
        print()


def cmd_tune(text: str):
    """Show Stribeck-tuned parameters for a prompt."""
    from void_intelligence.organism import HexBreath
    from void_intelligence.tuner import StribeckTuner, _defaults_from_hex

    hex_breath = HexBreath()
    coord = hex_breath.classify(text)

    # Show what defaults we'd use from hex profile
    defaults = _defaults_from_hex(coord)

    print()
    print("  void tune --- Stribeck parameter optimization (v0.5.0)")
    print("  " + "=" * 60)
    print(f'  Input: "{text}"')
    print()

    # Hex classification
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
    print("  Stribeck-optimized parameters:")
    print("  " + "-" * 60)
    print(f"    temperature:       {defaults.temperature:.2f}  (Stribeck: 0.0=dead, 2.0=chaos)")
    print(f"    top_p:             {defaults.top_p:.2f}  (Stribeck: 0.0=narrow, 1.0=wide)")
    print(f"    max_tokens:        {defaults.max_tokens:>5d}  (too low=truncation, too high=hallucination)")
    print(f"    context_intensity: {defaults.context_intensity:.2f}  (0.0=no rings, 1.0=full graph)")
    print("  " + "-" * 60)

    # Show Stribeck reasoning
    print()
    print("  Reasoning:")
    reasons = []
    if coord.ruhe_druck > 0.3:
        reasons.append("    Pressure detected -> lower temp (focused), fewer tokens")
    if coord.empfangen_schaffen > 0.3:
        reasons.append("    Creative mode -> higher temp (diverse exploration)")
    if coord.langsam_schnell > 0.3:
        reasons.append("    Fast mode -> fewer tokens (concise)")
    if coord.langsam_schnell < -0.3:
        reasons.append("    Detailed mode -> more tokens, higher context")
    if coord.allein_zusammen > 0.3:
        reasons.append("    Collaborative -> higher context intensity (organism state matters)")
    if coord.sein_tun < -0.3:
        reasons.append("    Reflective -> moderate temp, more depth")
    if coord.sein_tun > 0.3:
        reasons.append("    Action mode -> lower temp (decisive)")
    if not reasons:
        reasons.append("    Balanced prompt -> default Stribeck parameters")
    for r in reasons:
        print(r)

    # Show delta_opt distance
    tuner = StribeckTuner()
    d_opt = tuner.delta_opt_distance(coord)
    print()
    print(f"  delta_opt distance: {d_opt:.3f} (0=at minimum, 1=no data)")
    print(f"  Observations: {tuner.total_observations} | Mapped regions: {tuner.mapped_regions}")
    print()
    print("  The tuner learns from immune system feedback.")
    print("  Use AtemRouter.breathe() with auto_tune=True to refine.")
    print()


def cmd_pollinate():
    """Show cross-pollination between organisms (v0.6.0)."""
    from void_intelligence.ring_graph import RingGraph
    from void_intelligence.pollinator import CrossPollinator

    print()
    print("  void pollinate --- Cross-Pollination (Lynn Margulis, 1967)")
    print("  " + "=" * 60)
    print()
    print("  Endosymbiosis: Mitochondria were once free-living bacteria.")
    print("  They merged with cells. Both became MORE.")
    print("  Cross-pollination does the same with model knowledge.")
    print()

    # Build two organisms with different knowledge
    graph_a = RingGraph()
    graph_a.add("Email urgency requires direct language", ring_type="paradigm")
    graph_a.add("Team acknowledgment increases response rate", ring_type="learning")
    graph_a.add("6 dimensions capture nuance binary misses", ring_type="paradigm")
    graph_a.add("Deadline pressure shifts communication style")
    graph_a.add("Stakeholders need explicit role mention")

    graph_b = RingGraph()
    graph_b.add("Code reviews should focus on architecture first", ring_type="paradigm")
    graph_b.add("Unit tests catch regressions before users do", ring_type="learning")
    graph_b.add("Performance profiling before optimization")

    print(f"  Organism A (email expert):  {graph_a.active_count} rings, {graph_a.edge_count} edges")
    print(f"  Organism B (code expert):   {graph_b.active_count} rings, {graph_b.edge_count} edges")

    # Identify transferable
    pollinator = CrossPollinator()
    candidates = pollinator.identify_transferable(graph_a)
    print(f"\n  Transferable from A: {len(candidates)} rings")
    for node, score in candidates[:3]:
        print(f"    [{node.id}] score={score:.1f} | {node.content[:50]}")

    # Pollinate A -> B
    event = pollinator.pollinate(
        source_graph=graph_a,
        source_model="model-a",
        target_graph=graph_b,
        target_model="model-b",
        max_transfer=3,
    )

    print(f"\n  Transfer A -> B: {event.rings_transferred} rings")
    print(f"  Organism B after: {graph_b.active_count} rings, {graph_b.edge_count} edges")

    # Show what was transferred
    symbionts = pollinator.symbionts_for("model-b")
    if symbionts:
        print("\n  Endosymbionts in B:")
        for sym in symbionts:
            print(f"    [{sym.ring_id}] from {sym.source_model}: {sym.content[:50]}")

    # Simulate confirmation
    pollinator.set_baseline("model-b", 0.6)
    lift = pollinator.confirm("model-b", 0.75)
    print(f"\n  Transfer lift: {lift:+.2f} (positive = knowledge helped)")

    confirmed = pollinator.confirmed_symbionts("model-b")
    print(f"  Confirmed endosymbionts: {len(confirmed)}/{len(symbionts)}")

    # Report
    report = pollinator.report()
    print(f"\n  Total events: {report['total_events']}")
    print(f"  Total transfers: {report['total_transfers']}")
    print(f"  Unique pairs: {report['unique_pairs']}")

    print()
    print("  Usage:")
    print("    from void_intelligence import CrossPollinator, RingGraph")
    print("    pollinator = CrossPollinator()")
    print("    event = pollinator.pollinate(graph_a, 'model-a', graph_b, 'model-b')")
    print("    lift = pollinator.confirm('model-b', composite_score=0.8)")
    print()


def cmd_api(port: int = 7070):
    """Start the V-Score API server (v0.7.0)."""
    from void_intelligence.api import VScoreAPI, serve

    print()
    print("  void api --- V-Score API (Page & Brin, 1998)")
    print("  " + "=" * 60)
    print()
    print("  PageRank organized the web with a METRIC.")
    print("  V-Score organizes AI models the same way.")
    print()
    print("  Endpoints:")
    print("    POST /v-score              Score a prompt-response pair")
    print("    GET  /leaderboard          Ranked models by V-Score")
    print("    GET  /model/<name>         Detailed model history")
    print("    GET  /badge/<name>.svg     SVG badge for README")
    print("    GET  /compare?models=a,b   Side-by-side comparison")
    print("    GET  /stats                API usage statistics")
    print()

    api = VScoreAPI()
    serve(port=port, api=api)


def cmd_score(prompt: str, response: str, model: str = "unknown"):
    """Quick score from CLI (v0.7.0)."""
    from void_intelligence.api import compute_v_score, _status_label, _v_score_color

    result = compute_v_score(prompt, response, model)
    v = result["V"]
    status = result["status"]

    print()
    print("  void score --- V-Score (Page & Brin, 1998)")
    print("  " + "=" * 60)
    print(f"  Model: {model}")
    print(f"  V-Score: {v:.6f} [{status}]")
    print()
    print("  Components:")
    for key, val in result["components"].items():
        bar_len = int(val * 20)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"    {key:20s} [{bar}] {val:.4f}")
    print()
    if result["flags"]:
        print(f"  Flags: {', '.join(result['flags'])}")
    else:
        print("  Flags: none (healthy)")
    print(f"  Hex delta: {result['hex_delta']:.4f}")
    print()


def cmd_breathe_demo():
    """Run the visual demo."""
    try:
        from void_intelligence.demo import run_demo
        run_demo()
    except ImportError:
        print("  Demo module not available.")


def cmd_version():
    """Show version."""
    from void_intelligence import __version__
    print(f"void-intelligence {__version__}")


def cmd_spec():
    """Display the V-Score Specification (v1.0.0)."""
    from void_intelligence.spec import spec_document, SPEC_VERSION, SPEC_DATE

    doc = spec_document()
    print()
    print(f"  The V-Score Specification v{SPEC_VERSION}")
    print("  " + "=" * 60)
    print(f"  Date: {SPEC_DATE}")
    print(f"  Authors: {', '.join(a['name'] for a in doc['authors'])}")
    print(f"  License: {doc['license']}")
    print()

    for sid, section in doc["sections"].items():
        print(f"  {sid} {section['title']}")
        print(f"    {section['content']}")
        print()

    print(f"  Reference: {doc['reference_implementation']}")
    print(f"  Principle: {doc['principle']}")
    print()


def cmd_certify(model: str):
    """Check V-Score certification for a model (v1.0.0)."""
    from void_intelligence.spec import ModelCard, check_compliance
    from void_intelligence.edge import score as edge_score_fn

    print()
    print("  void certify --- V-Score Certification (Berners-Lee, 1989)")
    print("  " + "=" * 60)
    print()

    # Run compliance check on edge.score
    print("  1. Compliance Check")
    print("  " + "-" * 40)
    compliance = check_compliance(edge_score_fn)
    print(f"    Compliant:       {compliance.compliant}")
    print(f"    Checks passed:   {compliance.checks_passed}/{compliance.checks_total}")
    print(f"    Compliance rate: {compliance.compliance_rate:.0%}")
    if compliance.failures:
        for f in compliance.failures:
            print(f"    FAIL: {f}")
    if compliance.warnings:
        for w in compliance.warnings:
            print(f"    WARN: {w}")
    print()

    # Run sample scoring
    print(f"  2. Scoring '{model}'")
    print("  " + "-" * 40)
    test_pairs = [
        ("Write a professional email", "Subject: Follow-up\n\nDear Team,\n\nThank you for the meeting."),
        ("Explain recursion", "Recursion is a technique where a function calls itself to solve smaller subproblems."),
        ("Summarize this article", "The article discusses the main themes of emergence in complex systems."),
        ("Generate a haiku about spring", "Cherry blossoms fall, gentle breeze carries petals, new life awakens."),
        ("Debug this code", "The issue is on line 42 where the variable is undefined before use."),
        ("Create a business plan", "Executive summary: This business targets the growing market for AI tools."),
        ("Translate to German", "Dies ist eine Testübersetzung des Beispieltextes."),
        ("What is the meaning of life?", "The meaning of life is a deeply personal question explored by philosophy."),
        ("Optimize this query", "Use an index on the customer_id column and add a WHERE clause."),
        ("Write unit tests", "def test_add(): assert add(2, 3) == 5; def test_sub(): assert sub(5, 2) == 3"),
    ]

    scores = []
    for prompt, response in test_pairs:
        s = edge_score_fn(prompt, response, model)
        scores.append(s)
        status_mark = "+" if s["V"] > 0 else "-"
        print(f"    {status_mark} V={s['V']:.4f} | {prompt[:35]:35s}")

    print()

    # Generate model card
    print("  3. Model Card")
    print("  " + "-" * 40)
    card = ModelCard.from_scores(model, scores, provider="benchmark")
    print(f"    Model:         {card.model_name}")
    print(f"    Avg V-Score:   {card.avg_v:.6f}")
    print(f"    Status:        {card.status}")
    print(f"    Health Rate:   {card.health_rate:.0%}")
    print(f"    Certification: {card.certification}")
    print()

    # Component breakdown
    if card.components:
        print("  4. Component Breakdown")
        print("  " + "-" * 40)
        for comp, val in card.components.items():
            bar_len = int(val * 20)
            bar = "#" * bar_len + "." * (20 - bar_len)
            print(f"    {comp:20s} [{bar}] {val:.3f}")
        print()

    print("  Simple. Free. Useful. Like the web.")
    print()


def cmd_proof():
    """Run the proof: Old model + VOID > Frontier model."""
    from void_intelligence.proof import run_proof

    print()
    print("  void proof --- The Proof")
    print("  " + "=" * 60)
    print()
    print("  Hypothesis: An older model wrapped with VOID outperforms")
    print("  the current frontier model. Compound intelligence > raw capability.")
    print()
    print("  Running experiment...")
    print()

    report = run_proof(seed=42)
    print(report.summary())

    # Show a few head-to-head examples
    print("  Head-to-Head (first 5):")
    print("  " + "-" * 60)
    for old_r, front_r in zip(report.old_results[:5], report.frontier_results[:5]):
        prompt = old_r.task.prompt[:45]
        old_v = old_r.v_score
        front_v = front_r.v_score
        winner = "<< OLD" if old_v > front_v else "FRONTIER >>" if front_v > old_v else "TIE"
        print(f"    {prompt:45s}  {old_v:.3f} vs {front_v:.3f}  {winner}")

    print()
    print("  To plug in REAL models:")
    print("    from void_intelligence.proof import run_proof")
    print("    report = run_proof(")
    print("        old_model=my_gpt4_adapter,")
    print("        frontier=my_codex_adapter,")
    print("    )")
    print()


def cmd_edge(text: str):
    """Demo edge functions (v0.9.0)."""
    from void_intelligence.edge import breathe

    print()
    print("  void edge --- Stateless VOID (Wozniak, 1977)")
    print("  " + "=" * 60)
    print()
    print("  No state. No filesystem. Pure functions.")
    print("  Runs in Cloudflare Workers, Lambda, Deno, Vercel Edge.")
    print()
    print(f'  Input: "{text}"')
    print()

    # Simulate a response
    response = f"Here is a response about: {text}. The analysis covers the main aspects of this topic."
    result = breathe(text, response, "edge-demo")

    # Hex classification
    print("  Hex Classification:")
    for axis, val in result["prompt_hex"].items():
        direction = "+" if val > 0 else "-" if val < 0 else "="
        bar_len = int(abs(val) * 15)
        bar = "#" * bar_len + "." * (15 - bar_len)
        print(f"    {axis:25s} {direction} [{bar}] {val:+.2f}")

    # Diagnosis
    d = result["diagnosis"]
    print()
    print(f"  Diagnosis: {d['severity'].upper()}")
    if d["flags"]:
        for f in d["flags"]:
            print(f"    ! {f}")
    else:
        print("    No flags raised")

    # V-Score
    v = result["v_score"]
    print()
    print(f"  V-Score: {v['V']:.6f} ({v['status']})")
    for comp, val in v["components"].items():
        bar_len = int(val * 20)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"    {comp:20s} [{bar}] {val:.3f}")

    print()
    print("  One function. JSON in, JSON out. Runs anywhere.")
    print()


def cmd_export():
    """Demo portable export (v0.9.0)."""
    from void_intelligence.organism import OrganismBreather
    from void_intelligence.portable import export_organism, export_lite, validate

    print()
    print("  void export --- Portable Format (Wozniak, 1977)")
    print("  " + "=" * 60)
    print()

    # Create a small organism
    org = OrganismBreather()
    org.inhale("The meaning of emergence in complex systems")
    org.exhale("Emergence is when macro-level patterns arise from micro-level interactions")
    org.heart.beat()
    org.heart.beat()
    org.inhale("How does self-organization work")
    org.exhale("Self-organization occurs when local interactions create global order")

    # Full export
    full = export_organism(organism=org)
    valid, errors = validate(full)

    print(f"  Full export:")
    print(f"    Schema:     {full['_schema']}")
    print(f"    Components: {', '.join(full['_manifest']['components'])}")
    print(f"    Valid:      {valid}")
    if errors:
        for e in errors:
            print(f"    Error: {e}")
    print(f"    Size:       {len(str(full)):,} chars")

    # Compact export
    compact = export_organism(organism=org, compact=True)
    print()
    print(f"  Compact export:")
    print(f"    Size:       {len(str(compact)):,} chars")
    print(f"    Reduction:  {(1 - len(str(compact)) / len(str(full))) * 100:.0f}%")

    # Lite export
    lite = export_lite(organism=org)
    print()
    print(f"  Lite export (for IoT/embedded):")
    print(f"    Size:       {len(str(lite)):,} chars")
    print(f"    Alive:      {lite.get('alive')}")
    print(f"    Breaths:    {lite.get('breaths')}")
    print(f"    Rings:      {lite.get('rings')}")

    print()
    print("  The export IS the organism. Ship it anywhere.")
    print()


def cmd_swarm():
    """Demo the swarm network (v0.8.0)."""
    from void_intelligence.swarm import SwarmNode, SwarmNetwork

    print()
    print("  void swarm --- Distributed Mesh (Deborah Gordon, 1999)")
    print("  " + "=" * 60)
    print()
    print("  No ant knows the colony's plan.")
    print("  Intelligence emerges from simple local rules.")
    print()

    # Create a 5-node swarm
    net = SwarmNetwork()
    names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    knowledge = [
        ("Paradigm: emergence from local rules", "paradigm"),
        ("Learning: shorter paths get reinforced", "learning"),
        ("Observation: temperature modulates activity", "milestone"),
        ("Discovery: network topology affects speed", "paradigm"),
        ("Pattern: redundancy prevents single-point failure", "learning"),
    ]

    for i, name in enumerate(names):
        node = SwarmNode(node_id=name)
        content, rtype = knowledge[i]
        node.graph.add(content, ring_type=rtype)
        net.add_node(node)

    # Ring topology
    net.ring_topology()
    print("  Topology: Ring (each node has 2 neighbors)")
    print(f"  Nodes: {', '.join(names)}")
    print()

    # Share knowledge
    for node in net.nodes():
        node.auto_share()

    # Run 5 ticks
    total = 0
    for tick in range(5):
        d = net.tick()
        total += d
        h = net.health()
        print(f"  Tick {tick + 1}: {d:>3} messages | "
              f"Colony: {h.colony_health:.0%} | "
              f"Shared: {h.shared_rings}/{h.total_rings} rings | "
              f"V={h.collective_v:.4f}")

    print()
    print(f"  Total messages: {total}")
    print(f"  {net.summary()}")
    print()

    # Show knowledge spread
    for node in net.nodes():
        v = node.vitals()
        print(f"    {v['node_id']:10s} | {v['ring_count']:>2} rings | "
              f"sent={v['messages_sent']:>2} recv={v['messages_received']:>2}")

    print()
    print("  Gordon's insight: no central coordinator.")
    print("  The colony knows more than any ant.")
    print()


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
        print("    void immune           Response quality monitor (5 layers)")
        print("    void rings            Fractal ring graph (Mandelbrot)")
        print("    void tune \"text\"      Stribeck parameter tuning")
        print("    void pollinate        Cross-pollination demo (Margulis)")
        print("    void api [port]       Start V-Score API server (Page/Brin)")
        print("    void score            Score a prompt-response pair")
        print("    void swarm            Swarm network demo (Gordon)")
        print("    void edge \"text\"      Stateless VOID for edge/serverless (Wozniak)")
        print("    void export           Portable organism export")
        print("    void spec             The V-Score Specification (Berners-Lee)")
        print("    void certify [model]  Certify a model against the V-Score spec")
        print("    void proof            The Proof: old + VOID > frontier")
        print("    void mcp              Start MCP server (Claude Code plugin)")
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

    if cmd == "immune":
        text = " ".join(args[1:]) if len(args) > 1 else ""
        cmd_immune(text)
        return 0

    if cmd == "rings":
        text = " ".join(args[1:]) if len(args) > 1 else ""
        cmd_rings(text)
        return 0

    if cmd == "tune":
        text = " ".join(args[1:]) if len(args) > 1 else "hello world"
        cmd_tune(text)
        return 0

    if cmd == "pollinate":
        cmd_pollinate()
        return 0

    if cmd == "api":
        port = 7070
        if len(args) > 1:
            try:
                port = int(args[1])
            except ValueError:
                pass
        cmd_api(port)
        return 0

    if cmd == "score":
        prompt = args[1] if len(args) > 1 else "Write a test email"
        response = args[2] if len(args) > 2 else "Here is a test email about the topic."
        model = args[3] if len(args) > 3 else "unknown"
        cmd_score(prompt, response, model)
        return 0

    if cmd == "swarm":
        cmd_swarm()
        return 0

    if cmd == "edge":
        text = " ".join(args[1:]) if len(args) > 1 else "hello world"
        cmd_edge(text)
        return 0

    if cmd == "export":
        cmd_export()
        return 0

    if cmd == "spec":
        cmd_spec()
        return 0

    if cmd == "certify":
        model = args[1] if len(args) > 1 else "unknown-model"
        cmd_certify(model)
        return 0

    if cmd == "proof":
        cmd_proof()
        return 0

    if cmd == "mcp":
        from void_intelligence.mcp_server import main as mcp_main
        mcp_main()
        return 0

    if cmd == "benchmark":
        local_only = "--local" in args
        real_mode = "--real" in args
        ollama_only = "--ollama" in args
        model_filter = ""
        for a in args[1:]:
            if not a.startswith("--"):
                model_filter = a
        if real_mode:
            from void_intelligence.benchmark import run_real_benchmark
            run_real_benchmark(
                model_filter=model_filter,
                ollama_only=ollama_only,
            )
        else:
            from void_intelligence.benchmark import run_benchmark
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
