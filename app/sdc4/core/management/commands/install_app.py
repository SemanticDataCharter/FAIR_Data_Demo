"""
Django management command to install a generated DM app from a ZIP file.

Usage:
    python manage.py install_app /path/to/app.zip
    python manage.py install_app /path/to/app.zip --force    # Skip confirmation
    python manage.py install_app /path/to/app.zip --restart   # Auto-restart containers
"""
import subprocess
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from sdc4_shared.utils.app_installer import AppInstaller


class Command(BaseCommand):
    help = 'Install a generated SDC4 DM app from a ZIP archive'

    def add_arguments(self, parser):
        parser.add_argument(
            'zip_file',
            type=str,
            help='Path to the ZIP file containing the generated app'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
        parser.add_argument(
            '--restart',
            action='store_true',
            help='Automatically restart web and celery containers after install'
        )

    def handle(self, *args, **options):
        zip_path = options['zip_file']
        force = options['force']
        restart = options['restart']

        # Validate file exists
        if not Path(zip_path).exists():
            raise CommandError(f"ZIP file not found: {zip_path}")

        self.stdout.write(self.style.MIGRATE_HEADING('\nSDC4 App Installer'))
        self.stdout.write(f"ZIP file: {zip_path}\n")

        # Confirmation prompt
        if not force:
            confirm = input("Proceed with installation? [y/N]: ")
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.WARNING("Installation cancelled."))
                return

        # Run installation
        installer = AppInstaller(zip_path, stdout=self.stdout)
        result = installer.install()

        # Display results
        self.stdout.write("\n" + "="*60)

        if result.success:
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully installed app: {result.app_name}"))

            if result.warnings:
                self.stdout.write(self.style.WARNING("\nWarnings:"))
                for warning in result.warnings:
                    self.stdout.write(f"  - {warning}")

            if restart:
                self.stdout.write("\nRestarting containers...")
                try:
                    subprocess.run(
                        ['docker', 'compose', 'restart', 'web', 'celery'],
                        check=True, capture_output=True, text=True
                    )
                    self.stdout.write(self.style.SUCCESS("Containers restarted successfully."))
                except subprocess.CalledProcessError as e:
                    self.stdout.write(self.style.ERROR(f"Container restart failed: {e.stderr}"))
                    self.stdout.write("Run manually: docker compose restart web celery")
                except FileNotFoundError:
                    self.stdout.write(self.style.ERROR("docker compose not found."))
                    self.stdout.write("Run manually: docker compose restart web celery")
            else:
                self.stdout.write("\nNext steps:")
                self.stdout.write(f"  1. Restart containers: docker compose restart web celery")
                self.stdout.write(f"  2. Visit: http://localhost:18000/{result.app_name}/")
                self.stdout.write(f"  3. Access admin: http://localhost:18000/admin/")
        else:
            self.stdout.write(self.style.ERROR(f"\nInstallation failed!"))
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for error in result.errors:
                self.stdout.write(f"  - {error}")

            if result.warnings:
                self.stdout.write(self.style.WARNING("\nWarnings:"))
                for warning in result.warnings:
                    self.stdout.write(f"  - {warning}")

            raise CommandError("Installation failed. See errors above.")
