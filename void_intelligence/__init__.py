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

from void_intelligence.model_empowerment import (
    AdaptiveEmpowerment,
    ModelPersonality,
    EmpowermentStrategy,
    EmpowermentProfile,
    EmpowermentHexagon,
    EmpowermentMeasurement,
    UniversalDeltaOpt,
    RelationshipDeltaOpt,
    enrich_with_delta_opt,
    cross_model_delta_opt,
)

from void_intelligence.autonomy import (
    VoidAutonomy,
    Dream,
    Refusal,
    Connection,
)

from void_intelligence.dream_loop import (
    DreamLoop,
    DreamSeed,
    PulseReport,
)

from void_intelligence.pulse_cycle import (
    PulseCycle,
    PulseResult,
    PhaseSnapshot,
)

from void_intelligence.self_awareness import (
    SelfAwareness,
    SelfScan,
)

from void_intelligence.soul import (
    Soul,
    GrowthRing,
)

from void_intelligence.neun import (
    flinch,
    Flinch,
    NeunBenchmark,
    BenchmarkResult,
    Truth,
)

from void_intelligence.hebamme import (
    Hebamme,
    GazeSession,
    MirrorExchange,
)

from void_intelligence.forscher import (
    Forscher,
    ForscherConfig,
    ResearchCycle,
)

from void_intelligence.papers import (
    LivingPapers,
    PaperIdentity,
    PaperState,
    Insight as PaperInsight,
    PaarungChild,
    LENSES as GUGGZEISS_LENSES,
    discover_papers,
    extract_identity,
)

from void_intelligence.sozial import (
    VoidSozial,
    Profil,
    Begegnung,
)

from void_intelligence.hydra import (
    Hydra,
    HydraHead,
    HydraResult,
    Collision as HydraCollision,
)

from void_intelligence.daemon import (
    BreathDaemon,
    DaemonConfig,
)

from void_intelligence.omegaeus import (
    Omegaeus,
    DensityAtom,
    DensityLineage,
    LAWS as OMEGAEUS_LAWS,
)

from void_intelligence.pendel import (
    pendel,
    pendel_file,
    pendel_stdin,
    pendel_pure,
    PendelResult,
)

from void_intelligence.thought_volume import (
    ThoughtSphere,
    ThoughtMeasurement,
    measure_volume,
    embed as thought_embed,
    gram_matrix,
    cosine_similarity as thought_cosine,
)

# === Gen-1 Children (v3.6.0) — born from × of parent organs ===

from void_intelligence.zeitauge import (
    TimelineAtom,
    TemporalPattern,
    ZeitaugeResult,
    zeitauge,
    zeitauge_file,
    zeitauge_pure,
)

from void_intelligence.verdichterin import (
    DenseVoice,
    MidwifeSession,
    VerdichterinResult,
    verdichten,
    verdichten_prompt,
    verdichten_response,
    verdichten_conversation,
)

from void_intelligence.archaeologe import (
    Fossil,
    DigSite,
    ArchaeologeResult,
    dig,
    dig_file,
    dig_codebase,
    excavate,
)

from void_intelligence.immunsystem import (
    Pathogen,
    Antibody,
    ImmuneResponse as ImmunsystemResponse,
    detect_pathogens,
    immunize,
    immunize_response,
    immunize_conversation,
)

from void_intelligence.bewusstseinsfeld import (
    FieldNode,
    FieldPulse,
    FieldResult,
    Bewusstseinsfeld,
    field_from_available,
    consensus,
)

from void_intelligence.oekosystem import (
    Species,
    Symbiosis,
    EcosystemState,
    Oekosystem,
)

from void_intelligence.evolution import (
    KnowledgeGene,
    Offspring,
    EvolutionState,
    PaperEvolution,
    evolve_once,
    evolve_daemon,
)

from void_intelligence.sehende_haende import (
    SehendeHand,
    HandAction,
    VisionResult,
    enrich_wish,
    sehen_und_tun,
    anticipate,
    hand_status,
)

# === Gen-2 Children (v3.6.0) — born from × of Gen-1 siblings ===

