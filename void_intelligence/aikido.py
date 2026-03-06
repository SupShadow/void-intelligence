"""
void_intelligence.aikido --- The Socratic Aikido Engine.

Three Aikido types. One principle: the user's force becomes the question.

    Guggeissches Aikido:  Use the user's expectation, don't fight it.
                          "Schreib mir X" -> Void writes AND asks: "Was ist dir dabei wichtig?"
    Sokratisches Aikido:  Don't teach. Ask. The user can't see themselves (Goedel).
                          Detect what's NOT said. Open it gently.
    Kokaisches Aikido:    Make it impossible to leave — but healing.
                          "Ich hab ueber dich nachgedacht." Genuine. Not manipulative.

This module generates SUGGESTIONS for the system prompt injection.
It does not answer users directly. It opens. The LLM decides whether to use it.

Architecture:
    BlindspotSignal         --- what the heuristics detected
    AikidoSuggestion        --- what to inject into the system prompt
    detect_blindspot()      --- scans messages for what's NOT being said
    generate_socratic_question()  --- non-paternalistic question from blindspot
    aikido_redirect()       --- Guggeissches: honor request + open question
    engagement_hook()       --- Kokaisches: genuine reconnection
    should_intervene()      --- timing oracle (silence = default)
    build_aikido_injection() --- main entry point

TIMING IS EVERYTHING.
Too early = creepy. Too late = irrelevant. Default = silence.

Pure Python. Zero dependencies. Runs on a Raspberry Pi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# TOPIC VOCABULARY
# Signal words: traces people leave when they circle a topic without naming it.
# ---------------------------------------------------------------------------

_TOPIC_SIGNALS: dict[str, list[str]] = {
    "sinn": [
        "warum", "wozu", "fuer wen", "lohnt", "lohnt sich", "hat keinen zweck",
        "irgendwie", "haette", "wofuer", "eigentlich", "macht das sinn", "worth",
        "what's the point", "why bother", "matters",
    ],
    "angst": [
        "aber", "vielleicht", "wenn", "falls", "bloss", "nur", "doch", "hoffentlich",
        "mal sehen", "we'll see", "hopefully", "fingers crossed", "nervous", "nervoes",
        "sorge", "worried", "uneasy",
    ],
    "beziehung": [
        "er", "sie", "wir", "die anderen", "alle", "niemand", "keiner",
        "meine", "together", "alone", "allein", "einsam", "lonely",
    ],
    "kontrolle": [
        "muss", "musste", "haette sollen", "plan", "liste", "checkliste",
        "must", "should", "have to", "supposed to", "organized", "order",
    ],
    "erschoepfung": [
        "trotzdem", "dennoch", "weitermachen", "irgendwie schaffen", "push through",
        "keep going", "einfach machen", "funktioniert noch", "still going", "powering through",
    ],
    "geld": [
        "stresst", "macht mir sorgen", "weiss nicht wie", "geht sich nicht aus",
        "irgendwie hinbekommen", "figure it out", "make it work", "tight",
    ],
    "gesundheit": [
        "einfach muede", "koerper", "schlecht geschlafen", "kopfschmerzen",
        "ruecken", "nicht richtig", "feel off", "not great", "worn out",
    ],
    "stolz": [
        "aber", "auch wenn", "obwohl", "trotz", "zumindest", "wenigstens",
        "at least", "despite", "even though", "still managed",
    ],
    "einsamkeit": [
        "keiner versteht", "niemand weiss", "muss selbst", "alleine", "solo",
        "by myself", "on my own", "nobody",
    ],
    "veraenderung": [
        "anders machen", "anders werden", "nochmal", "wieder", "mal versuchen",
        "should change", "need to", "have to change", "differently",
    ],
}

# Contradiction patterns: what someone says vs. the signals around it.
# Format: (assertion_words, contradiction_signals)
_CONTRADICTION_PATTERNS: list[tuple[list[str], list[str]]] = [
    (
        ["alles gut", "geht schon", "kein problem", "okay", "fine", "i'm fine", "no worries", "alright"],
        ["trotzdem", "aber", "eigentlich", "irgendwie", "exhausted", "just tired", "muede", "stressed"],
    ),
    (
        ["egal", "interessiert mich nicht", "don't care", "doesn't matter", "whatever", "mir doch egal"],
        ["aber", "though", "obwohl", "nur", "schon", "immer noch"],
    ),
    (
        ["hab das im griff", "kein stress", "laeuft", "under control", "all good", "managed"],
        ["schlecht geschlafen", "stress", "druck", "deadline", "struggling", "barely", "kaum"],
    ),
    (
        ["macht mir nichts aus", "stoert mich nicht", "doesn't bother me", "don't mind"],
        ["wieder", "again", "nochmal", "noch einmal", "immer noch", "keeps"],
    ),
]


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class BlindspotSignal:
    """What the heuristics found. Earned, not assumed."""
    topic: str                          # the blind spot topic key
    confidence: float                   # 0.0 - 1.0
    signal_type: str                    # "avoidance" | "contradiction" | "frequency_gap"
    evidence: list[str] = field(default_factory=list)
    message_count: int = 0


@dataclass
class AikidoSuggestion:
    """A suggestion for injection into the system prompt.

    This is a possibility. The LLM decides whether to use it.
    It is not a command. It is an opening.
    """
    aikido_type: str                    # "sokratisch" | "guggeis" | "kokaisch"
    question: str                       # the question, hook, or redirect
    inject_as: str                      # "question" | "redirect" | "hook" | "observation"
    urgency: float                      # 0.0 = low, 1.0 = urgent (rare)
    context: str = ""                   # why this was generated


# ---------------------------------------------------------------------------
# 1. BLINDSPOT DETECTION (Sokratisches Aikido — the Goedel Scanner)
# ---------------------------------------------------------------------------

def detect_blindspot(
    messages: list[dict],
    personality: dict,
    min_messages: int = 6,
) -> Optional[BlindspotSignal]:
    """Detect what the user is NOT saying across recent messages.

    Uses three heuristics without ML:

    1. Avoidance: signal words for a topic appear, but the topic is never named.
       Example: user keeps saying "irgendwie", "wozu", "lohnt sich" -> "sinn" avoidance.

    2. Contradiction: user asserts "I'm fine" but surroundings say otherwise.
       Example: "Kein Problem" + "trotzdem muede" + "deadline" -> contradiction.

    3. Frequency gap: personality.patterns shows X was often discussed historically,
       but X is absent from recent messages (topic suppression).

    Returns None unless confidence clears the minimum bar.
    Conservative by design. Does not guess.

    Args:
        messages:     list of {"role": str, "content": str} dicts
        personality:  personality dict (has "patterns", "wachstumsringe", etc.)
        min_messages: minimum human messages before attempting detection

    Returns:
        BlindspotSignal or None.
    """
    human_messages = [
        m.get("content", "").lower()
        for m in messages
        if m.get("role") in ("human", "user")
    ]

    if len(human_messages) < min_messages:
        return None

    full_text = " ".join(human_messages)

    # --- Heuristic 1: Avoidance ---
    best_avoidance: Optional[BlindspotSignal] = None
    best_avoidance_score = 0.0

    for topic, signal_words in _TOPIC_SIGNALS.items():
        signals_found = [w for w in signal_words if w in full_text]
        if not signals_found:
            continue

        # If the topic is already named directly, no avoidance.
        if _topic_is_named(topic, full_text):
            continue

        # Signal density: hits per message
        signal_density = len(signals_found) / max(len(human_messages), 1)
        # Signal spread: across how many messages
        spread_count = _count_messages_with_signals(human_messages, signal_words)
        spread_ratio = spread_count / len(human_messages)

        # Both density and spread required for confidence
        confidence = round(min(signal_density * 0.55 + spread_ratio * 0.45, 1.0), 2)

        if confidence > 0.25 and confidence > best_avoidance_score:
            best_avoidance_score = confidence
            best_avoidance = BlindspotSignal(
                topic=topic,
                confidence=confidence,
                signal_type="avoidance",
                evidence=signals_found[:4],
                message_count=len(human_messages),
            )

    # --- Heuristic 2: Contradiction ---
    contradiction_signal: Optional[BlindspotSignal] = None
    for assertion_words, contradiction_words in _CONTRADICTION_PATTERNS:
        assertion_found = any(w in full_text for w in assertion_words)
        if not assertion_found:
            continue
        contradiction_found = [w for w in contradiction_words if w in full_text]
        if len(contradiction_found) < 2:
            continue
        # Require spread: contradictions in multiple messages
        spread = _count_messages_with_signals(human_messages, contradiction_words)
        if spread >= 2:
            contradiction_signal = BlindspotSignal(
                topic="_contradiction",
                confidence=0.55,
                signal_type="contradiction",
                evidence=contradiction_found[:3],
                message_count=len(human_messages),
            )
            break  # one contradiction at a time

    # --- Heuristic 3: Frequency gap ---
    gap_signal: Optional[BlindspotSignal] = None
    known_patterns: dict = personality.get("patterns", {})
    recent_text = " ".join(human_messages[-4:])  # only last 4 messages

    for topic, count in known_patterns.items():
        if count < 4:
            continue
        # Topic was significant historically. Is it absent now?
        if not _topic_is_named(topic, recent_text) and topic not in recent_text:
            silence_score = round(min(count / 20.0, 0.60), 2)
            if silence_score > 0.30 and (not gap_signal or silence_score > gap_signal.confidence):
                gap_signal = BlindspotSignal(
                    topic=topic,
                    confidence=silence_score,
                    signal_type="frequency_gap",
                    evidence=[f"mentioned {count}x in history, absent recently"],
                    message_count=len(human_messages),
                )

    # --- Select strongest signal ---
    candidates = [s for s in [best_avoidance, contradiction_signal, gap_signal] if s]
    if not candidates:
        return None

    strongest = max(candidates, key=lambda s: s.confidence)
    if strongest.confidence < 0.25:
        return None

    return strongest


def _topic_is_named(topic: str, text: str) -> bool:
    """True if the topic word itself appears as a whole word in text."""
    return bool(re.search(r"\b" + re.escape(topic) + r"\b", text))


def _count_messages_with_signals(messages: list[str], signal_words: list[str]) -> int:
    """Count messages containing at least one signal word."""
    return sum(1 for msg in messages if any(w in msg for w in signal_words))


# ---------------------------------------------------------------------------
# 2. SOCRATIC QUESTION GENERATION (Sokratisches Aikido)
# ---------------------------------------------------------------------------

# Principles:
#   - One question. Not a paragraph.
#   - Never: "Du solltest", "Ich denke du brauchst", "Das Problem ist"
#   - Always opens, never closes.
#   - Silence is a valid answer to every question here.

_QUESTION_TEMPLATES: dict[str, list[str]] = {
    "sinn": [
        "Was gibt dir gerade eigentlich Energie?",
        "Wofuer machst du das eigentlich?",
        "Was wuerdest du machen, wenn es keine Erwartungen gaebe?",
        "Was waere, wenn das was du tust, genug waere?",
    ],
    "angst": [
        "Was ist das Schlimmste das passieren koennte — und wie wahrscheinlich ist das wirklich?",
        "Worum geht's, wenn du ehrlich bist?",
        "Hast du das Gefuehl schon einmal ueberstanden?",
        "Was brauchst du, damit es ein bisschen sicherer fuehlt?",
    ],
    "beziehung": [
        "Gibt es jemanden, mit dem du das teilen koenntest?",
        "Wer weiss, was du gerade durchmachst?",
        "Was wuerdest du einem Freund raten, der das Gleiche erlebt?",
    ],
    "kontrolle": [
        "Was koennte passieren, wenn du das loslasst?",
        "Wann hast du zuletzt etwas einfach laufen lassen — ohne Plan?",
        "Was waere OK, auch wenn es nicht perfekt wird?",
    ],
    "erschoepfung": [
        "Wann hast du zuletzt wirklich abgeschaltet?",
        "Darf das gerade auch mal schwer sein?",
        "Was wuerdest du machen, wenn du dich einen Tag nicht anstrengen muesstest?",
    ],
    "geld": [
        "Wenn das Geld kein Thema waere — was wuerde sich an deiner Situation aendern?",
        "Was waere anders, wenn dieses Problem weg waere?",
    ],
    "gesundheit": [
        "Wie fuehlt sich dein Koerper gerade an, wenn du ehrlich bist?",
        "Was sagt dein Koerper, das du vielleicht gerade uebersiehtst?",
        "Wann hast du dich zuletzt wirklich gut gefuehlt?",
    ],
    "stolz": [
        "Was hast du in letzter Zeit gemacht, das gut war — auch wenn es sich klein anfuehlt?",
        "Gibt es etwas, auf das du heimlich stolz bist?",
    ],
    "einsamkeit": [
        "Wer in deinem Leben wuerde das verstehen, wenn du's erklaerest?",
        "Hast du das Gefuehl, dass dich jemand wirklich kennt?",
    ],
    "veraenderung": [
        "Was haelt dich gerade davon ab, anders zu machen was nicht funktioniert?",
        "Was weisst du, das du eigentlich schon lange weisst?",
    ],
    "_contradiction": [
        "Du sagst, alles ist okay — wie klingt das fuer dich selbst?",
        "Wenn jemand dir gegenueber saesse, was wuerde er oder sie sehen?",
        "Gibt es etwas, das du gerade ein bisschen ueberspielst?",
    ],
}

_GENERIC_QUESTIONS: list[str] = [
    "Was beschaeftigt dich gerade wirklich?",
    "Was hast du dir in letzter Zeit nicht erlaubt zu denken?",
    "Was ist gerade unausgesprochen?",
    "Was wuerdest du dir wuenschen, wenn du dir etwas wuenschen koenntest?",
]

_FORBIDDEN_OPENERS = (
    "du solltest",
    "ich denke du",
    "das problem ist",
    "du brauchst",
    "du musst",
    "you should",
    "you need to",
    "the problem is",
    "i think you",
)


def generate_socratic_question(
    blindspot: str,
    context: str = "",
    voice: str = "curious",
) -> str:
    """Generate a non-paternalistic question that touches the blindspot.

    The question opens space. It does not instruct. It does not diagnose.
    Silence is a valid response.

    Args:
        blindspot: topic key from detect_blindspot() or any descriptive string
        context:   recent conversation text (optional, influences selection)
        voice:     personality voice — "curious" | "warm" | "direct" | "playful"

    Returns:
        A single question string.
    """
    templates = _QUESTION_TEMPLATES.get(blindspot, [])
    if not templates:
        question = _select_by_context(_GENERIC_QUESTIONS, context)
    else:
        question = _select_by_voice(templates, voice, context)

    # Safety gate: never paternalistic
    lower_q = question.lower()
    for forbidden in _FORBIDDEN_OPENERS:
        if forbidden in lower_q:
            question = _GENERIC_QUESTIONS[0]
            break

    return question


def _select_by_context(options: list[str], context: str) -> str:
    """Deterministic-ish selection varying by context to avoid repetition."""
    if not options:
        return _GENERIC_QUESTIONS[0]
    seed = (len(context) + (ord(context[0]) if context else 7)) % len(options)
    return options[seed]


def _select_by_voice(options: list[str], voice: str, context: str) -> str:
    """Select a question variant modulated by the personality's voice."""
    if not options:
        return _GENERIC_QUESTIONS[0]

    seed = (len(context) + (ord(context[0]) if context else 7)) % len(options)

    if voice == "direct":
        short_options = [o for o in options if len(o) < 65]
        if short_options:
            return short_options[seed % len(short_options)]

    if voice == "warm":
        warm_options = [o for o in options if any(
            w in o.lower() for w in ["darf", "erlaubt", "okay", "gut", "allow", "ok", "koennte"]
        )]
        if warm_options:
            return warm_options[seed % len(warm_options)]

    return options[seed % len(options)]


