from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') + [
    '.onrender.com',
    'localhost',
]

# Render terminates SSL at its load balancer — don't redirect internally
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', ''
).split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []

# Allow any *.onrender.com subdomain so POST/PUT/DELETE work regardless
# of which Render service name the frontend gets assigned
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.onrender\.com$",
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]

# Also honour the explicit list from the env var (e.g. custom domains)
_extra = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if _extra:
    CORS_ALLOWED_ORIGINS = _extra.split(',')
