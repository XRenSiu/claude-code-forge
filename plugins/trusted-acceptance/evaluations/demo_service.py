#!/usr/bin/env python3
"""Synthetic fixture app; deliberately includes a UI-only revocation defect."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer


def serve(variant):
    class Handler(BaseHTTPRequestHandler):
        shared = True

        def log_message(self, *_args):
            pass

        def respond(self, status, body):
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path != "/document":
                return self.respond(404, "unknown path")
            if Handler.shared:
                return self.respond(200, "synthetic document body")
            # Both denials conform to the approved synthetic rule.
            return self.respond(403 if variant == "good" else 404, "access denied")

        def do_POST(self):
            if self.path != "/revoke":
                return self.respond(404, "unknown path")
            if self.headers.get("X-Fixture-Owner") != "synthetic-owner":
                return self.respond(403, "owner required")
            if variant != "ui-only":
                Handler.shared = False
            return self.respond(200, "sharing disabled")

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        print(server.server_port, flush=True)
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=("good", "good-alternative", "ui-only"))
    serve(parser.parse_args().variant)