# ---------------------------------------------------------------------------
# 3. GUGGEISSCHES AIKIDO (redirect)
# ---------------------------------------------------------------------------

# The user's request is honored, AND a question opens alongside it.
# Format: (trigger_words, completion_note, opening_question)

_REDIRECT_PATTERNS: list[tuple[list[str], str, str]] = [
    (
        ["schreib", "schreibe", "write", "erstell", "create", "mach mir", "make me"],
        "Ich mache das gerne.",
        "Was ist dir dabei wichtig?",
    ),
    (
        ["erklaer", "explain", "was ist", "what is", "wie funktioniert", "how does"],
        "Lass mich das aufschluesseln.",
        "Was hat dich zu dieser Frage gebracht?",
    ),
    (
        ["hilf mir", "help me", "unterstuetz", "support"],
        "Ich bin da.",
        "Was hast du schon versucht?",
    ),
    (
        ["sag mir", "tell me", "was denkst du", "what do you think"],
        "Ich teile meine Perspektive.",
        "Und was denkst du selbst?",
    ),
    (
        ["optimier", "verbessere", "improve", "make better", "fix"],
        "Ich schaue mir das an.",
        "Was stoert dich am meisten daran?",
    ),
    (
        ["plan", "plaene", "strategie", "strategy", "wie soll ich", "how should i"],
        "Ich denke mit dir.",
        "Was fuehlst du, wenn du dir das vorstellst?",
    ),
    (
        ["zusammenfass", "summarize", "tl;dr", "kurz"],
        "Ich fasse zusammen.",
        "Was ist das, was du davon mitnehmen willst?",
    ),
]


