import os

from . import schema
from .config import cfg

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")


def main() -> None:
    cfg.validate()
    if cfg.env == "development":
        # Django's own server with auto-reload. Never use it in production.
        from django.core.management import call_command, execute_from_command_line
        if schema.SCHEMA["db"] and cfg.auto_migrate:
            import django
            django.setup()
            call_command("migrate", interactive=False, verbosity=0)
        execute_from_command_line(["manage.py", "runserver", f"{cfg.host}:{cfg.port}"])
    else:
        from waitress import serve
        from .wsgi import application
        serve(application, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
