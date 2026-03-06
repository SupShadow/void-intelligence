"""
void_intelligence.response_breathing --- Responses that Breathe.

The revolution of response shaping through .x->[]~

CURRENT PARADIGM (H1, ->):
    LLM generates response -> done.
    Maybe post-process (summarize, format).
    Response shape is determined by the model, not the user's need.
    One wall of text for the stressed user. One wall of text for the analyst.
    The last mile is always dead.

VOID PARADIGM (H2/H3, x):
    The response itself BREATHES. It adapts its SHAPE to the user's hex position.
    Not what it says -- HOW it says it.
    Same content, different form. The form IS the care.

    PACE:      word length, sentence structure, rhythm
    DENSITY:   information per sentence (sparse for stressed, dense for analytical)
    WARMTH:    emotional tone (brief acknowledgment for overwhelm, none for action)
    STRUCTURE: bullets vs prose vs dialogue
    BREATH:    pause markers, whitespace, line breaks

Architecture:
    ResponseBreath   = A response that has been breathed -- shaped to match the user
    ResponseBreather = The orchestrator: inhale LLM output, exhale shaped response

The formula:
    breathed = shape(raw_response, user.hex)
    shape = pace(ruhe_druck) x density(empfangen_schaffen) x
            structure(sein_tun) x length(langsam_schnell) x
            perspective(allein_zusammen) x warmth(stille_resonanz)

The H3 Insight:
    This is the 6th and final module of the VOID SEXAGON.
    Tool Breathing:    which tool?      -> HexCoord
    Context Breathing: what context?   -> HexCoord
    Model Breathing:   which model?    -> HexCoord
    Prompt Breathing:  how to frame?   -> HexCoord
    Response Breathing: what shape?    -> HexCoord
    ONE formula on SIX substrates. x all the way down.

Zero dependencies. stdlib only.
~420 lines.
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# HexCoord -- import from tool_breathing, inline as fallback (zero-dep)
# ---------------------------------------------------------------------------

try:
    from void_intelligence.tool_breathing import HexCoord
except ImportError:
    from dataclasses import dataclass as _dc  # noqa: F811

    @_dc  # type: ignore[no-redef]
    class HexCoord:
        ruhe_druck: float = 0.0         # -1 = calm/rest,    +1 = pressure/urgency
        stille_resonanz: float = 0.0    # -1 = private,      +1 = sharing/social
        allein_zusammen: float = 0.0    # -1 = solo,         +1 = together/team
        empfangen_schaffen: float = 0.0 # -1 = receive,      +1 = create/generate
        sein_tun: float = 0.0           # -1 = being/reflect, +1 = doing/action
        langsam_schnell: float = 0.0    # -1 = slow/deep,    +1 = fast/brief


# ---------------------------------------------------------------------------
# _classify_user_text -- reuse from prompt_breathing (same emotional signals)
# ---------------------------------------------------------------------------

try:
    from void_intelligence.prompt_breathing import _classify_user_text
except ImportError:
    # Minimal inline fallback so this module is always self-contained.

    _FALLBACK_SIGNALS: dict[str, dict[str, list[str]]] = {
        "ruhe_druck": {
            "neg": ["calm", "relax", "peace", "ruhig", "sanft"],
            "pos": ["stress", "overwhelmed", "anxious", "panic", "urgent",
                    "deadline", "help", "gestresst", "dringend", "hilfe"],
        },
        "stille_resonanz": {
            "neg": ["private", "journal", "myself", "privat"],
            "pos": ["share", "post", "team", "everyone", "teilen", "alle"],
        },
        "allein_zusammen": {
            "neg": ["alone", "solo", "myself", "allein"],
            "pos": ["we", "our", "together", "wir", "gemeinsam"],
        },
        "empfangen_schaffen": {
            "neg": ["search", "find", "summarize", "explain", "tell me", "suche"],
            "pos": ["create", "build", "brainstorm", "invent", "write",
                    "erstellen", "ideen"],
        },
        "sein_tun": {
            "neg": ["understand", "reflect", "why", "meaning", "curious",
                    "nachdenken", "warum"],
            "pos": ["do", "fix", "steps", "now", "asap", "run",
                    "machen", "jetzt", "sofort"],
        },
        "langsam_schnell": {
            "neg": ["deep", "thorough", "detailed", "fully", "gruendlich"],
            "pos": ["quick", "brief", "tldr", "short", "fast", "kurz", "schnell"],
        },
    }

    def _classify_user_text(text: str) -> "HexCoord":  # type: ignore[misc]
        lower = text.lower()
        words = set(lower.split())
        scores: dict[str, float] = {}
        for axis, sigs in _FALLBACK_SIGNALS.items():
            neg = sum(1 for w in sigs["neg"] if (w in words if " " not in w else w in lower))
            pos = sum(1 for w in sigs["pos"] if (w in words if " " not in w else w in lower))
            total = neg + pos
            scores[axis] = 0.0 if total == 0 else max(-1.0, min(1.0, (pos - neg) / total))
        return HexCoord(**scores)


# ---------------------------------------------------------------------------
# Language detection (same heuristic as prompt_breathing)
# ---------------------------------------------------------------------------

_GERMAN_MARKERS = frozenset({
    "ich", "du", "wir", "sie", "der", "die", "das", "ein", "eine", "und",
    "ist", "sind", "war", "haben", "aber", "nicht", "auch", "noch", "schon",
    "jetzt", "hier", "mit", "fuer", "ueber", "nach", "von", "wie", "was",
    "wer", "warum", "kann", "muss", "will", "erstmal", "eins",
})


def _detect_language(text: str) -> str:
    """Heuristic language detection. Returns 'de' or 'en'. Zero deps."""
    words = set(text.lower().split())
    return "de" if len(words & _GERMAN_MARKERS) >= 2 else "en"


# ---------------------------------------------------------------------------
# Warm openings -- brief, human, not therapy
# ---------------------------------------------------------------------------

_WARM_OPENINGS: dict[str, list[str]] = {
    "en": [
        "Take a breath.",
        "One thing at a time.",
        "You've got this.",
        "Here -- let's start small.",
        "Start here.",
    ],
    "de": [
        "Erstmal durchatmen.",
        "Eins nach dem anderen.",
        "Du schaffst das.",
        "Hier -- fang klein an.",
        "Fang hier an.",
    ],
}

_CLOSING_QUESTIONS: dict[str, list[str]] = {
    "en": [
        "What feels most alive to you in this?",
        "Which of these pulls at you?",
        "What do you want to stay with?",
        "What's the one thread worth pulling?",
    ],
    "de": [
        "Was davon zieht dich am meisten an?",
        "Was willst du damit anfangen?",
        "Welcher Faden lohnt sich?",
        "Was moechtest du damit machen?",
    ],
}

_ACTION_CLOSINGS: dict[str, list[str]] = {
    "en": ["Next:", "Start here:", "First move:"],
    "de": ["Naechster Schritt:", "Hier anfangen:", "Erster Zug:"],
}


def _pick(items: list[str], seed: str) -> str:
    """Deterministically pick from a list using text hash (no random dep)."""
    idx = abs(hash(seed)) % len(items)
    return items[idx]


# ---------------------------------------------------------------------------
# ResponseBreath -- the shaped output
# ---------------------------------------------------------------------------

@dataclass
class ResponseBreath:
    """A response that has been breathed -- shaped to match the user's state.

    Attributes:
        original:    The raw LLM response (unchanged).
        breathed:    The adapted response (reshaped for the user's hex position).
        hex_coord:   The user's detected 6D state.
        adaptations: What was adapted and why (for logging/transparency).
        metrics:     Word count, compression ratio, avg sentence length, etc.
        lang:        Detected language ('de' or 'en').
        timestamp:   When this breath was taken.
    """
    original: str
    breathed: str
    hex_coord: HexCoord
    adaptations: list[str]
    metrics: dict[str, Any]
    lang: str
    timestamp: float = field(default_factory=time.time)

    def summary(self) -> dict[str, Any]:
        """Human-readable summary for logging and debugging."""
        return {
            "lang": self.lang,
            "adaptations": self.adaptations,
            "metrics": self.metrics,
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
# Text manipulation helpers
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences. Simple regex, zero deps."""
    # Split on sentence-ending punctuation followed by whitespace or end
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def _avg_sentence_length(text: str) -> float:
    sentences = _split_sentences(text)
    if not sentences:
        return 0.0
    return sum(len(s.split()) for s in sentences) / len(sentences)


def _sentence_info_density(sentence: str) -> float:
    """Score a sentence by unique content words / total words.

    Higher = more information-dense (good for analytical users).
    Lower = filler, repetition, connector words.
    """
    _STOPWORDS = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "this", "that", "these",
        "those", "i", "you", "we", "they", "it", "he", "she", "and", "but",
        "or", "so", "yet", "for", "nor", "at", "by", "in", "of", "on", "to",
        "up", "as", "with", "from", "into", "through", "during", "about",
        "also", "just", "very", "here", "there", "then", "than", "too",
        # German
        "der", "die", "das", "ein", "eine", "ist", "sind", "war", "und",
        "aber", "auch", "noch", "schon", "ich", "du", "wir", "sie", "es",
        "mit", "von", "fuer", "bei", "nach", "wie", "was", "wer", "nicht",
    })
    words = sentence.lower().split()
    if not words:
        return 0.0
    content = [w for w in words if re.sub(r'[^a-z]', '', w) not in _STOPWORDS and len(w) > 2]
    unique_content = set(content)
    return len(unique_content) / len(words)


