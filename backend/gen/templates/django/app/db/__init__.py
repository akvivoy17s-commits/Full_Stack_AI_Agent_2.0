"""Database access through the Django ORM. The adapter exposes the same methods as the adapters of the other generated backends,
so service.py and auth_service.py never know which framework runs them.
get / list_page / create / update / remove / find_one / remove_where / clean / parse_id / ping / migrate / close"""
import os


def connect():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()
    from .django_orm import DjangoDb
    return DjangoDb()
