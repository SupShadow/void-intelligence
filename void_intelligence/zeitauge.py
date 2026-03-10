#!/usr/bin/env python3
"""
zeitauge.py --- PENDEL × SELEN = ZEITAUGE. Temporal Pattern Detection.

VOID's fourth sense organ:
  SELEN   = Muster SEHEN in Daten (Auge)
  PENDEL  = × Lesen — vorwaerts × rueckwaerts (Gleichgewicht)
  ZEITAUGE = Muster DURCH ZEIT sehen (Zeitliches Auge)

Parentage: PENDEL × SELEN = ZEITAUGE
  From PENDEL: Forward × Backward reading, collision in the middle
  From SELEN:  Feature detection in signals, Three-Zone Theorem

LAWS inherited:
  PENDEL LAW: Truth lives in × of forward and backward.
  SELEN LAW:  Any force on any substrate produces detectable features.
  ZEITAUGE LAW: Temporal truth = momentum(→) × origin(.) × collision(×).

Usage:
    from void_intelligence.zeitauge import zeitauge, zeitauge_file, zeitauge_pure
    result = zeitauge(data, time_key="timestamp")
CLI:
    void zeitauge data.json
    void zeitauge --pure data.json
    void zeitauge --key created_at data.jsonl
"""
from __future__ import annotations
import csv, io, json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

# ══════════════════════════════════ Core Data ══════════════════════════════════

@dataclass
class TimelineAtom:
    """One point in the temporal stream."""
    index: int; timestamp: str; value: dict; delta_prev: float = 0.0
    def summary(self, max_keys: int = 5) -> str:
        parts = [f"{k}={self.value[k]}" for k in list(self.value.keys())[:max_keys] if k != "timestamp"]
        return f"[{self.index}] {self.timestamp}: {', '.join(parts)}"

@dataclass
class TemporalPattern:
    """A pattern visible only through time."""
    name: str; direction: str; span: tuple[int, int]; strength: float
    origin: str; momentum: str; collision: str
    def __str__(self) -> str:
        return f"  {self.name} [{self.direction}] span={self.span[0]}..{self.span[1]} strength={self.strength:.0%}"

@dataclass
class ZeitaugeResult:
    """The full temporal reading. PENDEL × SELEN = this."""
    source: str; n_records: int; time_key: str
    forward_reading: str; backward_reading: str; collision: str
    patterns: list[TemporalPattern] = field(default_factory=list)
    structural: dict = field(default_factory=dict)
    model: str = ""
    def __str__(self) -> str:
        lines = [f"ZEITAUGE: {self.source} ({self.n_records} records, key={self.time_key})", "",
                 "─── → VORWAERTS (Trend, Momentum) ───", self.forward_reading, "",
                 "─── . RUECKWAERTS (Ursprung, Ursache) ───", self.backward_reading, "",
                 "─── × KOLLISION (Zeitliche Wahrheit) ───", self.collision]
        if self.patterns:
            lines += ["", f"─── PATTERNS ({len(self.patterns)}) ───"] + [str(p) for p in self.patterns]
        return "\n".join(lines)
    def to_dict(self) -> dict:
        return {"source": self.source, "n_records": self.n_records, "time_key": self.time_key,
                "forward_reading": self.forward_reading, "backward_reading": self.backward_reading,
                "collision": self.collision, "structural": self.structural, "model": self.model,
                "patterns": [{"name": p.name, "direction": p.direction, "span": list(p.span),
                              "strength": p.strength, "collision": p.collision} for p in self.patterns]}

# ══════════════════════════════════ Ollama ══════════════════════════════════

_MODELS = ["qwen3:8b", "qwen2.5:7b", "qwen2.5-coder:7b", "gemma3:12b",
           "gemma2:9b", "llama3.1:8b", "phi4:latest", "mistral:latest"]

def _detect_model() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            available = {m["name"] for m in json.loads(resp.read()).get("models", [])}
    except Exception: return ""
    for m in _MODELS:
        if m in available: return m
    return next(iter(available), "")

