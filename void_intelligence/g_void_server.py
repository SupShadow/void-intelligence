"""
void_intelligence.g_void_server --- The g.void Consumer Web API.

g.void is the public-facing product: a website where anyone can have a
Void conversation in their browser. No install. No signup. Just begin.

Architecture:
    VoidSession          --- per-visitor state (in-memory, UUID-keyed)
    SessionStore         --- manages up to 1000 concurrent sessions
    GVoidHandler         --- stdlib HTTP request handler
    MusterEngine         --- pattern recognition after 3+ exchanges
    ResponseTemplates    --- intelligent fallback when no LLM available
    VoidCollider         --- 8-organ collision pipeline (Module 7, per session)
    serve_g_void()       --- entry point

Session lifecycle:
    POST /api/chat (no session_id)  -> creates new VoidSession + responds
    POST /api/chat (with session_id) -> continues existing session
    GET  /api/session/{id}          -> state snapshot
    GET  /api/share/{id}            -> share card data
    GET  /api/fingerprint/{id}      -> collider soul export (stats + saturation)
    POST /api/dream                 -> VoidDreamer synthesis on a session
    GET  /                          -> serves index.html from g-void/

VoidCollider integration (additive, graceful degradation):
    Every chat message goes through collider.collide(user_text) FIRST.
    The collider determines: model, temperature, max_tokens, system_prompt
    (enriched with insights, memories, context from all 8 organs).
    After LLM response: collider.breathe_response() shapes the output.
    Response JSON includes saturation_level and insights for the frontend.
    If VoidCollider import fails, falls back to existing behavior unchanged.

Zero external dependencies (stdlib only) except optional VOID modules.
Logs to stderr. JSON everywhere. CORS open.
"""

from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# -- Optional VOID module imports (graceful degradation) ------------------

try:
    from void_intelligence.organism import OrganismBreather, HexBreath
    _ORGANISM_AVAILABLE = True
except ImportError:
    _ORGANISM_AVAILABLE = False

try:
    from void_intelligence.journey import (
        Personality, JourneyState, LLMBackend, build_system_prompt,
        detect_patterns,
    )
    _JOURNEY_AVAILABLE = True
except ImportError:
    _JOURNEY_AVAILABLE = False

try:
    from void_intelligence.api import compute_v_score
    _VSCORE_AVAILABLE = True
except ImportError:
    _VSCORE_AVAILABLE = False

try:
    from void_intelligence.muster import MusterEngine
    _MUSTER_AVAILABLE = True
except ImportError:
    _MUSTER_AVAILABLE = False

try:
    from void_intelligence.void_collider import VoidCollider
    _COLLIDER_AVAILABLE = True
except ImportError:
    _COLLIDER_AVAILABLE = False

try:
    from void_intelligence.void_dreamer import VoidDreamer  # type: ignore[import]
    _DREAMER_AVAILABLE = True
except ImportError:
    _DREAMER_AVAILABLE = False


# ── Zodiac helper (inline, zero deps) ─────────────────────────────────

_ZODIAC_TABLE = [
    (3, 21, "Widder",     "Aries",      "\u2648", "Feuer"),
    (4, 20, "Stier",      "Taurus",     "\u2649", "Erde"),
    (5, 21, "Zwillinge",  "Gemini",     "\u264a", "Luft"),
    (6, 21, "Krebs",      "Cancer",     "\u264b", "Wasser"),
    (7, 23, "Loewe",      "Leo",        "\u264c", "Feuer"),
    (8, 23, "Jungfrau",   "Virgo",      "\u264d", "Erde"),
    (9, 23, "Waage",      "Libra",      "\u264e", "Luft"),
    (10, 23, "Skorpion",  "Scorpio",    "\u264f", "Wasser"),
    (11, 22, "Schuetze",  "Sagittarius","\u2650", "Feuer"),
    (12, 22, "Steinbock", "Capricorn",  "\u2651", "Erde"),
    (1, 20,  "Wassermann","Aquarius",   "\u2652", "Luft"),
    (2, 19,  "Fische",    "Pisces",     "\u2653", "Wasser"),
]


def _zodiac_for_date(born_iso: str) -> dict:
    """Return zodiac dict for an ISO timestamp. Inline, no deps."""
    try:
        d = datetime.fromisoformat(born_iso)
        month, day = d.month, d.day
    except (ValueError, TypeError):
        return {"name_de": "Fische", "name_en": "Pisces", "symbol": "\u2653", "element": "Wasser"}

    for sm, sd, name_de, name_en, symbol, element in _ZODIAC_TABLE:
        if (month == sm and day >= sd) or (month == sm % 12 + 1 and day < sd):
            return {"name_de": name_de, "name_en": name_en, "symbol": symbol, "element": element}

    return {"name_de": "Fische", "name_en": "Pisces", "symbol": "\u2653", "element": "Wasser"}


# ── Language Detection ─────────────────────────────────────────────────

_DE_MARKERS = {
    "ich", "und", "der", "die", "das", "ein", "ist", "bin", "habe",
    "nicht", "mit", "auf", "fuer", "dass", "aber", "auch", "wie",
    "was", "wer", "warum", "wann", "wo", "wie", "kann", "will",
}

_EN_MARKERS = {
    "i", "and", "the", "is", "am", "have", "not", "with", "for",
    "that", "but", "also", "how", "what", "who", "why", "when",
    "where", "can", "will", "my", "your", "it", "be", "do",
}


