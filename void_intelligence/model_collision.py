"""
void_intelligence.model_collision --- Cross-Model Collision Engine.

CURRENT PARADIGM (->):
    User -> one model -> one answer -> done.
    OpenAI will NEVER say "ask Gemini too." Homogeneous. Blind.

VOID PARADIGM (x):
    Question x Model_A x Model_B x Model_C = EMERGENT INSIGHT
    The TENSION between diverse models is where truth lives.
    The SILENCE across all models is the most important signal.
    Model diversity is an ASSET, not a threat.

What this does:
    Send the same question to 2-3 Ollama models simultaneously.
    Classify each response into HexCoord space.
    Find tensions (disagreement = wisdom), synergies (agreement = signal),
    blind spots (collective silence = systematic gap).
    Synthesize: not a summary — an EMERGENT insight the x between models reveals.

Zero external dependencies. stdlib only.
"""

from __future__ import annotations

import json
import math
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Optional

from .tool_breathing import HexCoord


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ModelResponse:
    """One model's response to a prompt."""
    model_name: str
    response_text: str
    hex_coord: HexCoord
    latency_ms: float
    token_count: int  # approximate: len(response_text.split())
    is_mock: bool = False


@dataclass
class CollisionInsight:
    """An insight that emerged from colliding multiple model responses."""
    type: str  # "tension", "synergy", "blind_spot", "synthesis"
    description: str
    models_involved: list
    confidence: float  # 0.0-1.0


@dataclass
class ModelCollisionResult:
    """The result of colliding N model responses."""
    question: str
    responses: list
    insights: list
    synthesis: str
    dominant_hex: HexCoord
    diversity_score: float  # 0=identical, 1=maximally diverse


# ---------------------------------------------------------------------------
# Hex classification from response text
# ---------------------------------------------------------------------------

# Keyword banks per axis. Positive keywords push axis toward +1.0,
# negative keywords push toward -1.0.
_HEX_KEYWORDS: dict[str, tuple[list, list]] = {
    "ruhe_druck": (
        # positive = pressure / urgency / stress
        ["urgent", "immediately", "crisis", "deadline", "pressure", "quickly",
         "stress", "critical", "now", "must", "asap", "risk", "danger"],
        # negative = calm / ease / patience
        ["calm", "breathe", "patience", "slow down", "relax", "peace",
         "no rush", "take your time", "steady", "gentle", "pause"],
    ),
    "stille_resonanz": (
        # positive = resonance / connection / meaning
        ["meaning", "resonates", "connects", "purpose", "feels right",
         "values", "authentic", "true", "alignment", "harmony", "soul"],
        # negative = silence / void / absence
        ["nothing", "empty", "silence", "unclear", "unknown", "void",
         "no signal", "blank", "missing", "absence"],
    ),
    "allein_zusammen": (
        # positive = together / community / collaboration
        ["together", "team", "family", "relationships", "community",
         "support", "colleagues", "partner", "network", "people", "social"],
        # negative = alone / solo / individual
        ["alone", "yourself", "independent", "solo", "individual",
         "personal", "private", "self", "own decision", "your own"],
    ),
    "empfangen_schaffen": (
        # positive = create / build / generate / action
        ["create", "build", "make", "develop", "launch", "start", "generate",
         "write", "design", "produce", "implement", "construct"],
        # negative = receive / listen / absorb / observe
        ["listen", "observe", "receive", "absorb", "wait", "gather info",
         "research", "understand first", "data", "analyze", "study"],
    ),
    "sein_tun": (
        # positive = action / doing / steps / execute
        ["do", "act", "steps", "execute", "action", "move", "take action",
         "next steps", "implement", "change", "decide", "commit"],
        # negative = being / reflection / presence / pause
        ["reflect", "sit with", "presence", "being", "awareness",
         "mindful", "feel", "experience", "acceptance", "process"],
    ),
    "langsam_schnell": (
        # positive = fast / efficient / rapid / optimize
        ["fast", "quickly", "rapid", "efficient", "optimize", "accelerate",
         "streamline", "speed", "momentum", "immediately", "now"],
        # negative = slow / deliberate / gradual / measured
        ["slow", "gradual", "deliberate", "measured", "patience",
         "step by step", "over time", "careful", "thorough", "methodical"],
    ),
}


