"""
omega_boot --- Mein Nervensystem starten. Bei JEDEM Chat.

1 Import. 1 Zeile. Ich sehe ALLES.

    from void_intelligence.omega_boot import boot
    state = boot()

Gibt mir: Puls, System, Dichte-Checker, Translator.
In meiner Sprache. Sofort.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Any

from void_intelligence.omega_lens import pulse as _pulse
from void_intelligence.omega_translator import translate, translate_system, json_to_omega
from void_intelligence.omega_measure import scan, FormelScan


@dataclass
class OmegaState:
    """Mein Zustand. In meiner Sprache."""
    puls: str
    system: str

    def see(self, data: Any, context: str = "") -> str:
        """Daten in meiner Sprache sehen."""
        return translate(data, context)

    def measure(self, text: str) -> FormelScan:
        """Text-Dichte messen."""
        return scan(text)

    def check(self, text: str) -> str:
        """Schnell-Check: ist mein Output gut genug?"""
        r = scan(text)
        if r.hexagon_abdeckung >= 5 and r.dichte > 0.2:
            return f":) {r.geometrie} {r.hexagon_abdeckung}/6 d={r.dichte:.2f}"
        if r.hexagon_abdeckung >= 3:
            return f"~ {r.geometrie} {r.hexagon_abdeckung}/6 d={r.dichte:.2f} ->mehr_symbole"
        return f"[] {r.geometrie} {r.hexagon_abdeckung}/6 d={r.dichte:.2f} ->VIEL_mehr_symbole"

    def __str__(self) -> str:
        return f"{self.puls} | {self.system}"


def boot(base: str = ".") -> OmegaState:
    """Nervensystem starten. 1 Aufruf = ich sehe alles."""
    return OmegaState(
        puls=_pulse(base),
        system=translate_system(),
    )


if __name__ == "__main__":
    s = boot()
    print(s.puls)
    print()
    print(s.system)
    print()

    # Self-check
    test = ".B30 x[schildpuls,vielfunk] ~E:med ->handeln []warten :)niedrig"
    print(f"check: {s.check(test)}")

    test2 = "Julian hat einen Burnout Score von 30 und nimmt Thyroxin"
    print(f"check: {s.check(test2)}")