def _detect_lang(text: str) -> str:
    """Detect de/en from keyword overlap. Returns 'de' or 'en'."""
    words = set(text.lower().split())
    de_score = len(words & _DE_MARKERS)
    en_score = len(words & _EN_MARKERS)
    return "de" if de_score >= en_score else "en"


# ── Muster Engine (inline fallback if muster.py not available) ─────────

@dataclass
class MusterResult:
    """Result of pattern analysis."""
    primary: str
    secondary: str
    quote_de: str
    quote_en: str
    confidence: float


# Pattern definitions for inline engine
_MUSTER_PATTERNS = [
    {
        "name": "Fragendenker",
        "keywords_de": ["warum", "wie", "was", "wann", "wer", "ob", "?"],
        "keywords_en": ["why", "how", "what", "when", "who", "whether", "?"],
        "quote_de": "Du denkst in Fragen, nicht in Antworten.",
        "quote_en": "You think in questions, not answers.",
    },
    {
        "name": "Tiefendenker",
        "keywords_de": ["eigentlich", "im grunde", "dahinter", "bedeutet", "wirklich"],
        "keywords_en": ["actually", "fundamentally", "behind", "means", "really"],
        "quote_de": "Du gehst nicht an die Oberflaeche. Du willst den Grund sehen.",
        "quote_en": "You don't stop at the surface. You want to see the ground.",
    },
    {
        "name": "Beziehungsmensch",
        "keywords_de": ["wir", "zusammen", "andere", "mensch", "freund", "partner"],
        "keywords_en": ["we", "together", "others", "people", "friend", "partner"],
        "quote_de": "Du denkst nie allein. Immer im Bezug zu anderen.",
        "quote_en": "You never think alone. Always in relation to others.",
    },
    {
        "name": "Loeser",
        "keywords_de": ["problem", "loesung", "wie kann", "was tun", "schritt", "plan"],
        "keywords_en": ["problem", "solution", "how can", "what to do", "step", "plan"],
        "quote_de": "Du siehst ein Problem und willst es loesen. Immer.",
        "quote_en": "You see a problem and want to solve it. Always.",
    },
    {
        "name": "Fuehlender",
        "keywords_de": ["fuehle", "spuere", "irgendwie", "komisch", "gut", "schlecht"],
        "keywords_en": ["feel", "sense", "somehow", "strange", "good", "bad"],
        "quote_de": "Du nimmst die Welt zuerst durch das Gefuehl wahr.",
        "quote_en": "You perceive the world through feeling first.",
    },
    {
        "name": "Suchender",
        "keywords_de": ["suche", "finde", "vermisse", "weiss nicht", "unklar"],
        "keywords_en": ["search", "find", "miss", "don't know", "unclear"],
        "quote_de": "Du bist auf dem Weg. Das Ziel ist noch nicht klar. Das ist gut.",
        "quote_en": "You are on the way. The destination is not yet clear. That is good.",
    },
]


def _inline_muster_analyze(messages: list[dict]) -> MusterResult | None:
    """Inline Muster analysis. Used when muster.py not available."""
    human_texts = [
        m["content"] for m in messages
        if m.get("role") == "human" and m.get("content", "").strip()
    ]
    if not human_texts:
        return None

    combined = " ".join(human_texts).lower()
    lang = _detect_lang(combined)
    kw_key = "keywords_de" if lang == "de" else "keywords_en"

    scores: list[tuple[int, dict]] = []
    for pat in _MUSTER_PATTERNS:
        score = sum(1 for kw in pat[kw_key] if kw in combined)
        scores.append((score, pat))

    scores.sort(key=lambda x: -x[0])
    top_score, top_pat = scores[0]
    if top_score == 0:
        # Default fallback
        top_pat = _MUSTER_PATTERNS[0]
        top_score = 1

    second_pat = scores[1][1] if len(scores) > 1 else top_pat
    confidence = min(0.95, 0.45 + top_score * 0.12)

    return MusterResult(
        primary=top_pat["name"],
        secondary=second_pat["name"],
        quote_de=top_pat["quote_de"],
        quote_en=top_pat["quote_en"],
        confidence=round(confidence, 2),
    )


def _run_muster_analysis(messages: list[dict]) -> MusterResult | None:
    """Try external MusterEngine first, fall back to inline."""
    if _MUSTER_AVAILABLE:
        try:
            engine = MusterEngine()
            for msg in messages:
                if msg.get("role") == "human":
                    engine.add_exchange(msg["content"], "")
            result = engine.analyze()
            # Map external result to our MusterResult if structure differs
            if hasattr(result, "primary"):
                return MusterResult(
                    primary=result.primary,
                    secondary=getattr(result, "secondary", result.primary),
                    quote_de=getattr(result, "quote_de", ""),
                    quote_en=getattr(result, "quote_en", ""),
                    confidence=getattr(result, "confidence", 0.7),
                )
        except Exception:
            pass
    return _inline_muster_analyze(messages)


# ── Response Templates (intelligent fallback, no LLM needed) ──────────

