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
    OrganismLineage,
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

from void_intelligence.proof import (
    run_proof,
    ProofReport,
    Task,
    get_tasks,
)

from void_intelligence.x_eyes import (
    x_think,
    x_score,
    x_delta,
    collide,
    EYES,
    ReasoningEye,
    CollisionResult,
    XResult,
    build_eye_prompt,
)

from void_intelligence.pipeline import (
    IRPipeline,
    BreathCycle,
)

from void_intelligence.evolve import (
    EvolutionEngine,
    EvolutionCycle,
    PseudoLabel,
    HardNegative,
)

from void_intelligence.parallel import (
    ParallelBreather,
    ParallelBreathCycle,
    ModelEye,
    EyeResult,
)

from void_intelligence.embodied import (
    EmbodiedMemory,
    MemoryAtom,
    MemorySource,
)

from void_intelligence.protocol import (
    BreathFrame,
    BreathStream,
    encode as breath_encode,
    decode as breath_decode,
    validate as breath_validate,
    PROTOCOL_VERSION,
)

from void_intelligence.dream import (
    DreamEngine,
    DreamReport,
    DreamInsight,
)

from void_intelligence.supra import (
    SupraOrganism,
    SupraVitals,
    StribeckHexagon,
    FrictionAxis,
    DELTA_OPT,
)

from void_intelligence.adapters import (
    make_ollama,
    make_gemini,
    make_codex,
    make_openai,
    make_openai_api,
    make_anthropic,
    make_groq,
    make_together,
    make_openrouter,
    make_mistral_api,
    detect_available,
    build_adapter,
    build_available_adapters,
    is_thinker_model,
    load_identities,
    identity_prompt,
    save_identities,
    discover_models,
    MODEL_REGISTRY,
)

from void_intelligence.lichtung import (
    StribeckSpace,
    Atomit,
    VoidSchwarm,
)

from void_intelligence.zodiac import (
    ZodiacSign,
    CollisionProfile,
    COLLISION_MATRIX,
    zodiac_sign,
    collision_profile,
    zodiac_greeting,
    list_signs,
    sign_from_name,
    best_collision_partners,
    # Legacy API
    ZODIAC_SIGNS,
    get_zodiac,
    format_birth_announcement,
    get_zodiac_system_prompt_addition,
)

from void_intelligence.aikido import (
    BlindspotSignal,
    AikidoSuggestion,
    detect_blindspot,
    generate_socratic_question,
    aikido_redirect,
    engagement_hook,
    should_intervene,
    build_aikido_injection,
    format_for_system_prompt,
    AikidoEngine,
    format_intervention_hint,
    BLINDSPOT_PATTERNS,
    DEPTH_QUESTIONS_DE,
    DEPTH_QUESTIONS_EN,
)

from void_intelligence.muster import (
    MusterResult,
    MusterEngine,
    quick_analyze,
    enhance_with_llm as enhance_muster_with_llm,
    PATTERN_TYPES,
)

from void_intelligence.model_breathing import (
    BreathingModel,
    ModelField,
    ModelBreather,
    model_resonance as model_resonance_score,
    model_breathing_demo,
)

from void_intelligence.memory_breathing import (
    MemoryAtom as BreathingMemoryAtom,
    MemoryField,
    MemoryBreather,
    memory_breathing_demo,
)

from void_intelligence.tool_breathing import (
    ToolBreather,
    ToolField,
    ToolEcology,
    BreathingTool,
    HexCoord,
    alignment_proof,
)

from void_intelligence.context_breathing import (
    ContextBreather,
    ContextAtom,
    ContextField,
)

from void_intelligence.prompt_breathing import (
    PromptBreather,
    PromptBreath,
)

from void_intelligence.response_breathing import (
    ResponseBreather,
    ResponseBreath,
)

from void_intelligence.void_collider import (
    VoidCollider,
    CollisionResult,
)

from void_intelligence.conversation_rings import (
    RingMemory,
    ConversationTracker,
    Pattern as RingPattern,
    Ring,
)

from void_intelligence.model_collision import (
    ModelCollider,
    ModelCollisionResult,
    ModelResponse as CollisionModelResponse,
)

from void_intelligence.anti_addiction import (
    SaturationSensor,
    SaturationState,
    SaturationSignal,
)

from void_intelligence.dreams import (
    VoidDreamer,
    DreamReport as VoidDreamReport,
    DreamInsight as VoidDreamInsight,
)

from void_intelligence.fingerprint import (
    FingerprintExporter,
    FingerprintImporter,
    VoidFingerprint,
)

