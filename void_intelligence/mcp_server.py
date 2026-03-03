"""
void_intelligence.mcp_server --- VOID Intelligence Plugin for Claude Code.

Gives Claude Code a living memory. Every session builds growth rings.
The next session is smarter because the previous one lived.

Setup:
    pip install void-intelligence mcp

    # Add to .mcp.json (project or ~/.claude/.mcp.json):
    {
        "mcpServers": {
            "void": {
                "type": "stdio",
                "command": "void",
                "args": ["mcp"]
            }
        }
    }

Tools:
    void_breathe    Record a learning cycle (inhale prompt, exhale response)
    void_score      Score any prompt-response pair (V = E x W x S x B x H)
    void_vitals     Organism health: rings, V-Score, pulse
    void_rings      Search what the organism has learned
    void_classify   6-axis intent classification (<0.02ms, no LLM)
    void_immune     5-layer quality check (Swiss Cheese Model)

Persistence:
    .void/organism.json    Serialized organism state
    .void/rings.jsonl      Append-only learning log
    .void/.gitignore       Keeps VOID state out of git
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from void_intelligence.organism import OrganismBreather
from void_intelligence.edge import (
    score as edge_score,
    diagnose as edge_diagnose,
    classify as edge_classify,
)

logger = logging.getLogger("void-mcp")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(asctime)s [VOID] %(message)s"))
logger.addHandler(_handler)


# ── Persistence ─────────────────────────────────────────────────

VOID_DIR = Path.cwd() / ".void"
ORGANISM_FILE = VOID_DIR / "organism.json"
RINGS_FILE = VOID_DIR / "rings.jsonl"


def _ensure_dir():
    """Create .void/ with .gitignore."""
    VOID_DIR.mkdir(exist_ok=True)
    gitignore = VOID_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")


def _load_organism() -> OrganismBreather:
    """Load organism from disk or create fresh."""
    if ORGANISM_FILE.exists():
        try:
            data = json.loads(ORGANISM_FILE.read_text())
            org = OrganismBreather.from_dict(data)
            logger.info(
                f"Organism loaded: {org.rings.count} rings, "
                f"{org._breath_count} breaths"
            )
            return org
        except Exception as e:
            logger.warning(f"Could not load organism, starting fresh: {e}")
    return OrganismBreather()


def _save_organism(organism: OrganismBreather):
    """Persist organism to disk."""
    _ensure_dir()
    ORGANISM_FILE.write_text(
        json.dumps(organism.to_dict(), indent=2, ensure_ascii=False)
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_ring(prompt: str, response: str, learnings: list[str], v: dict):
    """Append a growth ring to the log."""
    _ensure_dir()
    entry = {
        "ts": _now_iso(),
        "prompt": prompt[:300],
        "response": response[:300],
        "learnings": learnings,
        "v_score": v.get("V", 0),
        "status": v.get("status", "UNKNOWN"),
    }
    with open(RINGS_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Provider ────────────────────────────────────────────────────

class VoidProvider:
    """Business logic for VOID MCP tools."""

    def __init__(self):
        self._organism: OrganismBreather | None = None

    @property
    def organism(self) -> OrganismBreather:
        if self._organism is None:
            self._organism = _load_organism()
        return self._organism

    def breathe(
        self,
        prompt: str,
        response: str,
        learnings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Full breathing cycle. Inhale, exhale, grow, persist."""
        learnings = learnings or []

        self.organism.inhale(prompt)
        exhale = self.organism.exhale(response, learnings=learnings)

        v = edge_score(prompt, response)

        _save_organism(self.organism)
        _append_ring(prompt, response, learnings, v)

        return {
            "success": True,
            "v_score": v,
            "rings_total": exhale.get("total_rings", 0),
            "new_rings": exhale.get("new_rings", []),
            "learnings_recorded": len(learnings),
        }

    def score(self, prompt: str, response: str) -> dict[str, Any]:
        """Score without recording."""
        return {
            "success": True,
            "v_score": edge_score(prompt, response),
        }

    def vitals(self) -> dict[str, Any]:
        """Organism health check."""
        v = self.organism.vitals()

        ring_count = 0
        recent: list[dict] = []
        if RINGS_FILE.exists():
            lines = [l for l in RINGS_FILE.read_text().strip().split("\n") if l.strip()]
            ring_count = len(lines)
            for line in reversed(lines[-5:]):
                try:
                    recent.append(json.loads(line))
                except Exception:
                    pass

        return {
            "success": True,
            "alive": v.get("alive", False),
            "breaths": v.get("breaths", 0),
            "heartbeats": v.get("heartbeats", 0),
            "bpm": v.get("bpm", 0),
            "rings": v.get("rings", {}),
            "rings_persisted": ring_count,
            "uptime_sec": v.get("uptime_sec", 0),
            "recent_learnings": recent,
            "organism_file": str(ORGANISM_FILE),
        }

    def rings(self, query: str = "", limit: int = 20) -> dict[str, Any]:
        """Search growth rings."""
        results: list[dict] = []
        if RINGS_FILE.exists():
            for line in RINGS_FILE.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if not query or query.lower() in json.dumps(entry).lower():
                        results.append(entry)
                except Exception:
                    pass

        results = list(reversed(results[-limit:]))

        return {
            "success": True,
            "total": len(results),
            "query": query or "(all)",
            "rings": results,
        }

    def classify(self, text: str) -> dict[str, Any]:
        """6-axis HexBreath classification."""
        return {
            "success": True,
            "axes": edge_classify(text),
            "text_preview": text[:100],
        }

    def immune_check(self, prompt: str, response: str) -> dict[str, Any]:
        """5-layer immune system check."""
        d = edge_diagnose(prompt, response)
        return {
            "success": True,
            "healthy": d.get("healthy", False),
            "severity": d.get("severity", "unknown"),
            "flags": d.get("flags", []),
            "layer_scores": d.get("layer_scores", {}),
            "hex_delta": d.get("hex_delta", 0),
        }