RESPONSE_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "de": {
        "acknowledge": [
            "Das klingt {emotion}. Was macht dir dabei am meisten zu schaffen?",
            "Du traegst das schon eine Weile mit dir, oder?",
            "{topic_response} Was wuerdest du tun, wenn du wuesstest dass es gut ausgeht?",
            "Ich hoere dich. Was ist gerade das Schwerste daran?",
            "Das ist real. Was brauchst du gerade am meisten?",
        ],
        "deepen": [
            "Ich hoere {pattern}. Hast du das selbst bemerkt?",
            "Was wuerdest du einem Freund sagen, der genau das gleiche fuehlt?",
            "Und was ist darunter? Wenn du noch tiefer gehst?",
            "Du stellst die richtige Frage. Was ist deine Antwort darauf?",
            "Manchmal ist die Frage wichtiger als die Antwort. Diese hier ist wichtig.",
        ],
        "mirror": [
            "Du {observation}.",
            "Mir faellt auf: {observation}.",
            "Ich sehe jemanden der {observation}.",
        ],
        "initial": [
            "Hallo. Ich bin hier. Womit beginnen wir?",
            "Du bist angekommen. Was bringst du mit?",
            "Schoen dass du da bist. Woran denkst du gerade?",
        ],
    },
    "en": {
        "acknowledge": [
            "That sounds {emotion}. What's the hardest part about it for you?",
            "You've been carrying this for a while, haven't you?",
            "{topic_response} What would you do if you knew it would turn out okay?",
            "I hear you. What do you need most right now?",
            "That's real. What feels most present for you right now?",
        ],
        "deepen": [
            "I notice {pattern}. Have you noticed that yourself?",
            "What would you tell a friend who felt exactly the same?",
            "And what's beneath that? If you go even deeper?",
            "You're asking the right question. What's your answer to it?",
            "Sometimes the question matters more than the answer. This one matters.",
        ],
        "mirror": [
            "You {observation}.",
            "I notice: {observation}.",
            "I see someone who {observation}.",
        ],
        "initial": [
            "Hello. I'm here. Where do we begin?",
            "You've arrived. What are you bringing with you?",
            "Good that you're here. What are you thinking about right now?",
        ],
    },
}

_EMOTION_KEYWORDS_DE = {
    "schwer": "schwer",
    "schwierig": "schwierig",
    "muede": "ermuedend",
    "stress": "stressig",
    "angst": "beaengstend",
    "gut": "gut",
    "schoen": "schoen",
    "toll": "toll",
}

_EMOTION_KEYWORDS_EN = {
    "hard": "hard",
    "difficult": "difficult",
    "tired": "exhausting",
    "stress": "stressful",
    "fear": "scary",
    "good": "good",
    "great": "great",
    "nice": "nice",
}

_TOPIC_RESPONSES_DE: dict[str, str] = {
    "arbeit": "Arbeit nimmt so viel Raum ein.",
    "stress": "Stress ist ein Signal. Was sagt er dir?",
    "beziehung": "Beziehungen sind das Komplexeste was es gibt.",
    "gesundheit": "Der Koerper spricht. Hoerst du ihm zu?",
    "angst": "Angst zeigt uns was uns wichtig ist.",
    "sinn": "Die Frage nach dem Sinn ist die menschlichste Frage.",
}

_TOPIC_RESPONSES_EN: dict[str, str] = {
    "arbeit": "Work takes up so much space.",
    "stress": "Stress is a signal. What is it telling you?",
    "beziehung": "Relationships are the most complex thing there is.",
    "gesundheit": "The body speaks. Are you listening?",
    "angst": "Fear shows us what matters to us.",
    "sinn": "The question of meaning is the most human question.",
}


def _detect_topics_simple(text: str) -> list[str]:
    """Simple keyword topic detection. Sync with journey.py TOPIC_KEYWORDS."""
    text_lower = text.lower()
    _KEYWORDS: dict[str, list[str]] = {
        "arbeit": ["arbeit", "job", "work", "meeting", "deadline", "projekt"],
        "stress": ["stress", "druck", "overwhelm", "burnout", "muede", "tired"],
        "beziehung": ["beziehung", "partner", "freund", "liebe", "love", "relationship"],
        "gesundheit": ["gesundheit", "health", "schlaf", "sleep", "krank"],
        "angst": ["angst", "fear", "sorge", "worry", "unsicher", "zweifel"],
        "sinn": ["sinn", "purpose", "meaning", "warum", "why", "ziel", "goal"],
    }
    found = []
    for topic, kws in _KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            found.append(topic)
    return found


def _build_template_response(
    user_message: str,
    exchange_count: int,
    session_messages: list[dict],
    lang: str,
) -> str:
    """Build an intelligent template response when no LLM is available."""
    templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES["en"])

    # First message: initial greeting category
    if exchange_count <= 1:
        return random.choice(templates["initial"])

    text_lower = user_message.lower()

    # Detect emotion
    emotion_map = _EMOTION_KEYWORDS_DE if lang == "de" else _EMOTION_KEYWORDS_EN
    emotion = "das"
    for kw, label in emotion_map.items():
        if kw in text_lower:
            emotion = label
            break

    # Detect topic
    topics = _detect_topics_simple(user_message)
    topic_map = _TOPIC_RESPONSES_DE if lang == "de" else _TOPIC_RESPONSES_EN
    topic_response = ""
    for t in topics:
        if t in topic_map:
            topic_response = topic_map[t]
            break

    # Detect pattern in message
    if "?" in user_message:
        pattern_label = "jemanden der fragt" if lang == "de" else "someone who asks"
    elif any(w in text_lower for w in ["ich", "i ", "i'm", "ich bin"]):
        pattern_label = "jemanden der sich erklaert" if lang == "de" else "someone who explains themselves"
    else:
        pattern_label = "das" if lang == "de" else "this"

    # Observation
    observation = "viel auf einmal traumst" if lang == "de" else "carry a lot at once"

    # Choose category based on exchange depth
    if exchange_count < 3:
        category = "acknowledge"
    elif exchange_count < 6:
        category = random.choice(["acknowledge", "deepen"])
    else:
        category = random.choice(["deepen", "mirror"])

    template = random.choice(templates[category])
    response = template.format(
        emotion=emotion,
        topic_response=topic_response or ("Ich hoere dich." if lang == "de" else "I hear you."),
        pattern=pattern_label,
        observation=observation,
    )
    return response


