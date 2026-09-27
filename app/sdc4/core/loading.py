"""
The batch path through a domain's import pipeline.

Each generated app ships a BulkImportProcessor that takes one file at a time
through the same five steps: validate against the published XSD 1.1 schema,
extract the JSON projection, build the model row, extract the RDF, upload it
as its own named graph. Correct, and slow at scale, for two reasons that have
nothing to do with the record: the XSD 1.1 schema is rebuilt for every file,
and every graph is its own HTTP request. This loader keeps the steps and the
app's own utilities, builds the schema once per model, writes rows in batches,
and ships a batch of named graphs in one TriG request. Nothing about what a
record means changes between the two paths; only how many times the same work
is done.
"""
from __future__ import annotations

import importlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    invalid: int = 0
    with_ev: int = 0
    graphs: int = 0
    seconds: float = 0.0
    failures: List[str] = field(default_factory=list)


class BatchLoader:
    def __init__(self, app_label: str, model_class, xsd_path, dm_ct_id: str, dm_label: str, field_metadata, batch_size: int = 200):
        bip = importlib.import_module(f'{app_label}.utils.bulk_import')
        self.has_ev = bip._xml_has_exceptional_value
        # The app's processor supplies the per-file helpers this path reuses unchanged: identifier and
        # timestamp assignment, and the content fingerprint that keeps a reload from writing a record twice.
        self.processor = bip.BulkImportProcessor(model_class=model_class, xsd_path=xsd_path, dm_ct_id=dm_ct_id,
                                                 dm_label=dm_label, field_metadata=field_metadata)
        from sdc4_shared.utils.sdc_validator import SDCValidator
        from sdc4_shared.utils.triplestore import get_triplestore_client
        self.validator = SDCValidator(str(xsd_path))   # the schema is built here, once per model
        self.json_extractor = importlib.import_module(f'{app_label}.utils.json_extractor').JSONExtractor(field_metadata=field_metadata)
        self.json_instance = importlib.import_module(f'{app_label}.utils.json_instance_generator').JSONInstanceGenerator(field_metadata=field_metadata)
        self.rdf_extractor = importlib.import_module(f'{app_label}.utils.rdf_extractor').RDFExtractor(dm_ct_id=dm_ct_id, dm_label=dm_label, field_metadata=field_metadata)
        self.triplestore = get_triplestore_client()
        self.model_class = model_class
        self.dm_ct_id = dm_ct_id
        self.batch_size = max(1, batch_size)

    # ------------------------------------------------------------------ files
    def load_directory(self, directory: Path) -> BatchResult:
        started = time.monotonic()
        result = BatchResult()
        seen = self.processor._build_existing_fingerprints()
        pending: list[tuple[object, str]] = []   # (unsaved row, rdf turtle)
        for xml_file in sorted(Path(directory).glob('*.xml')):
            try:
                raw = xml_file.read_text(encoding='utf-8')
                fp = self.processor._content_fingerprint(raw)
                if fp in seen:
                    result.skipped += 1
                    continue
                seen.add(fp)
                row, rdf = self._prepare(raw)
            except Exception as e:   # one bad file must not stop the load
                logger.error('Error preparing %s: %s', xml_file.name, e)
                result.failed += 1
                result.failures.append(f'{xml_file.name}: {e}')
                continue
            result.invalid += row.validation_status == 'invalid'
            result.with_ev += row.instance_id.startswith('i-ev-')   # a stated absence, whether or not the instance validated
            pending.append((row, rdf))
            if len(pending) >= self.batch_size:
                result.successful += self._flush(pending, result)
                pending = []
        if pending:
            result.successful += self._flush(pending, result)
        result.seconds = time.monotonic() - started
        return result

    def _prepare(self, raw: str):
        has_ev = self.has_ev(raw)
        xml, instance_id = self.processor._assign_new_instance_id(raw, has_ev)
        xml = self.processor._update_creation_timestamp(xml)
        verdict = self.validator.validate(xml)
        status = 'valid_with_ev' if has_ev else 'valid'
        errors = {}
        if not verdict.is_valid:
            status, errors = 'invalid', verdict.errors
        extracted = self.json_extractor.extract(xml)
        row = self.model_class(instance_id=instance_id, xml_content=xml, json_instance=self.json_instance.generate(xml),
                               search_text=extracted['search_text'], validation_status=status, validation_errors=errors)
        rdf = self.rdf_extractor.extract(xml_content=xml, instance_id=instance_id, validation_status=status, auto_corrected_fields=[]) or ''
        return row, rdf

    # ------------------------------------------------------------------ batches
    def _flush(self, pending, result: BatchResult) -> int:
        rows = [row for row, _ in pending]
        self.model_class.objects.bulk_create(rows, batch_size=self.batch_size)
        if self.triplestore is None:
            for row in rows:
                row.rdf_sync_status = 'disabled'
            self.model_class.objects.bulk_update(rows, ['rdf_sync_status'], batch_size=self.batch_size)
            return len(rows)
        graphs = [(self.triplestore.get_graph_uri(row.instance_id, self.dm_ct_id), rdf) for row, rdf in pending if rdf]
        ok = self.triplestore.upload_graphs(graphs) if graphs else True
        if not ok:   # one request refused: fall back to one graph per request so a single bad graph is the only loss
            ok_uris = {uri for uri, rdf in graphs if self.triplestore.upload_graph(rdf, uri)}
        else:
            ok_uris = {uri for uri, _ in graphs}
        now = timezone.now()
        for row, rdf in pending:
            uri = self.triplestore.get_graph_uri(row.instance_id, self.dm_ct_id)
            if rdf and uri in ok_uris:
                row.fuseki_graph_uri, row.rdf_uploaded_at, row.rdf_sync_status = uri, now, 'synced'
                result.graphs += 1
            else:
                row.rdf_sync_status = 'failed'
        self.model_class.objects.bulk_update(rows, ['fuseki_graph_uri', 'rdf_uploaded_at', 'rdf_sync_status'], batch_size=self.batch_size)
        return len(rows)
