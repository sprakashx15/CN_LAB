try:
    from ip_utils import ip_to_binary, get_network_prefix
except ImportError:
    print("\n--- ERROR ---")
    print("Could not find 'ip_utils.py' in the same directory.")
    print("Please make sure 'ip_utils.py' is present before running 'router.py'.")
    print("-------------\n")
    exit()

class Router:

    def __init__(self, routes: list):
        # This list will store our "optimized" forwarding table
        self.forwarding_table = []
        
        # Call the helper method to process the routes as required [cite: 34]
        self._build_forwarding_table(routes)

    def _build_forwarding_table(self, routes: list):
        
        print("Building forwarding table...")
        temp_table = []
        for (cidr_prefix, output_link) in routes:
            binary_prefix = get_network_prefix(cidr_prefix)
            
            prefix_length = len(binary_prefix)
            temp_table.append((binary_prefix, prefix_length, output_link))
        
    
        self.forwarding_table = sorted(temp_table, 
                                       key=lambda item: item[1], 
                                       reverse=True)
        print("Forwarding table built and sorted.")

    def route_packet(self, dest_ip: str) -> str:
        binary_dest_ip = ip_to_binary(dest_ip)
        for (binary_prefix, prefix_len, output_link) in self.forwarding_table:
            
            if binary_dest_ip.startswith(binary_prefix):
                return output_link
                
        return "Default Gateway"


# --- Main execution block for testing ---
if __name__ == "__main__":
    
    print("--- Testing Part 2: router.py ---")

    # 1. Define the routes for the test case [cite: 50-52]
    routes_list = [
        ("223.1.1.0/24", "Link 0"),
        ("223.1.2.0/24", "Link 1"),
        ("223.1.3.0/24", "Link 2"),
        ("223.1.0.0/16", "Link 4 (ISP)")
    ]
    
    # 2. Initialize the Router
    my_router = Router(routes_list)

    # (Optional) Print the sorted internal table to verify the hint
    print("\n--- Internal Forwarding Table (Sorted Longest-to-Shortest) ---")
    for (prefix, length, link) in my_router.forwarding_table:
        print(f"  Prefix: {prefix:<24} (Len: {length}) -> {link}")
    print("---------------------------------------------------------------")

    # 3. Verify the test cases [cite: 53]
    
    print("\n--- Running Routing Tests ---")
    
    # Test 1: Should match "223.1.1.0/24"
    ip_1 = "223.1.1.100"
    link_1 = my_router.route_packet(ip_1)
    print(f"Routing '{ip_1}':\t -> {link_1} \t(Expected: Link 0)") # [cite: 54]

    # Test 2: Should match "223.1.2.0/24"
    ip_2 = "223.1.2.5"
    link_2 = my_router.route_packet(ip_2)
    print(f"Routing '{ip_2}':\t\t -> {link_2} \t(Expected: Link 1)") # [cite: 57]
    
    # Test 3: Should fail /24 matches, but match "223.1.0.0/16"
    ip_3 = "223.1.250.1"
    link_3 = my_router.route_packet(ip_3)
    print(f"Routing '{ip_3}':\t -> {link_3} \t(Expected: Link 4 (ISP))") # [cite: 58]

    # Test 4: Should match nothing
    ip_4 = "198.51.100.1"
    link_4 = my_router.route_packet(ip_4)
    print(f"Routing '{ip_4}':\t -> {link_4} (Expected: Default Gateway)") # [cite: 59]