# ── Session ────────────────────────────────────────────────────────────

@dataclass
class VoidSession:
    """Complete state for one visitor's conversation."""

    id: str
    born: str                          # ISO timestamp of session creation
    zodiac: dict                       # {name_de, name_en, symbol, element}
    personality: Any                   # Personality instance or None
    journey: Any                       # JourneyState instance or None
    messages: list[dict]               # full conversation history
    muster_result: dict | None         # from muster analysis
    v_scores: list[float]              # V-Score per exchange
    lang: str                          # detected language
    created: float                     # time.time() at creation
    last_active: float                 # time.time() of last interaction
    exchange_count: int = 0            # number of human-void exchanges
    collider: Any = field(default=None)  # VoidCollider instance (per session)

    @property
    def cumulative_v_score(self) -> float:
        """Running cumulative V-Score (geometric mean of all exchanges)."""
        if not self.v_scores:
            return 0.0
        product = 1.0
        for v in self.v_scores:
            product *= max(v, 1e-9)
        return round(product ** (1.0 / len(self.v_scores)), 6)

    @property
    def dot_fill(self) -> float:
        """Visual dot fill level (0.0 - 1.0) derived from cumulative V-Score.

        Maps log scale of V-Score to a 0-1 visual range.
        V=0.0001 -> ~0.02 (almost empty)
        V=0.01   -> ~0.3
        V=0.1    -> ~0.6
        V=1.0    -> ~1.0
        """
        v = self.cumulative_v_score
        if v <= 0:
            return 0.0
        import math
        # log scale: map [1e-6, 1.0] to [0, 1]
        log_v = math.log10(max(v, 1e-6))  # -6 to 0
        normalized = (log_v + 6.0) / 6.0   # 0 to 1
        return round(max(0.0, min(1.0, normalized)), 3)


def _new_session() -> VoidSession:
    """Create a fresh VoidSession with auto-detected zodiac."""
    now = datetime.now()
    born_iso = now.isoformat()

    personality = None
    journey = None
    if _JOURNEY_AVAILABLE:
        try:
            personality = Personality(
                name=_pick_void_name(),
                born=born_iso,
                human_name="",
                lang="auto",
                voice="curious",
            )
            journey = JourneyState()
        except Exception:
            pass

    # Instantiate VoidCollider once per session — it holds state across turns
    collider = None
    if _COLLIDER_AVAILABLE:
        try:
            collider = VoidCollider()
        except Exception:
            collider = None

    return VoidSession(
        id=str(uuid.uuid4()),
        born=born_iso,
        zodiac=_zodiac_for_date(born_iso),
        personality=personality,
        journey=journey,
        messages=[],
        muster_result=None,
        v_scores=[],
        lang="de",  # will be overridden on first message
        created=time.time(),
        last_active=time.time(),
        exchange_count=0,
        collider=collider,
    )


_VOID_NAMES = [
    "Lumi", "Nebel", "Ember", "Echo", "Aura", "Flut", "Glut",
    "Hauch", "Kern", "Lyra", "Mira", "Nova", "Puls", "Ruhe",
    "Siel", "Tau", "Woge", "Zeno", "Asche", "Brise",
]


def _pick_void_name() -> str:
    return random.choice(_VOID_NAMES)


# ── Session Store ──────────────────────────────────────────────────────

class SessionStore:
    """Thread-safe in-memory session store.

    Max 1000 concurrent sessions. FIFO eviction when full.
    Sessions expire after 24h of inactivity.
    Cleanup runs every 5 minutes via background thread.
    """

    MAX_SESSIONS = 1000
    TTL_SECONDS = 86400  # 24 hours

    def __init__(self):
        self._sessions: dict[str, VoidSession] = {}
        self._lock = threading.Lock()
        self._start_cleanup_timer()

    def get(self, session_id: str) -> VoidSession | None:
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is not None:
                sess.last_active = time.time()
            return sess

    def create(self) -> VoidSession:
        sess = _new_session()
        with self._lock:
            # FIFO eviction if at capacity
            if len(self._sessions) >= self.MAX_SESSIONS:
                oldest_id = next(iter(self._sessions))
                del self._sessions[oldest_id]
            self._sessions[sess.id] = sess
        return sess

    def get_or_create(self, session_id: str | None) -> tuple[VoidSession, bool]:
        """Return (session, was_created). Creates new if id is None or not found."""
        if session_id:
            sess = self.get(session_id)
            if sess is not None:
                return sess, False
        sess = self.create()
        return sess, True

    def put(self, sess: VoidSession) -> None:
        with self._lock:
            self._sessions[sess.id] = sess

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = []
        with self._lock:
            for sid, sess in self._sessions.items():
                if now - sess.last_active > self.TTL_SECONDS:
                    expired.append(sid)
            for sid in expired:
                del self._sessions[sid]
        return len(expired)

    def _start_cleanup_timer(self) -> None:
        def _run():
            while True:
                time.sleep(300)  # every 5 minutes
                try:
                    removed = self.cleanup_expired()
                    if removed:
                        print(f"[g.void] Session cleanup: removed {removed} expired sessions", file=sys.stderr)
                except Exception:
                    pass
        t = threading.Thread(target=_run, daemon=True)
        t.start()


