"""
ospf_sim.py

OSPF Simulation (Link-State) with LSDB flooding and Dijkstra SPT computation.

- Each router originates LSAs for its directly-connected links (with sequence numbers).
- LSAs are reliably flooded until all routers have identical LSDBs (link-state databases).
- Each router builds a local graph from its LSDB and runs Dijkstra to compute the shortest-path tree
  and routing table (destination -> cost, next_hop).
- Visualizes topology and per-router SPTs and saves routing tables to files.

"""

import os
import time
from copy import deepcopy
import networkx as nx
import matplotlib.pyplot as plt
from tabulate import tabulate
import itertools

# -----------------------------
# Configuration
# -----------------------------
OUTPUT_DIR = "ospf_outputs"
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
RT_DIR = os.path.join(OUTPUT_DIR, "routing_tables")
PAUSE = 0.1
MAX_FLOOD_ROUNDS = 50

def ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(RT_DIR, exist_ok=True)

# -----------------------------
# Topology creation (weighted)
# -----------------------------
def create_weighted_topology():
    """
    Returns a networkx Graph with edge attribute 'cost'.
    Edit nodes/edges here for different topologies.
    """
    G = nx.Graph()
    # nodes
    nodes = ["R1", "R2", "R3", "R4", "R5"]
    G.add_nodes_from(nodes)
    # edges: (u, v, cost)
    edges = [
        ("R1","R2", 2),
        ("R1","R3", 5),
        ("R2","R3", 1),
        ("R2","R4", 2),
        ("R3","R5", 3),
        ("R4","R5", 1),
        # add more links if desired
        # ("R1","R4", 7)
    ]
    for u,v,c in edges:
        G.add_edge(u, v, cost=c)
    return G

# -----------------------------
# LSA & Router classes
# -----------------------------
class LSA:
    """
    Simple LSA representation.
    link_id: tuple (u,v) with sorted nodes
    origin: router name
    seq: sequence number (int)
    cost: link cost
    """
    def __init__(self, link_id, origin, seq, cost):
        self.link_id = tuple(sorted(link_id))
        self.origin = origin
        self.seq = seq
        self.cost = cost

    def key(self):
        return self.link_id

    def to_dict(self):
        return {"link": self.link_id, "origin": self.origin, "seq": self.seq, "cost": self.cost}

    def __repr__(self):
        return f"LSA(link={self.link_id}, origin={self.origin}, seq={self.seq}, cost={self.cost})"

class OSPFRouter:
    """
    Router that keeps an LSDB (mapping link_id -> (cost, seq, origin)).
    For simplicity, LSDB holds latest LSA per link (identified by link tuple).
    """
    def __init__(self, name, neighbors):
        self.name = name
        self.neighbors = neighbors  # neighbor names list
        # LSDB: link_id -> {"cost":..., "seq":..., "origin":...}
        self.lsdb = {}
        # LSA sequence number counter for LSAs originated by this router
        self.seq_counter = itertools.count(start=1)
    def originate_lsas(self, graph):
        """
        Create LSAs for each adjacent link (u, v) where this router is u or v.
        Each LSA uses this router as the origin and increments sequence numbers.
        """
        created_lsas = []
        for u, v, data in graph.edges(self.name, data=True):
            link = tuple(sorted((u, v)))
            seq = next(self.seq_counter)
            cost = data.get("cost", 1)
            lsa = LSA(link, self.name, seq, cost)
            # store immediately in local LSDB (originated by self)
            self.lsdb[link] = {"cost": cost, "seq": seq, "origin": self.name}
            created_lsas.append(lsa)
        return created_lsas

    def receive_lsa(self, lsa: LSA):
        """
        When receiving an LSA, accept it if its sequence number is newer than what's in LSDB.
        Return True if LSDB changes.
        """
        key = lsa.key()
        existing = self.lsdb.get(key)
        if existing is None or lsa.seq > existing.get("seq", 0):
            # accept and store
            self.lsdb[key] = {"cost": lsa.cost, "seq": lsa.seq, "origin": lsa.origin}
            return True
        return False

# -----------------------------
# Flooding simulation (reliable)
# -----------------------------
def flood_lsas(routers: dict, initial_lsas: dict):
    """
    Simulate reliable flooding of LSAs until no router updates its LSDB.
    routers: name -> OSPFRouter
    initial_lsas: name -> list of LSAs originated by that router
    Returns number_of_rounds and total_advertisements_per_round list for plotting (optional)
    """
    # Each router maintains an 'inbox' (LSAs newly received this round) to avoid immediate re-flood loops.
    # We'll do synchronous rounds: in each round, every router sends its new/known LSAs to neighbors, neighbors process them next round.
    # For simplicity we initially give each router the LSAs it originated (local), then flood until quiescent.
    # Prepare initial known LSAs based on originations
    for name, lsas in initial_lsas.items():
        for lsa in lsas:
            routers[name].lsdb[lsa.key()] = {"cost": lsa.cost, "seq": lsa.seq, "origin": lsa.origin}

    rounds = 0
    advs_per_round = []
    while True:
        rounds += 1
        any_change = False
        advs = 0
        # snapshots to simulate atomic sending
        snapshots = {name: deepcopy(r.lsdb) for name, r in routers.items()}
        # each router sends their full LSDB to neighbors (in practice routers send only new LSAs; here we simplify)
        for name, r in routers.items():
            for nb in r.neighbors:
                # neighbor processes each LSA that the sender knows
                for link, info in snapshots[name].items():
                    lsa = LSA(link, info.get("origin"), info.get("seq"), info.get("cost"))
                    changed = routers[nb].receive_lsa(lsa)
                    if changed:
                        any_change = True
                        advs += 1
        advs_per_round.append(advs)
        # stop when no change occurred in this round
        if not any_change or rounds >= MAX_FLOOD_ROUNDS:
            break
        time.sleep(PAUSE)
    return rounds, advs_per_round

