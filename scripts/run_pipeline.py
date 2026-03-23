#!/usr/bin/env python3
"""
FAIR Data Demo — SDC Agents Pipeline

Seven-step pipeline that uses SDC_Agents toolsets to introspect NIH datasources,
discover/reuse catalog components, and assemble data models via the SDCStudio API.

Usage:
    python scripts/run_pipeline.py --study nhanes|adni|sprint|all [--step N] [--dry-run]

Requires:
    pip install -r requirements-pipeline.txt
    Environment variables: SDCSTUDIO_URL, SDC_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from fair_constants import (
    AE_COMPONENTS,
    ALL_REUSABLE_CT_IDS,
    COLUMN_OVERRIDES,
    SHARED_COMPONENTS,
    STUDIES,
)

# ---------------------------------------------------------------------------
# XPT metadata (SAS labels, value maps)
# ---------------------------------------------------------------------------
# NHANES XPT files carry metadata that CSV loses. The converter saves it as
# sidecar .meta.json files. We load these to give Discovery better column
# descriptions than coded names like BPXSY1.

NHANES_META_DIR = ROOT / "source_data" / "nhanes"


def _load_xpt_metadata(datasource_name: str) -> dict:
    """Load XPT sidecar metadata for a NHANES datasource, if available.

    Returns a dict mapping column names to their SAS metadata:
        {"BPXSY1": {"label": "Systolic: Blood pres (1st rdg) mm Hg", ...}, ...}
    Returns empty dict for non-NHANES datasources or if metadata is missing.
    """
    if not datasource_name.startswith("nhanes_"):
        return {}

    # Map datasource names to XPT filenames
    ds_to_xpt = {
        "nhanes_demographics": "DEMO_J",
        "nhanes_blood_pressure": "BPX_J",
        "nhanes_cbc": "CBC_J",
        "nhanes_cholesterol": "TCHOL_J",
        "nhanes_medications": "RXQ_RX_J",
        "nhanes_medical_conditions": "MCQ_J",
        "nhanes_smoking": "SMQ_J",
        "nhanes_physical_functioning": "PFQ_J",
    }
    xpt_stem = ds_to_xpt.get(datasource_name)
    if not xpt_stem:
        return {}

    meta_path = NHANES_META_DIR / f"{xpt_stem}.meta.json"
    if not meta_path.exists():
        return {}

    meta = json.loads(meta_path.read_text())
    return meta.get("columns", {})

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".sdc-cache"
MODELS_DIR = ROOT / "models"
CONFIG_PATH = ROOT / "sdc-agents.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _banner(step: int, title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print(f"{'='*60}\n")


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _info(msg: str) -> None:
    print(f"  [..] {msg}")


def _fail(msg: str) -> None:
    print(f"  [!!] {msg}", file=sys.stderr)


def _cache_path(study: str, step: str) -> Path:
    """Return cache file path for a study/step combination."""
    d = CACHE_DIR / study
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{step}.json"


def _save_cache(study: str, step: str, data: dict | list) -> None:
    path = _cache_path(study, step)
    path.write_text(json.dumps(data, indent=2, default=str))
    _info(f"Cached: {path}")


def _load_cache(study: str, step: str) -> dict | list | None:
    path = _cache_path(study, step)
    if path.exists():
        return json.loads(path.read_text())
    return None


def _confirm(prompt: str) -> bool:
    """Prompt user for yes/no confirmation."""
    while True:
        answer = input(f"\n  {prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def _load_config():
    """Load SDC Agents configuration."""
    from sdc_agents.common.config import load_config
    return load_config(str(CONFIG_PATH))


# ---------------------------------------------------------------------------
# Step 1 — Introspect
# ---------------------------------------------------------------------------

def step_introspect(study: str, dry_run: bool = False) -> dict:
    """Introspect all datasources for a study using IntrospectToolset."""
    _banner(1, f"Introspect — {study.upper()}")

    cached = _load_cache(study, "introspect")
    if cached:
        _ok(f"Using cached introspection results ({len(cached)} datasources)")
        return cached

    from sdc_agents.toolsets.introspect import IntrospectToolset
    config = _load_config()
    study_meta = STUDIES[study]
    results = {}

    async def _run():
        toolset = IntrospectToolset(config)
        try:
            for ds_name in study_meta["datasets"]:
                _info(f"Introspecting: {ds_name}")
                try:
                    result = await toolset.introspect_csv(ds_name)
                    results[ds_name] = result
                    cols = result.get("columns", [])
                    rows = result.get("row_count", 0)
                    _ok(f"  {len(cols)} columns, {rows} rows")

                    # Load XPT metadata for NHANES to show SAS labels
                    xpt_meta = _load_xpt_metadata(ds_name)
                    for col in cols[:5]:
                        name = col["name"]
                        sas_label = xpt_meta.get(name, {}).get("label", "")
                        label_display = f"  ({sas_label})" if sas_label else ""
                        print(f"    {name:<25} {col['inferred_type']:<12}{label_display}")
                    if len(cols) > 5:
                        print(f"    ... and {len(cols) - 5} more columns")
                except FileNotFoundError:
                    _fail(f"  Source file not found for {ds_name}")
                    _info(f"  Download data per source_data/README.md")
                except Exception as e:
                    _fail(f"  Error introspecting {ds_name}: {e}")
        finally:
            await toolset.close()

    if dry_run:
        _info("Dry run: would introspect the following datasources:")
        for ds_name in study_meta["datasets"]:
            print(f"    {ds_name}")
        return {}

    asyncio.run(_run())

    if results:
        _save_cache(study, "introspect", results)
    return results


# ---------------------------------------------------------------------------
# Step 2 — Verify catalog components
# ---------------------------------------------------------------------------

def step_verify_catalog(study: str) -> dict:
    """Verify that reusable catalog components exist in SDCStudio."""
    _banner(2, f"Verify Catalog — {study.upper()}")

    cached = _load_cache(study, "catalog_verify")
    if cached:
        _ok(f"Using cached catalog verification")
        return cached

    from sdc_agents.toolsets.catalog import CatalogToolset
    config = _load_config()

    # Determine which components this study needs
    components_needed = dict(SHARED_COMPONENTS)
    if study in ("adni", "sprint"):
        components_needed.update(AE_COMPONENTS)

    found = {}
    missing = []

    async def _run():
        toolset = CatalogToolset(config)
        try:
            for key, comp in components_needed.items():
                ct_id = comp["ct_id"]
                try:
                    schema = await toolset.catalog_get_schema(ct_id)
                    found[key] = {
                        "ct_id": ct_id,
                        "label": schema.get("title", comp["label"]),
                        "type": comp["type"],
                        "status": "found",
                    }
                    _ok(f"  {comp['label']} ({ct_id[:12]}...)")
                except Exception:
                    missing.append(key)
                    _fail(f"  {comp['label']} ({ct_id[:12]}...) — NOT FOUND")
        finally:
            await toolset.close()

    asyncio.run(_run())

    result = {"found": found, "missing": missing}
    _save_cache(study, "catalog_verify", result)

    print()
    _ok(f"Found {len(found)}/{len(components_needed)} reusable components")
    if missing:
        _fail(f"Missing {len(missing)}: {', '.join(missing)}")
        _info("Missing components will be minted during assembly (billable)")

    return result


# ---------------------------------------------------------------------------
# Step 3 — Discover components + merge manual overrides
# ---------------------------------------------------------------------------

def _match_sas_label_to_component(sas_label: str) -> dict | None:
    """Try to match a SAS label to a known reusable component.

    Uses case-insensitive substring matching on key terms.
    Returns component dict or None.
    """
    from difflib import SequenceMatcher

    label_lower = sas_label.lower()
    all_components = {**SHARED_COMPONENTS, **AE_COMPONENTS}

    best_match = None
    best_score = 0.0

    for _key, comp in all_components.items():
        comp_label = comp["label"].lower()
        # SequenceMatcher on the SAS label vs component label
        score = SequenceMatcher(None, label_lower, comp_label).ratio()
        if score > best_score:
            best_score = score
            best_match = comp

    # Require a reasonable match (SAS labels are descriptive enough)
    if best_match and best_score > 0.45:
        return {**best_match, "sas_score": round(best_score, 4)}
    return None


def step_discover(study: str, introspection: dict) -> dict:
    """Discover catalog matches for datasource columns, merge manual overrides."""
    _banner(3, f"Discover Components — {study.upper()}")

    cached = _load_cache(study, "discovery")
    if cached:
        _ok(f"Using cached discovery results")
        return cached

    from sdc_agents.toolsets.assembly import AssemblyToolset
    config = _load_config()
    study_meta = STUDIES[study]
    all_matches = {}

    async def _run():
        toolset = AssemblyToolset(config)
        try:
            for ds_name in study_meta["datasets"]:
                if ds_name not in introspection:
                    continue

                _info(f"Discovering components for: {ds_name}")
                result = await toolset.discover_components(ds_name)

                matches = result.get("matches", [])
                matched_cols = {m["column"] for m in matches}
                unmatched = result.get("unmatched", [])

                # Phase 1: Use XPT metadata (SAS labels) to match unmatched
                # coded columns against known components
                xpt_meta = _load_xpt_metadata(ds_name)
                if xpt_meta:
                    sas_matched = 0
                    still_unmatched = []
                    for col_name in list(unmatched):
                        if col_name in matched_cols:
                            continue
                        col_info = xpt_meta.get(col_name, {})
                        sas_label = col_info.get("label", "")
                        if not sas_label:
                            still_unmatched.append(col_name)
                            continue

                        comp = _match_sas_label_to_component(sas_label)
                        if comp:
                            matches.append({
                                "column": col_name,
                                "ct_id": comp["ct_id"],
                                "label": comp["label"],
                                "type": comp["type"],
                                "score": comp["sas_score"],
                                "source": "xpt_metadata",
                                "sas_label": sas_label,
                            })
                            matched_cols.add(col_name)
                            sas_matched += 1
                        else:
                            still_unmatched.append(col_name)
                    unmatched = still_unmatched
                    if sas_matched:
                        _info(f"  {sas_matched} columns matched via SAS labels")

                # Phase 2: Apply manual overrides (highest priority)
                overrides = COLUMN_OVERRIDES.get(ds_name, {})
                for col_name, ct_id in overrides.items():
                    if col_name not in matched_cols:
                        comp = next(
                            (c for c in {**SHARED_COMPONENTS, **AE_COMPONENTS}.values()
                             if c["ct_id"] == ct_id),
                            None,
                        )
                        if comp:
                            matches.append({
                                "column": col_name,
                                "ct_id": ct_id,
                                "label": comp["label"],
                                "type": comp["type"],
                                "score": 1.0,
                                "source": "manual_override",
                            })
                            matched_cols.add(col_name)
                            if col_name in unmatched:
                                unmatched.remove(col_name)
                    else:
                        # Override existing match
                        for m in matches:
                            if m["column"] == col_name:
                                m["ct_id"] = ct_id
                                m["source"] = "manual_override"

                reuse_count = sum(1 for m in matches if m.get("ct_id") in ALL_REUSABLE_CT_IDS)
                mint_count = len(unmatched)
                _ok(f"  {len(matches)} matched ({reuse_count} reuse, {mint_count} mint)")

                all_matches[ds_name] = {
                    "matches": matches,
                    "unmatched": unmatched,
                }
        finally:
            await toolset.close()

    asyncio.run(_run())

    _save_cache(study, "discovery", all_matches)

    # Print match report for human review
    print()
    print("  Match Report")
    print(f"  {'Dataset':<30} {'Auto':<7} {'SAS':<7} {'Manual':<7} {'Unmatched'}")
    print(f"  {'-'*30} {'-'*7} {'-'*7} {'-'*7} {'-'*10}")
    for ds_name, data in all_matches.items():
        matches = data["matches"]
        auto = sum(1 for m in matches if m.get("source") not in ("xpt_metadata", "manual_override"))
        sas = sum(1 for m in matches if m.get("source") == "xpt_metadata")
        manual = sum(1 for m in matches if m.get("source") == "manual_override")
        unmatched = len(data.get("unmatched", []))
        print(f"  {ds_name:<30} {auto:<7} {sas:<7} {manual:<7} {unmatched}")

    if not _confirm("Proceed with these component matches?"):
        _info("Aborted. Edit COLUMN_OVERRIDES in fair_constants.py and re-run.")
        sys.exit(0)

    return all_matches


# ---------------------------------------------------------------------------
# Step 4 — Propose cluster hierarchy
# ---------------------------------------------------------------------------

def step_propose_hierarchy(study: str, discovery: dict) -> dict:
    """Propose cluster hierarchy per study, grouped by CDE domain."""
    _banner(4, f"Propose Cluster Hierarchy — {study.upper()}")

    cached = _load_cache(study, "hierarchy")
    if cached:
        _ok(f"Using cached hierarchy proposal")
        return cached

    from sdc_agents.toolsets.assembly import AssemblyToolset
    config = _load_config()
    study_meta = STUDIES[study]
    hierarchies = {}

    async def _run():
        toolset = AssemblyToolset(config)
        try:
            for ds_name in study_meta["datasets"]:
                if ds_name not in discovery:
                    continue

                ds_data = discovery[ds_name]
                _info(f"Proposing hierarchy for: {ds_name}")

                result = await toolset.propose_cluster_hierarchy(
                    ds_name,
                    component_matches=ds_data["matches"],
                    unmatched_columns=ds_data.get("unmatched"),
                )

                clusters = result.get("cluster_count", 0)
                reuse = result.get("reuse_component_count", 0)
                mint = result.get("new_component_count", 0)
                _ok(f"  {clusters} clusters, {reuse} reuse, {mint} new")

                hierarchies[ds_name] = result
        finally:
            await toolset.close()

    asyncio.run(_run())

    _save_cache(study, "hierarchy", hierarchies)

    # Print hierarchy summary for human review
    print()
    print("  Hierarchy Summary")
    for ds_name, h in hierarchies.items():
        print(f"    {ds_name}:")
        tree = h.get("hierarchy", {})
        if isinstance(tree, dict):
            for cluster_name, cluster_data in tree.items():
                components = cluster_data if isinstance(cluster_data, list) else []
                print(f"      Cluster: {cluster_name} ({len(components)} components)")

    if not _confirm("Proceed with this cluster structure?"):
        _info("Aborted. Adjust hierarchy in SDCStudio and re-run.")
        sys.exit(0)

    return hierarchies


# ---------------------------------------------------------------------------
# Step 5 — Check wallet and estimate cost
# ---------------------------------------------------------------------------

def step_check_wallet(study: str, hierarchies: dict) -> dict:
    """Check wallet balance and estimate assembly cost."""
    _banner(5, f"Wallet Check — {study.upper()}")

    from sdc_agents.toolsets.catalog import CatalogToolset
    config = _load_config()

    wallet_info = {}

    async def _run():
        toolset = CatalogToolset(config)
        try:
            wallet_info.update(await toolset.catalog_check_wallet())
        finally:
            await toolset.close()

    asyncio.run(_run())

    balance = wallet_info.get("balance", 0)
    print(f"  Current balance:   ${balance:.2f}")

    # Estimate cost
    total_new = sum(
        h.get("new_component_count", 0)
        for h in hierarchies.values()
    )
    total_models = len(hierarchies)
    mint_cost = total_new * 0.10
    assembly_cost = total_models * 0.50
    estimated_total = mint_cost + assembly_cost

    print(f"  New components:    {total_new} x $0.10 = ${mint_cost:.2f}")
    print(f"  Model assemblies:  {total_models} x $0.50 = ${assembly_cost:.2f}")
    print(f"  Estimated total:   ${estimated_total:.2f}")
    print()

    if balance < estimated_total:
        _fail(f"Insufficient funds: ${balance:.2f} < ${estimated_total:.2f}")
        _info("Add funds in SDCStudio Settings > Wallet")
        if not _confirm("Continue anyway (wallet may auto-reload)?"):
            sys.exit(0)
    else:
        _ok(f"Sufficient funds: ${balance:.2f} >= ${estimated_total:.2f}")

    if not _confirm("Approve cost and proceed with assembly?"):
        _info("Aborted.")
        sys.exit(0)

    return wallet_info


# ---------------------------------------------------------------------------
# Step 6 — Assemble models
# ---------------------------------------------------------------------------

def step_assemble(study: str, hierarchies: dict) -> dict:
    """Assemble data models via SDCStudio Assembly API."""
    _banner(6, f"Assemble Models — {study.upper()}")

    cached = _load_cache(study, "assembly")
    if cached:
        _ok(f"Using cached assembly results")
        return cached

    from sdc_agents.toolsets.assembly import AssemblyToolset
    config = _load_config()
    study_meta = STUDIES[study]
    results = {}

    async def _run():
        toolset = AssemblyToolset(config)
        try:
            for ds_name, hierarchy in hierarchies.items():
                _info(f"Assembling model for: {ds_name}")

                title = f"{study_meta['label']} — {ds_name.split('_', 1)[-1].replace('_', ' ').title()}"
                description = (
                    f"SDC4 data model for {study_meta['full_name']} "
                    f"({ds_name}) — FAIR Data Demo"
                )

                try:
                    result = await toolset.assemble_model(
                        title=title,
                        description=description,
                        assembly_tree=hierarchy.get("hierarchy", {}),
                    )

                    if result.get("status") == "published":
                        # Pure reuse path (sync)
                        _ok(f"  Published: {result.get('dm_ct_id', 'unknown')}")
                    elif result.get("status") == "processing":
                        # Mixed reuse+mint path (async)
                        task_id = result.get("task_id")
                        _info(f"  Processing: task_id={task_id}")
                        _info(f"  Estimated cost: ${result.get('estimated_cost', 0):.2f}")
                        _info("  Check SDCStudio for completion")

                    results[ds_name] = result

                except Exception as e:
                    error_msg = str(e)
                    if "402" in error_msg or "InsufficientFunds" in error_msg:
                        _fail(f"  Insufficient funds for {ds_name}")
                        _info("  Add funds and re-run from step 6")
                        break
                    _fail(f"  Assembly failed for {ds_name}: {e}")
                    results[ds_name] = {"error": error_msg}
        finally:
            await toolset.close()

    asyncio.run(_run())

    if results:
        _save_cache(study, "assembly", results)

    # Summary
    print()
    published = sum(1 for r in results.values() if r.get("status") == "published")
    processing = sum(1 for r in results.values() if r.get("status") == "processing")
    errors = sum(1 for r in results.values() if r.get("error"))
    print(f"  Published: {published}, Processing: {processing}, Errors: {errors}")

    return results


# ---------------------------------------------------------------------------
# Step 7 — Download schemas and artifacts
# ---------------------------------------------------------------------------

def step_download_artifacts(study: str, assembly_results: dict) -> None:
    """Download generated schemas, RDF, and skeletons to models/{study}/."""
    _banner(7, f"Download Artifacts — {study.upper()}")

    from sdc_agents.toolsets.catalog import CatalogToolset
    config = _load_config()
    study_meta = STUDIES[study]
    output_dir = MODELS_DIR / study_meta["label"]
    output_dir.mkdir(parents=True, exist_ok=True)

    async def _run():
        toolset = CatalogToolset(config)
        try:
            for ds_name, result in assembly_results.items():
                dm_ct_id = result.get("dm_ct_id")
                if not dm_ct_id:
                    _info(f"  Skipping {ds_name} (no dm_ct_id, may still be processing)")
                    continue

                _info(f"Downloading artifacts for: {ds_name} (dm-{dm_ct_id})")

                # Fetch full schema (includes artifact URLs)
                try:
                    schema = await toolset.catalog_get_schema(dm_ct_id)
                    schema_path = output_dir / f"dm-{dm_ct_id}.json"
                    schema_path.write_text(json.dumps(schema, indent=2))
                    _ok(f"  Schema metadata: {schema_path.name}")
                except Exception as e:
                    _fail(f"  Failed to fetch schema: {e}")

                # Download RDF triples
                try:
                    rdf_content = await toolset.catalog_download_schema_rdf(dm_ct_id)
                    rdf_path = output_dir / f"dm-{dm_ct_id}.ttl"
                    rdf_path.write_text(rdf_content)
                    _ok(f"  RDF triples: {rdf_path.name}")
                except Exception as e:
                    _info(f"  RDF not available: {e}")

                # Download XML skeleton
                try:
                    skeleton = await toolset.catalog_download_skeleton(dm_ct_id)
                    skel_path = output_dir / f"dm-{dm_ct_id}_skeleton.xml"
                    skel_path.write_text(skeleton)
                    _ok(f"  Skeleton: {skel_path.name}")
                except Exception as e:
                    _info(f"  Skeleton not available: {e}")

        finally:
            await toolset.close()

    asyncio.run(_run())
    _ok(f"Artifacts saved to {output_dir}/")


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(study: str, start_step: int = 1, dry_run: bool = False) -> None:
    """Run the pipeline for a single study, starting from the given step."""
    study_meta = STUDIES[study]
    print()
    print(f"  FAIR Data Pipeline — {study_meta['label']}")
    print(f"  {'='*40}")
    print(f"  Study:    {study_meta['full_name']}")
    print(f"  Funder:   {study_meta['funder']}")
    print(f"  Datasets: {len(study_meta['datasets'])}")
    print(f"  Domains:  {', '.join(study_meta['cde_domains'])}")

    # Step 1: Introspect
    introspection = {}
    if start_step <= 1:
        introspection = step_introspect(study, dry_run)
        if dry_run:
            _info("Dry run complete.")
            return
    else:
        introspection = _load_cache(study, "introspect") or {}

    # Step 2: Verify catalog
    if start_step <= 2:
        step_verify_catalog(study)

    # Step 3: Discover components (human review)
    discovery = {}
    if start_step <= 3:
        if not introspection:
            introspection = _load_cache(study, "introspect") or {}
        discovery = step_discover(study, introspection)
    else:
        discovery = _load_cache(study, "discovery") or {}

    # Step 4: Propose hierarchy (human review)
    hierarchies = {}
    if start_step <= 4:
        if not discovery:
            discovery = _load_cache(study, "discovery") or {}
        hierarchies = step_propose_hierarchy(study, discovery)
    else:
        hierarchies = _load_cache(study, "hierarchy") or {}

    # Step 5: Check wallet (human approval)
    if start_step <= 5:
        if not hierarchies:
            hierarchies = _load_cache(study, "hierarchy") or {}
        step_check_wallet(study, hierarchies)

    # Step 6: Assemble models
    assembly_results = {}
    if start_step <= 6:
        if not hierarchies:
            hierarchies = _load_cache(study, "hierarchy") or {}
        assembly_results = step_assemble(study, hierarchies)
    else:
        assembly_results = _load_cache(study, "assembly") or {}

    # Step 7: Download artifacts
    if start_step <= 7:
        if not assembly_results:
            assembly_results = _load_cache(study, "assembly") or {}
        step_download_artifacts(study, assembly_results)

    print()
    _ok(f"Pipeline complete for {study_meta['label']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FAIR Data Demo — SDC Agents Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_pipeline.py --study nhanes --step 1 --dry-run
  python scripts/run_pipeline.py --study adni
  python scripts/run_pipeline.py --study all
  python scripts/run_pipeline.py --study sprint --step 6
        """,
    )
    parser.add_argument(
        "--study",
        choices=["nhanes", "adni", "sprint", "all"],
        required=True,
        help="Which study to process (or 'all' for all three)",
    )
    parser.add_argument(
        "--step",
        type=int,
        choices=range(1, 8),
        default=1,
        help="Start from this step (1-7, default: 1). Uses cache for prior steps.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making API calls (step 1 only)",
    )
    args = parser.parse_args()

    studies = list(STUDIES.keys()) if args.study == "all" else [args.study]

    for study in studies:
        run_pipeline(study, start_step=args.step, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