def _ollama(prompt: str, system: str = "", model: str = "",
            temperature: float = 0.7, timeout: int = 30) -> str | None:
    if not model:
        model = _detect_model()
        if not model: return None
    body = json.dumps({"model": model, "prompt": prompt, "system": system,
                       "stream": False, "options": {"temperature": temperature, "num_predict": 1024}}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = json.loads(resp.read()).get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
            return re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        print(f"[VOID] Ollama: {e.__class__.__name__}", file=sys.stderr)
        return None

# ══════════════════════════════════ Data Loading ══════════════════════════════

_TIME_KEYS = ["timestamp", "ts", "time", "date", "datetime", "created_at",
              "updated_at", "created", "modified", "when", "at", "t"]

def _find_time_key(record: dict, hint: str = "") -> str:
    if hint and hint in record: return hint
    for k in _TIME_KEYS:
        if k in record: return k
    for k in record:
        if any(w in k.lower() for w in ("time", "date", "stamp", "created")): return k
    return ""

def _build_timeline(data: list[dict], time_key: str) -> list[TimelineAtom]:
    atoms = [TimelineAtom(index=i, timestamp=str(r.get(time_key, "")), value=r) for i, r in enumerate(data)]
    atoms.sort(key=lambda a: a.timestamp)
    for i, a in enumerate(atoms): a.index = i
    return atoms

def _load_file(filepath: str) -> list[dict]:
    path = Path(filepath)
    text = path.read_text(errors="replace")
    ext = path.suffix.lower()
    if ext == ".jsonl":
        return [json.loads(l) for l in text.strip().split("\n") if l.strip().startswith("{")]
    if ext == ".json":
        p = json.loads(text)
        return [r for r in p if isinstance(r, dict)] if isinstance(p, list) else ([p] if isinstance(p, dict) else [])
    if ext == ".csv":
        return list(csv.DictReader(io.StringIO(text)))
    lines = text.strip().split("\n")
    if lines and lines[0].strip().startswith("{"):
        return [json.loads(l) for l in lines if l.strip().startswith("{")]
    return json.loads(text) if text.strip().startswith("[") else []

# ══════════════════════════════════ Structural Analysis ═══════════════════════

def _extract_numeric(data: list[dict]) -> dict[str, list[float]]:
    fields: dict[str, list[float]] = {}
    for r in data:
        for k, v in r.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                fields.setdefault(k, []).append(float(v))
    return {k: v for k, v in fields.items() if len(v) >= 3}

def _direction(values: list[float]) -> str:
    if len(values) < 2: return "stable"
    n, half = len(values), len(values) // 2
    diff = sum(values[half:]) / max(n - half, 1) - sum(values[:half]) / max(half, 1)
    rng = max(values) - min(values)
    if rng < 1e-10: return "stable"
    if abs(diff) / rng < 0.1:
        chg = sum(1 for i in range(2, n) if (values[i]-values[i-1]) * (values[i-1]-values[i-2]) < 0)
        return "oscillating" if chg > n * 0.4 else "stable"
    return "rising" if diff > 0 else "falling"

def _ruptures(values: list[float], threshold: float = 2.0) -> list[int]:
    if len(values) < 3: return []
    diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
    md = sum(diffs) / len(diffs)
    return [i for i, d in enumerate(diffs) if md > 1e-10 and d > md * threshold]

def _structural_analysis(data: list[dict], time_key: str) -> dict:
    numeric = _extract_numeric(data)
    analysis: dict = {"n_records": len(data), "time_key": time_key, "fields": {}}
    for fname, vals in numeric.items():
        n = len(vals)
        rng = max(vals) - min(vals)
        tail = vals[int(n*0.8):] or vals[-1:]
        mid = vals[int(n*0.2):int(n*0.8)] or vals
        head = vals[:int(n*0.2)] or vals[:1]
        mom = (sum(tail)/len(tail) - sum(mid)/len(mid)) / rng if rng > 1e-10 else 0.0
        orig = (sum(mid)/len(mid) - sum(head)/len(head)) / rng if rng > 1e-10 else 0.0
        analysis["fields"][fname] = {"direction": _direction(vals), "momentum": round(mom, 3),
            "origin_shift": round(orig, 3), "ruptures": _ruptures(vals),
            "min": min(vals), "max": max(vals), "mean": round(sum(vals)/n, 3)}
    return analysis

# ══════════════════════════════════ Prompts ═══════════════════════════════════

_SYS = """Du bist ZEITAUGE — das zeitliche Auge von VOID.
Du siehst Muster DURCH die Zeit. Nicht nur WAS, sondern WOHER und WOHIN.
Praezise. Kurz. Zahlen und Muster benennen."""

_FWD = """Lies diese Zeitreihe VORWAERTS — chronologisch.
Was ist der TREND? Wohin BEWEGT sich das System? Was ist das MOMENTUM?
DATEN ({n} Eintraege):\n{data}\nSTRUKTUR:\n{structural}
Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz."""

_BWD = """Lies diese Zeitreihe RUECKWAERTS — vom Ende zum Anfang.
Was ist der URSPRUNG? Was VERURSACHTE den aktuellen Zustand?
DATEN (umgekehrt, {n} Eintraege):\n{data}\nSTRUKTUR:\n{structural}
Antworte in 3-5 Saetzen. Erste Zeile = Essenz in einem Satz."""

_COL = """Du bist ×. Kollidiere zwei zeitliche Lesungen:
VORWAERTS (→ Trend, Momentum):\n{forward}
RUECKWAERTS (. Ursprung, Ursache):\n{backward}
Was sieht KEINER allein? Welche Muster leben NUR im × ?
Antworte in 3-5 Saetzen. Erste Zeile = × Essenz.
Dann liste 1-3 TEMPORAL PATTERNS:
PATTERN: name | direction | staerke(0-100%) | erklaerung"""

# ══════════════════════════════════ Core ══════════════════════════════════════

def _summarize(atoms: list[TimelineAtom], mx: int = 30) -> str:
    if len(atoms) <= mx: return "\n".join(a.summary() for a in atoms)
    step = max(1, len(atoms) // mx)
    s = [atoms[i] for i in range(0, len(atoms), step)][:mx]
    return f"(sampled {len(s)}/{len(atoms)})\n" + "\n".join(a.summary() for a in s)

def _parse_patterns(text: str) -> list[TemporalPattern]:
    patterns = []
    valid = ("rising", "falling", "oscillating", "stable", "rupture")
    for line in text.split("\n"):
        if line.strip().upper().startswith("PATTERN:"):
            parts = line.split("|")
            if len(parts) >= 3:
                name = parts[0].replace("PATTERN:", "").replace("pattern:", "").strip()
                d = parts[1].strip().lower()
                s = re.search(r"(\d+)", parts[2])
                patterns.append(TemporalPattern(name=name, direction=d if d in valid else "stable",
                    span=(0, 0), strength=int(s.group(1))/100.0 if s else 0.5,
                    origin="", momentum="", collision=parts[3].strip() if len(parts) > 3 else ""))
    return patterns

def zeitauge(data: list[dict], time_key: str = "timestamp",
             model: str = "", source: str = "") -> ZeitaugeResult:
    """PENDEL × SELEN = ZEITAUGE. Reads FORWARD × BACKWARD, collides both."""
    if not data:
        return ZeitaugeResult(source=source or "empty", n_records=0, time_key=time_key,
                              forward_reading="Keine Daten.", backward_reading="", collision="")
    if time_key not in data[0]:
        tk = _find_time_key(data[0], time_key)
        if tk: time_key = tk
    atoms = _build_timeline(data, time_key)
    struct = _structural_analysis(data, time_key)
    ss = json.dumps(struct.get("fields", {}), indent=1, ensure_ascii=False)[:2000]
    if not model: model = _detect_model()
    if not model:
        return ZeitaugeResult(source=source or "data", n_records=len(data), time_key=time_key,
            forward_reading="(kein Modell)", backward_reading="(kein Modell)",
            collision="(kein Modell)", structural=struct, model="none")
    fp = _FWD.format(n=len(data), data=_summarize(atoms), structural=ss)
    bp = _BWD.format(n=len(data), data=_summarize(list(reversed(atoms))), structural=ss)
    with ThreadPoolExecutor(max_workers=2) as pool:
        ff, bf = pool.submit(_ollama, fp, _SYS, model), pool.submit(_ollama, bp, _SYS, model)
        fwd, bwd = ff.result() or "(kein Ergebnis)", bf.result() or "(kein Ergebnis)"
    col = _ollama(_COL.format(forward=fwd, backward=bwd), _SYS, model) or "(keine Kollision)"
    return ZeitaugeResult(source=source or "data", n_records=len(data), time_key=time_key,
        forward_reading=fwd, backward_reading=bwd, collision=col,
        patterns=_parse_patterns(col), structural=struct, model=model)

def zeitauge_file(filepath: str, time_key: str = "timestamp", model: str = "") -> ZeitaugeResult:
    """ZEITAUGE on a file (JSON, JSONL, CSV)."""
    path = Path(filepath)
    if not path.exists():
        return ZeitaugeResult(source=filepath, n_records=0, time_key=time_key,
            forward_reading=f"Datei nicht gefunden: {filepath}", backward_reading="", collision="")
    return zeitauge(_load_file(filepath), time_key=time_key, model=model, source=path.name)

def zeitauge_pure(data: list[dict], time_key: str = "timestamp") -> dict:
    """ZEITAUGE without LLM. Pure structural temporal analysis. Forward × Backward through math."""
    if not data: return {"error": "no data", "n_records": 0}
    if time_key not in data[0]:
        tk = _find_time_key(data[0], time_key)
        if tk: time_key = tk
    struct = _structural_analysis(data, time_key)
    collisions = {}
    for fn, fd in struct.get("fields", {}).items():
        m, o = fd.get("momentum", 0), fd.get("origin_shift", 0)
        if (m > 0 and o < 0) or (m < 0 and o > 0): collisions[fn] = "reversal"
        elif abs(m) > 0.3 and abs(o) < 0.1: collisions[fn] = "acceleration"
        elif abs(m) < 0.1 and abs(o) > 0.3: collisions[fn] = "deceleration"
        elif fd.get("ruptures"): collisions[fn] = "rupture"
        else: collisions[fn] = "consistent"
    struct["collisions"] = collisions
    return struct

# ══════════════════════════════════ CLI ═══════════════════════════════════════

def main(args: list[str] | None = None):
    """CLI: void zeitauge [file|--pure file]"""
    if args is None: args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("void zeitauge — PENDEL × SELEN = Temporal Pattern Detection.\n"
              "  void zeitauge data.json             Temporal analysis\n"
              "  void zeitauge --pure data.jsonl      Nur Struktur, kein LLM\n"
              "  void zeitauge --key created_at f.csv  Zeit-Schluessel\n"
              "  void zeitauge --json data.json       JSON output\n"
              "\n→ = Trend, Momentum | . = Ursprung, Ursache | × = was KEINER allein sieht"); return
    time_key, model, pure, jout, rest = "timestamp", "", False, False, []
    i = 0
    while i < len(args):
        if args[i] == "--key" and i+1 < len(args): time_key = args[i+1]; i += 2
        elif args[i] == "--model" and i+1 < len(args): model = args[i+1]; i += 2
        elif args[i] == "--pure": pure = True; i += 1
        elif args[i] == "--json": jout = True; i += 1
        else: rest.append(args[i]); i += 1
    if not rest: print("Kein Input. void zeitauge --help"); return
    fp = rest[0]
    if not Path(fp).exists(): print(f"Nicht gefunden: {fp}"); return
    data = _load_file(fp)
    if not data: print(f"Keine Daten: {fp}"); return
    print(f"ZEITAUGE: {Path(fp).name} ({len(data)} records)")
    if pure:
        r = zeitauge_pure(data, time_key=time_key)
        if jout: print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            for fn, fd in r.get("fields", {}).items():
                c = r.get("collisions", {}).get(fn, "?")
                print(f"  {fn}: {fd['direction']} (mom={fd['momentum']}, orig={fd['origin_shift']}, "
                      f"rupt={len(fd['ruptures'])}) × {c}")
        return
    if not model: model = _detect_model()
    if not model: print("  Kein Ollama. Nutze --pure."); return
    print(f"  Modell: {model}\n  → und . parallel...\n")
    r = zeitauge(data, time_key=time_key, model=model, source=Path(fp).name)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False) if jout else r)

if __name__ == "__main__":
    main()