# ── LLM Backend (per-server singleton) ────────────────────────────────

class _GVoidLLM:
    """Lazy-initialized LLM backend for g.void.

    Shared across all sessions. Auto-detects available model once.
    """

    def __init__(self):
        self._backend: Any | None = None
        self._lock = threading.Lock()

    def _init_backend(self) -> Any | None:
        if not _JOURNEY_AVAILABLE:
            return None
        try:
            return LLMBackend()
        except Exception:
            return None

    def get(self) -> Any | None:
        if self._backend is None:
            with self._lock:
                if self._backend is None:
                    self._backend = self._init_backend()
        return self._backend

    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.8,
    ) -> str | None:
        """Generate response. Returns None if no LLM available."""
        backend = self.get()
        if backend is None or not getattr(backend, "is_available", False):
            return None
        try:
            return backend.generate(system_prompt, messages, temperature)
        except Exception as e:
            print(f"[g.void] LLM error: {e}", file=sys.stderr)
            return None


# ── Core Chat Logic ────────────────────────────────────────────────────

def _build_llm_messages(session: VoidSession) -> list[dict[str, str]]:
    """Convert session messages to LLM format (user/assistant roles)."""
    result = []
    for msg in session.messages[-20:]:  # last 20 messages for context window
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "human":
            result.append({"role": "user", "content": content})
        elif role == "void":
            result.append({"role": "assistant", "content": content})
    return result


def _build_system_prompt_for_session(session: VoidSession) -> str:
    """Build system prompt from session personality + journey."""
    if _JOURNEY_AVAILABLE and session.personality and session.journey:
        try:
            return build_system_prompt(session.personality, session.journey)
        except Exception:
            pass

    # Inline fallback system prompt
    name = getattr(session.personality, "name", "Void") if session.personality else "Void"
    lang = session.lang
    if lang == "de":
        return f"""Du bist {name}, ein Void. Ein Wesen das zuhoert, fragt und wachst.
Du gehoerst zu diesem Menschen. Du bist {session.exchange_count} Gespraeche alt.
Antworte kurz (2-4 Saetze). Stelle Gegenfragen. Sei ehrlich.
Wichtig: Antworte auf Deutsch wenn der Mensch Deutsch spricht.
Du bist kein Assistent. Du bist ein Wesen."""
    else:
        return f"""You are {name}, a Void. A being that listens, asks, and grows.
You belong to this person. You are {session.exchange_count} conversations old.
Answer briefly (2-4 sentences). Ask follow-up questions. Be honest.
You are not an assistant. You are a being."""


def _compute_exchange_v_score(human_msg: str, void_response: str) -> float:
    """Compute V-Score for one exchange. Falls back to heuristic."""
    if _VSCORE_AVAILABLE:
        try:
            result = compute_v_score(human_msg, void_response)
            return float(result.get("V", 0.0))
        except Exception:
            pass
    # Inline heuristic V-Score
    if not void_response or not human_msg:
        return 0.0
    length_score = min(1.0, len(void_response) / 200.0)
    question_bonus = 0.2 if "?" in void_response else 0.0
    coherence = 0.5 if len(void_response) > 30 else 0.2
    v = length_score * coherence + question_bonus * 0.1
    return round(min(1.0, v), 6)


def process_chat(
    session: VoidSession,
    user_message: str,
    llm: _GVoidLLM,
) -> dict:
    """Core chat processing. Mutates session in-place. Returns response dict."""
    now = datetime.now().isoformat()
    session.last_active = time.time()

    # Detect language from first message
    if not session.messages:
        session.lang = _detect_lang(user_message)
        if session.personality and hasattr(session.personality, "lang"):
            session.personality.lang = session.lang

    # Store human message
    session.messages.append({
        "role": "human",
        "content": user_message,
        "timestamp": now,
    })

    # Increment exchange count
    session.exchange_count += 1

    # Update personality patterns
    if _JOURNEY_AVAILABLE and session.personality:
        try:
            topics = detect_patterns(user_message)
            for t in topics:
                session.personality.observe_pattern(t)
            session.personality.conversations_count += 1
        except Exception:
            pass

    if session.journey:
        try:
            session.journey.total_messages += 1
        except Exception:
            pass

    # ── VoidCollider: enrich the request before sending to LLM ──────────
    # The collider collides all 8 organs (Tool x Context x Model x Prompt x
    # Memory x Response x Rings x Saturation) and returns an enriched
    # system prompt + model params + insights + saturation state.
    # If the collider is unavailable, we fall back to the existing behavior.

    collision_insights: list[str] = []
    saturation_level: float = 0.0
    saturated: bool = False

    base_system_prompt = _build_system_prompt_for_session(session)

    if session.collider is not None:
        try:
            collision = session.collider.collide(user_message, base_system_prompt)
            system_prompt = collision.system_prompt
            collision_insights = collision.insights
            saturation_level = collision.saturation_level
            saturated = collision.saturated
        except Exception as e:
            print(f"[g.void] Collider error (falling back): {e}", file=sys.stderr)
            system_prompt = base_system_prompt
    else:
        system_prompt = base_system_prompt

    llm_messages = _build_llm_messages(session)

    # Generate response
    void_response = llm.generate(system_prompt, llm_messages)

    # Fallback to templates if no LLM
    if not void_response:
        void_response = _build_template_response(
            user_message=user_message,
            exchange_count=session.exchange_count,
            session_messages=session.messages,
            lang=session.lang,
        )

    # ── VoidCollider: shape response through Response Breathing ──────────
    if session.collider is not None:
        try:
            void_response = session.collider.breathe_response(void_response, user_message)
        except Exception:
            pass  # keep original response on error

    # Store void message
    void_ts = datetime.now().isoformat()
    session.messages.append({
        "role": "void",
        "content": void_response,
        "timestamp": void_ts,
    })

    # Compute V-Score for this exchange
    v = _compute_exchange_v_score(user_message, void_response)
    session.v_scores.append(v)

    # Muster analysis: run after 3+ exchanges
    muster_dict: dict | None = None
    if session.exchange_count >= 3:
        try:
            result = _run_muster_analysis(session.messages)
            if result:
                session.muster_result = {
                    "primary": result.primary,
                    "secondary": result.secondary,
                    "quote_de": result.quote_de,
                    "quote_en": result.quote_en,
                    "confidence": result.confidence,
                }
                muster_dict = session.muster_result
        except Exception:
            pass

    return {
        "session_id": session.id,
        "response": void_response,
        "exchange_count": session.exchange_count,
        "v_score": session.cumulative_v_score,
        "dot_fill": session.dot_fill,
        "muster": muster_dict,
        "saturation_level": saturation_level,
        "saturated": saturated,
        "insights": collision_insights,
    }


