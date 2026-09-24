from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


class Bridge:
    """Local bridge. It does not access browser cookies or authentication tokens."""

    def __init__(self, host="127.0.0.1", port=18923):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.jobs = []

    def start(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def reply(self, code, data):
                raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.path == "/health":
                    return self.reply(200, {"ok": True, "service": "Hn38videoAItool"})
                if self.path == "/jobs":
                    return self.reply(200, {"jobs": bridge.jobs})
                return self.reply(404, {"error": "not_found"})

            def do_POST(self):
                if self.path != "/jobs":
                    return self.reply(404, {"error": "not_found"})
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except Exception:
                    return self.reply(400, {"error": "invalid_json"})
                bridge.jobs.append(payload)
                return self.reply(200, {"ok": True, "job": payload})

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