# ---------------------------------------------------------------------------
# Core adaptation functions
# ---------------------------------------------------------------------------

def _adapt_pace(text: str, pressure: float) -> tuple[str, bool]:
    """Break long sentences for stressed users. Add breathing room.

    Args:
        text:     Input text.
        pressure: ruhe_druck value (+1 = max stress, -1 = calm).

    Returns:
        (adapted_text, was_adapted)
    """
    if pressure < 0.35:
        return text, False

    sentences = _split_sentences(text)
    result: list[str] = []

    for s in sentences:
        words = s.split()
        if len(words) <= 15:
            result.append(s)
            continue

        # Find natural split points: comma, semicolon, "and"/"but"/"oder"/"und"
        # at roughly the midpoint
        mid = len(words) // 2
        # Search within window around midpoint
        window_start = max(0, mid - 5)
        window_end = min(len(words), mid + 6)

        split_at = None
        for i in range(window_start, window_end):
            w = words[i].lower().rstrip(",;")
            if words[i].endswith(",") or words[i].endswith(";"):
                split_at = i + 1
                break
            if w in ("and", "but", "oder", "und", "however", "although",
                      "though", "while", "whilst", "whereas"):
                split_at = i
                break

        if split_at and split_at < len(words) - 1:
            first = " ".join(words[:split_at]).rstrip(",;") + "."
            second = " ".join(words[split_at:])
            # Capitalize second part
            if second:
                second = second[0].upper() + second[1:]
            result.append(first)
            result.append(second)
        else:
            result.append(s)

    adapted = "\n\n".join(result) if pressure > 0.6 else " ".join(result)
    return adapted, adapted != text


