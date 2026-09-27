"""
GraphDB Client for RDF triple store operations.

This module provides a client for uploading RDF graphs to GraphDB (Ontotext)
for semantic query and neuro-symbolic AI applications with OWL 2 reasoning.
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional
from urllib.parse import quote
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GraphDBClient:
    """
    Client for GraphDB (Ontotext) triple store.

    Handles:
    - Graph upload with named graphs (with authentication)
    - SPARQL queries with OWL 2 reasoning
    - Connection health checks
    """

    def __init__(
        self,
        graphdb_url: Optional[str] = None,
        repository: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize GraphDB client.

        Args:
            graphdb_url: Base URL of GraphDB server (default from settings)
            repository: Repository name (default from settings)
            username: GraphDB admin username (default from settings)
            password: GraphDB admin password (default from settings)
        """
        self.graphdb_url = graphdb_url or getattr(settings, 'GRAPHDB_URL', 'http://localhost:17200')
        self.repository = repository or getattr(settings, 'GRAPHDB_REPOSITORY', 'sdc4_rdf')


        # Authentication credentials
        self.username = username or getattr(settings, 'GRAPHDB_USER', 'admin')
        self.password = password or getattr(settings, 'GRAPHDB_PASSWORD', 'admin123')

        # Construct endpoints (GraphDB uses /repositories/{repo}/ pattern)
        self.statements_endpoint = f"{self.graphdb_url}/repositories/{self.repository}/statements"
        self.query_endpoint = f"{self.graphdb_url}/repositories/{self.repository}"

        # Authentication object for requests
        self.auth = HTTPBasicAuth(self.username, self.password)

    def upload_graph(
        self,
        rdf_content: str,
        graph_uri: Optional[str] = None,
        content_type: str = 'text/turtle'
    ) -> bool:
        """
        Upload RDF graph to GraphDB.

        Args:
            rdf_content: RDF content as string (Turtle format by default)
            graph_uri: Named graph URI. If None, uploads to the default graph.
            content_type: MIME type of RDF content

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use HTTP POST to statements endpoint
            url = self.statements_endpoint
            
            # If graph_uri is provided, add context parameter
            # GraphDB requires the context parameter to be a valid N-Triples URI
            # which must be wrapped in angle brackets and URL-encoded
            if graph_uri:
                encoded_context = quote(f'<{graph_uri}>', safe='')
                url = f"{url}?context={encoded_context}"

            headers = {
                'Content-Type': content_type
            }

            response = requests.post(
                url,
                data=rdf_content.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=30
            )

            if response.status_code in [200, 201, 204]:
                target = f"graph <{graph_uri}>" if graph_uri else "default graph"
                logger.info(f"Successfully uploaded to {target}")
                return True
            else:
                target = f"graph <{graph_uri}>" if graph_uri else "default graph"
                logger.error(
                    f"Failed to upload to {target}: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"GraphDB connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading graph: {e}")
            return False

    def upload_graphs(self, graphs) -> bool:
        """
        Upload many named graphs in one request.

        ``graphs`` is a sequence of (graph_uri, turtle) pairs as upload_graph takes them
        one at a time. The Turtle prefixes are hoisted once and every graph's triples go
        inside its own GRAPH block of a TriG document, so a batch of records costs one
        round trip instead of one per record. Returns True when the store accepted the
        whole document; the caller falls back to single uploads otherwise.
        """
        prefixes: dict = {}
        blocks = []
        for graph_uri, turtle in graphs:
            body = []
            for line in turtle.splitlines():
                stripped = line.strip()
                if stripped.startswith('@prefix') or stripped.upper().startswith('PREFIX '):
                    prefixes.setdefault(stripped, None)
                elif stripped:
                    body.append(line)
            blocks.append(f'GRAPH <{graph_uri}> {{\n' + '\n'.join(body) + '\n}\n')
        document = '\n'.join(prefixes) + '\n\n' + '\n'.join(blocks)
        try:
            response = requests.post(
                self.statements_endpoint,
                data=document.encode('utf-8'),
                headers={'Content-Type': 'application/trig'},
                auth=self.auth,
                timeout=120,
            )
            if response.status_code in [200, 201, 204]:
                logger.info(f"Uploaded {len(blocks)} named graphs in one request")
                return True
            logger.error(f"Batch upload of {len(blocks)} graphs refused: Status {response.status_code}, Response: {response.text[:300]}")
            return False
        except requests.RequestException as e:
            logger.error(f"GraphDB connection error on batch upload: {e}")
            return False

    def update_sparql(self, sparql_update: str) -> bool:
        """Run one SPARQL UPDATE against the repository; True when the store accepted it."""
        try:
            response = requests.post(
                self.statements_endpoint,
                data=sparql_update.encode('utf-8'),
                headers={'Content-Type': 'application/sparql-update'},
                auth=self.auth,
                timeout=300,
            )
            if response.status_code in [200, 204]:
                return True
            logger.error(f"SPARQL update refused: Status {response.status_code}, Response: {response.text[:300]}")
            return False
        except requests.RequestException as e:
            logger.error(f"GraphDB connection error on update: {e}")
            return False

    def delete_graph(self, graph_uri: str) -> bool:
        """
        Delete a named graph from GraphDB.

        Args:
            graph_uri: Named graph URI to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # GraphDB uses SPARQL UPDATE for graph deletion
            sparql_update = f"DROP GRAPH <{graph_uri}>"

            headers = {
                'Content-Type': 'application/sparql-update'
            }

            response = requests.post(
                self.statements_endpoint,
                data=sparql_update.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=30
            )

            if response.status_code in [200, 204]:
                logger.info(f"Successfully deleted graph: {graph_uri}")
                return True
            else:
                logger.error(
                    f"Failed to delete graph {graph_uri}: "
                    f"Status {response.status_code}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"GraphDB connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting graph: {e}")
            return False

    def query_sparql(self, sparql_query: str) -> Optional[dict]:
        """
        Execute SPARQL query against GraphDB.

        Note: GraphDB applies OWL 2 RL reasoning automatically based on
        repository configuration.

        Args:
            sparql_query: SPARQL query string

        Returns:
            dict: Query results in JSON format, or None if failed
        """
        try:
            headers = {
                'Content-Type': 'application/sparql-query',
                'Accept': 'application/json'
            }

            # Disable OWL 2 RL reasoning for queries — demo data has all
            # explicit triples; reasoning expands the search space ~70x.
            query_url = f"{self.query_endpoint}?infer=false"

            response = requests.post(
                query_url,
                data=sparql_query.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=300
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"SPARQL query failed: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                return None

        except requests.RequestException as e:
            logger.error(f"GraphDB connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error executing SPARQL query: {e}")
            return None

    def health_check(self) -> bool:
        """
        Check if GraphDB server is reachable.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # GraphDB uses /rest/repositories endpoint for health check
            url = f"{self.graphdb_url}/rest/repositories"

            response = requests.get(url, auth=self.auth, timeout=5)

            return response.status_code == 200

        except requests.RequestException:
            return False
        except Exception:
            return False

    def get_graph_uri(self, instance_id: str, dm_ct_id: str) -> str:
        """
        Generate graph URI for an instance.

        Creates a URN that identifies the graph within the GraphDB repository.

        Args:
            instance_id: Instance ID (e.g., i-abc123)
            dm_ct_id: Data Model CT ID

        Returns:
            str: Graph URI (e.g., urn:sdc4:dm-{ct_id}:{instance_id})
        """
        return f"urn:sdc4:dm-{dm_ct_id}:{instance_id}"

    def get_inferred_statements(self, graph_uri: Optional[str] = None) -> Optional[dict]:
        """
        Get inferred statements from GraphDB's OWL 2 reasoning.

        This is a GraphDB-specific feature that returns statements
        inferred by the OWL 2 RL reasoner.

        Args:
            graph_uri: Optional named graph URI to filter by

        Returns:
            dict: Inferred statements in JSON format, or None if failed
        """
        try:
            # Query for inferred statements using GraphDB's implicit graph
            if graph_uri:
                sparql_query = f"""
                SELECT ?s ?p ?o
                FROM <{graph_uri}>
                FROM <http://www.ontotext.com/implicit>
                WHERE {{ ?s ?p ?o }}
                LIMIT 1000
                """
            else:
                sparql_query = """
                SELECT ?s ?p ?o
                FROM <http://www.ontotext.com/implicit>
                WHERE {{ ?s ?p ?o }}
                LIMIT 1000
                """

            return self.query_sparql(sparql_query)

        except Exception as e:
            logger.error(f"Error getting inferred statements: {e}")
            return None
