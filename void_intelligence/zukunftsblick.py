#!/usr/bin/env python3
"""
void_intelligence.zukunftsblick --- Proactive Temporal Assistance.

Gen-2 CHILD OF: SEHENDE HAENDE (seeing hands, proactive) x ZEITAUGE (temporal patterns)

ZUKUNFTSBLICK = Sees what Julian NEEDS before he asks.
Not just NOW but in 3 hours. Proactive temporal assistance.

From SEHENDE HAENDE: anticipation chains, context-aware seeing
From ZEITAUGE: temporal pattern detection, structural analysis through time

ZUKUNFTSBLICK LAW: Future need = temporal rhythm(.) x current context(x) x momentum(->)

CLI:
    python3 -m void_intelligence.zukunftsblick              Predict now
    python3 -m void_intelligence.zukunftsblick --rhythm     Show daily pattern
    python3 -m void_intelligence.zukunftsblick --learn "action"

Zero external dependencies. Pure Python.
State: ~/.void/zukunftsblick/patterns.jsonl
"""
from __future__ import annotations
import json, sys, time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".void" / "zukunftsblick"
PATTERNS_FILE = STATE_DIR / "patterns.jsonl"

# ══════════════════════════════════ Dataclasses ═══════════════════════════════

@dataclass
class FutureNeed:
    """A predicted future need."""
    what: str; when: str; confidence: float; why: str
    def __str__(self) -> str:
        return f"  [{self.confidence:.0%}:>4] {self.what}  ({self.when}) -- {self.why}"

@dataclass
class TemporalContext:
    """Current temporal situation."""
    hour: int; weekday: int; weekday_name: str; phase: str; iso: str
    @staticmethod
    def now() -> TemporalContext:
        n = datetime.now()
        wdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        h = n.hour
        phase = ("veto_zone" if h < 5 else "morning" if h < 10 else "high_energy" if h < 13
                 else "post_lunch" if h < 16 else "second_wind" if h < 20 else "deep_work")
        return TemporalContext(hour=h, weekday=n.weekday(),
                               weekday_name=wdays[n.weekday()], phase=phase, iso=n.isoformat())

@dataclass
class ZukunftsblickResult:
    """Full prediction result."""
    needs: list[FutureNeed]; context: TemporalContext; rhythm_match: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    def __str__(self) -> str:
        lines = [f"ZUKUNFTSBLICK  {self.context.weekday_name} {self.context.hour}:xx  "
                 f"phase={self.context.phase}", f"  Rhythm: {self.rhythm_match}", ""]
        if self.needs:
            lines.append(f"  Predicted needs ({len(self.needs)}):")
            lines.extend(str(n) for n in self.needs)
        else:
            lines.append("  (no predictions -- learn more patterns first)")
        return "\n".join(lines)

# ══════════════════════════════════ State ═════════════════════════════════════

def _load_patterns() -> list[dict]:
    if not PATTERNS_FILE.exists(): return []
    entries = []
    for line in PATTERNS_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try: entries.append(json.loads(line))
            except json.JSONDecodeError: pass
    return entries