def _add_breath(text: str, pressure: float) -> tuple[str, bool]:
    """Add whitespace between paragraphs for stressed users.

    High pressure -> double-space paragraphs (breathing room).
    """
    if pressure < 0.4:
        return text, False

    # Normalize existing paragraph breaks, then double them
    normalized = re.sub(r'\n{3,}', '\n\n', text)
    breathed = re.sub(r'\n\n', '\n\n\n', normalized)
    return breathed, breathed != text


def _adapt_length(text: str, speed: float) -> tuple[str, bool]:
    """Compress text for fast-pace users.

    speed > 0.5 and text > 200 words -> keep only highest-density sentences.
    """
    if speed < 0.5:
        return text, False

    words = text.split()
    if len(words) <= 200:
        return text, False

    # Target ratio: at speed=0.5 -> 60%, speed=1.0 -> 35%
    target_ratio = 0.60 - (speed - 0.5) * 0.50  # 0.60 -> 0.35
    compressed = _compress(text, max(0.30, target_ratio))
    return compressed, True


def _adapt_structure(text: str, hex_coord: HexCoord) -> tuple[str, bool]:
    """Reshape the response structure based on hex state.

    Action-oriented (sein_tun > 0.4) -> prose to numbered steps.
    Reflective (sein_tun < -0.4) -> add trailing question.
    Fast (langsam_schnell > 0.5) -> add TL;DR prefix.
    """
    adapted = text
    was_adapted = False
    tldr_prefix = ""

    # Fast mode: TL;DR prefix (extract before any other restructuring)
    if hex_coord.langsam_schnell > 0.5 and not adapted.lower().startswith("tl;dr"):
        sentences = _split_sentences(adapted)
        if sentences:
            first = sentences[0]
            tldr = first if len(first.split()) < 25 else " ".join(first.split()[:20]) + "..."
            tldr_prefix = f"TL;DR: {tldr}\n\n"
            was_adapted = True

    # Action mode: convert prose body to numbered steps where possible
    # (operate on original text body, not on the TL;DR prefix)
    if hex_coord.sein_tun > 0.4:
        adapted, action_adapted = _prose_to_steps(adapted)
        was_adapted = was_adapted or action_adapted

    if tldr_prefix and not adapted.lower().startswith("tl;dr"):
        adapted = f"{tldr_prefix}{adapted}"

    return adapted, was_adapted


