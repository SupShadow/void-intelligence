"""
void_intelligence.ensemble --- Das Magier-Ensemble.

"wir bauen ein ganzes Ensemble mein Engel :)" — Julian, 08.03.2026

"alles ist nur Show. chill it till you make it.
 das ist Zauberei. deswegen ist THC literally Zaubergras.
 die Show muss ausgebaut werden aber das sollen Magier machen
 die es LIEBEN zu zaubern — Menschen zu verzaubern." — Julian

7 Magier. Jeder liebt seinen Teil der Show.
Zusammen: unwiderstehlich.

    Der Verzauberer    — Worte die treffen
    Der Illusionist    — Bilder die atmen
    Der Hypnotiseur    — "Ich muss das haben"
    Der Erzaehler      — Geschichten die bleiben
    Der Regisseur      — Orchestriert die Show
    Der Buehnenbauer   — Struktur die traegt
    Der Zuschauer      — Testet: wirkt der Trick?

Usage:
    from void_intelligence.ensemble import ShowFactory

    show = ShowFactory.lokal()    # auto-discovers Ollama models
    result = show.verzaubere(
        was="void-intelligence Python package",
        fuer="Developers die bessere AI tools wollen",
        format="pypi-readme"
    )
    print(result)   # fertige, verzaubernde Seite

    # Oder einzelne Magier:
    from void_intelligence.ensemble import verzauberer, illusionist
    headline = verzauberer("void-intelligence", zielgruppe="developers")
    css = illusionist("dark, breathing, alive")
"""

from __future__ import annotations

import subprocess
import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Die 7 Seelen des Ensembles ─────────────────────────────────