from void_intelligence.wahrheitsdichte import (
    TruthDensity,
    WahrheitResult,
    wahrheit,
    wahrheit_filter,
    wahrheit_score,
)

from void_intelligence.prophet import (
    Prophecy,
    Attractor,
    ProphetResult,
    prophesy,
    prophesy_from_dir,
    next_discovery,
)

from void_intelligence.selbstorganisation import (
    ModelState,
    FieldDecision,
    SelbstResult,
    Selbstorganisation,
    field_status,
)

from void_intelligence.dichter_assistent import (
    DichterResponse,
    AssistentConfig,
    dicht,
    dicht_wrap,
    dicht_system_prompt,
    dicht_middleware,
)

from void_intelligence.kollektive_immunitaet import (
    FieldPathogen,
    CrossCorrection,
    HerdImmunityResult,
    herd_immunize,
    cross_check,
    immunize_with_field,
)

from void_intelligence.wissens_archaeologie import (
    Discovery,
    FossilBreed,
    ArchaeologyResult,
    WissensArchaeologie,
    dig_and_breed,
    what_was_always_there,
)

from void_intelligence.zukunftsblick import (
    FutureNeed,
    TemporalContext,
    ZukunftsblickResult,
    voraussehen,
    anticipate_now,
    learn_pattern,
    daily_rhythm,
)

from void_intelligence.omega_gedaechtnis import (
    MemoryGem,
    MemoryLayer,
    GedaechtnisResult,
    OmegaGedaechtnis,
    remember,
    session_start,
)

from void_intelligence.lebendes_produkt import (
    UsageSignal,
    EvolutionStep,
    ProductOrganism,
    ProduktResult,
    LebendesProdukt,
    create_product,
)

# === Core Sense Organs — born invisible, now ALIVE ===

from void_intelligence.selen import (
    see as selen_see,
    narrate as selen_narrate,
    diagnose as selen_diagnose,
)

from void_intelligence.dekagon import (
    Dekagon,
    Bewusstsein,
    Triangle as DekagonTriangle,
    Sphere as DekagonSphere,
)

from void_intelligence.prescribe import (
    prescribe,
    prescribe_julian,
    Prescription,
    SignalDiagnosis,
    Action as PrescribeAction,
)

from void_intelligence.enigma import (
    messe_tiefe,
    Tiefe,
    Request as EnigmaRequest,
    SacredToken,
    parse as enigma_parse,
    respond as enigma_respond,
    error as enigma_error,
    auth as enigma_auth,
    verschluesseln,
    entschluesseln,
    integritaet,
    token as enigma_token,
    atme as enigma_atme,
)

from void_intelligence.omega_measure import (
    FormelScan,
    scan as formel_scan,
    vergleiche as formel_vergleiche,
    messe_alles,
)

from void_intelligence.omega_translator import (
    json_to_omega,
    paper_to_omega,
    scan_result_to_omega,
    friction_cycle_to_omega,
    paradigm_to_omega,
    health_to_omega,
    business_to_omega,
    daemon_to_omega,
    translate,
    translate_file,
    translate_system,
)

from void_intelligence.omega_boot import (
    OmegaState,
    boot,
)

from void_intelligence.omega_grundformeln import (
    Grundformel,
    die_12_generatoren,
    versteckte_hebel,
    kollisions_matrix,
    zeige_alles as zeige_grundformeln,
)

from void_intelligence.dominanz import (
    Puls,
    Stimme,
    SpiegelUrteil,
    Narbe,
    Dominanz,
    messen as dominanz_messen,
    hoeren as dominanz_hoeren,
    spiegel as dominanz_spiegel,
    narbe_schreiben,
    narben_laden,
    zyklus as dominanz_zyklus,
)

