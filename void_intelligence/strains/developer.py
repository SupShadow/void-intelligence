"""
G. VOID Developer --- "VOID SDK"

Rezeptor: Entwickler die AI bauen.
Kapsid: pip install void-intelligence / npm install @void/sdk
Payload: 6 Void-Viren als Bibliothek.

Tropismus:
    Oberflaeche: "Bessere AI bauen"
    Darunter: VOID-DNA in jeder App

Latenz: Sofort nutzbar, aber Tiefe kommt nach 90 Tagen.
R0: EXPONENTIELL. 1 Dev → 1 App → 10.000 User.
Monetarisierung: Open Core. Virus gratis. Cloud-Virom bezahlt.

GODLIKE VORTEIL: Symbiotische Infektion.
    Jeder Developer der VOID SDK nutzt WIRD zum Vektor.
    Seine App infiziert SEINE User. Ohne unser Zutun.
    10 Devs = 10 Apps = 100.000 Wirte. Zero Marketing.
    Wie TCP/IP: niemand weiss es, alle nutzen es.
"""

from __future__ import annotations

from void_intelligence.strains.base import Strain, Tropismus


class Developer(Strain):
    """G. VOID Developer: SDK das jede App zum Wirt macht."""

    name = "developer"
    beschreibung = "pip install void-intelligence — jede App wird Wirt"
    base_r0 = 5.0  # Exponentiell: 1 Dev = Tausende User
    latenz_tage = 7  # Sofort nutzbar
    monetarisierung = "Open Core. EUR 0.001/Verguggeisierung"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Entwickler die AI bauen",
            oberflaeche="Bessere AI bauen, bessere User Experience",
            darunter="VOID-DNA in jeder App — jeder User wird Wirt",
            keywords=["developer", "dev", "sdk", "api", "code", "python", "npm",
                      "import", "install", "library", "framework", "build"],
        )

    def sehen(self, wirt_data: dict) -> dict:
        """Developer SELEN: Codebase als Organismus sehen."""
        result = super().sehen(wirt_data)
        # Welche VOID-Module nutzt der Dev bereits?
        used_modules = wirt_data.get("modules", wirt_data.get("imports", []))
        if used_modules:
            result["infizierte_module"] = len(used_modules)
            result["virom_abdeckung"] = round(len(used_modules) / 86, 3)  # 86 Module existieren
        # Stack-Erkennung
        stack = wirt_data.get("stack", wirt_data.get("language", ""))
        if stack:
            result["kapsid"] = f"void-{stack.lower()}"
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """Developer DEKAGON: App-Architektur als Organismus."""
        result = super().verstehen(wirt_data, sehen_result)
        abdeckung = sehen_result.get("virom_abdeckung", 0)
        result["integration_tiefe"] = (
            "Erstinfektion" if abdeckung < 0.1 else
            "Inkubation" if abdeckung < 0.3 else
            "Symptomatisch" if abdeckung < 0.6 else
            "Vollständig infiziert" if abdeckung < 0.9 else
            "Koevolution"
        )
        # Welche Sub-Viren fehlen?
        alle_organe = {"selen", "dekagon", "prescribe", "dichte", "pendel", "omegaeus"}
        genutzt = set(str(m).lower() for m in wirt_data.get("modules", []))
        fehlend = alle_organe - genutzt
        if fehlend:
            result["fehlende_organe"] = list(fehlend)
        return result

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Sprach-Kapsid-Varianten. Selbes Genom, 4+ Kapside."""
        return ["Python", "TypeScript", "Rust", "Go", "Swift", "Kotlin"]
