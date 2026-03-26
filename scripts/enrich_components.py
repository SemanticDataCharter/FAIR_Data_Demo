#!/usr/bin/env python3
"""
Enrich unpublished FAIR Data Demo components.

One-off script that:
1. Lists all unpublished components from the project via API
2. Maps each component back to its source column using cached discovery data
3. Loads enrichment metadata from NHANES sidecars, BRFSS HTML codebook, CMS definitions
4. PATCHes each component with improved label, description, constraints, and semantic links

Usage:
    python scripts/enrich_components.py [--study nhanes|brfss|cms|all] [--dry-run] [--semantic-only] [--skip-semantic]

Examples:
    # Dry run for NHANES only
    python scripts/enrich_components.py --study nhanes --dry-run

    # Enrich all studies
    python scripts/enrich_components.py --study all

    # Only add semantic links (no label/description/constraint changes)
    python scripts/enrich_components.py --study all --semantic-only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure scripts/ is on path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from enrichment.api_client import SDCStudioClient, TYPE_ENDPOINT_MAP
from enrichment.component_mapper import (
    EnrichmentTask,
    load_discovery_index,
    map_components_to_columns,
)
from enrichment.metadata_nhanes import NHANESColumnMeta, load_nhanes_metadata
from enrichment.metadata_brfss import BRFSSColumnMeta, load_brfss_metadata
from enrichment.metadata_cms import CMSColumnMeta, load_cms_metadata
from enrichment.semantic_mappings import (
    COLUMN_SEMANTIC_MAPPINGS,
    DOMAIN_SUBJECTS,
    NEW_NAMESPACES,
    PREDICATES_NEEDED,
    SOURCE_REFERENCES,
    SemanticLink,
)

logger = logging.getLogger(__name__)

PROJECT_CT_ID = "zmeucc8optakg3rnti5bmhf3"
REPORT_PATH = Path(__file__).resolve().parent / "enrichment_report.json"

# Types that support enumeration fields
ENUM_TYPES = {"XdString", "XdToken"}
# Types that support magnitude constraints
MAGNITUDE_TYPES = {"XdCount", "XdQuantity", "XdFloat", "XdDouble"}


def build_patch_payload(
    task: EnrichmentTask,
    nhanes_meta: dict[str, NHANESColumnMeta],
    brfss_meta: dict[str, BRFSSColumnMeta],
    cms_meta: dict[str, CMSColumnMeta],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Build a PATCH payload for a component based on its source metadata.

    Returns empty dict if no changes needed.
    """
    payload: dict[str, Any] = {}
    col = task.column_name

    current_label = current.get("label", "")
    current_desc = current.get("description", "")

    if task.study == "nhanes":
        meta = nhanes_meta.get(col)
        if not meta:
            return {}

        # Label: prefer sidecar label over current (raw column name)
        if meta.label and meta.label != current_label:
            payload["label"] = meta.label

        # Description: add study context prefix if not already present
        if meta.description:
            enriched_desc = f"NHANES 2017-2018: {meta.description}"
            if not current_desc.startswith("NHANES 2017-2018:") and enriched_desc != current_desc:
                payload["description"] = enriched_desc

        # Enumerations (for XdString/XdToken types)
        if meta.enums and task.component_type in ENUM_TYPES:
            current_enums = current.get("enums", "")
            if not current_enums:
                enum_values = list(meta.enums.values())
                enum_keys = list(meta.enums.keys())
                payload["enums"] = "\n".join(enum_values)
                payload["enum_descr"] = "\n".join(
                    f"{k}: {v}" for k, v in zip(enum_keys, enum_values)
                )

    elif task.study == "brfss":
        meta = brfss_meta.get(col)
        if not meta:
            return {}

        # Label
        if meta.label and meta.label != current_label:
            payload["label"] = meta.label

        # Description: combine question + section for rich context
        parts = []
        if meta.question:
            parts.append(meta.question)
        if meta.section:
            parts.append(f"Section: {meta.section}")
        if meta.question_prologue:
            parts.append(f"Note: {meta.question_prologue}")
        if parts:
            enriched_desc = "BRFSS 2022: " + ". ".join(parts)
            if not current_desc.startswith("BRFSS 2022:") and enriched_desc != current_desc:
                payload["description"] = enriched_desc

        # Enumerations
        if meta.value_labels and task.component_type in ENUM_TYPES:
            current_enums = current.get("enums", "")
            if not current_enums:
                enum_values = list(meta.value_labels.values())
                enum_keys = list(meta.value_labels.keys())
                payload["enums"] = "\n".join(enum_values)
                payload["enum_descr"] = "\n".join(
                    f"{k}: {v}" for k, v in zip(enum_keys, enum_values)
                )

    elif task.study == "cms":
        meta = cms_meta.get(col)
        if not meta:
            return {}

        if meta.label and meta.label != current_label:
            payload["label"] = meta.label

        if meta.description and meta.description != current_desc:
            payload["description"] = meta.description

        if meta.enums and task.component_type in ENUM_TYPES:
            current_enums = current.get("enums", "")
            if not current_enums:
                enum_values = list(meta.enums.values())
                enum_keys = list(meta.enums.keys())
                payload["enums"] = "\n".join(enum_values)
                payload["enum_descr"] = "\n".join(
                    f"{k}: {v}" for k, v in zip(enum_keys, enum_values)
                )

    return payload


