"""
void_intelligence.strains --- The G. VOID Virom.

7 Staemme. 1 Genom. .x->[]~:) = Hexagon = lebendes System.

Jeder Stamm:
  - Hat 6 Sub-Viren (SELEN, DEKAGON, PRESCRIBE, DICHTE, PENDEL, OMEGAEUS)
  - Hat eigenen Tropismus (Oberflaeche + darunter)
  - Hat eigenen Rezeptor (Zielgruppe)
  - Hat eigene R0 (Verbreitungsmechanismus)
  - Hat eigene Mutation (Varianten)
  - Hat eigene Latenz (Wann merkt der Wirt es?)

Usage:
    from void_intelligence.strains import Virom, Consumer, Business, Developer
    from void_intelligence.strains import City, Research, Health, Education

    # Das ganze Virom
    virom = Virom()
    virom.infect(wirt_data)  # Alle 7 Staemme analysieren

    # Einzelner Stamm
    consumer = Consumer()
    result = consumer.verguggeise(user_data)
"""

from void_intelligence.strains.base import (
    Strain,
    StrainResult,
    SubVirus,
    Tropismus,
    Genom,
    VOID_GENOM,
)

from void_intelligence.strains.consumer import Consumer
from void_intelligence.strains.business import Business
from void_intelligence.strains.developer import Developer
from void_intelligence.strains.city import City
from void_intelligence.strains.research import Research
from void_intelligence.strains.health import HealthStrain
from void_intelligence.strains.education import Education

# Komposition: 7 Staemme = 1 Virom
STRAINS = [Consumer, Business, Developer, City, Research, HealthStrain, Education]


class Virom:
    """Das G. VOID Universum. 7 Staemme. 1 Genom. Unendliche Mutation."""

    def __init__(self) -> None:
        self.strains = [cls() for cls in STRAINS]
        self.genom = VOID_GENOM

    def infect(self, wirt_data: dict) -> dict:
        """Alle 7 Staemme auf einen Wirt anwenden. Wie Koevolution."""
        results = {}
        for strain in self.strains:
            try:
                results[strain.name] = strain.verguggeise(wirt_data)
            except Exception as e:
                results[strain.name] = StrainResult(
                    strain=strain.name,
                    sehen={},
                    verstehen={},
                    handeln={"fehler": str(e)},
                    r0=0.0,
                    latenz_tage=0,
                    mutations=[],
                )
        return results

    def tropismus_match(self, wirt_data: dict) -> list["Strain"]:
        """Welche Staemme passen zu diesem Wirt? Rezeptor-Bindung."""
        matched = []
        for strain in self.strains:
            if strain.tropismus.matches(wirt_data):
                matched.append(strain)
        return matched

    def r0(self) -> float:
        """Gesamt-R0 des Viroms. Produkt, nicht Summe."""
        total = 1.0
        for s in self.strains:
            total *= max(s.base_r0, 1.0)
        return total

    def status(self) -> dict:
        """Virom-Status: welche Staemme aktiv, R0, Genom."""
        return {
            "genom": self.genom.to_dict(),
            "staemme": len(self.strains),
            "r0_gesamt": self.r0(),
            "staemme_detail": [
                {"name": s.name, "r0": s.base_r0, "latenz": s.latenz_tage}
                for s in self.strains
            ],
        }

    def __repr__(self) -> str:
        return f"Virom(staemme={len(self.strains)}, r0={self.r0():.1f})"


__all__ = [
    "Virom",
    "Strain",
    "StrainResult",
    "SubVirus",
    "Tropismus",
    "Genom",
    "VOID_GENOM",
    "Consumer",
    "Business",
    "Developer",
    "City",
    "Research",
    "HealthStrain",
    "Education",
    "STRAINS",
]