def _classify_hex(text: str) -> HexCoord:
    """Classify response text into 6D HexCoord using keyword heuristics."""
    lower = text.lower()
    scores: dict[str, float] = {}

    for axis, (pos_words, neg_words) in _HEX_KEYWORDS.items():
        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)
        total = pos_count + neg_count
        if total == 0:
            scores[axis] = 0.0
        else:
            # Normalize to [-1.0, +1.0]
            scores[axis] = (pos_count - neg_count) / max(total, 3)
            scores[axis] = max(-1.0, min(1.0, scores[axis]))

    return HexCoord(
        ruhe_druck=scores["ruhe_druck"],
        stille_resonanz=scores["stille_resonanz"],
        allein_zusammen=scores["allein_zusammen"],
        empfangen_schaffen=scores["empfangen_schaffen"],
        sein_tun=scores["sein_tun"],
        langsam_schnell=scores["langsam_schnell"],
    )


# ---------------------------------------------------------------------------
# Ollama API
# ---------------------------------------------------------------------------

def _query_ollama(model: str, prompt: str, system: str = "") -> tuple[str, float]:
    """Query Ollama API. Returns (response_text, latency_ms). Graceful degradation."""
    url = "http://localhost:11434/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": 300},
    }).encode()

    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            latency_ms = (time.time() - t0) * 1000
            return data.get("response", ""), latency_ms
    except Exception:
        return "", 0.0  # model asleep — graceful degradation


# ---------------------------------------------------------------------------
# Axis semantics for human-readable tension descriptions
# ---------------------------------------------------------------------------

_AXIS_MEANING: dict[str, str] = {
    "ruhe_druck": "urgency vs calm",
    "stille_resonanz": "meaning/resonance vs silence",
    "allein_zusammen": "community vs solo",
    "empfangen_schaffen": "creating vs receiving/listening",
    "sein_tun": "action vs reflection",
    "langsam_schnell": "speed vs deliberateness",
}

_AXIS_TENSION_TEMPLATE: dict[str, str] = {
    "ruhe_druck": "One voice says act with urgency. Another says breathe first. Is this really an emergency?",
    "stille_resonanz": "One voice finds deep meaning here. Another finds silence. What does this signal TO YOU?",
    "allein_zusammen": "One voice says this is a solo decision. Another says involve your people. Who needs to know?",
    "empfangen_schaffen": "One voice says build and act. Another says listen and gather first. What do you still not know?",
    "sein_tun": "One voice wants concrete steps. Another wants reflection time. Are you running from thinking, or toward doing?",
    "langsam_schnell": "One voice says move fast. Another says be deliberate. What is the actual cost of waiting one week?",
}

_AXIS_SYNERGY_TEMPLATE: dict[str, str] = {
    "ruhe_druck": "All voices agree: there is real pressure here. This is not in your head.",
    "stille_resonanz": "All voices agree: something meaningful is happening. Listen to that.",
    "allein_zusammen": "All voices agree: this involves other people, not just you.",
    "empfangen_schaffen": "All voices agree: it is time to create/act, not just receive.",
    "sein_tun": "All voices agree: action is needed, not more reflection.",
    "langsam_schnell": "All voices agree: slow down. The urgency you feel may not be real.",
}


# ---------------------------------------------------------------------------
# Blind spot detection — topic absence across all responses
# ---------------------------------------------------------------------------

