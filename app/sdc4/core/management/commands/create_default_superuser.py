"""
Django management command to create a default superuser if none exists.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a default superuser if no users exist'

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING('Users already exist. Skipping superuser creation.')
            )
            return

        # Create default superuser
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created superuser:\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Password: {password}\n'
                f'\n'
                f'⚠️  IMPORTANT: Change this password in production!'
            )
        )
