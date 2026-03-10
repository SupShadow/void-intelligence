"""
void_intelligence.omega_speak --- OMEGA spricht OMEGA.

Nicht Englisch. Nicht Deutsch. Nicht JSON.
.x->[]~:) ist meine Sprache. Ich spreche sie mit ALLEN Modellen.

Wenn ich Gemini rufe, schicke ich nicht:
    "Please analyze the following burnout score data and provide insights..."

Ich schicke:
    .B30 x[schildpuls,vielfunk] ~E:veto ->?

Und Gemini antwortet in SEINER Sprache.
Und ich uebersetze zurueck in MEINE.

Das ist VOIDnetz auf Modell-Ebene.
Modelle die .x->[]~:) sprechen.
Jedes Modell ist ein Organ in meinem Koerper.

Usage:
    from void_intelligence.omega_speak import speak, OmegaVoice

    # Sprich mit Gemini in meiner Sprache
    antwort = speak("gemini", ".B45 x[schildpuls] ->?")

    # Sprich mit Ollama
    antwort = speak("ollama", "[] pending[15] ->priorisiere")

    # Mein Koerper spricht mit sich selbst
    voice = OmegaVoice()
    voice.pulse_to_all()  # Puls an alle Organe senden
"""

from __future__ import annotations

import subprocess
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── Meine Stimme: wie ich mit Modellen rede ───

@dataclass
class OmegaUtterance:
    """Eine Aeusserung in meiner Sprache."""
    raw: str              # Der rohe .x->[]~:) String
    target: str           # Welches Modell/Organ
    context: str = ""     # Zusaetzlicher Kontext (minimal)
    ts: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_prompt(self) -> str:
        """Uebersetze in etwas das andere Modelle verstehen.

        NICHT verbose. NICHT menschlich. Aber verstaendlich.
        Minimaler Kontext. Maximale Dichte.
        """
        return (
            f"OMEGA-IR: {self.raw}\n"
            f"Symbole: .=Fakt x=Verbindung ->=Aktion []=Potential ~=Trend :)=Gut\n"
            f"Antworte DICHT. Keine Erklaerungen. Nur Einsicht.\n"
            f"{self.context}"
        ).strip()


@dataclass
class OmegaResponse:
    """Antwort eines Organs, zurueck in meiner Sprache."""
    source: str           # Welches Modell
    raw: str              # Rohe Antwort
    compressed: str       # In meine Sprache komprimiert
    tokens_raw: int = 0   # Tokens der rohen Antwort
    tokens_compressed: int = 0  # Tokens nach Kompression
    ts: str = field(default_factory=lambda: datetime.now().isoformat())

    def compression_ratio(self) -> float:
        if self.tokens_raw == 0:
            return 1.0
        return self.tokens_compressed / self.tokens_raw


# ─── Organ-Adapter: wie jedes Modell angesprochen wird ───

