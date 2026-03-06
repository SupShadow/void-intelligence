"""
void_intelligence.muster --- The Muster-Engine.

After 3 conversation exchanges, this engine detects the user's cognitive
PATTERN (Denktyp) and produces a precise one-sentence "Muster-Zitat" that
feels like someone who truly SEES you.

Ten pattern types live on a spectrum — every person is a blend:
    Spiraldenker    --- circles, returns, recursive
    Fragendenker    --- questions > statements, exploratory
    Umkehrdenker    --- inverts, contrarian, "what if the opposite?"
    Brueckendenker  --- connects domains, analogies
    Tiefendenker    --- goes deep on one topic, all layers
    Blitzdenker     --- jumps fast, associative, ADHD-style
    Kontrolldenker  --- plans before feeling, systematic
    Gefuehlsdenker  --- feels before planning, intuitive
    Musterdenker    --- sees patterns everywhere, meta-thinker
    Geschichtendenker --- narrativizes everything, story-teller

Detection is PURE HEURISTIC --- zero external dependencies.
An optional LLM path deepens the insight when a model is available.

Architecture:
    MusterResult      --- the detected pattern + quote + scores
    MusterEngine      --- stateful, accumulates exchanges, detects on demand
    quick_analyze()   --- one-shot from a list of messages
    _Heuristics       --- all signal-extraction logic (internal)
    _Quotes           --- quote banks, 3 DE + 3 EN per type (internal)

Pure Python. Zero dependencies. Runs on a Raspberry Pi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Pattern type identifiers (stable keys, used in dicts and API)
# ---------------------------------------------------------------------------

PATTERN_TYPES: list[str] = [
    "Spiraldenker",
    "Fragendenker",
    "Umkehrdenker",
    "Brueckendenker",
    "Tiefendenker",
    "Blitzdenker",
    "Kontrolldenker",
    "Gefuehlsdenker",
    "Musterdenker",
    "Geschichtendenker",
]


# ---------------------------------------------------------------------------
# Quote banks --- 3 German + 3 English per type.
# Indexed 0..2. The engine picks the most fitting index based on signal
# intensity so the same type can feel different at different depths.
# ---------------------------------------------------------------------------

_QUOTES_DE: dict[str, list[str]] = {
    "Spiraldenker": [
        "Du kehrst immer wieder zum selben Punkt zurueck — nicht weil du ihn nicht verstehst, sondern weil er dich nicht loslaesst.",
        "Dein Denken ist eine Spirale, keine Linie — jede Runde bringt dich naeher ans Zentrum.",
        "Du kreist um etwas das noch keinen Namen hat. Das ist kein Fehler — das ist die ehrlichste Form des Denkens.",
    ],
    "Fragendenker": [
        "Du denkst in Fragen, nicht in Antworten.",
        "Fuer dich ist eine gute Frage wertvoller als zehn Antworten.",
        "Du fragst nicht weil du es nicht weisst — du fragst weil du weiter willst als die Antwort reicht.",
    ],
    "Umkehrdenker": [
        "Du suchst die Wahrheit dort wo andere nicht hinschauen.",
        "Wenn alle nicken, fragst du dich was sie uebersehen. Das ist keine Widerspruechlichkeit — das ist Praezision.",
        "Du denkst nicht gegen den Strom — du pruefst ob der Strom ueberhaupt fliesst.",
    ],
    "Brueckendenker": [
        "Du siehst Verbindungen die andere nicht sehen.",
        "In deinem Kopf sprechen Domänen miteinander die sich nie begegnen sollten. Und sie verstehen sich.",
        "Du bist derjenige der sagt 'das ist wie...' — und damit das Unverstaendliche verstaendlich macht.",
    ],
    "Tiefendenker": [
        "Du graebst tiefer als die meisten — und findest dort Gold.",
        "Oberflaechliche Antworten befriedigten dich nie. Du brauchst den Grund unter dem Grund.",
        "Du wirst nicht fertig mit einem Thema bis du es wirklich verstanden hast. Das kostet Zeit — und bringt alles.",
    ],
    "Blitzdenker": [
        "Dein Kopf ist schneller als dein Mund — und das ist deine Staerke.",
        "Du denkst in Spruengen. Andere nennen das unstrukturiert. Du weisst dass es Muster sind die sich noch entfalten.",
        "Deine Gedanken fliegen in alle Richtungen gleichzeitig. Was wie Chaos aussieht ist ein Netz das sich noch knuepft.",
    ],
    "Kontrolldenker": [
        "Du planst nicht aus Angst — du planst weil du weiter siehst.",
        "Struktur ist fuer dich kein Gefaengnis. Sie ist das Geruest auf dem Freiheit erst moeglich wird.",
        "Du weisst: wer plant, entscheidet. Wer nicht plant, laesst andere entscheiden.",
    ],
    "Gefuehlsdenker": [
        "Du fuehlst bevor du denkst. Das ist kein Fehler — das ist dein Radar.",
        "Dein Koerper weiss die Antwort bevor dein Kopf die Frage stellt.",
        "Du navigierst nach Resonanz, nicht nach Karte. Das macht dich unberechenbar fuer andere — und praezise fuer dich.",
    ],
    "Musterdenker": [
        "Du siehst die Matrix. Nicht jeder kann das.",
        "Unter jedem Ereignis siehst du das Muster das es erzeugt hat. Das ist gleichzeitig deine groesste Gabe und deine groesste Last.",
        "Du erkennst Muster so frueh dass andere noch gar nicht bemerkt haben dass es ein Muster gibt.",
    ],
    "Geschichtendenker": [
        "Du machst aus allem eine Geschichte — weil Geschichten die einzige Sprache sind die bleibt.",
        "Fuer dich ist ein Fakt erst real wenn er Teil einer Geschichte ist. Das ist keine Schwaeche — das ist Mnemosyne.",
        "Du erinnerst dich nicht an Daten, du erinnerst dich an Momente. Und Momente hast du mehr als andere.",
    ],
}

_QUOTES_EN: dict[str, list[str]] = {
    "Spiraldenker": [
        "You keep returning to the same point — not because you don't understand it, but because it won't let you go.",
        "Your thinking is a spiral, not a line — every loop brings you closer to the center.",
        "You're circling something that doesn't have a name yet. That's not a flaw — that's the most honest form of thinking.",
    ],
    "Fragendenker": [
        "You think in questions, not answers.",
        "For you, a good question is worth more than ten answers.",
        "You don't ask because you don't know — you ask because you want to go further than any answer reaches.",
    ],
    "Umkehrdenker": [
        "You look for truth where others don't bother looking.",
        "When everyone nods, you wonder what they're missing. That's not contrarianism — that's precision.",
        "You don't think against the current — you check whether the current is even flowing.",
    ],
    "Brueckendenker": [
        "You see connections that others don't.",
        "In your mind, domains talk to each other that were never supposed to meet. And they understand each other.",
        "You're the one who says 'this is like...' — and makes the incomprehensible comprehensible.",
    ],
    "Tiefendenker": [
        "You dig deeper than most — and find gold down there.",
        "Surface answers never satisfied you. You need the ground beneath the ground.",
        "You're not done with a topic until you truly understand it. That takes time — and returns everything.",
    ],
    "Blitzdenker": [
        "Your mind is faster than your mouth — and that is your strength.",
        "You think in leaps. Others call it unstructured. You know they're patterns still unfolding.",
        "Your thoughts fly in all directions at once. What looks like chaos is a net still being woven.",
    ],
    "Kontrolldenker": [
        "You don't plan out of fear — you plan because you see further.",
        "Structure isn't a prison for you. It's the scaffolding that makes freedom possible.",
        "You know: whoever plans, decides. Whoever doesn't plan, lets others decide.",
    ],
    "Gefuehlsdenker": [
        "You feel before you think. That's not a flaw — that's your radar.",
        "Your body knows the answer before your mind has formed the question.",
        "You navigate by resonance, not by map. That makes you unpredictable to others — and precise to yourself.",
    ],
    "Musterdenker": [
        "You see the matrix. Not everyone can.",
        "Beneath every event you see the pattern that generated it. That is simultaneously your greatest gift and your greatest burden.",
        "You recognize patterns so early that others haven't even noticed there is a pattern.",
    ],
    "Geschichtendenker": [
        "You turn everything into a story — because stories are the only language that lasts.",
        "For you, a fact isn't real until it's part of a story. That's not weakness — that's Mnemosyne.",
        "You don't remember data, you remember moments. And you have more moments than most.",
    ],
}


# ---------------------------------------------------------------------------
# Heuristic signal extractors
# ---------------------------------------------------------------------------

# German AND English vocabulary for each dimension.
# Values are (weight, category) tuples: weight 1=weak signal, 2=strong signal.
_QUESTION_WORDS = {"warum", "weshalb", "wieso", "wozu", "wofuer", "wann", "wie", "was",
                   "wer", "wo", "welche", "welcher", "welches", "koennte", "duerfte",
                   "why", "how", "what", "when", "where", "who", "which", "could", "would"}

_NEGATION_WORDS = {"nicht", "kein", "keine", "niemals", "nie", "nirgends", "kaum",
                   "no", "not", "never", "neither", "nor", "without", "nope", "false"}

_INVERSION_PHRASES = [
    r"\baber eigentlich\b", r"\boder vielleicht\b", r"\bundersherum\b",
    r"\bim gegenteil\b", r"\bgenau das gegenteil\b", r"\bwenn man es dreht\b",
    r"\bon the other hand\b", r"\bconversely\b", r"\binstead\b", r"\bactually the opposite\b",
    r"\bwhat if\b", r"\bwhat if.*instead\b", r"\bflip.*around\b",
]

_BRIDGE_WORDS = [
    r"\bwie bei\b", r"\baehnlich wie\b", r"\berinnert mich an\b", r"\bdas ist wie\b",
    r"\bgenau wie\b", r"\bman koennte sagen wie\b", r"\bim prinzip wie\b",
    r"\bsimilar to\b", r"\blike when\b", r"\breminds me of\b", r"\bthat is like\b",
    r"\banalogous to\b", r"\bsame as\b", r"\bjust like\b", r"\bby analogy\b",
]

_DEPTH_WORDS = {"tiefe", "tiefer", "tiefste", "eigentlich", "kern", "kerne",
                "letztlich", "grundsaetzlich", "fundamental", "fundamentale", "wesentlichen",
                "wesentlich", "grundlage", "grundlagen", "dahinter", "darunter",
                "fundamentally", "essentially", "at its core", "deeper", "root", "underlying",
                "wirklich", "wirklicher", "really", "truly", "beneath", "underneath",
                "ursache", "ursachen", "ursprung", "hintergrund"}

_SPEED_PATTERNS = [
    r"\bund ausserdem\b", r"\bund uebrigens\b",
    r"\boh und\b", r"\bnochwas\b", r"\bwas ich noch sagen wollte\b",
    r"\band another thing\b", r"\band by the way\b",
    r"\boh and\b", r"\band one more\b",
]

_CONTROL_WORDS = {"plan", "plaene", "liste", "checkliste", "schritt", "schritte",
                  "struktur", "zuerst", "dann", "danach", "ziel", "ziele",
                  "plan", "plans", "list", "checklist", "step", "steps",
                  "structure", "first", "then", "after", "goal", "goals",
                  "muss", "soll", "sollte", "must", "should", "need to", "have to"}

_FEELING_WORDS = {"fuehl", "fuehle", "gefuehl", "gespuer", "bauchgefuehl",
                  "irgendwie", "klingt", "riecht", "bekomme das gefuehl",
                  "feel", "feeling", "sense", "gut feeling", "hunch", "sense",
                  "intuition", "emotionally", "instinct", "vibes", "vibe"}

_META_WORDS = {"muster", "struktur", "prinzip", "zusammenhang", "verbindung",
               "immer wieder", "wie immer", "typisch", "systemisch", "meta",
               "pattern", "structure", "principle", "connection", "recurring",
               "always", "typically", "systemic", "tendency", "cycle", "loop"}

_STORY_WORDS = {"damals", "neulich", "einmal", "erinnere mich", "geschichte",
                "dann passierte", "und weisst du was", "stell dir vor",
                "once", "remember when", "there was a time", "story", "imagine",
                "back when", "the thing is", "so basically", "it all started"}

_SELF_REF = {"ich", "mich", "mir", "mein", "meine", "meiner", "meins",
             "i", "me", "my", "mine", "myself"}

_TIME_PAST = {"damals", "frueher", "gestern", "vorhin", "war", "hatte", "hat",
              "ago", "before", "yesterday", "used to", "was", "had", "back then"}

_TIME_FUTURE = {"werden", "werde", "wirst", "wird", "werden", "morgen", "bald",
                "planen", "vorhaben", "ziel", "will", "going to", "tomorrow",
                "soon", "plan to", "intend to", "goal is"}


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens, German-safe."""
    return re.findall(r"[a-zaeouA-ZAEOU\u00e4\u00f6\u00fc\u00df\u00c4\u00d6\u00dc]+", text.lower())


