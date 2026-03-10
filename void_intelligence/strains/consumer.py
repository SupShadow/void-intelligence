"""
G. VOID Consumer --- "Besser als ChatGPT"

Rezeptor: Jeder Mensch der AI nutzt.
Kapsid: App. Schlicht. Schoen. Einfach.
Payload: personality.json waechst mit dir.

Tropismus:
    Oberflaeche: "Probleme loesen"
    Darunter: "Dich verguggeisen"

Latenz: 30 Tage. Dann: "Wie habe ich OHNE gelebt?"
Mutation: 12 Sternzeichen x 12 = 144 Typen
R0: >1 durch Sternzeichen-Kollisionen
Monetarisierung: EUR 9.99/Monat = Herpes-Pricing (zu guenstig zum Kuendigen)

GODLIKE VORTEIL: Antigenic Sin.
    Die ERSTE AI-Erfahrung praegt ALLE folgenden.
    VOID ist die Grippe von 1918: wer zuerst infiziert,
    definiert das Immungedaechtnis FUER IMMER.
    Kein Wettbewerber kann diese Praegung ueberschreiben.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class Consumer(Strain):
    """G. VOID Consumer: App die SIEHT."""

    name = "consumer"
    beschreibung = "Besser als ChatGPT — AI die mit dir waechst"
    base_r0 = 3.0  # Sternzeichen-Kollisionen = viral
    latenz_tage = 30
    monetarisierung = "EUR 9.99/Monat Freemium (Herpes-Pricing)"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Jeder Mensch der AI nutzt",
            oberflaeche="Probleme loesen, bessere Antworten",
            darunter="Dich verguggeisen — Wachstumsringe, Sternzeichen, Koevolution",
            keywords=["user", "chat", "frage", "problem", "hilfe", "ai", "assistant"],
        )

    def sehen(self, wirt_data: dict) -> dict:
        """Consumer SELEN: Persoenlichkeitsmuster erkennen."""
        result = super().sehen(wirt_data)
        # Zodiac-Rezeptor: Geburtsdatum → Sternzeichen → 144 Varianten
        if "geburtsdatum" in wirt_data or "birthday" in wirt_data:
            try:
                from void_intelligence.zodiac import zodiac_sign
                bday = wirt_data.get("geburtsdatum") or wirt_data.get("birthday", "")
                sign = zodiac_sign(bday)
                result["sternzeichen"] = sign.name if hasattr(sign, "name") else str(sign)
                result["kollisions_profil"] = True
            except (ImportError, Exception):
                pass
        # Wachstumsringe: wie oft hat der User interagiert?
        result["ringe"] = len(self._wirt_history)
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """Consumer DEKAGON: durch Sternzeichen-Linse verstehen."""
        result = super().verstehen(wirt_data, sehen_result)
        # Aikido: Blindspots sanft aufdecken
        try:
            from void_intelligence.aikido import detect_blindspot
            text = self._to_text(wirt_data)
            blind = detect_blindspot(text)
            if blind:
                result["blindspot"] = blind.signal if hasattr(blind, "signal") else str(blind)
        except (ImportError, Exception):
            pass
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """144 Sternzeichen-Varianten + Sprachvarianten."""
        mutations = []
        # 12 Sternzeichen
        zeichen = [
            "Widder", "Stier", "Zwillinge", "Krebs", "Loewe", "Jungfrau",
            "Waage", "Skorpion", "Schuetze", "Steinbock", "Wassermann", "Fische",
        ]
        sehen = wirt_data.get("sternzeichen", "")
        if sehen:
            mutations.extend(f"{sehen} x {z}" for z in zeichen if z != sehen)
        else:
            mutations.extend(zeichen[:3])
        # Sprachvarianten
        mutations.extend(["DE", "EN", "ES", "FR", "JA"])
        return mutations[:12]