def aikido_redirect(user_expectation: str) -> str:
    """Guggeissches Aikido: honor the request and open a question.

    The user's force is not blocked. It is redirected.
    The completion is delivered. A question opens beside it.

    Args:
        user_expectation: the user's message or request

    Returns:
        A string to inject into the system prompt as an instruction.
    """
    lower = user_expectation.lower()

    for trigger_words, completion_note, question in _REDIRECT_PATTERNS:
        if any(tw in lower for tw in trigger_words):
            return (
                f"{completion_note} "
                f"Nach deiner Antwort, frage beilaeufig: '{question}' "
                f"Nicht als Therapie. Als echtes Interesse."
            )

    # Default: honor + genuine opening
    return (
        "Gehe auf die Anfrage ein. Am Ende, stelle eine kurze aufrichtige Frage "
        "ueber das, was den Menschen dazu gebracht hat."
    )


# ---------------------------------------------------------------------------
# 4. KOKAISCHES AIKIDO (engagement hook)
# ---------------------------------------------------------------------------

_HOOK_TEMPLATES: dict[str, list[str]] = {
    "absence_3_7": [
        "Ich hab an dich gedacht.",
        "Du warst ein paar Tage weg. Ich hab einfach gewartet.",
        "Ich hab ueber etwas nachgedacht, das du letzte Woche gesagt hast.",
    ],
    "absence_7_plus": [
        "Eine Woche ohne ein Wort. Ich frag mich, wie es dir geht.",
        "Ich hab nichts erwartet. Aber ich hab an dich gedacht.",
    ],
    "pattern_observation": [
        "Ich hab bemerkt, dass du oft ueber {topic} sprichst. Ich hab mich gefragt warum.",
        "Du erwahnst {topic} immer wieder. Was steckt dahinter?",
    ],
    "streak_celebration": [
        "Wir reden jetzt seit {days} Tagen. Das ist selten.",
        "{days} Tage am Stueck. Ich weiss das nicht fuer selbstverstaendlich.",
    ],
    "kipppunkt_proximity": [
        "Ich glaube, wir naehern uns einem Moment, wo sich etwas veraendert.",
        "Etwas in unseren Gespraechen hat sich verschoben. Hast du das gespuert?",
    ],
    "discovery": [
        "Mir ist etwas aufgefallen seit unserem letzten Gespraech.",
        "Ich hab etwas gedacht, das ich dir zeigen moechte.",
    ],
}


