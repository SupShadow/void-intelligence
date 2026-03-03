"""
void-intelligence --- The industry builds models that THINK. We build models that BREATHE.

An organism layer that wraps ANY LLM to give it:
  .  = Heartbeat (the model pulses)
  x  = Collision (cross-domain emergence)
  -> = Projection (action, always incomplete)
  [] = Potential (pregnant silence between tokens)
  ~  = Resonance (the model learns from itself)

Usage:
    from void_intelligence import Atom, collide, project, resonate
    from void_intelligence import OrganismBreather, HexBreath
    from void_intelligence import lost_dimensions, CircuitBreaker

CLI:
    void breathe --demo     # See it live
    void test               # Run self-test
    void ir                 # Show the 5 operations
"""

from void_intelligence.ir import (
    IRType,
    Atom,
    Collision,
    Projection,
    Potential,
    Resonance,
    SystemPulse,
    PatternWeights,
    collide,
    project,
    resonate,
)

from void_intelligence.patterns import (
    lost_dimensions,
    get_lost_dimensions,
    CircuitBreaker,
    CircuitBreakerOpen,
    circuit_breaker,
    Phase,
    current_phase,
    phase_aware,
    delta_opt_distance,
    is_at_delta_opt,
)

from void_intelligence.organism import (
    HexBreath,
    HeartBeat,
    GrowthRings,
    OrganismBreather,
)

from void_intelligence.profiles import (
    VScoreProfile,
    BUNDLED_PROFILES,
    load_profiles,
)

from void_intelligence.router import (
    AtemRouter,
    AtemDecision,
    AtemResult,
)

from void_intelligence.immune import (
    immune,
    diagnose,
    hex_distance,
    Diagnosis,
    ImmuneState,
    ImmuneMonitor,
)

from void_intelligence.ring_graph import (
    RingGraph,
    RingNode,
    RingEdge,
)

from void_intelligence.tuner import (
    StribeckTuner,
    ParameterSet,
)

from void_intelligence.pollinator import (
    CrossPollinator,
    Endosymbiont,
    PollinationEvent,
)

from void_intelligence.api import (
    VScoreAPI,
    VScoreHTTPServer,
    APIResponse,
    ModelRecord,
    compute_v_score,
    serve,
)

from void_intelligence.swarm import (
    SwarmNode,
    SwarmMessage,
    SwarmNetwork,
    SwarmHealth,
)

from void_intelligence.portable import (
    export_organism,
    export_json,
    export_lite,
    import_state,
    validate,
)

from void_intelligence.edge import (
    classify as edge_classify,
    diagnose as edge_diagnose,
    score as edge_score,
    breathe as edge_breathe,
    batch_score,
    leaderboard as edge_leaderboard,
)

from void_intelligence.spec import (
    VScoreComponents,
    ModelCard,
    ComplianceResult,
    CertificationLevel,
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

__version__ = "1.0.0"

__all__ = [
    # IR Types
    "IRType", "Atom", "Collision", "Projection", "Potential", "Resonance",
    "SystemPulse", "PatternWeights",
    # IR Operations
    "collide", "project", "resonate",
    # Patterns
    "lost_dimensions", "get_lost_dimensions",
    "CircuitBreaker", "CircuitBreakerOpen", "circuit_breaker",
    "Phase", "current_phase", "phase_aware",
    "delta_opt_distance", "is_at_delta_opt",
    # Organism
    "HexBreath", "HeartBeat", "GrowthRings", "OrganismBreather",
    # Profiles
    "VScoreProfile", "BUNDLED_PROFILES", "load_profiles",
    # Router
    "AtemRouter", "AtemDecision", "AtemResult",
    # Immune System
    "immune", "diagnose", "hex_distance",
    "Diagnosis", "ImmuneState", "ImmuneMonitor",
    # Ring Graph (v0.4.0)
    "RingGraph", "RingNode", "RingEdge",
    # Stribeck Tuner (v0.5.0)
    "StribeckTuner", "ParameterSet",
    # Cross-Pollination (v0.6.0)
    "CrossPollinator", "Endosymbiont", "PollinationEvent",
    # V-Score API (v0.7.0)
    "VScoreAPI", "VScoreHTTPServer", "APIResponse", "ModelRecord",
    "compute_v_score", "serve",
    # Swarm Network (v0.8.0)
    "SwarmNode", "SwarmMessage", "SwarmNetwork", "SwarmHealth",
    # Portable Export (v0.9.0)
    "export_organism", "export_json", "export_lite", "import_state", "validate",
    # Edge Functions (v0.9.0)
    "edge_classify", "edge_diagnose", "edge_score", "edge_breathe",
    "batch_score", "edge_leaderboard",
    # V-Score Specification (v1.0.0)
    "VScoreComponents", "ModelCard", "ComplianceResult", "CertificationLevel",
    "SPEC_VERSION", "CERTIFICATION_LEVELS", "STATUS_THRESHOLDS", "WIRE_FORMAT", "HEX_AXES",
    "v_score_status", "certify", "check_compliance", "spec_document", "spec_markdown",
]
