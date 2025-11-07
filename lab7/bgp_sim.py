"""
bgp_sim.py

Simplified BGP path-vector simulation.

- Each node is an AS (autonomous system) identified by an integer AS number or string.
- Each AS may originate one or more prefixes (we model prefixes as 'P<ASN>' or custom strings).
- ASes exchange UPDATEs containing AS-paths to prefixes.
- Route selection: shortest AS-path (fewer AS hops). Tie-breaker: lexicographically smaller path.
- Loop prevention: a router rejects any advertised path containing its own AS.
- Convergence: when a full round causes no route changes.

"""

import os
import time
from copy import deepcopy
import networkx as nx
import matplotlib.pyplot as plt
from tabulate import tabulate

# ----------------------------
# Config / Paths
# ----------------------------
OUTPUT_DIR = "bgp_outputs"
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
RT_DIR = os.path.join(OUTPUT_DIR, "routing_tables")
PAUSE = 0.05  # small pause between rounds (for nicer console output)
MAX_ROUNDS = 50

# ----------------------------
# Utilities
# ----------------------------
def ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(RT_DIR, exist_ok=True)

def save_routing_table(asn, table):
    fname = os.path.join(RT_DIR, f"bgp_AS{asn}.txt")
    with open(fname, "w") as f:
        f.write(f"BGP routing table for AS{asn}\n")
        f.write(tabulate([[prefix, " -> ".join(map(str,path)), (len(path)-1 if path else "inf"), (path[1] if len(path)>1 else None)]
                         for prefix, path in sorted(table.items())],
                         headers=["Prefix","AS-Path","AS-Path-Length","Next-Hop"], tablefmt="plain"))
    return fname

def print_table(asn, table):
    rows = []
    for prefix, path in sorted(table.items()):
        rows.append([prefix, " -> ".join(map(str, path)) if path else "unreachable",
                     (len(path)-1 if path else "inf"), (path[1] if path and len(path)>1 else "-")])
    print(f"\nRouting table for AS{asn}:")
    print(tabulate(rows, headers=["Prefix","AS-Path","AS-Path-Length","Next-Hop"], tablefmt="grid"))

# ----------------------------
# BGP simulation core
# ----------------------------
class ASNode:
    """
    Represents an AS router in the simplified simulation.
    - asn: AS number (int or str)
    - neighbors: list of neighbor AS numbers
    - local_rib: local routing table prefix -> AS-path (list)
      Example: prefix 'P5' -> [2, 5] meaning next-hop is 2 then 5; local AS would be at index 0 if originated.
    - orig_prefixes: set/list of prefixes this AS originates. For an origin AS X and prefix 'P5', the originating path is [X].
    """
    def __init__(self, asn, neighbors=None, orig_prefixes=None):
        self.asn = asn
        self.neighbors = neighbors if neighbors else []
        # local routing information base (prefix -> AS-path)
        self.local_rib = {}
        # origin prefixes: if this AS originates prefix P, it initially installs path [asn] for that prefix
        self.orig_prefixes = set(orig_prefixes) if orig_prefixes else set()
        for p in self.orig_prefixes:
            self.local_rib[p] = [asn]

    def originate_updates(self):
        """
        Returns a dict of prefix -> as_path that this AS will advertise (its current local_rib).
        In real BGP, AS prepends itself when sending; in this sim we will prepend at send time.
        """
        return deepcopy(self.local_rib)

    def receive_update(self, from_asn, prefix, path):
        """
        Handle an UPDATE for prefix received from neighbor 'from_asn' whose advertised path is 'path'.
        'path' is the AS-path as advertised by the neighbor (i.e., neighbor's local path).
        When we receive it, the AS will consider a candidate path = [self.asn] + path? No — reorder carefully:
        In BGP, a router receiving path P from neighbor N treats the path as [N] + P_from_N? Actually neighbor advertises P that already starts with neighbor as origin?
        For simplicity, we assume neighbor advertises a path that already includes neighbor at its head.
        So when receiver evaluates, it constructs candidate = [from_asn] + path_after_from? To keep it straightforward:
        We'll assume 'path' is the advertised path that starts at the advertising AS (so doesn't include 'from_asn' twice).
        For our sending logic, we'll advertise path = [self.asn] + current_path_if_any.
        Here, if neighbor sent us advertised_path (which already begins with neighbor), we will consider advertised_path as candidate.
        """
        # Loop prevention: if our own ASN is in the received AS-path, reject.
        if self.asn in path:
            return False  # reject due to loop

        # Candidate path is as received (the neighbor's advertised path),
        # but in our modeling the neighbor advertises as [neighbor, ...destAS] or [neighbor] for origin.
        # We don't need to prepend here because the neighbor already included itself at start.
        current = self.local_rib.get(prefix)
        # Select by shortest AS-path length; tie-breaker: lexicographical compare of path lists
        def better(new, old):
            if old is None:
                return True
            if len(new) < len(old):
                return True
            if len(new) == len(old) and list(map(str,new)) < list(map(str,old)):
                return True
            return False

        if better(path, current):
            # install candidate path BUT we must make it appear from our view:
            # Our local_rib stores the path as [originators_chain], not including self.
            # However to be consistent with advertising, we'll store the path as [from_asn] + path_rest if needed.
            # In this implementation we assume 'path' already starts with the neighbor (advertiser),
            # and that's OK to store directly.
            self.local_rib[prefix] = list(path)
            return True
        return False

