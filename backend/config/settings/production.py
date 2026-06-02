from .base import *
import os

DEBUG = False

# Render sets the service URL automatically — add it plus any custom domain
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') + [
    '.onrender.com',
    'localhost',
]

# Render terminates SSL at the load balancer, so never redirect internally
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