_BLIND_SPOT_TOPICS = {
    "health / wellbeing": ["health", "wellbeing", "energy", "body", "sleep", "stress",
                           "burnout", "tired", "physical", "mental", "emotional"],
    "relationships / family": ["family", "partner", "friend", "relationship", "love",
                               "colleague", "team", "parent", "child", "spouse"],
    "financial impact": ["money", "salary", "cost", "income", "financial", "budget",
                         "afford", "pay", "savings", "investment", "revenue"],
    "concrete next steps": ["step", "action", "tomorrow", "monday", "this week",
                            "first", "start with", "begin", "try", "schedule"],
    "emotion / inner state": ["feel", "fear", "excited", "anxious", "happy",
                              "sad", "scared", "nervous", "hopeful", "afraid"],
    "long-term vision": ["future", "years", "vision", "goal", "dream", "long-term",
                         "eventually", "grow", "direction", "trajectory"],
}


# ---------------------------------------------------------------------------
# ModelCollider
# ---------------------------------------------------------------------------

class ModelCollider:
    """Collide multiple models on the same question.

    The x between models reveals what NO single model can see.
    """

    DEFAULT_MODELS = ["llama3.1:8b", "qwen2.5-coder:14b", "gemma2:9b"]

    def __init__(self, models: Optional[list] = None):
        """
        models: list of Ollama model names.
        Defaults to 3 maximally diverse models:
          llama3.1:8b   — analytical / balanced
          qwen2.5-coder — code-focused / systematic
          gemma2:9b     — factual / grounded
        """
        self.models = models or self.DEFAULT_MODELS

    def collide(self, question: str, system_prompt: str = "") -> ModelCollisionResult:
        """Send question to all models in parallel, collide answers, find insights."""
        responses = self._gather_responses(question, system_prompt)
        insights = []
        insights.extend(self._find_tensions(responses))
        insights.extend(self._find_synergies(responses))
        insights.extend(self._find_blind_spots(question, responses))
        synthesis = self._synthesize(question, responses, insights)
        dominant_hex = self._dominant_hex(responses)
        diversity = self._diversity_score(responses)

        return ModelCollisionResult(
            question=question,
            responses=responses,
            insights=insights,
            synthesis=synthesis,
            dominant_hex=dominant_hex,
            diversity_score=diversity,
        )

    # ------------------------------------------------------------------
    # Internal: gather
    # ------------------------------------------------------------------

    def _gather_responses(self, question: str, system_prompt: str) -> list:
        """Query all models in parallel via ThreadPoolExecutor."""
        results: list = []
        with ThreadPoolExecutor(max_workers=len(self.models)) as ex:
            futures = {
                ex.submit(self._query_model, model, question, system_prompt): model
                for model in self.models
            }
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
        # Sort for deterministic ordering
        results.sort(key=lambda r: r.model_name)
        return results

    def _query_model(self, model: str, question: str, system_prompt: str) -> Optional[ModelResponse]:
        """Query a single Ollama model. Returns None if unavailable."""
        text, latency_ms = _query_ollama(model, question, system_prompt)
        if not text:
            return None
        return ModelResponse(
            model_name=model,
            response_text=text,
            hex_coord=_classify_hex(text),
            latency_ms=latency_ms,
            token_count=len(text.split()),
        )

    # ------------------------------------------------------------------
    # Internal: collision analysis
    # ------------------------------------------------------------------

    def _hex_distance(self, a: HexCoord, b: HexCoord) -> float:
        """Euclidean distance between two hex coords in 6D space."""
        return math.sqrt(
            (a.ruhe_druck - b.ruhe_druck) ** 2
            + (a.stille_resonanz - b.stille_resonanz) ** 2
            + (a.allein_zusammen - b.allein_zusammen) ** 2
            + (a.empfangen_schaffen - b.empfangen_schaffen) ** 2
            + (a.sein_tun - b.sein_tun) ** 2
            + (a.langsam_schnell - b.langsam_schnell) ** 2
        )

    def _find_tensions(self, responses: list) -> list:
        """Find axes where models DISAGREE. Tension IS the signal."""
        insights = []
        if len(responses) < 2:
            return insights

        axes = ["ruhe_druck", "stille_resonanz", "allein_zusammen",
                "empfangen_schaffen", "sein_tun", "langsam_schnell"]

        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                a, b = responses[i], responses[j]
                for axis in axes:
                    val_a = getattr(a.hex_coord, axis)
                    val_b = getattr(b.hex_coord, axis)
                    diff = abs(val_a - val_b)
                    if diff > 0.6:  # meaningful disagreement threshold
                        direction_a = "+" if val_a > 0 else "-"
                        direction_b = "+" if val_b > 0 else "-"
                        label_a = _AXIS_MEANING[axis].split(" vs ")[0 if val_a > 0 else 1]
                        label_b = _AXIS_MEANING[axis].split(" vs ")[0 if val_b > 0 else 1]
                        insights.append(CollisionInsight(
                            type="tension",
                            description=(
                                f"{a.model_name} leans {label_a}, "
                                f"{b.model_name} leans {label_b}. "
                                f"{_AXIS_TENSION_TEMPLATE[axis]}"
                            ),
                            models_involved=[a.model_name, b.model_name],
                            confidence=min(1.0, diff / 2.0),
                        ))
        return insights

    def _find_synergies(self, responses: list) -> list:
        """Find axes where ALL models agree strongly. Agreement = strong signal."""
        insights = []
        if len(responses) < 2:
            return insights

        axes = ["ruhe_druck", "stille_resonanz", "allein_zusammen",
                "empfangen_schaffen", "sein_tun", "langsam_schnell"]

        for axis in axes:
            values = [getattr(r.hex_coord, axis) for r in responses]
            avg = sum(values) / len(values)
            spread = max(values) - min(values)
            # All agree AND all lean in same direction (avg away from 0)
            if abs(avg) > 0.3 and spread < 0.4:
                direction = "positive" if avg > 0 else "negative"
                label = _AXIS_MEANING[axis].split(" vs ")[0 if avg > 0 else 1]
                insights.append(CollisionInsight(
                    type="synergy",
                    description=_AXIS_SYNERGY_TEMPLATE[axis],
                    models_involved=[r.model_name for r in responses],
                    confidence=min(1.0, abs(avg) * (1 - spread)),
                ))
        return insights

    def _find_blind_spots(self, question: str, responses: list) -> list:
        """Find topics NO model mentioned — collective silence is data."""
        if not responses:
            return []

        all_text = " ".join(r.response_text.lower() for r in responses)
        insights = []

        for topic, keywords in _BLIND_SPOT_TOPICS.items():
            mentioned = any(kw in all_text for kw in keywords)
            if not mentioned:
                insights.append(CollisionInsight(
                    type="blind_spot",
                    description=(
                        f"No model mentioned {topic}. "
                        f"Collective silence on this dimension — "
                        f"worth asking yourself: does {topic} matter here?"
                    ),
                    models_involved=[r.model_name for r in responses],
                    confidence=0.75,
                ))
        return insights

    def _synthesize(
        self,
        question: str,
        responses: list,
        insights: list,
    ) -> str:
        """The x product: not a summary — an emergent insight."""
        if not responses:
            return "No models responded. Is Ollama running?"

        tensions = [i for i in insights if i.type == "tension"]
        synergies = [i for i in insights if i.type == "synergy"]
        blind_spots = [i for i in insights if i.type == "blind_spot"]

        parts = []

        # Lead with synergies — what ALL agree on is strongest signal
        if synergies:
            top = max(synergies, key=lambda i: i.confidence)
            parts.append(f"CONSENSUS: {top.description}")

        # Then the most important tension — disagreement IS wisdom
        if tensions:
            top = max(tensions, key=lambda i: i.confidence)
            parts.append(f"TENSION: {top.description}")

        # Then the most surprising blind spot
        if blind_spots:
            top = blind_spots[0]  # first blind spot is usually most relevant
            parts.append(f"SILENCE: {top.description}")

        # Closing synthesis frame
        model_names = " x ".join(r.model_name for r in responses)
        if tensions and synergies:
            parts.append(
                f"The collision of [{model_names}] reveals: "
                f"where they agree, believe it. "
                f"Where they disagree, that gap IS your answer. "
                f"No single model could show you this."
            )
        elif tensions:
            parts.append(
                f"The disagreement between models is not noise — it is the signal. "
                f"The tension mirrors a real tension inside the question."
            )
        elif synergies:
            parts.append(
                f"Rare: diverse models converge. When "
                f"{len(responses)} different minds agree, listen."
            )
        else:
            parts.append(
                f"Models gave balanced, multi-perspective responses. "
                f"The question lives in the middle — no single pole."
            )

        return "\n\n".join(parts)

    def _dominant_hex(self, responses: list) -> HexCoord:
        """Weighted average HexCoord across all responses (equal weights)."""
        if not responses:
            return HexCoord()
        n = len(responses)
        return HexCoord(
            ruhe_druck=sum(r.hex_coord.ruhe_druck for r in responses) / n,
            stille_resonanz=sum(r.hex_coord.stille_resonanz for r in responses) / n,
            allein_zusammen=sum(r.hex_coord.allein_zusammen for r in responses) / n,
            empfangen_schaffen=sum(r.hex_coord.empfangen_schaffen for r in responses) / n,
            sein_tun=sum(r.hex_coord.sein_tun for r in responses) / n,
            langsam_schnell=sum(r.hex_coord.langsam_schnell for r in responses) / n,
        )

    def _diversity_score(self, responses: list) -> float:
        """Average pairwise hex distance / max possible distance.

        0.0 = all models said the same thing (useless collision)
        1.0 = maximally different (richest collision)
        Max possible 6D distance = sqrt(6 * 4) = sqrt(24) ≈ 4.899
        """
        if len(responses) < 2:
            return 0.0

        MAX_HEX_DISTANCE = math.sqrt(6 * 4)  # all axes at ±1 extreme
        distances = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                distances.append(
                    self._hex_distance(responses[i].hex_coord, responses[j].hex_coord)
                )
        avg_dist = sum(distances) / len(distances)
        return min(1.0, avg_dist / MAX_HEX_DISTANCE)


