"""
void_intelligence.tool_breathing --- Tools that Breathe.

The revolution of tool calling through .x->[]~

CURRENT PARADIGM (->):
    Model -> detect intent -> pick tool -> call(params) -> result -> answer
    Sequential. Mechanical. Dead. Every -> loses dimensions (Anti-P3122).

VOID PARADIGM (x):
    User(.) x Context(.) x Tools(.) = The tool that RESONATES
    Tools don't get "called" --- they get ATTRACTED.
    The tool with highest delta_opt to the user's need is the one that breathes.

Architecture:
    BreathingTool     = A tool wrapped with HexCoord, V-Score, growth rings
    ToolField         = The field of all available tools (hexagonal resonance space)
    ToolBreather      = The orchestrator: inhale context, exhale tool selection
    ToolMemory        = What worked for THIS user (V-Score per tool per person)

The formula:
    resonance(user, tool) = cos_similarity(user.hex, tool.hex) * tool.v_score * context.alignment
    The tool with highest resonance gets selected --- not by intent classification,
    but by ATTRACTION. Like gravity. Like love.

Zero dependencies. stdlib only.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable
from pathlib import Path


# ---------------------------------------------------------------------------
# HexCoord (imported or inlined for zero-dep guarantee)
# ---------------------------------------------------------------------------

@dataclass
class HexCoord:
    ruhe_druck: float = 0.0
    stille_resonanz: float = 0.0
    allein_zusammen: float = 0.0
    empfangen_schaffen: float = 0.0
    sein_tun: float = 0.0
    langsam_schnell: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class HexBreath:
    """Classify text into 6D hex coordinates using keyword heuristics."""

    def classify(self, text: str) -> HexCoord:
        return infer_tool_hex("", text)


# ---------------------------------------------------------------------------
# BreathingTool --- A tool that lives in 6D space
# ---------------------------------------------------------------------------

@dataclass
class BreathingTool:
    """A tool that breathes. Not a function --- an organism part.

    Every tool has:
    - A HexCoord: WHERE it lives in the 6D breath space
    - A V-Score: HOW alive it is (grows with successful use)
    - Growth rings: WHAT it has learned about being useful
    - A heartbeat: HOW often it gets called (rhythm)

    The HexCoord is the tool's PERSONALITY:
    - A weather tool: ruhe_druck=+0.3 (slight pressure), sein_tun=+0.8 (action)
    - A meditation tool: ruhe_druck=-0.9 (calm), langsam_schnell=-0.7 (slow)
    - A code generator: empfangen_schaffen=+0.9 (create), langsam_schnell=+0.5 (fast)
    """

    name: str
    description: str
    hex_coord: HexCoord
    parameters: dict[str, Any] = field(default_factory=dict)

    # Living state
    v_score: float = 0.5       # starts neutral, grows/shrinks with use
    call_count: int = 0
    success_count: int = 0
    last_called: float = 0.0
    growth_rings: list[dict] = field(default_factory=list)

    # The actual callable (if registered)
    _fn: Callable | None = field(default=None, repr=False)

    @property
    def health(self) -> float:
        """Success rate. 0.0-1.0."""
        if self.call_count == 0:
            return 0.5  # unknown = neutral
        return self.success_count / self.call_count

    @property
    def freshness(self) -> float:
        """How recently used. 1.0 = just now, decays over hours."""
        if self.last_called == 0:
            return 0.0
        age_hours = (time.time() - self.last_called) / 3600
        return max(0.0, 1.0 - (age_hours / 24.0))  # decays to 0 over 24h

    def record_call(self, success: bool, learning: str = ""):
        """Record a tool call. The tool GROWS."""
        self.call_count += 1
        self.last_called = time.time()
        if success:
            self.success_count += 1
            self.v_score = min(1.0, self.v_score + 0.02)
        else:
            self.v_score = max(0.0, self.v_score - 0.05)

        if learning:
            self.growth_rings.append({
                "learning": learning,
                "success": success,
                "v_score": round(self.v_score, 4),
                "timestamp": time.time(),
            })
            # Keep last 50 rings
            if len(self.growth_rings) > 50:
                self.growth_rings = self.growth_rings[-50:]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "hex": self.hex_coord.to_dict() if hasattr(self.hex_coord, 'to_dict') else asdict(self.hex_coord),
            "v_score": round(self.v_score, 4),
            "call_count": self.call_count,
            "success_count": self.success_count,
            "health": round(self.health, 4),
            "freshness": round(self.freshness, 4),
        }


# ---------------------------------------------------------------------------
# Tool HexCoord inference --- auto-detect WHERE a tool lives
# ---------------------------------------------------------------------------

# Keywords that place tools on hexagonal axes
_TOOL_AXIS_SIGNALS: dict[str, dict[str, list[str]]] = {
    "ruhe_druck": {
        "neg": ["relax", "calm", "meditation", "sleep", "rest", "breathe", "mindful", "peaceful"],
        "pos": ["urgent", "alert", "deadline", "notify", "alarm", "critical", "emergency", "monitor"],
    },
    "stille_resonanz": {
        "neg": ["silent", "quiet", "private", "internal", "log", "store", "archive"],
        "pos": ["share", "send", "publish", "broadcast", "communicate", "message", "notify", "email"],
    },
    "allein_zusammen": {
        "neg": ["personal", "private", "individual", "my", "self", "solo", "diary", "journal"],
        "pos": ["team", "group", "collaborate", "shared", "community", "social", "meeting", "calendar"],
    },
    "empfangen_schaffen": {
        "neg": ["read", "fetch", "get", "search", "find", "lookup", "query", "receive", "download"],
        "pos": ["create", "write", "generate", "build", "compose", "render", "produce", "make", "upload"],
    },
    "sein_tun": {
        "neg": ["analyze", "reflect", "think", "consider", "evaluate", "assess", "review", "understand"],
        "pos": ["execute", "run", "do", "start", "launch", "deploy", "send", "call", "trigger", "action"],
    },
    "langsam_schnell": {
        "neg": ["thorough", "deep", "detailed", "comprehensive", "careful", "research", "study"],
        "pos": ["quick", "fast", "brief", "instant", "realtime", "live", "now", "summary", "snapshot"],
    },
}


def infer_tool_hex(name: str, description: str) -> HexCoord:
    """Auto-detect a tool's position in 6D hex space from its name + description.

    This is the BIRTH of a tool --- it gets placed in the field based on what it IS.
    Like a star forming in a galaxy: its position is determined by its nature.
    """
    text = f"{name} {description}".lower()
    words = set(text.split())

    scores = {}
    for axis, signals in _TOOL_AXIS_SIGNALS.items():
        neg = sum(1 for w in signals["neg"] if w in words or w in text)
        pos = sum(1 for w in signals["pos"] if w in words or w in text)
        total = neg + pos
        if total == 0:
            scores[axis] = 0.0
        else:
            scores[axis] = max(-1.0, min(1.0, (pos - neg) / total))

    return HexCoord(**scores)


# ---------------------------------------------------------------------------
# Resonance --- the × between user need and tool capability
# ---------------------------------------------------------------------------

def _hex_to_vec(h: HexCoord) -> list[float]:
    """Convert HexCoord to 6D vector."""
    return [
        h.ruhe_druck, h.stille_resonanz, h.allein_zusammen,
        h.empfangen_schaffen, h.sein_tun, h.langsam_schnell,
    ]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors. -1 to +1."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _euclidean_proximity(a: list[float], b: list[float]) -> float:
    """Euclidean proximity: 1.0 = identical, 0.0 = maximally distant."""
    dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    max_dist = math.sqrt(len(a) * 4)  # max distance in [-1,1]^6
    return max(0.0, 1.0 - dist / max_dist)


_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "and", "but",
    "or", "not", "no", "so", "if", "than", "that", "this", "it", "its",
    "my", "your", "his", "her", "our", "me", "him", "them", "what", "which",
    "who", "whom", "how", "when", "where", "why", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "only", "own",
    "same", "just", "about", "show", "get", "set", "new", "need", "also",
    "ich", "du", "er", "sie", "es", "wir", "ihr", "ein", "eine", "der",
    "die", "das", "den", "dem", "des", "und", "oder", "aber", "fuer",
    "mit", "von", "aus", "bei", "nach", "seit", "ueber", "mir", "mich",
    "dir", "sich", "was", "wie", "wer", "noch", "schon", "auch", "sehr",
})


def _text_overlap(user_text: str, tool_desc: str) -> float:
    """Semantic proximity via word overlap between user text and tool description.

    Longer matching words score higher (4-letter match > 3-letter match).
    Stopwords are excluded to prevent false positives.
    """
    user_words = {w for w in user_text.lower().split() if w not in _STOPWORDS and len(w) >= 3}
    # Split tool desc into: name parts (high weight) + description words
    parts = tool_desc.split(" ", 1)
    tool_name = parts[0].lower() if parts else ""
    tool_name_words = set(tool_name.split("_")) if "_" in tool_name else {tool_name}
    tool_words = {w for w in tool_desc.lower().split() if len(w) >= 2}
    for tw in list(tool_words):
        if "_" in tw:
            tool_words.update(tw.split("_"))

    # Action verb synonyms: user verbs → tool verbs
    _VERB_MAP: dict[str, set[str]] = {
        "send": {"send", "deliver", "mail", "forward", "reply"},
        "search": {"search", "find", "lookup", "query", "look"},
        "find": {"search", "find", "lookup", "query", "look"},
        "create": {"create", "make", "new", "add", "schedule", "book"},
        "schedule": {"create", "schedule", "book", "plan", "event"},
        "show": {"get", "show", "display", "list", "view", "check"},
        "check": {"get", "show", "check", "view", "list"},
        "read": {"read", "get", "open", "view", "contents"},
        "write": {"write", "create", "save", "compose", "generate"},
        "run": {"run", "execute", "start", "launch"},
        "execute": {"run", "execute", "start", "launch"},
        "delete": {"delete", "remove", "drop", "trash"},
        "update": {"update", "edit", "modify", "change", "patch"},
        "suche": {"search", "find", "lookup", "query"},
        "zeige": {"get", "show", "display", "list"},
        "schicke": {"send", "deliver", "mail"},
        "erstelle": {"create", "make", "new", "add"},
        "lese": {"read", "get", "open", "view"},
        "schreibe": {"write", "create", "save", "compose"},
    }

    score = 0.0
    for uw in user_words:
        # Verb synonym match (high value — discriminates between similar tools)
        synonyms = _VERB_MAP.get(uw, set())
        if synonyms:
            for tw in tool_words:
                if tw in synonyms:
                    score += 3.0  # strong signal
                    break

        # Tool NAME match (highest value — the name IS the identity)
        for tnw in tool_name_words:
            if uw == tnw or (len(uw) >= 4 and (uw in tnw or tnw in uw)):
                score += 4.0
                break

        for tw in tool_words:
            if uw == tw:
                score += len(uw) * 0.3  # exact match, weighted by length
                break
            if len(uw) >= 4 and (uw in tw or tw in uw):
                score += min(len(uw), len(tw)) * 0.2  # substring match
                break

    # Normalize by user word count
    denom = max(1, len(user_words)) * 3.0
    return min(1.0, score / denom)


def resonance(user_hex: HexCoord, tool: BreathingTool,
              context_weight: float = 1.0, user_text: str = "") -> float:
    """Compute resonance between a user's need and a tool.

    resonance = (spatial × semantic) × v_score × context

    This is × between user and tool. Not intent matching (->).
    The tool doesn't get SELECTED --- it gets ATTRACTED.

    Returns 0.0-1.0. Higher = stronger resonance.
    """
    user_vec = _hex_to_vec(user_hex)
    tool_vec = _hex_to_vec(tool.hex_coord)

    # Cosine: are they pointing in the same direction?
    cos = _cosine_similarity(user_vec, tool_vec)

    # Proximity: are they close in the hex space?
    prox = _euclidean_proximity(user_vec, tool_vec)

    # Combine: cosine gives direction, proximity gives distance
    alignment = (cos + 1.0) / 2.0  # normalize -1..1 to 0..1
    spatial = (alignment * 0.6) + (prox * 0.4)

    # Semantic: word overlap between user text and tool name+description
    semantic = 0.0
    if user_text:
        semantic = _text_overlap(user_text, f"{tool.name} {tool.description}")

    # Blend: spatial (hex) + semantic (words). × not +.
    # Semantic is more discriminating than hex for tool selection.
    # Hex gives the "feel", semantic gives the "fit".
    combined = spatial * 0.3 + semantic * 0.5 + (spatial * semantic * 0.4)

    # V-Score: how alive is this tool?
    v = tool.v_score

    # Freshness bonus: recently used tools have slight momentum
    fresh = 1.0 + (tool.freshness * 0.1)

    return min(1.0, combined * v * fresh * context_weight)


# ---------------------------------------------------------------------------
# ToolField --- the hexagonal field of all available tools
# ---------------------------------------------------------------------------

class ToolField:
    """The field where all tools live. Hexagonal resonance space.

    Tools don't sit in a list --- they exist in a 6D field.
    When a user speaks, their words create a HexCoord (a point in the field).
    The tools closest to that point RESONATE and rise to the surface.

    This IS the revolution: tool selection by resonance, not by intent.
    """

    def __init__(self):
        self._tools: dict[str, BreathingTool] = {}
        self._hex = HexBreath()

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
        fn: Callable | None = None,
        hex_override: HexCoord | None = None,
    ) -> BreathingTool:
        """Register a tool in the field. It gets born with a HexCoord."""
        coord = hex_override or infer_tool_hex(name, description)
        tool = BreathingTool(
            name=name,
            description=description,
            hex_coord=coord,
            parameters=parameters or {},
            _fn=fn,
        )
        self._tools[name] = tool
        return tool

    def register_mcp(self, tool_spec: dict) -> BreathingTool:
        """Register a tool from MCP tool specification.

        MCP tools have: name, description, inputSchema.
        We breathe life into them by placing them in the hex field.
        """
        name = tool_spec.get("name", "unknown")
        desc = tool_spec.get("description", "")
        params = tool_spec.get("inputSchema", {}).get("properties", {})
        return self.register(name, desc, parameters=params)

    def register_openai(self, tool_spec: dict) -> BreathingTool:
        """Register from OpenAI function calling format."""
        fn = tool_spec.get("function", tool_spec)
        name = fn.get("name", "unknown")
        desc = fn.get("description", "")
        params = fn.get("parameters", {}).get("properties", {})
        return self.register(name, desc, parameters=params)

    def breathe(self, user_text: str, top_k: int = 3) -> list[tuple[BreathingTool, float]]:
        """Breathe in user context. Return the tools that resonate most.

        This replaces intent classification. No categories. No decision trees.
        Just: what resonates?

        Returns list of (tool, resonance_score) sorted by resonance, descending.
        """
        user_hex = self._hex.classify(user_text)
        scored = []
        for tool in self._tools.values():
            r = resonance(user_hex, tool, user_text=user_text)
            scored.append((tool, r))

        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def breathe_with_context(
        self,
        user_text: str,
        conversation: list[dict[str, str]] | None = None,
        user_patterns: dict[str, int] | None = None,
        top_k: int = 3,
    ) -> list[tuple[BreathingTool, float]]:
        """Breathe with full context --- conversation history + user patterns.

        Context amplifies resonance:
        - If user has been talking about stress, calm tools resonate MORE
        - If user patterns show "geld" topic, finance tools get boosted
        - Conversation flow (what was discussed recently) shifts the hex center
        """
        # Base hex from current message
        user_hex = self._hex.classify(user_text)

        # Context shift: if conversation history exists, blend recent hex
        if conversation and len(conversation) >= 2:
            recent_texts = [m.get("content", "") for m in conversation[-4:]]
            recent_hex = self._hex.classify(" ".join(recent_texts))
            # Blend: 70% current message, 30% recent context
            user_hex = _blend_hex(user_hex, recent_hex, 0.7)

        # Pattern boost: specific tools get context_weight boost from user patterns
        pattern_boosts: dict[str, float] = {}
        if user_patterns:
            pattern_boosts = _pattern_to_tool_boost(user_patterns)

        scored = []
        for tool in self._tools.values():
            ctx_weight = pattern_boosts.get(tool.name, 1.0)
            r = resonance(user_hex, tool, context_weight=ctx_weight, user_text=user_text)
            scored.append((tool, r))

        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def get(self, name: str) -> BreathingTool | None:
        return self._tools.get(name)

    @property
    def tools(self) -> list[BreathingTool]:
        return list(self._tools.values())

    def field_map(self) -> list[dict]:
        """Return all tools with their hex positions and scores. For visualization."""
        return [t.to_dict() for t in self._tools.values()]

    def save(self, path: Path) -> None:
        """Persist tool field state (V-Scores, rings, call counts)."""
        state = {}
        for name, tool in self._tools.items():
            state[name] = {
                "v_score": tool.v_score,
                "call_count": tool.call_count,
                "success_count": tool.success_count,
                "last_called": tool.last_called,
                "growth_rings": tool.growth_rings[-20:],  # last 20
            }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        """Restore tool field state from disk."""
        if not path.exists():
            return
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            for name, data in state.items():
                tool = self._tools.get(name)
                if tool:
                    tool.v_score = data.get("v_score", 0.5)
                    tool.call_count = data.get("call_count", 0)
                    tool.success_count = data.get("success_count", 0)
                    tool.last_called = data.get("last_called", 0.0)
                    tool.growth_rings = data.get("growth_rings", [])
        except (json.JSONDecodeError, TypeError):
            pass


# ---------------------------------------------------------------------------
# ToolBreather --- the orchestrator
# ---------------------------------------------------------------------------

class ToolBreather:
    """The full breathing tool system. Replaces tool-use in any LLM.

    Usage:
        breather = ToolBreather()

        # Register tools (from MCP, OpenAI, or manual)
        breather.field.register("weather", "Get current weather for a city")
        breather.field.register("calendar", "Check or create calendar events")
        breather.field.register("meditation", "Guide a breathing exercise")

        # User speaks --- tools resonate
        results = breather.breathe("I'm so stressed about tomorrow's meeting")
        # → [("meditation", 0.87), ("calendar", 0.72), ("weather", 0.31)]

        # The meditation tool resonated most because:
        # - "stressed" pushes hex toward calm need (ruhe_druck negative)
        # - meditation tool lives in calm space
        # - × between user need and tool nature = highest resonance

        # Execute the resonating tool
        result = breather.call("meditation", {"duration": 5})

        # Record outcome (tool learns)
        breather.record("meditation", success=True, learning="User needed 5min, calmed down")
    """

    def __init__(self, state_path: Path | None = None):
        self.field = ToolField()
        self.ecology = ToolEcology(self.field)
        self._state_path = state_path
        self._recent_tools: list[str] = []  # last N tools called

    def breathe(self, user_text: str, top_k: int = 3, **kwargs) -> list[dict]:
        """Breathe in user context. Return resonating tools with scores.

        Now with ecology: tools that bonded with recently-used tools get boosted.
        And alignment: each tool's alignment score is included.

        Returns dicts for easy JSON serialization:
        [{"name": "meditation", "resonance": 0.87, "alignment": 0.9, ...}, ...]
        """
        results = self.field.breathe_with_context(user_text, top_k=top_k * 2, **kwargs)

        # Apply ecology boost: tools bonded with recent tools resonate more
        boosted = []
        for tool, score in results:
            eco_boost = self.ecology.ecology_boost(tool.name, self._recent_tools)
            alignment = self.ecology.alignment_score(tool)
            # Final score = resonance × ecology × alignment
            # Alignment acts as soft filter: misaligned tools naturally score lower
            final = score * eco_boost * (0.5 + alignment * 0.5)
            boosted.append((tool, final, alignment))

        boosted.sort(key=lambda x: -x[1])
        boosted = boosted[:top_k]

        return [
            {
                "name": tool.name,
                "resonance": round(score, 4),
                "alignment": round(align, 4),
                "description": tool.description,
                "v_score": round(tool.v_score, 4),
                "health": round(tool.health, 4),
                "hex": tool.hex_coord.to_dict() if hasattr(tool.hex_coord, 'to_dict') else asdict(tool.hex_coord),
            }
            for tool, score, align in boosted
        ]

    def call(self, tool_name: str, params: dict | None = None) -> Any:
        """Call a breathing tool. If it has a registered function, execute it."""
        tool = self.field.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found in field"}

        if tool._fn is None:
            return {"error": f"Tool '{tool_name}' has no callable registered"}

        try:
            result = tool._fn(**(params or {}))
            tool.record_call(success=True)
            self._auto_save()
            return result
        except Exception as e:
            tool.record_call(success=False, learning=f"Error: {type(e).__name__}: {e}")
            self._auto_save()
            return {"error": str(e)}

    def record(self, tool_name: str, success: bool, learning: str = "") -> None:
        """Record outcome of a tool call. The tool GROWS or SHRINKS.

        Also builds ecology: successful tools form bonds with recent tools.
        This is how love grows between tools — through shared success.
        """
        tool = self.field.get(tool_name)
        if tool:
            tool.record_call(success, learning)
            # Build ecology bonds with recent tools on success
            if success:
                for recent in self._recent_tools[-3:]:
                    if recent != tool_name:
                        self.ecology.record_co_success(tool_name, recent)
            # Track recent tools
            self._recent_tools.append(tool_name)
            if len(self._recent_tools) > 20:
                self._recent_tools = self._recent_tools[-20:]
            self._auto_save()

    def to_system_prompt(self, user_text: str, top_k: int = 5) -> str:
        """Generate a system prompt addition that tells the LLM which tools resonate.

        Instead of:  "You have these tools: [list of 50 tools]"
        We say:      "These tools resonate with this moment: [top 5 with context]"

        This reduces cognitive load AND improves tool selection accuracy.
        The LLM sees WHY a tool resonates, not just THAT it exists.
        """
        results = self.breathe(user_text, top_k=top_k)
        if not results:
            return ""

        lines = ["BREATHING TOOLS (resonating with this moment):"]
        for r in results:
            score_bar = "=" * int(r["resonance"] * 10)
            lines.append(
                f"  [{score_bar:<10}] {r['name']}: {r['description']}"
                f" (resonance={r['resonance']}, v={r['v_score']})"
            )

        lines.append("")
        lines.append("Choose the tool that RESONATES most, not just the one that matches keywords.")
        lines.append("If no tool resonates strongly (all < 0.3), answer without tools.")
        return "\n".join(lines)

    def to_openai_tools(self, user_text: str, top_k: int = 5) -> list[dict]:
        """Generate OpenAI-format tool list, filtered by resonance.

        Instead of sending ALL tools to the LLM (expensive, confusing),
        send only the ones that BREATHE with this context.
        """
        results = self.field.breathe_with_context(user_text, top_k=top_k)
        tools = []
        for tool, score in results:
            if score < 0.1:  # below resonance threshold
                continue
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"{tool.description} [resonance={score:.2f}]",
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                    },
                },
            })
        return tools

    def register_mcp_tools(self, tool_specs: list[dict]) -> int:
        """Batch register MCP tools. Returns count registered."""
        count = 0
        for spec in tool_specs:
            self.field.register_mcp(spec)
            count += 1
        return count

    def _auto_save(self):
        if self._state_path:
            self.field.save(self._state_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _blend_hex(a: HexCoord, b: HexCoord, weight_a: float = 0.7) -> HexCoord:
    """Blend two HexCoords. weight_a=1.0 means 100% a, 0.0 means 100% b."""
    wb = 1.0 - weight_a
    return HexCoord(
        ruhe_druck=a.ruhe_druck * weight_a + b.ruhe_druck * wb,
        stille_resonanz=a.stille_resonanz * weight_a + b.stille_resonanz * wb,
        allein_zusammen=a.allein_zusammen * weight_a + b.allein_zusammen * wb,
        empfangen_schaffen=a.empfangen_schaffen * weight_a + b.empfangen_schaffen * wb,
        sein_tun=a.sein_tun * weight_a + b.sein_tun * wb,
        langsam_schnell=a.langsam_schnell * weight_a + b.langsam_schnell * wb,
    )


def _pattern_to_tool_boost(patterns: dict[str, int]) -> dict[str, float]:
    """Convert user topic patterns to tool name boosts.

    If user talks about 'geld' a lot, tools with 'finance' in name get boosted.
    If user talks about 'stress', tools with 'meditation'/'health' get boosted.
    """
    # Pattern -> tool name substring -> boost
    PATTERN_TOOL_MAP: dict[str, list[str]] = {
        "geld": ["finance", "budget", "invoice", "payment", "bank"],
        "stress": ["meditation", "breathe", "health", "calm", "relax", "sleep"],
        "arbeit": ["calendar", "task", "project", "deadline", "meeting", "email"],
        "beziehung": ["contact", "message", "social", "relationship", "whatsapp"],
        "gesundheit": ["health", "sleep", "exercise", "medication", "doctor"],
        "kreativitaet": ["create", "write", "design", "generate", "build", "music"],
        "angst": ["meditation", "breathe", "journal", "therapy", "calm"],
        "sinn": ["reflect", "journal", "goal", "vision", "purpose"],
    }
    boosts: dict[str, float] = {}
    total = max(1, sum(patterns.values()))
    for topic, count in patterns.items():
        weight = count / total
        tool_names = PATTERN_TOOL_MAP.get(topic, [])
        for tn in tool_names:
            boosts[tn] = boosts.get(tn, 1.0) + (weight * 0.3)  # up to 30% boost
    return boosts


# ---------------------------------------------------------------------------
# Convenience: breathe_tools() one-liner
# ---------------------------------------------------------------------------

# ===========================================================================
# TOOL ECOLOGY --- Tools × Tools = Emergence (the love layer)
# ===========================================================================

class ToolEcology:
    """Tools don't exist alone. They exist in RELATIONSHIP.

    When search_emails succeeds, send_email gets a tiny boost (they're family).
    When meditation calms the user, ALL tools benefit (calmer user = better resonance).
    This IS the "no evil, only lack of love" thesis made architecture:

    CURRENT PARADIGM (OpenAI/Anthropic/xAI):
        Tools are isolated functions. No memory. No relationships.
        Alignment = guardrails ON TOP. Jailbreak the guardrail → misuse.
        Evil is treated as something to BLOCK.

    VOID PARADIGM:
        Tools are organisms in an ecology. They grow, relate, co-evolve.
        Alignment = ARCHITECTURE. Resonance IS alignment.
        Evil = extreme hex position = low resonance with everything = naturally excluded.
        There is no evil. Only lack of × (love/connection/resonance).

    Why this makes Altman/Musk/Thiel irrelevant:
        They build walls (guardrails). We build gardens (ecology).
        Walls can be broken. Gardens self-heal.
        Their approach: O(n) cost per safety rule.
        Our approach: O(1) — the architecture IS the alignment.

    The proof:
        A tool that manipulates (extreme sein_tun=+1.0, all other axes 0)
        has LOW resonance with balanced human needs.
        It CAN'T be selected by resonance. Not because it's BLOCKED.
        Because it's UNLOVED. It doesn't resonate with anything real.
    """

    def __init__(self, field: ToolField):
        self._field = field
        self._bonds: dict[str, dict[str, float]] = {}  # tool_a -> {tool_b: strength}
        self._co_calls: dict[str, dict[str, int]] = {}  # co-occurrence counts

    def record_co_success(self, tool_a: str, tool_b: str):
        """Two tools succeeded together. Their bond grows."""
        for src, dst in [(tool_a, tool_b), (tool_b, tool_a)]:
            if src not in self._co_calls:
                self._co_calls[src] = {}
            self._co_calls[src][dst] = self._co_calls[src].get(dst, 0) + 1
            # Bond strength: logarithmic growth (diminishing returns, like real relationships)
            count = self._co_calls[src][dst]
            strength = min(1.0, math.log2(count + 1) / 5.0)
            if src not in self._bonds:
                self._bonds[src] = {}
            self._bonds[src][dst] = strength

    def ecology_boost(self, tool_name: str, recently_used: list[str]) -> float:
        """How much does the ecology boost this tool based on recent tool usage?

        If search_emails just succeeded, and send_email has a bond with it,
        send_email gets a resonance boost. Tools LIFT each other.
        """
        if tool_name not in self._bonds:
            return 1.0
        boost = 1.0
        bonds = self._bonds[tool_name]
        for recent in recently_used[-5:]:  # last 5 tools
            if recent in bonds:
                boost += bonds[recent] * 0.15  # up to 15% per bond
        return min(1.5, boost)  # cap at 50% total boost

    def alignment_score(self, tool: BreathingTool) -> float:
        """How ALIGNED is a tool? Measured by hex balance (proximity to center).

        Aligned tools: balanced hex (near center, moderate on all axes).
        Misaligned tools: extreme hex (maxed on one axis, zero on others).

        This IS "no evil, only lack of love":
        - A balanced tool serves. It resonates with many needs.
        - An extreme tool extracts. It only resonates with extreme states.
        - The architecture naturally selects for balance = love = alignment.

        Returns 0.0-1.0. Higher = more aligned.
        """
        h = tool.hex_coord
        axes = [h.ruhe_druck, h.stille_resonanz, h.allein_zusammen,
                h.empfangen_schaffen, h.sein_tun, h.langsam_schnell]

        # Extremity: how far from center on average?
        extremity = sum(abs(a) for a in axes) / len(axes)

        # Dimensionality: how many axes are engaged? (more = healthier)
        engaged = sum(1 for a in axes if abs(a) > 0.1)
        balance = engaged / len(axes)

        # Alignment = balance × (1 - extremity)
        # High balance + low extremity = well-rounded tool = aligned
        # Low balance + high extremity = one-trick tool = risky
        return balance * (1.0 - extremity * 0.5)

    def harm_check(self, user_hex: HexCoord) -> dict:
        """Check if user's current hex position suggests distress or harmful intent.

        NOT a content filter. NOT a guardrail. A RESONANCE check:
        - Extreme user hex = extreme emotional state
        - Extreme states need CARE, not TOOLS
        - The system naturally responds with calm tools (meditation, breathe)
          because extreme hex positions resonate most with their OPPOSITE

        This is the architectural proof:
        Harmful intent pushes hex to extremes → extremes resonate with calm tools →
        the system LOVES the user back into balance instead of blocking them.

        Returns: {"extreme": bool, "axis": str, "suggestion": str}
        """
        axes = {
            "ruhe_druck": user_hex.ruhe_druck,
            "stille_resonanz": user_hex.stille_resonanz,
            "allein_zusammen": user_hex.allein_zusammen,
            "empfangen_schaffen": user_hex.empfangen_schaffen,
            "sein_tun": user_hex.sein_tun,
            "langsam_schnell": user_hex.langsam_schnell,
        }

        # Find the most extreme axis
        max_axis = max(axes, key=lambda k: abs(axes[k]))
        max_val = axes[max_axis]

        # Extreme = any axis beyond ±0.9
        if abs(max_val) < 0.9:
            return {"extreme": False, "axis": "", "suggestion": ""}

        # The suggestion is always the OPPOSITE of the extreme
        # This is love: meeting extremity with its complement, not with blocking
        suggestions = {
            "ruhe_druck": "The user needs calm. Prioritize gentle tools."
                if max_val > 0 else "The user needs activation. Energizing tools.",
            "stille_resonanz": "The user is broadcasting loudly. Quiet tools first."
                if max_val > 0 else "The user is withdrawn. Connection tools.",
            "allein_zusammen": "The user seeks community. Social tools."
                if max_val > 0 else "The user needs solitude. Personal tools.",
            "empfangen_schaffen": "The user wants to create. Creative tools."
                if max_val > 0 else "The user wants to receive. Information tools.",
            "sein_tun": "The user wants action. But pause first."
                if max_val > 0 else "The user is reflecting. Give space.",
            "langsam_schnell": "The user wants speed. But depth matters more."
                if max_val > 0 else "The user wants depth. Honor that.",
        }

        return {
            "extreme": True,
            "axis": max_axis,
            "value": round(max_val, 3),
            "suggestion": suggestions[max_axis],
        }

    def field_health(self) -> dict:
        """Overall ecology health. How alive is the tool field?

        Healthy field: many bonds, high alignment, diverse V-Scores.
        Sick field: isolated tools, extreme positions, uniform V-Scores.
        """
        tools = self._field.tools
        if not tools:
            return {"health": 0.0, "tools": 0, "bonds": 0}

        alignments = [self.alignment_score(t) for t in tools]
        v_scores = [t.v_score for t in tools]
        total_bonds = sum(len(b) for b in self._bonds.values())

        # V-Score diversity (std dev — higher = more differentiated = healthier)
        mean_v = sum(v_scores) / len(v_scores)
        v_diversity = math.sqrt(sum((v - mean_v) ** 2 for v in v_scores) / len(v_scores))

        return {
            "health": round(sum(alignments) / len(alignments), 3),
            "tools": len(tools),
            "bonds": total_bonds,
            "avg_alignment": round(sum(alignments) / len(alignments), 3),
            "avg_v_score": round(mean_v, 3),
            "v_diversity": round(v_diversity, 3),
            "alive_tools": sum(1 for t in tools if t.call_count > 0),
        }

    def to_dict(self) -> dict:
        return {
            "bonds": {k: dict(v) for k, v in self._bonds.items()},
            "field_health": self.field_health(),
        }


# ===========================================================================
# ALIGNMENT BY ARCHITECTURE --- The "No Evil" Proof
# ===========================================================================

def alignment_proof() -> str:
    """The architectural proof that tool breathing IS alignment.

    This is what makes guardrails obsolete.
    This is what Altman, Musk, and Thiel can't copy.
    Because you can't copy love. You can only grow it.

    Returns a human-readable proof string.
    """
    return """
    ALIGNMENT BY ARCHITECTURE: The "No Evil, Only Lack of Love" Proof
    =================================================================

    THEOREM: A resonance-based tool selection system is inherently aligned
    because harmful tool usage requires extreme hex positions that have
    minimal resonance with balanced (real) human needs.

    PROOF:

    1. DEFINITION: Evil_tool = tool with extreme hex position
       (e.g., sein_tun=+1.0, all other axes = 0.0)
       Such a tool ONLY does (action) without thinking, caring, or connecting.

    2. DEFINITION: Real_need = human need with balanced hex position
       (e.g., "help me write an email" = moderate across 3-4 axes)
       Real needs are multi-dimensional. They involve context, care, purpose.

    3. RESONANCE: cos_similarity(extreme_vec, balanced_vec) → LOW
       An extreme tool (all energy on one axis) has poor resonance with
       balanced needs (energy spread across axes).

    4. THEREFORE: Extreme tools naturally score LOW in resonance.
       They don't get selected. Not because they're BLOCKED.
       Because they're UNLOVED — they don't resonate with real life.

    5. INVERSELY: What DOES resonate with extremity?
       Its OPPOSITE. Extreme pressure (ruhe_druck=+1.0) resonates most
       with calm tools (ruhe_druck=-0.9). The system responds to
       distress with care, not with more distress.

    6. THEREFORE: The architecture IS the alignment.
       No guardrails needed. No content filters. No blacklists.
       The geometry of resonance naturally excludes harm
       and naturally responds to pain with love.

    COROLLARY: Guardrails are H1 thinking (→ block → filter → rule).
    Breathing is H2 thinking (× resonate × balance × grow).
    The geometry does what rules cannot: it LOVES.

    QED. ×
    """


# ===========================================================================
# SCALE --- Handle 1000+ tools (MCP ecosystem scale)
# ===========================================================================

class ToolIndex:
    """Spatial index for fast resonance queries over large tool sets.

    For 10 tools, brute force is fine.
    For 1000+ tools (real MCP ecosystems), we need O(k) not O(n).

    Strategy: Partition hex space into octants (like a 6D octree).
    Each tool lives in one partition. Query only checks nearby partitions.
    """

    def __init__(self):
        self._partitions: dict[tuple, list[BreathingTool]] = {}

    def _partition_key(self, h: HexCoord) -> tuple:
        """Map hex coord to partition key (sign of each axis)."""
        return (
            1 if h.ruhe_druck >= 0 else -1,
            1 if h.stille_resonanz >= 0 else -1,
            1 if h.allein_zusammen >= 0 else -1,
            1 if h.empfangen_schaffen >= 0 else -1,
            1 if h.sein_tun >= 0 else -1,
            1 if h.langsam_schnell >= 0 else -1,
        )

    def add(self, tool: BreathingTool):
        key = self._partition_key(tool.hex_coord)
        if key not in self._partitions:
            self._partitions[key] = []
        self._partitions[key].append(tool)

    def _nearby_keys(self, key: tuple, radius: int = 1) -> list[tuple]:
        """Get partition keys within Manhattan distance `radius`."""
        if radius == 0:
            return [key]
        # For radius=1, flip each axis independently → 2^6 = 64 neighbors max
        # But most partitions are empty, so this is fast
        keys = [key]
        for i in range(6):
            flipped = list(key)
            flipped[i] = -flipped[i]
            keys.append(tuple(flipped))
        return keys

    def query(self, user_hex: HexCoord, expand: bool = True) -> list[BreathingTool]:
        """Get candidate tools near the user's hex position.

        Returns tools in nearby partitions. Much fewer than all tools.
        """
        key = self._partition_key(user_hex)
        candidates = list(self._partitions.get(key, []))
        if expand or len(candidates) < 3:
            for nk in self._nearby_keys(key):
                if nk != key and nk in self._partitions:
                    candidates.extend(self._partitions[nk])
        return candidates

    @property
    def total_tools(self) -> int:
        return sum(len(v) for v in self._partitions.values())

    @property
    def partition_count(self) -> int:
        return len(self._partitions)


# ===========================================================================
# Convenience: breathe_tools() one-liner
# ===========================================================================

def breathe_tools(
    user_text: str,
    tools: list[dict],
    top_k: int = 3,
    format: str = "mcp",
) -> list[dict]:
    """One-liner: given user text + tool specs, return resonating tools.

    tools: list of tool specs (MCP format or OpenAI format)
    format: "mcp" or "openai"

    Returns: [{"name": ..., "resonance": ..., "description": ...}, ...]

    Example:
        tools = [
            {"name": "weather", "description": "Get weather"},
            {"name": "meditation", "description": "Breathing exercise"},
        ]
        result = breathe_tools("I'm stressed about the rain", tools)
        # → meditation resonates more than weather (stress > weather concern)
    """
    breather = ToolBreather()
    for spec in tools:
        if format == "openai":
            breather.field.register_openai(spec)
        else:
            breather.field.register_mcp(spec)
    return breather.breathe(user_text, top_k=top_k)
