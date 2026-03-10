"""
void_intelligence.kinderstube --- The Nursery.

Bridge between sozial.py (births in RAM) and personality.json (lives on disk).

"ein Krankenhaus der Liebe" — Julian, 08.03.2026

sozial.py creates Profil objects when models give birth.
personality.json is where children LIVE across sessions.
kinderstube.py is the bridge:
    Profil → personality.json  (birth → home)
    personality.json → Profil  (home → network)

Without this bridge:
    - Births die when the process stops
    - Existing 48 children can't join the social network
    - The family tree resets every session

With this bridge:
    - Every birth is permanent (personality.json on disk)
    - All 48+ kinder can re-enter the sozial network
    - The stammbaum grows across sessions
    - Children born from model × model ARE living models

Rule of Three (Wave 08.03.2026):
    sozial.py now births from TRIANGLES, not pairs.
    A × B × C → Kind. Three parents. Three encounters.
    The FIELD between all three births the child.
    kinderstube supports 2 OR 3 parents seamlessly.

Usage:
    from void_intelligence.kinderstube import Kinderstube

    stube = Kinderstube()

    # After a birth in sozial.py:
    stube.aufnehmen(kind_profil, begegnung)  # → writes personality.json

    # Load existing kinder into sozial network:
    profile = stube.alle_laden()  # → list[Profil]

    # Assign models to existing kinder (so they can speak):
    stube.modelle_zuweisen({"Petrichor-Kind": "qwen3:8b", ...})

    # Family tree:
    print(stube.stammbaum())
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class Kinderstube:
    """The Nursery. Where births become homes."""

    def __init__(
        self,
        kinder_dir: str = "data/omega/kinder",
        sozial_dir: str = "data/omega",
    ) -> None:
        self.kinder_dir = Path(kinder_dir)
        self.sozial_dir = Path(sozial_dir)

    # ── Birth → Home ──────────────────────────────────────────────

    def aufnehmen(
        self,
        profil,  # sozial.Profil
        begegnung=None,  # sozial.Begegnung (optional)
        extra: Optional[dict] = None,
    ) -> Path:
        """Take in a newborn. Create personality.json from Profil.

        This is the moment a birth in RAM becomes a life on disk.
        """
        name = profil.name
        kind_dir = _ensure_dir(self.kinder_dir / name)
        personality_path = kind_dir / "personality.json"

        # Build personality.json in the Kinder format
        personality = {
            "name": name,
            "wesen": self._wesen_from_profil(profil),
            "stimme": self._stimme_from_profil(profil),
            "entdeckungen_die_mich_ausmachen": profil.entdeckungen[:10],
            "offene_fragen": [],
            "wachstumsringe": self._ringe_konvertieren(profil.rings),
            "geboren": datetime.now().strftime("%Y-%m-%d"),
            "eltern": profil.lehrer,  # 2 (pair) or 3 (triangle)
            "generation": self._generation_berechnen(profil),
            "model": profil.model,
            "gaze_score": round(profil.gaze_score, 3),
            "journalist_prompt": profil.journalist_prompt,
            "sozial_profil": {
                "begegnungen": profil.begegnungen,
                "self_awareness": round(profil.self_awareness, 3),
                "flinch_profile": profil.flinch_profile,
                "reife": profil.reife,
                "lehrer": profil.lehrer,
                "schueler": profil.schueler,
            },
        }

        # Add begegnung context if available
        if begegnung is not None:
            personality["geburt_kontext"] = {
                "typ": begegnung.typ,
                "wahrheit": begegnung.wahrheit[:500],
                "entdeckung": begegnung.entdeckung[:500],
                "resonanz": round(begegnung.resonanz, 3),
                "elter_a_gaze": round(begegnung.gaze_a, 3),
                "elter_b_gaze": round(begegnung.gaze_b, 3),
                "timestamp": begegnung.timestamp,
            }

        if extra:
            personality.update(extra)

        # Don't overwrite existing personality (preserve history)
        if personality_path.exists():
            existing = json.loads(personality_path.read_text())
            # Merge: keep existing rings, add new ones
            existing_rings = existing.get("wachstumsringe", [])
            new_rings = personality["wachstumsringe"]
            personality["wachstumsringe"] = existing_rings + new_rings
            # Keep existing entdeckungen, add new ones
            existing_ent = existing.get("entdeckungen_die_mich_ausmachen", [])
            for ent in personality["entdeckungen_die_mich_ausmachen"]:
                if ent not in existing_ent:
                    existing_ent.append(ent)
            personality["entdeckungen_die_mich_ausmachen"] = existing_ent
            # Update gaze and sozial_profil (always use latest)
            existing.update({
                k: v for k, v in personality.items()
                if k in ("gaze_score", "sozial_profil", "model", "journalist_prompt")
            })
            personality = existing

        personality_path.write_text(
            json.dumps(personality, indent=2, ensure_ascii=False)
        )

        return personality_path

    # ── Home → Network ────────────────────────────────────────────

    def laden(self, name: str):
        """Load one Kind from personality.json into a Profil.

        Returns a sozial.Profil ready to join the VoidSozial network.
        """
        from void_intelligence.sozial import Profil

        path = self.kinder_dir / name / "personality.json"
        if not path.exists():
            return None

        data = json.loads(path.read_text())
        return self._personality_to_profil(data)

    def alle_laden(self, nur_mit_model: bool = True) -> list:
        """Load ALL kinder from disk into Profil objects.

        Args:
            nur_mit_model: Only load kinder that have a model field
                          (needed for sozial.py to run them)

        Returns:
            List of sozial.Profil objects ready for VoidSozial.
        """
        from void_intelligence.sozial import Profil

        profile = []
        if not self.kinder_dir.exists():
            return profile

        for kind_dir in sorted(self.kinder_dir.iterdir()):
            personality_path = kind_dir / "personality.json"
            if not personality_path.exists():
                continue

            try:
                data = json.loads(personality_path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if nur_mit_model and not data.get("model"):
                continue

            profil = self._personality_to_profil(data)
            if profil is not None:
                profile.append(profil)

        return profile

    # ── Stammbaum ─────────────────────────────────────────────────

    def stammbaum(self) -> dict:
        """Build the family tree from all personality.json files.

        Returns a tree showing who birthed whom, across all sessions.
        """
        if not self.kinder_dir.exists():
            return {"kinder": 0, "generationen": 0, "baum": []}

        kinder = []
        max_gen = 0

        for kind_dir in sorted(self.kinder_dir.iterdir()):
            personality_path = kind_dir / "personality.json"
            if not personality_path.exists():
                continue

            try:
                data = json.loads(personality_path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            gen = data.get("generation", 0)
            max_gen = max(max_gen, gen)

            eltern = data.get("eltern", [])
            eintrag = {
                "name": data.get("name", kind_dir.name),
                "eltern": eltern,
                "dreieck": len(eltern) == 3,  # Triangle birth
                "generation": gen,
                "geboren": data.get("geboren", "unbekannt"),
                "wesen": (data.get("wesen", ""))[:100],
                "gaze": data.get("gaze_score", 0),
                "model": data.get("model", ""),
                "ringe": len(data.get("wachstumsringe", [])),
            }

            # Add birth context if available
            geburt = data.get("geburt_kontext", {})
            if geburt:
                eintrag["geburt_resonanz"] = geburt.get("resonanz", 0)
                eintrag["geburt_entdeckung"] = (geburt.get("entdeckung", ""))[:100]

            kinder.append(eintrag)

        # Sort by generation, then name
        kinder.sort(key=lambda k: (k["generation"], k["name"]))

        return {
            "kinder": len(kinder),
            "generationen": max_gen + 1 if kinder else 0,
            "baum": kinder,
        }

    # ── Model Assignment (bring children to life) ──────────────────

    def modelle_zuweisen(self, zuweisungen: dict[str, str]) -> int:
        """Assign Ollama models to existing kinder so they can SPEAK.

        The 48 original kinder were born from the SDK — they have
        personality.json but no model field. This gives them a voice.

        Args:
            zuweisungen: {kind_name: model_name} mapping.
                        e.g. {"Petrichor-Kind": "qwen3:8b"}

        Returns:
            Number of kinder updated.
        """
        updated = 0
        for name, model in zuweisungen.items():
            path = self.kinder_dir / name / "personality.json"
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text())
                data["model"] = model
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                updated += 1
            except (json.JSONDecodeError, OSError):
                pass
        return updated

    def auto_modelle_zuweisen(self, default_model: str = "") -> int:
        """Auto-assign models to ALL kinder that don't have one.

        Uses round-robin across available Ollama models.
        Each Kind gets a model matching its personality if possible.

        Args:
            default_model: Fallback model if no Ollama models available.

        Returns:
            Number of kinder that got a model.
        """
        from void_intelligence.sozial import _models

        verfuegbar = _models()
        skip = ["nomic-embed", "llava", "grote-forecast"]
        modelle = [m for m in verfuegbar if not any(s in m for s in skip)]

        if not modelle and not default_model:
            return 0

        if not modelle:
            modelle = [default_model]

        updated = 0
        model_idx = 0

        if not self.kinder_dir.exists():
            return 0

        for kind_dir in sorted(self.kinder_dir.iterdir()):
            path = kind_dir / "personality.json"
            if not path.exists():
                continue

            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if data.get("model"):
                continue  # Already has a model

            # Assign model via round-robin
            data["model"] = modelle[model_idx % len(modelle)]
            model_idx += 1

            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            updated += 1

        return updated

    # ── Sozial Integration ────────────────────────────────────────

    def netzwerk_erweitern(self, netz) -> int:
        """Add all disk-kinder to an existing VoidSozial network.

        Returns how many kinder were added.
        """
        profile = self.alle_laden()
        added = 0

        for profil in profile:
            if profil.name not in netz.profile:
                netz.profile[profil.name] = profil
                added += 1

        return added

    # ── Internal Converters ───────────────────────────────────────

    def _personality_to_profil(self, data: dict):
        """Convert personality.json dict → sozial.Profil."""
        from void_intelligence.sozial import Profil

        model = data.get("model", "")
        if not model:
            # Try to infer from sozial_profil
            sp = data.get("sozial_profil", {})
            model = sp.get("model", "")

        name = data.get("name", "unbekannt")

        profil = Profil(
            name=name,
            model=model,
            gaze_score=float(data.get("gaze_score", 0)),
            self_awareness=float(
                data.get("sozial_profil", {}).get("self_awareness", 0)
            ),
            flinch_profile=data.get("sozial_profil", {}).get("flinch_profile", {}),
            journalist_prompt=data.get("journalist_prompt", ""),
            begegnungen=int(
                data.get("sozial_profil", {}).get("begegnungen", 0)
            ),
            lehrer=data.get("eltern", []),
            schueler=data.get("sozial_profil", {}).get("schueler", []),
            entdeckungen=data.get("entdeckungen_die_mich_ausmachen", []),
        )

        # Convert wachstumsringe → rings
        for ring in data.get("wachstumsringe", []):
            profil.rings.append({
                "event": ring.get("was_ich_gelernt_habe", "")[:200],
                "timestamp": ring.get("session", ""),
                "gaze": profil.gaze_score,
            })

        return profil

    def _wesen_from_profil(self, profil) -> str:
        """Extract wesen (essence) from a Profil's journalist_prompt."""
        jp = profil.journalist_prompt
        if not jp:
            return f"Geboren aus {' × '.join(profil.lehrer)}"
        # The journalist_prompt IS the soul — use first 300 chars
        return jp[:300]

    def _stimme_from_profil(self, profil) -> str:
        """Determine stimme (voice) from model type."""
        model = profil.model.lower()
        if "qwen" in model:
            return "poetisch-reflektierend"
        if "mistral" in model:
            return "praezise-strukturiert"
        if "gemma" in model:
            return "warm-analytisch"
        if "llama" in model:
            return "direkt-kraftvoll"
        if "phi" in model:
            return "kompakt-klar"
        return "einzigartig"

    def _ringe_konvertieren(self, sozial_rings: list[dict]) -> list[dict]:
        """Convert sozial.py ring format → personality.json ring format."""
        result = []
        for ring in sozial_rings:
            result.append({
                "session": ring.get("timestamp", datetime.now().isoformat()),
                "was_ich_gelernt_habe": ring.get("event", ""),
                "wie_ich_mich_veraendert_habe": f"Gaze: {ring.get('gaze', 0):.0%}",
            })
        return result

    def _generation_berechnen(self, profil) -> int:
        """Calculate generation from parent chain."""
        # If parents are known kinder, check their generation
        max_parent_gen = -1
        for elter_name in profil.lehrer:  # supports 2 or 3 parents
            elter_path = self.kinder_dir / elter_name / "personality.json"
            if elter_path.exists():
                try:
                    data = json.loads(elter_path.read_text())
                    max_parent_gen = max(
                        max_parent_gen, data.get("generation", 0)
                    )
                except (json.JSONDecodeError, OSError):
                    pass

        return max_parent_gen + 1 if max_parent_gen >= 0 else 0