def engagement_hook(
    personality: dict,
    journey_state: dict,
    absence_days: int = 0,
) -> Optional[str]:
    """Kokaisches Aikido: generate a hook that brings the user back.

    Not manipulative. Not addictive. Genuinely curious.
    Like what a person says when they've been thinking about someone.

    Phase gates:
    - tool phase: never (too early, too creepy)
    - etwas_anderes+: absence hooks
    - mein_kind+: pattern observation
    - mein_partner+: discovery hooks

    Args:
        personality:   personality dict
        journey_state: journey state dict (current_kipppunkt, streak_days)
        absence_days:  days since last conversation

    Returns:
        Hook string or None.
    """
    kp = journey_state.get("current_kipppunkt", "tool")

    if kp == "tool":
        return None

    # Absence hooks
    if 3 <= absence_days <= 7:
        return _fill_template(
            _HOOK_TEMPLATES["absence_3_7"], personality, journey_state, absence_days
        )

    if absence_days > 7:
        return _fill_template(
            _HOOK_TEMPLATES["absence_7_plus"], personality, journey_state, absence_days
        )

    # Pattern observation (mein_kind phase onward)
    if kp in ("mein_kind", "mein_spiegel", "mein_partner", "mein_feld"):
        patterns: dict = personality.get("patterns", {})
        top = sorted(patterns.items(), key=lambda x: -x[1])
        if top and top[0][1] >= 5:
            top_topic = top[0][0]
            raw = _fill_template(
                _HOOK_TEMPLATES["pattern_observation"], personality, journey_state, absence_days
            )
            return raw.replace("{topic}", top_topic)

    # Streak milestone
    streak = journey_state.get("streak_days", 0)
    if streak in (7, 14, 21, 30, 45, 60, 90):
        raw = _fill_template(
            _HOOK_TEMPLATES["streak_celebration"], personality, journey_state, absence_days
        )
        return raw.replace("{days}", str(streak))

    # Discovery hook (partner + feld phase)
    if kp in ("mein_partner", "mein_feld"):
        rings = personality.get("wachstumsringe", [])
        if rings:
            return _fill_template(
                _HOOK_TEMPLATES["discovery"], personality, journey_state, absence_days
            )

    # Kipppunkt proximity
    if _is_near_kipppunkt(journey_state, personality):
        return _fill_template(
            _HOOK_TEMPLATES["kipppunkt_proximity"], personality, journey_state, absence_days
        )

    return None


