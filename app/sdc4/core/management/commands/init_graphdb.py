"""
Django management command to initialize GraphDB RDF store.

Creates the default repository and loads SDC4 ontologies.
GraphDB provides OWL 2 reasoning capabilities.

GraphDB 10.x requires Turtle (.ttl) configuration files for repository creation.
See: https://graphdb.ontotext.com/documentation/10.8/manage-repos-with-restapi.html
"""
import io
import os
import time
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Initialize GraphDB RDF store with SDC4 repository and ontologies'

    def handle(self, *args, **options):
        graphdb_url = getattr(settings, 'GRAPHDB_URL', 'http://graphdb:7200')
        repository = getattr(settings, 'GRAPHDB_REPOSITORY', 'sdc4_rdf')

        # GraphDB credentials
        graphdb_user = os.environ.get('GRAPHDB_USER', 'admin')
        graphdb_password = os.environ.get('GRAPHDB_PASSWORD', 'admin123')
        auth = (graphdb_user, graphdb_password)

        # Wait for GraphDB to be ready (up to 120 seconds - GraphDB takes longer to start)
        self.stdout.write('Waiting for GraphDB to be ready...')
        for i in range(120):
            try:
                response = requests.get(f"{graphdb_url}/rest/repositories", timeout=5)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('GraphDB is ready!'))
                    time.sleep(1)
                    break
            except requests.exceptions.RequestException:
                if i % 10 == 0 and i > 0:
                    self.stdout.write(f'  Still waiting... ({i}s elapsed)')
            time.sleep(1)
        else:
            self.stdout.write(
                self.style.WARNING(
                    'GraphDB did not respond in time. Continuing anyway - '
                    'you may need to run this command again after GraphDB is fully started.'
                )
            )
            return

        # Check if repository exists
        self.stdout.write(f'Checking if repository "{repository}" exists...')
        try:
            response = requests.get(f"{graphdb_url}/rest/repositories", timeout=10)
            if response.status_code == 200:
                repos = response.json()
                repo_exists = any(r.get('id') == repository for r in repos)

                if repo_exists:
                    self.stdout.write(
                        self.style.SUCCESS(f'Repository "{repository}" already exists!')
                    )
                else:
                    # Create the repository using TTL config file (GraphDB 10.x format)
                    self.stdout.write(f'Creating repository "{repository}"...')
                    repo_config_ttl = self._get_repository_config_ttl(repository)

                    # GraphDB 10.x requires multipart form data with TTL config file
                    files = {
                        'config': ('repo-config.ttl', io.BytesIO(repo_config_ttl.encode('utf-8')), 'text/turtle')
                    }
                    response = requests.post(
                        f"{graphdb_url}/rest/repositories",
                        auth=auth,
                        files=files,
                        timeout=30
                    )
                    if response.status_code in [200, 201, 204]:
                        self.stdout.write(
                            self.style.SUCCESS(f'Repository "{repository}" created successfully!')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to create repository: {response.status_code} - {response.text}'
                            )
                        )
                        return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking/creating repository: {e}'))
            return

        # Load SDC4 ontologies
        self.stdout.write(self.style.MIGRATE_HEADING('\nLoading SDC4 Ontologies'))
        ontologies_dir = Path(settings.BASE_DIR) / 'ontologies'
        ontology_files = [
            ('sdc4.ttl', 'SDC4 core ontology'),
            ('sdc4-meta.ttl', 'SDC4 metadata ontology'),
        ]

        for filename, description in ontology_files:
            ontology_path = ontologies_dir / filename

            if not ontology_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'Ontology file not found: {ontology_path}')
                )
                continue

            self.stdout.write(f'Loading {description} ({filename})...')

            content_type = 'text/turtle' if filename.endswith('.ttl') else 'application/rdf+xml'

            try:
                with open(ontology_path, 'rb') as f:
                    # GraphDB uses /repositories/{repo}/statements endpoint for data upload
                    response = requests.post(
                        f"{graphdb_url}/repositories/{repository}/statements",
                        headers={'Content-Type': content_type},
                        auth=auth,
                        data=f.read(),
                        timeout=30
                    )

                if response.status_code in [200, 201, 204]:
                    self.stdout.write(self.style.SUCCESS(f'Loaded {filename} successfully!'))
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to load {filename}: {response.status_code} - {response.text}'
                        )
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading {filename}: {e}'))

        # Load Data Model RDF schemas
        self.stdout.write(self.style.MIGRATE_HEADING('\nLoading Data Model RDF Schemas'))

        dm_schemas_loaded = 0

        def load_rdf_files(dmlib_dir, source_label):
            nonlocal dm_schemas_loaded
            if not dmlib_dir.exists():
                return

            dm_files = list(dmlib_dir.glob('dm-*.rdf')) + list(dmlib_dir.glob('dm-*.ttl'))

            for dm_file in dm_files:
                self.stdout.write(f'Loading DM schema: {dm_file.name} from {source_label}...')

                content_type = 'text/turtle' if dm_file.suffix == '.ttl' else 'application/rdf+xml'

                try:
                    with open(dm_file, 'rb') as f:
                        response = requests.post(
                            f"{graphdb_url}/repositories/{repository}/statements",
                            headers={'Content-Type': content_type},
                            auth=auth,
                            data=f.read(),
                            timeout=30
                        )

                    if response.status_code in [200, 201, 204]:
                        self.stdout.write(self.style.SUCCESS(f'Loaded {dm_file.name} successfully!'))
                        dm_schemas_loaded += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to load {dm_file.name}: {response.status_code} - {response.text}'
                            )
                        )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error loading {dm_file.name}: {e}'))

        project_dmlib = Path(settings.BASE_DIR) / 'mediafiles' / 'dmlib'
        load_rdf_files(project_dmlib, 'project root')

        if dm_schemas_loaded == 0:
            self.stdout.write(
                self.style.WARNING('No Data Model RDF schemas found.')
            )
            self.stdout.write(f'  DM schemas should be in: {project_dmlib}/dm-*.ttl')
        else:
            self.stdout.write(self.style.SUCCESS(f'\nLoaded {dm_schemas_loaded} Data Model schema(s)'))

        self.stdout.write(self.style.SUCCESS('\nGraphDB initialization complete!'))
        self.stdout.write(f'Repository URL: {graphdb_url}/repositories/{repository}')
        self.stdout.write(f'Workbench URL: {graphdb_url}')

    def _get_repository_config_ttl(self, repo_id):
        """
        Return GraphDB 10.x repository configuration in Turtle format with OWL 2 RL reasoning.

        GraphDB 10.x uses:
        - rep:repositoryType "graphdb:SailRepository"
        - sail:sailType "graphdb:Sail"
        - graphdb: prefix for configuration parameters

        See: https://graphdb.ontotext.com/documentation/10.8/manage-repos-with-restapi.html
        """
        return f'''@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix rep: <http://www.openrdf.org/config/repository#>.
@prefix sr: <http://www.openrdf.org/config/repository/sail#>.
@prefix sail: <http://www.openrdf.org/config/sail#>.
@prefix graphdb: <http://www.ontotext.com/config/graphdb#>.

[] a rep:Repository ;
    rep:repositoryID "{repo_id}" ;
    rdfs:label "{repo_id} - SDC4 Repository with OWL 2 RL Reasoning" ;
    rep:repositoryImpl [
        rep:repositoryType "graphdb:SailRepository" ;
        sr:sailImpl [
            sail:sailType "graphdb:Sail" ;

            graphdb:base-URL "http://sdc4.net/dm#" ;
            graphdb:defaultNS "" ;
            graphdb:entity-index-size "10000000" ;
            graphdb:entity-id-size "32" ;
            graphdb:imports "" ;
            graphdb:repository-type "file-repository" ;
            graphdb:ruleset "owl2-rl" ;
            graphdb:storage-folder "storage" ;

            graphdb:enable-context-index "true" ;
            graphdb:enablePredicateList "true" ;
            graphdb:in-memory-literal-properties "true" ;
            graphdb:enable-literal-index "true" ;

            graphdb:check-for-inconsistencies "false" ;
            graphdb:disable-sameAs "true" ;
            graphdb:query-timeout "0" ;
            graphdb:query-limit-results "0" ;
            graphdb:throw-QueryEvaluationException-on-timeout "false" ;
            graphdb:read-only "false" ;
        ]
    ].
'''
