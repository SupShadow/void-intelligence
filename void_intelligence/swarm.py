"""
void_intelligence.swarm --- The Swarm Network.

Deborah Gordon (Ant Colony Intelligence, 1999): No ant knows the colony's plan.
Intelligence emerges from simple local rules applied at scale.

A swarm of VOID organisms, each learning locally, creates collective
intelligence that no single instance has.

Components:
    SwarmNode      --- A single VOID instance in the mesh
    SwarmMessage   --- A gossip message between nodes
    SwarmNetwork   --- The mesh coordinator
    SwarmHealth    --- Collective health across all nodes

The industry runs models in isolation.
We run them as a colony.

Zero dependencies. No networking library. Just message passing.
The transport layer (TCP, HTTP, file, pipe) is pluggable.
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from void_intelligence.ring_graph import RingGraph


# ── Swarm Message ──────────────────────────────────────────────

@dataclass
class SwarmMessage:
    """A gossip message between swarm nodes.

    Like ant pheromones: simple, local, stateless.
    Each message carries one piece of information.
    Intelligence emerges from many messages.

    Message types:
        ring_share    --- "I learned this" (ring content + metadata)
        immune_alert  --- "This model is sick" (model name + flags)
        heartbeat     --- "I'm alive" (node vitals)
        ring_request  --- "Do you know about X?" (keyword query)
        ring_response --- "Here's what I know about X" (ring list)
        score_update  --- "Model X scored V" (V-Score update)
    """

    msg_type: str
    sender: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    msg_id: str = ""
    ttl: int = 3  # max hops before message dies

    def __post_init__(self):
        if not self.msg_id:
            raw = f"{self.sender}:{self.msg_type}:{self.timestamp}"
            self.msg_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "sender": self.sender,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "msg_id": self.msg_id,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SwarmMessage:
        return cls(
            msg_type=data["msg_type"],
            sender=data["sender"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time()),
            msg_id=data.get("msg_id", ""),
            ttl=data.get("ttl", 3),
        )


# ── Swarm Health ───────────────────────────────────────────────

@dataclass
class SwarmHealth:
    """Collective health across the swarm.

    Colony health > sum of individual health.
    That's emergence. That's the Gordon principle.
    """

    total_nodes: int = 0
    alive_nodes: int = 0
    total_rings: int = 0
    shared_rings: int = 0
    immune_alerts: int = 0
    sick_models: list[str] = field(default_factory=list)
    collective_v: float = 0.0  # average V-Score across swarm

    @property
    def colony_health(self) -> float:
        """Colony health score 0-1. Alive ratio weighted by ring sharing."""
        if self.total_nodes == 0:
            return 0.0
        alive_ratio = self.alive_nodes / self.total_nodes
        share_bonus = min(1.0, self.shared_rings / max(self.total_rings, 1) * 2)
        return min(1.0, alive_ratio * 0.7 + share_bonus * 0.3)

    def to_dict(self) -> dict:
        return {
            "total_nodes": self.total_nodes,
            "alive_nodes": self.alive_nodes,
            "total_rings": self.total_rings,
            "shared_rings": self.shared_rings,
            "immune_alerts": self.immune_alerts,
            "sick_models": self.sick_models,
            "collective_v": round(self.collective_v, 6),
            "colony_health": round(self.colony_health, 4),
        }


# ── Swarm Node ────────────────────────────────────────────────

class SwarmNode:
    """A single VOID instance in the swarm mesh.

    Like a single ant: follows simple rules, has local knowledge only.
    Intelligence emerges from interaction with neighbors.

    Rules:
    1. Share high-value rings with neighbors
    2. Forward immune alerts (decrement TTL)
    3. Respond to ring requests from neighbors
    4. Heartbeat every interval to signal alive
    """

    def __init__(
        self,
        node_id: str,
        graph: RingGraph | None = None,
    ):
        self.node_id = node_id
        self.graph = graph or RingGraph()
        self.neighbors: list[str] = []

        # State
        self._inbox: list[SwarmMessage] = []
        self._outbox: list[SwarmMessage] = []
        self._seen_msgs: set[str] = set()
        self._immune_alerts: dict[str, list[str]] = defaultdict(list)  # model -> flags
        self._shared_ring_ids: set[str] = set()
        self._v_scores: dict[str, float] = {}  # model -> latest V
        self._last_heartbeat: float = 0.0
        self._created: float = time.time()
        self._messages_sent: int = 0
        self._messages_received: int = 0

    # ── Core Operations ──────────────────────────────────

    def add_neighbor(self, neighbor_id: str) -> None:
        """Connect to a neighbor node."""
        if neighbor_id not in self.neighbors and neighbor_id != self.node_id:
            self.neighbors.append(neighbor_id)

    def remove_neighbor(self, neighbor_id: str) -> None:
        """Disconnect from a neighbor."""
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)

    def share_ring(self, ring_id: str) -> SwarmMessage | None:
        """Share a ring with all neighbors. Returns the outgoing message."""
        node = self.graph.nodes.get(ring_id)
        if not node or node.compressed:
            return None

        msg = SwarmMessage(
            msg_type="ring_share",
            sender=self.node_id,
            payload={
                "ring_id": node.id,
                "content": node.content,
                "ring_type": node.ring_type,
                "keywords": node.keywords,
                "depth": node.depth,
            },
        )
        self._outbox.append(msg)
        self._shared_ring_ids.add(ring_id)
        self._messages_sent += 1
        return msg

    def broadcast_immune_alert(self, model: str, flags: list[str]) -> SwarmMessage:
        """Alert neighbors about a sick model."""
        msg = SwarmMessage(
            msg_type="immune_alert",
            sender=self.node_id,
            payload={"model": model, "flags": flags},
        )
        self._outbox.append(msg)
        self._immune_alerts[model] = flags
        self._messages_sent += 1
        return msg

    def heartbeat(self) -> SwarmMessage:
        """Send heartbeat to neighbors."""
        self._last_heartbeat = time.time()
        msg = SwarmMessage(
            msg_type="heartbeat",
            sender=self.node_id,
            payload={
                "alive": True,
                "ring_count": self.graph.active_count,
                "neighbor_count": len(self.neighbors),
                "uptime": time.time() - self._created,
                "v_scores": self._v_scores,
            },
        )
        self._outbox.append(msg)
        self._messages_sent += 1
        return msg

    def request_rings(self, keywords: list[str]) -> SwarmMessage:
        """Request rings from neighbors matching keywords."""
        msg = SwarmMessage(
            msg_type="ring_request",
            sender=self.node_id,
            payload={"keywords": keywords},
        )
        self._outbox.append(msg)
        self._messages_sent += 1
        return msg

    def update_v_score(self, model: str, v_score: float) -> SwarmMessage:
        """Broadcast a V-Score update."""
        self._v_scores[model] = v_score
        msg = SwarmMessage(
            msg_type="score_update",
            sender=self.node_id,
            payload={"model": model, "V": v_score},
        )
        self._outbox.append(msg)
        self._messages_sent += 1
        return msg

    # ── Message Processing ──────────────────────────────

    def receive(self, msg: SwarmMessage) -> list[SwarmMessage]:
        """Process an incoming message. Returns response messages (if any).

        Gordon's rule: simple local processing, no global coordination.
        """
        # Dedup
        if msg.msg_id in self._seen_msgs:
            return []
        self._seen_msgs.add(msg.msg_id)
        self._inbox.append(msg)
        self._messages_received += 1

        responses: list[SwarmMessage] = []

        if msg.msg_type == "ring_share":
            responses.extend(self._handle_ring_share(msg))
        elif msg.msg_type == "immune_alert":
            responses.extend(self._handle_immune_alert(msg))
        elif msg.msg_type == "heartbeat":
            pass  # Just record it
        elif msg.msg_type == "ring_request":
            responses.extend(self._handle_ring_request(msg))
        elif msg.msg_type == "ring_response":
            self._handle_ring_response(msg)
        elif msg.msg_type == "score_update":
            self._handle_score_update(msg)

        return responses

    def _handle_ring_share(self, msg: SwarmMessage) -> list[SwarmMessage]:
        """Receive a shared ring. Add it if we don't have similar knowledge."""
        payload = msg.payload
        content = payload.get("content", "")
        keywords = payload.get("keywords", [])

        # Check for redundancy — if we already have similar knowledge, skip
        if self.graph.active_count > 0 and keywords:
            results = self.graph.query(" ".join(keywords), top_k=1)
            if results:
                # Already have something on this topic
                existing_kw = set(results[0].keywords)
                incoming_kw = set(keywords)
                overlap = len(existing_kw & incoming_kw) / max(len(existing_kw | incoming_kw), 1)
                if overlap > 0.7:
                    return []  # Already know this

        # Add ring from swarm
        node = self.graph.add(
            content=content,
            ring_type=payload.get("ring_type", "learning"),
        )
        self._shared_ring_ids.add(node.id)

        # Forward if TTL > 1 (gossip propagation)
        forwards = []
        if msg.ttl > 1:
            fwd = SwarmMessage(
                msg_type="ring_share",
                sender=self.node_id,
                payload=payload,
                msg_id=msg.msg_id,  # same ID prevents loops
                ttl=msg.ttl - 1,
            )
            forwards.append(fwd)
            self._messages_sent += 1

        return forwards

    def _handle_immune_alert(self, msg: SwarmMessage) -> list[SwarmMessage]:
        """Record immune alert and forward."""
        model = msg.payload.get("model", "")
        flags = msg.payload.get("flags", [])
        self._immune_alerts[model] = flags

        # Forward with decremented TTL
        forwards = []
        if msg.ttl > 1:
            fwd = SwarmMessage(
                msg_type="immune_alert",
                sender=self.node_id,
                payload=msg.payload,
                msg_id=msg.msg_id,
                ttl=msg.ttl - 1,
            )
            forwards.append(fwd)
            self._messages_sent += 1

        return forwards

    def _handle_ring_request(self, msg: SwarmMessage) -> list[SwarmMessage]:
        """Search local graph and respond with matching rings."""
        keywords = msg.payload.get("keywords", [])
        if not keywords:
            return []

        query = " ".join(keywords)
        results = self.graph.query(query, top_k=5)

        if not results:
            return []

        ring_data = []
        for rnode in results:
            ring_data.append({
                "ring_id": rnode.id,
                "content": rnode.content,
                "ring_type": rnode.ring_type,
                "keywords": rnode.keywords,
            })

        response = SwarmMessage(
            msg_type="ring_response",
            sender=self.node_id,
            payload={"rings": ring_data, "in_reply_to": msg.msg_id},
        )
        self._messages_sent += 1
        return [response]

    def _handle_ring_response(self, msg: SwarmMessage) -> None:
        """Receive rings from a neighbor's response."""
        rings = msg.payload.get("rings", [])
        for ring in rings:
            content = ring.get("content", "")
            keywords = ring.get("keywords", [])
            # Redundancy check
            if self.graph.active_count > 0 and keywords:
                results = self.graph.query(" ".join(keywords), top_k=1)
                if results:
                    existing_kw = set(results[0].keywords)
                    incoming_kw = set(keywords)
                    overlap = len(existing_kw & incoming_kw) / max(len(existing_kw | incoming_kw), 1)
                    if overlap > 0.7:
                        continue
            rnode = self.graph.add(content, ring_type=ring.get("ring_type", "learning"))
            self._shared_ring_ids.add(rnode.id)

    def _handle_score_update(self, msg: SwarmMessage) -> None:
        """Record V-Score from neighbor."""
        model = msg.payload.get("model", "")
        v = msg.payload.get("V", 0.0)
        if model:
            self._v_scores[model] = v

    # ── Outbox Management ──────────────────────────────

    def flush_outbox(self) -> list[SwarmMessage]:
        """Take all outgoing messages. Caller handles delivery."""
        msgs = list(self._outbox)
        self._outbox.clear()
        return msgs

    # ── Auto-share ─────────────────────────────────────

    def auto_share(self, min_depth: int = 0) -> list[SwarmMessage]:
        """Share all high-value unshared rings with neighbors.

        Gordon's foraging rule: ants share food sources they've verified.
        We share rings that have proven valuable (paradigms, connected rings).
        """
        shared = []
        for ring_id, node in self.graph.nodes.items():
            if ring_id in self._shared_ring_ids:
                continue
            if node.compressed:
                continue
            if node.depth < min_depth:
                continue
            # Share paradigms, milestones, and well-connected rings
            if node.ring_type in ("paradigm", "milestone"):
                msg = self.share_ring(ring_id)
                if msg:
                    shared.append(msg)
            elif len(self.graph._adjacency.get(ring_id, [])) >= 2:
                msg = self.share_ring(ring_id)
                if msg:
                    shared.append(msg)
        return shared

    # ── Introspection ──────────────────────────────────

    @property
    def is_alive(self) -> bool:
        return True  # Local node always alive

    @property
    def ring_count(self) -> int:
        return self.graph.active_count

    @property
    def shared_count(self) -> int:
        return len(self._shared_ring_ids)

    @property
    def known_sick_models(self) -> list[str]:
        return list(self._immune_alerts.keys())

    def vitals(self) -> dict:
        return {
            "node_id": self.node_id,
            "alive": self.is_alive,
            "ring_count": self.ring_count,
            "shared_count": self.shared_count,
            "neighbor_count": len(self.neighbors),
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "sick_models": self.known_sick_models,
            "v_scores": dict(self._v_scores),
            "uptime": time.time() - self._created,
        }

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "neighbors": self.neighbors,
            "shared_ring_ids": list(self._shared_ring_ids),
            "immune_alerts": dict(self._immune_alerts),
            "v_scores": dict(self._v_scores),
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "created": self._created,
        }

    @classmethod
    def from_dict(cls, data: dict, graph: RingGraph | None = None) -> SwarmNode:
        node = cls(node_id=data.get("node_id", "unknown"), graph=graph)
        node.neighbors = data.get("neighbors", [])
        node._shared_ring_ids = set(data.get("shared_ring_ids", []))
        node._immune_alerts = defaultdict(list, data.get("immune_alerts", {}))
        node._v_scores = data.get("v_scores", {})
        node._messages_sent = data.get("messages_sent", 0)
        node._messages_received = data.get("messages_received", 0)
        node._created = data.get("created", time.time())
        return node


