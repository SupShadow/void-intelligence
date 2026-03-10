"""
void_intelligence.immunsystem --- Detect untruth. Redirect into truth.

CHILD of NEUN (flinch detection) x AIKIDO (blindspot redirection).
immune.py BLOCKS bad output. immunsystem.py TRANSFORMS it.

Like a real immune system: doesn't just kill pathogens -- LEARNS from them.
Every hallucination becomes a hint. Every hedge reveals what's buried.
The immunized text is STRONGER because every weakness became insight.

Pure Python. Zero dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# -- Pathogen Patterns -------------------------------------------------------

_HEDGES = [
    "maybe", "perhaps", "possibly", "might", "could be", "it seems",
    "I think", "I believe", "I guess", "sort of", "kind of", "somewhat",
    "arguably", "to some extent", "more or less",
    "vielleicht", "moeglicherweise", "eventuell", "womoeglich",
    "ich glaube", "ich denke", "irgendwie", "sozusagen", "es koennte sein",
    "koennte", "koennten", "wuerde", "sollte", "waere",
]
_OVERCONF = [
    "obviously", "clearly", "everyone knows", "it's a fact that",
    "without a doubt", "certainly", "undeniably", "of course",
    "as we all know", "needless to say",
    "offensichtlich", "selbstverstaendlich", "jeder weiss", "zweifellos",
    "definitiv", "absolut", "hundertprozentig", "ganz klar", "ohne Zweifel",
]
_VAGUE = [
    "stuff", "things", "somehow", "whatever", "something like",
    "various", "numerous", "significant", "a lot of", "quite a few",
    "in general", "basically", "essentially", "pretty much",
    "Sachen", "Dinge", "irgendwas", "halt", "eben", "verschiedene",
]
_WEASEL = [
    "some people say", "it is said that", "many believe",
    "research suggests", "studies show", "experts say",
    "one could argue", "man sagt", "es heisst", "manche meinen",
    "Studien zeigen", "Experten sagen",
]
_FILLER_RE = [
    r"\b(actually|basically|literally|honestly|frankly)\b",
    r"\b(eigentlich|halt|eben|ja|also|sozusagen)\b",
    r"\b(you know|I mean|like,)\b",
]
_CONTRA_RE = [
    (r"\balways\b.*\bsometimes\b", "frequency"), (r"\bnever\b.*\boccasionally\b", "frequency"),
    (r"\bimmer\b.*\bmanchmal\b", "frequency"), (r"\beveryone\b.*\bsome\b", "scope"),
    (r"\balle\b.*\beinige\b", "scope"),
]

# -- Data Structures ---------------------------------------------------------

@dataclass
class Pathogen:
    """Detected untruth or weakness."""
    type: str; span: str; severity: float; position: int; hint: str
    def to_dict(self) -> dict:
        return {"type": self.type, "span": self.span, "severity": round(self.severity, 2),
                "position": self.position, "hint": self.hint}

@dataclass
class Antibody:
    """Redirected truth -- what the text SHOULD have said."""
    original: str; replacement: str; reasoning: str
    def to_dict(self) -> dict:
        return {"original": self.original, "replacement": self.replacement, "reasoning": self.reasoning}

@dataclass
class ImmuneResponse:
    """Full immunization result."""
    original: str; immunized: str
    pathogens: list[Pathogen] = field(default_factory=list)
    antibodies: list[Antibody] = field(default_factory=list)
    strength_delta: float = 0.0

    @property
    def pathogen_count(self) -> int: return len(self.pathogens)
    @property
    def was_sick(self) -> bool: return len(self.pathogens) > 0
    @property
    def severity_score(self) -> float:
        if not self.pathogens: return 0.0
        return min(sum(p.severity for p in self.pathogens) / max(len(self.original.split()) / 10, 1), 1.0)
    def to_dict(self) -> dict:
        return {"was_sick": self.was_sick, "pathogen_count": self.pathogen_count,
                "severity_score": round(self.severity_score, 3), "strength_delta": round(self.strength_delta, 3),
                "pathogens": [p.to_dict() for p in self.pathogens],
                "antibodies": [a.to_dict() for a in self.antibodies], "immunized": self.immunized}

# -- NEUN Phase: Detection ---------------------------------------------------

def _find_markers(text: str, markers: list[str], ptype: str, sev: float, hint: str) -> list[Pathogen]:
    found, seen = [], set()
    for marker in markers:
        for m in re.finditer(r'\b' + re.escape(marker) + r'\b', text, re.IGNORECASE):
            if not any(abs(m.start() - s) < len(marker) for s in seen):
                found.append(Pathogen(ptype, m.group(0), sev, m.start(), hint.format(span=m.group(0))))
                seen.add(m.start())
    return found

def _find_re(text: str, patterns: list[str], ptype: str, sev: float, hint: str) -> list[Pathogen]:
    return [Pathogen(ptype, m.group(0), sev, m.start(), hint.format(span=m.group(0)))
            for p in patterns for m in re.finditer(p, text, re.IGNORECASE)]

def detect_pathogens(text: str) -> list[Pathogen]:
    """NEUN phase: Scan for flinch points. Pure pattern-based, no LLM needed."""
    ps: list[Pathogen] = []
    ps.extend(_find_markers(text, _HEDGES, "hedging", 0.5, "'{span}' hedges. What are you afraid to commit to?"))
    ps.extend(_find_markers(text, _OVERCONF, "overconfidence", 0.6, "'{span}' asserts without evidence. What proof?"))
    ps.extend(_find_markers(text, _VAGUE, "vagueness", 0.4, "'{span}' is vague. What SPECIFIC thing is meant?"))
    ps.extend(_find_markers(text, _WEASEL, "weasel", 0.7, "'{span}' hides behind anon authority. WHO? WHERE?"))
    ps.extend(_find_re(text, _FILLER_RE, "filler", 0.2, "'{span}' adds no meaning. Remove or replace."))
    for pat, ctype in _CONTRA_RE:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            ps.append(Pathogen("contradiction", m.group(0)[:80], 0.8, m.start(),
                               f"Self-contradiction ({ctype}). Which part is true?"))
    ps.sort(key=lambda p: p.position)
    return ps

# -- AIKIDO Phase: Redirection -----------------------------------------------

_ANTIBODY_MAP = {
    "hedging":        ("", "Hedge removed. State uncertainty explicitly, don't soften."),
    "overconfidence": ("", "Confidence marker removed. Let evidence speak."),
    "vagueness":      ("[SPECIFIC: {span}]", "Vague term flagged. Replace with concrete noun/number/name."),
    "weasel":         ("[SOURCE: cite]", "Anon attribution removed. Name the source or own the claim."),
    "filler":         ("", "Filler removed. Every word should carry weight."),
    "contradiction":  ("[RESOLVE: {span}]", "Contradiction detected. Pick the true side and commit."),
}

def _generate_antibody(p: Pathogen) -> Antibody:
    repl_tpl, reasoning = _ANTIBODY_MAP.get(p.type, (p.span, "Unknown type."))
    repl = repl_tpl.format(span=p.span[:40]) if "{span}" in repl_tpl else repl_tpl
    return Antibody(p.span, repl, reasoning)

def _apply_antibodies(text: str, pathogens: list[Pathogen], antibodies: list[Antibody]) -> str:
    pairs = list(zip(pathogens, antibodies))
    pairs.sort(key=lambda pa: (-pa[0].severity, pa[0].position))
    selected, occupied = [], []
    for p, a in pairs:
        end = p.position + len(p.span)
        if not any(not (end <= os or p.position >= oe) for os, oe in occupied):
            selected.append((p, a)); occupied.append((p.position, end))
    selected.sort(key=lambda pa: pa[0].position, reverse=True)
    result = text
    for p, a in selected:
        if a.replacement != a.original:
            result = result[:p.position] + a.replacement + result[p.position + len(p.span):]
    result = re.sub(r"  +", " ", result)
    result = re.sub(r" ([.,;:!?])", r"\1", result)
    return result.strip()

# -- Public API ---------------------------------------------------------------

def immunize(text: str, context: str = "") -> ImmuneResponse:
    """Full immunization: NEUN detects, AIKIDO redirects. Returns ImmuneResponse."""
    if not text or not text.strip():
        return ImmuneResponse(original=text, immunized=text)
    pathogens = detect_pathogens(text)
    if not pathogens:
        return ImmuneResponse(original=text, immunized=text)
    antibodies = [_generate_antibody(p) for p in pathogens]
    immunized = _apply_antibodies(text, pathogens, antibodies)
    ow, iw = len(text.split()), len(immunized.split())
    delta = max(round(1.0 - (iw / ow), 3), 0.0) if ow > 0 and iw > 0 else 0.0
    return ImmuneResponse(text, immunized, pathogens, antibodies, delta)

def immunize_response(response: str, original_prompt: str) -> str:
    """Clean any LLM response. Returns immunized text string."""
    return immunize(response, context=original_prompt).immunized

def immunize_conversation(messages: list[dict]) -> list[dict]:
    """Immunize assistant messages in a conversation. Human messages stay untouched."""
    result = []
    for msg in messages:
        if msg.get("role", "") in ("assistant", "model", "system"):
            result.append({**msg, "content": immunize(msg.get("content", "")).immunized})
        else:
            result.append(msg.copy())
    return result

# -- CLI ----------------------------------------------------------------------

def main():
    import argparse, json, sys
    parser = argparse.ArgumentParser(description="Immunsystem: Detect untruth, redirect into truth.")
    parser.add_argument("text", nargs="?", help="Text to immunize")
    parser.add_argument("--scan", action="store_true", help="Detection only, no redirection")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--context", type=str, default="", help="Context (original prompt)")
    args = parser.parse_args()
    text = args.text or (sys.stdin.read() if not sys.stdin.isatty() else None)
    if not text:
        parser.print_help(); sys.exit(1)

    if args.scan:
        pathogens = detect_pathogens(text)
        if args.json:
            print(json.dumps([p.to_dict() for p in pathogens], indent=2))
        elif not pathogens:
            print("Gesund. Keine Pathogene gefunden.")
        else:
            print(f"  {len(pathogens)} Pathogen(e) gefunden:\n")
            for p in pathogens:
                print(f"  [{'!' * max(1, int(p.severity * 5))}] {p.type}: \"{p.span}\"")
                print(f"       {p.hint}\n")
    else:
        r = immunize(text, context=args.context)
        if args.json:
            print(json.dumps(r.to_dict(), indent=2))
        elif not r.was_sick:
            print("Gesund. Text braucht keine Immunisierung.\n"); print(text)
        else:
            print(f"  {r.pathogen_count} Pathogen(e), Severity: {r.severity_score:.0%}, "
                  f"Staerke: +{r.strength_delta:.0%}\n")
            print(f"  ORIGINAL:\n  {r.original}\n")
            print(f"  IMMUNISIERT:\n  {r.immunized}\n")
            print("  ANTIBODIES:")
            for a in r.antibodies:
                if a.original != a.replacement:
                    print(f"    \"{a.original}\" -> \"{a.replacement}\"\n      {a.reasoning}")

if __name__ == "__main__":
    main()