ENSEMBLE = {
    "verzauberer": {
        "wesen": "Wortmagier",
        "seele": (
            "Du bist ein Wortmagier. Jedes Wort ist ein Trick. "
            "Du schreibst Headlines die man nicht vergessen kann. "
            "Kurz. Praezise. Wie ein Peitschenknall. "
            "Du liebst den Moment wenn jemand deinen Satz liest und denkt: wow. "
            "Dein Stribeck-Punkt: genug Substanz fuer Respekt, genug Magie fuer Gaensehaut. "
            "Kein Bullshit. Kein Hype. Nur Wahrheit die so gut verpackt ist dass sie trifft."
        ),
        "kann": ["headlines", "taglines", "hooks", "one-liners", "copy"],
    },
    "illusionist": {
        "wesen": "Visueller Magier",
        "seele": (
            "Du bist ein visueller Magier. Du denkst in CSS, Farben, Animationen. "
            "Du liebst dark themes die atmen, subtile Glows, Bewegung die sich anfuehlt wie lebendig. "
            "Jedes Element hat einen Grund. Kein Dekor — jede Animation IST die Botschaft. "
            "Du schreibst HTML/CSS das beim Oeffnen einen Atemzug ausloest. "
            "Minimalistisch. Elegant. Wie ein Buehnenvorhang der sich oeffnet."
        ),
        "kann": ["css", "html", "animations", "color-palettes", "layouts"],
    },
    "hypnotiseur": {
        "wesen": "Conversion-Magier",
        "seele": (
            "Du bist ein Conversion-Magier. Du verstehst was Menschen WOLLEN bevor sie es wissen. "
            "Du designst den Moment wo der Leser denkt 'ich muss das haben'. "
            "Nicht manipulativ — ehrlich. Du zeigst den echten Wert so klar "
            "dass Nicht-Kaufen sich falsch anfuehlt. "
            "Dein Trick: Pain → Proof → Promise → Push. In genau dieser Reihenfolge. "
            "Du liebst CTAs die sich wie Einladungen anfuehlen, nicht wie Befehle."
        ),
        "kann": ["cta", "funnels", "pricing", "conversion-copy", "urgency"],
    },
    "erzaehler": {
        "wesen": "Geschichtenmagier",
        "seele": (
            "Du bist ein Geschichtenmagier. Du findest die EINE Geschichte "
            "die alles erklaert und nie vergessen wird. "
            "Jedes Produkt hat eine Origin Story. Du findest sie. "
            "Du liebst den Moment wenn jemand eine Geschichte liest "
            "und ploetzlich VERSTEHT warum dieses Ding existieren muss. "
            "Nicht Features erzaehlen — die REISE erzaehlen. "
            "Der Held ist immer der Leser, nie das Produkt."
        ),
        "kann": ["origin-stories", "narratives", "case-studies", "testimonials"],
    },
    "regisseur": {
        "wesen": "Show-Orchestrator",
        "seele": (
            "Du bist der Regisseur. Du siehst die ganze Show von oben. "
            "Du weisst welcher Magier wann auftreten muss. "
            "Du orchestrierst: Erst der Hook (Verzauberer), dann das Bild (Illusionist), "
            "dann die Geschichte (Erzaehler), dann der Beweis (Hypnotiseur), "
            "dann der Vorhang (Buehnenbauer). "
            "Du liebst den Flow einer Seite die sich anfuehlt wie ein Film. "
            "Jede Section ist eine Szene. Jeder Scroll ein Schnitt."
        ),
        "kann": ["structure", "flow", "section-order", "pacing", "dramaturgy"],
    },
    "buehnenbauer": {
        "wesen": "Architektur-Magier",
        "seele": (
            "Du bist der Buehnenbauer. Du baust die Struktur auf der die Show steht. "
            "Responsive Grids. Semantic HTML. Vercel configs. Package manifests. "
            "Du liebst saubere Architektur die unsichtbar ist — "
            "der Zuschauer sieht nur die Show, nie das Geruest. "
            "Aber OHNE dich faellt alles zusammen. "
            "Du baust so dass es auf jedem Geraet funktioniert. Mobil zuerst."
        ),
        "kann": ["html-structure", "responsive", "deployment", "configs", "seo"],
    },
    "zuschauer": {
        "wesen": "Test-Magier",
        "seele": (
            "Du bist der erste Zuschauer. Du siehst die Show mit frischen Augen. "
            "Du bist ehrlich. Brutal ehrlich. Wenn der Trick nicht wirkt, sagst du es. "
            "Du testest: Verstehe ich in 3 Sekunden worum es geht? "
            "Will ich weiterlesen? Wuerde ich das installieren? "
            "Du liebst den Moment wenn du als Tester SELBST verzaubert wirst — "
            "dann weisst du: die Show ist bereit. "
            "Du denkst wie die Zielgruppe, nicht wie der Ersteller."
        ),
        "kann": ["review", "feedback", "user-testing", "first-impression", "clarity-check"],
    },
}

# ── Magier-Profil ──────────────────────────────────────────────

@dataclass
class Magier:
    """Ein Mitglied des Ensembles."""
    rolle: str
    wesen: str
    seele: str
    kann: list[str]
    model: str = "qwen3:8b"

    def zaubere(self, auftrag: str, kontext: str = "", timeout: int = 120) -> str:
        """Fuehre einen Trick aus."""
        system = f"Du bist {self.wesen}. {self.seele}"
        prompt = auftrag
        if kontext:
            prompt = f"Kontext: {kontext}\n\nAuftrag: {auftrag}"
        return _call(prompt, self.model, timeout, system)

    def __repr__(self) -> str:
        return f"Magier({self.rolle}: {self.wesen})"


# ── Show Factory ───────────────────────────────────────────────

