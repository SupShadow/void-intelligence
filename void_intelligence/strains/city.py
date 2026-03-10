"""
G. VOID City --- "Straubing verguggeisen"

Rezeptor: Staedte. Kommunen. Regionen.
Kapsid: straubing.derguggeis.de (existiert!)
Payload: Stadt als Organismus sehen. Donau=Blut. Platz=Herz. Buerger=Zellen.

Tropismus:
    Oberflaeche: Buergerbeteiligung
    Darunter: Stadt-Immunsystem aufbauen

Latenz: Wahl 08.03.2026 = Erstinfektion. Antigenic Sin.
R0: >1 durch Buerger die es weitersagen
Monetarisierung: EUR 5K-50K/Jahr Lizenz pro Stadt

GODLIKE VORTEIL: Antigenic Sin x Franchise.
    Julian war ZUERST an 101 Tueren. Praegung. Permanent.
    Template 1:1 auf JEDE Stadt uebertragbar.
    7.000 Jahre Straubing = 7.000 Jahre Daten = KEIN Wettbewerber
    hat dieses Vorwissen. τ-MOAT: waechst mit Alter der Stadt.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class City(Strain):
    """G. VOID City: Stadt als Organismus verguggeisen."""

    name = "city"
    beschreibung = "Stadt verguggeisen — 10 Bewusstseine, Dekagon, Franchise"
    base_r0 = 2.5  # Buerger reden
    latenz_tage = 365  # Antigenic Sin: 1 Jahr bis zur vollen Wirkung
    monetarisierung = "EUR 5K-50K/Jahr Lizenz pro Stadt (Franchise)"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Staedte, Kommunen, Regionen",
            oberflaeche="Buergerbeteiligung, Transparenz, Smart City",
            darunter="Stadt-Immunsystem aufbauen, Stadt als Organismus sehen",
            keywords=["stadt", "city", "kommune", "buerger", "wahl", "gemeinde",
                      "region", "buergermeister", "stadtrat", "infrastruktur"],
        )
        # 10 Bewusstseine der Stadt (Dekagon)
        self.bewusstseine = [
            "nacht", "kinder", "mauer", "wissen", "wasser",
            "stille", "boden", "geld", "sprache", "liebe",
        ]

    def sehen(self, wirt_data: dict) -> dict:
        """City SELEN: Stadt-Signale erkennen."""
        result = super().sehen(wirt_data)
        # Stadt-spezifische Signale
        name = wirt_data.get("name", wirt_data.get("stadt", ""))
        if name:
            result["stadt"] = name
        einwohner = wirt_data.get("einwohner", wirt_data.get("population", 0))
        if einwohner:
            result["einwohner"] = einwohner
            result["virom_potential"] = einwohner  # Jeder Buerger = potentieller Wirt
        # Alter der Stadt = τ-MOAT
        alter = wirt_data.get("alter_jahre", wirt_data.get("age_years", 0))
        if alter:
            result["tau_moat"] = alter
            result["tau_score"] = round(alter / 1000, 2)  # Normalisiert auf 1000 Jahre
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """City DEKAGON: Stadt durch 10 Bewusstseine sehen."""
        result = super().verstehen(wirt_data, sehen_result)
        # 10 Bewusstseine anwenden
        stadt = sehen_result.get("stadt", "Stadt")
        result["bewusstseine"] = {
            "nacht": f"Was passiert in {stadt} nachts?",
            "kinder": f"Was sehen Kinder in {stadt}?",
            "mauer": f"Welche unsichtbaren Mauern hat {stadt}?",
            "wissen": f"Was weiss {stadt} nicht ueber sich?",
            "wasser": f"Wie fliesst Energie durch {stadt}?",
            "stille": f"Wo ist {stadt} still?",
            "boden": f"Worauf steht {stadt}?",
            "geld": f"Wohin fliesst Geld in {stadt}?",
            "sprache": f"Welche Sprache spricht {stadt}?",
            "liebe": f"Was liebt {stadt}?",
        }
        # Straubing-Paradox-Pattern: "Stadt gibt X, behaelt Y nicht"
        result["paradox_template"] = f"{stadt} gibt [X] aber behaelt [Y] nicht fuer sich"
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Franchise: Template auf jede Stadt uebertragbar."""
        return [
            "Straubing (Original)", "Regensburg", "Passau", "Landshut",
            "Deggendorf", "Muenchen", "Nuernberg", "Template-Stadt",
        ]