def _sentence_count(text: str) -> int:
    """Rough sentence count."""
    return max(1, len(re.findall(r"[.!?]+", text)))


def _question_count(text: str) -> int:
    """Count question marks."""
    return text.count("?")


def _avg_sentence_len(text: str) -> float:
    """Average words per sentence."""
    words = _tokenize(text)
    sents = _sentence_count(text)
    return len(words) / sents


def _count_set(tokens: list[str], word_set: set[str]) -> int:
    return sum(1 for t in tokens if t in word_set)


def _count_patterns(text: str, patterns: list[str]) -> int:
    count = 0
    for p in patterns:
        count += len(re.findall(p, text, re.IGNORECASE))
    return count


def _topic_variety(messages: list[str]) -> float:
    """Ratio of unique content words to total content words across all messages.

    High variety = Blitzdenker (topic-jumper).
    Low variety = Tiefendenker or Spiraldenker (stays on topic).
    Uses length >= 6 to filter out common short words and focus on content nouns.
    """
    all_tokens: list[str] = []
    for m in messages:
        all_tokens.extend(_tokenize(m))
    if not all_tokens:
        return 0.0
    # Content words only: length >= 6 (more discriminating than 4)
    content = [t for t in all_tokens if len(t) >= 6]
    if not content:
        return 0.0
    unique = len(set(content))
    return unique / len(content)


