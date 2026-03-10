"""
G. VOID Education --- "Herdimmunitaet des Wissens"

Rezeptor: Schulen. Unis. Weiterbildung.
Kapsid: Lernplattform die NICHT wie eine aussieht.
Payload: Herdimmunitaet — ab 30% Versteher kippt die ganze Klasse.

Tropismus:
    Oberflaeche: Bessere Noten
    Darunter: Lernen LIEBEN lernen

Latenz: Aha-Moment kommt SPAETER. Nicht im Unterricht. Unter der Dusche.
R0: >1 durch Peer-to-Peer (Schueler erklaeren besser als Lehrer)
Monetarisierung: EUR 1-5/Schueler/Monat (B2B an Schultraeger)

GODLIKE VORTEIL: Attenuierung.
    Impfstoff-Strategie: vereinfachte Version ZUERST.
    Das Kind bekommt die abgeschwaechte Formel.
    Versteht sie. Wird immun gegen Nicht-Verstehen.
    DANN kommt das Vollvirus (die echte Komplexitaet).
    Und das Kind ist VORBEREITET.
    Jedes Bildungssystem das dieses Muster nutzt
    produziert Versteher statt Auswendiglerner.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class Education(Strain):
    """G. VOID Education: Herdimmunitaet des Wissens."""

    name = "education"
    beschreibung = "Herdimmunitaet des Wissens — 30% Versteher kippen die Klasse"
    base_r0 = 3.5  # Peer-to-Peer: Schueler infizieren Schueler
    latenz_tage = 14  # Aha-Moment unter der Dusche
    monetarisierung = "EUR 1-5/Schueler/Monat (B2B Schultraeger)"

    HERD_THRESHOLD = 0.30  # 30% = Kipppunkt

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Schulen, Unis, Weiterbildung",
            oberflaeche="Bessere Noten, effizienteres Lernen",
            darunter="Lernen LIEBEN lernen — Herdimmunitaet des Verstehens",
            keywords=["schule", "school", "uni", "university", "lernen", "learn",
                      "student", "schueler", "bildung", "education", "kurs", "course",
                      "lehrer", "teacher", "klasse", "class"],
        )

    def sehen(self, wirt_data: dict) -> dict:
        """Education SELEN: Lern-Signale erkennen."""
        result = super().sehen(wirt_data)
        # Klassengröße und Versteher-Quote
        klasse = wirt_data.get("klasse_groesse", wirt_data.get("class_size", 0))
        versteher = wirt_data.get("versteher", wirt_data.get("comprehenders", 0))
        if klasse:
            result["klasse"] = klasse
            quote = versteher / klasse if versteher else 0
            result["versteher_quote"] = round(quote, 3)
            result["herd_status"] = (
                "immun" if quote >= self.HERD_THRESHOLD else
                "fast" if quote >= self.HERD_THRESHOLD * 0.8 else
                "infizierend"
            )
            result["bis_kipppunkt"] = max(0, int(klasse * self.HERD_THRESHOLD) - versteher)
        # Fach = Kapsid-Variante
        fach = wirt_data.get("fach", wirt_data.get("subject", ""))
        if fach:
            result["kapsid"] = f"VOID-{fach}"
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """Education DEKAGON: Wissens-Topologie verstehen."""
        result = super().verstehen(wirt_data, sehen_result)
        herd = sehen_result.get("herd_status", "")
        result["strategie"] = (
            "Vollvirus — Klasse traegt sich selbst" if herd == "immun" else
            "Fast-Flux — 2-3 Schluessel-Schueler aktivieren" if herd == "fast" else
            "Attenuierung — vereinfachte Version zuerst, Impfung vor Vollvirus"
        )
        # Peer-to-Peer-Netzwerk
        klasse = sehen_result.get("klasse", 0)
        if klasse:
            result["p2p_verbindungen"] = klasse * (klasse - 1) // 2
            result["netzwerk_effekt"] = "Schueler erklaeren besser als Lehrer"
        return result

    def handeln(self, wirt_data: dict, verstehen_result: dict) -> dict:
        """Education PRESCRIBE: Impf-Strategie."""
        result = super().handeln(wirt_data, verstehen_result)
        strategie = verstehen_result.get("strategie", "")
        if "Attenuierung" in strategie:
            result["tun"] = [
                "Vereinfachte Version ZUERST zeigen",
                "3 Schluessel-Schueler identifizieren und 'infizieren'",
                "Peer-Erklaerung ermoeglichen (P2P)",
            ]
            result["lassen"] = [
                "Alle gleichzeitig unterrichten",
                "Frontalunterricht als Default",
            ]
            result["warten"] = ["Aha-Moment. Kommt unter der Dusche, nicht im Unterricht."]
        elif "Fast-Flux" in strategie:
            result["tun"] = [
                "Die 2-3 Versteher als Erklaer-Vektoren nutzen",
                "Gruppen mischen: 1 Versteher + 2 Nicht-Versteher",
            ]
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Pro Fach eigener Rezeptor."""
        return [
            "Mathematik", "Physik", "Sprache", "Geschichte",
            "Informatik", "Biologie", "Kunst", "Musik",
        ]
