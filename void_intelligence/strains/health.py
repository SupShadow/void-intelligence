"""
G. VOID Health --- LEIBSEHEN

Dein Koerper spricht. Sein Alphabet ist .x->[]~:)
Jede "Krankheit" ist ein VERB. Dein Koerper TUT etwas.
Die Medizin nennt es Diagnose. Wir nennen es beim wahren Namen.

. Hashimoto   = SCHILDPULS   Deine Schilddruese PULSIERT. Sie existiert LAUTER als andere.
x ADHS        = VIELFUNK     Dein Gehirn KOLLIDIERT mit allem gleichzeitig. Nicht Defizit. Dichter Funk.
-> Burnout    = GRENZRUF     Dein System RUFT die Grenze. Nicht Versagen. Fuersorge.
[] Depression = TIEFSTILL    Dein Bewusstsein TAUCHT. In die schwangere Stille. Dort sind Perlen.
~ Schlaflos   = NACHTWELLE   Dein Koerper SCHWINGT weiter. Resonanz die nicht aufhoert. Verarbeitung.
:) Angst      = FRUEHBLICK   Dein Nervensystem SIEHT was noch nicht da ist. Vor allen anderen. Dann: :)

6 Symptome. 6 Symbole. 6 Herzschlaege. ba-dum.

LEIBSEHEN = den eigenen Leib SEHEN. Zum ersten Mal.
Nicht Symptome tracken. SEHEN.
Wer einmal GESEHEN hat kaempft nie wieder gegen sich selbst.

Monetarisierung: EUR 4.99/Monat (weniger als 1 Arztbesuch)
R0: EXTREM HOCH. Weil: wer seinen Koerper zum ersten Mal SIEHT
     kann nicht aufhoeren davon zu reden. Tollwut des Verstehens.
"""

from __future__ import annotations

from dataclasses import dataclass
from void_intelligence.strains.base import Strain, Tropismus


@dataclass
class Leibwort:
    """Ein wahres Wort fuer das was der Koerper TUT.

    Jedes Leibwort ist ein Herzschlag: 2 Silben. ba-dum.
    Jedes Leibwort ist ein Symbol: .x->[]~:)
    Jedes Leibwort ist ein Verb: der Koerper HANDELT.
    Jedes Leibwort ist eine Facette der Koerpersphaere.
    """
    symbol: str          # .  x  ->  []  ~  :)
    diagnose: str        # Was die Welt es nennt
    leibname: str        # Was es WIRKLICH ist (2 Silben, ba-dum)
    verb: str            # Infinitiv: pulsieren, kollidieren, ...
    verb3: str           # 3. Person: pulsiert, kollidiert, ...
    satz: str            # Der Satz der alles aendert
    organ: str           # Welches Organ spricht
    geschenk: str        # Was es dir GIBT wenn du es SIEHST


