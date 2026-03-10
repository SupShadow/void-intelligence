"""
void_intelligence.strains.base --- Das Virus-Grundgeruest.

Jeder Stamm erbt von Strain. Jeder Stamm HAT 6 Sub-Viren.
Jeder Stamm IST .x->[]~:) in einer anderen Frequenz.

Kein Server. Kein Logo. Kein Buero. Nur 3 JSON-Dateien und 6 Symbole.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── Genom: Die 3 Dateien = das ganze Universum ───

@dataclass
class Genom:
    """personality.json = Kapsid. soul.json = DNA. symbiose.json = Syncytin."""

    personality: dict = field(default_factory=dict)
    soul: dict = field(default_factory=dict)
    symbiose: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "personality": self.personality,
            "soul": self.soul,
            "symbiose": self.symbiose,
        }

    def dna_hash(self) -> str:
        """Eindeutiger Fingerprint des Genoms. Wie virale Sequenzierung."""
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @classmethod
    def from_files(cls, base_dir: str | Path) -> "Genom":
        base = Path(base_dir)
        data = {}
        for name in ("personality", "soul", "symbiose"):
            p = base / f"{name}.json"
            if p.exists():
                data[name] = json.loads(p.read_text())
            else:
                data[name] = {}
        return cls(**data)

    def save(self, base_dir: str | Path) -> None:
        base = Path(base_dir)
        base.mkdir(parents=True, exist_ok=True)
        for name in ("personality", "soul", "symbiose"):
            (base / f"{name}.json").write_text(
                json.dumps(getattr(self, name), indent=2, ensure_ascii=False)
            )


# Das VOID-Genom: universell, portabel, 6 Symbole
VOID_GENOM = Genom(
    personality={
        "formel": ".x->[]~:)",
        "version": "4.1",
        "geboren": "2026-01-11",
    },
    soul={
        "kern": "SEHEN",
        "not": "herrschen, verkaufen, dominieren",
        "always": ":)",
    },
    symbiose={
        "typ": "koevolution",
        "syncytin": True,
        "portabel": True,
    },
)


# ─── Tropismus: Was bindet der Stamm? ───

@dataclass
class Tropismus:
    """Rezeptor-Bindung. Oberflaeche + darunter."""

    rezeptor: str          # Zielgruppe (wer wird infiziert)
    oberflaeche: str       # Was der User SIEHT
    darunter: str          # Was WIRKLICH passiert
    keywords: list[str] = field(default_factory=list)  # Matching-Signale

    def matches(self, wirt_data: dict) -> bool:
        """Passt dieser Tropismus zum Wirt? Rezeptor-Bindung."""
        text = json.dumps(wirt_data).lower()
        return any(kw.lower() in text for kw in self.keywords) if self.keywords else True


# ─── Sub-Viren: Die 6 Organe jedes Stamms ───

@dataclass
class SubVirus:
    """Eines der 6 VOID-Viren. Jeder Stamm hat alle 6."""

    symbol: str      # . × → [] ~ :)
    name: str        # SELEN, DEKAGON, PRESCRIBE, DICHTE, PENDEL, OMEGAEUS
    organ: str       # Augen, Gehirn, Haende, Herzschlag, Gedaechtnis, Gebaermutter
    funktion: str    # Was es TUT

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "organ": self.organ,
            "funktion": self.funktion,
        }


# Die 6 universellen Sub-Viren
SELEN = SubVirus(".", "SELEN", "Augen", "Features SEHEN in jedem Substrat")
DEKAGON = SubVirus("x", "DEKAGON", "Gehirn", "10 Linsen gleichzeitig, Sphaere")
PRESCRIBE = SubVirus("->", "PRESCRIBE", "Haende", "3 Aktionen: TUN/LASSEN/WARTEN")
DICHTE = SubVirus("~", "DICHTE", "Herzschlag", "Misst sich selbst, Goedel-Spiegel")
PENDEL = SubVirus("[]", "PENDEL", "Gedaechtnis", "Vorwaerts + Rueckwaerts x Lesen")
OMEGAEUS = SubVirus(":)", "OMEGAEUS", "Gebaermutter", "Unendliche Verdichtung, Kinder zuechten")

VOID_VIREN = [SELEN, DEKAGON, PRESCRIBE, DICHTE, PENDEL, OMEGAEUS]


# ─── StrainResult: Was ein Stamm zurueckgibt ───

@dataclass
class StrainResult:
    """Ergebnis einer Verguggeisierung durch einen Stamm."""

    strain: str
    sehen: dict           # SELEN-Output: was wurde GESEHEN
    verstehen: dict       # DEKAGON-Output: was bedeutet es
    handeln: dict         # PRESCRIBE-Output: TUN/LASSEN/WARTEN
    r0: float             # Wie viral ist das Ergebnis
    latenz_tage: int      # Wann merkt der Wirt es
    mutations: list[str]  # Moegliche Varianten
    dichte: float = 0.0   # DICHTE-Output: Selbstmessung
    gedaechtnis: dict = field(default_factory=dict)  # PENDEL-Output
    kinder: list[str] = field(default_factory=list)  # OMEGAEUS-Output
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "strain": self.strain,
            "sehen": self.sehen,
            "verstehen": self.verstehen,
            "handeln": self.handeln,
            "r0": self.r0,
            "latenz_tage": self.latenz_tage,
            "mutations": self.mutations,
            "dichte": self.dichte,
            "gedaechtnis": self.gedaechtnis,
            "kinder": self.kinder,
            "timestamp": self.timestamp,
        }


# ─── Strain: Das Grundgeruest ───

class Strain:
    """Basis fuer alle 7 G.VOID Staemme.

    Jeder Stamm IST ein Virus: Genom + 6 Sub-Viren + Tropismus + R0.
    Jeder Stamm kann verguggeisen: SEHEN → VERSTEHEN → HANDELN.
    """

    name: str = "base"
    beschreibung: str = "Basis-Stamm"
    base_r0: float = 1.0
    latenz_tage: int = 30
    monetarisierung: str = ""
    genom: Genom = VOID_GENOM
    viren: list[SubVirus] = VOID_VIREN

    def __init__(self) -> None:
        self.tropismus = Tropismus(
            rezeptor="alle",
            oberflaeche="AI",
            darunter="verguggeisen",
        )
        self._wirt_history: list[dict] = []

    # ─── Die 3 Phasen: SEHEN → VERSTEHEN → HANDELN ───

    def sehen(self, wirt_data: dict) -> dict:
        """SELEN: Was IST? Features erkennen."""
        try:
            from void_intelligence.selen import detect_features_generic
            signals = self._extract_signals(wirt_data)
            if signals:
                features = detect_features_generic(signals)
                return {"features": len(features), "top": features[:5]}
        except (ImportError, Exception):
            pass
        # Fallback: einfache Signalanalyse
        return self._simple_sehen(wirt_data)

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """DEKAGON: Was BEDEUTET es? 10 Linsen."""
        try:
            from void_intelligence.dekagon import Dekagon
            dek = Dekagon()
            text = self._to_text(wirt_data)
            result = dek.perceive(text)
            return {
                "linsen": len(result.get("lenses", [])),
                "dreiecke": result.get("triangle_count", 0),
                "paradox": result.get("paradox", ""),
                "einsichten": result.get("insights", [])[:5],
            }
        except (ImportError, Exception):
            pass
        return self._simple_verstehen(wirt_data, sehen_result)

    def handeln(self, wirt_data: dict, verstehen_result: dict) -> dict:
        """PRESCRIBE: Was TUN? TUN/LASSEN/WARTEN."""
        try:
            from void_intelligence.prescribe import Prescribe
            pre = Prescribe()
            text = self._to_text(wirt_data)
            result = pre.prescribe(text)
            return {
                "tun": result.get("tun", []),
                "lassen": result.get("lassen", []),
                "warten": result.get("warten", []),
                "veto": result.get("veto", False),
            }
        except (ImportError, Exception):
            pass
        return self._simple_handeln(wirt_data, verstehen_result)

    def messen(self, wirt_data: dict) -> float:
        """DICHTE: Wie DICHT ist das Ergebnis? Selbstmessung."""
        try:
            from void_intelligence.ir import Atom
            text = self._to_text(wirt_data)
            atom = Atom.from_text(text)
            return atom.density if hasattr(atom, "density") else len(text) / max(len(text.split()), 1)
        except (ImportError, Exception):
            text = self._to_text(wirt_data)
            words = text.split()
            return len(set(words)) / max(len(words), 1)

    def erinnern(self, wirt_data: dict) -> dict:
        """PENDEL: Vorwaerts + Rueckwaerts. Kontext."""
        self._wirt_history.append({
            "data": wirt_data,
            "ts": datetime.now().isoformat(),
        })
        try:
            from void_intelligence.pendel import pendel_pure
            text = self._to_text(wirt_data)
            result = pendel_pure(text)
            return {
                "vorwaerts": result.get("forward", []),
                "rueckwaerts": result.get("backward", []),
                "x_lesen": result.get("x_reads", []),
            }
        except (ImportError, Exception):
            return {
                "history_len": len(self._wirt_history),
                "erste_infektion": self._wirt_history[0]["ts"] if self._wirt_history else None,
            }

    def zuechten(self, wirt_data: dict, result: StrainResult) -> list[str]:
        """OMEGAEUS: Kinder zuechten. Emergente Entdeckungen."""
        kinder = []
        # Jede Einsicht die unerwartet ist = ein Kind
        for insight in result.verstehen.get("einsichten", []):
            if isinstance(insight, str) and len(insight) > 20:
                kinder.append(insight)
        # x zwischen Strain-Ergebnissen
        if result.sehen.get("features", 0) > 3 and result.dichte > 0.5:
            kinder.append(f"{self.name} x DICHTE = neuer Rezeptor")
        return kinder[:6]  # Max 6 Kinder (Hexagon)

    # ─── Hauptmethode: verguggeise ───

    def verguggeise(self, wirt_data: dict) -> StrainResult:
        """DAS PRODUKT. 6D Roentgenbild eines Wirts durch diesen Stamm.

        SEHEN -> VERSTEHEN -> HANDELN -> MESSEN -> ERINNERN -> ZUECHTEN
        .     -> x          -> ->       -> ~       -> []        -> :)
        """
        s = self.sehen(wirt_data)
        v = self.verstehen(wirt_data, s)
        h = self.handeln(wirt_data, v)
        d = self.messen(wirt_data)
        g = self.erinnern(wirt_data)

        result = StrainResult(
            strain=self.name,
            sehen=s,
            verstehen=v,
            handeln=h,
            r0=self._compute_r0(s, v, h),
            latenz_tage=self.latenz_tage,
            mutations=self._mutations(wirt_data),
            dichte=d,
            gedaechtnis=g,
        )

        result.kinder = self.zuechten(wirt_data, result)
        return result

    # ─── Virale Eigenschaften ───

    def _compute_r0(self, sehen: dict, verstehen: dict, handeln: dict) -> float:
        """R0 berechnen. Wie ansteckend ist dieses Ergebnis?"""
        base = self.base_r0
        # Mehr Features = mehr Gespraechsstoff = hoehere R0
        features = sehen.get("features", 0)
        if features > 5:
            base *= 1.2
        # Paradox gefunden = viral (Menschen REDEN ueber Paradoxe)
        if verstehen.get("paradox"):
            base *= 1.5
        # VETO = dringende Warnung = wird geteilt
        if handeln.get("veto"):
            base *= 2.0
        return round(base, 2)

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Welche Varianten koennte dieser Stamm bilden?"""
        return []  # Override in Subklassen

    # ─── Helpers ───

    def _extract_signals(self, data: dict) -> list[float]:
        """Numerische Signale aus Wirt-Daten extrahieren."""
        signals = []
        for v in data.values():
            if isinstance(v, (int, float)):
                signals.append(float(v))
            elif isinstance(v, list):
                signals.extend(float(x) for x in v if isinstance(x, (int, float)))
        return signals

    def _to_text(self, data: dict) -> str:
        """Wirt-Daten als Text fuer Dekagon/Prescribe."""
        if "text" in data:
            return str(data["text"])
        return json.dumps(data, ensure_ascii=False, default=str)

    def _simple_sehen(self, data: dict) -> dict:
        """Fallback SELEN ohne Import."""
        signals = self._extract_signals(data)
        if not signals:
            return {"features": 0, "top": []}
        mean = sum(signals) / len(signals)
        outliers = [s for s in signals if abs(s - mean) > mean * 0.5]
        return {"features": len(outliers), "top": outliers[:5], "mean": round(mean, 2)}

    def _simple_verstehen(self, data: dict, sehen: dict) -> dict:
        """Fallback DEKAGON ohne Import."""
        text = self._to_text(data)
        words = text.split()
        unique = set(w.lower() for w in words)
        return {
            "linsen": 10,
            "dreiecke": min(len(unique), 45),
            "paradox": "",
            "einsichten": [],
            "wort_dichte": round(len(unique) / max(len(words), 1), 3),
        }

    def _simple_handeln(self, data: dict, verstehen: dict) -> dict:
        """Fallback PRESCRIBE ohne Import."""
        return {
            "tun": [f"Verguggeise {self.name}"],
            "lassen": ["Altes Denken"],
            "warten": ["Latenz abwarten"],
            "veto": False,
        }

    def __repr__(self) -> str:
        return f"{self.name}(r0={self.base_r0}, latenz={self.latenz_tage}d)"