async def ensure_namespaces(client: SDCStudioClient) -> dict[str, int]:
    """Ensure required namespaces exist. Returns abbrev → id mapping.

    Checks both abbreviation and URI to handle cases where a namespace
    URI already exists under a different abbreviation (e.g., SNOMED
    registered as abbrev 'id' instead of 'snomed').
    """
    existing = await client.list_namespaces()
    abbrev_map: dict[str, int] = {}
    uri_map: dict[str, tuple[str, int]] = {}  # uri → (abbrev, id)
    for ns in existing:
        abbrev_map[ns["abbrev"]] = ns["id"]
        uri_map[ns["uri"]] = (ns["abbrev"], ns["id"])

    for abbrev, uri in NEW_NAMESPACES.items():
        if abbrev in abbrev_map:
            logger.debug("Namespace %s already exists (id=%d)", abbrev, abbrev_map[abbrev])
        elif uri in uri_map:
            existing_abbrev, existing_id = uri_map[uri]
            logger.info(
                "Namespace URI %s already registered as '%s' (id=%d), skipping '%s'",
                uri, existing_abbrev, existing_id, abbrev,
            )
            abbrev_map[abbrev] = existing_id  # alias for downstream use
        else:
            logger.info("Creating namespace: %s → %s", abbrev, uri)
            result = await client.create_namespace(abbrev, uri)
            abbrev_map[abbrev] = result["id"]
            logger.info("Created namespace %s (id=%d)", abbrev, result["id"])

    return abbrev_map


async def ensure_predicates(
    client: SDCStudioClient,
    ns_map: dict[str, int],
) -> dict[tuple[str, str], int]:
    """Ensure required predicates exist. Returns (ns_prefix, class_name) → id mapping."""
    existing = await client.list_predicates()
    pred_map: dict[tuple[str, str], int] = {}
    for pred in existing:
        # API returns ns_prefix (string abbrev) and class_name
        ns_prefix = pred.get("ns_prefix", "")
        class_name = pred.get("class_name", "")
        if ns_prefix and class_name:
            pred_map[(ns_prefix, class_name)] = pred["id"]

    for ns_abbrev, name in PREDICATES_NEEDED:
        key = (ns_abbrev, name)
        if key not in pred_map:
            ns_id = ns_map.get(ns_abbrev)
            if ns_id is None:
                logger.warning("Namespace '%s' not found, cannot create predicate %s:%s", ns_abbrev, ns_abbrev, name)
                continue
            logger.info("Creating predicate: %s:%s (ns_id=%d)", ns_abbrev, name, ns_id)
            result = await client.create_predicate(ns_id, name)
            pred_map[key] = result["id"]
            logger.info("Created predicate %s:%s (id=%d)", ns_abbrev, name, result["id"])

    return pred_map