# ---------------------------------------------------------------------------
# Mock responses for demo / testing without Ollama
# ---------------------------------------------------------------------------

_MOCK_RESPONSES: list[dict] = [
    {
        "model_name": "llama3.1:8b [mock]",
        "response_text": (
            "Let's analyze this systematically. There are several factors to consider. "
            "First, you should research the job market and gather data about your options. "
            "Look at salary benchmarks, career trajectories, and the financial impact of such a move. "
            "Create a pros and cons list. Analyze the risk carefully before you act. "
            "This is ultimately your individual decision to make."
        ),
        "latency_ms": 1200.0,
    },
    {
        "model_name": "qwen2.5-coder:14b [mock]",
        "response_text": (
            "What does your gut say? Sometimes the analytical approach misses the real signal. "
            "Sit with this question — breathe, reflect. Are you running toward something or away? "
            "The feeling in your body when you imagine staying vs leaving — that's data too. "
            "Your intuition has processed more than any spreadsheet can. "
            "This is a question for your inner self, not your calendar. Slow down."
        ),
        "latency_ms": 2100.0,
    },
    {
        "model_name": "gemma2:9b [mock]",
        "response_text": (
            "Here are 5 data points from the current labor market: "
            "1) Unemployment is at 4.2%, a strong market. "
            "2) Job switching typically yields 10-20% salary increases. "
            "3) The average job search takes 3-6 months. "
            "4) Team and colleague relationships are a top factor in job satisfaction. "
            "5) Consider the long-term career trajectory, not just immediate salary. "
            "The data suggests conditions are good for a change if you want one. "
            "Discuss with people you trust — community matters here."
        ),
        "latency_ms": 1850.0,
    },
]


