"""
void_intelligence.portable --- Universal Export Format.

Wozniak (Apple II, 1977): He didn't make the best computer.
He made computing ACCESSIBLE. VOID should run everywhere.

This module serializes the entire VOID state into a portable JSON format
that can be consumed by any runtime: Python, JavaScript, Rust, Go, WASM.

The format is self-describing: it includes schema version, component
manifests, and all data needed to reconstruct the organism.

Components exported:
    organism   --- Breaths, heartbeats, growth rings
    immune     --- Health rate, flag history
    rings      --- Full ring graph with edges
    swarm      --- Node states and network topology
    api        --- V-Score history and model records
    profiles   --- V-Score profiles
    router     --- Routing decisions and organism state
    pollinator --- Cross-pollination events and endosymbionts

Zero dependencies. Pure stdlib. The export IS the organism.
"""

from __future__ import annotations

import json
import time
from typing import Any


SCHEMA_VERSION = "0.9.0"


def export_organism(
    organism=None,
    router=None,
    api=None,
    swarm_network=None,
    *,
    include: list[str] | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    """Export VOID state to portable JSON format.

    Args:
        organism: OrganismBreather instance
        router: AtemRouter instance
        api: VScoreAPI instance
        swarm_network: SwarmNetwork instance
        include: Component whitelist (None = all)
        compact: Strip timestamps, IDs, and history for minimal size

    Returns:
        Portable dict ready for json.dumps()
    """
    export: dict[str, Any] = {
        "_schema": SCHEMA_VERSION,
        "_exported": time.time(),
        "_format": "void-intelligence-portable",
    }

    should_include = include or [
        "organism", "immune", "rings", "router",
        "api", "swarm", "pollinator", "profiles",
    ]

    if organism and "organism" in should_include:
        export["organism"] = _export_organism(organism, compact)

    if organism and "immune" in should_include:
        export["immune"] = _export_immune(organism, compact)

    if organism and "rings" in should_include:
        export["rings"] = _export_rings(organism, compact)

    if router and "router" in should_include:
        export["router"] = _export_router(router, compact)

    if router and "pollinator" in should_include:
        export["pollinator"] = _export_pollinator(router, compact)

    if api and "api" in should_include:
        export["api"] = _export_api(api, compact)

    if swarm_network and "swarm" in should_include:
        export["swarm"] = _export_swarm(swarm_network, compact)

    if "profiles" in should_include:
        export["profiles"] = _export_profiles(compact)

    # Compute manifest
    components = [k for k in export if not k.startswith("_")]
    export["_manifest"] = {
        "components": components,
        "component_count": len(components),
    }

    return export


def export_json(
    organism=None,
    router=None,
    api=None,
    swarm_network=None,
    **kwargs,
) -> str:
    """Export as JSON string."""
    data = export_organism(organism, router, api, swarm_network, **kwargs)
    indent = None if kwargs.get("compact") else 2
    return json.dumps(data, indent=indent, default=str)


def import_state(data: dict[str, Any]) -> dict[str, Any]:
    """Import portable format back into component states.

    Returns a dict of component names to their reconstructable data.
    Does NOT instantiate objects — that's the caller's job.
    This keeps portable.py dependency-free from other modules.
    """
    schema = data.get("_schema", "0.0.0")
    result: dict[str, Any] = {
        "_schema": schema,
        "_imported": time.time(),
    }

    for key in data:
        if not key.startswith("_"):
            result[key] = data[key]

    return result


def validate(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a portable export. Returns (valid, errors)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return False, ["Root must be a dict"]

    if "_schema" not in data:
        errors.append("Missing _schema field")

    if "_format" not in data:
        errors.append("Missing _format field")
    elif data["_format"] != "void-intelligence-portable":
        errors.append(f"Unknown format: {data['_format']}")

    manifest = data.get("_manifest", {})
    declared = set(manifest.get("components", []))
    actual = {k for k in data if not k.startswith("_")}

    missing = declared - actual
    if missing:
        errors.append(f"Declared but missing: {missing}")

    extra = actual - declared
    if extra:
        errors.append(f"Present but not in manifest: {extra}")

    return len(errors) == 0, errors


# ── Component Exporters ─────────────────────────────────────

def _export_organism(organism, compact: bool) -> dict:
    """Export organism state."""
    vitals = organism.vitals()
    data: dict[str, Any] = {
        "alive": vitals.get("alive", False),
        "breaths": vitals.get("breaths", 0),
        "heartbeats": vitals.get("heartbeats", 0),
        "bpm": vitals.get("bpm", 0),
    }

    # Growth rings
    rings = vitals.get("rings", {})
    data["total_rings"] = rings.get("total", 0)
    data["compressed_rings"] = rings.get("compressed", 0)

    if not compact:
        data["ring_types"] = rings.get("types", {})

    # Last breath classification
    if hasattr(organism, "_last_hex") and organism._last_hex:
        coord = organism._last_hex
        data["last_hex"] = {
            "ruhe_druck": coord.ruhe_druck,
            "stille_resonanz": coord.stille_resonanz,
            "allein_zusammen": coord.allein_zusammen,
            "empfangen_schaffen": coord.empfangen_schaffen,
            "sein_tun": coord.sein_tun,
            "langsam_schnell": coord.langsam_schnell,
        }

    return data


def _export_immune(organism, compact: bool) -> dict:
    """Export immune state."""
    data: dict[str, Any] = {}

    if hasattr(organism, "immune_state"):
        state = organism.immune_state
        data["total_calls"] = state.total_calls
        data["healthy_calls"] = state.healthy_calls
        data["fallback_calls"] = state.fallback_calls
        data["health_rate"] = round(
            state.healthy_calls / max(state.total_calls, 1), 4
        )
        if not compact:
            data["flags_history"] = dict(state.flags_history)
            data["consecutive_failures"] = state.consecutive_failures

    return data


def _export_rings(organism, compact: bool) -> dict:
    """Export ring graph."""
    data: dict[str, Any] = {"nodes": [], "edges": []}

    if hasattr(organism, "graph") and organism.graph:
        graph = organism.graph

        for nid, node in graph.nodes.items():
            entry: dict[str, Any] = {
                "id": nid,
                "content": node.content,
                "ring_type": node.ring_type,
                "keywords": node.keywords,
                "depth": node.depth,
                "compressed": node.compressed,
            }
            if not compact:
                entry["timestamp"] = node.timestamp
            data["nodes"].append(entry)

        if hasattr(graph, "_adjacency"):
            for src, targets in graph._adjacency.items():
                for tgt in targets:
                    edge_info = graph.edges.get((src, tgt))
                    entry = {"source": src, "target": tgt}
                    if edge_info and not compact:
                        entry["label"] = edge_info.label
                        entry["weight"] = edge_info.weight
                    data["edges"].append(entry)

        data["active_count"] = graph.active_count
        data["total_count"] = len(graph.nodes)

    return data


def _export_router(router, compact: bool) -> dict:
    """Export router state."""
    data: dict[str, Any] = {}

    if hasattr(router, "organisms"):
        data["organism_count"] = len(router.organisms)
        data["organisms"] = {}
        for name, org in router.organisms.items():
            v = org.vitals()
            data["organisms"][name] = {
                "breaths": v.get("breaths", 0),
                "rings": v.get("rings", {}).get("total", 0),
                "alive": v.get("alive", False),
            }

    if hasattr(router, "_decision_log") and not compact:
        data["recent_decisions"] = len(router._decision_log)

    return data


def _export_pollinator(router, compact: bool) -> dict:
    """Export cross-pollination state."""
    data: dict[str, Any] = {}

    if hasattr(router, "pollinator") and router.pollinator:
        p = router.pollinator
        if hasattr(p, "events"):
            data["total_transfers"] = len(p.events)
            if not compact and p.events:
                data["last_transfer"] = {
                    "source": p.events[-1].source_model,
                    "target": p.events[-1].target_model,
                    "rings": p.events[-1].ring_count,
                }

    return data


def _export_api(api, compact: bool) -> dict:
    """Export V-Score API state."""
    data: dict[str, Any] = {
        "total_models": api.total_models,
        "total_requests": api.total_requests,
    }

    models = {}
    for name, record in api._models.items():
        entry: dict[str, Any] = {
            "latest_v": round(record.latest_v, 6),
            "health_rate": round(record.health_rate, 4),
            "total_checks": record.total_checks,
        }
        if not compact:
            entry["scores"] = record.scores[-10:]  # last 10
        models[name] = entry

    data["models"] = models
    return data


def _export_swarm(network, compact: bool) -> dict:
    """Export swarm network state."""
    data: dict[str, Any] = {
        "node_count": network.node_count,
        "total_deliveries": network.total_deliveries,
    }

    # Health
    h = network.health()
    data["health"] = h.to_dict()

    # Nodes
    nodes = {}
    for node in network.nodes():
        v = node.vitals()
        entry: dict[str, Any] = {
            "ring_count": v["ring_count"],
            "shared_count": v["shared_count"],
            "neighbors": node.neighbors,
            "sick_models": v["sick_models"],
            "v_scores": v["v_scores"],
        }
        if not compact:
            entry["messages_sent"] = v["messages_sent"]
            entry["messages_received"] = v["messages_received"]
        nodes[v["node_id"]] = entry

    data["nodes"] = nodes
    return data


def _export_profiles(compact: bool) -> dict:
    """Export bundled profiles."""
    from void_intelligence.profiles import BUNDLED_PROFILES

    data: dict[str, Any] = {"count": len(BUNDLED_PROFILES)}

    if not compact:
        profiles = {}
        for name, p in BUNDLED_PROFILES.items():
            profiles[name] = {
                "V": round(p.V, 6),
                "provider": p.provider,
                "is_local": p.is_local,
            }
        data["profiles"] = profiles

    return data


# ── Lite Export (minimal, single-purpose) ────────────────────

def export_lite(organism=None) -> dict[str, Any]:
    """Ultra-minimal export. Just the vitals. < 1KB.

    For edge/IoT/embedded where every byte counts.
    """
    data: dict[str, Any] = {
        "_schema": SCHEMA_VERSION,
        "_format": "void-intelligence-lite",
    }

    if organism:
        v = organism.vitals()
        data["alive"] = v.get("alive", False)
        data["breaths"] = v.get("breaths", 0)
        data["rings"] = v.get("rings", {}).get("total", 0)
        data["bpm"] = v.get("bpm", 0)

    return data