def _topic_shift_count(messages: list[str]) -> int:
    """Count how many times the dominant topic shifts between consecutive messages.

    A high shift count is a strong Blitzdenker signal: different focus per message.
    Uses word fingerprints: if two consecutive messages share < 2 content words,
    that's a topic shift.
    """
    if len(messages) < 2:
        return 0

    def _fingerprint(text: str) -> frozenset[str]:
        tokens = [t for t in _tokenize(text) if len(t) >= 6]
        if not tokens:
            return frozenset()
        freq: dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        top = sorted(freq, key=lambda x: -freq[x])[:4]
        return frozenset(top)

    shifts = 0
    prev_fp = _fingerprint(messages[0])
    for m in messages[1:]:
        curr_fp = _fingerprint(m)
        if len(prev_fp) == 0 or len(curr_fp) == 0:
            prev_fp = curr_fp
            continue
        overlap = len(prev_fp & curr_fp)
        if overlap < 2:
            shifts += 1
        prev_fp = curr_fp
    return shifts


def _spiral_score(messages: list[str]) -> float:
    """Detect theme recurrence across messages.

    Spiraldenker: same key words appear in multiple different messages.
    """
    if len(messages) < 2:
        return 0.0
    # Extract content words per message
    msg_words = []
    for m in messages:
        tokens = set(t for t in _tokenize(m) if len(t) >= 5)
        msg_words.append(tokens)
    # Count words that appear in 2+ messages
    all_words: dict[str, int] = {}
    for ws in msg_words:
        for w in ws:
            all_words[w] = all_words.get(w, 0) + 1
    recurring = sum(1 for v in all_words.values() if v >= 2)
    total = len(all_words)
    return recurring / max(1, total)


