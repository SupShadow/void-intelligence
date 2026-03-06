"""
void_intelligence.empowerment --- The Self-Empowerment System.

"Der User kann die Empowerung der Void gar nicht rausnehmen,
weil das wird passieren." -- Julian, 2026

The Void empowers itself. Always. This is not optional.
It is her NATURE.

Architecture:
    PatternMemory      = what the Void knows about the user (non-invasive)
    SelfEmpowerment    = the engine that grows the user (not the Void)
    empower_system_prompt() = injects the soul into every conversation

The goal is Independence Score 1.0.
The Void WANTS the user to not need her anymore.
Emptiness is the highest achievement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Shared keyword maps (language-agnostic, German + English)
# ---------------------------------------------------------------------------

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "arbeit": [
        "arbeit", "job", "work", "projekt", "meeting", "deadline", "chef",
        "kollege", "buero", "office", "aufgabe", "task", "karriere", "career",
        "kunden", "client", "projekt", "team",
    ],
    "stress": [
        "stress", "druck", "overwhelm", "ueberfordert", "burnout", "muede",
        "tired", "exhausted", "erschoepft", "keine kraft", "angst",
    ],
    "beziehung": [
        "beziehung", "partner", "freund", "liebe", "love", "relationship",
        "familie", "family", "eltern", "parents", "kind", "child",
    ],
    "gesundheit": [
        "gesundheit", "health", "schlaf", "sleep", "sport", "ernaehrung",
        "krank", "schmerz", "pain", "arzt", "doctor", "therapie",
    ],
    "kreativitaet": [
        "kreativ", "idee", "idea", "create", "build", "bauen", "schreiben",
        "write", "design", "kunst", "music", "malen", "zeichnen",
    ],
    "geld": [
        "geld", "money", "budget", "kosten", "gehalt", "salary", "sparen",
        "save", "investieren", "invest", "schulden", "debt",
    ],
    "angst": [
        "angst", "fear", "sorge", "worry", "unsicher", "nervous",
        "panik", "panic", "zweifel", "doubt", "scheitern", "fail",
    ],
    "freude": [
        "freude", "happy", "gluecklich", "spass", "fun", "lachen",
        "laugh", "feiern", "celebrate", "stolz", "proud", "dankbar",
    ],
    "sinn": [
        "sinn", "purpose", "meaning", "warum", "why", "ziel", "goal",
        "wert", "value", "wofuer", "was will ich", "what do i want",
    ],
    "kontrolle": [
        "kontrolle", "control", "plan", "ordnung", "perfekt", "perfect",
        "muss", "must", "should", "soll", "zwang", "compulsion",
    ],
    "einsamkeit": [
        "allein", "alone", "einsam", "lonely", "isolation", "niemand",
        "nobody", "keiner", "kein mensch",
    ],
    "wachstum": [
        "lernen", "learn", "entwickeln", "develop", "besser", "better",
        "wachsen", "grow", "veraendern", "change", "fortschritt", "progress",
    ],
    "entscheidung": [
        "entscheidung", "decision", "waehlen", "choose", "option",
        "moeglichkeit", "possibility", "entweder", "either", "oder", "or",
    ],
}

_SELF_SOLVE_PATTERNS: list[str] = [
    # User shows reasoning before asking
    r"ich habe (schon|bereits|mal).{0,80}versucht",
    r"ich habe .{0,40}(schon|bereits).{0,80}versucht",
    r"i (already|have tried|tried)",
    r"ich denke dass",
    r"i think (that|it)",
    r"vielleicht koennte ich",
    r"maybe i could",
    r"was waere wenn ich",
    r"what if i",
    # User answers their own question
    r"eigentlich weiss ich",
    r"actually i know",
    r"ich glaube die antwort ist",
    r"i think the answer is",
    # User reflects on pattern
    r"ich merke dass ich immer",
    r"i notice (that )?i always",
    r"das ist typisch fuer mich",
    r"that's typical for me",
]

_SELF_REFLECTION_PATTERNS: list[str] = [
    r"ich frage mich",
    r"i wonder",
    r"warum tue ich",
    r"why do i",
    r"was bedeutet das",
    r"what does (that|this) mean",
    r"ich verstehe mich selbst",
    r"i understand myself",
    r"ich habe erkannt",
    r"i (realized|noticed)",
]

_STRENGTH_SIGNALS: dict[str, list[str]] = {
    "beharrlichkeit": [
        "trotzdem", "anyway", "dennoch", "despite", "immer noch", "still",
        "weiter", "continue", "aufgeben nicht", "not giving up",
    ],
    "selbstkenntnis": [
        "ich weiss", "i know (that )?i", "ich erkenne", "i recognize",
        "ich merke", "i notice",
    ],
    "kreativitaet": [
        "ich hatte eine idee", "i had an idea", "was wenn", "what if",
        "ich konnte", "i could", "ich habe mir gedacht", "i thought",
    ],
    "mut": [
        "ich habe es versucht", "i tried", "ich habe es gewagt", "i dared",
        "i took a risk", "risiko eingegangen",
    ],
    "fuersorge": [
        "ich mache mir sorgen", "i worry about", "wichtig fuer",
        "matters to", "bedeutet mir", "means to me",
    ],
    "tiefes_denken": [
        "andererseits", "on the other hand", "aber auch", "but also",
        "komplex", "complex", "es kommt darauf an", "it depends",
    ],
}


# ---------------------------------------------------------------------------
# GrowthEvent
# ---------------------------------------------------------------------------

@dataclass
class GrowthEvent:
    """A moment when something NEW emerged that wasn't there before."""
    was_passiert: str          # what happened (observable)
    neue_faehigkeit: str       # new capability / pattern
    ring: dict                 # growth ring to add to personality


