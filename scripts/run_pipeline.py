#!/usr/bin/env python3
"""
FAIR Data Demo — SDC Agents Pipeline

Seven-step pipeline that uses SDC_Agents toolsets to introspect federal health
datasources, discover/reuse catalog components, and assemble data models via
the SDCStudio API.

Usage:
    python scripts/run_pipeline.py --study nhanes|brfss|cms|all [--step N] [--dry-run]

Requires:
    pip install -r requirements-pipeline.txt
    .env file or environment variables: SDCSTUDIO_URL, SDC_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env before anything reads os.environ

from fair_constants import (
    ALL_REUSABLE_CT_IDS,
    COLUMN_OVERRIDES,
    SHARED_COMPONENTS,
    STUDIES,
)

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


def _demo_reuse_summary(total_matched: int, total_unmatched: int) -> None:
    """Print a highlighted reuse summary banner when all components are catalog matches."""
    if total_unmatched > 0:
        return
    lines = [
        f"  All {total_matched} components matched existing catalog entries.",
        "  0 new components to mint.",
        "  These components were originally built from 3 federal",
        "  datasets using 3 different metadata formats.",
        "  Now they are permanently reusable at zero cost.",
    ]
    width = 59
    print()
    print(f"  ┌{'─' * width}┐")
    print(f"  │  {'REUSE SUMMARY':<{width - 2}}│")
    for line in lines:
        # Strip leading 2 spaces since we add our own padding
        text = line.strip()
        print(f"  │  {text:<{width - 2}}│")
    print(f"  └{'─' * width}┘")




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
        for ds_name in study_meta["datasets"]:
            _info(f"Introspecting: {ds_name}")
            try:
                result = await toolset.introspect_csv(ds_name)
                results[ds_name] = result
                cols = result.get("columns", [])
                rows = result.get("row_count", 0)
                _ok(f"  {len(cols)} columns, {rows} rows")

                for col in cols[:5]:
                    name = col["name"]
                    desc = col.get("description", "")
                    desc_display = f"  ({desc})" if desc else ""
                    print(f"    {name:<25} {col['data_type']:<12}{desc_display}")
                if len(cols) > 5:
                    print(f"    ... and {len(cols) - 5} more columns")
            except FileNotFoundError:
                _fail(f"  Source file not found for {ds_name}")
                _info(f"  Download data per source_data/README.md")
            except Exception as e:
                _fail(f"  Error introspecting {ds_name}: {e}")

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

    # Skip verification when no ct_ids are populated yet
    components_needed = {
        k: v for k, v in SHARED_COMPONENTS.items() if v.get("ct_id")
    }
    if not components_needed:
        _info("No ct_ids configured in SHARED_COMPONENTS — skipping verification")
        _info("Catalog-first discovery (4.3.1+) will find matches by keyword")
        result: dict = {"found": {}, "missing": []}
        _save_cache(study, "catalog_verify", result)
        return result

    from sdc_agents.toolsets.catalog import CatalogToolset
    config = _load_config()

    found = {}
    missing = []

    async def _run():
        toolset = CatalogToolset(config)
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
        for ds_name in study_meta["datasets"]:
            if ds_name not in introspection:
                continue

            _info(f"Discovering components for: {ds_name}")
            # project_ct_id auto-fetched from Modeler API by toolset
            result = await toolset.discover_components(ds_name)

            matches = result.get("matches", [])
            matched_cols = {m["column"] for m in matches}
            unmatched = result.get("unmatched", [])
            catalog_hits = result.get("catalog_matches", 0)

            # Apply manual overrides (highest priority fallback)
            overrides = COLUMN_OVERRIDES.get(ds_name, {})
            for col_name, ct_id in overrides.items():
                if not ct_id:
                    continue  # Skip empty ct_ids
                if col_name not in matched_cols:
                    comp = next(
                        (c for c in SHARED_COMPONENTS.values()
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
            _ok(f"  {len(matches)} matched ({catalog_hits} catalog, {reuse_count} reuse, {mint_count} mint)")

            all_matches[ds_name] = {
                "matches": matches,
                "unmatched": unmatched,
            }

    asyncio.run(_run())

    _save_cache(study, "discovery", all_matches)

    # Print match report for human review
    print()
    print("  Match Report")
    print(f"  {'Dataset':<30} {'Auto':<7} {'Manual':<7} {'Unmatched'}")
    print(f"  {'-'*30} {'-'*7} {'-'*7} {'-'*10}")
    total_matched = 0
    total_unmatched = 0
    for ds_name, data in all_matches.items():
        matches = data["matches"]
        auto = sum(1 for m in matches if m.get("source") != "manual_override")
        manual = sum(1 for m in matches if m.get("source") == "manual_override")
        unmatched = len(data.get("unmatched", []))
        total_matched += len(matches)
        total_unmatched += unmatched
        print(f"  {ds_name:<30} {auto:<7} {manual:<7} {unmatched}")

    _demo_reuse_summary(total_matched, total_unmatched)

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
        for ds_name in study_meta["datasets"]:
            if ds_name not in discovery:
                continue

            ds_data = discovery[ds_name]
            _info(f"Proposing hierarchy for: {ds_name}")

            unmatched = ds_data.get("unmatched", [])

            result = await toolset.propose_cluster_hierarchy(
                ds_name,
                component_matches=ds_data["matches"],
                unmatched_columns=unmatched,
            )

            clusters = result.get("cluster_count", 0)
            reuse = result.get("reuse_component_count", 0)
            mint = result.get("new_component_count", 0)
            _ok(f"  {clusters} clusters, {reuse} reuse, {mint} new")

            hierarchies[ds_name] = result

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
        wallet_info.update(await toolset.catalog_check_wallet())

    asyncio.run(_run())

    balance = float(wallet_info.get("balance", 0))
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

    print()
    print(f"  Cost breakdown:")
    print(f"    New components:    {total_new} x $0.10 = ${mint_cost:.2f}")
    print(f"    Model assemblies:  {total_models} x $0.50 = ${assembly_cost:.2f}")
    print(f"    Estimated total:   ${estimated_total:.2f}")
    print()

    if mint_cost == 0:
        _ok("The catalog did all the work. Minting cost: $0.00")
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
                    _info(f"  Estimated cost: ${float(result.get('estimated_cost', 0)):.2f}")
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

    print()
    _info(f"{len(assembly_results)} model(s) submitted. Complete these steps in SDCStudio:")
    _info("  1. Review the assembled components and clusters")
    _info("  2. Edit component details as needed (descriptions, constraints, units)")
    _info("  3. Publish all components and clusters")
    _info("  4. Generate and download the data model package")
    _info("  5. Generate and download the application")
    print()
    _info("See SDCStudio documentation for details on generating packages and apps.")
    _ok("Pipeline complete — remaining steps are in SDCStudio.")


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
  python scripts/run_pipeline.py --study brfss
  python scripts/run_pipeline.py --study all
  python scripts/run_pipeline.py --study cms --step 6
        """,
    )
    parser.add_argument(
        "--study",
        choices=["nhanes", "brfss", "cms", "all"],
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
