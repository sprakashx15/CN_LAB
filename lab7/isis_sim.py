"""
isis_sim.py

IS-IS Simulation (Link-State style) for lab assignment.

- Each router originates LSPs for adjacent links with sequence numbers.
- LSPs are flooded reliably until all routers have identical LSDBs.
- Each router computes shortest-path tree (Dijkstra) from its LSDB and generates routing table.
- Outputs saved under outputs/screenshots and outputs/routing_tables.

"""

import os
import time
from copy import deepcopy
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from tabulate import tabulate

# -----------------------------
# Configuration
# -----------------------------
OUTPUT_DIR = "isis_outputs"
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
RT_DIR = os.path.join(OUTPUT_DIR, "routing_tables")
PAUSE = 0.08
MAX_FLOOD_ROUNDS = 60

INF = float('inf')

# -----------------------------
# Ensure directories exist
# -----------------------------
def ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(RT_DIR, exist_ok=True)

# -----------------------------
# Topology (weighted)
# -----------------------------
def create_isis_topology():
    """
    Build a sample weighted topology for IS-IS simulation.
    Edit nodes/edges to experiment.
    """
    G = nx.Graph()
    nodes = ["A","B","C","D","E","F"]
    G.add_nodes_from(nodes)
    edges = [
        ("A","B", 2),
        ("A","C", 3),
        ("B","C", 1),
        ("B","D", 4),
        ("C","E", 5),
        ("D","E", 1),
        ("D","F", 3),
        ("E","F", 2)
    ]
    for u,v,c in edges:
        G.add_edge(u, v, cost=c)
    return G

# -----------------------------
# LSP (Link State PDU) representation
# -----------------------------
class LSP:
    """
    Simple LSP representation.
    link_id: tuple (u,v) sorted
    origin: originator router name
    seq: sequence number
    cost: link metric
    """
    def __init__(self, link_id, origin, seq, cost):
        self.link_id = tuple(sorted(link_id))
        self.origin = origin
        self.seq = seq
        self.cost = cost

    def key(self):
        return self.link_id

    def __repr__(self):
        return f"LSP(link={self.link_id}, origin={self.origin}, seq={self.seq}, cost={self.cost})"

# -----------------------------
# Router object for IS-IS
# -----------------------------
class ISISRouter:
    def __init__(self, name, neighbors):
        self.name = name
        self.neighbors = neighbors  # list of neighbor names
        # LSDB: link_id -> {"cost":..., "seq":..., "origin":...}
        self.lsdb = {}
        # local sequence counter to originate LSPs
        self.seq_counter = itertools.count(start=1)

    def originate_lsps(self, graph):
        """
        Create LSPs for incident links and store locally.
        Returns list of LSPs originated.
        """
        created = []
        for u, v, data in graph.edges(self.name, data=True):
            link = tuple(sorted((u, v)))
            seq = next(self.seq_counter)
            cost = data.get("cost", 1)
            lsp = LSP(link, self.name, seq, cost)
            # store in local LSDB
            self.lsdb[lsp.key()] = {"cost": cost, "seq": seq, "origin": self.name}
            created.append(lsp)
        return created

    def receive_lsp(self, lsp: LSP):
        """
        Accept LSP if seq is newer than stored entry; return True if LSDB changed.
        """
        key = lsp.key()
        existing = self.lsdb.get(key)
        if existing is None or lsp.seq > existing.get("seq", 0):
            self.lsdb[key] = {"cost": lsp.cost, "seq": lsp.seq, "origin": lsp.origin}
            return True
        return False

# -----------------------------
# Flooding logic (reliable synchronous rounds)
# -----------------------------
def flood_lsps(routers: dict, initial_lsps: dict):
    """
    Flood LSPs until no LSDB changes occur.
    routers: name -> ISISRouter
    initial_lsps: name -> list of LSPs originated by that router
    Returns (rounds, lsp_advs_per_round_list)
    """
    # preload origin LSPs into routers' own LSDBs
    for name, lsps in initial_lsps.items():
        for lsp in lsps:
            routers[name].lsdb[lsp.key()] = {"cost": lsp.cost, "seq": lsp.seq, "origin": lsp.origin}

    rounds = 0
    advs_per_round = []
    while True:
        rounds += 1
        any_change = False
        advs = 0
        snapshots = {name: deepcopy(r.lsdb) for name, r in routers.items()}
        # each router sends its LSDB snapshot to neighbors
        for name, r in routers.items():
            for nb in r.neighbors:
                # neighbor processes every LSP in sender's snapshot
                for link, info in snapshots[name].items():
                    lsp = LSP(link, info.get("origin"), info.get("seq"), info.get("cost"))
                    changed = routers[nb].receive_lsp(lsp)
                    if changed:
                        any_change = True
                        advs += 1
        advs_per_round.append(advs)
        if not any_change or rounds >= MAX_FLOOD_ROUNDS:
            break
        time.sleep(PAUSE)
    return rounds, advs_per_round

# -----------------------------
# Build graph from an LSDB
# -----------------------------
def build_graph_from_lsdb(lsdb):
    H = nx.Graph()
    for (u,v), info in lsdb.items():
        cost = info.get("cost", 1)
        H.add_edge(u, v, cost=cost)
    return H