# ----------------------------
# Network / Topology helpers
# ----------------------------
def create_as_topology():
    """
    Customize here: return (nodes_dict, list_of_edges)
    nodes_dict: asn -> orig_prefixes
    edges: list of (asn1, asn2) connections (peerings)
    Example topology:
        AS1 -- AS2 -- AS3
         |               \
        AS4 ------------ AS5
    We'll create a small demo topology for lab purposes.
    """
    # Define AS nodes and which prefix(es) they originate
    nodes = {
        1: ["P1"],
        2: [],           # transit AS
        3: ["P3"],
        4: ["P4"],
        5: []            # transit AS
    }
    # Define AS-level links (peerings)
    edges = [
        (1,2),
        (2,3),
        (2,4),
        (3,5),
        (4,5)
    ]
    return nodes, edges

def draw_as_topology(edges, filename=None):
    G = nx.Graph()
    # add edges; nodes will be derived
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(7,5))
    nx.draw_networkx_nodes(G, pos, node_size=900)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")
    nx.draw_networkx_edges(G, pos, width=2)
    plt.title("AS-level Topology (BGP sim)")
    plt.axis('off')
    if filename:
        plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

# ----------------------------
# BGP propagation simulation
# ----------------------------
def bgp_propagate(as_nodes, max_rounds=MAX_ROUNDS, pause=PAUSE, verbose=True):
    """
    Simulate rounds of UPDATE propagation:
    Synchronous rounds: in each round, every AS advertises all prefixes it knows (local_rib) to all neighbors.
    When sending to neighbor, the sender advertises a path that starts with sender's AS (i.e., [sender_asn] + current_path_if_any_if_needed).
    For simplicity, our stored local_rib entries are already AS-paths where head may be origin or previous advertiser.
    When sending to neighbor, we will advertise: advertised_path = [sender_asn] + best_path_without_self if best_path exists and DOES NOT already start with sender_asn.
    The neighbor will receive that advertised_path and decide whether to accept (loop prevention + path selection).
    Continue until a round produces no updates.
    """
    rounds = 0
    for r in range(1, max_rounds+1):
        rounds += 1
        if verbose:
            print(f"\n--- BGP ROUND {r} ---")
        snapshots = {asn: deepcopy(node.local_rib) for asn, node in as_nodes.items()}
        any_change = False
        for asn, node in as_nodes.items():
            # for each prefix this AS knows, prepare an advertisement to neighbors
            for prefix, path in snapshots[asn].items():
                # Build advertised path: it should include this AS at the head
                # If path already begins with this AS (originated here), advertise that same [asn,...]
                if len(path) == 0:
                    continue
                # In our storage, path is some list whose head might or might not be the asn.
                # Force the advertised form to start with asn:
                # Remove any leading duplicates and ensure first element is asn
                advertised = [asn] + [p for p in path if p != asn]
                # send to neighbors
                for nb in node.neighbors:
                    # Avoid immediate reflection: the neighbor will receive 'advertised'
                    # neighbor.receive_update will check loop prevention and selection
                    changed = as_nodes[nb].receive_update(asn, prefix, advertised)
                    if changed:
                        any_change = True
                        if verbose:
                            print(f"AS{asn} -> AS{nb}: UPDATE for {prefix} with path {advertised}")
        if verbose:
            # print brief summary
            for asn, node in as_nodes.items():
                print(f"AS{asn} knows prefixes: {list(node.local_rib.keys())}")
        time.sleep(pause)
        if not any_change:
            if verbose:
                print("\nNo changes this round — converged.")
            break
    return rounds