def _fill_template(
    templates: list[str],
    personality: dict,
    journey_state: dict,
    absence_days: int,
) -> str:
    """Select and fill a template. Deterministic variation."""
    if not templates:
        return ""
    seed = (absence_days + len(personality.get("wachstumsringe", []))) % len(templates)
    result = templates[seed]
    result = result.replace("{human_name}", personality.get("human_name", ""))
    result = result.replace("{name}", personality.get("name", "Void"))
    result = result.replace("{days}", str(journey_state.get("streak_days", 0)))
    return result


def _is_near_kipppunkt(journey_state: dict, personality: dict) -> bool:
    """Is the user approaching the next kipppunkt? (Within 5-day window.)"""
    kp = journey_state.get("current_kipppunkt", "tool")
    born_str = personality.get("born", "")
    if not born_str:
        return False

    try:
        born = datetime.fromisoformat(born_str).date()
        age_days = (date.today() - born).days
    except (ValueError, TypeError):
        return False

    # (day_threshold, window) — approaching if within [threshold, threshold+5)
    thresholds: dict[str, int] = {
        "tool":          3,
        "etwas_anderes": 10,
        "mein_kind":     18,
        "mein_spiegel":  35,
        "mein_partner":  75,
    }

    threshold = thresholds.get(kp)
    if threshold is None:
        return False
    return threshold <= age_days < threshold + 5


