"""Management command to initialize GraphDB repository and load ontologies."""

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize GraphDB repository and load SDC4 ontologies"

    def handle(self, *args, **options):
        base_url = settings.GRAPHDB_URL
        repo_name = settings.GRAPHDB_REPOSITORY

        # Check GraphDB connectivity
        self.stdout.write(f"Connecting to GraphDB at {base_url}...")
        try:
            resp = requests.get(f"{base_url}/rest/repositories", timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Cannot connect to GraphDB: {e}"))
            return

        # Check if repository exists
        repos = [r["id"] for r in resp.json()]
        if repo_name in repos:
            self.stdout.write(
                self.style.WARNING(f"Repository '{repo_name}' already exists.")
            )
        else:
            # Create repository
            self.stdout.write(f"Creating repository '{repo_name}'...")
            config = {
                "id": repo_name,
                "title": "FAIR Data Demo - Cross-Study Knowledge Graph",
                "type": "graphdb",
                "params": {
                    "ruleset": {"value": "owl2-rl"},
                    "disableSameAs": {"value": "true"},
                },
            }
            try:
                resp = requests.put(
                    f"{base_url}/rest/repositories/{repo_name}",
                    json=config,
                    timeout=30,
                )
                resp.raise_for_status()
                self.stdout.write(
                    self.style.SUCCESS(f"Repository '{repo_name}' created.")
                )
            except requests.RequestException as e:
                self.stderr.write(
                    self.style.ERROR(f"Failed to create repository: {e}")
                )
                return

        self.stdout.write(self.style.SUCCESS("GraphDB initialization complete."))
