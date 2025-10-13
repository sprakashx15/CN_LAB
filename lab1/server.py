import socket
import threading

SERVER_NAME = "Server of John Q. Smith"
HOST = '0.0.0.0'
PORT = 5050
SERVER_INTEGER = 42

def handle_client(client_socket, client_address):
    with client_socket:
        print(f"[+] Connected by {client_address}")

        data = client_socket.recv(1024).decode()
        if not data:
            print("[-] No data received. Closing connection.")
            return

        try:
            client_name, client_number = data.strip().split('|')
            client_number = int(client_number)
        except ValueError:
            print("[-] Invalid data format.")
            return

        if not (1 <= client_number <= 100):
            print("[-] Invalid number from client. Closing connection.")
            return

        total = client_number + SERVER_INTEGER

        print("\n--- Communication Summary ---")
        print("Client Name:", client_name)
        print("Server Name:", SERVER_NAME)
        print("Client Integer:", client_number)
        print("Server Integer:", SERVER_INTEGER)
        print("Sum:", total)
        print("-----------------------------\n")

        response = f"{SERVER_NAME}|{SERVER_INTEGER}"
        client_socket.sendall(response.encode())

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[+] Server listening on {HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
            print(f"[+] Active threads: {threading.active_count() - 1}")  # Minus main thread

if __name__ == "__main__":
    run_server()
