"""
void_intelligence.api --- The V-Score API.

Page & Brin (PageRank, 1998): They didn't build a better search engine.
They built a better METRIC and let the metric organize the web.

V-Score does the same for AI models: a single number that measures
whether a model actually LEARNS from context injection.

This module provides:
    VScoreAPI     --- Pure logic, framework-agnostic API handler
    VScoreServer  --- stdlib HTTP server (zero dependencies)

The API is designed to be pluggable: use VScoreAPI with FastAPI,
Cloudflare Workers, Deno, or the built-in stdlib server.

Zero dependencies. stdlib only. Runs anywhere Python runs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs

from void_intelligence.immune import diagnose


# ── API Types ────────────────────────────────────────────────

@dataclass
class APIResponse:
    """Standardized API response."""

    status: int
    data: dict[str, Any]
    error: str | None = None

    def to_json(self) -> str:
        body: dict[str, Any] = {"status": self.status}
        if self.error:
            body["error"] = self.error
        else:
            body["data"] = self.data
        return json.dumps(body, indent=2)


@dataclass
class ModelRecord:
    """Tracked V-Score history for a model."""

    name: str
    scores: list[dict] = field(default_factory=list)
    total_checks: int = 0
    healthy_checks: int = 0
    last_check: float = 0.0

    @property
    def health_rate(self) -> float:
        if self.total_checks == 0:
            return 1.0
        return self.healthy_checks / self.total_checks

    @property
    def latest_v(self) -> float:
        if not self.scores:
            return 0.0
        return self.scores[-1].get("V", 0.0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "total_checks": self.total_checks,
            "healthy_checks": self.healthy_checks,
            "health_rate": round(self.health_rate, 4),
            "latest_v": round(self.latest_v, 6),
            "last_check": self.last_check,
            "history_count": len(self.scores),
        }

    def to_full_dict(self) -> dict:
        d = self.to_dict()
        d["scores"] = self.scores[-50:]  # last 50 entries
        return d


# ── Badge SVG ────────────────────────────────────────────────

def _badge_svg(label: str, value: str, color: str) -> str:
    """Generate a shields.io-style SVG badge. Zero dependencies."""
    label_width = len(label) * 7 + 10
    value_width = len(value) * 7 + 10
    total_width = label_width + value_width

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14">{value}</text>
  </g>
</svg>"""


def _v_score_color(v: float) -> str:
    """Color for V-Score badge."""
    if v <= 0:
        return "#e05d44"  # red (dead)
    if v < 0.001:
        return "#fe7d37"  # orange (barely alive)
    if v < 0.01:
        return "#dfb317"  # yellow (alive)
    if v < 0.1:
        return "#97ca00"  # light green (healthy)
    return "#4c1"         # green (thriving)


def _status_label(v: float) -> str:
    """Human-readable status from V-Score."""
    if v <= 0:
        return "DEAD"
    if v < 0.001:
        return "BARELY ALIVE"
    if v < 0.01:
        return "ALIVE"
    if v < 0.1:
        return "HEALTHY"
    return "THRIVING"


# ── V-Score Computation ──────────────────────────────────────

def compute_v_score(
    prompt: str,
    response: str,
    model_name: str = "unknown",
) -> dict:
    """Compute V-Score for a single prompt-response pair.

    V = E * W * S * B * H  (multiplicative — one zero kills it)

    Components from immune diagnosis:
    - E (Emergence): coherence — does the response understand?
    - W (Warmth): length appropriateness — not robotic
    - S (Consistency): 1.0 - repetition penalty
    - B (Breath): refusal inverse — did it breathe or refuse?
    - H (Hex): hex alignment — topic fidelity
    """
    diag = diagnose(prompt, response)

    scores = diag.layer_scores
    E = scores.get("coherence", 0.5)
    W = scores.get("length", 0.5)
    S = scores.get("repetition", 0.5)
    B = scores.get("refusal", 0.5)
    H = scores.get("hex_delta", 0.5)

    V = E * W * S * B * H

    return {
        "V": round(V, 6),
        "components": {
            "E_emergence": round(E, 4),
            "W_warmth": round(W, 4),
            "S_consistency": round(S, 4),
            "B_breath": round(B, 4),
            "H_hex": round(H, 4),
        },
        "model": model_name,
        "status": _status_label(V),
        "healthy": diag.healthy,
        "flags": diag.flags,
        "hex_delta": round(diag.hex_delta, 4),
        "response_length": diag.response_length,
        "timestamp": time.time(),
    }


