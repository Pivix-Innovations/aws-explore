from django.apps import AppConfig


class ScannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scanner'

    def ready(self):
        # Import services to ensure registration
        import scanner.services.ec2