def _append_pattern(entry: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PATTERNS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ══════════════════════════════════ ZEITAUGE Phase ════════════════════════════

def _bucket_hour(ts: str) -> int:
    try: return int(ts[11:13])
    except (IndexError, ValueError): return -1

def _bucket_weekday(ts: str) -> int:
    try: return datetime.fromisoformat(ts[:19]).weekday()
    except (ValueError, IndexError): return -1

def _temporal_patterns(history: list[dict]) -> dict:
    by_hour: dict[int, list[str]] = {h: [] for h in range(24)}
    by_weekday: dict[int, list[str]] = {d: [] for d in range(7)}
    for entry in history:
        ts, action = entry.get("timestamp", ""), entry.get("action", "")
        if not action: continue
        h = _bucket_hour(ts)
        if 0 <= h <= 23: by_hour[h].append(action)
        wd = _bucket_weekday(ts)
        if 0 <= wd <= 6: by_weekday[wd].append(action)
    return {"by_hour": by_hour, "by_weekday": by_weekday}

def _top_actions(actions: list[str], n: int = 3) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for a in actions: counts[a] = counts.get(a, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

# ══════════════════════════════════ SEHENDE HAENDE Phase ═════════════════════

def _recent_actions(history: list[dict], minutes: int = 60) -> list[str]:
    now, recent = datetime.now(), []
    for entry in reversed(history):
        try:
            dt = datetime.fromisoformat(entry.get("timestamp", "")[:19])
            if (now - dt).total_seconds() <= minutes * 60: recent.append(entry.get("action", ""))
            else: break
        except (ValueError, IndexError): continue
    return [a for a in recent if a]

# ══════════════════════════════════ COLLISION ═════════════════════════════════

def voraussehen(history: list[dict], current_time: str = "") -> ZukunftsblickResult:
    """ZEITAUGE x SEHENDE HAENDE = prediction of next 3 needs."""
    ctx = TemporalContext.now()
    temporal = _temporal_patterns(history)
    hour_actions = temporal["by_hour"].get(ctx.hour, [])
    hour_top = _top_actions(hour_actions)
    weekday_top = _top_actions(temporal["by_weekday"].get(ctx.weekday, []))
    recent_top = _top_actions(_recent_actions(history, 60), n=2)

    # Rhythm description
    if hour_top: rhythm = f"hour {ctx.hour}: {', '.join(a for a, _ in hour_top)}"
    elif weekday_top: rhythm = f"{ctx.weekday_name}: {', '.join(a for a, _ in weekday_top)}"
    else: rhythm = "not enough data yet"

    needs: list[FutureNeed] = []
    # 1) Hour-based predictions (strongest signal)
    for action, count in hour_top:
        conf = min(count / max(len(hour_actions), 1), 0.95)
        if conf >= 0.1:
            needs.append(FutureNeed(what=action, when=f"now (hour {ctx.hour})",
                confidence=conf, why=f"done {count}x at this hour ({len(hour_actions)} total)"))

    # 2) Upcoming hours: +1h, +2h, +3h
    for offset in (1, 2, 3):
        future_h = (ctx.hour + offset) % 24
        future_actions = temporal["by_hour"].get(future_h, [])
        for action, count in _top_actions(future_actions, n=1):
            conf = min(count / max(len(future_actions), 1) * 0.8, 0.9)
            if conf >= 0.15:
                needs.append(FutureNeed(what=action, when=f"in ~{offset}h (hour {future_h})",
                    confidence=conf, why=f"done {count}x at hour {future_h}"))

    # 3) Momentum: recent pattern differs from rhythm
    if recent_top and hour_top:
        novel = {a for a, _ in recent_top} - {a for a, _ in hour_top}
        for action in novel:
            needs.append(FutureNeed(what=f"(momentum) {action}", when="continuing now",
                confidence=0.6, why="active now but unusual for this hour"))

    needs.sort(key=lambda n: n.confidence, reverse=True)
    return ZukunftsblickResult(needs=needs[:3], context=ctx, rhythm_match=rhythm)

# ══════════════════════════════════ Public API ════════════════════════════════

def anticipate_now(state_file: str = "") -> list[FutureNeed]:
    """Load state, predict NOW."""
    return voraussehen(_load_patterns()).needs

def learn_pattern(action: str, timestamp: str = ""):
    """Record an action for future prediction."""
    _append_pattern({"action": action, "timestamp": timestamp or datetime.now().isoformat()})

def daily_rhythm() -> dict:
    """Show the learned daily rhythm: hour -> typical actions."""
    temporal = _temporal_patterns(_load_patterns())
    rhythm: dict[str, list[str]] = {}
    for h in range(24):
        top = _top_actions(temporal["by_hour"].get(h, []), n=3)
        if top: rhythm[f"{h:02d}:00"] = [f"{a} ({c}x)" for a, c in top]
    return rhythm

# ══════════════════════════════════ CLI ═══════════════════════════════════════

def main() -> int:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print("ZUKUNFTSBLICK -- Proactive Temporal Assistance.\n"
              "  Gen-2: SEHENDE HAENDE x ZEITAUGE\n\n"
              "  void zukunftsblick              Predict now\n"
              "  void zukunftsblick --rhythm     Show daily pattern\n"
              '  void zukunftsblick --learn "action"  Record action'); return 0
    if "--rhythm" in args:
        r = daily_rhythm()
        if not r: print("No patterns learned yet. Use --learn to record actions."); return 0
        print("Daily Rhythm (learned):\n")
        for hour, actions in sorted(r.items()): print(f"  {hour}  {', '.join(actions)}")
        return 0
    if "--learn" in args:
        idx = args.index("--learn")
        if idx + 1 < len(args):
            learn_pattern(args[idx + 1])
            print(f"Learned: {args[idx + 1]} at {datetime.now().strftime('%H:%M')}")
        else: print('Usage: void zukunftsblick --learn "action"')
        return 0
    # Default: predict now
    t0 = time.time()
    history = _load_patterns()
    result = voraussehen(history)
    print(result)
    print(f"\n({time.time() - t0:.3f}s, {len(history)} patterns learned)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
