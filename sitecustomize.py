"""SonicTrace local Python runtime customizations.

Python imports ``sitecustomize`` automatically when it is available on
``sys.path``. The local frontend is launched with ``python -m http.server`` from
the repository root, so this patch makes that development/runtime server emit
strict no-cache headers without changing the backend or the launcher contract.
"""

from __future__ import annotations

try:
    from http.server import SimpleHTTPRequestHandler

    _original_end_headers = SimpleHTTPRequestHandler.end_headers

    if not getattr(_original_end_headers, "__sonictrace_no_store__", False):
        def _sonictrace_end_headers(self: SimpleHTTPRequestHandler) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("X-SonicTrace-Frontend", "fresh-runtime-v3.3.1")
            _original_end_headers(self)

        _sonictrace_end_headers.__sonictrace_no_store__ = True
        SimpleHTTPRequestHandler.end_headers = _sonictrace_end_headers
except Exception:
    # Never block a Python process if the optional frontend patch cannot load.
    pass
