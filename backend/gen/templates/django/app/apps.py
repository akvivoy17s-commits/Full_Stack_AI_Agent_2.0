from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "app"
    label = "app"
    default_auto_field = "django.db.models.AutoField"   # 32-bit ids, the same range every generated backend accepts
