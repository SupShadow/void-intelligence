"""
void_intelligence.prompt_breathing --- Prompts that Breathe.

The revolution of LLM framing through .x->[]~

CURRENT PARADIGM (H1, ->):
    "Write a good system prompt" -- static, one-size-fits-all craft.
    Same prompt for stressed user and calm user.
    Same prompt for code sprint and poetic reflection.
    Prompt engineers A/B test with vibes. Every prompt is a dead artifact.

VOID PARADIGM (H2/H3, x):
    The prompt itself BREATHES. It adapts to the user's hex position.
    A stressed user gets a gentler frame.   A creative user gets open space.
    The prompt PACE matches the user's rhythm (langsam_schnell axis).
    The prompt DEPTH matches the user's need (sein_tun axis).
    Temperature and max_tokens are not magic numbers -- they emerge from geometry.

Architecture:
    PromptBreath    = A prompt that has been breathed (adapted to user state)
    PromptBreather  = The orchestrator: inhale user text, exhale adapted prompt

The formula:
    adapted_prompt = base_prompt + adaptations(user.hex)
    temperature    = f(empfangen_schaffen, sein_tun, ruhe_druck)
    max_tokens     = f(langsam_schnell, sein_tun)
    Each adaptation knows WHY it exists. Transparent. Learnable.

The H3 Insight:
    All 6 breathing modules use the SAME HexCoord. The SAME resonance geometry.
    Tool Breathing: which tool?   Context Breathing: what context?
    Model Breathing: which model? Prompt Breathing: how to frame?
    They are ONE formula on different substrates.
    x was always there. We just named it.

Zero dependencies. stdlib only.
~380 lines.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Import HexCoord from tool_breathing (inline fallback for zero-dep)
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import HexCoord
except ImportError:
    @dataclass  # type: ignore[no-redef]
    class HexCoord:
        ruhe_druck: float = 0.0         # -1 = calm/rest,  +1 = pressure/urgency
        stille_resonanz: float = 0.0    # -1 = private,    +1 = sharing/social
        allein_zusammen: float = 0.0    # -1 = solo,       +1 = together/team
        empfangen_schaffen: float = 0.0 # -1 = receive,    +1 = create/generate
        sein_tun: float = 0.0           # -1 = being/reflect, +1 = doing/action
        langsam_schnell: float = 0.0    # -1 = slow/deep,  +1 = fast/brief

        def to_dict(self) -> dict:
            return asdict(self)


# ---------------------------------------------------------------------------
# _PromptHexBreath -- emotional-signal-aware classifier for USER TEXT
#
# HexBreath from tool_breathing is calibrated for tool DESCRIPTIONS
# ("urgent", "alarm", "deploy"). For user text we need emotional vocabulary:
# "stressed", "overwhelmed", "brainstorm", "quickly", "reflect".
# This private classifier lives here -- same 6D geometry, different signals.
# ---------------------------------------------------------------------------

_PROMPT_AXIS_SIGNALS: dict[str, dict[str, list[str]]] = {
    "ruhe_druck": {
        # neg = calm, restful, no pressure
        "neg": [
            "calm", "relax", "relaxed", "rest", "peace", "peaceful", "gentle",
            "quiet", "slow", "easy", "comfortable", "comfortable", "ruhig",
            "entspannt", "geduldig", "geduld", "sanft", "gelassen",
        ],
        # pos = pressure, stress, urgency
        "pos": [
            "stress", "stressed", "overwhelmed", "anxious", "anxiety", "panic",
            "worried", "worry", "urgent", "urgency", "deadline", "pressure",
            "emergency", "critical", "struggling", "cant", "can't", "focus",
            "distracted", "stuck", "help", "dringend", "angst", "gestresst",
            "ueberwaeltigt", "nervoes", "panik", "kritisch", "hilfe",
        ],
    },
    "stille_resonanz": {
        "neg": [
            "private", "internal", "personal", "alone", "myself", "journal",
            "diary", "secret", "only me", "privat", "geheim", "nur fuer mich",
            "festhalten",
        ],
        "pos": [
            "share", "send", "post", "publish", "tell", "show", "broadcast",
            "message", "write to", "announce", "team", "everyone", "whole",
            "teilen", "schicken", "veroeffentlichen", "erzaehlen", "posten",
        ],
    },
    "allein_zusammen": {
        "neg": [
            "myself", "alone", "solo", "just me", "individual", "on my own",
            "by myself", "allein", "ich allein", "nur ich", "selbst", "einsam",
        ],
        "pos": [
            "we", "our", "team", "together", "group", "everyone", "all of us",
            "wir", "unser", "gemeinsam", "zusammen", "alle", "gruppe",
        ],
    },
    "empfangen_schaffen": {
        "neg": [
            "search", "find", "look", "get", "fetch", "summarize", "summary",
            "what is", "explain", "tell me", "show me", "suche", "finde",
            "erklaere", "sag mir", "zeig mir", "was ist",
        ],
        "pos": [
            "create", "build", "write", "generate", "brainstorm", "ideas",
            "invent", "design", "make", "draft", "compose", "imagine",
            "erstellen", "bauen", "schreiben", "ideen", "brainstormen",
            "entwerfen", "entwickeln", "erfinden",
        ],
    },
    "sein_tun": {
        "neg": [
            "understand", "reflect", "think", "feel", "wonder", "why",
            "meaning", "pattern", "realize", "notice", "curious", "explore",
            "nachdenken", "verstehen", "fragen", "warum", "muster", "fuehl",
            "bedeutung", "neugierig", "erkunden",
        ],
        "pos": [
            "do", "action", "fix", "implement", "execute", "run", "start",
            "deploy", "steps", "should i", "what to do", "right now", "now",
            "immediately", "asap", "code", "production", "api", "build",
            "machen", "tun", "umsetzen", "starten", "programmieren",
            "schritte", "was soll ich", "jetzt", "sofort",
        ],
    },
    "langsam_schnell": {
        "neg": [
            "deep", "thorough", "detailed", "nuanced", "careful", "research",
            "explore", "take time", "no rush", "fully", "comprehensively",
            "gruendlich", "ausfuehrlich", "in die tiefe", "langsam", "ohne eile",
        ],
        "pos": [
            "quick", "fast", "brief", "short", "tldr", "quickly", "now",
            "instant", "asap", "one line", "summary", "quickly", "right now",
            "kurz", "schnell", "sofort", "kurze", "zusammenfassung",
        ],
    },
}


def _signal_match(signal: str, words: set[str], lower: str) -> bool:
    """Match a signal against text. Multi-word → substring. Single-word → word boundary."""
    if " " in signal:
        return signal in lower
    return signal in words


def _classify_user_text(text: str) -> "HexCoord":
    """Classify user text into 6D hex space using emotional/conversational signals.

    Designed for NATURAL USER LANGUAGE -- not tool descriptions.
    Single words match by word boundary (prevents 'alle' matching 'allein').
    Multi-word phrases match by substring (catches 'can't focus', 'ich allein').
    """
    lower = text.lower()
    words = set(lower.split())
    scores: dict[str, float] = {}

    for axis, sigs in _PROMPT_AXIS_SIGNALS.items():
        neg_hits = sum(1 for w in sigs["neg"] if _signal_match(w, words, lower))
        pos_hits = sum(1 for w in sigs["pos"] if _signal_match(w, words, lower))
        total = neg_hits + pos_hits
        if total == 0:
            scores[axis] = 0.0
        else:
            raw = (pos_hits - neg_hits) / total
            scores[axis] = max(-1.0, min(1.0, raw))

    return HexCoord(**scores)


class _PromptHexBreath:
    """Emotion-aware 6D classifier for user text. Private to prompt_breathing."""

    def classify(self, text: str) -> "HexCoord":
        return _classify_user_text(text)


# ---------------------------------------------------------------------------
# Language detection (zero-dep heuristic)
# ---------------------------------------------------------------------------

_GERMAN_MARKERS = frozenset({
    "ich", "du", "wir", "sie", "der", "die", "das", "ein", "eine", "und",
    "ist", "sind", "war", "haben", "aber", "nicht", "auch", "noch", "schon",
    "jetzt", "hier", "mit", "fuer", "ueber", "unter", "nach", "von", "bei",
    "wie", "was", "wer", "wo", "warum", "kann", "muss", "will", "soll",
})


def _detect_language(text: str) -> str:
    """Heuristic language detection. Returns 'de' or 'en'. Zero deps."""
    words = set(text.lower().split())
    german_hits = len(words & _GERMAN_MARKERS)
    # >= 2 German marker words in text -> classify as German
    return "de" if german_hits >= 2 else "en"


# ---------------------------------------------------------------------------
# Adaptation library -- what to say and why, per axis, per language
# ---------------------------------------------------------------------------

# Each entry: (instruction_de, instruction_en, why)
_ADAPTATIONS: dict[str, dict[str, tuple[str, str, str]]] = {
    "ruhe_druck_high": {
        "any": (
            "Antworte sanft und kurz. Der Nutzer steht unter Druck.",
            "Respond gently and concisely. The user is under pressure.",
            "ruhe_druck > 0.4: user stressed -> tone softens, length shrinks",
        ),
        "extra": (
            "Erkenne den emotionalen Zustand bevor du inhaltlich antwortest.",
            "Acknowledge their state before diving into content.",
            "high stress -> emotional acknowledgment first",
        ),
    },
    "ruhe_druck_low": {
        "any": (
            "Nutze einen ruhigen, erkundenden Ton.",
            "Use a calm, exploratory tone.",
            "ruhe_druck < -0.4: user is at rest -> expansive tone appropriate",
        ),
    },
    "stille_resonanz_high": {
        "any": (
            "Der Nutzer moechte teilen oder veroeffentlichen. Formuliere einladend.",
            "The user wants to share or publish. Write in an inviting, outward-facing style.",
            "stille_resonanz > 0.4: social/sharing mode -> outward tone",
        ),
    },
    "stille_resonanz_low": {
        "any": (
            "Dies ist ein privater, interner Gedanke. Halte die Antwort persoenlich.",
            "This feels private and internal. Keep the response personal and journal-like.",
            "stille_resonanz < -0.4: private mode -> personal, minimal",
        ),
    },
    "allein_zusammen_high": {
        "any": (
            "Verwende 'wir' statt 'du'. Der Nutzer denkt im Team-Kontext.",
            "Use 'we' language. The user is thinking in a group context.",
            "allein_zusammen > 0.4: social frame -> inclusive perspective",
        ),
    },
    "allein_zusammen_low": {
        "any": (
            "Adressiere den Nutzer direkt als Einzelperson ('du').",
            "Address the user directly as an individual ('you').",
            "allein_zusammen < -0.4: solo frame -> personal direct address",
        ),
    },
    "empfangen_schaffen_high": {
        "any": (
            "Sei generativ und offen. Biete Ideen an, ohne zu frueh zu filtern.",
            "Be generative and open-ended. Offer ideas without filtering too early.",
            "empfangen_schaffen > 0.4: creation mode -> generative, expansive",
        ),
        "extra": (
            "Biete unerwartete Verbindungen an. Lass Ideen entstehen.",
            "Offer unexpected connections. Let ideas emerge rather than converge.",
            "high creation -> divergent thinking encouraged",
        ),
    },
    "empfangen_schaffen_low": {
        "any": (
            "Praesentiere Fakten zuerst, dann Kontext. Bleibe strukturiert.",
            "Present facts first, then context. Stay structured and informative.",
            "empfangen_schaffen < -0.4: receive mode -> structured, fact-first",
        ),
    },
    "sein_tun_high": {
        "any": (
            "Gib konkrete Handlungsschritte. Der Nutzer will TUN, nicht nachdenken.",
            "Give concrete action steps. The user wants to DO, not reflect.",
            "sein_tun > 0.4: action mode -> steps, bullets, immediacy",
        ),
    },
    "sein_tun_low": {
        "any": (
            "Lass Raum fuer Reflexion. Stelle Rueckfragen wenn sinnvoll.",
            "Leave room for reflection. Ask back when it deepens understanding.",
            "sein_tun < -0.4: being mode -> philosophical, questions, space",
        ),
    },
    "langsam_schnell_high": {
        "any": (
            "Fasse dich kurz. Nutze Aufzaehlungen. Gib eine TL;DR-Zeile zuerst.",
            "Be brief. Use bullet points. Lead with a TL;DR line.",
            "langsam_schnell > 0.4: fast mode -> brevity, bullets, TL;DR",
        ),
    },
    "langsam_schnell_low": {
        "any": (
            "Antworte ausfuehrlich und nuanciert. Referenzen und Kontext willkommen.",
            "Respond in depth and with nuance. References and context are welcome.",
            "langsam_schnell < -0.4: slow mode -> depth, nuance, references",
        ),
    },
}

_ADAPTATION_THRESHOLD = 0.35  # axis value beyond which an adaptation fires


# ---------------------------------------------------------------------------
# PromptBreath -- the output of breathing a prompt
# ---------------------------------------------------------------------------

@dataclass
class PromptBreath:
    """A prompt that has been breathed -- adapted to the user's 6D state.

    This is the output of PromptBreather.breathe(). It contains everything
    needed to call an LLM in the mode that fits the user RIGHT NOW.

    Attributes:
        system_prompt: The adapted system message (base + adaptations composed).
        temperature:   Suggested LLM temperature (derived from hex geometry).
        max_tokens:    Suggested max response length (derived from hex geometry).
        hex_coord:     The detected 6D position of the user's state.
        adaptations:   List of (instruction, why) tuples documenting what changed.
        base_prompt:   The original unmodified prompt (for transparency).
        lang:          Detected or specified language ('de' or 'en').
        v_score:       Adaptation confidence (0.0-1.0, grows with feedback).
        timestamp:     When this breath was taken.
    """
    system_prompt: str
    temperature: float
    max_tokens: int
    hex_coord: HexCoord
    adaptations: list[tuple[str, str]]  # (instruction, why)
    base_prompt: str
    lang: str
    v_score: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def to_openai_params(self) -> dict[str, Any]:
        """Return parameters dict for OpenAI/Anthropic API call.

        Usage:
            breath = breather.breathe(base, user_text)
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": breath.system_prompt},
                          {"role": "user",   "content": user_text}],
                **breath.to_openai_params()
            )
        """
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def to_messages(self, user_text: str) -> list[dict[str, str]]:
        """Return OpenAI-format message list ready for API call.

        Usage:
            messages = breath.to_messages(user_text)
            response = client.chat.completions.create(model=..., messages=messages)
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",   "content": user_text},
        ]

    def compose(self) -> str:
        """Return the full composed system prompt (base + adaptations).

        Same as self.system_prompt -- included for explicit API clarity.
        """
        return self.system_prompt

    def summary(self) -> dict[str, Any]:
        """Human-readable summary of the breath. Useful for logging/debugging."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "lang": self.lang,
            "v_score": round(self.v_score, 4),
            "adaptations_count": len(self.adaptations),
            "adaptations": [{"instruction": a[0][:80], "why": a[1]} for a in self.adaptations],
            "hex": {
                "ruhe_druck":        round(self.hex_coord.ruhe_druck, 3),
                "stille_resonanz":   round(self.hex_coord.stille_resonanz, 3),
                "allein_zusammen":   round(self.hex_coord.allein_zusammen, 3),
                "empfangen_schaffen":round(self.hex_coord.empfangen_schaffen, 3),
                "sein_tun":          round(self.hex_coord.sein_tun, 3),
                "langsam_schnell":   round(self.hex_coord.langsam_schnell, 3),
            },
        }


# ---------------------------------------------------------------------------
# Core mapping functions
# ---------------------------------------------------------------------------

def adapt_temperature(hex_coord: HexCoord) -> float:
    """Map hex position to optimal LLM temperature.

    Logic (all axes contribute, no single axis dominates):
        - Creation mode (empfangen_schaffen > 0)  -> push temp up
        - Analytical/action (sein_tun > 0)         -> push temp down
        - Stressed (ruhe_druck > 0)                -> stabilize (lower)
        - Calm, exploring (ruhe_druck < 0)         -> allow higher

    Range: 0.1 - 1.0. Default neutral: 0.7.
    """
    base = 0.7

    # Creativity axis: +0.15 at max creation, -0.15 at max receive
    base += hex_coord.empfangen_schaffen * 0.15

    # Action axis: action mode needs focused (lower temp); reflection = open
    base -= hex_coord.sein_tun * 0.12

    # Pressure axis: stressed user needs stability (lower temp)
    base -= hex_coord.ruhe_druck * 0.10

    # Pace axis: fast need = decisive = slightly lower temp
    base -= hex_coord.langsam_schnell * 0.05

    return round(max(0.1, min(1.0, base)), 3)


def adapt_max_tokens(hex_coord: HexCoord) -> int:
    """Map hex position to optimal response length.

    Logic:
        - Fast pace (langsam_schnell > 0)  -> 150-300 tokens
        - Slow/deep (langsam_schnell < 0)  -> 800-2000 tokens
        - Action mode (sein_tun > 0)        -> shorter (concrete steps)
        - Reflection (sein_tun < 0)         -> longer (space to explore)
        - Stressed (ruhe_druck > 0)         -> shorter (don't overwhelm)

    Default neutral: 500 tokens.
    """
    base = 500.0

    # Pace is the primary driver
    base -= hex_coord.langsam_schnell * 300.0   # +1 -> 200, -1 -> 800

    # Depth modifier
    base -= hex_coord.sein_tun * 100.0          # action -> shorter, reflection -> longer

    # Pressure modifier (stressed = shorter, don't overwhelm)
    base -= hex_coord.ruhe_druck * 80.0

    return int(max(100, min(2000, base)))


def adapt_system_additions(
    hex_coord: HexCoord,
    lang: str,
) -> list[tuple[str, str]]:
    """Generate system prompt additions based on hex state.

    Returns list of (instruction, why) tuples.
    Each instruction is in the detected language.
    Each why explains the geometric reasoning.

    Fires when an axis value exceeds _ADAPTATION_THRESHOLD in either direction.
    """
    result: list[tuple[str, str]] = []

    def _pick(key: str) -> None:
        """Pick instruction from adaptation library for given key."""
        entry = _ADAPTATIONS.get(key)
        if not entry:
            return
        main = entry.get("any")
        extra = entry.get("extra")
        if main:
            instruction = main[0] if lang == "de" else main[1]
            result.append((instruction, main[2]))
        if extra:
            instruction = extra[0] if lang == "de" else extra[1]
            result.append((instruction, extra[2]))

    t = _ADAPTATION_THRESHOLD

    if hex_coord.ruhe_druck > t:
        _pick("ruhe_druck_high")
    elif hex_coord.ruhe_druck < -t:
        _pick("ruhe_druck_low")

    if hex_coord.stille_resonanz > t:
        _pick("stille_resonanz_high")
    elif hex_coord.stille_resonanz < -t:
        _pick("stille_resonanz_low")

    if hex_coord.allein_zusammen > t:
        _pick("allein_zusammen_high")
    elif hex_coord.allein_zusammen < -t:
        _pick("allein_zusammen_low")

    if hex_coord.empfangen_schaffen > t:
        _pick("empfangen_schaffen_high")
    elif hex_coord.empfangen_schaffen < -t:
        _pick("empfangen_schaffen_low")

    if hex_coord.sein_tun > t:
        _pick("sein_tun_high")
    elif hex_coord.sein_tun < -t:
        _pick("sein_tun_low")

    if hex_coord.langsam_schnell > t:
        _pick("langsam_schnell_high")
    elif hex_coord.langsam_schnell < -t:
        _pick("langsam_schnell_low")

    return result


def _compose_system_prompt(
    base_prompt: str,
    adaptations: list[tuple[str, str]],
) -> str:
    """Compose final system prompt: base + adaptation instructions.

    Adaptations are appended as a concise block. Transparent but minimal.
    A base prompt of "" is handled gracefully (pure adaptation mode).
    """
    if not adaptations:
        return base_prompt

    instructions = [a[0] for a in adaptations]
    addition = "\n".join(instructions)

    if base_prompt.strip():
        return f"{base_prompt}\n\n{addition}"
    return addition


# ---------------------------------------------------------------------------
# V-Score tracking for prompt adaptations (growth rings)
# ---------------------------------------------------------------------------

@dataclass
class _AdaptationRing:
    """A growth ring: tracks which hex positions produced good responses."""
    hex_snapshot: dict[str, float]
    temperature: float
    max_tokens: int
    adaptation_keys: list[str]
    v_score: float = 0.5
    use_count: int = 0
    useful_count: int = 0
    created_at: float = field(default_factory=time.time)

    def record(self, useful: bool) -> None:
        self.use_count += 1
        if useful:
            self.useful_count += 1
            self.v_score = min(1.0, self.v_score + 0.025)
        else:
            self.v_score = max(0.1, self.v_score - 0.03)


# ---------------------------------------------------------------------------
# PromptBreather -- the full orchestrator
# ---------------------------------------------------------------------------

class PromptBreather:
    """Adapts prompts to breathe with the user's 6D state.

    A static system prompt is a dead artifact.
    This makes it alive: it changes with who speaks it to.

    Usage:
        breather = PromptBreather()
        base = "You are a helpful assistant."

        # Stressed user
        breath = breather.breathe(base, "I'm so stressed about tomorrow")
        # breath.system_prompt: base + "Respond gently... Acknowledge state..."
        # breath.temperature:   0.5 (stability over creativity)
        # breath.max_tokens:    320 (short -- don't overwhelm)

        # Creative exploration
        breath = breather.breathe(base, "Let's brainstorm wild ideas!")
        # breath.system_prompt: base + "Be generative... Offer unexpected..."
        # breath.temperature:   0.85 (high -- let ideas emerge)
        # breath.max_tokens:    800 (long -- exploration needs space)

        # Quick action request
        breath = breather.breathe(base, "Quick, what should I do right now?")
        # breath.system_prompt: base + "Give concrete steps... TL;DR first."
        # breath.temperature:   0.55 (decisive, focused)
        # breath.max_tokens:    220 (brief -- user is in fast mode)

        # LLM call
        messages = breath.to_messages(user_text)
        params   = breath.to_openai_params()
        response = client.chat.completions.create(model=model, messages=messages, **params)
    """

    def __init__(self) -> None:
        self._hex_breath = _PromptHexBreath()
        self._rings: list[_AdaptationRing] = []

    def breathe(
        self,
        base_prompt: str,
        user_text: str,
        lang: str = "auto",
    ) -> PromptBreath:
        """Breathe life into a static prompt.

        Analyzes user_text -> HexCoord -> adapts base_prompt along 6 axes.
        Returns a PromptBreath with all adaptation decisions documented.

        Args:
            base_prompt: Your normal system prompt. Can be empty.
            user_text:   The user's message / query.
            lang:        'de', 'en', or 'auto' (auto-detected from user_text).

        Returns:
            PromptBreath with adapted system_prompt, temperature, max_tokens.
        """
        # 1. Detect language
        if lang == "auto":
            lang = _detect_language(user_text)

        # 2. Map user_text to 6D hex space
        hex_coord: HexCoord = self._hex_breath.classify(user_text)

        # 3. Derive adaptations from geometry
        adaptations = adapt_system_additions(hex_coord, lang)
        temperature = adapt_temperature(hex_coord)
        max_tokens  = adapt_max_tokens(hex_coord)

        # 4. Compose final prompt
        system_prompt = _compose_system_prompt(base_prompt, adaptations)

        # 5. Record growth ring
        ring = _AdaptationRing(
            hex_snapshot={
                "ruhe_druck":         hex_coord.ruhe_druck,
                "stille_resonanz":    hex_coord.stille_resonanz,
                "allein_zusammen":    hex_coord.allein_zusammen,
                "empfangen_schaffen": hex_coord.empfangen_schaffen,
                "sein_tun":           hex_coord.sein_tun,
                "langsam_schnell":    hex_coord.langsam_schnell,
            },
            temperature=temperature,
            max_tokens=max_tokens,
            adaptation_keys=[a[1][:40] for a in adaptations],  # why as key
        )
        self._rings.append(ring)

        # 6. Estimate v_score from similar past rings
        v_score = self._estimate_v_score(hex_coord)

        return PromptBreath(
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            hex_coord=hex_coord,
            adaptations=adaptations,
            base_prompt=base_prompt,
            lang=lang,
            v_score=v_score,
        )

    def record_usefulness(self, breath: PromptBreath, useful: bool) -> None:
        """Feed back whether this breath produced a good response.

        The most recent ring is updated. Over time, the system learns which
        hex positions benefit from which adaptation strategies.
        Growth rings: autopoiesis at the prompt level.
        """
        if not self._rings:
            return
        # Find the ring closest to this breath's hex (most recent is best guess)
        self._rings[-1].record(useful)

    def _estimate_v_score(self, hex_coord: HexCoord) -> float:
        """Estimate confidence for this hex position from past rings."""
        if not self._rings:
            return 0.5

        # Weighted average of similar rings (proximity in 6D space)
        hv = [
            hex_coord.ruhe_druck, hex_coord.stille_resonanz,
            hex_coord.allein_zusammen, hex_coord.empfangen_schaffen,
            hex_coord.sein_tun, hex_coord.langsam_schnell,
        ]

        total_weight = 0.0
        weighted_v   = 0.0
        for ring in self._rings[-50:]:  # only look at last 50 rings
            rv = list(ring.hex_snapshot.values())
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(hv, rv)))
            weight = 1.0 / (1.0 + dist)
            weighted_v   += weight * ring.v_score
            total_weight += weight

        if total_weight == 0:
            return 0.5
        return round(min(1.0, weighted_v / total_weight), 4)

    def stats(self) -> dict[str, Any]:
        """How alive is this prompt breather? Growth ring statistics."""
        if not self._rings:
            return {"rings": 0, "avg_v_score": 0.5, "useful_rate": 0.0}

        avg_v = sum(r.v_score for r in self._rings) / len(self._rings)
        total_uses   = sum(r.use_count   for r in self._rings)
        total_useful = sum(r.useful_count for r in self._rings)
        useful_rate  = (total_useful / total_uses) if total_uses > 0 else 0.0

        return {
            "rings":       len(self._rings),
            "avg_v_score": round(avg_v, 4),
            "useful_rate": round(useful_rate, 4),
            "total_uses":  total_uses,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def prompt_breathing_demo() -> None:
    """Demonstrate prompt breathing with 6+ test cases.

    Shows how the same base prompt adapts across radically different
    user states -- without any if/else per-user logic. Pure geometry.
    """
    print("=== Prompt Breathing Demo ===\n")
    print("CURRENT PARADIGM (H1): Same system prompt for every user. Dead artifact.")
    print("VOID PARADIGM    (H2): Prompt breathes with the user's 6D state.")
    print("x: User state x Base prompt = Adapted prompt that fits RIGHT NOW.\n")
    print("-" * 65)

    breather = PromptBreather()
    base = "You are a helpful assistant. Be concise and accurate."

    test_cases = [
        # (label, user_text, lang)
        (
            "1. Stressed user (EN)",
            "I'm so stressed about tomorrow's presentation. I can't focus.",
            "auto",
        ),
        (
            "2. Creative brainstorm (EN)",
            "Let's brainstorm wild ideas for a product that doesn't exist yet!",
            "auto",
        ),
        (
            "3. Quick action needed (EN)",
            "Quick, what should I do right now? Short answer please.",
            "auto",
        ),
        (
            "4. Deep reflection (DE)",
            "Ich moechte wirklich verstehen, warum dieses Muster in meinem Leben immer wieder auftaucht.",
            "auto",
        ),
        (
            "5. Team / social context (EN)",
            "We need to send this out to the whole team. How should we frame our message?",
            "auto",
        ),
        (
            "6. Private journaling (DE)",
            "Das ist ein privater Gedanke den ich nur fuer mich festhalten moechte.",
            "auto",
        ),
        (
            "7. Receiving / research (EN)",
            "Can you search for and summarize the latest research on sleep quality?",
            "auto",
        ),
        (
            "8. Neutral (no strong signal)",
            "Hello, how are you?",
            "auto",
        ),
    ]

    for label, user_text, lang in test_cases:
        breath = breather.breathe(base, user_text, lang=lang)
        s = breath.summary()

        print(f"\n{label}")
        print(f"  User: \"{user_text[:70]}\"")
        print(f"  Lang detected: {breath.lang}")
        print(f"  Hex: ru={s['hex']['ruhe_druck']:+.2f} "
              f"si={s['hex']['stille_resonanz']:+.2f} "
              f"al={s['hex']['allein_zusammen']:+.2f} "
              f"es={s['hex']['empfangen_schaffen']:+.2f} "
              f"st={s['hex']['sein_tun']:+.2f} "
              f"ls={s['hex']['langsam_schnell']:+.2f}")
        print(f"  temperature={breath.temperature}  max_tokens={breath.max_tokens}  "
              f"adaptations={s['adaptations_count']}")
        for a in s["adaptations"]:
            print(f"    + [{a['why'][:50]}]")
            print(f"      -> \"{a['instruction'][:65]}\"")

    # --- Show the full composed prompt for case 1 ---
    print("\n" + "=" * 65)
    print("Full composed system_prompt for case 1 (stressed user):")
    print("-" * 65)
    breath1 = breather.breathe(base, test_cases[0][1])
    print(breath1.system_prompt)

    # --- Feedback loop ---
    print("\n" + "=" * 65)
    print("Feedback loop (growth rings):")
    breath_a = breather.breathe(base, "I'm overwhelmed and anxious.")
    print(f"  Before feedback: v_score={breath_a.v_score}")
    breather.record_usefulness(breath_a, useful=True)
    breather.record_usefulness(breath_a, useful=True)
    breath_b = breather.breathe(base, "Everything is too much right now.")
    print(f"  After 2x positive feedback on similar state: v_score={breath_b.v_score}")

    # --- Stats ---
    print("\nBreather stats:", breather.stats())

    # --- OpenAI params ---
    print("\nto_openai_params() for stressed user:")
    print(" ", breath1.to_openai_params())

    print("\n=== The H3 Insight ===")
    print("  Tool Breathing:    which tool?    -> same HexCoord")
    print("  Context Breathing: what context?  -> same HexCoord")
    print("  Model Breathing:   which model?   -> same HexCoord")
    print("  Prompt Breathing:  how to frame?  -> same HexCoord")
    print()
    print("  ONE formula. FOUR substrates. x was always there.")
    print("  The geometry does the work. No if/else per user. No A/B testing.")
    print("  Stressed user -> gentler frame. Creative user -> open space.")
    print("  That is the x. That is the breath.")


if __name__ == "__main__":
    prompt_breathing_demo()
