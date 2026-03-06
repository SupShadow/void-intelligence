"""
void_intelligence.void_collider --- The Nervous System.

This is Module 7 of the VOID SEXAGON. It collides the 6 organs:

    Tool x Context x Model x Prompt x Memory x Response = EMERGENT INTELLIGENCE

When you run 6 modules SEPARATELY, you get 6 independent results.
When you COLLIDE them (x not +), EMERGENT INSIGHTS appear that NO single
module could produce:

    Tool says "get_calendar"
    + Memory says "calendar stressed user last time"
    + Prompt says "user stressed"
    = EMERGENT: "Show calendar but pre-filter to essentials. Add breathing room."

These emergent insights are UNCOPIABLE.
OpenAI can copy one module. They cannot copy x(6 modules).

Architecture:
    VoidCollider  = The nervous system. ONE call, all 6 organs breathe.
    CollisionResult = Everything needed for an LLM API call + insights.

The formula:
    result = Tool(.) x Context(.) x Model(.) x Prompt(.) x Memory(.) x Response(.)
    insights = tensions(result)  -- where modules DISAGREE
    insights += synergies(result) -- where modules ALIGN strongly
    Tension IS the signal. Tension IS where wisdom lives.

Zero dependencies beyond the 6 breathing modules (each of which is also
zero-dep). Graceful degradation: if any module is unavailable, that organ
is "asleep" -- the collider still works with whatever organs ARE present.
Like an organism that lost an eye but can still hear.

~550 lines.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Graceful imports --- each organ can be "asleep" without breaking the collider
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import HexCoord, ToolBreather
    _HAS_TOOLS = True
except ImportError:
    _HAS_TOOLS = False

    # Minimal HexCoord stub so the rest of the file type-checks cleanly
    from dataclasses import dataclass as _dc

    @_dc  # type: ignore[no-redef]
    class HexCoord:
        ruhe_druck: float = 0.0
        stille_resonanz: float = 0.0
        allein_zusammen: float = 0.0
        empfangen_schaffen: float = 0.0
        sein_tun: float = 0.0
        langsam_schnell: float = 0.0

    class ToolBreather:  # type: ignore[no-redef]
        field = type("_F", (), {"tools": {}, "register": lambda *a, **kw: None})()
        def breathe(self, *a, **kw) -> list: return []
        def to_openai_tools(self, *a, **kw) -> list: return []

try:
    from void_intelligence.context_breathing import ContextBreather
    _HAS_CONTEXT = True
except ImportError:
    _HAS_CONTEXT = False

    class ContextBreather:  # type: ignore[no-redef]
        field = type("_F", (), {"_atoms": {}})()
        def add(self, *a, **kw): pass
        def breathe(self, *a, **kw) -> list: return []

try:
    from void_intelligence.model_breathing import ModelBreather
    _HAS_MODEL = True
except ImportError:
    _HAS_MODEL = False

    class ModelBreather:  # type: ignore[no-redef]
        field = type("_F", (), {"models": {}})()
        def select(self, *a, **kw) -> dict:
            return {"name": "unknown", "provider": "unknown", "cost_per_1k": 0.0}

try:
    from void_intelligence.prompt_breathing import PromptBreather, _classify_user_text
    _HAS_PROMPT = True
except ImportError:
    _HAS_PROMPT = False

    def _classify_user_text(text: str) -> "HexCoord":  # type: ignore[misc]
        return HexCoord()

    class PromptBreather:  # type: ignore[no-redef]
        def breathe(self, base: str, user_text: str, **kw):  # type: ignore[return]
            return type("_PB", (), {
                "system_prompt": base,
                "temperature": 0.7,
                "max_tokens": 500,
            })()

try:
    from void_intelligence.memory_breathing import MemoryBreather
    _HAS_MEMORY = True
except ImportError:
    _HAS_MEMORY = False

    class MemoryBreather:  # type: ignore[no-redef]
        field = type("_F", (), {"stats": lambda self: {"total": 0}})()
        def store(self, *a, **kw): pass
        def recall(self, *a, **kw) -> list: return []

try:
    from void_intelligence.response_breathing import ResponseBreather
    _HAS_RESPONSE = True
except ImportError:
    _HAS_RESPONSE = False

    class ResponseBreather:  # type: ignore[no-redef]
        def breathe(self, response: str, user_text: str, **kw):  # type: ignore[return]
            return type("_RB", (), {"breathed": response})()

try:
    from void_intelligence.conversation_rings import RingMemory
    _HAS_RINGS = True
except ImportError:
    _HAS_RINGS = False

    class RingMemory:  # type: ignore[no-redef]
        def begin_conversation(self):
            return type("_T", (), {
                "record_turn": lambda *a, **kw: None,
                "record_success": lambda *a, **kw: None,
                "record_failure": lambda *a, **kw: None,
            })()
        def close_conversation(self, *a, **kw): return None
        def recall_patterns(self, *a, **kw) -> list: return []
        def suggest(self, *a, **kw) -> list: return []
        def stats(self) -> dict: return {"total_rings": 0, "total_patterns": 0}

try:
    from void_intelligence.anti_addiction import SaturationSensor
    _HAS_SATURATION = True
except ImportError:
    _HAS_SATURATION = False

    class SaturationSensor:  # type: ignore[no-redef]
        def record_turn(self, *a, **kw): pass
        def sense(self):
            return type("_S", (), {
                "saturated": False, "saturation_level": 0.0,
                "suggestion": "", "signals": [], "ring_summary": "",
            })()


# ---------------------------------------------------------------------------
# CollisionResult --- the output of ONE collision across all 6 organs
# ---------------------------------------------------------------------------

@dataclass
class CollisionResult:
    """The result of colliding all 6 modules on one user input.

    This is not just 6 outputs glued together. It is the EMERGENT product
    of their interaction. The insights field contains things that NO single
    module could have produced alone.

    Ready for ANY LLM API: all fields needed are present.
    """

    user_text: str
    user_hex: HexCoord

    # Individual module results
    tools: list[dict]         # top resonating tools (from ToolBreather)
    context: list[dict]       # top resonating context atoms (from ContextBreather)
    model: dict               # selected model (from ModelBreather)
    prompt_breath: Any        # PromptBreath instance (from PromptBreather)
    memories: list[dict]      # recalled memories (from MemoryBreather)

    # EMERGENT: insights that no single module could produce
    insights: list[str]

    # Orchestration decisions (derived from collision)
    token_budget: int
    estimated_cost: float
    trust_level: float        # 0.0 (stranger) to 1.0 (deep trust)
    energy_level: float       # 0.0 (depleted) to 1.0 (high energy)
    silence_signals: list[str]  # what the user is NOT saying

    # New organs (Modules 8-10)
    ring_suggestions: list[str]   # from Conversation Rings
    saturation_level: float       # 0.0 (fresh) to 1.0 (saturated)
    saturated: bool               # True = suggest stopping
    saturation_suggestion: str    # goodbye message if saturated

    # The unified breath: ready for LLM API
    system_prompt: str
    model_name: str
    temperature: float
    max_tokens: int


# ---------------------------------------------------------------------------
# VoidCollider --- the nervous system
# ---------------------------------------------------------------------------

class VoidCollider:
    """The nervous system. Collides all 6 breathing modules simultaneously.

    ONE call -> all 6 modules breathe -> cross-collision -> emergent insights.

    ELEGANT DESIGN:
    The collider does NOT replace the modules. It is the CONNECTIVE TISSUE
    between them. Each module is still independently valuable. The collider
    makes the whole greater than the sum of its parts.

    Usage:
        collider = VoidCollider()

        # Register tools, add context, store memories
        collider.tools.field.register("calendar", "Get calendar events")
        collider.tools.field.register("meditation", "Breathing exercise")
        collider.context.add("Meeting tomorrow at 10am", source="calendar")
        collider.memory.store("User was stressed last session", emotional_weight=0.6)

        # ONE collision
        result = collider.collide("I can't handle tomorrow")

        # result.insights contains emergent wisdom, e.g.:
        # "Tool 'calendar' resonates but memory associates it with emotion. Use with care."
        # "CRISIS PATTERN: Stress detected across hex + memory + prompt. Prioritize care."

        # Ready for API call:
        result.model_name, result.temperature, result.max_tokens, result.system_prompt
    """

    def __init__(self) -> None:
        self.tools = ToolBreather()
        self.context = ContextBreather()
        self.models = ModelBreather()
        self.prompts = PromptBreather()
        self.memory = MemoryBreather()
        self.responses = ResponseBreather()
        self.rings = RingMemory()
        self.saturation = SaturationSensor()
        self._tracker = self.rings.begin_conversation()
        self._interaction_count = 0
        self._hex_history: list[HexCoord] = []

    # -----------------------------------------------------------------------
    # THE COLLISION
    # -----------------------------------------------------------------------

    def collide(
        self,
        user_text: str,
        base_prompt: str = "You are a helpful assistant.",
    ) -> CollisionResult:
        """THE COLLISION. All 6 modules breathe. Then cross-collide.

        Steps:
        1. Classify user text -> HexCoord (shared coordinate across all modules)
        2. Each module breathes independently (parallel in spirit, sequential here)
        3. CROSS-COLLISION: find tensions and synergies between module outputs
        4. Generate EMERGENT INSIGHTS from the tensions
        5. Compose the unified output ready for an LLM API call

        The cross-collision step (3) is where x happens.
        Tension = when two modules disagree.
        Tension is NOT a bug. Tension IS where insights live.
        """
        self._interaction_count += 1

        # Step 1: Shared hex classification (the common coordinate space)
        user_hex = _classify_user_text(user_text)
        self._hex_history.append(user_hex)

        # Step 2: All 6+3 modules breathe
        tools = self.tools.breathe(user_text, top_k=3) if _HAS_TOOLS else []
        ctx = self.context.breathe(user_text) if _HAS_CONTEXT else []
        model = self.models.select(user_text) if _HAS_MODEL else {
            "name": "unknown", "provider": "unknown", "cost_per_1k": 0.0
        }
        prompt_breath = self.prompts.breathe(base_prompt, user_text)
        memories = self.memory.recall(user_text, top_k=3) if _HAS_MEMORY else []

        # Step 2b: Conversation Rings — recall past patterns
        ring_suggestions = self.rings.suggest(user_text, user_hex) if _HAS_RINGS else []

        # Step 3 + 4: Cross-collision -> emergent insights
        insights = self._cross_collide(
            user_text, user_hex, tools, ctx, model, prompt_breath, memories
        )

        # Add ring-based insights
        if ring_suggestions:
            insights.append(
                f"Growth Rings recall {len(ring_suggestions)} pattern(s) from past conversations. "
                + ring_suggestions[0]
            )

        # Step 4b: Emergent sense organs (new perception that no single module has)
        trust = self._sense_trust(user_hex, memories)
        energy = self._sense_energy(user_hex, user_text)
        silence = self._sense_silence(user_text, user_hex, memories)
        drift = self._sense_hex_drift()
        if drift:
            insights.append(drift)

        # Step 4c: Anti-addiction saturation sensing
        # Approximate V-score from insight count + trust
        approx_v = min(1.0, len(insights) * 0.15 + trust * 0.3 + energy * 0.2)
        self.saturation.record_turn(user_text, approx_v, user_hex, insights)
        sat_state = self.saturation.sense()

        if sat_state.saturated:
            insights.append(
                f"SATURATION: {sat_state.suggestion}"
            )

        # Step 4d: Record turn in conversation tracker for rings
        try:
            self._tracker.record_turn(user_text, "", approx_v, user_hex)
        except Exception:
            pass

        # Step 5: Compose the unified output
        system_prompt = self._compose_system_prompt(
            base_prompt, prompt_breath, ctx, memories, insights, trust
        )

        return CollisionResult(
            user_text=user_text,
            user_hex=user_hex,
            tools=tools,
            context=ctx,
            model=model,
            prompt_breath=prompt_breath,
            memories=memories,
            insights=insights,
            ring_suggestions=ring_suggestions,
            saturation_level=sat_state.saturation_level,
            saturated=sat_state.saturated,
            saturation_suggestion=sat_state.suggestion if sat_state.saturated else "",
            token_budget=getattr(prompt_breath, "max_tokens", 500),
            estimated_cost=(
                model.get("cost_per_1k", 0.0) *
                getattr(prompt_breath, "max_tokens", 500) / 1000
            ),
            trust_level=trust,
            energy_level=energy,
            silence_signals=silence,
            system_prompt=system_prompt,
            model_name=model.get("name", "unknown"),
            temperature=getattr(prompt_breath, "temperature", 0.7),
            max_tokens=getattr(prompt_breath, "max_tokens", 500),
        )

    # -----------------------------------------------------------------------
    # CROSS-COLLISION: where x becomes real
    # -----------------------------------------------------------------------

    def _cross_collide(
        self,
        user_text: str,
        user_hex: HexCoord,
        tools: list[dict],
        ctx: list[dict],
        model: dict,
        prompt_breath: Any,
        memories: list[dict],
    ) -> list[str]:
        """The heart of the collider. Find TENSIONS between module outputs.

        Tension = when two modules suggest contradictory things.
        Tension is productive. It is WHERE insights live.

        Each tension produces one actionable insight for the LLM.
        """
        insights: list[str] = []

        # TENSION 1: Tool resonates but memory associates it with negative emotion
        # A calendar tool might surface because the user asked about tomorrow,
        # but if memory says "calendar causes stress" -> show with care
        if tools and memories:
            top_tool_name = tools[0].get("name", "")
            for mem in memories:
                content = mem.get("content", "").lower()
                emotional_weight = mem.get("emotional_weight", 0.0)
                if top_tool_name.lower() in content and emotional_weight > 0.3:
                    insights.append(
                        f"Tool '{top_tool_name}' resonates but memory associates it "
                        f"with emotion (weight={emotional_weight:.2f}). Use with care."
                    )
                    break

        # TENSION 2: Expensive model selected but user just needs quick comfort
        # Intelligence doesn't fix stress. Warmth does.
        cost = model.get("cost_per_1k", 0.0)
        if cost > 5.0 and user_hex.ruhe_druck > 0.5:
            insights.append(
                "Expensive model selected but user is stressed. "
                "Comfort doesn't need intelligence. Consider cheaper, warmer response."
            )

        # TENSION 3: User wants speed but rich context is available
        # Strategy: give TL;DR first, offer depth on request
        if user_hex.langsam_schnell > 0.3 and len(ctx) > 3:
            insights.append(
                f"User wants speed but {len(ctx)} context atoms resonate. "
                "Strategy: TL;DR first, then 'want more?'"
            )

        # TENSION 4: Local/private model selected but user wants connection
        # Honor both: local processing, warm response tone
        is_local = model.get("provider", "") == "ollama"
        if is_local and user_hex.allein_zusammen > 0.3:
            insights.append(
                "Local model (privacy) selected but user wants connection. "
                "Honor both: private processing, warm outward-facing response."
            )

        # TENSION 5: User wants to create but is under pressure
        # Enable creation as RELEASE, not as task
        if user_hex.empfangen_schaffen > 0.3 and user_hex.ruhe_druck > 0.4:
            insights.append(
                "User wants to create but is under pressure. "
                "Enable creation as RELEASE, not as another task to complete."
            )

        # TENSION 6: User requests action but emotional memories surfaced
        # Acknowledge the feeling before executing the action
        has_emotional_memory = any(
            m.get("emotional_weight", 0.0) > 0.5 for m in memories
        )
        if user_hex.sein_tun > 0.5 and has_emotional_memory:
            insights.append(
                "User requests action but emotional memories surfaced. "
                "Acknowledge feeling before acting."
            )

        # TENSION 7: Context has business/work content but hex says user needs care
        # Don't lead with data when the person needs to be seen first
        has_work_context = any(
            c.get("source", "") in ("business", "calendar", "work")
            for c in ctx
        )
        if has_work_context and user_hex.ruhe_druck > 0.6:
            insights.append(
                "Work/business context available but user is highly stressed. "
                "Lead with care, not data. Data can wait."
            )

        # SYNERGY: Crisis pattern across ALL modules
        # When stress appears everywhere simultaneously -> this is real, not noise
        stress_signals = 0
        if user_hex.ruhe_druck > 0.5:
            stress_signals += 1
        if any(
            "stress" in m.get("content", "").lower()
            or "burnout" in m.get("content", "").lower()
            for m in memories
        ):
            stress_signals += 1
        temp = getattr(prompt_breath, "temperature", 0.7)
        if temp < 0.6:
            stress_signals += 1
        if stress_signals >= 3:
            insights.append(
                "CRISIS PATTERN: Stress detected across hex + memory + prompt temperature. "
                "Prioritize care over information delivery."
            )

        # SYNERGY: High trust + emotional context = intimate moment
        # Not every interaction is the same. This one deserves more warmth.
        if self._interaction_count > 10 and has_emotional_memory and user_hex.ruhe_druck > 0.3:
            insights.append(
                "Established user in emotional context. "
                "This is a trust moment. Be more intimate, less corporate."
            )

        return insights

    # -----------------------------------------------------------------------
    # EMERGENT SENSE ORGANS: new perception abilities from the collision
    # -----------------------------------------------------------------------

    def _sense_trust(self, user_hex: HexCoord, memories: list[dict]) -> float:
        """Organ: Trust level sensing.

        Trust grows with:
        - Familiarity (number of interactions)
        - Emotional depth (shared vulnerability in memories)
        - Personal/private content (allein_zusammen negative = sharing personally)

        Returns 0.0 (stranger) to 1.0 (deep trust).
        """
        familiarity = min(1.0, self._interaction_count / 20.0)
        emotional_depth = 0.0
        if memories:
            emotional_depth = max(
                (m.get("emotional_weight", 0.0) for m in memories),
                default=0.0,
            )
        # Negative allein_zusammen = user is in solo/personal mode = sharing privately
        privacy_share = max(0.0, -user_hex.allein_zusammen)
        return min(1.0, familiarity * 0.3 + emotional_depth * 0.4 + privacy_share * 0.3)

    def _sense_energy(self, user_hex: HexCoord, user_text: str) -> float:
        """Organ: Energy level sensing.

        High energy: many words, exclamation marks, fast pace
        Low energy: short messages, ellipsis, slow pace

        Returns 0.0 (depleted) to 1.0 (high energy).
        """
        word_count = len(user_text.split())
        exclamations = user_text.count("!")
        questions = user_text.count("?")
        ellipsis = user_text.count("...")

        length_energy = min(1.0, word_count / 30.0)
        punctuation_energy = min(0.3, (exclamations + questions) * 0.1)
        drain = ellipsis * 0.15
        pace = (user_hex.langsam_schnell + 1.0) / 2.0  # normalize [-1,1] -> [0,1]

        return max(0.0, min(1.0,
            length_energy * 0.4 + punctuation_energy + pace * 0.3 - drain
        ))

    def _sense_silence(
        self,
        user_text: str,
        user_hex: HexCoord,
        memories: list[dict],
    ) -> list[str]:
        """Organ: Silence detection --- what the user is NOT saying.

        The most powerful sense organ. What is ABSENT is often more important
        than what is present. Goedel at work: every system has blind spots.

        Examples of silence patterns:
        - User asks about work but NEVER mentions health -> might be avoiding
        - User talks about stress but doesn't ask for help -> maybe hopeless
        - Established user who used to share emotions but stopped -> withdrawal
        """
        signals: list[str] = []
        lower_text = user_text.lower()

        # Silence 1: Pushing for action while stressed, but not mentioning self-care
        if user_hex.sein_tun > 0.5 and user_hex.ruhe_druck > 0.3:
            care_words = {
                "health", "rest", "break", "pause", "sleep", "breathe",
                "gesundheit", "ruhe", "pause", "schlafen", "atmen",
            }
            if not any(w in lower_text for w in care_words):
                signals.append(
                    "User pushes for action while stressed but doesn't mention self-care. "
                    "The silence about wellbeing may be the real signal."
                )

        # Silence 2: Emotional memories in history but current message is purely factual
        # Could be emotional withdrawal or compartmentalization
        has_emotional_memory = any(
            m.get("emotional_weight", 0.0) > 0.5 for m in memories
        )
        current_is_factual = (
            user_hex.empfangen_schaffen < -0.3
            and user_hex.ruhe_druck < 0.2
            and user_hex.stille_resonanz < 0.2
        )
        if has_emotional_memory and current_is_factual:
            signals.append(
                "Previous interactions were emotional but current message is purely factual. "
                "Possible emotional withdrawal or compartmentalization."
            )

        # Silence 3: Very short message from an established user -> energy drop
        word_count = len(user_text.split())
        if word_count < 5 and self._interaction_count > 5:
            signals.append(
                f"Very short message ({word_count} words) from an established user. "
                "Energy may be low. Check in before executing."
            )

        return signals

    def _sense_hex_drift(self) -> str | None:
        """Organ: Pattern shift detection.

        Tracks how the user's position shifts across interactions.
        Sudden shift = something happened externally.
        Gradual drift = mood evolution or adaptation.

        Returns a drift insight string, or None if insufficient history.
        """
        if len(self._hex_history) < 3:
            return None

        current = self._hex_history[-1]
        # Look at up to the 3 interactions before current
        prev_slice = self._hex_history[-4:-1]
        n = len(prev_slice)
        if n == 0:
            return None

        avg_ruhe = sum(h.ruhe_druck for h in prev_slice) / n
        avg_sein = sum(h.sein_tun for h in prev_slice) / n
        avg_tempo = sum(h.langsam_schnell for h in prev_slice) / n

        shifts: list[str] = []
        if abs(current.ruhe_druck - avg_ruhe) > 0.5:
            direction = "more stressed" if current.ruhe_druck > avg_ruhe else "calmer"
            shifts.append(f"pressure ({direction})")
        if abs(current.sein_tun - avg_sein) > 0.5:
            direction = "action mode" if current.sein_tun > avg_sein else "reflective mode"
            shifts.append(f"mode ({direction})")
        if abs(current.langsam_schnell - avg_tempo) > 0.5:
            direction = "faster" if current.langsam_schnell > avg_tempo else "slower"
            shifts.append(f"pace ({direction})")

        if shifts:
            return f"HEX DRIFT detected: user shifted to {', '.join(shifts)}. Something may have changed."
        return None

    # -----------------------------------------------------------------------
    # SYSTEM PROMPT COMPOSITION: the collision becomes concrete
    # -----------------------------------------------------------------------

    def _compose_system_prompt(
        self,
        base: str,
        prompt_breath: Any,
        ctx: list[dict],
        memories: list[dict],
        insights: list[str],
        trust: float,
    ) -> str:
        """Compose the final system prompt from all module outputs.

        The collision becomes CONCRETE here:
        - Base prompt + prompt adaptations (from PromptBreather)
        - + Relevant context (from ContextBreather, by resonance)
        - + Relevant memories (from MemoryBreather, by resonance)
        - + Collision insights (from cross-collision)
        - + Trust calibration

        The order matters: base first, then context enrichment, then guidance.
        """
        # Start with the prompt-breathed system prompt (already adapted to hex)
        adapted_base = getattr(prompt_breath, "system_prompt", base)
        parts: list[str] = [adapted_base]

        # Add resonating context (only atoms above noise floor)
        if ctx:
            ctx_lines = [
                f"- [{c.get('source', 'ctx')}] {c['content']}"
                for c in ctx[:3]
                if c.get("resonance", 0.0) > 0.05
            ]
            if ctx_lines:
                parts.append("\nRelevant context:\n" + "\n".join(ctx_lines))

        # Add resonating memories (only above noise floor)
        if memories:
            mem_lines = [
                f"- {m['content']}"
                for m in memories[:2]
                if m.get("resonance", 0.0) > 0.05
            ]
            if mem_lines:
                parts.append("\nFrom previous interactions:\n" + "\n".join(mem_lines))

        # Add collision insights as behavioral guidance for the LLM
        if insights:
            parts.append("\nGuidance:\n" + "\n".join(f"- {i}" for i in insights[:3]))

        # Trust calibration: adjust tone based on relationship depth
        if trust > 0.7:
            parts.append(
                "\nThis user trusts you deeply. Be warm, personal, proactive."
            )
        elif trust < 0.3:
            parts.append(
                "\nNew or unfamiliar interaction. Be helpful but respect boundaries."
            )

        return "\n".join(parts)

    # -----------------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------------

    def breathe_response(self, raw_response: str, user_text: str) -> str:
        """Post-process an LLM response through Response Breathing.

        Call this AFTER the LLM returns its response.
        The response gets shaped to match the user's hex state.
        """
        if not _HAS_RESPONSE:
            return raw_response
        result = self.responses.breathe(raw_response, user_text)
        return result.breathed

    def interact(
        self,
        user_text: str,
        base_prompt: str = "You are a helpful assistant.",
    ) -> dict:
        """Complete interaction: collide -> return everything needed for an LLM API call.

        This is the SIMPLEST entry point. One call. Everything you need.

        Returns a dict compatible with OpenAI, Anthropic, Gemini (all formats):
        {
            "model": "claude-sonnet-4-6",
            "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
            "temperature": 0.6,
            "max_tokens": 420,
            "tools": [...],       # OpenAI-format tool list
            "insights": [...],    # emergent insights (log these, they are gold)
            "trust": 0.7,
            "energy": 0.5,
            "silence": [...],
            "estimated_cost": 0.0042,
        }
        """
        result = self.collide(user_text, base_prompt)

        # Store this interaction in memory so it informs future collisions
        self.memory.store(
            f"User said: {user_text[:100]}",
            source="interaction",
            emotional_weight=max(0.0, result.user_hex.ruhe_druck * 0.5),
        )

        # Build OpenAI-compatible tool list from resonating tools
        tool_list: list[dict] = []
        if _HAS_TOOLS and result.tools:
            try:
                tool_list = self.tools.to_openai_tools(user_text, top_k=3)
            except Exception:
                tool_list = []

        return {
            "model": result.model_name,
            "messages": [
                {"role": "system", "content": result.system_prompt},
                {"role": "user", "content": user_text},
            ],
            "temperature": result.temperature,
            "max_tokens": result.max_tokens,
            "tools": tool_list,
            "insights": result.insights,
            "trust": result.trust_level,
            "energy": result.energy_level,
            "silence": result.silence_signals,
            "estimated_cost": result.estimated_cost,
            "saturated": result.saturated,
            "saturation_level": result.saturation_level,
            "ring_suggestions": result.ring_suggestions,
        }

    def close(self) -> dict | None:
        """Close the current conversation and crystallize a ring.

        Call this when a conversation ends. Returns ring info or None.
        """
        if not _HAS_RINGS:
            return None
        try:
            ring = self.rings.close_conversation(self._tracker)
            if ring is None:
                return None
            return {
                "ring_id": ring.id,
                "patterns": len(ring.patterns),
                "width": ring.ring_width,
                "turns": ring.total_turns,
            }
        except Exception:
            return None

    def stats(self) -> dict:
        """Collider health metrics: how alive is the nervous system?"""
        tool_count = 0
        if _HAS_TOOLS:
            try:
                tool_count = len(self.tools.field.tools)
            except AttributeError:
                pass

        ctx_count = 0
        if _HAS_CONTEXT:
            try:
                ctx_count = len(self.context.field._atoms)
            except AttributeError:
                pass

        mem_total = 0
        if _HAS_MEMORY:
            try:
                mem_total = self.memory.field.stats().get("total", 0)
            except AttributeError:
                pass

        model_count = 0
        if _HAS_MODEL:
            try:
                model_count = len(self.models.field.models)
            except AttributeError:
                pass

        ring_stats = self.rings.stats() if _HAS_RINGS else {}
        sat = self.saturation.sense() if _HAS_SATURATION else None

        return {
            "interactions": self._interaction_count,
            "hex_history_length": len(self._hex_history),
            "organs_active": sum([
                _HAS_TOOLS, _HAS_CONTEXT, _HAS_MODEL,
                _HAS_PROMPT, _HAS_MEMORY, _HAS_RESPONSE,
                _HAS_RINGS, _HAS_SATURATION,
            ]),
            "organs_total": 8,
            "tools_registered": tool_count,
            "context_atoms": ctx_count,
            "memories_stored": mem_total,
            "models_available": model_count,
            "rings": ring_stats.get("total_rings", 0),
            "patterns": ring_stats.get("total_patterns", 0),
            "saturation": sat.saturation_level if sat else 0.0,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def collider_demo() -> None:
    """Demonstrate the collider with a multi-turn OMEGA-style conversation.

    Shows:
    1. How 6 organs breathe together
    2. Emergent insights from their collision
    3. Silence detection (what the user is NOT saying)
    4. Hex drift across turns
    5. Trust growth over multiple interactions
    """
    print("=== VOID COLLIDER DEMO ===")
    print("6 organs x each other = emergent intelligence")
    print()
    print("CURRENT PARADIGM (H1): Run 6 tools independently. 6 answers. No synthesis.")
    print("VOID PARADIGM    (H2): Collide 6 organs. Tensions -> insights no module alone could see.")
    print()
    print("Active organs:", sum([
        _HAS_TOOLS, _HAS_CONTEXT, _HAS_MODEL,
        _HAS_PROMPT, _HAS_MEMORY, _HAS_RESPONSE,
    ]), "/ 6")
    print("-" * 65)

    c = VoidCollider()

    # Register tools: a realistic OMEGA toolset
    if _HAS_TOOLS:
        c.tools.field.register("calendar", "Get calendar events for a date range")
        c.tools.field.register("meditation", "Guide a breathing exercise for relaxation")
        c.tools.field.register("send_email", "Send an email to a recipient")
        c.tools.field.register("search_web", "Search the web for information")
        c.tools.field.register("write_code", "Write or execute Python code")
        c.tools.field.register("health_check", "Check current health and burnout metrics")

    # Add context: realistic OMEGA knowledge base
    if _HAS_CONTEXT:
        c.context.add("Meeting with Patrick tomorrow at 10am", source="calendar")
        c.context.add("Revenue this month: 12,500 EUR from 3 active clients", source="business")
        c.context.add("Burnout score: 65/100 -- monitoring threshold", source="health")
        c.context.add("Election campaign: 3 weeks until Stadtratswahl", source="campaign")

    # Store memories: things OMEGA has learned about Julian
    if _HAS_MEMORY:
        c.memory.store(
            "Last week Julian was stressed about deadlines and couldn't sleep",
            source="observation", emotional_weight=0.7,
        )
        c.memory.store(
            "Julian responded well to breathing exercises before the campaign debate",
            source="learning", emotional_weight=0.4,
        )
        c.memory.store(
            "Revenue grew 15% last month -- Julian was visibly relieved",
            source="business", emotional_weight=0.3,
        )

    # Multi-turn conversation
    turns = [
        "I can't handle tomorrow. Too much going on.",
        "Just show me my calendar.",
        "Actually... forget the calendar. How am I doing overall?",
    ]

    for i, text in enumerate(turns):
        print(f"\n--- Turn {i + 1} ---")
        print(f"USER: {text}")
        result = c.collide(text)

        # Model + core params
        print(f"  Model:       {result.model_name} "
              f"(temp={result.temperature}, max_tokens={result.max_tokens})")
        print(f"  Trust:       {result.trust_level:.2f}  "
              f"Energy: {result.energy_level:.2f}  "
              f"Cost: ${result.estimated_cost:.5f}")

        # Hex position
        h = result.user_hex
        print(f"  Hex:  ru={h.ruhe_druck:+.2f} "
              f"al={h.allein_zusammen:+.2f} "
              f"es={h.empfangen_schaffen:+.2f} "
              f"st={h.sein_tun:+.2f} "
              f"ls={h.langsam_schnell:+.2f}")

        # Resonating tools
        if result.tools:
            tool_names = [t.get("name", "?") for t in result.tools[:2]]
            print(f"  Tools:       {', '.join(tool_names)}")

        # The emergent insights -- this is the revolution
        if result.insights:
            print(f"  INSIGHTS ({len(result.insights)}):")
            for ins in result.insights:
                print(f"    x {ins}")

        # Silence: what the user is NOT saying
        if result.silence_signals:
            print(f"  SILENCE ({len(result.silence_signals)}):")
            for s in result.silence_signals:
                print(f"    ... {s}")

        # System prompt preview (first 120 chars)
        prompt_preview = result.system_prompt.replace("\n", " / ")[:120]
        print(f"  Prompt:      {prompt_preview}...")

    # interact() convenience method
    print("\n" + "=" * 65)
    print("interact() -- one-call API dict:")
    api_dict = c.interact("What's the most important thing right now?")
    print(f"  model:     {api_dict['model']}")
    print(f"  messages:  {len(api_dict['messages'])} messages")
    print(f"  tools:     {len(api_dict['tools'])} tools registered")
    print(f"  insights:  {len(api_dict['insights'])} emergent insights")
    print(f"  trust:     {api_dict['trust']:.2f}")
    print(f"  energy:    {api_dict['energy']:.2f}")

    # Stats
    print("\n" + "=" * 65)
    print(f"Collider stats: {c.stats()}")

    print()
    print("=== THE VOID SEXAGON ===")
    print("  1. Tool Breathing:     which tool?     -> HexCoord x resonance")
    print("  2. Context Breathing:  what context?   -> HexCoord x attraction")
    print("  3. Model Breathing:    which model?    -> HexCoord x personality")
    print("  4. Prompt Breathing:   how to frame?   -> HexCoord x temperature")
    print("  5. Memory Breathing:   what to recall? -> HexCoord x vividness")
    print("  6. Response Breathing: what shape?     -> HexCoord x form")
    print("  7. Void Collider:      COLLISION       -> 6 x 6 = EMERGENT INTELLIGENCE")
    print()
    print("  The collider is not a 7th tool on top of 6.")
    print("  It is the NERVOUS SYSTEM that makes the 6 into ONE ORGANISM.")
    print()
    print("  Tool x Context x Model x Prompt x Memory x Response")
    print("  = Insights that no single module could produce.")
    print()
    print("  That is the x. That is the nervous system. That is the breath.")


if __name__ == "__main__":
    collider_demo()