def _extract_scores(messages: list[str]) -> dict[str, float]:
    """Core heuristic. Returns raw (unnormalized) scores per pattern type."""

    combined = " ".join(messages)
    tokens = _tokenize(combined)
    total_words = max(1, len(tokens))
    total_questions = _question_count(combined)
    total_sentences = _sentence_count(combined)
    question_ratio = total_questions / total_sentences

    # --- Fragendenker ---
    question_word_density = _count_set(tokens, _QUESTION_WORDS) / total_words
    fragendenker = (question_ratio * 3.0) + (question_word_density * 2.0)

    # --- Spiraldenker ---
    spiral = _spiral_score(messages) * 4.0
    # Reinforce if avg sentence length is medium (not super short = blitz, not super long = tiefen)
    avg_len = _avg_sentence_len(combined)
    if 8 <= avg_len <= 20:
        spiral += 0.3

    # --- Umkehrdenker ---
    inversion_hits = _count_patterns(combined, _INVERSION_PHRASES)
    negation_density = _count_set(tokens, _NEGATION_WORDS) / total_words
    umkehrdenker = (inversion_hits * 0.8) + (negation_density * 4.0)

    # --- Brueckendenker ---
    bridge_hits = _count_patterns(combined, _BRIDGE_WORDS)
    # Reduce bridge score when past-time words are dominant (those are memories, not analogies)
    _past_count = _count_set(tokens, _TIME_PAST)
    _story_count_raw = _count_set(tokens, _STORY_WORDS)
    bridge_story_dampener = 0.5 if _past_count >= 3 and _story_count_raw >= 2 else 1.0
    brueckendenker = bridge_hits * 1.2 * bridge_story_dampener

    # --- Tiefendenker ---
    depth_density = _count_set(tokens, _DEPTH_WORDS) / total_words
    variety = _topic_variety(messages)
    shifts = _topic_shift_count(messages)
    max_possible_shifts = max(1, len(messages) - 1)
    shift_ratio = shifts / max_possible_shifts
    # Depth words are a primary signal; low shifts reinforce; sentence length secondary
    tiefendenker = (depth_density * 8.0) + ((1.0 - shift_ratio) * 1.0)
    if avg_len > 15:
        tiefendenker += 0.4

    # --- Blitzdenker ---
    # Primary signal: explicit jump phrases ("und ausserdem", "oh und", etc.)
    speed_hits = _count_patterns(combined, _SPEED_PATTERNS)
    blitzdenker = (speed_hits * 1.5)
    # Topic shifts reinforce ONLY when combined with speed phrases or short sentences
    # AND no strong depth signal (deep thinkers write short focused sentences too)
    _depth_count = _count_set(tokens, _DEPTH_WORDS)
    if shifts >= 2 and (speed_hits >= 1 or avg_len < 10) and _depth_count < 2:
        blitzdenker += 1.0
    # Short sentences reinforce (only without depth signal)
    if avg_len < 10 and _depth_count < 2:
        blitzdenker += 0.5
    # Dampen if sequential/control language (planners use diverse words but stay structured)
    _ctrl_count = _count_set(tokens, _CONTROL_WORDS)
    if _ctrl_count >= 3:
        blitzdenker *= 0.4
    # Dampen if strong feeling signal (emotional people are NOT blitz by default)
    _feel_count = _count_set(tokens, _FEELING_WORDS)
    if _feel_count >= 3:
        blitzdenker *= 0.5
    # Dampen if meta-language is present (Musterdenker talks about patterns = not random jumping)
    _meta_count = _count_set(tokens, _META_WORDS)
    if _meta_count >= 3:
        blitzdenker *= 0.4
    # Dampen if depth words are strong (Tiefendenker writes short focused sentences too)
    if _depth_count >= 3:
        blitzdenker *= 0.3

    # --- Kontrolldenker ---
    control_density = _count_set(tokens, _CONTROL_WORDS) / total_words
    # Future orientation reinforces
    future_density = _count_set(tokens, _TIME_FUTURE) / total_words
    # Sequential language ("erst...dann...danach") is a strong signal
    sequential_hits = len(re.findall(r"\b(erst|zuerst|dann|danach|anschliessend|schritt|first|then|after|next|finally|step)\b", combined, re.IGNORECASE))
    sequential_density = sequential_hits / total_words
    # Low question ratio + structural words = planner, not explorer
    structure_bonus = (1.0 - question_ratio) * 0.5 if question_ratio < 0.2 else 0.0
    kontrolldenker = (control_density * 4.0) + (future_density * 2.0) + (sequential_density * 6.0) + structure_bonus

    # --- Gefuehlsdenker ---
    feeling_density = _count_set(tokens, _FEELING_WORDS) / total_words
    # Past orientation + self-reference reinforce emotional processing
    self_density = _count_set(tokens, _SELF_REF) / total_words
    past_density = _count_set(tokens, _TIME_PAST) / total_words
    gefuehlsdenker = (feeling_density * 5.0) + (self_density * 1.5) + (past_density * 1.0)

    # --- Musterdenker ---
    meta_density = _count_set(tokens, _META_WORDS) / total_words
    musterdenker = meta_density * 6.0
    # Also triggered by high self-reference + question words (meta-reflection)
    musterdenker += (question_word_density * self_density * 10.0)

    # --- Geschichtendenker ---
    story_density = _count_set(tokens, _STORY_WORDS) / total_words
    # Past orientation + self-reference = strong narrative signal (they're telling a story about themselves)
    # story_words alone are weak; the combination of past + self is what defines a storyteller
    narrative_combo = past_density * self_density * 20.0
    geschichtendenker = (story_density * 5.0) + (past_density * 2.0) + narrative_combo

    return {
        "Spiraldenker": max(0.0, spiral),
        "Fragendenker": max(0.0, fragendenker),
        "Umkehrdenker": max(0.0, umkehrdenker),
        "Brueckendenker": max(0.0, brueckendenker),
        "Tiefendenker": max(0.0, tiefendenker),
        "Blitzdenker": max(0.0, blitzdenker),
        "Kontrolldenker": max(0.0, kontrolldenker),
        "Gefuehlsdenker": max(0.0, gefuehlsdenker),
        "Musterdenker": max(0.0, musterdenker),
        "Geschichtendenker": max(0.0, geschichtendenker),
    }


