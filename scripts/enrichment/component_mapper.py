"""
Maps API components to source columns via discovery cache.

Discovery cache structure per study:
  {dataset_name: {matches: [...], unmatched: [...]}}

- matches: reused catalog components (already enriched, skip)
- unmatched: columns that got minted as new components (enrich these)

Minted component labels are derived from the column name during assembly.
We match by normalizing both the component label and the unmatched column name.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from enrichment.api_client import TYPE_NORMALIZE

logger = logging.getLogger(__name__)

CACHE_ROOT = Path(__file__).resolve().parent.parent.parent / ".sdc-cache"

# Study name → discovery cache file
STUDY_CACHE_FILES = {
    "nhanes": CACHE_ROOT / "nhanes" / "discovery.json",
    "brfss": CACHE_ROOT / "brfss" / "discovery.json",
    "cms": CACHE_ROOT / "cms" / "discovery.json",
}

# Dataset name → study mapping
DATASET_TO_STUDY = {
    "nhanes_demographics": "nhanes",
    "nhanes_blood_pressure": "nhanes",
    "nhanes_cbc": "nhanes",
    "nhanes_cholesterol": "nhanes",
    "nhanes_medications": "nhanes",
    "nhanes_medical_conditions": "nhanes",
    "nhanes_smoking": "nhanes",
    "nhanes_physical_functioning": "nhanes",
    "brfss": "brfss",
    "cms_beneficiary": "cms",
    "cms_inpatient": "cms",
    "cms_outpatient": "cms",
    "cms_prescriptions": "cms",
}

# Dataset name → NHANES sidecar filename mapping
DATASET_TO_SIDECAR = {
    "nhanes_demographics": "DEMO_J.json",
    "nhanes_blood_pressure": "BPX_J.json",
    "nhanes_cbc": "CBC_J.json",
    "nhanes_cholesterol": "TCHOL_J.json",
    "nhanes_medications": "RXQ_RX_J.json",
    "nhanes_medical_conditions": "MCQ_J.json",
    "nhanes_smoking": "SMQ_J.json",
    "nhanes_physical_functioning": "PFQ_J.json",
}


def _normalize(name: str) -> str:
    """Normalize a column/label name for matching."""
    return re.sub(r"[-_ ]", "", name).lower()


@dataclass
class EnrichmentTask:
    """Represents a component that needs enrichment."""
    ct_id: str
    component_type: str
    current_label: str
    column_name: str
    study: str
    dataset: str


@dataclass
class DiscoveryIndex:
    """Index of unmatched columns from discovery cache."""
    # normalized_column → list of {study, dataset, column_name, data_type, description}
    unmatched: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    # Set of matched ct_ids (reused from catalog; skip these)
    matched_ct_ids: set[str] = field(default_factory=set)


def load_discovery_index(studies: list[str] | None = None) -> DiscoveryIndex:
    """Load discovery caches and build a reverse lookup index.

    Args:
        studies: List of study names to load. None = all.

    Returns:
        DiscoveryIndex with unmatched column lookup and matched ct_id set.
    """
    index = DiscoveryIndex()
    target_studies = studies or list(STUDY_CACHE_FILES.keys())

    for study in target_studies:
        cache_file = STUDY_CACHE_FILES.get(study)
        if not cache_file or not cache_file.exists():
            logger.warning("Discovery cache not found for %s: %s", study, cache_file)
            continue

        with open(cache_file) as f:
            data = json.load(f)

        for dataset_name, dataset_data in data.items():
            # Track matched ct_ids (reused components — skip)
            for match in dataset_data.get("matches", []):
                ct_id = match.get("ct_id")
                if ct_id:
                    index.matched_ct_ids.add(ct_id)

            # Build lookup for unmatched (minted) columns
            for col in dataset_data.get("unmatched", []):
                col_name = col.get("name", "")
                if not col_name:
                    continue
                norm = _normalize(col_name)
                entry = {
                    "study": study,
                    "dataset": dataset_name,
                    "column_name": col_name,
                    "data_type": col.get("data_type", ""),
                    "description": col.get("description", ""),
                }
                index.unmatched.setdefault(norm, []).append(entry)

    logger.info(
        "Discovery index: %d unmatched columns, %d matched ct_ids",
        len(index.unmatched), len(index.matched_ct_ids),
    )
    return index


def map_components_to_columns(
    components: list[dict[str, Any]],
    index: DiscoveryIndex,
    studies: list[str] | None = None,
) -> tuple[list[EnrichmentTask], list[dict]]:
    """Map fetched API components to source columns.

    Args:
        components: List of component dicts from the API.
        index: Pre-built discovery index.
        studies: Optional filter to only map components from specific studies.

    Returns:
        Tuple of (enrichment_tasks, unmatched_components).
    """
    tasks: list[EnrichmentTask] = []
    unmatched: list[dict] = []
    target_studies = set(studies) if studies else None

    for comp in components:
        ct_id = comp.get("ct_id", "")
        raw_type = comp.get("type", "")
        comp_type = TYPE_NORMALIZE.get(raw_type, raw_type)
        label = comp.get("label", "")

        # Skip components that were reused from catalog
        if ct_id in index.matched_ct_ids:
            continue

        # Try to match label to an unmatched column name
        norm_label = _normalize(label)
        candidates = index.unmatched.get(norm_label, [])

        if not candidates:
            unmatched.append(comp)
            continue

        # Filter by study if specified
        if target_studies:
            candidates = [c for c in candidates if c["study"] in target_studies]
            if not candidates:
                unmatched.append(comp)
                continue

        # Use first match (columns should be unique per study)
        match = candidates[0]
        tasks.append(EnrichmentTask(
            ct_id=ct_id,
            component_type=comp_type,
            current_label=label,
            column_name=match["column_name"],
            study=match["study"],
            dataset=match["dataset"],
        ))

    logger.info(
        "Component mapping: %d enrichable, %d unmatched",
        len(tasks), len(unmatched),
    )
    return tasks, unmatched