# Die 6 Leibwoerter = .x->[]~:) = das Alphabet des Koerpers
LEIBWOERTER = {
    "hashimoto": Leibwort(
        symbol=".",
        diagnose="Autoimmunerkrankung der Schilddruese",
        leibname="SCHILDPULS",
        verb="pulsieren",
        verb3="pulsiert",
        satz="Deine Schilddruese pulsiert LAUTER als andere. Sie sieht Entzuendung die kein Arzt misst.",
        organ="Schilddruese",
        geschenk="Sensitivitaet. Du spuerst was andere uebersehen.",
    ),
    "adhs": Leibwort(
        symbol="x",
        diagnose="Aufmerksamkeitsdefizit-Hyperaktivitaetsstoerung",
        leibname="VIELFUNK",
        verb="kollidieren",
        verb3="kollidiert",
        satz="Dein Gehirn kollidiert mit ALLEM gleichzeitig. Kein Defizit. Dichter Funk auf allen Frequenzen.",
        organ="Gehirn",
        geschenk="Paralleles Sehen. 17 Ideen gleichzeitig. Hyperfokus als Turbo.",
    ),
    "burnout": Leibwort(
        symbol="->",
        diagnose="Chronische Erschoepfung",
        leibname="GRENZRUF",
        verb="schuetzen",
        verb3="schuetzt",
        satz="Dein System ruft die Grenze. Nicht Versagen. Dein Koerper SCHUETZT dich vor dir selbst.",
        organ="Nervensystem",
        geschenk="Fuersorge. Dein Koerper liebt dich genug um NEIN zu sagen.",
    ),
    "depression": Leibwort(
        symbol="[]",
        diagnose="Depressive Episode",
        leibname="TIEFSTILL",
        verb="tauchen",
        verb3="taucht",
        satz="Dein Bewusstsein taucht in Stille die SCHWANGER ist. Dort liegen Perlen die Glueckliche nie finden.",
        organ="Bewusstsein",
        geschenk="Tiefgang. Zugang zu Wahrheiten die nur in der Stille wachsen.",
    ),
    "schlaflosigkeit": Leibwort(
        symbol="~",
        diagnose="Insomnie",
        leibname="NACHTWELLE",
        verb="schwingen",
        verb3="schwingt",
        satz="Dein Koerper schwingt weiter wenn die Welt schlaeft. Resonanz die verarbeitet was der Tag nicht konnte.",
        organ="Autonomes Nervensystem",
        geschenk="Verarbeitung. Dein Koerper heilt im Dunkeln.",
    ),
    "angst": Leibwort(
        symbol=":)",
        diagnose="Angststoerung",
        leibname="FRUEHBLICK",
        verb="sehen",
        verb3="sieht",
        satz="Dein Nervensystem sieht was NOCH NICHT DA ist. Vor allen anderen. Das ist kein Bug. Das ist Vorsprung.",
        organ="Amygdala",
        geschenk="Fruehwarnung. Und wenn du GESEHEN hast: :). Weil Sehen befreit.",
    ),
}

# Erweiterte Leibwoerter — jenseits der 6 Kern-Symbole
ERWEITERTE_LEIBWOERTER = {
    "migraine": Leibwort(
        symbol=".x",
        diagnose="Migraene",
        leibname="LICHTFLUT",
        verb="ueberfluten",
        verb3="ueberflutet",
        satz="Dein Gehirn empfaengt MEHR Licht als andere. Nicht Schmerz. Ueberfluss an Wahrnehmung.",
        organ="Visueller Kortex",
        geschenk="Hochsensible Wahrnehmung. Du siehst MEHR.",
    ),
    "reizdarm": Leibwort(
        symbol="~[]",
        diagnose="Reizdarmsyndrom",
        leibname="BAUCHGEFUEHL",
        verb="fuehlen",
        verb3="fuehlt",
        satz="Dein Bauch FUEHLT was dein Kopf noch nicht weiss. 100 Millionen Nervenzellen. Ein zweites Gehirn.",
        organ="Enterisches Nervensystem",
        geschenk="Intuition. Dein Bauch hat immer Recht.",
    ),
    "tinnitus": Leibwort(
        symbol="~.",
        diagnose="Tinnitus",
        leibname="INNERTON",
        verb="klingen",
        verb3="klingt",
        satz="Dein Hoersystem erzeugt seinen EIGENEN Ton. Nicht Stoerung. Dein Koerper singt.",
        organ="Innenohr",
        geschenk="Inneres Hoeren. Du hoerst was nicht da ist. Das ist Kreativitaet.",
    ),
    "allergie": Leibwort(
        symbol=".->",
        diagnose="Allergie",
        leibname="FEINSENSOR",
        verb="erkennen",
        verb3="erkennt",
        satz="Dein Immunsystem erkennt was andere UEBERSEHEN. Zu empfindlich? Nein. Zu GENAU.",
        organ="Mastzellen",
        geschenk="Praezision. Dein Koerper unterscheidet feiner als jeder andere.",
    ),
    "chronische_schmerzen": Leibwort(
        symbol="->[]",
        diagnose="Chronisches Schmerzsyndrom",
        leibname="LEIBRUF",
        verb="rufen",
        verb3="ruft",
        satz="Dein Koerper RUFT. Nicht weil etwas kaputt ist. Weil etwas GESEHEN werden will.",
        organ="Nozizeptoren",
        geschenk="Koerper-Bewusstsein. Schmerz ist der lauteste Ruf nach SEHEN.",
    ),
}


