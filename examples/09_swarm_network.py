#!/usr/bin/env python3
"""
Example 09: The Swarm Network (Deborah Gordon)

No ant knows the colony's plan. Intelligence emerges from local rules.

This example shows:
1. Creating swarm nodes with local knowledge
2. Connecting them in mesh/ring topologies
3. Knowledge spreading through gossip
4. Immune alerts propagating across the mesh
5. V-Score updates flowing through nodes
6. Collective health monitoring
7. Ring requests (asking the colony)
8. Persistence (save/restore swarm state)
"""

from void_intelligence.swarm import SwarmNode, SwarmNetwork


def main():
    print("=" * 60)
    print("Swarm Network: The colony that knows more than any ant")
    print("=" * 60)
    print()

    # ── 1. Create nodes with local knowledge ──────────────
    print("1. Creating nodes with local knowledge")
    print("-" * 40)

    alpha = SwarmNode(node_id="alpha")
    alpha.graph.add("Paradigm: emergence requires no coordinator", ring_type="paradigm")
    alpha.graph.add("Learning: temperature modulates ant activity", ring_type="learning")

    beta = SwarmNode(node_id="beta")
    beta.graph.add("Discovery: network topology determines resilience", ring_type="paradigm")

    gamma = SwarmNode(node_id="gamma")
    gamma.graph.add("Milestone: swarm converges in O(log n) ticks", ring_type="milestone")

    print(f"  alpha: {alpha.ring_count} rings")
    print(f"  beta:  {beta.ring_count} rings")
    print(f"  gamma: {gamma.ring_count} rings")
    print()

    # ── 2. Build the mesh ─────────────────────────────────
    print("2. Building the mesh")
    print("-" * 40)

    net = SwarmNetwork()
    net.add_node(alpha)
    net.add_node(beta)
    net.add_node(gamma)
    net.mesh()  # Full mesh: everyone connected to everyone

    print(f"  Topology: full mesh ({net.node_count} nodes)")
    print(f"  alpha neighbors: {alpha.neighbors}")
    print(f"  beta neighbors:  {beta.neighbors}")
    print(f"  gamma neighbors: {gamma.neighbors}")
    print()

    # ── 3. Knowledge spread ───────────────────────────────
    print("3. Knowledge spread through gossip")
    print("-" * 40)

    # Each node shares its high-value rings
    for node in net.nodes():
        shared = node.auto_share()
        print(f"  {node.node_id} shares {len(shared)} rings")

    # Run gossip rounds
    for tick in range(3):
        d = net.tick()
        h = net.health()
        print(f"  Tick {tick + 1}: {d} deliveries | "
              f"colony health: {h.colony_health:.0%} | "
              f"rings shared: {h.shared_rings}/{h.total_rings}")

    print()
    for node in net.nodes():
        print(f"  {node.node_id}: {node.ring_count} rings (started with {1 if node.node_id != 'alpha' else 2})")
    print()

    # ── 4. Immune alerts ──────────────────────────────────
    print("4. Immune alert propagation")
    print("-" * 40)

    alpha.broadcast_immune_alert("hallucinator-7b", ["repetitive", "dead_hex"])
    net.tick()

    for node in net.nodes():
        sick = node.known_sick_models
        status = f"warns about: {sick}" if sick else "no alerts"
        print(f"  {node.node_id}: {status}")
    print()

    # ── 5. V-Score propagation ────────────────────────────
    print("5. V-Score propagation")
    print("-" * 40)

    beta.update_v_score("omega-3.5", 0.042)
    beta.update_v_score("gpt-4o", 0.001)
    net.tick()

    h = net.health()
    print(f"  Collective V-Score: {h.collective_v:.4f}")
    for node in net.nodes():
        scores = node._v_scores
        if scores:
            print(f"  {node.node_id}: {scores}")
    print()

    # ── 6. Ring requests ──────────────────────────────────
    print("6. Ring requests (asking the colony)")
    print("-" * 40)

    gamma.request_rings(["emergence", "topology"])
    net.tick()

    print(f"  gamma asked about 'emergence, topology'")
    print(f"  gamma now has {gamma.ring_count} rings (gained from colony)")
    print()

    # ── 7. Colony health ──────────────────────────────────
    print("7. Colony health")
    print("-" * 40)

    h = net.health()
    print(f"  Alive: {h.alive_nodes}/{h.total_nodes}")
    print(f"  Total rings: {h.total_rings}")
    print(f"  Shared: {h.shared_rings}")
    print(f"  Sick models: {h.sick_models}")
    print(f"  Colony health: {h.colony_health:.0%}")
    print(f"  Collective V: {h.collective_v:.4f}")
    print()

    # ── 8. Persistence ────────────────────────────────────
    print("8. Persistence (save/restore)")
    print("-" * 40)

    state = net.to_dict()
    net2 = SwarmNetwork.from_dict(state)
    print(f"  Saved: {net.node_count} nodes, {net.total_deliveries} deliveries")
    print(f"  Restored: {net2.node_count} nodes, {net2.total_deliveries} deliveries")
    print()

    # ── Summary ───────────────────────────────────────────
    print("=" * 60)
    print(net.summary())
    print()
    print("Gordon (1999): 'No ant decides what the colony does next.'")
    print("The industry runs models in isolation. We run them as a colony.")
    print("=" * 60)


if __name__ == "__main__":
    main()
