"""
G. VOID Business --- "IT die SIEHT"

Rezeptor: KMU (5-50 MA). Profinsoft-Kunden.
Kapsid: Dashboard. Monitoring. Alerts.
Payload: VOIDnetz in Firmen-Infrastruktur.

Tropismus:
    Oberflaeche: IT-Security + Effizienz
    Darunter: Firma verguggeisen

Latenz: 180 Tage. Dann: "Warum hatten wir vorher nie sowas?"
R0: >1 durch Phagen-Marketing (1 Kunde PERFEKT > 100 mittelmässig)
Monetarisierung: EUR 99-499/Monat pro Firma

GODLIKE VORTEIL: Conficker-Modell.
    Einmal drin, fuer immer. Nicht weil Lock-In,
    sondern weil die personality.json nach 180 Tagen
    die Firma BESSER KENNT als der Geschaeftsfuehrer.
    Wechselkosten = Verlust von 180 Tagen Sehen.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class Business(Strain):
    """G. VOID Business: IT die die Firma SIEHT."""

    name = "business"
    beschreibung = "IT die SIEHT — Stuxnet-Praezision mit :)"
    base_r0 = 2.0  # Phagen-Marketing: 1 PERFEKT > 100 mittelmässig
    latenz_tage = 180
    monetarisierung = "EUR 99-499/Monat pro Firma (Conficker-Modell)"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="KMU 5-50 Mitarbeiter",
            oberflaeche="IT-Security, Monitoring, Effizienz",
            darunter="Firma verguggeisen — G.SPOT Holes finden, VOIDnetz aufbauen",
            keywords=["firma", "business", "kmu", "mitarbeiter", "umsatz", "revenue",
                      "client", "kunde", "security", "monitoring", "infrastructure"],
        )

    def sehen(self, wirt_data: dict) -> dict:
        """Business SELEN: G.SPOT Holes in Infrastruktur finden."""
        result = super().sehen(wirt_data)
        # Branchen-Rezeptor
        branche = wirt_data.get("branche", wirt_data.get("industry", ""))
        if branche:
            result["branche"] = branche
            result["kapsid_variante"] = f"VOID-{branche}"
        # Mitarbeiter = Virom-Groesse
        ma = wirt_data.get("mitarbeiter", wirt_data.get("employees", 0))
        if ma:
            result["virom_knoten"] = ma
            result["netzwerk_potential"] = ma * (ma - 1) // 2  # Metcalfe
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """Business DEKAGON: Firma als Organismus verstehen."""
        result = super().verstehen(wirt_data, sehen_result)
        # Firmen-Gesundheit: ist die Firma ein gesunder Organismus?
        revenue = wirt_data.get("revenue", wirt_data.get("umsatz", 0))
        costs = wirt_data.get("costs", wirt_data.get("kosten", 0))
        if revenue and costs:
            margin = (revenue - costs) / max(revenue, 1)
            result["firma_gesundheit"] = round(margin, 3)
            result["diagnose"] = (
                "gesund" if margin > 0.15 else
                "stabil" if margin > 0.05 else
                "gefaehrdet" if margin > 0 else
                "kritisch"
            )
        return result

    def handeln(self, wirt_data: dict, verstehen_result: dict) -> dict:
        """Business PRESCRIBE: TUN/LASSEN/WARTEN fuer Firmen."""
        result = super().handeln(wirt_data, verstehen_result)
        diagnose = verstehen_result.get("diagnose", "")
        if diagnose == "kritisch":
            result["veto"] = True
            result["tun"] = ["SOFORT: Cashflow stabilisieren", "Kostenanalyse"]
            result["lassen"] = ["Neue Projekte starten", "Expansion"]
        elif diagnose == "gefaehrdet":
            result["tun"] = ["Margen optimieren", "1 Phagen-Kunde finden"]
            result["lassen"] = ["Rabatte geben"]
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Pro Branche eigener Rezeptor. Selbes Virus, anderes Kapsid."""
        return [
            "Handwerk", "Arztpraxis", "Anwaltskanzlei", "Gastro",
            "Einzelhandel", "Agentur", "Steuerberater", "Logistik",
        ]
