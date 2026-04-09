"""Small stdlib HTTP API for Dialectica."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .canonical import canonicalize_logical_form, serialize_logical_form
from .fingerprint import fingerprint_logical_form
from .parser import parse_document, parse_text
from .validation import validate_logical_form


class DialecticaHandler(BaseHTTPRequestHandler):
    server_version = "DialecticaHTTP/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/parse":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        payload = self._read_json_body()
        if not isinstance(payload, dict) or not payload.get("text"):
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Expected JSON body with a non-empty 'text' field"})
            return

        parse_fn = parse_document if bool(payload.get("document")) else parse_text
        parsed = parse_fn(str(payload["text"]), language=str(payload.get("language", "en")))
        canonical = canonicalize_logical_form(parsed)
        errors = validate_logical_form(canonical)
        response: dict[str, Any] = {
            "logical_form": canonical,
            "canonical_text": serialize_logical_form(canonical),
            "structural_fingerprint": fingerprint_logical_form(canonical),
            "validation_errors": errors,
        }
        self._write_json(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _read_json_body(self) -> Any:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b""
        if not raw_body:
            return None
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), DialecticaHandler)
    print(f"Dialectica API listening on http://{host}:{port}")
    server.serve_forever()