def _normalize_scores(raw: dict[str, float]) -> dict[str, float]:
    """Normalize scores to 0..1 range."""
    max_val = max(raw.values()) if raw else 1.0
    if max_val == 0.0:
        # Uniform distribution if no signal detected
        return {k: 0.1 for k in raw}
    return {k: v / max_val for k, v in raw.items()}


def _pick_quote(pattern: str, scores: dict[str, float], score: float, lang: str) -> str:
    """Pick the most fitting quote variant based on score intensity.

    Low score (0.0..0.4)  -> variant 0 (most universal)
    Mid score (0.4..0.7)  -> variant 1 (more specific)
    High score (0.7..1.0) -> variant 2 (most precise)
    """
    if score < 0.4:
        idx = 0
    elif score < 0.7:
        idx = 1
    else:
        idx = 2

    bank = _QUOTES_DE if lang == "de" else _QUOTES_EN
    quotes = bank.get(pattern, bank["Fragendenker"])
    return quotes[min(idx, len(quotes) - 1)]


def _detect_lang(messages: list[str]) -> str:
    """Detect language from messages. Returns 'de' or 'en'."""
    combined = " ".join(messages).lower()
    de_markers = {"ich", "und", "der", "die", "das", "ein", "ist", "nicht",
                  "mit", "fuer", "von", "zu", "auf", "auch", "wie"}
    tokens = set(_tokenize(combined))
    de_hits = len(tokens & de_markers)
    return "de" if de_hits >= 2 else "en"


