import socket

import dns.resolver

# Domain to query
domain = "youtube.com"

# Output log file
log_file = "dns_results.txt"

def log_result(text):
    """Helper function to log results into a file"""
    with open(log_file, "a") as f:
        f.write(text + "\n")
    print(text)

def main():
    # 1. Resolve IP address of the domain
    try:
        ip_address = socket.gethostbyname(domain)
        log_result(f"IP Address of {domain}: {ip_address}")
    except Exception as e:
        log_result(f"Error resolving IP: {e}")

    # 2. Retrieve DNS records
    record_types = ["A", "MX", "CNAME"]
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            for rdata in answers:
                log_result(f"{rtype} Record: {rdata.to_text()}")
        except Exception as e:
            log_result(f"No {rtype} record found: {e}")

    log_result("\n--- DNS Query Completed ---\n")

if __name__ == "__main__":
    main()