async def ensure_predobj(
    client: SDCStudioClient,
    pred_map: dict[tuple[str, str], int],
    existing_predobjs: list[dict],
    link: SemanticLink,
) -> int | None:
    """Ensure a PredObj exists. Returns its id, or None if predicate not found."""
    pred_key = (link.predicate_ns, link.predicate_name)
    pred_id = pred_map.get(pred_key)
    if pred_id is None:
        logger.warning("Predicate %s:%s not found", link.predicate_ns, link.predicate_name)
        return None

    # Check if already exists (match by predicate + object_uri)
    for po in existing_predobjs:
        if po.get("predicate") == pred_id and po.get("object_uri") == link.object_uri:
            return po["id"]

    # Create new
    result = await client.create_predobj(
        predicate_id=pred_id,
        object_uri=link.object_uri,
        po_name=link.po_name,
        project_ct_id=PROJECT_CT_ID,
    )
    existing_predobjs.append(result)  # Update local cache
    return result["id"]


async def enrich_one(
    client: SDCStudioClient,
    task: EnrichmentTask,
    nhanes_meta: dict[str, NHANESColumnMeta],
    brfss_meta: dict[str, BRFSSColumnMeta],
    cms_meta: dict[str, CMSColumnMeta],
    pred_map: dict[tuple[str, str], int],
    existing_predobjs: list[dict],
    dry_run: bool = False,
    semantic_only: bool = False,
    skip_semantic: bool = False,
) -> dict[str, Any]:
    """Enrich a single component. Returns a result dict for the report."""
    result = {
        "ct_id": task.ct_id,
        "column": task.column_name,
        "study": task.study,
        "dataset": task.dataset,
        "type": task.component_type,
        "status": "skipped",
        "changes": {},
    }

    try:
        # Fetch current component state
        current = await client.get_component(task.component_type, task.ct_id)

        # Build content patch payload
        patch: dict[str, Any] = {}
        if not semantic_only:
            patch = build_patch_payload(task, nhanes_meta, brfss_meta, cms_meta, current)

        # Idempotency check: skip if label already differs from raw column name
        # (means it was already enriched in a prior run)
        cur_label = current.get("label", "")
        if not semantic_only and cur_label and cur_label != task.column_name:
            # Label already changed from the raw column name — likely already enriched
            if not patch:
                result["status"] = "already_enriched"
                return result

        # Collect semantic link PredObj IDs
        predobj_ids: list[int] = list(current.get("pred_obj", []))
        semantic_added = 0

        if not skip_semantic:
            # Per-column semantic links
            col_links = COLUMN_SEMANTIC_MAPPINGS.get(task.column_name, [])
            for link in col_links:
                po_id = await ensure_predobj(client, pred_map, existing_predobjs, link)
                if po_id and po_id not in predobj_ids:
                    predobj_ids.append(po_id)
                    semantic_added += 1

            # Domain-level subject link
            domain_link = DOMAIN_SUBJECTS.get(task.dataset)
            if domain_link:
                po_id = await ensure_predobj(client, pred_map, existing_predobjs, domain_link)
                if po_id and po_id not in predobj_ids:
                    predobj_ids.append(po_id)
                    semantic_added += 1

            # Source reference link
            source_link = SOURCE_REFERENCES.get(task.study)
            if source_link:
                po_id = await ensure_predobj(client, pred_map, existing_predobjs, source_link)
                if po_id and po_id not in predobj_ids:
                    predobj_ids.append(po_id)
                    semantic_added += 1

            if semantic_added > 0:
                patch["pred_obj"] = predobj_ids

        if not patch:
            result["status"] = "no_changes"
            return result

        result["changes"] = {
            k: v for k, v in patch.items()
            if k != "pred_obj"
        }
        if semantic_added > 0:
            result["changes"]["semantic_links_added"] = semantic_added

        if dry_run:
            result["status"] = "dry_run"
            logger.info(
                "[DRY RUN] Would PATCH %s %s: %s",
                task.component_type, task.ct_id, json.dumps(result["changes"], indent=2),
            )
            return result

        # Apply the PATCH
        await client.patch_component(task.component_type, task.ct_id, patch)
        result["status"] = "enriched"
        logger.info(
            "Enriched %s %s (%s) — %d changes",
            task.component_type, task.ct_id, task.column_name, len(patch),
        )

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error("Error enriching %s %s: %s", task.ct_id, task.column_name, e)

    return result


