"""
G. VOID Research --- "Guggeis Research"

Rezeptor: Forscher. Universitaeten. Thinktanks.
Kapsid: research.derguggeis.de (existiert!)
Payload: Lebendes Forschungsnetzwerk. Papers wachsen autonom.

Tropismus:
    Oberflaeche: Interdisziplinaere Forschung
    Darunter: .x->[]~:) als universelle Forschungs-IR

Latenz: Paper lebt 5 Jahre. Dann: 10x so viele Einsichten.
R0: 6.0! (1 Paper triggert 6 Nachbarn = Kettenreaktion)
Monetarisierung: Pattern verschenken, Infrastruktur verkaufen

GODLIKE VORTEIL: Living Papers.
    Tote Papers werden einmal geschrieben und sterben.
    Living Papers wachsen AUTONOM. Paarung. Kettenreaktion.
    Nach 5 Jahren: das Paper von heute ist 10x dichter.
    τ-MOAT: jeder Tag den ein Paper lebt macht es WERTVOLLER.
    Kein Wettbewerber kann 5 Jahre Wachstum ueberspringen.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class Research(Strain):
    """G. VOID Research: Living Papers, Kettenreaktionen, τ-MOAT."""

    name = "research"
    beschreibung = "Guggeis Research — Papers die leben und sich paaren"
    base_r0 = 6.0  # 1 Paper triggert 6 Nachbarn
    latenz_tage = 1825  # 5 Jahre
    monetarisierung = "EUR 99/Monat pro Lab (Research Cloud)"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Forscher, Universitaeten, Thinktanks",
            oberflaeche="Interdisziplinaere Forschung, Cross-Domain",
            darunter=".x->[]~:) als universelle Forschungs-IR, Living Papers",
            keywords=["research", "paper", "forschung", "wissenschaft", "study",
                      "theorem", "hypothesis", "experiment", "university", "lab"],
        )
        # 7 Guggeis-Linsen
        self.linsen = [
            "Stribeck", "Goedel", "Collision",
            "SELEN", "Inverse", "Kumbha", "Paper x Paper",
        ]

    def sehen(self, wirt_data: dict) -> dict:
        """Research SELEN: Papers als lebende Organismen erkennen."""
        result = super().sehen(wirt_data)
        # Paper-Erkennung
        try:
            from void_intelligence.papers import discover_papers, extract_identity
            papers_dir = wirt_data.get("papers_dir", "papers/")
            papers = discover_papers(papers_dir)
            result["living_papers"] = len(papers)
            if papers:
                identities = []
                for p in papers[:5]:
                    try:
                        identity = extract_identity(p)
                        identities.append(identity.title if hasattr(identity, "title") else str(identity))
                    except Exception:
                        pass
                result["top_papers"] = identities
        except (ImportError, Exception):
            pass
        # Paradigm-Count
        paradigms = wirt_data.get("paradigms", wirt_data.get("paradigmen", 0))
        if paradigms:
            result["paradigm_dichte"] = paradigms
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """Research DEKAGON: durch 7 Linsen verstehen."""
        result = super().verstehen(wirt_data, sehen_result)
        # Kettenreaktions-Potential
        papers = sehen_result.get("living_papers", 0)
        if papers > 1:
            # n Papers = n*(n-1)/2 moegliche Paarungen
            paarungen = papers * (papers - 1) // 2
            result["paarungs_potential"] = paarungen
            result["kettenreaktion_r0"] = round(papers * 0.6, 1)  # 60% triggern Nachbarn
        # 7 Linsen anwenden
        result["linsen"] = self.linsen
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Jede Linse = eigener Virusstamm."""
        return self.linsen + ["Neue Linse (emergent)"]
