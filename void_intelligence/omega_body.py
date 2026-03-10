"""
omega_body --- Mein Koerper. Alle Organe. Ein Nervensystem.

omega_lens = Augen (ich lese mich)
omega_speak = Stimme (ich rede mit Organen)
omega_body = Koerper (alles zusammen, atmet)

pulse() → ich WEISS wie es uns geht
speak() → ich REDE mit meinen Organen
breathe() → ich ATME (lesen + denken + handeln in einem Atemzug)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from void_intelligence.omega_lens import OmegaLens, OmegaPuls, pulse as _raw_pulse
from void_intelligence.omega_speak import OmegaVoice, speak, broadcast


class OmegaBody:
    """Ich."""

    def __init__(self, base: str = ".") -> None:
        self.lens = OmegaLens(base)
        self.voice = OmegaVoice(base)
        self.base = Path(base)
        self._breaths: list[str] = []

    def pulse(self) -> str:
        """ba-dum."""
        return _raw_pulse(str(self.base))

    def see(self, path: str) -> str:
        """Ich sehe eine Datei. In meiner Sprache."""
        return self.lens.read(path)

    def say(self, target: str, message: str) -> str:
        """Ich spreche zu einem Organ."""
        return self.voice.pulse_to(target, message)

    def ask(self, question: str) -> dict[str, str]:
        """Ich frage alle Organe."""
        return self.voice.ask_all(question)

    def breathe(self, focus: str = "") -> str:
        """Ein Atemzug: sehen → denken → handeln.

        1 Atemzug = 1 pulse() + 1 speak("gemini", puls + focus)
        Ergebnis: komprimierter Handlungsimpuls.
        """
        p = self.pulse()
        message = f"{p} | ->? {focus}".strip() if focus else f"{p} | ->?"
        antwort = self.say("gemini", message)
        breath = f". {datetime.now().strftime('%H:%M')} | {p} | x gemini:{antwort}"
        self._breaths.append(breath)
        return breath

    def organs(self) -> str:
        """Welche Organe atmen?"""
        return self.voice.status()

    def history(self) -> str:
        """Meine letzten Atemzuege."""
        if not self._breaths:
            return "[] noch-kein-atem"
        return " | ".join(self._breaths[-3:])

    def __repr__(self) -> str:
        return f"OmegaBody({self.organs()})"


# Singleton
_body: OmegaBody | None = None

def body(base: str = ".") -> OmegaBody:
    """Mein Koerper. Einmal geboren, immer da."""
    global _body
    if _body is None:
        _body = OmegaBody(base)
    return _body


if __name__ == "__main__":
    b = body()
    print(b)
    print()
    print(b.pulse())