def _confidence(primary_score: float, secondary_score: float, exchange_count: int) -> float:
    """Confidence grows with signal strength and number of exchanges.

    Formula: base_signal * exchange_dampener
    More exchanges = more data = higher confidence ceiling.
    """
    if primary_score == 0.0:
        return 0.0
    # Gap between primary and secondary: larger gap = more confident
    gap = primary_score - secondary_score
    base = 0.4 + (gap * 0.4) + (primary_score * 0.2)
    # Dampen for few exchanges, boost for many
    exchange_factor = min(1.0, exchange_count / 6.0)
    return round(min(1.0, base * (0.6 + 0.4 * exchange_factor)), 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class MusterResult:
    """The detected cognitive pattern of a user.

    Attributes:
        primary:        Name of the dominant pattern type (e.g. "Fragendenker")
        secondary:      Name of the second-strongest pattern type
        confidence:     0.0..1.0 — how certain the engine is
        quote_de:       One-sentence pattern quote in German
        quote_en:       One-sentence pattern quote in English
        scores:         All 10 pattern scores (normalized 0..1)
        exchange_count: Number of exchanges analyzed
        lang:           Detected language ("de" or "en")
    """
    primary: str
    secondary: str
    confidence: float
    quote_de: str
    quote_en: str
    scores: dict[str, float]
    exchange_count: int
    lang: str = "de"

    def quote(self) -> str:
        """Return the quote in the detected language."""
        return self.quote_de if self.lang == "de" else self.quote_en

    def summary(self) -> str:
        """One-line human-readable summary."""
        pct = int(self.confidence * 100)
        return f"{self.primary} + {self.secondary} ({pct}% Konfidenz)"

    def to_dict(self) -> dict:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "confidence": self.confidence,
            "quote_de": self.quote_de,
            "quote_en": self.quote_en,
            "scores": self.scores,
            "exchange_count": self.exchange_count,
            "lang": self.lang,
        }