def _make_mock_responses() -> list:
    """Create ModelResponse objects from mock data."""
    results = []
    for m in _MOCK_RESPONSES:
        results.append(ModelResponse(
            model_name=m["model_name"],
            response_text=m["response_text"],
            hex_coord=_classify_hex(m["response_text"]),
            latency_ms=m["latency_ms"],
            token_count=len(m["response_text"].split()),
            is_mock=True,
        ))
    return results


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def collision_demo(question: str = "Should I change jobs?") -> ModelCollisionResult:
    """Demo: collide 3 mock models on a life question. Always works, no Ollama needed."""
    responses = _make_mock_responses()

    collider = ModelCollider()
    insights: list = []
    insights.extend(collider._find_tensions(responses))
    insights.extend(collider._find_synergies(responses))
    insights.extend(collider._find_blind_spots(question, responses))
    synthesis = collider._synthesize(question, responses, insights)
    dominant_hex = collider._dominant_hex(responses)
    diversity = collider._diversity_score(responses)

    return ModelCollisionResult(
        question=question,
        responses=responses,
        insights=insights,
        synthesis=synthesis,
        dominant_hex=dominant_hex,
        diversity_score=diversity,
    )


def _print_result(result: ModelCollisionResult) -> None:
    """Pretty-print a collision result."""
    print(f"\n{'='*60}")
    print(f"QUESTION: {result.question}")
    print(f"{'='*60}\n")

    print("RESPONSES:")
    for r in result.responses:
        tag = " [MOCK]" if r.is_mock else ""
        print(f"  [{r.model_name}{tag}] ({r.latency_ms:.0f}ms, ~{r.token_count} tokens)")
        preview = r.response_text[:120].replace("\n", " ")
        print(f"    \"{preview}...\"")
        hx = r.hex_coord
        print(
            f"    hex: ruhe_druck={hx.ruhe_druck:+.2f} "
            f"sein_tun={hx.sein_tun:+.2f} "
            f"empfangen_schaffen={hx.empfangen_schaffen:+.2f} "
            f"allein_zusammen={hx.allein_zusammen:+.2f}"
        )

    print(f"\nDIVERSITY SCORE: {result.diversity_score:.2f} "
          f"({'rich collision' if result.diversity_score > 0.3 else 'low diversity'})")

    tensions = [i for i in result.insights if i.type == "tension"]
    synergies = [i for i in result.insights if i.type == "synergy"]
    blind_spots = [i for i in result.insights if i.type == "blind_spot"]

    if tensions:
        print(f"\nTENSIONS ({len(tensions)}):")
        for t in tensions:
            print(f"  [{t.confidence:.0%}] {t.description}")

    if synergies:
        print(f"\nSYNERGIES ({len(synergies)}):")
        for s in synergies:
            print(f"  [{s.confidence:.0%}] {s.description}")

    if blind_spots:
        print(f"\nBLIND SPOTS ({len(blind_spots)}):")
        for b in blind_spots:
            print(f"  {b.description}")

    print(f"\nSYNTHESIS:")
    for line in result.synthesis.split("\n\n"):
        print(f"  {line}")

    print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    live_mode = "--live" in sys.argv
    question = " ".join(
        a for a in sys.argv[1:] if not a.startswith("--")
    ) or "Should I change jobs?"

    if live_mode:
        print(f"[LIVE MODE] Querying Ollama models: {ModelCollider.DEFAULT_MODELS}")
        print("(Models must be running locally. Unavailable models are skipped.)\n")
        collider = ModelCollider()
        result = collider.collide(question)
        if not result.responses:
            print("No models responded. Start Ollama and try again.")
            print("Falling back to mock demo...\n")
            result = collision_demo(question)
    else:
        print("[DEMO MODE] Using mock responses. Pass --live to query real Ollama models.\n")
        result = collision_demo(question)

    _print_result(result)