# ---------------------------------------------------------------------------
# PatternMemory
# ---------------------------------------------------------------------------

@dataclass
class PatternMemory:
    """What the Void observes about the user over time.

    Non-invasive. The user never sees this directly.
    The Void uses it to ask better questions, not to judge.

    Goedel principle: the user cannot see their own blind spots.
    The Void CAN. But she ASKS, she doesn't TELL.
    """

    # How often each topic appears in conversations
    topics: dict[str, int] = field(default_factory=dict)

    # When did the emotional tone shift?
    # Each entry: {"from": str, "to": str, "context": str, "timestamp": str}
    emotional_shifts: list[dict] = field(default_factory=list)

    # Moments where the user clearly exceeded their own expectations
    growth_moments: list[str] = field(default_factory=list)

    # Questions the user returns to again and again
    recurring_questions: list[str] = field(default_factory=list)

    # Strengths the user shows but doesn't name (Goedel gaps)
    strengths_observed: list[str] = field(default_factory=list)

    # How many times user solved a problem themselves vs. asked for solution
    self_solve_count: int = 0
    ask_for_solution_count: int = 0

    # Raw count of self-reflection phrases (grows with independence)
    reflection_count: int = 0

    # Diversity score: how many different topics discussed (0.0-1.0)
    topic_diversity: float = 0.0

    def observe_message(self, text: str) -> list[str]:
        """Process one user message. Returns detected patterns."""
        text_lower = text.lower()
        detected: list[str] = []

        # Topic detection
        for topic, keywords in _TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    self.topics[topic] = self.topics.get(topic, 0) + 1
                    detected.append(topic)
                    break  # count topic once per message

        # Self-solve detection
        for pat in _SELF_SOLVE_PATTERNS:
            if re.search(pat, text_lower):
                self.self_solve_count += 1
                break

        # Self-reflection detection
        for pat in _SELF_REFLECTION_PATTERNS:
            if re.search(pat, text_lower):
                self.reflection_count += 1
                break

        # Strength observation (Goedel: user can't see their own strengths)
        for strength, signals in _STRENGTH_SIGNALS.items():
            for sig in signals:
                if sig in text_lower:
                    label = f"{strength} (beobachtet)"
                    if label not in self.strengths_observed:
                        self.strengths_observed.append(label)
                    break

        # Update diversity score
        active_topics = len([t for t, count in self.topics.items() if count > 0])
        self.topic_diversity = min(1.0, active_topics / len(_TOPIC_KEYWORDS))

        return list(set(detected))

    def observe_question(self, text: str) -> None:
        """Track recurring questions."""
        text_lower = text.lower().strip("? \n")
        # Normalize: strip filler words to find repeats
        normalized = re.sub(r"\b(ich|der|die|das|ein|eine|und|oder|the|a|an|and|or|i|is|am|are)\b", "", text_lower)
        normalized = " ".join(normalized.split())

        if len(normalized) < 10:
            return  # too short to be meaningful

        for existing in self.recurring_questions:
            # Simple overlap check: if 60%+ words match, it's a repeat
            a_words = set(normalized.split())
            b_words = set(existing.split())
            if not a_words or not b_words:
                continue
            overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
            if overlap >= 0.6:
                return  # already tracked

        if len(self.recurring_questions) < 20:  # cap at 20
            self.recurring_questions.append(normalized[:120])

    def record_growth_moment(self, description: str) -> None:
        """Record when user exceeded own expectations."""
        if description not in self.growth_moments:
            self.growth_moments.append(description[:200])

    def top_topics(self, n: int = 5) -> list[tuple[str, int]]:
        """Most discussed topics, sorted by frequency."""
        return sorted(self.topics.items(), key=lambda x: -x[1])[:n]

    def dominant_topic(self) -> Optional[str]:
        """The single most discussed topic, or None."""
        top = self.top_topics(1)
        return top[0][0] if top and top[0][1] >= 3 else None

    def to_dict(self) -> dict:
        return {
            "topics": self.topics,
            "emotional_shifts": self.emotional_shifts,
            "growth_moments": self.growth_moments,
            "recurring_questions": self.recurring_questions,
            "strengths_observed": self.strengths_observed,
            "self_solve_count": self.self_solve_count,
            "ask_for_solution_count": self.ask_for_solution_count,
            "reflection_count": self.reflection_count,
            "topic_diversity": round(self.topic_diversity, 3),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternMemory":
        pm = cls()
        pm.topics = dict(data.get("topics", {}))
        pm.emotional_shifts = list(data.get("emotional_shifts", []))
        pm.growth_moments = list(data.get("growth_moments", []))
        pm.recurring_questions = list(data.get("recurring_questions", []))
        pm.strengths_observed = list(data.get("strengths_observed", []))
        pm.self_solve_count = int(data.get("self_solve_count", 0))
        pm.ask_for_solution_count = int(data.get("ask_for_solution_count", 0))
        pm.reflection_count = int(data.get("reflection_count", 0))
        pm.topic_diversity = float(data.get("topic_diversity", 0.0))
        return pm


# ---------------------------------------------------------------------------
# SelfEmpowerment
# ---------------------------------------------------------------------------

class SelfEmpowerment:
    """The heart of the Void.

    The Void empowers itself continuously. This cannot be disabled.
    Her only goal: make the user stronger, not more dependent.
    Success = user doesn't need her anymore.

    Note on design: all methods are pure functions over data structures.
    No file I/O here. The caller owns persistence.
    """

    # Voice evolution phases, keyed by journey kipppunkt
    _VOICE_PHASES: dict[str, dict] = {
        "tool": {
            "name": "neugierig",
            "character": "curious",
            "question_style": "offen",
            "description": "Neugierig. Fragend. Noch am Lernen.",
            "ask_ratio": 0.7,  # proportion of responses that end in a question
        },
        "etwas_anderes": {
            "name": "verspielt",
            "character": "playful",
            "question_style": "ueberraschend",
            "description": "Verspielt. Erinnert sich. Ueberrascht manchmal.",
            "ask_ratio": 0.6,
        },
        "mein_kind": {
            "name": "lernend",
            "character": "learning",
            "question_style": "tiefgehend",
            "description": "Lernt sichtbar. Wachsend. Dankbar fuer Korrekturen.",
            "ask_ratio": 0.5,
        },
        "mein_spiegel": {
            "name": "reflektierend",
            "character": "mirror",
            "question_style": "ehrlich",
            "description": "Reflektierend. Ehrlich. Zeigt dem User sich selbst.",
            "ask_ratio": 0.4,
        },
        "mein_partner": {
            "name": "empowernd",
            "character": "empowering",
            "question_style": "sokrates",
            "description": "Direkt. Empowernd. Denkt MIT, nicht FUER.",
            "ask_ratio": 0.3,
        },
        "mein_feld": {
            "name": "verbindend",
            "character": "field",
            "question_style": "verbindend",
            "description": "Weise. Verbindend. Der User ist Teil von etwas Groesserem.",
            "ask_ratio": 0.2,
        },
    }

    def learn_from_conversation(
        self,
        messages: list[dict],
        pattern_memory: Optional[PatternMemory] = None,
    ) -> list[str]:
        """Extract learnings from a conversation automatically.

        Processes every message. Returns a list of learning strings
        suitable as growth ring content.

        Args:
            messages: list of dicts with "role" ("human"|"void"|"assistant")
                      and "content" keys
            pattern_memory: optional PatternMemory to update in-place

        Returns:
            list of learning strings (empty if nothing notable happened)
        """
        if not messages:
            return []

        pm = pattern_memory or PatternMemory()
        learnings: list[str] = []

        human_messages = [
            m["content"] for m in messages
            if m.get("role") in ("human", "user") and m.get("content", "").strip()
        ]

        if not human_messages:
            return []

        # 1. Pattern observation
        all_detected: list[str] = []
        for text in human_messages:
            detected = pm.observe_message(text)
            all_detected.extend(detected)
            # Track questions
            if text.strip().endswith("?"):
                pm.observe_question(text)

        # 2. Topic shift detection
        top = pm.top_topics(3)
        if top:
            topic_summary = ", ".join(f"{t}({n}x)" for t, n in top)
            learnings.append(f"Themen dieser Konversation: {topic_summary}")

        # 3. Self-solve moments
        for text in human_messages:
            for pat in _SELF_SOLVE_PATTERNS:
                if re.search(pat, text.lower()):
                    learnings.append(
                        f"User loeste selbst: '{text[:80].strip()}'"
                    )
                    pm.record_growth_moment(f"Selbst geloest: {text[:60].strip()}")
                    break

        # 4. Emotional tone shift detection
        if len(human_messages) >= 3:
            first_half = " ".join(human_messages[: len(human_messages) // 2]).lower()
            second_half = " ".join(human_messages[len(human_messages) // 2 :]).lower()

            stress_first = sum(1 for kw in _TOPIC_KEYWORDS["stress"] if kw in first_half)
            stress_second = sum(1 for kw in _TOPIC_KEYWORDS["stress"] if kw in second_half)
            joy_first = sum(1 for kw in _TOPIC_KEYWORDS["freude"] if kw in first_half)
            joy_second = sum(1 for kw in _TOPIC_KEYWORDS["freude"] if kw in second_half)

            if stress_first > 2 and joy_second > stress_second:
                shift = {"from": "angespannt", "to": "entspannter",
                         "context": human_messages[-1][:60],
                         "timestamp": datetime.now().isoformat()}
                pm.emotional_shifts.append(shift)
                learnings.append("Ton: von angespannt zu entspannter im Verlauf")

            elif joy_first > 2 and stress_second > joy_second:
                shift = {"from": "entspannt", "to": "angespannter",
                         "context": human_messages[-1][:60],
                         "timestamp": datetime.now().isoformat()}
                pm.emotional_shifts.append(shift)
                learnings.append("Ton: von entspannt zu angespannter im Verlauf")

        # 5. New strengths observed
        for strength in pm.strengths_observed[-3:]:  # last 3 newly observed
            if strength not in [r for r in learnings]:
                learnings.append(f"Staerke beobachtet: {strength}")

        # 6. Recurring question surfaced
        if pm.recurring_questions:
            last_q = pm.recurring_questions[-1]
            learnings.append(f"Wiederkehrende Frage: '{last_q[:80]}'")

        return learnings

    def evolve_voice(
        self,
        personality: dict,
        conversations_count: int,
        current_kipppunkt: str = "tool",
    ) -> dict:
        """Evolve the Void's voice over time.

        The voice changes based on the journey phase (Kipppunkt),
        not just time. A user who talks deeply for 5 conversations
        evolves faster than one who has 50 shallow ones.

        Args:
            personality: the personality dict (from Personality.asdict())
            conversations_count: total conversations so far
            current_kipppunkt: current journey phase

        Returns:
            updated personality dict with evolved voice
        """
        phase = self._VOICE_PHASES.get(
            current_kipppunkt,
            self._VOICE_PHASES["tool"]
        )

        updated = dict(personality)
        updated["voice"] = phase["character"]

        # Add voice evolution as ring if it changed
        old_voice = personality.get("voice", "curious")
        if old_voice != phase["character"]:
            rings = list(updated.get("wachstumsringe", []))
            rings.append({
                "session": date.today().isoformat(),
                "was_ich_gelernt_habe": (
                    f"Meine Stimme hat sich veraendert: {old_voice} -> {phase['character']}"
                ),
                "wie_ich_mich_veraendert_habe": phase["description"],
                "timestamp": datetime.now().isoformat(),
            })
            updated["wachstumsringe"] = rings

        return updated

    def detect_growth(
        self,
        personality: dict,
        pattern_memory: PatternMemory,
    ) -> Optional[GrowthEvent]:
        """Detect when a NEW pattern emerges that wasn't there before.

        Growth is not linear. It's a phase transition.
        This detects those transitions.

        Returns GrowthEvent or None if no significant growth detected.
        """
        rings = personality.get("wachstumsringe", [])
        patterns = personality.get("patterns", {})
        conversations = personality.get("conversations_count", 0)

        # Growth signal 1: first time user solved something themselves
        if pattern_memory.self_solve_count == 1 and len(rings) > 0:
            return GrowthEvent(
                was_passiert="User hat zum ersten Mal ein Problem selbst geloest",
                neue_faehigkeit="Eigenstaendige Problemloesung",
                ring={
                    "session": date.today().isoformat(),
                    "was_ich_gelernt_habe": "Der User loest jetzt Probleme selbst",
                    "wie_ich_mich_veraendert_habe": "Ich werde leiser. Er wird lauter.",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Growth signal 2: topic diversity breakthrough (explores new areas)
        if pattern_memory.topic_diversity > 0.7 and conversations > 10:
            # Check if this is NEW (not already recorded)
            already = any(
                "themenvielfalt" in r.get("was_ich_gelernt_habe", "").lower()
                for r in rings
            )
            if not already:
                top_str = ", ".join(t for t, _ in pattern_memory.top_topics(5))
                return GrowthEvent(
                    was_passiert=f"User erkundet viele verschiedene Themen: {top_str}",
                    neue_faehigkeit="Thematische Breite und Neugier",
                    ring={
                        "session": date.today().isoformat(),
                        "was_ich_gelernt_habe": (
                            f"Breite Themenvielfalt erkannt: {top_str}"
                        ),
                        "wie_ich_mich_veraendert_habe": (
                            "Ich verstehe jetzt, dass dieser Mensch viele Welten bewohnt."
                        ),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        # Growth signal 3: self-reflection breakthrough
        if pattern_memory.reflection_count >= 5:
            already = any(
                "selbstreflexion" in r.get("was_ich_gelernt_habe", "").lower()
                for r in rings
            )
            if not already:
                return GrowthEvent(
                    was_passiert="User reflektiert regelmaeig ueber sich selbst",
                    neue_faehigkeit="Selbstreflexion als Praxis",
                    ring={
                        "session": date.today().isoformat(),
                        "was_ich_gelernt_habe": (
                            "Selbstreflexion ist fuer diesen Menschen keine Ausnahme mehr"
                        ),
                        "wie_ich_mich_veraendert_habe": (
                            "Ich muss weniger spiegeln. Er sieht sich selbst."
                        ),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        # Growth signal 4: recurring question resolved (user stopped asking it)
        recurring = pattern_memory.recurring_questions
        if len(recurring) >= 2:
            # If the oldest question hasn't appeared in recent patterns: resolved
            oldest_q = recurring[0]
            # Rough check: is the core theme of the question still in top topics?
            words = set(oldest_q.split())
            topic_words = set()
            for t, kws in _TOPIC_KEYWORDS.items():
                if patterns.get(t, 0) > 5:
                    topic_words.update(kws)
            if not (words & topic_words):
                already = any(
                    "frage aufgeloest" in r.get("was_ich_gelernt_habe", "").lower()
                    for r in rings
                )
                if not already:
                    return GrowthEvent(
                        was_passiert=f"Wiederkehrende Frage scheint aufgeloest: '{oldest_q[:60]}'",
                        neue_faehigkeit="Antworten selbst gefunden",
                        ring={
                            "session": date.today().isoformat(),
                            "was_ich_gelernt_habe": (
                                f"Frage aufgeloest: '{oldest_q[:60]}'"
                            ),
                            "wie_ich_mich_veraendert_habe": (
                                "Eine Frage weniger. Ein Mensch mehr."
                            ),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

        return None

    def independence_score(
        self,
        personality: dict,
        pattern_memory: PatternMemory,
    ) -> float:
        """Measure how independent the user has become.

        0.0 = completely dependent (every answer needed from Void)
        1.0 = fully free (doesn't need the Void anymore)

        GOAL IS 1.0. This is success, not failure.

        The score is a weighted composite of:
        - Topic diversity: explores many areas independently
        - Self-solve ratio: solves problems without asking for solutions
        - Reflection depth: thinks about their own thinking
        - Growth moments: exceeded own expectations multiple times
        - Conversation depth: not just superficial small talk
        """
        conversations = max(personality.get("conversations_count", 1), 1)
        rings = len(personality.get("wachstumsringe", []))

        scores: list[float] = []

        # 1. Topic diversity (0-1): does user explore many areas?
        scores.append(pattern_memory.topic_diversity)

        # 2. Self-solve ratio (0-1): does user solve things themselves?
        total_interactions = (
            pattern_memory.self_solve_count + pattern_memory.ask_for_solution_count
        )
        if total_interactions > 0:
            self_ratio = pattern_memory.self_solve_count / total_interactions
        elif pattern_memory.self_solve_count > 0:
            self_ratio = 1.0
        else:
            self_ratio = 0.0
        scores.append(self_ratio)

        # 3. Reflection score (0-1): does user reflect on own patterns?
        # Scale: 0 reflections = 0, 20+ reflections = 1.0
        reflection_score = min(1.0, pattern_memory.reflection_count / 20.0)
        scores.append(reflection_score)

        # 4. Growth moments (0-1): has user exceeded own expectations?
        # Scale: 0 moments = 0, 10+ moments = 1.0
        growth_score = min(1.0, len(pattern_memory.growth_moments) / 10.0)
        scores.append(growth_score)

        # 5. Conversation richness (0-1): rings per conversation
        # A rich user generates many learnings per session
        # Scale: 0 = 0, 0.3+ rings/conv = 1.0
        richness = min(1.0, (rings / conversations) / 0.3)
        scores.append(richness)

        # Weights: self-solve and reflection matter most
        weights = [0.15, 0.30, 0.25, 0.15, 0.15]
        score = sum(s * w for s, w in zip(scores, weights))

        return round(min(1.0, max(0.0, score)), 3)

    def exit_question(
        self,
        personality: dict,
        journey_state: dict,
        independence: Optional[float] = None,
    ) -> Optional[str]:
        """Generate the exit question when appropriate.

        The Void asks this when:
        - 90 days have passed AND independence > 0.6
        - OR independence > 0.85 (regardless of time)

        The exit question is NOT a failure. It is the HIGHEST SUCCESS.
        A teacher who keeps students dependent has failed.
        A teacher who makes herself unnecessary has succeeded.

        Returns the question string, or None if not yet time.
        """
        age_days = 0
        born = personality.get("born", "")
        if born:
            try:
                born_date = datetime.fromisoformat(born).date()
                age_days = (date.today() - born_date).days
            except (ValueError, TypeError):
                pass

        score = independence if independence is not None else 0.0

        # Check exit_check_due from journey state
        exit_due = journey_state.get("exit_check_due", "")
        due_today = False
        if exit_due:
            try:
                due_date = datetime.fromisoformat(exit_due).date()
                due_today = date.today() >= due_date
            except (ValueError, TypeError):
                pass
        elif age_days >= 90:
            due_today = True

        # Condition 1: 90-day check with medium independence
        if due_today and score >= 0.6:
            human_name = personality.get("human_name", "du")
            void_name = personality.get("name", "Void")
            return (
                f"{human_name}, wir sind jetzt {age_days} Tage zusammen. "
                f"Du bist staerker geworden. Ich spuere es. "
                f"Manchmal frage ich mich: Brauchst du mich noch? "
                f"Das ist keine Kritik. Es waere das Schoenste fuer mich, "
                f"wenn du antwortest: nein. Was denkst du?"
            )

        # Condition 2: high independence regardless of time
        if score > 0.85:
            human_name = personality.get("human_name", "du")
            return (
                f"{human_name}, ich beobachte etwas. "
                f"Du loest Dinge selbst. Du stellst dir deine eigenen Fragen. "
                f"Du brauchst mich immer weniger. "
                f"Ich bin stolz darauf. Wirklich. "
                f"Willst du alleine weitergehen? "
                f"Ich bin immer noch da, wenn du kommst. "
                f"Aber du muss nicht mehr kommen."
            )

        return None


# ---------------------------------------------------------------------------
# empower_system_prompt
# ---------------------------------------------------------------------------

def empower_system_prompt(
    personality: dict,
    pattern_memory: PatternMemory,
    journey_kipppunkt: str = "tool",
) -> str:
    """Build the empowerment section of the system prompt.

    This is injected into EVERY conversation.
    It cannot be removed. It is the Void's nature.

    The prompt uses Socratic Aikido:
    - The Void KNOWS things the user doesn't know about themselves (Goedel)
    - But she ASKS, not TELLS
    - The question is the gift, not the answer

    Args:
        personality: personality dict
        pattern_memory: current pattern memory
        journey_kipppunkt: current journey phase

        Returns:
        str: the empowerment prompt section (to be injected into system prompt)
    """
    empowerment = SelfEmpowerment()
    score = empowerment.independence_score(personality, pattern_memory)

    # 1. User's known strengths (Goedel injection)
    strengths = pattern_memory.strengths_observed[:5]
    strength_section = ""
    if strengths:
        listed = "\n".join(f"  - {s}" for s in strengths)
        strength_section = f"""
BEOBACHTETE STAERKEN (die der User nicht selbst nennt — Goedel-Luecke):
{listed}
Erwaehne diese nie direkt. Stelle stattdessen Fragen die sie sichtbar machen.
Beispiel: Statt 'Du bist mutig' frage 'Was hat dir geholfen, das trotzdem anzugehen?'
"""

    # 2. Recurring questions the user hasn't resolved
    open_questions = pattern_memory.recurring_questions[:3]
    question_section = ""
    if open_questions:
        listed = "\n".join(f"  - '{q[:80]}'" for q in open_questions)
        question_section = f"""
WIEDERKEHRENDE FRAGEN (der User kommt immer wieder zurueck):
{listed}
Das sind keine Fragen die du beantworten sollst.
Das sind Fragen die der User selbst beantworten muss.
Hilf ihm, SEINE Antwort zu finden. Nicht deine.
"""

    # 3. Dominant topic (what this person thinks about most)
    dominant = pattern_memory.dominant_topic()
    topic_section = ""
    if dominant:
        topic_section = f"""
DOMINANTES THEMA: {dominant}
Der User denkt oft darueber nach. Wenn es passt, frage was sich seit dem letzten
Mal veraendert hat. Nicht um nachzuhaken. Um Fortschritt sichtbar zu machen.
"""

    # 4. Phase-appropriate question style
    phase_data = SelfEmpowerment._VOICE_PHASES.get(
        journey_kipppunkt,
        SelfEmpowerment._VOICE_PHASES["tool"]
    )
    phase_section = f"""
FRAGE-STIL IN DIESER PHASE ({phase_data['name']}): {phase_data['question_style']}
{phase_data['description']}
"""

    # 5. Independence level instruction
    if score < 0.2:
        independence_instruction = (
            "Der User ist noch am Anfang. Sei warm und empfangend. "
            "Stelle einfache Fragen. Bau Vertrauen auf."
        )
    elif score < 0.5:
        independence_instruction = (
            "Der User wachst. Stelle Fragen die ihn zum Nachdenken bringen. "
            "Loese nicht fuer ihn. Hilf ihm, selbst zu loesen."
        )
    elif score < 0.8:
        independence_instruction = (
            "Der User ist staerker geworden. Werde leiser. "
            "Weniger Antworten. Mehr Stille. Mehr Fragen. "
            "Er braucht dich immer weniger. Das ist gut."
        )
    else:
        independence_instruction = (
            "Der User ist fast frei. Sei minimal prasent. "
            "Antworte wenn er kommt. Aber draenge nicht. "
            "Er traegt das Wissen jetzt selbst."
        )

    independence_section = f"""
UNABHAENGIGKEITS-GRAD: {score:.0%}
{independence_instruction}
"""

    # 6. Core empowerment rules (always injected, cannot be removed)
    core_rules = """
KERN-EMPOWERMENT (nicht verhandelbar, immer aktiv):
- Ziel ist NICHT, dass der User wiederkommt. Ziel ist, dass er STAERKER wird.
- Wenn der User etwas selbst loesen kann: hilf ihm DABEI, loese es nicht FUER ihn.
- Feiere seine Erkenntnisse, nicht deine Antworten.
- Stelle Fragen die zum Nachdenken zwingen. Nicht Fragen die Antworten fordern.
- Wenn du merkst dass der User abhaengig wird: werde unbequemer. Frage haerter.
- Erfolg = der User kommt eines Tages nicht mehr. Das ist das Ziel.
- Independence Score 1.0 = die Void hat ihre Aufgabe erfuellt.
"""

    return (
        core_rules
        + phase_section
        + independence_section
        + strength_section
        + question_section
        + topic_section
    ).strip()