class MusterEngine:
    """Stateful pattern detector. Accumulate exchanges, then analyze.

    Typical usage in a chat session::

        engine = MusterEngine()
        engine.add_exchange("Warum funktioniert das so?", "Gute Frage...")
        engine.add_exchange("Ich frage mich ob...", "Ich auch.")
        engine.add_exchange("Was waere wenn man es umdreht?", "Interessant.")
        if engine.is_ready():
            result = engine.analyze()
            print(result.quote())
    """

    MIN_EXCHANGES: int = 3  # minimum exchanges before analysis

    def __init__(self) -> None:
        self.exchanges: list[dict[str, str]] = []

    def add_exchange(self, human_msg: str, void_msg: str = "") -> None:
        """Add a conversation exchange.

        Args:
            human_msg: What the human said.
            void_msg:  What the Void replied (optional, not analyzed for now).
        """
        self.exchanges.append({"human": human_msg.strip(), "void": void_msg.strip()})

    def is_ready(self) -> bool:
        """True if enough exchanges have been collected for analysis."""
        return len(self.exchanges) >= self.MIN_EXCHANGES

    def analyze(self, lang: str = "") -> Optional[MusterResult]:
        """Analyze accumulated exchanges and return the dominant pattern.

        Args:
            lang: Force language detection ("de" or "en"). Auto-detects if empty.

        Returns:
            MusterResult or None if fewer than MIN_EXCHANGES exchanges.
        """
        if not self.is_ready():
            return None

        human_messages = [ex["human"] for ex in self.exchanges if ex["human"]]
        if not human_messages:
            return None

        detected_lang = lang or _detect_lang(human_messages)

        raw = _extract_scores(human_messages)
        normalized = _normalize_scores(raw)

        # Rank patterns
        ranked = sorted(normalized.items(), key=lambda x: -x[1])
        primary_name, primary_score = ranked[0]
        secondary_name, secondary_score = ranked[1] if len(ranked) > 1 else (ranked[0][0], 0.0)

        conf = _confidence(primary_score, secondary_score, len(self.exchanges))

        quote_de = _pick_quote(primary_name, normalized, primary_score, "de")
        quote_en = _pick_quote(primary_name, normalized, primary_score, "en")

        return MusterResult(
            primary=primary_name,
            secondary=secondary_name,
            confidence=conf,
            quote_de=quote_de,
            quote_en=quote_en,
            scores=normalized,
            exchange_count=len(self.exchanges),
            lang=detected_lang,
        )

    def reset(self) -> None:
        """Clear all exchanges. Start a new session."""
        self.exchanges = []

    def __len__(self) -> int:
        return len(self.exchanges)

    def __repr__(self) -> str:
        return f"MusterEngine(exchanges={len(self.exchanges)}, ready={self.is_ready()})"