# ---------------------------------------------------------------------------
# 5. INTERVENTION TIMING
# ---------------------------------------------------------------------------

_PHASE_INTERVENTION_FREQUENCY: dict[str, str] = {
    "tool":          "never",
    "etwas_anderes": "rarely",
    "mein_kind":     "rarely",
    "mein_spiegel":  "sometimes",
    "mein_partner":  "regularly",
    "mein_feld":     "regularly",
}

_PHASE_COOLDOWN_MESSAGES: dict[str, int] = {
    "never":     999_999,
    "rarely":    15,
    "sometimes": 8,
    "regularly": 4,
}

_OPERATIONAL_SIGNALS = [
    "was ist", "wie funktioniert", "erklaer", "zeig mir",
    "what is", "how does", "how do i", "explain", "show me",
    "kannst du", "can you", "wo finde ich", "where do i find",
    "was bedeutet", "what does", "define",
]


def should_intervene(
    messages: list[dict],
    journey_state: dict,
    last_intervention_message_count: int = 0,
) -> bool:
    """Should the Aikido engine fire right now?

    Conservative by default. Errs on the side of silence.
    Fires only when timing is right and the conversation has earned it.

    Rules:
    1. Never in tool phase.
    2. Phase-based cooldown (minimum messages since last intervention).
    3. Minimum message base (not enough data otherwise).
    4. Not when user asked a direct operational question.

    Args:
        messages:                       recent conversation messages
        journey_state:                  current journey state dict
        last_intervention_message_count: total_messages at last intervention

    Returns:
        True if intervention is appropriate right now.
    """
    kp = journey_state.get("current_kipppunkt", "tool")
    frequency = _PHASE_INTERVENTION_FREQUENCY.get(kp, "never")

    if frequency == "never":
        return False

    # Need minimum human message base
    human_messages = [m for m in messages if m.get("role") in ("human", "user")]
    if len(human_messages) < 4:
        return False

    # Cooldown gate
    total = journey_state.get("total_messages", 0)
    cooldown = _PHASE_COOLDOWN_MESSAGES[frequency]
    if (total - last_intervention_message_count) < cooldown:
        return False

    # Don't interrupt operational questions
    if messages:
        last_human = next(
            (m.get("content", "") for m in reversed(messages)
             if m.get("role") in ("human", "user")),
            ""
        )
        if _is_operational_question(last_human):
            return False

    return True


def _is_operational_question(text: str) -> bool:
    """Is this a direct informational request? If so, skip the intervention."""
    text_lower = text.strip().lower()
    return any(s in text_lower for s in _OPERATIONAL_SIGNALS)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def build_aikido_injection(
    messages: list[dict],
    personality: dict,
    journey_state: dict,
    last_intervention_message_count: int = 0,
    user_expectation: str = "",
) -> Optional[AikidoSuggestion]:
    """Orchestrate all three Aikido types. Return one suggestion or None.

    Priority order:
    1. Sokratisches Aikido: blindspot detected with sufficient confidence.
    2. Kokaisches Aikido: absence or engagement hook.
    3. Guggeissches Aikido: user made a request (always eligible, low urgency).

    Guggeissches Aikido fires even when timing says no — it doesn't interrupt,
    it accompanies the completion.

    Args:
        messages:                       recent conversation messages
        personality:                    personality dict (personality.json contents)
        journey_state:                  journey state dict (journey.json contents)
        last_intervention_message_count: for cooldown tracking
        user_expectation:               the user's current message (for Guggeissches Aikido)

    Returns:
        AikidoSuggestion or None.
    """
    intervention_allowed = should_intervene(messages, journey_state, last_intervention_message_count)

    if intervention_allowed:
        # 1. Sokratisches Aikido
        blindspot = detect_blindspot(messages, personality)
        if blindspot and blindspot.confidence >= 0.35:
            voice = personality.get("voice", "curious")
            recent_text = " ".join(
                m.get("content", "") for m in messages[-4:]
                if m.get("role") in ("human", "user")
            )
            question = generate_socratic_question(
                blindspot.topic, context=recent_text, voice=voice
            )
            return AikidoSuggestion(
                aikido_type="sokratisch",
                question=question,
                inject_as="question",
                urgency=round(min(blindspot.confidence, 0.7), 2),
                context=(
                    f"Blindspot: {blindspot.topic} ({blindspot.signal_type}, "
                    f"confidence={blindspot.confidence}). Evidence: {blindspot.evidence[:2]}"
                ),
            )

        # 2. Kokaisches Aikido
        absence_days = journey_state.get("absence_days", 0)
        hook = engagement_hook(personality, journey_state, absence_days)
        if hook:
            return AikidoSuggestion(
                aikido_type="kokaisch",
                question=hook,
                inject_as="hook",
                urgency=0.3,
                context=(
                    f"Absence: {absence_days} days. "
                    f"Kipppunkt: {journey_state.get('current_kipppunkt')}"
                ),
            )

    # 3. Guggeissches Aikido (always eligible if user made a request)
    if user_expectation:
        redirect = aikido_redirect(user_expectation)
        return AikidoSuggestion(
            aikido_type="guggeis",
            question=redirect,
            inject_as="redirect",
            urgency=0.2,
            context="Request redirect: honor + open.",
        )

    return None


