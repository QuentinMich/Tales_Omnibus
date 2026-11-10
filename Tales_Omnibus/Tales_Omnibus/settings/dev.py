from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-#3)u(=fzkf@t1@*bj9dr$%r)(i%k#9us^8p&wj^58rw%y^$-4j"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

try:
    from .local import *
except ImportError:
    pass