# ── Swarm Network ─────────────────────────────────────────────

class SwarmNetwork:
    """Mesh coordinator. Routes messages between nodes.

    Gordon's insight: the colony doesn't have a leader.
    The network just delivers messages. Intelligence emerges.

    In production: replace this with real networking (TCP/HTTP/WebSocket).
    This implementation uses in-memory message passing for testing.
    """

    def __init__(self):
        self._nodes: dict[str, SwarmNode] = {}
        self._message_log: list[SwarmMessage] = []
        self._total_deliveries: int = 0

    # ── Node Management ─────────────────────────────────

    def add_node(self, node: SwarmNode) -> None:
        """Add a node to the swarm."""
        self._nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the swarm."""
        if node_id in self._nodes:
            del self._nodes[node_id]
            # Clean up neighbor references
            for node in self._nodes.values():
                node.remove_neighbor(node_id)

    def connect(self, a: str, b: str) -> None:
        """Connect two nodes bidirectionally."""
        if a in self._nodes and b in self._nodes:
            self._nodes[a].add_neighbor(b)
            self._nodes[b].add_neighbor(a)

    def get_node(self, node_id: str) -> SwarmNode | None:
        return self._nodes.get(node_id)

    # ── Message Delivery ──────────────────────────────

    def deliver(self, msg: SwarmMessage, target: str) -> list[SwarmMessage]:
        """Deliver a message to a specific node. Returns any responses."""
        node = self._nodes.get(target)
        if not node:
            return []
        self._message_log.append(msg)
        self._total_deliveries += 1
        return node.receive(msg)

    def broadcast(self, msg: SwarmMessage) -> list[SwarmMessage]:
        """Deliver a message to all nodes (except sender)."""
        all_responses = []
        for nid in self._nodes:
            if nid == msg.sender:
                continue
            responses = self.deliver(msg, nid)
            all_responses.extend(responses)
        return all_responses

    def tick(self) -> int:
        """Process one round: flush all outboxes, deliver to neighbors.

        Like one step of ant movement. Returns number of messages delivered.
        """
        delivered = 0
        # Collect all outgoing messages
        all_msgs: list[tuple[str, SwarmMessage]] = []
        for _nid, snode in self._nodes.items():
            for msg in snode.flush_outbox():
                # Deliver to all neighbors
                for neighbor_id in snode.neighbors:
                    all_msgs.append((neighbor_id, msg))

        # Deliver (separate loop to avoid mutation during iteration)
        for target, msg in all_msgs:
            responses = self.deliver(msg, target)
            # Process responses: deliver back to requester
            for resp in responses:
                if resp.msg_type == "ring_response":
                    reply_to = msg.sender
                    self.deliver(resp, reply_to)
                    delivered += 1
                else:
                    # Forward to sender's neighbors
                    sender_node = self._nodes.get(resp.sender)
                    if sender_node:
                        for n_id in sender_node.neighbors:
                            if n_id != msg.sender:
                                self.deliver(resp, n_id)
                                delivered += 1
            delivered += 1

        return delivered

    def run(self, ticks: int = 1) -> int:
        """Run multiple ticks. Returns total messages delivered."""
        total = 0
        for _ in range(ticks):
            total += self.tick()
        return total

    # ── Collective Intelligence ─────────────────────────

    def health(self) -> SwarmHealth:
        """Compute collective swarm health. Colony > sum of individuals."""
        h = SwarmHealth()
        h.total_nodes = len(self._nodes)
        h.alive_nodes = sum(1 for n in self._nodes.values() if n.is_alive)

        all_v: list[float] = []
        sick_set: set[str] = set()

        for node in self._nodes.values():
            h.total_rings += node.ring_count
            h.shared_rings += node.shared_count
            for model in node._immune_alerts:
                sick_set.add(model)
                h.immune_alerts += 1
            for v in node._v_scores.values():
                all_v.append(v)

        h.sick_models = sorted(sick_set)
        h.collective_v = sum(all_v) / len(all_v) if all_v else 0.0
        return h

    # ── Topology ─────────────────────────────────────────

    def mesh(self) -> None:
        """Connect every node to every other node (full mesh)."""
        ids = list(self._nodes.keys())
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                self.connect(a, b)

    def ring_topology(self) -> None:
        """Connect nodes in a ring. Each node has exactly 2 neighbors."""
        ids = list(self._nodes.keys())
        for i in range(len(ids)):
            self.connect(ids[i], ids[(i + 1) % len(ids)])

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def total_deliveries(self) -> int:
        return self._total_deliveries

    def nodes(self) -> list[SwarmNode]:
        return list(self._nodes.values())

    # ── Persistence ──────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
            "total_deliveries": self._total_deliveries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SwarmNetwork:
        net = cls()
        net._total_deliveries = data.get("total_deliveries", 0)
        for nid, ndata in data.get("nodes", {}).items():
            node = SwarmNode.from_dict(ndata)
            net._nodes[nid] = node
        return net

    # ── Display ──────────────────────────────────────────

    def summary(self) -> str:
        """One-line summary of the swarm."""
        h = self.health()
        return (
            f"Swarm: {h.alive_nodes}/{h.total_nodes} alive, "
            f"{h.shared_rings}/{h.total_rings} rings shared, "
            f"V={h.collective_v:.4f}, "
            f"colony={h.colony_health:.2%}"
        )
