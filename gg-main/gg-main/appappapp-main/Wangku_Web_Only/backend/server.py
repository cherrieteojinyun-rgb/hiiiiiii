"""Private pilot backend. Host behind an HTTPS reverse proxy; no Gemini key in APK."""
import hmac
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from gemini_service import SYSTEM, CoachError, _request, receipt_payload

TOKENS = [t.strip() for t in os.environ.get('WANGKU_ACCESS_TOKENS', '').split(',') if t.strip()]
GATE = threading.BoundedSemaphore(3)
LOCK = threading.Lock()
USAGE = defaultdict(deque)
LOG = logging.getLogger('wangku.backend')
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        'WANGKU_ALLOWED_ORIGINS',
        'https://cherrieteojinyun-rgb.github.io',
    ).split(',')
    if origin.strip()
}


def validate(data):
    context = data.get('context')
    contents = data.get('contents')
    if not isinstance(context, dict) or not isinstance(contents, list) or not 1 <= len(contents) <= 20:
        raise ValueError()
    clean = []
    for item in contents:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'model'):
            raise ValueError()
        parts = item.get('parts')
        if not isinstance(parts, list) or len(parts) != 1:
            raise ValueError()
        text = parts[0].get('text') if isinstance(parts[0], dict) else None
        if not isinstance(text, str) or not text.strip() or len(text) > 16000:
            raise ValueError()
        clean.append({'role': item['role'], 'parts': [{'text': text}]})
    if clean[0]['role'] != 'user' or clean[-1]['role'] != 'user':
        raise ValueError()
    return {'systemInstruction': {'parts': [{'text': SYSTEM + '\nKonteks kewangan:\n' + json.dumps(context, ensure_ascii=False)}]}, 'contents': clean,
            'generationConfig': {'maxOutputTokens': 1200, 'temperature': 0.4}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Never log chat, credentials or provider error bodies.

    def respond(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Vary', 'Origin')
        origin = self.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        if self.path not in ('/health', '/coach', '/receipt'):
            return self.respond(404, {'error': 'not_found'})
        origin = self.headers.get('Origin')
        requested_method = self.headers.get('Access-Control-Request-Method', '').upper()
        if origin not in ALLOWED_ORIGINS or requested_method not in ('GET', 'POST'):
            return self.respond(403, {'error': 'origin_or_method_not_allowed'})
        requested_headers = {
            header.strip().lower()
            for header in self.headers.get('Access-Control-Request-Headers', '').split(',')
            if header.strip()
        }
        if not requested_headers.issubset({'authorization', 'content-type'}):
            return self.respond(403, {'error': 'headers_not_allowed'})

        self.send_response(204)
        self.send_header('Content-Length', '0')
        self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()

    def do_GET(self):
        self.respond(200 if self.path == '/health' else 404, {'status': 'ok' if self.path == '/health' else 'not_found'})

    def do_POST(self):
        if self.path not in ('/coach', '/receipt'):
            return self.respond(404, {'error': 'not_found'})
        token = self.headers.get('Authorization', '').removeprefix('Bearer ')
        match = next((i for i, expected in enumerate(TOKENS) if hmac.compare_digest(token.encode(), expected.encode())), None)
        if match is None:
            return self.respond(401, {'error': 'unauthorized'})
        with LOCK:
            history = USAGE[match]
            now = time.monotonic()
            while history and now - history[0] >= 3600:
                history.popleft()
            if len(history) >= 60 or sum(now - t < 60 for t in history) >= 6:
                return self.respond(429, {'error': 'rate_limit'})
            history.append(now)
        try:
            is_receipt = self.path == '/receipt'
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= (6 * 1024 * 1024 if is_receipt else 65536):
                return self.respond(413, {'error': 'body_size'})
            self.connection.settimeout(15)
            data = json.loads(self.rfile.read(length))
            payload = receipt_payload(data) if is_receipt else validate(data)
        except (ValueError, TypeError, AttributeError, KeyError, OSError):
            return self.respond(400, {'error': 'invalid_request'})
        if not GATE.acquire(blocking=False):
            return self.respond(503, {
                'error': 'busy',
                'message': 'Pelayan sedang sibuk. Tunggu sebentar sebelum mencuba lagi.',
            })
        try:
            self.respond(200, {'reply': _request(payload)})
        except CoachError as error:
            message = str(error).strip()[:300] or 'Perkhidmatan AI terganggu buat sementara waktu.'
            self.respond(503, {'error': 'provider_unavailable', 'message': message})
        except Exception as error:
            LOG.error('Unexpected error while processing %s: %s', self.path, type(error).__name__)
            self.respond(502, {
                'error': 'upstream_failure',
                'message': 'Backend mengalami ralat tidak dijangka. Semak log Render untuk mengenal pasti punca.',
            })
        finally:
            GATE.release()


if __name__ == '__main__':
    if not TOKENS or not os.environ.get('GEMINI_API_KEY'):
        raise SystemExit('Set WANGKU_ACCESS_TOKENS and GEMINI_API_KEY on the server first.')
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