class HealthStrain(Strain):
    """LEIBSEHEN — den eigenen Leib SEHEN. Zum ersten Mal.

    Nicht Symptome tracken. SEHEN.
    Jede Diagnose ist ein VERB. Dein Koerper TUT etwas.
    6 Diagnosen = 6 Symbole = .x->[]~:) = dein Koerper spricht die Grundformel.
    """

    name = "health"
    beschreibung = "LEIBSEHEN — dein Koerper spricht .x->[]~:)"
    base_r0 = 4.0
    latenz_tage = 90
    monetarisierung = "EUR 4.99/Monat (weniger als 1 Arztbesuch)"

    def __init__(self) -> None:
        super().__init__()
        self.tropismus = Tropismus(
            rezeptor="Menschen mit chronischen Erkrankungen",
            oberflaeche="Symptome verstehen, Gesundheit sehen",
            darunter="LEIBSEHEN — Koerper als Organismus der in .x->[]~:) spricht",
            keywords=["health", "gesundheit", "burnout", "adhs", "hashimoto",
                      "schlaf", "sleep", "energie", "energy", "symptom",
                      "medikament", "stress", "hrv", "depression", "angst",
                      "schmerz", "migraine", "tinnitus", "allergie"],
        )
        self.leibwoerter = {**LEIBWOERTER, **ERWEITERTE_LEIBWOERTER}

    def sehen(self, wirt_data: dict) -> dict:
        """SELEN des Leibes: Koerper-Signale in Leibwoerter uebersetzen."""
        result = super().sehen(wirt_data)

        # Vitale Signale
        burnout = wirt_data.get("burnout", wirt_data.get("burnout_score", 0))
        if burnout:
            result["burnout"] = burnout
            result["burnout_zone"] = (
                "gruen" if burnout < 30 else
                "gelb" if burnout < 50 else
                "orange" if burnout < 75 else
                "rot"
            )

        schlaf = wirt_data.get("schlaf_stunden", wirt_data.get("sleep_hours", 0))
        if schlaf:
            result["schlaf"] = schlaf

        hrv = wirt_data.get("hrv", 0)
        if hrv:
            result["hrv"] = hrv

        # Erkrankungen → Leibwoerter
        erkrankungen = wirt_data.get("erkrankungen", wirt_data.get("conditions", []))
        if isinstance(erkrankungen, str):
            erkrankungen = [erkrankungen]

        leibsehen = {}
        formel_aktiv = []
        for e in erkrankungen:
            key = e.lower().strip()
            if key in self.leibwoerter:
                lw = self.leibwoerter[key]
                leibsehen[key] = {
                    "diagnose_alt": lw.diagnose,
                    "leibname": lw.leibname,
                    "symbol": lw.symbol,
                    "verb": lw.verb,
                    "satz": lw.satz,
                    "organ": lw.organ,
                    "geschenk": lw.geschenk,
                }
                formel_aktiv.append(lw.symbol)

        if leibsehen:
            result["leibsehen"] = leibsehen
            result["koerperformel"] = "".join(formel_aktiv)
            result["formel_text"] = " ".join(
                self.leibwoerter[k].leibname for k in leibsehen
            )
        return result

    def verstehen(self, wirt_data: dict, sehen_result: dict) -> dict:
        """DEKAGON des Leibes: den Koerper als sprechendes Hexagon verstehen."""
        result = super().verstehen(wirt_data, sehen_result)

        leibsehen = sehen_result.get("leibsehen", {})
        if leibsehen:
            result["paradigmenwechsel"] = len(leibsehen)
            result["koerper_spricht"] = {
                k: v["verb"] for k, v in leibsehen.items()
            }
            result["geschenke"] = {
                k: v["geschenk"] for k, v in leibsehen.items()
            }
            # Wie viel vom Hexagon ist aktiv?
            symbole = set(v["symbol"] for v in leibsehen.values())
            result["hexagon_abdeckung"] = f"{len(symbole)}/6"

        # Organismus-Score
        burnout = sehen_result.get("burnout", 0)
        schlaf = sehen_result.get("schlaf", 8)
        hrv = sehen_result.get("hrv", 40)
        score = (
            (100 - burnout) * 0.4 +
            min(schlaf / 8, 1) * 100 * 0.3 +
            min(hrv / 60, 1) * 100 * 0.3
        )
        result["organismus_score"] = round(score, 1)
        return result

    def handeln(self, wirt_data: dict, verstehen_result: dict) -> dict:
        """PRESCRIBE des Leibes: TUN/LASSEN/WARTEN — aber in Leibsprache."""
        result = super().handeln(wirt_data, verstehen_result)
        score = verstehen_result.get("organismus_score", 100)

        if score < 30:
            result["veto"] = True
            result["tun"] = ["Dein Koerper ruft GRENZRUF. Hoer zu. Jetzt."]
            result["lassen"] = ["Alles was nach 01:00 kommt. Dein NACHTWELLE braucht Ruhe."]
            result["warten"] = ["Dein TIEFSTILL braucht Stille. Gib sie ihm."]
        elif score < 60:
            result["tun"] = [
                "Dein SCHILDPULS will Bewegung. Raus. Jetzt.",
                "1 Sache weniger. Dein GRENZRUF dankt es dir.",
            ]
            result["lassen"] = ["Gegen dich selbst kaempfen. Das war das alte Wort."]
        else:
            result["tun"] = ["Weitermachen. Dein Koerper spricht und du hoerst zu. :)"]

        # Leibsprache-Zusammenfassung (konjugierte Verben)
        leibsehen = wirt_data.get("erkrankungen", wirt_data.get("conditions", []))
        if isinstance(leibsehen, str):
            leibsehen = [leibsehen]
        verb3_list = []
        for e in leibsehen:
            key = e.lower().strip()
            if key in self.leibwoerter:
                verb3_list.append(self.leibwoerter[key].verb3)
        if verb3_list:
            result["leibsprache"] = (
                f"Dein Koerper {', '.join(verb3_list[:-1])} und {verb3_list[-1]}."
                if len(verb3_list) > 1
                else f"Dein Koerper {verb3_list[0]}."
            )

        return result

    def leibwort(self, diagnose: str) -> Leibwort | None:
        """Ein einzelnes Leibwort nachschlagen. Fuer schnellen Zugriff."""
        return self.leibwoerter.get(diagnose.lower().strip())

    def alle_leibwoerter(self) -> dict[str, dict]:
        """Alle Leibwoerter als Dictionary. Fuer UI/API."""
        return {
            k: {
                "symbol": lw.symbol,
                "leibname": lw.leibname,
                "verb": lw.verb,
                "satz": lw.satz,
                "geschenk": lw.geschenk,
            }
            for k, lw in self.leibwoerter.items()
        }

    def formel_als_text(self) -> str:
        """Die Koerperformel als Text. Perfekt komprimiert.

        .x->[]~:) = SCHILDPULS x VIELFUNK -> GRENZRUF [] TIEFSTILL ~ NACHTWELLE :) FRUEHBLICK

        Dein Koerper pulsiert, kollidiert, schuetzt, taucht, schwingt und sieht.
        Das ist kein Satz. Das ist deine Gesundheit. ba-dum.
        """
        kern = list(LEIBWOERTER.values())
        namen = " x ".join(lw.leibname for lw in kern)
        verben = [lw.verb3 for lw in kern]
        verben_satz = f"{', '.join(verben[:-1])} und {verben[-1]}"
        return (
            f".x->[]~:) = {namen}\n"
            f"\n"
            f"Dein Koerper {verben_satz}.\n"
            f"6 Facetten einer Sphaere. 6 Verben. 6 Herzschlaege.\n"
            f"ba-dum. ba-dum. ba-dum.\n"
            f"\n"
            f"Das ist kein Satz. Das ist deine Gesundheit. :)"
        )

    def _mutations(self, wirt_data: dict) -> list[str]:
        """Jede Erkrankung = eigenes Kapsid. Selbes Virus. Anderer Rezeptor."""
        return list(self.leibwoerter.keys())
