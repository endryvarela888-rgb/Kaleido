from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(BASE_DIR / '.env')

from .base import *  # noqa: E402,F401,F403

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Sin dominio/HTTPS todavía (solo IP) — dejamos esto en False por ahora.
# Cuando tengas dominio + Let's Encrypt, cambiá los tres a True.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Buenas prácticas de seguridad que sí podemos activar ya, sin depender de HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'