import socket

# Client details
CLIENT_NAME = "Client of Shubham returns"
SERVER_IP = '127.0.0.1'  # Change this to the server's IP if on different machine
PORT = 5050

def run_client():
    try:
        client_number = int(input("Enter an integer between 1 and 100: "))
        if not (1 <= client_number <= 100):
            print("Invalid number. Must be between 1 and 100.")
            return
    except ValueError:
        print("Invalid input. Please enter an integer.")
        return

    message = f"{CLIENT_NAME}|{client_number}"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        s.sendall(message.encode())

        response = s.recv(2048).decode()
        server_name, server_number = response.strip().split('|')
        server_number = int(server_number)

        total = client_number + server_number

        print("Client Name:", CLIENT_NAME)
        print("Server Name:", server_name)
        print("Client Integer:", client_number)
        print("Server Integer:", server_number)
        print("Sum:", total)
        print("-----------------------------\n")

if __name__ == "__main__":
    run_client()
