import http.server
import socketserver
import os
import hashlib
import time
from email.utils import formatdate

PORT = 8000
file = "doc.html"

class CachingHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/" and self.path != f"/{file}":
            self.send_error(404, "File not found please create the file")
            return

        with open(file, "rb") as f:
            content = f.read()

    # generatin a tocken using the hashing library 
        etag = hashlib.md5(content).hexdigest()

    # time that we modified the file
        last_modified_time = os.path.getmtime(file)
        last_modified = formatdate(last_modified_time, usegmt=True)

        client_etag = self.headers.get("If-None-Match")
        client_modified_since = self.headers.get("If-Modified-Since")

    # comaprinng the tag and time
        if (client_etag == etag) or (client_modified_since == last_modified):
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Last-Modified", last_modified)
            self.end_headers()
            return

    # In case of mismatch
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("ETag", etag)
        self.send_header("Last-Modified", last_modified)
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CachingHandler) as httpd:
        print(f"Serving on port {PORT}... (Open http://localhost:{PORT}/)")
        httpd.serve_forever()
