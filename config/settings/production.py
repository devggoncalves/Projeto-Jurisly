from .base import *  # noqa: F403
from .base import env

DEBUG = False

# Render injeta RENDER_EXTERNAL_HOSTNAME automaticamente
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host:
    if _render_host not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, _render_host]  # noqa: F405
    _origin = f"https://{_render_host}"
    if _origin not in CSRF_TRUSTED_ORIGINS:  # noqa: F405
        CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, _origin]  # noqa: F405

# Fly.io: FLY_APP_NAME → {app}.fly.dev
_fly_app = env("FLY_APP_NAME", default="")
if _fly_app:
    _fly_host = f"{_fly_app}.fly.dev"
    if _fly_host not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, _fly_host]  # noqa: F405
    _fly_origin = f"https://{_fly_host}"
    if _fly_origin not in CSRF_TRUSTED_ORIGINS:  # noqa: F405
        CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, _fly_origin]  # noqa: F405

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING["root"]["level"] = "INFO"  # noqa: F405
