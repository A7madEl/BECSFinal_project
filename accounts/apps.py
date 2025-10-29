from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.exceptions import OperationalError


def create_default_doctor():
    """
    Create default doctor user if it doesn't exist.
    This function is idempotent - safe to call multiple times.
    """
    try:
        from .models import User
        # Check if doctor user already exists
        if not User.objects.filter(username='doctor1').exists():
            User.objects.create_user(
                username='doctor1',
                email='doctor@example.com',
                password='Root1978',
                role=User.Role.DOCTOR,
                first_name='Mahmood',
                last_name='Gneam',
                national_id='1234567890',
                phone='1234567890'
            )
            print("✓ Default doctor user 'doctor1' created successfully!")
    except (OperationalError, Exception):
        # Database might not be ready yet (during migrations)
        pass


def on_post_migrate(sender, **kwargs):
    """
    Callback for post_migrate signal to create doctor after migrations.
    """
    create_default_doctor()


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Set up signal to create default doctor user.
        Also attempts to create on startup if database is ready.
        """
        # Connect signal for post-migration creation
        post_migrate.connect(on_post_migrate, sender=self)
        # Also try to create on startup (if migrations already completed)
        create_default_doctor()