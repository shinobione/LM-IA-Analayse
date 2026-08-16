from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse


class NoStoreHandler(SimpleHTTPRequestHandler):
    """Static handler for the SonicTrace local UI.

    The local UI is a runtime/development surface. Serving stale JavaScript after
    an update is worse than the tiny extra local I/O, so responses are
    deliberately non-cacheable.
    """

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description="SonicTrace no-cache local static server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), NoStoreHandler)
    print(f"[frontend] SonicTrace no-cache UI on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