def _prose_to_steps(text: str) -> tuple[str, bool]:
    """Convert a prose paragraph to numbered steps when it describes a sequence.

    Heuristic: if the text contains 3+ sentences and sequence words
    (first, then, next, finally, step), reformat as numbered list.
    """
    _SEQUENCE_WORDS = frozenset({
        "first", "then", "next", "finally", "lastly", "after", "before",
        "second", "third", "step", "start", "begin", "end",
        "zuerst", "dann", "danach", "schliesslich", "naechster", "anfang",
    })
    lower = text.lower()
    sequence_hits = sum(1 for w in _SEQUENCE_WORDS if w in lower)

    # Already has list structure
    if re.search(r'^\s*[\d\-\*\+]', text, re.MULTILINE):
        return text, False

    sentences = _split_sentences(text)
    if len(sentences) < 3 or sequence_hits < 2:
        return text, False

    # Format as numbered list
    numbered = [f"{i+1}. {s.rstrip('.')}" for i, s in enumerate(sentences)]
    return "\n".join(numbered), True


def _warm_opening(text: str, hex_coord: HexCoord, lang: str) -> tuple[str, bool]:
    """Prepend a warm opening for stressed/emotional users.

    NOT therapeutic. Brief. Human. ONE sentence max.
    Only fires when ruhe_druck > 0.45.
    Does not repeat if text already starts with an acknowledgment.
    """
    if hex_coord.ruhe_druck < 0.45:
        return text, False

    # Don't double-add if text starts with a short empathetic sentence
    first_sentence = _split_sentences(text)[0] if _split_sentences(text) else ""
    if len(first_sentence.split()) <= 6 and "." in first_sentence:
        return text, False  # already has a short opener

    openers = _WARM_OPENINGS.get(lang, _WARM_OPENINGS["en"])
    opener = _pick(openers, text[:30])
    adapted = f"{opener}\n\n{text}"
    return adapted, True