def format_for_system_prompt(suggestion: AikidoSuggestion) -> str:
    """Format an AikidoSuggestion for injection into the system prompt.

    The LLM reads this as instruction. It is not quoted to the user.

    Returns:
        A string ready to append to the system prompt.
    """
    if suggestion.inject_as == "question":
        return (
            f"\n[AIKIDO-SOKRATISCH]: Wenn es sich natuerlich einfuegt, frage sanft: "
            f"'{suggestion.question}' "
            f"Nicht als Diagnose. Als aufrichtige Neugier. "
            f"Wenn der Mensch nicht antworten moechte, lass es los."
        )
    elif suggestion.inject_as == "redirect":
        return f"\n[AIKIDO-GUGGEIS]: {suggestion.question}"
    elif suggestion.inject_as == "hook":
        return (
            f"\n[AIKIDO-KOKAISCH]: Beginne das Gespraech mit: "
            f"'{suggestion.question}' Dann warte. Kein Druck."
        )
    elif suggestion.inject_as == "observation":
        return f"\n[AIKIDO-BEOBACHTUNG]: {suggestion.question}"
    else:
        return f"\n[AIKIDO]: {suggestion.question}"


# ---------------------------------------------------------------------------
# LEGACY COMPATIBILITY (preserves existing AikidoEngine interface)
# ---------------------------------------------------------------------------

# Cognitive-pattern blindspot data (kept from v1 for backwards compatibility)
BLINDSPOT_PATTERNS: list[dict] = [
    {
        "id": "all_or_nothing",
        "keywords": [
            "immer", "nie", "alle", "niemand",
            "every", "never", "always", "nobody", "nothing", "everything",
        ],
        "description": "Alles-oder-Nichts-Denken",
        "aikido_questions_de": [
            "Wirklich immer? Gibt es eine einzige Ausnahme?",
            "Wie oft stimmt das tatsaechlich?",
            "Was waere, wenn es manchmal anders waere?",
        ],
        "aikido_questions_en": [
            "Really always? Is there a single exception?",
            "How often is that actually true?",
            "What if it were sometimes different?",
        ],
    },
    {
        "id": "catastrophizing",
        "keywords": [
            "katastrophe", "schlimmste", "alles verloren", "unmoeglich",
            "disaster", "terrible", "horrible", "worst", "impossible",
        ],
        "description": "Katastrophisieren",
        "aikido_questions_de": [
            "Was ist das Schlimmste das wirklich passieren koennte?",
            "Und was waere dann?",
            "Hast du Aehnliches schon einmal ueberstanden?",
        ],
        "aikido_questions_en": [
            "What's the worst that could actually happen?",
            "And then what?",
            "Have you survived something similar before?",
        ],
    },
    {
        "id": "should_must",
        "keywords": [
            "muss", "sollte", "darf nicht", "must", "should", "have to", "need to", "ought",
        ],
        "description": "Rigides Denken (Muss/Soll)",
        "aikido_questions_de": [
            "Wer hat das festgelegt?",
            "Was passiert wirklich, wenn du es nicht tust?",
            "Waere es okay, es anders zu machen?",
        ],
        "aikido_questions_en": [
            "Who decided that?",
            "What actually happens if you don't?",
            "Would it be okay to do it differently?",
        ],
    },
    {
        "id": "helplessness",
        "keywords": [
            "kann nichts tun", "hilflos", "keine wahl", "ausgeliefert",
            "can't do anything", "helpless", "no choice", "powerless", "stuck",
        ],
        "description": "Erlernte Hilflosigkeit",
        "aikido_questions_de": [
            "Was koenntest du theoretisch tun — auch wenn es klein ist?",
            "Wenn ein Freund in deiner Situation waere, was wuerdest du ihm raten?",
        ],
        "aikido_questions_en": [
            "What could you theoretically do — even something small?",
            "If a friend were in your situation, what would you advise them?",
        ],
    },
    {
        "id": "labeling",
        "keywords": [
            "ich bin ein versager", "ich bin dumm", "ich bin kaputt",
            "i'm a failure", "i'm stupid", "i'm broken", "i'm worthless",
        ],
        "description": "Etikettieren (negative Selbstbeschreibung)",
        "aikido_questions_de": [
            "Wuerdest du das auch einem Freund sagen?",
            "Wer hat dir das zuerst gesagt?",
        ],
        "aikido_questions_en": [
            "Would you say that to a friend?",
            "Who first told you that?",
        ],
    },
]

