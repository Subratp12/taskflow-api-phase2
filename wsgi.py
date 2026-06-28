"""
WSGI Entry Point — TaskFlow API
─────────────────────────────────
This is the file Gunicorn loads.

Production:  gunicorn -c gunicorn.conf.py wsgi:app
Development: flask run  (uses FLASK_APP=wsgi.py)
"""

import os

from dotenv import load_dotenv

# Load .env before creating the app so all env vars are available
load_dotenv()

from app import create_app  # noqa: E402  (must be after load_dotenv)

app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Development only — Gunicorn is used in production
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(os.environ.get('FLASK_ENV') == 'development'),
    )
