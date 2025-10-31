
def ip_to_binary(ip_address: str) -> str:
    """
    Converts a standard dotted-decimal IP address string into a 32-bit binary string.
    
    For example: "192.168.1.1" -> "11000000101010000000000100000001"
    """
    octets = ip_address.split('.')
    
    binary_octets = []
    for octet_str in octets:
        octet_int = int(octet_str)
        
        binary_str = bin(octet_int)
        
        binary_str = binary_str[2:]
        
        padded_binary_str = binary_str.zfill(8)
        
        binary_octets.append(padded_binary_str)
        
    return "".join(binary_octets)

def get_network_prefix(ip_cidr: str) -> str:
    try:
        ip_address, prefix_len_str = ip_cidr.split('/')
    except ValueError:
        return "Invalid CIDR format. Must be 'ip/prefix'."
        
    try:
        prefix_len = int(prefix_len_str)
    except ValueError:
        return "Invalid prefix length."
        
    if not (0 <= prefix_len <= 32):
        return "Prefix length must be between 0 and 32."

    full_binary_ip = ip_to_binary(ip_address)
    
    network_prefix = full_binary_ip[:prefix_len]
    
    return network_prefix

# --- Main execution block for testing ---
if __name__ == "__main__":
    print("--- Testing Part 1: ip_utils.py ---")
    
    
    ip1 = "192.168.1.1"
    binary_ip1 = ip_to_binary(ip1)
    print(f"IP Address: {ip1}")
    print(f"Binary:       {binary_ip1}")
    expected_bin_ip1 = "11000000101010000000000100000001"
    print(f"Expected:     {expected_bin_ip1}")
    print(f"Test Passed:  {binary_ip1 == expected_bin_ip1}\n")

    
    ip2 = "10.0.2.1"
    binary_ip2 = ip_to_binary(ip2)
    print(f"IP Address: {ip2}")
    print(f"Binary:       {binary_ip2}")
    expected_bin_ip2 = "00001010000000000000001000000001"
    print(f"Expected:     {expected_bin_ip2}")
    print(f"Test Passed:  {binary_ip2 == expected_bin_ip2}\n")

   
    cidr1 = "200.23.16.0/23"
    prefix1 = get_network_prefix(cidr1)
    print(f"CIDR:        {cidr1}")
    print(f"Net Prefix:  {prefix1}")
    expected_prefix1 = "11001000000101110001000"
    print(f"Expected:    {expected_prefix1}")
    print(f"Test Passed: {prefix1 == expected_prefix1}\n")


    cidr2 = "223.1.1.0/24" 
    prefix2 = get_network_prefix(cidr2)
    print(f"CIDR:        {cidr2}")
    print(f"Net Prefix:  {prefix2}")
    # 223 -> 11011111
    # 1   -> 00000001
    # 1   -> 00000001
    # 0   -> 00000000
    # Full: 11011111000000010000000100000000
    # /24:  110111110000000100000001
    expected_prefix2 = "110111110000000100000001"
    print(f"Expected:    {expected_prefix2}")
    print(f"Test Passed: {prefix2 == expected_prefix2}\n")