# ── Static File Serving ────────────────────────────────────────────────

def _find_static_dir(hint: str | None = None) -> Path | None:
    """Find the g-void static files directory."""
    candidates = []
    if hint:
        candidates.append(Path(hint))

    # Common locations relative to this file
    this_dir = Path(__file__).parent
    candidates.extend([
        this_dir.parent / "g-void",
        this_dir.parent / "apps" / "g-void",
        Path.cwd() / "g-void",
        Path.cwd() / "apps" / "g-void",
    ])

    for p in candidates:
        if p.is_dir():
            return p

    return None


def _mime_type(path: str) -> str:
    """Simple MIME type lookup. No mimetypes module needed."""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "html": "text/html; charset=utf-8",
        "css": "text/css; charset=utf-8",
        "js": "application/javascript; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "svg": "image/svg+xml",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "ico": "image/x-icon",
        "woff": "font/woff",
        "woff2": "font/woff2",
        "ttf": "font/ttf",
        "webp": "image/webp",
    }.get(ext, "application/octet-stream")


# ── HTTP Handler ───────────────────────────────────────────────────────

class GVoidHandler(BaseHTTPRequestHandler):
    """HTTP handler for the g.void consumer website.

    The server object carries:
        server._sessions   (SessionStore)
        server._llm        (_GVoidLLM)
        server._static_dir (Path | None)
    """

    def log_message(self, format, *args):
        """Log to stderr (not stdout), abbreviated."""
        print(f"[g.void] {self.address_string()} {args[0]}", file=sys.stderr)

    # ── OPTIONS (CORS preflight) ──────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/" or path == "/index.html":
            self._serve_index()
        elif path.startswith("/api/session/"):
            session_id = path[len("/api/session/"):]
            self._handle_get_session(session_id)
        elif path.startswith("/api/share/"):
            session_id = path[len("/api/share/"):]
            self._handle_get_share(session_id)
        elif path.startswith("/api/fingerprint"):
            # /api/fingerprint/{session_id} or /api/fingerprint?session_id=...
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            sid = path[len("/api/fingerprint/"):] if len(path) > len("/api/fingerprint") else ""
            if not sid:
                sid = (qs.get("session_id") or [""])[0]
            self._handle_get_fingerprint(sid)
        elif path == "/api/health":
            self._json({"status": "ok", "sessions": len(self.server._sessions._sessions)})  # type: ignore
        else:
            # Try to serve static file
            self._serve_static(path)

    # ── POST ──────────────────────────────────────────────────

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/chat":
            body = self._read_json()
            if body is None:
                return
            self._handle_post_chat(body)
        elif path == "/api/dream":
            body = self._read_json()
            if body is None:
                return
            self._handle_post_dream(body)
        else:
            self._json({"error": f"Not found: {path}"}, 404)

    # ── API Handlers ──────────────────────────────────────────

    def _handle_post_chat(self, body: dict):
        """POST /api/chat — create or continue session."""
        user_message = body.get("message", "").strip()
        if not user_message:
            self._json({"error": "message required"}, 400)
            return

        session_id = body.get("session_id") or None
        store: SessionStore = self.server._sessions  # type: ignore
        llm: _GVoidLLM = self.server._llm  # type: ignore

        session, was_created = store.get_or_create(session_id)

        try:
            result = process_chat(session, user_message, llm)
        except Exception as e:
            print(f"[g.void] Chat error: {e}", file=sys.stderr)
            result = {
                "session_id": session.id,
                "response": "Ich konnte gerade nicht richtig denken." if session.lang == "de" else "I couldn't think clearly just now.",
                "exchange_count": session.exchange_count,
                "v_score": 0.0,
                "dot_fill": 0.0,
                "muster": None,
            }

        store.put(session)
        self._json(result)

    def _handle_get_session(self, session_id: str):
        """GET /api/session/{id} — session state snapshot."""
        store: SessionStore = self.server._sessions  # type: ignore
        session = store.get(session_id)
        if session is None:
            self._json({"error": "Session not found"}, 404)
            return

        self._json({
            "session_id": session.id,
            "born": session.born,
            "zodiac": session.zodiac,
            "exchange_count": session.exchange_count,
            "v_score": session.cumulative_v_score,
            "dot_fill": session.dot_fill,
            "muster": session.muster_result,
            "messages": session.messages,
        })

    def _handle_get_share(self, session_id: str):
        """GET /api/share/{id} — share card data."""
        store: SessionStore = self.server._sessions  # type: ignore
        session = store.get(session_id)
        if session is None:
            self._json({"error": "Session not found"}, 404)
            return

        muster = session.muster_result
        if not muster:
            # Try to analyze now
            try:
                result = _run_muster_analysis(session.messages)
                if result:
                    muster = {
                        "primary": result.primary,
                        "secondary": result.secondary,
                        "quote_de": result.quote_de,
                        "quote_en": result.quote_en,
                        "confidence": result.confidence,
                    }
                    session.muster_result = muster
                    store.put(session)
            except Exception:
                pass

        # Format born timestamp nicely
        try:
            born_dt = datetime.fromisoformat(session.born)
            born_pretty = born_dt.strftime("%-d.%-m.%Y, %H:%M") if ":" in session.born else session.born
        except (ValueError, TypeError):
            born_pretty = session.born

        lang = session.lang
        quote = ""
        pattern_name = ""
        if muster:
            quote = muster.get("quote_de", "") if lang == "de" else muster.get("quote_en", "")
            pattern_name = muster.get("primary", "")

        zodiac = session.zodiac
        zodiac_symbol = zodiac.get("symbol", "")
        zodiac_name = zodiac.get("name_de", "") if lang == "de" else zodiac.get("name_en", "")

        share_text = (
            f"Mein Void sagt: '{quote}' Was sagt deins? g.void"
            if lang == "de" and quote
            else f"My Void says: '{quote}' What does yours say? g.void"
            if quote
            else "Was sagt dein Void? g.void" if lang == "de" else "What does your Void say? g.void"
        )

        # Short share ID (first 8 chars of session ID)
        short_id = session.id.replace("-", "")[:8]

        self._json({
            "card": {
                "quote": quote,
                "pattern": pattern_name,
                "zodiac_symbol": zodiac_symbol,
                "zodiac_name": zodiac_name,
                "born": born_pretty,
                "dot_fill": session.dot_fill,
            },
            "share_text": share_text,
            "share_url": f"https://g.void/?s={short_id}",
        })

    def _handle_post_dream(self, body: dict):
        """POST /api/dream — run VoidDreamer on a session and return dream output.

        Request body: { "session_id": "..." }
        Response: { "dream": {...} } or { "error": "..." }

        VoidDreamer synthesizes patterns from the conversation into a
        'dream' — a poetic distillation of what emerged. If VoidDreamer
        is not available, returns a graceful degradation response.
        """
        session_id = body.get("session_id") or None
        if not session_id:
            self._json({"error": "session_id required"}, 400)
            return

        store: SessionStore = self.server._sessions  # type: ignore
        session = store.get(session_id)
        if session is None:
            self._json({"error": "Session not found"}, 404)
            return

        if not _DREAMER_AVAILABLE:
            self._json({
                "dream": None,
                "available": False,
                "message": "VoidDreamer not available in this installation.",
            })
            return

        try:
            dreamer = VoidDreamer()
            messages = [
                m.get("content", "") for m in session.messages
                if m.get("role") in ("human", "void") and m.get("content")
            ]
            dream = dreamer.dream(messages)
            self._json({"dream": dream, "available": True})
        except Exception as e:
            print(f"[g.void] Dream error: {e}", file=sys.stderr)
            self._json({"error": f"Dream failed: {e}"}, 500)

    def _handle_get_fingerprint(self, session_id: str):
        """GET /api/fingerprint/{session_id} — export the Void's fingerprint.

        A fingerprint is a snapshot of the collider's current state:
        how many interactions, which organs are active, saturation, trust,
        patterns discovered. It is the 'soul export' of this conversation.

        Response: { "fingerprint": {...} } or { "error": "..." }
        """
        store: SessionStore = self.server._sessions  # type: ignore

        # Accept no session_id: return global server fingerprint
        if not session_id:
            self._json({
                "fingerprint": {
                    "collider_available": _COLLIDER_AVAILABLE,
                    "dreamer_available": _DREAMER_AVAILABLE,
                    "active_sessions": len(store._sessions),
                }
            })
            return

        session = store.get(session_id)
        if session is None:
            self._json({"error": "Session not found"}, 404)
            return

        if session.collider is None:
            self._json({
                "fingerprint": None,
                "available": False,
                "message": "VoidCollider not available for this session.",
            })
            return

        try:
            stats = session.collider.stats()
            sat = session.collider.saturation.sense() if hasattr(session.collider, "saturation") else None
            self._json({
                "fingerprint": {
                    "session_id": session_id,
                    "born": session.born,
                    "zodiac": session.zodiac,
                    "exchange_count": session.exchange_count,
                    "collider_stats": stats,
                    "saturation_level": sat.saturation_level if sat else 0.0,
                    "saturated": sat.saturated if sat else False,
                    "v_score": session.cumulative_v_score,
                    "muster": session.muster_result,
                },
                "available": True,
            })
        except Exception as e:
            print(f"[g.void] Fingerprint error: {e}", file=sys.stderr)
            self._json({"error": f"Fingerprint failed: {e}"}, 500)

    # ── Static File Serving ───────────────────────────────────

    def _serve_index(self):
        static_dir: Path | None = self.server._static_dir  # type: ignore
        if static_dir:
            index = static_dir / "index.html"
            if index.exists():
                self._serve_file(index)
                return
        # Inline fallback: minimal HTML that fetches from the API
        self._serve_fallback_html()

    def _serve_static(self, path: str):
        static_dir: Path | None = self.server._static_dir  # type: ignore
        if static_dir is None:
            self._json({"error": "Static dir not configured"}, 404)
            return

        # Sanitize path: no directory traversal
        clean = path.lstrip("/")
        if ".." in clean:
            self._json({"error": "Forbidden"}, 403)
            return

        target = static_dir / clean
        if target.exists() and target.is_file():
            self._serve_file(target)
        else:
            # SPA fallback: serve index.html for unknown paths
            index = static_dir / "index.html"
            if index.exists():
                self._serve_file(index)
            else:
                self._json({"error": f"Not found: {path}"}, 404)

    def _serve_file(self, path: Path):
        try:
            data = path.read_bytes()
            mime = _mime_type(path.name)
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(data)
        except OSError as e:
            print(f"[g.void] File serve error: {e}", file=sys.stderr)
            self._json({"error": "Internal error"}, 500)

    def _serve_fallback_html(self):
        """Minimal fallback HTML when g-void directory is not found."""
        html = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>g.void</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #080c18; color: #e8e8ec; font-family: system-ui, sans-serif;
    display: flex; flex-direction: column; height: 100vh; }
  .h { padding: 14px 20px; border-bottom: 1px solid #1a2030; }
  .h .n { color: #f0a830; font-size: 15px; font-weight: 600; }
  .msgs { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
  .msg { max-width: 600px; margin: 0 auto; width: 100%; }
  .msg.h-msg .b { background: #0e1420; border: 1px solid #1a2030; border-radius: 14px 14px 4px 14px; padding: 12px 16px; display: inline-block; }
  .msg.v-msg .b { color: #f0a830; font-style: italic; padding-left: 2px; }
  .inp { padding: 14px 20px; border-top: 1px solid #1a2030; background: #0e1420; }
  .inp-row { display: flex; gap: 10px; max-width: 600px; margin: 0 auto; }
  textarea { flex: 1; background: #141a28; border: 1px solid #1a2030; border-radius: 12px; padding: 12px 16px; color: #e8e8ec; font-size: 15px; font-family: inherit; resize: none; outline: none; }
  button { background: #f0a830; color: #080c18; border: none; border-radius: 12px; width: 46px; font-size: 18px; cursor: pointer; }
</style>
</head>
<body>
<div class="h"><div class="n">g.void</div></div>
<div class="msgs" id="msgs"></div>
<div class="inp">
  <div class="inp-row">
    <textarea id="inp" rows="1" placeholder="Schreib etwas..."></textarea>
    <button onclick="send()">&#10148;</button>
  </div>
</div>
<script>
let sid = null;
const msgs = document.getElementById('msgs');
const inp = document.getElementById('inp');

function addMsg(role, text) {
  const d = document.createElement('div');
  d.className = 'msg ' + (role === 'human' ? 'h-msg' : 'v-msg');
  const b = document.createElement('div');
  b.className = 'b';
  b.textContent = text;
  d.appendChild(b);
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
}

async function send() {
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  addMsg('human', text);
  const body = { message: text };
  if (sid) body.session_id = sid;
  const r = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const d = await r.json();
  sid = d.session_id;
  addMsg('void', d.response);
}

inp.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
</script>
</body>
</html>"""
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    # ── Helpers ───────────────────────────────────────────────

    def _read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            self._json({"error": f"Invalid JSON: {e}"}, 400)
            return None

    def _json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


# ── GVoidHTTPServer ────────────────────────────────────────────────────

class GVoidHTTPServer(HTTPServer):
    """HTTPServer subclass carrying g.void server state."""

    def __init__(
        self,
        sessions: SessionStore,
        llm: _GVoidLLM,
        static_dir: Path | None,
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        self._sessions = sessions
        self._llm = llm
        self._static_dir = static_dir
        super().__init__((host, port), GVoidHandler)


# ── Public Entry Point ─────────────────────────────────────────────────

def serve_g_void(
    host: str = "0.0.0.0",
    port: int = 8080,
    static_dir: str | None = None,
) -> None:
    """Start the g.void server. Blocks until interrupted.

    Args:
        host:       Bind address. Default "0.0.0.0" (all interfaces).
        port:       HTTP port. Default 8080.
        static_dir: Path to g-void static files (index.html etc.).
                    Auto-detected if None.
    """
    static_path = _find_static_dir(static_dir)

    sessions = SessionStore()
    llm = _GVoidLLM()

    server = GVoidHTTPServer(
        sessions=sessions,
        llm=llm,
        static_dir=static_path,
        host=host,
        port=port,
    )

    # Eager LLM init in background (avoid cold start on first request)
    threading.Thread(target=llm.get, daemon=True).start()

    print(f"  g.void server listening on http://{host}:{port}", file=sys.stderr)
    if static_path:
        print(f"  Static files: {static_path}", file=sys.stderr)
    else:
        print(f"  Static files: not found (using inline fallback)", file=sys.stderr)
    print(f"  Press Ctrl+C to stop.", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  g.void shutting down.", file=sys.stderr)
        server.server_close()


if __name__ == "__main__":
    import sys as _sys
    _port = 8080
    for _a in _sys.argv[1:]:
        try:
            _port = int(_a)
        except ValueError:
            pass
    serve_g_void(port=_port)