# -----------------------------
# Compute routing tables (Dijkstra)
# -----------------------------
def compute_routing_tables(routers: dict):
    """
    For each router, build graph from its LSDB and compute shortest paths.
    Returns mapping: router_name -> routing_table (dest -> (cost, next_hop))
    """
    routing_tables = {}
    for name, r in routers.items():
        H = build_graph_from_lsdb(r.lsdb)
        # ensure node present even if isolated
        if name not in H.nodes():
            H.add_node(name)
        try:
            lengths, paths = nx.single_source_dijkstra(H, source=name, weight='cost')
        except Exception:
            lengths = {}
            paths = {}
        rt = {}
        for dest in sorted(H.nodes()):
            if dest == name:
                rt[dest] = (0, name)
            elif dest in paths:
                path = paths[dest]
                cost = lengths[dest]
                next_hop = path[1] if len(path) >= 2 else None
                rt[dest] = (cost, next_hop)
            else:
                rt[dest] = (INF, None)
        routing_tables[name] = rt
    return routing_tables

# -----------------------------
# Visualization helpers
# -----------------------------
def draw_topology(G, filename=None):
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8,6))
    nx.draw_networkx_nodes(G, pos, node_size=700)
    nx.draw_networkx_labels(G, pos, font_size=11, font_weight="bold")
    nx.draw_networkx_edges(G, pos, width=2)
    edge_labels = { (u,v): G[u][v].get("cost",1) for u,v in G.edges() }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("IS-IS Topology (link metrics)")
    plt.axis('off')
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def draw_spt(router_name, lsdb, routing_table, filename=None):
    H = build_graph_from_lsdb(lsdb)
    pos = nx.spring_layout(H, seed=42)
    plt.figure(figsize=(8,6))
    nx.draw_networkx_nodes(H, pos, node_size=600)
    nx.draw_networkx_labels(H, pos, font_size=11)
    nx.draw_networkx_edges(H, pos, alpha=0.3)
    # Highlight SPT edges by reconstructing paths
    spt_edges = []
    for dest, (cost, nh) in routing_table.items():
        if dest == router_name or nh is None or cost == INF:
            continue
        try:
            path = nx.shortest_path(H, source=router_name, target=dest, weight='cost')
            path_edges = list(zip(path[:-1], path[1:]))
            for e in path_edges:
                if e not in spt_edges:
                    spt_edges.append(e)
        except Exception:
            pass
    if spt_edges:
        nx.draw_networkx_edges(H, pos, edgelist=spt_edges, width=3, edge_color='tab:green')
    plt.title(f"IS-IS SPT for {router_name}")
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

# -----------------------------
# Print & save routing tables
# -----------------------------
def print_and_save_tables(routing_tables, rounds):
    print("\n====== FINAL ROUTING TABLES ======")
    for name, rt in routing_tables.items():
        rows = []
        for dest, (cost, nh) in sorted(rt.items()):
            rows.append([dest, (cost if cost != INF else "inf"), nh])
        print(f"\nRouter {name} routing table (rounds={rounds}):")
        print(tabulate(rows, headers=["Destination","Cost","Next Hop"], tablefmt="grid"))
        fname = os.path.join(RT_DIR, f"isis_{name}.txt")
        with open(fname, "w") as f:
            f.write(f"IS-IS routing table for {name} (rounds={rounds})\n")
            f.write(tabulate(rows, headers=["Destination","Cost","Next Hop"], tablefmt="plain"))
    print(f"\nRouting tables saved to: {RT_DIR}")

# -----------------------------
# Main simulation flow
# -----------------------------
def main():
    ensure_dirs()
    # Build ground-truth topology
    G = create_isis_topology()
    topo_file = os.path.join(SCREENSHOT_DIR, "topology_isis.png")
    draw_topology(G, filename=topo_file)
    print(f"Topology image saved to: {topo_file}")

    # Create routers and originate LSPs
    routers = {}
    initial_lsps = {}
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        r = ISISRouter(node, neighbors)
        routers[node] = r

    for name, r in routers.items():
        lsps = r.originate_lsps(G)
        initial_lsps[name] = lsps

    print("Starting LSP flooding (IS-IS style)...")
    rounds, advs_per_round = flood_lsps(routers, initial_lsps)
    print(f"Flooding converged after {rounds} rounds.")
    for name, r in routers.items():
        print(f"Router {name} LSDB size: {len(r.lsdb)}")

    # Compute routing tables
    routing_tables = compute_routing_tables(routers)
    print_and_save_tables(routing_tables, rounds)

    # Save per-router SPT images
    for name, r in routers.items():
        spt_file = os.path.join(SCREENSHOT_DIR, f"isis_spt_{name}.png")
        draw_spt(name, r.lsdb, routing_tables[name], filename=spt_file)
        print(f"SPT saved: {spt_file}")

    # Optionally plot flooding activity (advs per round)
    conv_file = os.path.join(SCREENSHOT_DIR, "isis_flooding_activity.png")
    try:
        import matplotlib.pyplot as plt
        rounds_x = list(range(1, len(advs_per_round)+1))
        plt.figure(figsize=(8,4))
        plt.plot(rounds_x, advs_per_round, marker='o')
        plt.title("IS-IS Flooding: LSP updates per round")
        plt.xlabel("Round")
        plt.ylabel("Number of LSP updates applied")
        plt.grid(True)
        plt.savefig(conv_file, bbox_inches='tight', dpi=200)
        plt.close()
        print(f"Flooding activity plot saved: {conv_file}")
    except Exception:
        pass

    print("IS-IS simulation complete.")

if __name__ == "__main__":
    main()