# ----------------------------
# Build ASNodes from topology
# ----------------------------
def build_as_nodes(nodes_def, edges):
    """
    nodes_def: dict asn -> list of prefixes originated
    edges: list of (asn1, asn2)
    returns dict: asn -> ASNode
    """
    # Create adjacency
    adj = {}
    for a,b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    # Build ASNode objects
    as_nodes = {}
    for asn, prefixes in nodes_def.items():
        neighbors = adj.get(asn, [])
        as_nodes[asn] = ASNode(asn, neighbors=neighbors, orig_prefixes=prefixes)
    # Ensure all nodes present in adj are included even if no orig prefixes
    for asn in adj:
        if asn not in as_nodes:
            as_nodes[asn] = ASNode(asn, neighbors=adj.get(asn, []), orig_prefixes=[])
    return as_nodes

# ----------------------------
# Output helpers: save tables and print final state
# ----------------------------
def save_and_print_all(as_nodes):
    for asn, node in sorted(as_nodes.items()):
        print_table(asn, node.local_rib)
        fname = save_routing_table(asn, node.local_rib)
        print(f"Saved: {fname}")

# ----------------------------
# Optional: simulate a withdrawal or topology change
# ----------------------------
def simulate_withdrawal(as_nodes, withdrawing_asn, prefix):
    """
    Withdraw prefix from an origin AS by removing it from its local RIB (origin withdraws).
    Then run another propagation round(s) to observe changes.
    """
    origin = as_nodes.get(withdrawing_asn)
    if origin is None:
        return False
    if prefix in origin.local_rib:
        del origin.local_rib[prefix]
        print(f"\n*** AS{withdrawing_asn} withdrew {prefix} from its local RIB ***")
        return True
    else:
        print(f"AS{withdrawing_asn} does not originate {prefix} (no-op).")
        return False

# ----------------------------
# Main
# ----------------------------
def main():
    ensure_dirs()
    # Create topology and nodes
    nodes_def, edges = create_as_topology()
    topo_file = os.path.join(SCREENSHOT_DIR, "topology_bgp.png")
    draw_as_topology(edges, filename=topo_file)
    print(f"AS-level topology saved to: {topo_file}")

    # Build ASNode objects
    as_nodes = build_as_nodes(nodes_def, edges)

    # Initial state: each AS has its locally originated prefixes already (set in constructor)
    print("\nInitial local RIBs (origins):")
    for asn, node in sorted(as_nodes.items()):
        print(f"AS{asn} originates: {sorted(node.orig_prefixes)}")

    # Run BGP propagation until convergence
    rounds = bgp_propagate(as_nodes, max_rounds=MAX_ROUNDS, pause=PAUSE, verbose=True)
    print(f"\nConverged after {rounds} rounds.\n")

    # Print and save final tables
    save_and_print_all(as_nodes)

    # Optional: simulate a withdrawal and reconverge (uncomment below to demo)
    #withdraw_prefix = "P3"
    #if simulate_withdrawal(as_nodes, withdrawing_asn=3, prefix=withdraw_prefix):
    #    # run propagation again to observe reconvergence
    #    rounds2 = bgp_propagate(as_nodes, max_rounds=MAX_ROUNDS, pause=PAUSE, verbose=True)
    #    print(f"After withdrawal, converged in {rounds2} rounds.")
    #    save_and_print_all(as_nodes)

    print("\nBGP simulation finished.")

if __name__ == "__main__":
    main()