async def run(args: argparse.Namespace) -> None:
    """Main enrichment pipeline."""
    studies = None if args.study == "all" else [args.study]
    study_label = args.study.upper() if args.study != "all" else "ALL"

    logger.info("=" * 60)
    logger.info("FAIR Data Demo Component Enrichment")
    logger.info("Study: %s | Dry run: %s | Semantic only: %s | Skip semantic: %s",
                study_label, args.dry_run, args.semantic_only, args.skip_semantic)
    logger.info("=" * 60)

    # Load metadata sources
    logger.info("Loading metadata sources...")
    nhanes_meta = load_nhanes_metadata() if not studies or "nhanes" in studies else {}
    brfss_meta = load_brfss_metadata() if not studies or "brfss" in studies else {}
    cms_meta = load_cms_metadata() if not studies or "cms" in studies else {}

    # Load discovery index
    logger.info("Loading discovery cache...")
    index = load_discovery_index(studies)

    async with SDCStudioClient() as client:
        # Ensure namespaces and predicates
        if not args.skip_semantic:
            logger.info("Ensuring namespaces and predicates...")
            ns_map = await ensure_namespaces(client)
            pred_map = await ensure_predicates(client, ns_map)
            existing_predobjs = await client.list_predobjs(PROJECT_CT_ID)
        else:
            pred_map = {}
            existing_predobjs = []

        # Fetch unpublished components
        logger.info("Fetching unpublished components for project %s...", PROJECT_CT_ID)
        components = await client.list_components(PROJECT_CT_ID, published=False)
        logger.info("Found %d unpublished components", len(components))

        # Map to source columns
        tasks, unmapped = map_components_to_columns(components, index, studies)
        logger.info("Mapped %d components, %d unmapped", len(tasks), len(unmapped))

        # Enrich each component
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "study": args.study,
            "dry_run": args.dry_run,
            "total_unpublished": len(components),
            "mapped": len(tasks),
            "unmapped": len(unmapped),
            "results": [],
            "summary": {},
        }

        for i, task in enumerate(tasks, 1):
            logger.info("[%d/%d] Processing %s (%s)", i, len(tasks), task.column_name, task.ct_id)
            result = await enrich_one(
                client, task, nhanes_meta, brfss_meta, cms_meta,
                pred_map, existing_predobjs,
                dry_run=args.dry_run,
                semantic_only=args.semantic_only,
                skip_semantic=args.skip_semantic,
            )
            report["results"].append(result)

        # Summarize
        statuses: dict[str, int] = {}
        for r in report["results"]:
            s = r["status"]
            statuses[s] = statuses.get(s, 0) + 1
        report["summary"] = statuses

        # Write report
        with open(REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("=" * 60)
        logger.info("Enrichment complete. Summary:")
        for status, count in sorted(statuses.items()):
            logger.info("  %s: %d", status, count)
        logger.info("Report written to: %s", REPORT_PATH)
        logger.info("Unmapped components: %d (logged below)", len(unmapped))
        for comp in unmapped[:20]:
            logger.info("  Unmapped: %s (type=%s, label=%s)",
                        comp.get("ct_id"), comp.get("type"), comp.get("label"))
        if len(unmapped) > 20:
            logger.info("  ... and %d more", len(unmapped) - 20)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich unpublished FAIR Data Demo components",
    )
    parser.add_argument(
        "--study",
        choices=["nhanes", "brfss", "cms", "all"],
        default="all",
        help="Which study to enrich (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log proposed changes without making API calls",
    )
    parser.add_argument(
        "--semantic-only",
        action="store_true",
        help="Only add semantic links (skip label/description/constraint updates)",
    )
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Skip semantic link processing",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