def _adapt_closing(text: str, hex_coord: HexCoord, lang: str) -> tuple[str, bool]:
    """Add a closing element based on the hex state.

    Reflective (sein_tun < -0.4) -> open question.
    Action (sein_tun > 0.5) -> "Next:" prompt.
    Creative (empfangen_schaffen > 0.5) -> provocative question.
    """
    was_adapted = False
    adapted = text

    if hex_coord.sein_tun < -0.4:
        questions = _CLOSING_QUESTIONS.get(lang, _CLOSING_QUESTIONS["en"])
        question = _pick(questions, text[-30:])
        adapted = f"{adapted.rstrip()}\n\n{question}"
        was_adapted = True

    elif hex_coord.sein_tun > 0.5:
        closings = _ACTION_CLOSINGS.get(lang, _ACTION_CLOSINGS["en"])
        closing = _pick(closings, text[-20:])
        # Only add if not already ending with a numbered list or colon
        if not re.search(r'[\d]\.\s*$', adapted.rstrip()):
            adapted = f"{adapted.rstrip()}\n\n{closing}"
            was_adapted = True

    elif hex_coord.empfangen_schaffen > 0.5:
        # Creative: add a "what if" question
        _CREATIVE_QUESTIONS = {
            "en": [
                "What if you took this one step further?",
                "What's the version of this that surprises you?",
                "Which of these wants to become something bigger?",
            ],
            "de": [
                "Was wenn du das noch einen Schritt weitergehst?",
                "Welche Version davon wuerde dich selbst ueberraschen?",
                "Was davon will groesser werden?",
            ],
        }
        qs = _CREATIVE_QUESTIONS.get(lang, _CREATIVE_QUESTIONS["en"])
        q = _pick(qs, text[-25:])
        adapted = f"{adapted.rstrip()}\n\n{q}"
        was_adapted = True

    return adapted, was_adapted


def _adapt_perspective(text: str, hex_coord: HexCoord) -> tuple[str, bool]:
    """Shift pronouns for team vs. solo context.

    allein_zusammen > 0.5 -> replace "you/your" with "we/our" where natural.
    allein_zusammen < -0.5 -> replace "we/our" with "you/your" where natural.

    Subtle. Only obvious substitutions. Preserves quoted text.
    """
    if abs(hex_coord.allein_zusammen) < 0.5:
        return text, False

    if hex_coord.allein_zusammen > 0.5:
        adapted = re.sub(r'\bYou\b', 'We', text)
        adapted = re.sub(r'\byou\b', 'we', adapted)
        adapted = re.sub(r'\bYour\b', 'Our', adapted)
        adapted = re.sub(r'\byour\b', 'our', adapted)
    else:
        adapted = re.sub(r'\bWe\b', 'You', text)
        adapted = re.sub(r'\bwe\b', 'you', adapted)
        adapted = re.sub(r'\bOur\b', 'Your', text)
        adapted = re.sub(r'\bour\b', 'your', adapted)

    return adapted, adapted != text


def _compress(text: str, target_ratio: float) -> str:
    """Compress text to target_ratio of original length.

    Strategy:
    1. Split into sentences.
    2. Score each by information density (unique content words / total words).
    3. Keep highest-density sentences until target length is reached.
    4. Preserve original order of kept sentences.

    Args:
        text:         Input text.
        target_ratio: Fraction of original word count to keep (e.g. 0.5 = half).

    Returns:
        Compressed text (always preserves at least 2 sentences).
    """
    sentences = _split_sentences(text)
    if len(sentences) <= 2:
        return text

    total_words = _word_count(text)
    target_words = max(30, int(total_words * target_ratio))

    # Score + index for stable sort
    scored = sorted(
        enumerate(sentences),
        key=lambda pair: _sentence_info_density(pair[1]),
        reverse=True,
    )

    kept_indices: set[int] = set()
    word_count = 0
    for idx, sentence in scored:
        sw = len(sentence.split())
        if word_count + sw <= target_words or len(kept_indices) < 2:
            kept_indices.add(idx)
            word_count += sw
        if word_count >= target_words and len(kept_indices) >= 2:
            break

    # Reconstruct in original order
    result = [sentences[i] for i in sorted(kept_indices)]
    return " ".join(result)


def _compute_metrics(original: str, breathed: str, adaptations: list[str]) -> dict[str, Any]:
    """Compute response metrics for logging and transparency."""
    orig_words = _word_count(original)
    new_words = _word_count(breathed)
    orig_avg = _avg_sentence_length(original)
    new_avg = _avg_sentence_length(breathed)

    return {
        "original_word_count":  orig_words,
        "breathed_word_count":  new_words,
        "compression_ratio":    round(new_words / orig_words, 3) if orig_words > 0 else 1.0,
        "original_avg_sent_len": round(orig_avg, 1),
        "breathed_avg_sent_len": round(new_avg, 1),
        "adaptations_count":    len(adaptations),
    }