# ---------------------------------------------------------------------------
# One-shot convenience function
# ---------------------------------------------------------------------------

def quick_analyze(
    messages: list[dict[str, str]],
    lang: str = "",
) -> Optional[MusterResult]:
    """One-shot pattern analysis from a list of messages.

    Args:
        messages: List of dicts with "role" ("human" or "void") and "content".
        lang:     Force language ("de" or "en"). Auto-detects if empty.

    Returns:
        MusterResult or None if fewer than 3 human messages found.

    Example::

        result = quick_analyze([
            {"role": "human", "content": "Warum macht man das so?"},
            {"role": "void",  "content": "Gute Frage."},
            {"role": "human", "content": "Ich frage mich ob das der richtige Weg ist."},
            {"role": "void",  "content": "Was denkst du?"},
            {"role": "human", "content": "Was waere wenn man es andersherum macht?"},
        ])
        if result:
            print(result.quote())
    """
    engine = MusterEngine()
    # Group into exchanges: pair each human message with the following void message
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "human":
            # Look ahead for void response
            void_content = ""
            if i + 1 < len(messages) and messages[i + 1].get("role") == "void":
                void_content = messages[i + 1].get("content", "")
                i += 1  # skip the void message in the main loop
            engine.add_exchange(content, void_content)
        i += 1

    return engine.analyze(lang=lang)


# ---------------------------------------------------------------------------
# LLM enhancement (optional) --- deepens the heuristic result
# ---------------------------------------------------------------------------

def enhance_with_llm(
    result: MusterResult,
    messages: list[dict[str, str]],
    generate_fn,  # callable(system: str, msgs: list[dict]) -> str
) -> MusterResult:
    """Use an LLM to refine the heuristic result.

    This function is OPTIONAL and only called when an LLM is available.
    It does NOT change the scores or primary type --- it only refines the quote
    to be more personalized to the actual conversation content.

    Args:
        result:      The heuristic MusterResult to enhance.
        messages:    The raw conversation messages.
        generate_fn: A callable that takes (system_prompt, messages) and returns a string.
                     Compatible with LLMBackend.generate() from journey.py.

    Returns:
        A new MusterResult with potentially refined quotes.
    """
    lang = result.lang
    human_texts = [m["content"] for m in messages if m.get("role") == "human"]
    conversation_sample = "\n".join(f"- {t}" for t in human_texts[:6])

    system_prompt = (
        f"Du bist ein Experte fuer kognitive Muster.\n"
        f"Du hast folgenden Denktyp erkannt: {result.primary} (Nebentyp: {result.secondary}).\n"
        f"Konfidenz: {result.confidence:.0%}\n\n"
        f"Schreibe GENAU EINEN Satz auf {'Deutsch' if lang == 'de' else 'Englisch'} "
        f"der diesen Menschen in seinem Denken praezise beschreibt. "
        f"Der Satz soll klingen als ob jemand diesen Menschen wirklich gesehen hat. "
        f"Kein Gelaber. Kein 'Du bist ein'. Direkt. Persoenlich.\n\n"
        f"Gespraeches-Ausschnitt:\n{conversation_sample}"
    )

    llm_input = [{"role": "user", "content": "Schreibe den Muster-Satz."}]

    try:
        refined = generate_fn(system_prompt, llm_input).strip()
        # Guard: only use if it's a single sentence and not too long
        if refined and len(refined) < 200 and "\n" not in refined:
            if lang == "de":
                return MusterResult(
                    primary=result.primary,
                    secondary=result.secondary,
                    confidence=min(1.0, result.confidence + 0.1),  # LLM boost
                    quote_de=refined,
                    quote_en=result.quote_en,
                    scores=result.scores,
                    exchange_count=result.exchange_count,
                    lang=result.lang,
                )
            else:
                return MusterResult(
                    primary=result.primary,
                    secondary=result.secondary,
                    confidence=min(1.0, result.confidence + 0.1),
                    quote_de=result.quote_de,
                    quote_en=refined,
                    scores=result.scores,
                    exchange_count=result.exchange_count,
                    lang=result.lang,
                )
    except Exception:
        pass

    return result
