import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402  (the settings module must be named first)

from . import schema  # noqa: E402
from .config import cfg  # noqa: E402

application = get_wsgi_application()
if schema.SCHEMA["db"] and cfg.auto_migrate:
    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)