# ── MCP Server ──────────────────────────────────────────────────

def create_server():
    """Create and configure the MCP server. Returns (app, stdio_server)."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except ImportError:
        print(
            "Error: 'mcp' package required.\n"
            "Install with: pip install mcp\n"
            "Or: pip install void-intelligence[mcp]",
            file=sys.stderr,
        )
        sys.exit(1)

    app = Server("void-intelligence")
    provider = VoidProvider()

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="void_breathe",
                description=(
                    "Record a learning cycle. Inhale a prompt, exhale a response, "
                    "grow a ring. The organism remembers across sessions. "
                    "Use after interactions where something was LEARNED."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt/question that was asked",
                        },
                        "response": {
                            "type": "string",
                            "description": "The response that was given",
                        },
                        "learnings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "What was learned (e.g., 'user prefers TypeScript', "
                                "'this API needs auth headers', 'tests use pytest not unittest')"
                            ),
                            "default": [],
                        },
                    },
                    "required": ["prompt", "response"],
                },
            ),
            Tool(
                name="void_score",
                description=(
                    "Score a prompt-response pair. V = E x W x S x B x H "
                    "(multiplicative — one zero kills it). "
                    "Read-only, no side effects."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to score",
                        },
                        "response": {
                            "type": "string",
                            "description": "The response to score",
                        },
                    },
                    "required": ["prompt", "response"],
                },
            ),
            Tool(
                name="void_vitals",
                description=(
                    "Organism health. Shows rings, breaths, pulse, recent learnings. "
                    "Use at session start to see what the organism already knows."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="void_rings",
                description=(
                    "Search growth rings — accumulated experience from past sessions. "
                    "Each ring records what was learned. "
                    "Use to recall patterns, preferences, and project knowledge."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term (empty = all recent)",
                            "default": "",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max rings to return",
                            "default": 20,
                        },
                    },
                },
            ),
            Tool(
                name="void_classify",
                description=(
                    "6-axis HexBreath classification. Maps any text to 6 dimensions: "
                    "calm/pressure, silence/resonance, alone/together, "
                    "receive/create, being/doing, slow/fast. "
                    "<0.02ms, no LLM needed."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to classify",
                        },
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="void_immune",
                description=(
                    "5-layer immune check (Swiss Cheese Model). "
                    "Layers: HexDelta, Length, Refusal, Repetition, Coherence. "
                    "A failure only gets through if ALL layers have aligned holes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The original prompt",
                        },
                        "response": {
                            "type": "string",
                            "description": "The response to check",
                        },
                    },
                    "required": ["prompt", "response"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "void_breathe":
                result = await asyncio.to_thread(
                    provider.breathe,
                    prompt=arguments["prompt"],
                    response=arguments["response"],
                    learnings=arguments.get("learnings", []),
                )
            elif name == "void_score":
                result = await asyncio.to_thread(
                    provider.score,
                    prompt=arguments["prompt"],
                    response=arguments["response"],
                )
            elif name == "void_vitals":
                result = await asyncio.to_thread(provider.vitals)
            elif name == "void_rings":
                result = await asyncio.to_thread(
                    provider.rings,
                    query=arguments.get("query", ""),
                    limit=arguments.get("limit", 20),
                )
            elif name == "void_classify":
                result = await asyncio.to_thread(
                    provider.classify,
                    text=arguments["text"],
                )
            elif name == "void_immune":
                result = await asyncio.to_thread(
                    provider.immune_check,
                    prompt=arguments["prompt"],
                    response=arguments["response"],
                )
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False),
            )]
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }, indent=2),
            )]

    return app, stdio_server


async def run_server():
    """Start the VOID Intelligence MCP server."""
    app, stdio = create_server()
    logger.info(f"VOID Intelligence MCP Server starting (cwd: {Path.cwd()})")
    logger.info(f"Organism: {ORGANISM_FILE}")
    async with stdio() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main():
    """Entry point for ``void mcp``."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