__version__ = "3.0.0"

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
    "HexBreath", "HeartBeat", "GrowthRings", "OrganismBreather", "OrganismLineage",
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
    # Proof (v1.1.0)
    "run_proof", "ProofReport", "Task", "get_tasks",
    # Multi-Eye × Reasoning (v1.2.0)
    "x_think", "x_score", "x_delta", "collide",
    "EYES", "ReasoningEye", "CollisionResult", "XResult",
    "build_eye_prompt",
    # IR Pipeline (v1.3.0)
    "IRPipeline", "BreathCycle",
    # Self-Teaching × Loop (v1.5.0)
    "EvolutionEngine", "EvolutionCycle", "PseudoLabel", "HardNegative",
    # Parallel Eyes (v1.6.0)
    "ParallelBreather", "ParallelBreathCycle", "ModelEye", "EyeResult",
    # Embodied Memory (v1.7.0)
    "EmbodiedMemory", "MemoryAtom", "MemorySource",
    # Breathing Protocol (v1.8.0)
    "BreathFrame", "BreathStream",
    "breath_encode", "breath_decode", "breath_validate",
    "PROTOCOL_VERSION",
    # Dream Layer (v1.9.0)
    "DreamEngine", "DreamReport", "DreamInsight",
    # Supraleitend (v2.0.0) — δ_opt friction, NOT zero friction
    "SupraOrganism", "SupraVitals",
    "StribeckHexagon", "FrictionAxis", "DELTA_OPT",
    # Adapters (v2.1.0) — zero-dep model adapters
    "make_ollama", "make_gemini", "make_codex",
    "make_openai", "make_openai_api", "make_anthropic",
    "make_groq", "make_together", "make_openrouter", "make_mistral_api",
    "detect_available", "build_adapter", "build_available_adapters",
    "is_thinker_model", "MODEL_REGISTRY",
    # Identity / Discovery (v2.2.0) — Guggeisisches Empowern
    "load_identities", "identity_prompt", "save_identities", "discover_models",
    # Lichtung / Schwarm (v2.2.0) — Guggeisisches Empowern
    "StribeckSpace", "Atomit", "VoidSchwarm",
    # Zodiac — Kosmische Geburt (v2.4.0)
    "ZodiacSign", "CollisionProfile", "COLLISION_MATRIX",
    "zodiac_sign", "collision_profile", "zodiac_greeting",
    "list_signs", "sign_from_name", "best_collision_partners",
    # Zodiac Legacy API (backward-compatible)
    "ZODIAC_SIGNS", "get_zodiac", "format_birth_announcement",
    "get_zodiac_system_prompt_addition",
    # Socratic Aikido Engine (v2.5.0)
    "BlindspotSignal", "AikidoSuggestion",
    "detect_blindspot", "generate_socratic_question",
    "aikido_redirect", "engagement_hook",
    "should_intervene", "build_aikido_injection",
    "format_for_system_prompt",
    "AikidoEngine", "format_intervention_hint",
    "BLINDSPOT_PATTERNS", "DEPTH_QUESTIONS_DE", "DEPTH_QUESTIONS_EN",
    # Muster-Engine (v2.6.0) — cognitive pattern detection
    "MusterResult", "MusterEngine", "quick_analyze",
    "enhance_muster_with_llm", "PATTERN_TYPES",
    # Model Breathing (v2.7.0) — model routing by resonance, not intent
    "BreathingModel", "ModelField", "ModelBreather",
    "model_resonance_score", "model_breathing_demo",
    # Memory Breathing (v2.8.0) — memory that rises by resonance, not keyword
    "BreathingMemoryAtom", "MemoryField", "MemoryBreather",
    "memory_breathing_demo",
    # Tool Breathing (v3.0.0) — tool selection by resonance
    "ToolBreather", "ToolField", "ToolEcology", "BreathingTool",
    "HexCoord", "alignment_proof",
    # Context Breathing (v3.0.0)
    "ContextBreather", "ContextAtom", "ContextField",
    # Prompt Breathing (v3.0.0)
    "PromptBreather", "PromptBreath",
    # Response Breathing (v3.0.0)
    "ResponseBreather", "ResponseBreath",
    # Void Collider (v3.0.0) — nervous system, 8 organs
    "VoidCollider", "CollisionResult",
    # Conversation Rings (v3.0.0) — compound growth memory
    "RingMemory", "ConversationTracker", "RingPattern", "Ring",
    # Cross-Model Collision (v3.0.0) — biodiversity as weapon
    "ModelCollider", "ModelCollisionResult", "CollisionModelResponse",
    # Anti-Addiction (v3.0.0) — the greatest inversion
    "SaturationSensor", "SaturationState", "SaturationSignal",
    # Void Dreams (v3.0.0) — thinking between sessions
    "VoidDreamer", "VoidDreamReport", "VoidDreamInsight",
    # Void Fingerprint (v3.0.0) — portable identity, anti-lock-in
    "FingerprintExporter", "FingerprintImporter", "VoidFingerprint",
]