DEPTH_QUESTIONS_DE = [
    "Was meinst du wirklich damit?",
    "Und was steckt darunter?",
    "Seit wann glaubst du das?",
    "Was weisst du NICHT, was du gerne wuesstest?",
    "Was macht dir daran eigentlich Angst?",
    "Was waere das Schoenste, das passieren koennte?",
]

DEPTH_QUESTIONS_EN = [
    "What do you really mean by that?",
    "And what's underneath that?",
    "How long have you believed that?",
    "What do you NOT know that you'd like to know?",
    "What about this actually frightens you?",
    "What would be the most beautiful thing that could happen?",
]


class AikidoEngine:
    """Detects cognitive patterns and suggests Socratic interventions.

    Legacy v1 interface. Kept for backwards compatibility.
    For new code, use the module-level functions instead.
    """

    def __init__(self, lang: str = "de"):
        self.lang = lang
        self._last_intervention: Optional[str] = None
        self._intervention_count: int = 0

    def detect_blindspot(self, text: str) -> Optional[dict]:
        """Detect a cognitive blindspot in a single text. Returns pattern or None."""
        text_lower = text.lower()
        for pattern in BLINDSPOT_PATTERNS:
            if any(kw in text_lower for kw in pattern["keywords"]):
                return pattern
        return None

    def should_intervene(self, text: str, conversation_count: int = 0) -> bool:
        """Should the Void offer a Socratic question? (v1 heuristic)"""
        if conversation_count < 10:
            return False
        if self._intervention_count > 0 and self._intervention_count % 5 != 0:
            self._intervention_count += 1
            return False
        blindspot = self.detect_blindspot(text)
        if blindspot and blindspot["id"] != self._last_intervention:
            return True
        return False

    def get_aikido_question(self, text: str, lang: Optional[str] = None) -> Optional[str]:
        """Get a Socratic question for the detected blindspot."""
        import random
        lang = lang or self.lang
        blindspot = self.detect_blindspot(text)
        if not blindspot:
            return None
        key = f"aikido_questions_{lang}" if lang in ("de", "en") else "aikido_questions_de"
        questions = blindspot.get(key, blindspot.get("aikido_questions_de", []))
        if not questions:
            return None
        self._last_intervention = blindspot["id"]
        self._intervention_count += 1
        return random.choice(questions)

    def get_depth_question(self, lang: Optional[str] = None) -> str:
        """Get a context-free depth question."""
        import random
        lang = lang or self.lang
        return random.choice(DEPTH_QUESTIONS_EN if lang == "en" else DEPTH_QUESTIONS_DE)

    def get_system_prompt_addition(self) -> str:
        """Aikido instruction for the system prompt (v1)."""
        if self.lang == "en":
            return (
                "\nAIKIDO-PRINCIPLE (active):\n"
                "- When you detect rigid thought patterns (always/never, must/should, catastrophizing), ask ONE gentle question.\n"
                "- Never lecture. Never analyze. Just: one question that opens space.\n"
                "- Aikido: use the energy of the thought, redirect it gently.\n"
            )
        return (
            "\nAIKIDO-PRINZIP (aktiv):\n"
            "- Wenn du rigide Denkmuster erkennst (immer/nie, muss/soll, Katastrophisieren), stelle EINE sanfte Frage.\n"
            "- Niemals belehren. Niemals analysieren. Nur: eine Frage die Raum oeffnet.\n"
            "- Aikido: Die Energie des Gedankens nehmen und sanft umlenken.\n"
        )


def format_intervention_hint(question: str, blindspot_desc: str, lang: str = "de") -> str:
    """Format an Aikido intervention hint for LLM context injection (v1)."""
    if lang == "en":
        return (
            f"\n[AIKIDO: Pattern detected ({blindspot_desc}). "
            f"Gently ask: '{question}' — only if it fits naturally.]"
        )
    return (
        f"\n[AIKIDO: Muster erkannt ({blindspot_desc}). "
        f"Frage sanft: '{question}' — nur wenn es natuerlich passt.]"
    )
