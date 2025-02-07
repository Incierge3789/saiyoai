from django.apps import AppConfig


class MySaiyoaiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_saiyoai'

    def ready(self):
        import my_saiyoai.signals  # 追加