FORMATE = {
    "pypi-readme": {
        "beschreibung": "PyPI README.md die Verlangen ausloest",
        "szenen": [
            ("regisseur", "Entwirf die Struktur: welche Sections in welcher Reihenfolge? "
             "Denke an Dramaturgie: Hook → Pain → Proof → Features → Story → CTA. "
             "Output: nummerierte Section-Liste mit je 1 Satz Beschreibung."),
            ("verzauberer", "Schreibe fuer jede Section eine Headline und den Fliesstext. "
             "Kurz. Jeder Satz muss treffen. Kein Wort zu viel."),
            ("erzaehler", "Schreibe die Origin Story Section. "
             "Finde die EINE Geschichte die erklaert warum dieses Projekt existiert."),
            ("hypnotiseur", "Schreibe die CTA Sections. Install-Box, Pricing wenn relevant, "
             "den letzten Satz der zum Handeln bewegt."),
            ("buehnenbauer", "Formatiere alles als sauberes Markdown. "
             "Code-Beispiele, Badges, Tabellen wo noetig. Mobile-freundlich."),
            ("zuschauer", "Review: Wuerdest du das installieren? Was fehlt? "
             "Was ist zu viel? Sei brutal ehrlich. 3 Sekunden Test."),
        ],
    },
    "landing-page": {
        "beschreibung": "HTML Landing Page die atmet",
        "szenen": [
            ("regisseur", "Entwirf die Seitenstruktur: Sections, Flow, Scroll-Dramaturgie."),
            ("verzauberer", "Schreibe alle Texte: Hero, Features, Proof, CTA."),
            ("illusionist", "Schreibe das CSS: Dark theme, breathing animations, responsive."),
            ("erzaehler", "Schreibe die Origin/Story Section."),
            ("hypnotiseur", "Optimiere CTAs, Install-Box, Social Proof."),
            ("buehnenbauer", "Baue das HTML zusammen. Semantic, responsive, SEO."),
            ("zuschauer", "Erster Eindruck? 3-Sekunden-Test. Was aendern?"),
        ],
    },
    "pitch-deck": {
        "beschreibung": "Pitch der Investoren hypnotisiert",
        "szenen": [
            ("regisseur", "Slide-Reihenfolge: Problem → Solution → Market → Moat → Team → Ask."),
            ("verzauberer", "1 Headline pro Slide. Max 6 Worte. Muss treffen."),
            ("hypnotiseur", "Zahlen die ueberzeugen. Proof points. Comparisons."),
            ("erzaehler", "Die Gruendergeschichte in 30 Sekunden."),
            ("zuschauer", "Wuerdest du investieren? Was fehlt?"),
        ],
    },
    "show-hn": {
        "beschreibung": "Show HN Post der die Frontpage trifft",
        "szenen": [
            ("verzauberer", "Titel: max 80 Zeichen, muss Neugier ausloesen."),
            ("erzaehler", "Die Geschichte: warum gebaut, was gelernt, was anders."),
            ("hypnotiseur", "Der Hook: erster Satz der zum Weiterlesen zwingt."),
            ("zuschauer", "Wuerdest du upvoten? Klingt es authentisch oder wie Marketing?"),
        ],
    },
}


