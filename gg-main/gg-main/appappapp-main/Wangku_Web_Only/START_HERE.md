# Wangku web app

Extract this ZIP. Open a terminal in the folder containing pyproject.toml.
Use Python 3.12 or later.

Install the web dependencies:

    python -m pip install flet flet-cli flet-web flet-camera flet-charts

Start Wangku:

    python -m flet.cli run --web --host 127.0.0.1 --port 8550 src/main.py

Open http://127.0.0.1:8550 on the same computer and keep the terminal open.
Allow camera access if you want to capture receipts.

## Enable Jurulatih

The web app connects to the Gemini backend over HTTPS. You can use the other
features while the backend is being set up.

The backend/ folder contains a standalone Python service and Dockerfile. Deploy
that folder to a service supporting Docker web services and HTTPS. Configure these
as server secrets/environment settings, never inside source code or browser files:

    GEMINI_API_KEY = your Google API key
    GEMINI_MODEL = gemini-flash-latest (or an available model for your project)
    WANGKU_ACCESS_TOKENS = a long random access token per tester, comma separated
    PORT = the port expected by the hosting provider (default 8080)

Generate a tester token locally with:
    python -c "import secrets; print(secrets.token_urlsafe(32))"

Use a NEW token, never your Gemini key. Host behind provider-managed HTTPS.
The backend responds at GET /health and POST /coach. It does not log request bodies.


In Wangku: Jurulatih > Tetapan AI. Enter your hosted HTTPS base URL (without /coach)
and a tester access token. The URL is saved locally; the access token lasts for the
current app session only. Enter it again after restarting. All interface messages
and AI instructions remain Malay. AI-generated language/accuracy cannot be guaranteed.

This is a private-pilot backend: six attempts per minute and 60 per hour per token,
three concurrent provider calls, 64 KiB request cap, server-owned instructions.
Limits are in memory and per process, reset on restart, and are not shared across
replicas. Use a single instance for this pilot. Tokens are bearer credentials;
revoke a tester by removing their token and restarting. Before public distribution,
add real user authentication, durable shared limits and operational monitoring.
Questions and financial summaries are sent to Google. Do not enter sensitive data.

Run the existing checks with `python -m unittest discover -s tests -v`.

## Automatic receipt analysis

Use the updated frontend and redeploy the updated backend together. The scanner
uses the same HTTPS URL and access token as Jurulatih. Tap Ambil gambar, wait
for Gemini, then review the description, RM total and category before saving.
Use a Gemini model that accepts images and supports structured JSON output.
Manual entry is available if analysis fails or the browser camera extension
returns a browser-only image URL rather than bytes or base64.