# -----------------------------
# Build graph from LSDB (for a router)
# -----------------------------
def build_graph_from_lsdb(lsdb):
    """
    lsdb: dict link_id -> {"cost":..., "seq":..., "origin":...}
    Returns a networkx Graph constructed from LSDB (edges with 'cost')
    """
    H = nx.Graph()
    for (u,v), info in lsdb.items():
        cost = info.get("cost", 1)
        H.add_edge(u, v, cost=cost)
    return H

# -----------------------------
# Compute routing table for each router using Dijkstra
# -----------------------------
def compute_routing_tables(routers: dict):
    """
    For each router, build Graph from its LSDB and run Dijkstra to obtain
    cost and next-hop to every destination.
    Returns a mapping: router_name -> routing_table (dest -> (cost, next_hop))
    """
    routing_tables = {}
    for name, r in routers.items():
        H = build_graph_from_lsdb(r.lsdb)
        # ensure the graph includes the router itself (even isolated)
        if name not in H.nodes():
            H.add_node(name)
        try:
            lengths, paths = nx.single_source_dijkstra(H, source=name, weight='cost')
        except Exception as e:
            # disconnected graph may raise errors; handle by creating default unreachable entries
            lengths = {}
            paths = {}
        # construct routing table: for each reachable destination, next_hop is the first hop on the path
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
                rt[dest] = (float('inf'), None)
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
    plt.title("OSPF Topology (link costs shown)")
    plt.axis('off')
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def draw_spt(router_name, lsdb, routing_table, filename=None):
    """
    Draw the shortest path tree for router_name.
    lsdb: router's LSDB (to build the underlying network)
    routing_table: mapping dest -> (cost, next_hop)
    """
    H = build_graph_from_lsdb(lsdb)
    pos = nx.spring_layout(H, seed=42)
    plt.figure(figsize=(8,6))
    # draw base topology (faded)
    nx.draw_networkx_nodes(H, pos, node_size=600)
    nx.draw_networkx_labels(H, pos, font_size=11)
    nx.draw_networkx_edges(H, pos, alpha=0.3)
    # build edges of SPT from routing_table (by following next hops)
    # We'll collect SPT edges as (u,v) pairs where v is next hop from u? Prefer to draw from root to dest along path.
    spt_edges = []
    for dest, (cost, next_hop) in routing_table.items():
        if dest == router_name:
            continue
        if next_hop is None or cost == float('inf'):
            continue
        # reconstruct path by repeatedly following next hops using routing_table of the router
        # Simpler: use networkx shortest_path in local H to get exact tree edges
        try:
            path = nx.shortest_path(H, source=router_name, target=dest, weight='cost')
            path_edges = list(zip(path[:-1], path[1:]))
            for e in path_edges:
                if e not in spt_edges:
                    spt_edges.append(e)
        except Exception:
            pass
    # draw SPT edges highlighted
    if spt_edges:
        nx.draw_networkx_edges(H, pos, edgelist=spt_edges, width=3, edge_color='tab:orange')
    # annotate title
    plt.title(f"SPT for {router_name}")
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

# -----------------------------
# Utility: save routing tables to files & print
# -----------------------------
def print_and_save_routing_tables(routing_tables):
    for name, rt in routing_tables.items():
        print(f"\nRouting table for {name}:")
        rows = []
        for dest, (cost, nh) in sorted(rt.items()):
            rows.append([dest, (cost if cost != float('inf') else "inf"), nh])
        print(tabulate(rows, headers=["Destination","Cost","Next Hop"], tablefmt="grid"))
        fname = os.path.join(RT_DIR, f"ospf_{name}.txt")
        with open(fname, "w") as f:
            f.write(f"OSPF routing table for {name}\n")
            f.write(tabulate(rows, headers=["Destination","Cost","Next Hop"], tablefmt="plain"))
    print(f"\nRouting tables saved to: {RT_DIR}")

# -----------------------------
# Main simulation glue
# -----------------------------
def main():
    ensure_dirs()
    # Build the true network topology (ground truth)
    G = create_weighted_topology()
    topo_file = os.path.join(SCREENSHOT_DIR, "topology_ospf.png")
    draw_topology(G, filename=topo_file)
    print(f"Topology image saved to: {topo_file}")

    # Create routers and originate LSAs
    routers = {}
    initial_lsas = {}
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        r = OSPFRouter(node, neighbors)
        routers[node] = r
    # Each router originates LSAs for its incident links
    for name, r in routers.items():
        lsas = r.originate_lsas(G)
        initial_lsas[name] = lsas

    # Flood LSAs until convergence
    print("Starting LSA flooding...")
    rounds, advs_per_round = flood_lsas(routers, initial_lsas)
    print(f"LSA flooding converged after {rounds} rounds.")
    # optional: print LSDB sizes
    for name, r in routers.items():
        print(f"Router {name} LSDB entries: {len(r.lsdb)}")

    # Compute routing tables (Dijkstra)
    routing_tables = compute_routing_tables(routers)
    print_and_save_routing_tables(routing_tables)

    # Save SPT images for each router
    for name, r in routers.items():
        spt_file = os.path.join(SCREENSHOT_DIR, f"ospf_spt_{name}.png")
        draw_spt(name, r.lsdb, routing_tables[name], filename=spt_file)
        print(f"SPT image for {name} saved to: {spt_file}")

    print("OSPF simulation complete.")

if __name__ == "__main__":
    main()
