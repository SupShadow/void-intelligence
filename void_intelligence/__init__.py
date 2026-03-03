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

__version__ = "0.2.0"

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
]
