#!/usr/bin/env python3
"""CodeXplorer — mini VS Code dans le navigateur.
Usage: python tools/codexplorer.py [chemin_dossier]
"""
import http.server
import json
import os
import socket
import sys
import webbrowser
from pathlib import Path

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
HTML_FILE = Path(__file__).parent / "codexplorer.html"
PORT = int(os.environ.get("CODEXPLORER_PORT", 0))


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_FILE.read_bytes())
        elif self.path == "/codexplorer.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_FILE.read_bytes())
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.read(length)) if length else {}
        if self.path == "/api/files/list":
            self._handle_list(body)
        elif self.path == "/api/files/read":
            self._handle_read(body)
        else:
            self.send_error(404)

    def _handle_list(self, body):
        dir_path = body.get("path", ".")
        full = os.path.join(ROOT, dir_path) if dir_path != "." else ROOT
        try:
            items = []
            for name in sorted(os.listdir(full), key=lambda x: (not os.path.isdir(os.path.join(full, x)), x.lower())):
                fpath = os.path.join(full, name)
                items.append({
                    "name": name,
                    "path": os.path.relpath(fpath, ROOT),
                    "is_dir": os.path.isdir(fpath),
                    "size": os.path.getsize(fpath) if os.path.isfile(fpath) else 0,
                })
            self._json(items)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_read(self, body):
        file_path = body.get("path", "")
        full = os.path.join(ROOT, file_path)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._json({"content": content, "path": file_path})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


if __name__ == "__main__":
    port = PORT or find_free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"CodeXplorer ouvert sur {url}")
    print(f"Dossier racine : {ROOT}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")
        server.server_close()
