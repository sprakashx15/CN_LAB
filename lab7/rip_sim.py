"""
rip_sim.py

RIP Simulation (Distance-Vector) using Bellman–Ford style updates.

"""

import os
import time
from copy import deepcopy
import networkx as nx
import matplotlib.pyplot as plt
from tabulate import tabulate

# -----------------------------
# Configuration / parameters
# -----------------------------
OUTPUT_DIR = "rip_outputs"
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
RT_DIR = os.path.join(OUTPUT_DIR, "routing_tables")
PAUSE_BETWEEN_ROUNDS = 0.2  # seconds (for nicer console output, optional)
MAX_ROUNDS = 50
INF = 10**9

# -----------------------------
# Helper utilities
# -----------------------------
def ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(RT_DIR, exist_ok=True)

def save_routing_table_to_file(router_name, dv, rounds):
    fname = os.path.join(RT_DIR, f"rip_{router_name}.txt")
    with open(fname, "w") as f:
        f.write(f"Router {router_name} routing table after convergence (rounds={rounds})\n")
        f.write(tabulate([[dest, (cost if cost < INF else "inf"), nh] for dest, (cost, nh) in sorted(dv.items())],
                         headers=["Destination","Cost","Next Hop"], tablefmt="plain"))
    # no return

def print_routing_table(router_name, dv):
    rows = []
    for dest, (cost, next_hop) in sorted(dv.items()):
        rows.append([router_name, dest, (cost if cost < INF else "inf"), next_hop])
    print(tabulate(rows, headers=["Router","Destination","Cost","Next Hop"], tablefmt="grid"))

# -----------------------------
# Topology creation
# -----------------------------
def create_sample_topology(weighted=False):
    """
    Returns a networkx Graph representing the network topology.

    - weighted=False -> unweighted (hop count)
    - weighted=True  -> edges carry 'cost' attribute (you can set different costs)
    """
    G = nx.Graph()
    # Example routers (nodes)
    nodes = ["A", "B", "C", "D", "E"]
    G.add_nodes_from(nodes)

    # Example edges (bidirectional links)
    # You can edit this list to test different topologies
    edges = [
        ("A","B",1),
        ("A","C",1),
        ("B","C",1),
        ("B","D",1),
        ("C","E",1),
        # you can add more edges or weights
        # ("D","E", 3)
    ]
    if weighted:
        for u,v,c in edges:
            G.add_edge(u, v, cost=c)
    else:
        for u,v,c in edges:
            G.add_edge(u, v)
    return G

# -----------------------------
# Router class
# -----------------------------
class Router:
    def __init__(self, name, neighbors, is_weighted=False, graph=None):
        self.name = name
        self.neighbors = neighbors  # list of neighbor names
        self.dv = {}  # distance vector: dest -> (cost, next_hop)
        self.is_weighted = is_weighted
        self.graph = graph  # if weighted, we may need this to fetch link cost

    def initialize(self, all_nodes):
        # Initialize distance vector:
        for n in all_nodes:
            if n == self.name:
                self.dv[n] = (0, self.name)  # 0 cost to self
            elif n in self.neighbors:
                # cost to neighbor is link cost (1 if unweighted)
                if self.is_weighted and self.graph is not None:
                    try:
                        cost = int(self.graph[self.name][n].get("cost", 1))
                    except Exception:
                        cost = 1
                else:
                    cost = 1
                self.dv[n] = (cost, n)
            else:
                self.dv[n] = (INF, None)

# -----------------------------
# Bellman-style update logic
# -----------------------------
def process_update(router_obj, neighbor_name, neighbor_vector, is_weighted=False, graph=None):
    """
    Apply neighbor's distance vector to router_obj using Bellman-Ford relaxation.
    Returns True if the router's DV changed, otherwise False.
    """
    updated = False
    # cost to neighbor
    if is_weighted and graph is not None:
        try:
            cost_to_nb = int(graph[router_obj.name][neighbor_name].get("cost", 1))
        except Exception:
            cost_to_nb = 1
    else:
        cost_to_nb = 1

    for dest, (nbr_cost, _) in neighbor_vector.items():
        if nbr_cost >= INF:
            new_cost = INF
        else:
            new_cost = cost_to_nb + nbr_cost
        cur_cost, cur_nh = router_obj.dv[dest]
        # If new cost is better, update
        if new_cost < cur_cost:
            router_obj.dv[dest] = (new_cost, neighbor_name)
            updated = True
    return updated