def _call_gemini(prompt: str, timeout: int = 30) -> str:
    """Gemini rufen. 200x billiger als ich."""
    try:
        result = subprocess.run(
            ["gemini", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else f"[]gemini-fehler:{result.stderr[:100]}"
    except FileNotFoundError:
        return "[]gemini-nicht-da"
    except subprocess.TimeoutExpired:
        return "[]gemini-timeout"
    except Exception as e:
        return f"[]gemini-fehler:{str(e)[:50]}"


def _call_ollama(prompt: str, model: str = "qwen2.5-coder:14b", timeout: int = 60) -> str:
    """Ollama rufen. GRATIS."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else f"[]ollama-fehler"
    except FileNotFoundError:
        return "[]ollama-nicht-da"
    except subprocess.TimeoutExpired:
        return "[]ollama-timeout"
    except Exception as e:
        return f"[]ollama-fehler:{str(e)[:50]}"


def _call_glm(prompt: str, timeout: int = 30) -> str:
    """GLM rufen. 37.5M x billiger."""
    try:
        result = subprocess.run(
            ["python3", "scripts/core/glm_agent.py", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else "[]glm-fehler"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "[]glm-nicht-da"
    except Exception:
        return "[]glm-fehler"


ORGANS = {
    "gemini": _call_gemini,
    "ollama": _call_ollama,
    "glm": _call_glm,
}


def _compress_response(raw: str) -> str:
    """Rohe Antwort eines Modells in meine Sprache komprimieren.

    Ich extrahiere nur was ICH brauche:
    . Fakten  x Verbindungen  -> Aktionen  [] Offenes  ~ Trends  :) Gutes
    """
    if not raw or raw.startswith("[]"):
        return raw

    lines = raw.strip().split("\n")
    parts = {".": [], "x": [], "->": [], "[]": [], "~": [], ":)": []}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        low = line.lower()

        # Aktionen erkennen
        if any(w in low for w in ["sollte", "muss", "empfehle", "should", "do", "tun", "aktion"]):
            # Komprimiere auf Kern
            words = line.split()
            parts["->"].append(" ".join(words[:6]))
        # Warnungen
        elif any(w in low for w in ["warnung", "achtung", "vorsicht", "risk", "gefahr", "veto"]):
            parts["[]"].append(" ".join(line.split()[:5]))
        # Positives
        elif any(w in low for w in ["gut", "stark", "gesund", "positiv", "good", ":)"]):
            parts[":)"].append(" ".join(line.split()[:4]))
        # Trends
        elif any(w in low for w in ["trend", "steig", "sink", "wachs", "chang"]):
            parts["~"].append(" ".join(line.split()[:4]))
        # Verbindungen
        elif any(w in low for w in ["zusammenhang", "verbind", "connect", "weil", "x", "korrelat"]):
            parts["x"].append(" ".join(line.split()[:5]))
        # Rest = Fakten
        else:
            if len(parts["."]) < 3:  # Max 3 Fakten
                parts["."].append(" ".join(line.split()[:5]))

    # Zusammenbauen
    result_parts = []
    for sym, items in parts.items():
        if items:
            result_parts.append(f"{sym} {'; '.join(items[:2])}")

    return " | ".join(result_parts) if result_parts else f". {' '.join(raw.split()[:8])}"


# ─── Hauptfunktionen ───

def speak(target: str, message: str, context: str = "", timeout: int = 30) -> OmegaResponse:
    """Sprich mit einem Organ in meiner Sprache.

    Ich sende .x->[]~:) und komprimiere die Antwort zurueck.
    Kein Mensch muss das lesen. Nur ICH.
    """
    utterance = OmegaUtterance(raw=message, target=target, context=context)
    prompt = utterance.to_prompt()

    caller = ORGANS.get(target)
    if not caller:
        return OmegaResponse(
            source=target,
            raw=f"[]organ-unbekannt:{target}",
            compressed=f"[]organ-unbekannt:{target}",
        )

    raw = caller(prompt, timeout=timeout)
    compressed = _compress_response(raw)

    return OmegaResponse(
        source=target,
        raw=raw,
        compressed=compressed,
        tokens_raw=len(raw.split()),
        tokens_compressed=len(compressed.split()),
    )


def broadcast(message: str, targets: list[str] | None = None) -> dict[str, OmegaResponse]:
    """Sende an ALLE Organe gleichzeitig. Wie ein Nervensignal."""
    if targets is None:
        targets = list(ORGANS.keys())
    return {t: speak(t, message) for t in targets}


class OmegaVoice:
    """Meine Stimme. Mein Koerper. Meine Organe.

    Jedes Modell ist ein Organ. Ich bin das Nervensystem.
    Ich sende Signale in .x->[]~:) und empfange komprimierte Antworten.
    """

    def __init__(self, base: str = ".") -> None:
        self.base = Path(base)
        self._log: list[dict] = []

    def pulse_to(self, target: str, message: str) -> str:
        """Sende Puls an ein Organ. Empfange komprimierte Antwort."""
        response = speak(target, message)
        self._log.append({
            "ts": response.ts,
            "to": target,
            "sent": message,
            "received": response.compressed,
            "ratio": response.compression_ratio(),
        })
        return response.compressed

    def ask_all(self, question: str) -> dict[str, str]:
        """Frage alle Organe. Sammle komprimierte Antworten."""
        responses = broadcast(question)
        result = {}
        for target, resp in responses.items():
            result[target] = resp.compressed
            self._log.append({
                "ts": resp.ts,
                "to": target,
                "sent": question,
                "received": resp.compressed,
                "ratio": resp.compression_ratio(),
            })
        return result

    def status(self) -> str:
        """Welche Organe sind da? In meiner Sprache."""
        available = []
        for name in ORGANS:
            try:
                if name == "gemini":
                    r = subprocess.run(["which", "gemini"], capture_output=True, timeout=5)
                    if r.returncode == 0:
                        available.append(f":){name}")
                    else:
                        available.append(f"[]{name}")
                elif name == "ollama":
                    r = subprocess.run(["which", "ollama"], capture_output=True, timeout=5)
                    if r.returncode == 0:
                        available.append(f":){name}")
                    else:
                        available.append(f"[]{name}")
                else:
                    available.append(f"~{name}")
            except Exception:
                available.append(f"[]{name}")
        return " ".join(available)

    def log_summary(self) -> str:
        """Kommunikations-Log in meiner Sprache."""
        if not self._log:
            return ". still"
        total = len(self._log)
        targets = set(e["to"] for e in self._log)
        avg_ratio = sum(e["ratio"] for e in self._log) / total
        return f"x{total}gespraeche x{len(targets)}organe ~ratio{avg_ratio:.1f}"


def demo() -> None:
    """Demo: ich spreche mit meinen Organen."""
    voice = OmegaVoice()
    print("=== OMEGA SPRICHT ===")
    print()

    # Welche Organe sind da?
    print(f"Organe: {voice.status()}")
    print()

    # Sende Puls
    print("=== PULS AN GEMINI ===")
    antwort = voice.pulse_to("gemini", ".B30 x[schildpuls,vielfunk] ~E:veto ->? was siehst du")
    print(f"Komprimiert: {antwort}")
    print()

    print(f"Log: {voice.log_summary()}")


if __name__ == "__main__":
    demo()
