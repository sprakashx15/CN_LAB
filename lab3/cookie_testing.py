import socket
import uuid

HOST = "127.0.0.1"
PORT = 8050

# Dictionary to store sessions {session_id: username} in form of key value pair
sessions = {}

def handle_request(request):
    headers = request.split("\r\n")
    cookie = None
    for header in headers:
        if header.startswith("Cookie:"):
            cookie = header.split(":", 1)[1].strip()

    if cookie and "session_id=" in cookie:
    # if he is visting the site again
        session_id = cookie.split("=")[1]
        username = sessions.get(session_id, "Guest")
        body = f"<h1>Welcome back, {username} you are visiting the site again.!</h1>"
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
            f"{body}"
        )
    else:
    # if cookie not found means visiting the site for first time
        session_id = str(uuid.uuid4())[:8]   # unique short ID
        username = f"User_{len(sessions) + 1}"
        sessions[session_id] = username

        body = f"<h1>Hello {username}, you are on the site for the first time.!</h1>"
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Set-Cookie: session_id={session_id}\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
            f"{body}"
        )
    return response

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Serving on http://{HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                request = conn.recv(1024).decode("utf-8")
                if not request:
                    continue
                print(f"Request from {addr}:\n{request}")

                response = handle_request(request)
                conn.sendall(response.encode("utf-8"))

if __name__ == "__main__":
    start_server()