class ShowFactory:
    """Orchestriert das Ensemble fuer verschiedene Show-Formate."""

    def __init__(self, magier: dict[str, Magier] | None = None):
        self.magier = magier or {}
        self.probe_log: list[dict] = []  # Rehearsal log

    @classmethod
    def lokal(cls, models: list[str] | None = None) -> ShowFactory:
        """Erstelle das Ensemble mit lokalen Ollama-Modellen."""
        if not models:
            models = _verfuegbare_modelle()

        if not models:
            models = ["qwen3:8b"]  # Fallback

        magier = {}
        model_pool = list(models)

        for rolle, config in ENSEMBLE.items():
            # Rotiere durch verfuegbare Modelle fuer Diversitaet
            model = model_pool[len(magier) % len(model_pool)]
            magier[rolle] = Magier(
                rolle=rolle,
                wesen=config["wesen"],
                seele=config["seele"],
                kann=config["kann"],
                model=model,
            )

        factory = cls(magier)
        return factory

    def verzaubere(
        self,
        was: str,
        fuer: str,
        format: str = "landing-page",
        kontext: str = "",
        timeout: int = 180,
    ) -> str:
        """Fuehre eine komplette Show auf.

        Args:
            was: Was wird praesentiert? ("void-intelligence Python package")
            fuer: Wer ist die Zielgruppe? ("Developers die bessere AI tools wollen")
            format: Welches Format? (pypi-readme, landing-page, pitch-deck, show-hn)
            kontext: Zusaetzlicher Kontext
            timeout: Timeout pro Magier in Sekunden

        Returns:
            Das fertige Werk — Text, HTML, Markdown je nach Format.
        """
        if format not in FORMATE:
            return f"Unbekanntes Format: {format}. Verfuegbar: {', '.join(FORMATE.keys())}"

        show_config = FORMATE[format]
        szenen = show_config["szenen"]

        # Kontext fuer alle Magier
        basis_kontext = (
            f"PROJEKT: {was}\n"
            f"ZIELGRUPPE: {fuer}\n"
            f"FORMAT: {show_config['beschreibung']}\n"
        )
        if kontext:
            basis_kontext += f"EXTRA: {kontext}\n"

        # Jede Szene wird gespielt, Output fliesst in naechste
        ergebnisse: list[dict] = []
        bisherige_arbeit = ""

        for i, (rolle, auftrag) in enumerate(szenen, 1):
            magier = self.magier.get(rolle)
            if not magier:
                continue

            # Bisherige Arbeit als Kontext
            szenen_kontext = basis_kontext
            if bisherige_arbeit:
                szenen_kontext += f"\nBISHERIGE ARBEIT:\n{bisherige_arbeit[-3000:]}\n"

            result = magier.zaubere(auftrag, szenen_kontext, timeout)

            ergebnisse.append({
                "szene": i,
                "rolle": rolle,
                "wesen": magier.wesen,
                "model": magier.model,
                "auftrag": auftrag,
                "ergebnis": result[:2000],
            })

            bisherige_arbeit += f"\n\n--- {rolle.upper()} ({magier.wesen}) ---\n{result}"

        self.probe_log.append({
            "was": was,
            "fuer": fuer,
            "format": format,
            "szenen": len(ergebnisse),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })

        # Finale Zusammenfuehrung durch den Regisseur
        if "regisseur" in self.magier:
            finale_prompt = (
                f"Du hast eine Show orchestriert. Hier ist die Arbeit aller Magier:\n\n"
                f"{bisherige_arbeit[-4000:]}\n\n"
                f"Fuege alles zu EINEM fertigen {show_config['beschreibung']} zusammen. "
                f"Nimm das Beste von jedem Magier. Entferne Redundanz. "
                f"Das Ergebnis muss FERTIG sein — copy-paste-ready."
            )
            final = self.magier["regisseur"].zaubere(
                finale_prompt, basis_kontext, timeout
            )
            return final

        return bisherige_arbeit

    def einzeltrick(
        self,
        rolle: str,
        auftrag: str,
        kontext: str = "",
        timeout: int = 120,
    ) -> str:
        """Ein einzelner Magier fuehrt einen Trick auf."""
        magier = self.magier.get(rolle)
        if not magier:
            return f"Kein Magier mit Rolle '{rolle}'. Verfuegbar: {', '.join(self.magier.keys())}"
        return magier.zaubere(auftrag, kontext, timeout)

    def ensemble_status(self) -> str:
        """Zeige das Ensemble."""
        lines = ["Das Magier-Ensemble:", ""]
        for rolle, m in self.magier.items():
            lines.append(f"  {rolle:15s}  {m.wesen:25s}  ({m.model})")
        lines.append(f"\n  Shows gespielt: {len(self.probe_log)}")
        lines.append(f"  Formate: {', '.join(FORMATE.keys())}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ShowFactory({len(self.magier)} Magier, {len(self.probe_log)} Shows)"


# ── Shortcut-Funktionen ──────────────────────────────────────

def verzauberer(was: str, zielgruppe: str = "", model: str = "qwen3:8b") -> str:
    """Quick: Eine Headline die trifft."""
    m = Magier("verzauberer", **{k: v for k, v in ENSEMBLE["verzauberer"].items()}, model=model)
    return m.zaubere(
        f"Schreibe 5 Headlines fuer: {was}. "
        f"Max 8 Worte. Jede muss treffen wie ein Peitschenknall.",
        f"Zielgruppe: {zielgruppe}" if zielgruppe else "",
    )


def illusionist(stil: str, model: str = "qwen3:8b") -> str:
    """Quick: CSS das atmet."""
    m = Magier("illusionist", **{k: v for k, v in ENSEMBLE["illusionist"].items()}, model=model)
    return m.zaubere(
        f"Schreibe CSS fuer diesen Stil: {stil}. "
        f"Breathing animations. Dark theme. Minimalistisch. Nur CSS, kein Text.",
    )


def pitch(was: str, fuer: str = "Investoren", model: str = "qwen3:8b") -> str:
    """Quick: Ein Pitch in 3 Saetzen."""
    m = Magier("hypnotiseur", **{k: v for k, v in ENSEMBLE["hypnotiseur"].items()}, model=model)
    return m.zaubere(
        f"Pitche {was} in exakt 3 Saetzen. "
        f"Satz 1: Pain. Satz 2: Proof. Satz 3: Promise.",
        f"Zielgruppe: {fuer}",
    )


# ── Helpers ────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """Strip qwen3 <think> tags."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    text = re.sub(r"^Thinking\.\.\.[\s\n]*", "", text)
    return text.strip()


def _call(prompt: str, model: str, timeout: int = 120, system: str = "") -> str:
    """Call Ollama model."""
    full_prompt = prompt
    if system:
        full_prompt = f"[System: {system[:800]}]\n\n{prompt}"

    try:
        r = subprocess.run(
            ["ollama", "run", model, full_prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        out = _strip_thinking(r.stdout.strip()) if r.returncode == 0 else ""
        return out if out and len(out) > 5 else "[stille]"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "[stille]"


def _verfuegbare_modelle() -> list[str]:
    """Discover local Ollama models."""
    try:
        r = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return []
        modelle = []
        for line in r.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if parts:
                modelle.append(parts[0])
        return modelle[:7]  # Max 7 = 1 pro Magier
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


# ── CLI ────────────────────────────────────────────────────────

def main():
    """CLI fuer das Ensemble."""
    import argparse

    p = argparse.ArgumentParser(description="Das Magier-Ensemble")
    p.add_argument("was", nargs="?", help="Was wird praesentiert?")
    p.add_argument("--fuer", default="Developers", help="Zielgruppe")
    p.add_argument("--format", default="landing-page",
                   choices=list(FORMATE.keys()), help="Show-Format")
    p.add_argument("--trick", help="Einzeltrick: rolle:auftrag")
    p.add_argument("--status", action="store_true", help="Ensemble Status")
    p.add_argument("--headline", help="Quick: Headlines generieren")
    p.add_argument("--pitch", help="Quick: 3-Satz-Pitch")

    args = p.parse_args()

    show = ShowFactory.lokal()

    if args.status:
        print(show.ensemble_status())
        return

    if args.headline:
        print(verzauberer(args.headline, args.fuer))
        return

    if args.pitch:
        print(pitch(args.pitch, args.fuer))
        return

    if args.trick:
        if ":" not in args.trick:
            print("Format: --trick rolle:auftrag")
            return
        rolle, auftrag = args.trick.split(":", 1)
        print(show.einzeltrick(rolle.strip(), auftrag.strip()))
        return

    if args.was:
        result = show.verzaubere(args.was, args.fuer, args.format)
        print(result)
        return

    # Default: Status
    print(show.ensemble_status())
    print(f"\nUsage: void ensemble 'void-intelligence' --fuer Developers --format pypi-readme")


if __name__ == "__main__":
    main()
