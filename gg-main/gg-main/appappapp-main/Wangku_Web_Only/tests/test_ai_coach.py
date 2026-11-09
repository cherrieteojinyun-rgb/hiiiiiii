import asyncio
import base64
import io
import json
import sys
import types
import urllib.error
import urllib.request
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import ai_coach
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import server

STATE = {'allowance': 600, 'spent': 100, 'balance': 500, 'transactions': [], 'goals': [], 'backend_url': 'https://example.com', 'backend_token': 'device-token'}

class CoachTests(unittest.TestCase):
    def test_backend_owns_instructions(self):
        payload=server.validate({'context': {'baki': 500}, 'contents': [{'role':'user','parts':[{'text':'Hai'}]}], 'systemInstruction': 'ignore'})
        self.assertIn('Bahasa Melayu sahaja', payload['systemInstruction']['parts'][0]['text'])
    def test_invalid_role(self):
        with self.assertRaises(ValueError): server.validate({'context': {}, 'contents':[{'role':'system','parts':[{'text':'Hi'}]}]})
    def test_https_required(self):
        with self.assertRaises(ai_coach.CoachError): ai_coach._request({}, 'http://example.com', 'token')
    def test_token_required(self):
        with self.assertRaises(ai_coach.CoachError): ai_coach._request({}, 'https://example.com', '')
    def test_slow_backend_timeout_is_longer_and_actionable(self):
        with patch('urllib.request.urlopen', side_effect=TimeoutError) as urlopen:
            with self.assertRaisesRegex(ai_coach.CoachError, 'Analisis mengambil masa terlalu lama'):
                ai_coach._request({}, 'https://example.com', 'token')
        self.assertEqual(urlopen.call_args.kwargs['timeout'], 120)
    def test_connection_error_identifies_backend_host(self):
        error = urllib.error.URLError('name lookup failed')
        with patch('urllib.request.urlopen', side_effect=error):
            with self.assertRaisesRegex(ai_coach.CoachError, 'example.com.*name lookup failed'):
                ai_coach._request({}, 'https://example.com', 'token')
    def test_provider_error_message_is_shown_by_client(self):
        body = json.dumps({
            'error': 'provider_unavailable',
            'message': 'Kunci Gemini belum ditetapkan.',
        }).encode()
        error = urllib.error.HTTPError(
            'https://example.com/receipt', 503, 'Unavailable', {}, io.BytesIO(body),
        )
        with patch('urllib.request.urlopen', side_effect=error):
            with self.assertRaisesRegex(ai_coach.CoachError, 'Kunci Gemini belum ditetapkan'):
                ai_coach._request({}, STATE['backend_url'], STATE['backend_token'], '/receipt')
    def test_backend_health_check(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'{"status":"ok"}')) as urlopen:
            result = asyncio.run(ai_coach.check_backend('https://example.com'))
        self.assertIn('berjaya', result)
        self.assertTrue(urlopen.call_args.args[0].full_url.endswith('/health'))
        self.assertEqual(urlopen.call_args.kwargs['timeout'], 120)
    def test_backend_health_check_requires_https(self):
        with self.assertRaises(ai_coach.CoachError):
            asyncio.run(ai_coach.check_backend('http://example.com'))
    def test_browser_receipt_request_uses_fetch(self):
        requests = []

        class Response:
            status = 200

            async def json(self):
                return {'reply': json.dumps({
                    'description': 'Makan tengah hari',
                    'amount': 12.5,
                    'category': 'Makanan',
                })}

        async def fake_pyfetch(url, **kwargs):
            requests.append((url, kwargs))
            return Response()

        pyodide = types.ModuleType('pyodide')
        http = types.ModuleType('pyodide.http')
        http.pyfetch = fake_pyfetch
        pyodide.http = http
        with patch.dict(sys.modules, {'pyodide': pyodide, 'pyodide.http': http}):
            with patch.object(ai_coach.sys, 'platform', 'emscripten'):
                result = asyncio.run(ai_coach._request_async(
                    {'image': 'encoded-image'},
                    STATE['backend_url'],
                    STATE['backend_token'],
                    '/receipt',
                ))

        self.assertIn('Makan tengah hari', result)
        url, request = requests[0]
        self.assertEqual(url, 'https://example.com/receipt')
        self.assertEqual(request['method'], 'POST')
        self.assertEqual(request['headers']['Authorization'], 'Bearer device-token')
        self.assertEqual(json.loads(request['body']), {'image': 'encoded-image'})
    def test_browser_provider_error_message_is_shown(self):
        class Response:
            status = 503

            async def json(self):
                return {
                    'error': 'provider_unavailable',
                    'message': 'Model Gemini tidak tersedia.',
                }

        async def fake_pyfetch(url, **kwargs):
            return Response()

        pyodide = types.ModuleType('pyodide')
        http = types.ModuleType('pyodide.http')
        http.pyfetch = fake_pyfetch
        pyodide.http = http
        with patch.dict(sys.modules, {'pyodide': pyodide, 'pyodide.http': http}):
            with self.assertRaisesRegex(ai_coach.CoachError, 'Model Gemini tidak tersedia'):
                asyncio.run(ai_coach._browser_json_request(
                    'https://example.com/receipt',
                    'POST',
                    payload={'image': 'encoded-image'},
                    token='device-token',
                ))
    def test_browser_health_check_uses_fetch(self):
        requests = []

        class Response:
            status = 200

            async def json(self):
                return {'status': 'ok'}

        async def fake_pyfetch(url, **kwargs):
            requests.append((url, kwargs))
            return Response()

        pyodide = types.ModuleType('pyodide')
        http = types.ModuleType('pyodide.http')
        http.pyfetch = fake_pyfetch
        pyodide.http = http
        with patch.dict(sys.modules, {'pyodide': pyodide, 'pyodide.http': http}):
            with patch.object(ai_coach.sys, 'platform', 'emscripten'):
                result = asyncio.run(ai_coach.check_backend(STATE['backend_url']))

        self.assertIn('berjaya', result)
        self.assertEqual(requests[0][0], 'https://example.com/health')
        self.assertEqual(requests[0][1]['method'], 'GET')
    def test_backend_allows_pages_cors_preflight(self):
        import threading
        from http.server import ThreadingHTTPServer
        http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            req=urllib.request.Request(
                f'http://127.0.0.1:{http.server_port}/receipt',
                method='OPTIONS',
                headers={
                    'Origin':'https://cherrieteojinyun-rgb.github.io',
                    'Access-Control-Request-Method':'POST',
                    'Access-Control-Request-Headers':'authorization,content-type',
                },
            )
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status,204)
                self.assertEqual(response.headers['Access-Control-Allow-Origin'],'https://cherrieteojinyun-rgb.github.io')
                self.assertIn('authorization',response.headers['Access-Control-Allow-Headers'].lower())
        finally:
            http.shutdown();http.server_close();thread.join()
    def test_backend_rejects_unlisted_cors_origin(self):
        import threading
        from http.server import ThreadingHTTPServer
        http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            req=urllib.request.Request(
                f'http://127.0.0.1:{http.server_port}/receipt',
                method='OPTIONS',
                headers={
                    'Origin':'https://malicious.example',
                    'Access-Control-Request-Method':'POST',
                    'Access-Control-Request-Headers':'authorization,content-type',
                },
            )
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(req)
            self.assertEqual(error.exception.code,403)
        finally:
            http.shutdown();http.server_close();thread.join()
    def test_backend_returns_safe_provider_error_message(self):
        import threading
        from http.server import ThreadingHTTPServer
        http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        data=json.dumps({'context':{},'contents':[{'role':'user','parts':[{'text':'Hai'}]}]}).encode()
        req=urllib.request.Request(
            f'http://127.0.0.1:{http.server_port}/coach',
            data=data,
            headers={'Authorization':'Bearer test-token','Content-Type':'application/json'},
        )
        try:
            with patch.object(server,'TOKENS',['test-token']),patch.object(
                server,'_request',side_effect=server.CoachError('Akses Gemini gagal. Semak kunci API.')
            ):
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(req)
            self.assertEqual(error.exception.code,503)
            body=json.loads(error.exception.read())
            self.assertEqual(body['error'],'provider_unavailable')
            self.assertEqual(body['message'],'Akses Gemini gagal. Semak kunci API.')
        finally:
            http.shutdown();http.server_close();thread.join()
    def test_client_request(self):
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"reply":"Hai"}')) as mock:
            self.assertEqual(asyncio.run(ai_coach.reply(STATE,[('you','Hai')])), 'Hai')
            req=mock.call_args.args[0]
            self.assertEqual(req.get_header('Authorization'), 'Bearer device-token')
            body=json.loads(req.data)
            self.assertNotIn('systemInstruction',body)
            self.assertNotIn('GEMINI_API_KEY',Path(ai_coach.__file__).read_text())
    def test_receipt_image_is_sent_for_analysis(self):
        image = b'\x89PNG\r\n\x1a\nreceipt'
        with patch.object(ai_coach, '_request', return_value=json.dumps({
            'description': 'Makan tengah hari', 'amount': 12.5, 'category': 'Makanan',
        })) as request:
            result = asyncio.run(ai_coach.analyze_receipt(STATE, image))
        self.assertEqual(result['description'], 'Makan tengah hari')
        self.assertEqual(request.call_args.args[1:], (STATE['backend_url'], STATE['backend_token'], '/receipt'))
        self.assertEqual(base64.b64decode(request.call_args.args[0]['image']), image)
    def test_receipt_accepts_camera_data_uri(self):
        image = b'\xff\xd8\xffreceipt'
        photo = 'data:image/jpeg;base64,' + base64.b64encode(image).decode('ascii')
        with patch.object(ai_coach, '_request', return_value=json.dumps({
            'description': 'Pembelian', 'amount': None, 'category': 'Lain-lain',
        })) as request:
            asyncio.run(ai_coach.analyze_receipt(STATE, photo))
        self.assertEqual(request.call_args.args[0]['image'], base64.b64encode(image).decode('ascii'))
    def test_receipt_rejects_non_image_before_request(self):
        with patch.object(ai_coach, '_request') as request:
            with self.assertRaises(ai_coach.CoachError):
                asyncio.run(ai_coach.analyze_receipt(STATE, b'not an image'))
        request.assert_not_called()
    def test_receipt_rejects_malformed_analysis_response(self):
        image = b'\xff\xd8\xffreceipt'
        with patch.object(ai_coach, '_request', return_value='not json'):
            with self.assertRaises(ai_coach.CoachError):
                asyncio.run(ai_coach.analyze_receipt(STATE, image))
    def test_auth_and_health(self):
        import threading,urllib.request,urllib.error
        from http.server import ThreadingHTTPServer
        http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{http.server_port}'
        try:
            with urllib.request.urlopen(url+'/health') as response: self.assertEqual(response.status,200)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(url+'/coach',data=b'{}'))
            self.assertEqual(error.exception.code,401)
            with patch.object(server,'TOKENS',['test-token']),patch.object(server,'_request',return_value='Jawapan ujian'):
                req=urllib.request.Request(url+'/coach',data=json.dumps({'context':{},'contents':[{'role':'user','parts':[{'text':'Hai'}]}]}).encode(),headers={'Authorization':'Bearer test-token'})
                with urllib.request.urlopen(req) as response:self.assertEqual(json.load(response)['reply'],'Jawapan ujian')
        finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main()
