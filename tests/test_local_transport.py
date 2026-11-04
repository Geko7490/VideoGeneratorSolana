import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from vex.local_ai import request


def test_direct_loopback_transport_and_loading_errors(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'{"status":"loading"}')

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"received": payload}).encode())

        def log_message(self, *args):
            pass

    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        port = server.server_port
        assert request(port, "/v1/chat/completions", {"story": "local only"}) == {"received": {"story": "local only"}}
        with pytest.raises(OSError, match="503"):
            request(port, "/health")
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