# -----------------------------
# Main simulation: synchronous rounds
# -----------------------------
def simulate_rip(G, weighted=False, max_rounds=MAX_ROUNDS, pause=PAUSE_BETWEEN_ROUNDS, verbose=True):
    all_nodes = list(G.nodes())
    # create router objects
    routers = {n: Router(n, list(G.neighbors(n)), is_weighted=weighted, graph=G if weighted else None) for n in all_nodes}
    # initialize DVs
    for r in routers.values():
        r.initialize(all_nodes)

    updates_per_round = []
    for round_no in range(1, max_rounds+1):
        if verbose:
            print(f"\n========== ROUND {round_no} ==========")
        # snapshots to simulate atomic send
        snapshots = {name: deepcopy(r.dv) for name, r in routers.items()}
        any_update = False
        updates_this_round = 0
        # each router sends its snapshot to its neighbors
        for name, r in routers.items():
            for nb in r.neighbors:
                changed = process_update(routers[nb], name, snapshots[name], is_weighted=weighted, graph=G if weighted else None)
                if changed:
                    any_update = True
                    updates_this_round += 1
        updates_per_round.append(updates_this_round)

        # print current routing tables for visibility
        if verbose:
            for r in routers.values():
                print_routing_table(r.name, r.dv)

        if not any_update:
            if verbose:
                print(f"\nConverged after {round_no} rounds.")
            return routers, round_no, updates_per_round
        time.sleep(pause)
    if verbose:
        print("\nMax rounds reached; may not have fully converged.")
    return routers, max_rounds, updates_per_round

# -----------------------------
# Visualization helpers
# -----------------------------
def draw_topology(G, filename=None, weighted=False):
    pos = nx.spring_layout(G, seed=42)  # deterministic layout
    plt.figure(figsize=(7,5))
    nx.draw_networkx_nodes(G, pos, node_size=800)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")
    nx.draw_networkx_edges(G, pos, width=2)
    if weighted:
        edge_labels = { (u,v): G[u][v].get("cost",1) for u,v in G.edges() }
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.axis('off')
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def plot_convergence(updates_per_round, filename=None):
    rounds = list(range(1, len(updates_per_round)+1))
    plt.figure(figsize=(8,4))
    plt.plot(rounds, updates_per_round, marker='o')
    plt.title("RIP Convergence: updates per round")
    plt.xlabel("Round")
    plt.ylabel("Number of updates (router reactions)")
    plt.grid(True)
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

# -----------------------------
# Utility to pretty-format final tables and save
# -----------------------------
def save_and_print_final_tables(routers, rounds):
    print("\n\n======= FINAL ROUTING TABLES =======")
    for r in routers.values():
        print_routing_table(r.name, r.dv)
        save_routing_table_to_file(r.name, r.dv, rounds)

# -----------------------------
# Example usage
# -----------------------------
def main():
    ensure_dirs()
    # Choose whether to use weighted links
    weighted = False  # set True if you want to test weighted links

    # Create topology (edit this function to change network)
    G = create_sample_topology(weighted=weighted)

    # Save topology image
    topo_file = os.path.join(SCREENSHOT_DIR, "topology.png")
    draw_topology(G, filename=topo_file, weighted=weighted)
    print(f"Topology image saved to: {topo_file}")

    # Run simulation
    routers, rounds, updates = simulate_rip(G, weighted, max_rounds=MAX_ROUNDS, pause=PAUSE_BETWEEN_ROUNDS, verbose=True)

    # Save final tables and print to console
    save_and_print_final_tables(routers, rounds)

    # Save convergence plot
    conv_file = os.path.join(SCREENSHOT_DIR, "rip_convergence.png")
    plot_convergence(updates, filename=conv_file)
    print(f"Convergence plot saved to: {conv_file}")

    print(f"Routing tables saved under: {RT_DIR}")
    print("Done.")

if __name__ == "__main__":
    main()