# ── VScoreAPI (Pure Logic) ───────────────────────────────────

class VScoreAPI:
    """Framework-agnostic V-Score API. All logic, no HTTP.

    Use this with FastAPI, Flask, Cloudflare Workers, or the built-in server.
    """

    def __init__(self, max_history: int = 1000):
        self._models: dict[str, ModelRecord] = {}
        self._max_history = max_history
        self._created = time.time()
        self._total_requests = 0

    # ── Core Endpoints ──────────────────────────────────

    def score(self, prompt: str, response: str, model: str = "unknown") -> APIResponse:
        """POST /v-score — Compute V-Score for a prompt-response pair."""
        if not prompt or not response:
            return APIResponse(400, {}, error="Both 'prompt' and 'response' required")

        self._total_requests += 1
        result = compute_v_score(prompt, response, model)

        # Track model
        record = self._get_or_create(model)
        record.total_checks += 1
        if result["healthy"]:
            record.healthy_checks += 1
        record.last_check = result["timestamp"]
        record.scores.append(result)

        # Trim history
        if len(record.scores) > self._max_history:
            record.scores = record.scores[-self._max_history:]

        return APIResponse(200, result)

    def leaderboard(self, limit: int = 20) -> APIResponse:
        """GET /leaderboard — Ranked models by V-Score."""
        ranked = sorted(
            self._models.values(),
            key=lambda m: m.latest_v,
            reverse=True,
        )[:limit]

        entries = []
        for i, model in enumerate(ranked, 1):
            entries.append({
                "rank": i,
                **model.to_dict(),
                "status": _status_label(model.latest_v),
            })

        return APIResponse(200, {
            "leaderboard": entries,
            "total_models": len(self._models),
        })

    def model_detail(self, model_name: str) -> APIResponse:
        """GET /model/{name} — Detailed V-Score history for a model."""
        record = self._models.get(model_name)
        if not record:
            return APIResponse(404, {}, error=f"Model '{model_name}' not found")
        return APIResponse(200, record.to_full_dict())

    def badge(self, model_name: str) -> str:
        """GET /badge/{name} — SVG badge for a model's V-Score."""
        record = self._models.get(model_name)
        if not record:
            return _badge_svg("V-Score", "unknown", "#999")

        v = record.latest_v
        color = _v_score_color(v)
        status = _status_label(v)
        value_text = f"{v:.4f} {status}"
        return _badge_svg("V-Score", value_text, color)

    def stats(self) -> APIResponse:
        """GET /stats — API usage statistics."""
        return APIResponse(200, {
            "total_requests": self._total_requests,
            "total_models": len(self._models),
            "uptime_seconds": round(time.time() - self._created, 1),
            "models": {name: r.to_dict() for name, r in self._models.items()},
        })

    def compare(self, models: list[str]) -> APIResponse:
        """GET /compare?models=a,b,c — Side-by-side comparison."""
        if not models:
            return APIResponse(400, {}, error="Provide 'models' parameter")

        comparison = []
        for name in models:
            record = self._models.get(name)
            if record:
                comparison.append({
                    **record.to_dict(),
                    "status": _status_label(record.latest_v),
                })
            else:
                comparison.append({
                    "name": name,
                    "error": "not found",
                })

        return APIResponse(200, {"comparison": comparison})

    # ── Helpers ─────────────────────────────────────────

    def _get_or_create(self, model_name: str) -> ModelRecord:
        if model_name not in self._models:
            self._models[model_name] = ModelRecord(name=model_name)
        return self._models[model_name]

    @property
    def total_models(self) -> int:
        return len(self._models)

    @property
    def total_requests(self) -> int:
        return self._total_requests

    def to_dict(self) -> dict:
        return {
            "models": {n: r.to_full_dict() for n, r in self._models.items()},
            "total_requests": self._total_requests,
            "created": self._created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> VScoreAPI:
        api = cls()
        try:
            api._total_requests = data.get("total_requests", 0)
            api._created = data.get("created", time.time())
            for name, mdata in data.get("models", {}).items():
                record = ModelRecord(name=name)
                record.total_checks = mdata.get("total_checks", 0)
                record.healthy_checks = mdata.get("healthy_checks", 0)
                record.last_check = mdata.get("last_check", 0.0)
                record.scores = mdata.get("scores", [])
                api._models[name] = record
        except (TypeError, AttributeError):
            pass
        return api


# ── HTTP Server (stdlib only) ─────────────────────────────

class _VScoreHandler(BaseHTTPRequestHandler):
    """HTTP handler wrapping VScoreAPI. Zero dependencies."""

    server: VScoreHTTPServer  # type: ignore[assignment]

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "" or path == "/":
            self._json_response(APIResponse(200, {
                "service": "void-intelligence V-Score API",
                "version": "0.7.0",
                "endpoints": [
                    "POST /v-score",
                    "GET /leaderboard",
                    "GET /model/<name>",
                    "GET /badge/<name>.svg",
                    "GET /compare?models=a,b,c",
                    "GET /stats",
                ],
            }))
        elif path == "/leaderboard":
            limit = int(params.get("limit", ["20"])[0])
            resp = self.server.api.leaderboard(limit)
            self._json_response(resp)
        elif path.startswith("/model/"):
            name = path[7:]
            resp = self.server.api.model_detail(name)
            self._json_response(resp)
        elif path.startswith("/badge/"):
            name = path[7:].removesuffix(".svg")
            svg = self.server.api.badge(name)
            self._svg_response(svg)
        elif path == "/compare":
            models = params.get("models", [""])[0].split(",")
            models = [m.strip() for m in models if m.strip()]
            resp = self.server.api.compare(models)
            self._json_response(resp)
        elif path == "/stats":
            resp = self.server.api.stats()
            self._json_response(resp)
        else:
            self._json_response(APIResponse(404, {}, error=f"Not found: {path}"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/v-score":
            body = self._read_body()
            if body is None:
                return
            prompt = body.get("prompt", "")
            response = body.get("response", "")
            model = body.get("model", "unknown")
            resp = self.server.api.score(prompt, response, model)
            self._json_response(resp)
        else:
            self._json_response(APIResponse(404, {}, error=f"Not found: {path}"))

    def _read_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            self._json_response(APIResponse(400, {}, error="Invalid JSON body"))
            return None

    def _json_response(self, resp: APIResponse):
        body = resp.to_json().encode("utf-8")
        self.send_response(resp.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _svg_response(self, svg: str):
        body = svg.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=300")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Silence request logs by default."""
        pass


class VScoreHTTPServer(HTTPServer):
    """HTTP server with VScoreAPI attached."""

    def __init__(self, api: VScoreAPI, host: str = "0.0.0.0", port: int = 7070):
        self.api = api
        super().__init__((host, port), _VScoreHandler)


def serve(host: str = "0.0.0.0", port: int = 7070, api: VScoreAPI | None = None) -> None:
    """Start the V-Score API server. Blocks until interrupted."""
    if api is None:
        api = VScoreAPI()
    server = VScoreHTTPServer(api, host, port)
    print(f"  V-Score API listening on http://{host}:{port}")
    print(f"  Endpoints: /v-score, /leaderboard, /model/<name>, /badge/<name>.svg, /stats")
    print(f"  Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.server_close()