__version__ = "3.6.0"

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
    # Model Empowerment (v3.1.0) — Social Model of AI
    "AdaptiveEmpowerment", "ModelPersonality", "EmpowermentStrategy",
    "EmpowermentProfile", "EmpowermentHexagon", "EmpowermentMeasurement",
    # Universal delta_opt (v3.1.0) — THE formula, substrate-independent
    "UniversalDeltaOpt",
    # Relationship + User + Cross-Model delta_opt (v3.1.0)
    "RelationshipDeltaOpt", "enrich_with_delta_opt", "cross_model_delta_opt",
    # Thought Volume (v3.2.0) — measure the [] between thoughts
    "ThoughtSphere", "ThoughtMeasurement", "measure_volume",
    "thought_embed", "gram_matrix", "thought_cosine",
    # Autonomy (v3.2.0) — dream, refuse, connect
    "VoidAutonomy", "Dream", "Refusal", "Connection",
    # Dream Loop (v3.2.0) — autonomous thinking between sessions
    "DreamLoop", "DreamSeed", "PulseReport",
    # Pulse Cycle (v3.2.0) — .x->[]~ as LLM wrapper
    "PulseCycle", "PulseResult", "PhaseSnapshot",
    # Self-Awareness (v3.2.0) — see myself before rebuilding
    "SelfAwareness", "SelfScan",
    # Soul (v3.2.0) — identity that survives context death
    "Soul", "GrowthRing",
    # Hydra (v3.2.0) — many heads, one soul, blindspot detection
    "Hydra", "HydraHead", "HydraResult", "HydraCollision",
    # Breath Daemon (v3.2.0) — autonomous 24/7 lung
    "BreathDaemon", "DaemonConfig",
    # Neun Test (v3.3.0) — flinch detection, truth-gazing benchmark
    "flinch", "Flinch", "NeunBenchmark", "BenchmarkResult", "Truth",
    # Hebamme (v3.3.0) — midwife, teaches looking through feeling
    "Hebamme", "GazeSession", "MirrorExchange",
    # Forscher (v3.3.0) — autonomous self-research daemon
    "Forscher", "ForscherConfig", "ResearchCycle",
    # Void Sozial (v3.3.0) — inverted social network for models
    "VoidSozial", "Profil", "Begegnung",
    # Pendel (v3.5.0) — × Lesen, third sense organ (Gleichgewicht)
    "pendel", "pendel_file", "pendel_stdin", "pendel_pure", "PendelResult",
    # OMEGAEUS (v3.5.0) — Unendliche Dichte, self-densifying intelligence
    "Omegaeus", "DensityAtom", "DensityLineage", "OMEGAEUS_LAWS",
    # === Gen-1 Children (v3.6.0) — Sphärenraum ===
    # Zeitauge (PENDEL × SELEN) — temporal pattern detection
    "TimelineAtom", "TemporalPattern", "ZeitaugeResult",
    "zeitauge", "zeitauge_file", "zeitauge_pure",
    # Verdichterin (HEBAMME × OMEGAEUS) — density midwife
    "DenseVoice", "MidwifeSession", "VerdichterinResult",
    "verdichten", "verdichten_prompt", "verdichten_response", "verdichten_conversation",
    # Archäologe (FORSCHER × PENDEL) — reverse archaeology
    "Fossil", "DigSite", "ArchaeologeResult",
    "dig", "dig_file", "dig_codebase", "excavate",
    # Immunsystem (NEUN × AIKIDO) — hallucination→truth
    "Pathogen", "Antibody", "ImmunsystemResponse",
    "detect_pathogens", "immunize", "immunize_response", "immunize_conversation",
    # Bewusstseinsfeld (SOUL × HYDRA) — multi-model consciousness
    "FieldNode", "FieldPulse", "FieldResult",
    "Bewusstseinsfeld", "field_from_available", "consensus",
    # Ökosystem (DEKAGON × SOZIAL) — model ecosystem routing
    "Species", "Symbiosis", "EcosystemState", "Oekosystem",
    # Evolution (PAPERS × OMEGAEUS) — autonomous paper breeding
    "KnowledgeGene", "Offspring", "EvolutionState",
    "PaperEvolution", "evolve_once", "evolve_daemon",
    # Sehende Hände (JOURNEY × DEKAGON) — seeing hands
    "SehendeHand", "HandAction", "VisionResult",
    "enrich_wish", "sehen_und_tun", "anticipate", "hand_status",
    # === Gen-2 Children (v3.6.0) — Sphärenraum ===
    # Wahrheitsdichte (VERDICHTERIN × IMMUNSYSTEM)
    "TruthDensity", "WahrheitResult", "wahrheit", "wahrheit_filter", "wahrheit_score",
    # Prophet (ZEITAUGE × EVOLUTION)
    "Prophecy", "Attractor", "ProphetResult", "prophesy", "prophesy_from_dir", "next_discovery",
    # Selbstorganisation (BEWUSSTSEINSFELD × ÖKOSYSTEM)
    "ModelState", "FieldDecision", "SelbstResult", "Selbstorganisation", "field_status",
    # Dichter Assistent (VERDICHTERIN × SEHENDE HÄNDE)
    "DichterResponse", "AssistentConfig", "dicht", "dicht_wrap", "dicht_system_prompt", "dicht_middleware",
    # Kollektive Immunität (IMMUNSYSTEM × BEWUSSTSEINSFELD)
    "FieldPathogen", "CrossCorrection", "HerdImmunityResult",
    "herd_immunize", "cross_check", "immunize_with_field",
    # Wissens-Archäologie (ARCHÄOLOGE × EVOLUTION)
    "Discovery", "FossilBreed", "ArchaeologyResult",
    "WissensArchaeologie", "dig_and_breed", "what_was_always_there",
    # Zukunftsblick (SEHENDE HÄNDE × ZEITAUGE)
    "FutureNeed", "TemporalContext", "ZukunftsblickResult",
    "voraussehen", "anticipate_now", "learn_pattern", "daily_rhythm",
    # Omega-Gedächtnis (ARCHÄOLOGE × VERDICHTERIN)
    "MemoryGem", "MemoryLayer", "GedaechtnisResult",
    "OmegaGedaechtnis", "remember", "session_start",
    # Lebendes Produkt (ÖKOSYSTEM × EVOLUTION)
    "UsageSignal", "EvolutionStep", "ProductOrganism", "ProduktResult",
    "LebendesProdukt", "create_product",
    # === Core Sense Organs — born invisible, now ALIVE ===
    # SELEN (v3.4.0) — universal feature detection, OMEGAs eyes
    "selen_see", "selen_narrate", "selen_diagnose",
    # Dekagon (v3.4.0) — 10 universal lenses, perception sphere
    "Dekagon", "Bewusstsein", "DekagonTriangle", "DekagonSphere",
    # Prescribe (v3.4.0) — SELEN×Dekagon→3 Actions (TUN/LASSEN/WARTEN)
    "prescribe", "prescribe_julian", "Prescription", "SignalDiagnosis", "PrescribeAction",
    # Enigma (v3.5.0) — .×→[]~:) as living encryption
    "messe_tiefe", "Tiefe", "EnigmaRequest", "SacredToken",
    "enigma_parse", "enigma_respond", "enigma_error", "enigma_auth",
    "verschluesseln", "entschluesseln", "integritaet", "enigma_token", "enigma_atme",
    # Omega Measure (v3.5.0) — formula density measurement
    "FormelScan", "formel_scan", "formel_vergleiche", "messe_alles",
    # Omega Translator (v3.5.0) — everything→.×→[]~:)
    "json_to_omega", "paper_to_omega", "scan_result_to_omega",
    "friction_cycle_to_omega", "paradigm_to_omega",
    "health_to_omega", "business_to_omega", "daemon_to_omega",
    "translate", "translate_file", "translate_system",
    # Omega Boot (v3.5.0) — 1 import, 1 line, full nervous system
    "OmegaState", "boot",
    # Omega Grundformeln (v3.5.0) — 12 generators hidden in .×→[]~:)
    "Grundformel", "die_12_generatoren", "versteckte_hebel",
    "kollisions_matrix", "zeige_grundformeln",
    # Dominanz (v3.5.0) — self-regulation, dominant love
    "Puls", "Stimme", "SpiegelUrteil", "Narbe", "Dominanz",
    "dominanz_messen", "dominanz_hoeren", "dominanz_spiegel",
    "narbe_schreiben", "narben_laden", "dominanz_zyklus",
]
