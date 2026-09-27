"""
Django management command to bulk-load all XML instances across all DM apps.

Iterates the DM registry, locates each app's import_data/ directory and
XSD schema, and runs BulkImportProcessor.process_directory() for each.
"""
import importlib
import re
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.loading import BatchLoader
from sdc4_shared.utils.dm_registry import get_dm_registry
from sdc4_shared.utils.graphdb_client import GraphDBClient


def _published_title(xsd_path):
    """The dc:title the published data model carries, or None."""
    try:
        with open(xsd_path, 'r', encoding='utf-8') as fh:
            head = fh.read(20000)
    except OSError:
        return None
    match = re.search(r'<dc:title>(.*?)</dc:title>', head)
    return match.group(1).strip() if match else None


class Command(BaseCommand):
    help = 'Bulk-load all XML instances for every registered data model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Only load data for this specific app (e.g. civil_registry)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing records before importing',
        )
        parser.add_argument(
            '--batch',
            type=int,
            default=200,
            help='Records per database write and per triple-store request (default 200); 0 takes the one-file-at-a-time path',
        )

    def _clear_graphs(self, dm_ct_id):
        """
        Drop this data model's named graphs from the triple store.

        Deleting the rows is not enough. Every load mints fresh instance
        identifiers, so a reload writes new named graphs and leaves the previous
        ones behind. They are unreachable from PostgreSQL and perfectly visible
        to SPARQL, which silently inflates every cross-domain count: six loads of
        this dataset had left 7,272 orphaned graphs against 1,446 live instances.

        Graphs are found by URI prefix rather than from the rows being deleted,
        so orphans from earlier runs are cleaned up too.
        """
        prefix = f'urn:sdc4:dm-{dm_ct_id}:'
        try:
            client = GraphDBClient()
            if not client.health_check():
                self.stdout.write(self.style.WARNING(
                    '  Triple store unreachable; named graphs NOT cleared. '
                    'Cross-domain counts will be inflated until it is rerun.'
                ))
                return 0

            # Listed in batches. An unbounded DISTINCT over every graph in the
            # store scans the whole repository, and on the largest domain that
            # query simply fails, which is how vital statistics ended up holding
            # two generations while every other domain was clean.
            # A model's graphs are dropped by name, up to CHUNK per request: one SPARQL update
            # carrying one DROP per graph. Dropping a graph by its context is cheap for the
            # store, where a DELETE over a pattern across a hundred thousand graphs was not,
            # and one request per graph was the path that took hours. The loop runs until
            # the listing is empty; the per-graph fallback below remains for a store that
            # refuses the batch.
            CHUNK = 1000
            dropped = 0
            for _ in range(500):
                listing = client.query_sparql(
                    'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } '
                    f'FILTER(STRSTARTS(STR(?g), "{prefix}")) }} LIMIT {CHUNK}'
                )
                graphs = [b['g']['value'] for b in (listing or {}).get('results', {}).get('bindings', [])]
                if not graphs:
                    return dropped
                if not client.update_sparql('; '.join(f'DROP SILENT GRAPH <{g}>' for g in graphs)):
                    break   # the per-graph loop below takes over
                dropped += len(graphs)
            for _ in range(200):  # bounded, so a delete that never succeeds cannot spin
                result = client.query_sparql(
                    'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } '
                    f'FILTER(STRSTARTS(STR(?g), "{prefix}")) }} LIMIT 200'
                )
                # A failed listing returns None, which is not the same thing as
                # an empty result. Reporting them the same way is how a silent
                # failure hides.
                if result is None:
                    self.stdout.write(self.style.WARNING(
                        f'  Could not list named graphs for {dm_ct_id}; '
                        f'{dropped} dropped before the listing failed.'
                    ))
                    return dropped

                graphs = [
                    b['g']['value']
                    for b in result.get('results', {}).get('bindings', [])
                ]
                if not graphs:
                    return dropped

                batch = sum(1 for g in graphs if client.delete_graph(g))
                dropped += batch
                if batch == 0:
                    # Nothing in this batch could be deleted; stop rather than
                    # request the same rows forever.
                    self.stdout.write(self.style.WARNING(
                        f'  {len(graphs)} named graphs for {dm_ct_id} refused deletion.'
                    ))
                    return dropped
            self.stdout.write(self.style.WARNING(
                f'  Stopped after 200 batches clearing {dm_ct_id}; {dropped} dropped.'
            ))
            return dropped
        except Exception as exc:  # never block a load on the triple store
            self.stdout.write(self.style.WARNING(
                f'  Could not clear named graphs for {dm_ct_id}: {exc}'
            ))
            return 0

    def _clear_orphan_graphs(self, registry) -> int:
        """
        Drop named graphs of data models this build no longer registers.

        A superseded model's graphs otherwise outlive it: the 4.3.1 models' graphs
        stayed behind a 4.4.0 load and gave one person eleven domains.
        """
        try:
            client = GraphDBClient()
            if not client.health_check():
                return 0
            keep = ' || '.join(f'STRSTARTS(STR(?g), "urn:sdc4:dm-{ct}:")' for ct in registry)
            dropped = 0
            for _ in range(500):
                listing = client.query_sparql(
                    'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } '
                    f'FILTER(STRSTARTS(STR(?g), "urn:sdc4:dm-") && !({keep})) }} LIMIT 1000'
                )
                graphs = [b['g']['value'] for b in (listing or {}).get('results', {}).get('bindings', [])]
                if not graphs:
                    return dropped
                if not client.update_sparql('; '.join(f'DROP SILENT GRAPH <{g}>' for g in graphs)):
                    return dropped
                dropped += len(graphs)
            return dropped
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Orphaned graphs not cleared: {e}'))
            return 0

    def handle(self, *args, **options):
        registry = get_dm_registry()
        filter_app = options.get('app')
        clear = options.get('clear', False)

        total_imported = 0
        total_failed = 0
        total_skipped = 0
        total_invalid = 0
        total_with_ev = 0
        batch = options.get('batch', 200)
        started = time.monotonic()

        for dm_ct_id, model_class in registry.items():
            app_label = model_class._meta.app_label

            if filter_app and app_label != filter_app:
                continue

            if clear:
                count, _ = model_class.objects.all().delete()
                dropped = self._clear_graphs(dm_ct_id)
                note = f'  Cleared {count} existing {app_label} records'
                if dropped:
                    note += f' and {dropped} named graphs'
                self.stdout.write(note)

            # Locate import_data directory
            import_dir = Path(settings.BASE_DIR) / 'import_data' / app_label
            if not import_dir.exists():
                self.stdout.write(
                    self.style.WARNING(f'  No import_data/ for {app_label}, skipping')
                )
                continue

            xml_count = len(list(import_dir.glob('*.xml')))
            if xml_count == 0:
                self.stdout.write(
                    self.style.WARNING(f'  No XML files in {import_dir}, skipping')
                )
                continue

            # Locate XSD schema
            dmlib_dir = Path(settings.MEDIA_ROOT) / 'dmlib'
            xsd_path = dmlib_dir / f'dm-{dm_ct_id}.xsd'
            if not xsd_path.exists():
                self.stdout.write(
                    self.style.ERROR(f'  XSD not found: {xsd_path}')
                )
                continue

            # Import FIELD_METADATA from the app's wizard_config
            try:
                wc = importlib.import_module(f'{app_label}.utils.wizard_config')
                field_metadata = wc.FIELD_METADATA
            except (ImportError, AttributeError) as e:
                self.stdout.write(
                    self.style.ERROR(f'  Cannot load FIELD_METADATA for {app_label}: {e}')
                )
                continue

            # Import the app's BulkImportProcessor
            try:
                bip_mod = importlib.import_module(f'{app_label}.utils.bulk_import')
                BulkImportProcessor = bip_mod.BulkImportProcessor
            except (ImportError, AttributeError) as e:
                self.stdout.write(
                    self.style.ERROR(f'  Cannot load BulkImportProcessor for {app_label}: {e}')
                )
                continue

            # The name asserted on the data model node in every instance's RDF.
            # It must be the model's published title, exactly as the model
            # library states it: the generated constants (DM_LABEL,
            # DMMetadata.TITLE) are code identifiers such as "CivilRegistry",
            # and passing one of those gave every model a second dc:title,
            # which doubled the rows of every query that joined on it.
            dm_label = _published_title(xsd_path) or getattr(model_class, 'DM_LABEL', app_label)

            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f'\n{app_label} ({xml_count} XML files)'
                )
            )

            if batch > 0:
                loader = BatchLoader(app_label, model_class, xsd_path, dm_ct_id, dm_label, field_metadata, batch_size=batch)
                result = loader.load_directory(import_dir)
                self.stdout.write(
                    f'  Imported: {result.successful}  Failed: {result.failed}  Skipped: {result.skipped}  '
                    f'Invalid: {result.invalid}  Stating an absence: {result.with_ev}  Named graphs: {result.graphs}  '
                    f'({result.seconds:.0f}s)'
                )
                for line in result.failures[:5]:
                    self.stdout.write(self.style.ERROR(f'    {line}'))
                total_invalid += result.invalid
                total_with_ev += result.with_ev
            else:
                processor = BulkImportProcessor(
                    model_class=model_class,
                    xsd_path=xsd_path,
                    dm_ct_id=dm_ct_id,
                    dm_label=dm_label,
                    field_metadata=field_metadata,
                )
                result = processor.process_directory(import_dir)
                self.stdout.write(
                    f'  Imported: {result.successful}  '
                    f'Failed: {result.failed}  '
                    f'Skipped: {result.skipped}'
                )
            total_imported += result.successful
            total_failed += result.failed
            total_skipped += result.skipped

        if clear and not filter_app:
            orphans = self._clear_orphan_graphs(registry)
            if orphans:
                self.stdout.write(f'  Dropped {orphans} named graphs of models no longer registered')

        elapsed = time.monotonic() - started
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Imported: {total_imported}  '
                f'Failed: {total_failed}  '
                f'Skipped (duplicates): {total_skipped}'
                + (f'  Invalid: {total_invalid}  Stating an absence: {total_with_ev}' if batch > 0 else '')
                + f'  ({elapsed:.0f}s, {elapsed / 60:.1f} min)'
            )
        )