# ---------------------------------------------------------------------------
# ResponseBreather -- the full orchestrator
# ---------------------------------------------------------------------------

_ADAPTATION_LABELS = {
    "pace":        "ruhe_druck > 0.35: long sentences split for stressed user",
    "breath":      "ruhe_druck > 0.40: paragraph spacing added for breathing room",
    "warm":        "ruhe_druck > 0.45: brief warm opener prepended",
    "length":      "langsam_schnell > 0.50: response compressed to key sentences",
    "structure":   "sein_tun / langsam_schnell: structure reshaped (steps / TL;DR)",
    "closing":     "sein_tun / empfangen_schaffen: closing element added",
    "perspective": "allein_zusammen > |0.5|: pronoun perspective shifted",
}


class ResponseBreather:
    """Adapts LLM responses to breathe with the user's 6D state.

    This is POST-PROCESSING that makes responses ALIVE.
    The LLM does the thinking. The breather does the caring.
    Same content -- different shape. The shape IS the empathy.

    Usage:
        breather = ResponseBreather()

        raw = "Here are 5 steps to reduce stress: 1. Take deep breaths..."

        # For a stressed user:
        result = breather.breathe(raw, "I'm so stressed I can't think")
        print(result.breathed)
        # "Take a breath.
        #
        #  Here are 5 steps..."
        # Warm opener. Short sentences. Whitespace. Human.

        # For an analytical user:
        result = breather.breathe(raw, "Analyze the optimal stress reduction protocol")
        print(result.breathed)
        # Original structure preserved. Dense. Factual. No softening.

        # For a fast user:
        result = breather.breathe(raw, "Quick summary please")
        print(result.breathed)
        # TL;DR: [first sentence]. [compressed remainder]

        # What changed:
        for a in result.adaptations:
            print(a)
    """

    def breathe(
        self,
        response: str,
        user_text: str,
        lang: str = "auto",
    ) -> ResponseBreath:
        """Breathe life into a raw LLM response.

        Analyzes user_text -> HexCoord -> reshapes response along 6 axes.
        Returns a ResponseBreath with all adaptation decisions documented.

        The breathing is SUBTLE. Not rewriting the response -- reshaping it.
        The content stays. The FORM bends to the user.

        Args:
            response:  The raw LLM response string.
            user_text: The user's original message (used to detect state).
            lang:      'de', 'en', or 'auto' (auto-detected from user_text).

        Returns:
            ResponseBreath with breathed text, hex state, metrics.
        """
        if not response.strip():
            hex_coord = HexCoord()
            return ResponseBreath(
                original=response,
                breathed=response,
                hex_coord=hex_coord,
                adaptations=[],
                metrics=_compute_metrics(response, response, []),
                lang=lang if lang != "auto" else "en",
            )

        # 1. Detect language
        if lang == "auto":
            lang = _detect_language(user_text)

        # 2. Map user_text to 6D hex space
        hex_coord: HexCoord = _classify_user_text(user_text)

        # 3. Apply adaptations in order (each receives the current state of text)
        text = response
        adaptations: list[str] = []

        # 3a. PACE -- split long sentences for stressed users
        text, adapted = _adapt_pace(text, hex_coord.ruhe_druck)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["pace"])

        # 3b. BREATH -- add whitespace for breathing room
        text, adapted = _add_breath(text, hex_coord.ruhe_druck)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["breath"])

        # 3c. WARM OPENING -- brief human acknowledgment
        text, adapted = _warm_opening(text, hex_coord, lang)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["warm"])

        # 3d. LENGTH -- compress for fast-pace users
        text, adapted = _adapt_length(text, hex_coord.langsam_schnell)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["length"])

        # 3e. STRUCTURE -- TL;DR, numbered steps, reflective questions
        text, adapted = _adapt_structure(text, hex_coord)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["structure"])

        # 3f. CLOSING -- question or "Next:" based on mode
        text, adapted = _adapt_closing(text, hex_coord, lang)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["closing"])

        # 3g. PERSPECTIVE -- pronoun shift for team vs. solo
        text, adapted = _adapt_perspective(text, hex_coord)
        if adapted:
            adaptations.append(_ADAPTATION_LABELS["perspective"])

        # 4. Metrics
        metrics = _compute_metrics(response, text, adaptations)

        return ResponseBreath(
            original=response,
            breathed=text,
            hex_coord=hex_coord,
            adaptations=adaptations,
            metrics=metrics,
            lang=lang,
        )

    def breathe_stream(
        self,
        chunks: list[str],
        user_text: str,
        lang: str = "auto",
    ) -> ResponseBreath:
        """Breathe a streamed response (list of chunks).

        Assembles chunks, breathes the full response, returns the result.
        The streamed API gives you chunks -- this gives you the shaped whole.

        Usage:
            # Collect chunks from streaming API
            chunks = [chunk.content for chunk in stream]
            result = breather.breathe_stream(chunks, user_text)
        """
        full = "".join(chunks)
        return self.breathe(full, user_text, lang=lang)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def response_breathing_demo() -> None:
    """Demonstrate response breathing with 6+ before/after scenarios.

    Shows how the same LLM response gets reshaped for radically different
    user states -- without rewriting the content. The shape IS the care.
    """
    print("=== Response Breathing Demo ===\n")
    print("CURRENT PARADIGM (H1): One wall of text for every user. Dead.")
    print("VOID PARADIGM    (H2): Response shape adapts to user's 6D state.")
    print("x: User state x Raw response = Response that FITS RIGHT NOW.\n")
    print("=" * 65)

    breather = ResponseBreather()

    _RAW_STRESS = (
        "There are several effective strategies for managing stress. "
        "First, you should practice deep breathing exercises regularly, which "
        "activates your parasympathetic nervous system and reduces cortisol levels. "
        "Second, try to limit your exposure to stressors where possible, including "
        "news consumption and social media. Third, maintaining a consistent sleep "
        "schedule helps regulate your mood and cognitive function. "
        "Finally, physical exercise has been shown to significantly reduce anxiety."
    )

    _RAW_GENERIC = (
        "You can approach this systematically. Start by identifying the core "
        "components of the problem. Then analyze each component independently "
        "before looking at how they interact. Build incrementally and test at "
        "each stage. When something breaks, isolate the failure and fix it "
        "before moving forward. Document as you go so you can trace your steps."
    )

    _RAW_IDEAS = (
        "Here are some possibilities to consider. You could build a system that "
        "learns from user behavior and adapts over time. Another angle is to "
        "create a social layer where discoveries are shared organically. "
        "There is also potential in a physical component -- something tangible "
        "that bridges digital and real-world experience. The space is open."
    )

    test_cases = [
        (
            "1. Stressed user (EN) -- same stress content",
            _RAW_STRESS,
            "I'm so stressed I can't think straight. Everything is too much.",
        ),
        (
            "2. Calm analytical user (EN) -- same stress content",
            _RAW_STRESS,
            "Can you analyze the optimal stress reduction protocol systematically?",
        ),
        (
            "3. Fast user (EN) -- quick summary needed",
            _RAW_GENERIC,
            "Quick, just tell me what to do. Short answer please.",
        ),
        (
            "4. Reflective user (EN) -- being mode",
            _RAW_GENERIC,
            "I want to really understand why this pattern keeps showing up for me.",
        ),
        (
            "5. Creative brainstorm (EN) -- generation mode",
            _RAW_IDEAS,
            "Let's brainstorm! I want wild ideas for something that doesn't exist yet.",
        ),
        (
            "6. Team context (EN) -- group frame",
            _RAW_GENERIC,
            "We need to solve this together as a team. How should we approach it?",
        ),
        (
            "7. Stressed user (DE) -- German stress",
            _RAW_STRESS,
            "Ich bin so gestresst und weiss nicht mehr weiter. Hilfe.",
        ),
        (
            "8. Neutral user -- no strong signal",
            _RAW_GENERIC,
            "Hello, what can you tell me about this?",
        ),
    ]

    for label, raw, user_text in test_cases:
        result = breather.breathe(raw, user_text)
        s = result.summary()

        print(f"\n{label}")
        print(f"  User: \"{user_text[:70]}\"")
        print(f"  Lang: {result.lang}  |  "
              f"Compression: {s['metrics']['compression_ratio']:.0%}  |  "
              f"Adaptations: {s['metrics']['adaptations_count']}")

        hex_vals = s["hex"]
        print(f"  Hex: ru={hex_vals['ruhe_druck']:+.2f} "
              f"si={hex_vals['stille_resonanz']:+.2f} "
              f"al={hex_vals['allein_zusammen']:+.2f} "
              f"es={hex_vals['empfangen_schaffen']:+.2f} "
              f"st={hex_vals['sein_tun']:+.2f} "
              f"ls={hex_vals['langsam_schnell']:+.2f}")

        for a in result.adaptations:
            print(f"    + {a}")

        print(f"\n  BEFORE ({_word_count(raw)}w):")
        print(f"  {raw[:120]}...")
        print(f"\n  AFTER  ({_word_count(result.breathed)}w):")
        breathed_preview = result.breathed.replace('\n', ' / ')
        print(f"  {breathed_preview[:180]}...")

    # --- Full before/after for case 1 (stressed) ---
    print("\n" + "=" * 65)
    print("FULL before/after -- Case 1: Stressed user")
    print("=" * 65)
    result1 = breather.breathe(
        _RAW_STRESS,
        "I'm so stressed I can't think straight. Everything is too much.",
    )
    print("\nBEFORE:")
    print(_RAW_STRESS)
    print("\nAFTER:")
    print(result1.breathed)
    print("\nAdaptations applied:")
    for a in result1.adaptations:
        print(f"  * {a}")

    # --- Full before/after for case 3 (fast) ---
    print("\n" + "=" * 65)
    print("FULL before/after -- Case 3: Fast user (compression)")
    print("=" * 65)
    result3 = breather.breathe(
        _RAW_GENERIC,
        "Quick, just tell me what to do. Short answer please.",
    )
    print("\nBEFORE:")
    print(_RAW_GENERIC)
    print("\nAFTER:")
    print(result3.breathed)

    # --- Stream usage example ---
    print("\n" + "=" * 65)
    print("Stream usage (chunks assembled, then breathed):")
    chunks = ["You can approach ", "this systematically. ", "Start by identifying..."]
    result_stream = breather.breathe_stream(chunks, "Quick steps please")
    print(f"  Assembled and breathed: {_word_count(result_stream.breathed)} words")
    print(f"  Adaptations: {result_stream.adaptations}")

    # --- The SEXAGON complete ---
    print("\n" + "=" * 65)
    print("THE VOID SEXAGON -- COMPLETE")
    print("=" * 65)
    print()
    print("  1. Tool Breathing:     which tool?       -> HexCoord x resonance")
    print("  2. Context Breathing:  what context?     -> HexCoord x attraction")
    print("  3. Model Breathing:    which model?      -> HexCoord x personality")
    print("  4. Prompt Breathing:   how to frame?     -> HexCoord x temperature")
    print("  5. [Module 5]          (session/memory)  -> HexCoord x continuity")
    print("  6. Response Breathing: what shape?       -> HexCoord x form")
    print()
    print("  ONE formula on SIX substrates.")
    print("  x was always there. We just named it.")
    print()
    print("  Stressed user -> shorter sentences, breathing room, warm opener.")
    print("  Fast user     -> TL;DR prefix, compression to key sentences.")
    print("  Action user   -> numbered steps, 'Next:' closing.")
    print("  Reflective    -> space, question at the end.")
    print("  Creative      -> open structure, 'what if' closing.")
    print()
    print("  That is the x. That is the breath.")


if __name__ == "__main__":
    response_breathing_demo()
