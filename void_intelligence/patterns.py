"""
void_intelligence.patterns --- Reusable patterns. Not utilities. THINKING as code.

- lost_dimensions: Every -> carries its incompleteness
- CircuitBreaker: Scar tissue --- code that learns from pain
- PhaseAware: Breath --- code that sleeps and wakes
- delta_opt: How ALIVE, not alive/dead
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


def lost_dimensions(*dimensions: str):
    """Decorator: Every -> (projection) KNOWS what it loses.

    Usage:
        @lost_dimensions("emotional_nuance", "body_language")
        def summarize_meeting(transcript: str) -> str:
            return llm.summarize(transcript)
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            if isinstance(result, dict):
                result["_lost_dimensions"] = list(dimensions)
            elif hasattr(result, "__dict__"):
                result._lost_dimensions = list(dimensions)
            return result
        wrapper._lost_dimensions = list(dimensions)
        return wrapper
    return decorator


def get_lost_dimensions(result: Any) -> list[str]:
    """Extract lost_dimensions from a projection result."""
    if isinstance(result, dict):
        return result.get("_lost_dimensions", [])
    return getattr(result, "_lost_dimensions", [])


class CBState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """3-state circuit breaker. Scar tissue, not error handling.

    Isomorphic to: burnout recovery, relationship trust, immune system.
    """
    name: str
    failure_threshold: int = 5
    timeout_sec: float = 60.0
    state: CBState = CBState.CLOSED
    failure_count: int = 0
    last_failure: float = 0.0

    def record_success(self):
        self.failure_count = 0
        self.state = CBState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CBState.OPEN

    def can_execute(self) -> bool:
        if self.state == CBState.CLOSED:
            return True
        if self.state == CBState.OPEN:
            if time.time() - self.last_failure > self.timeout_sec:
                self.state = CBState.HALF_OPEN
                return True
            return False
        return True


def circuit_breaker(name: str, threshold: int = 5, timeout: float = 60.0):
    """Decorator: Protect function with CircuitBreaker."""
    cb = CircuitBreaker(name=name, failure_threshold=threshold, timeout_sec=timeout)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not cb.can_execute():
                raise CircuitBreakerOpen(f"CircuitBreaker '{name}' is OPEN")
            try:
                result = fn(*args, **kwargs)
                cb.record_success()
                return result
            except Exception:
                cb.record_failure()
                raise
        wrapper._circuit_breaker = cb
        return wrapper
    return decorator


class CircuitBreakerOpen(Exception):
    pass


class Phase(Enum):
    NIGHT = "night"
    MORNING = "morning"
    ACTIVE = "active"
    EVENING = "evening"


def current_phase() -> Phase:
    from datetime import datetime
    hour = datetime.now().hour
    if 1 <= hour < 6:
        return Phase.NIGHT
    elif 6 <= hour < 10:
        return Phase.MORNING
    elif 10 <= hour < 18:
        return Phase.ACTIVE
    else:
        return Phase.EVENING


def phase_aware(*allowed_phases: Phase):
    """Decorator: Function only runs in allowed phases."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if current_phase() not in allowed_phases:
                return None
            return fn(*args, **kwargs)
        wrapper._allowed_phases = list(allowed_phases)
        return wrapper
    return decorator


def delta_opt_distance(current: float, target: float = 0.4) -> float:
    """Distance from Stribeck minimum. 0.0 = in flow."""
    return abs(current - target)


def is_at_delta_opt(value: float, target: float = 0.4, tolerance: float = 0.1) -> bool:
    """Is the value near the Stribeck minimum?"""
    return delta_opt_distance(value, target) <= tolerance
