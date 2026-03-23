#!/usr/bin/env python3
"""
FAIR Data Demo — Post-Assembly XML Instance Generation

After models are assembled and approved in SDCStudio, this script generates
XML instances from source CSV data using the GeneratorToolset and optionally
validates them via VaaS.

Usage:
    python scripts/generate_instances.py --study nhanes|adni|sprint|all
                                         [--validate] [--limit N]

Requires:
    pip install -r requirements-pipeline.txt
    Completed assembly (run_pipeline.py steps 1-7)
    Source data files downloaded per source_data/README.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from fair_constants import STUDIES

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".sdc-cache"
OUTPUT_DIR = ROOT / "output" / "instances"
CONFIG_PATH = ROOT / "sdc-agents.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _banner(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _info(msg: str) -> None:
    print(f"  [..] {msg}")


def _fail(msg: str) -> None:
    print(f"  [!!] {msg}", file=sys.stderr)


def _load_config():
    from sdc_agents.common.config import load_config
    return load_config(str(CONFIG_PATH))


def _load_cache(study: str, step: str) -> dict | list | None:
    path = CACHE_DIR / study / f"{step}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


# ---------------------------------------------------------------------------
# Generate instances for a study
# ---------------------------------------------------------------------------

def generate_study(study: str, validate: bool = False, limit: int = 100) -> dict:
    """Generate XML instances for all datasources in a study."""
    _banner(f"Generate Instances — {study.upper()}")

    study_meta = STUDIES[study]

    # Check that mappings exist (created during pipeline)
    assembly = _load_cache(study, "assembly")
    if not assembly:
        _fail(f"No assembly results found for {study}. Run the pipeline first.")
        return {"error": "no_assembly"}

    from sdc_agents.toolsets.generator import GeneratorToolset
    config = _load_config()

    study_output = OUTPUT_DIR / study
    study_output.mkdir(parents=True, exist_ok=True)

    results = {}

    async def _run():
        toolset = GeneratorToolset(config)
        try:
            for ds_name in study_meta["datasets"]:
                _info(f"Generating instances for: {ds_name}")

                try:
                    result = await toolset.generate_batch(
                        mapping_name=ds_name,
                        limit=limit,
                    )

                    count = result.get("count", 0)
                    errors = result.get("errors", [])
                    _ok(f"  Generated {count} instances")
                    if errors:
                        _info(f"  {len(errors)} errors during generation")
                        for err in errors[:3]:
                            print(f"    {err}")

                    results[ds_name] = {
                        "count": count,
                        "errors": len(errors),
                        "output_dir": str(result.get("output_dir", study_output)),
                    }

                except Exception as e:
                    _fail(f"  Generation failed for {ds_name}: {e}")
                    results[ds_name] = {"error": str(e)}
        finally:
            await toolset.close()

    asyncio.run(_run())

    # Print summary
    print()
    total = sum(r.get("count", 0) for r in results.values())
    total_errors = sum(r.get("errors", 0) for r in results.values())
    _ok(f"Total: {total} instances generated, {total_errors} errors")

    return results


# ---------------------------------------------------------------------------
# Validate instances for a study
# ---------------------------------------------------------------------------

def validate_study(study: str) -> dict:
    """Validate all generated XML instances for a study via VaaS."""
    _banner(f"Validate Instances — {study.upper()}")

    study_output = OUTPUT_DIR / study
    if not study_output.exists():
        _fail(f"No generated instances found at {study_output}")
        return {"error": "no_instances"}

    from sdc_agents.toolsets.validation import ValidationToolset
    config = _load_config()

    result = {}

    async def _run():
        toolset = ValidationToolset(config)
        try:
            batch_result = await toolset.validate_batch(
                xml_dir=str(study_output),
            )
            result.update(batch_result)
        finally:
            await toolset.close()

    asyncio.run(_run())

    count = result.get("count", 0)
    failed = result.get("failed", 0)
    print(f"  Validated: {count}")
    print(f"  Failed:    {failed}")

    if result.get("halt_reason"):
        _fail(f"Validation halted: {result['halt_reason']}")
        pending = result.get("pending_files", [])
        if pending:
            _info(f"  {len(pending)} files remaining")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FAIR Data Demo — Generate XML instances from assembled models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_instances.py --study nhanes
  python scripts/generate_instances.py --study all --validate
  python scripts/generate_instances.py --study adni --limit 50
        """,
    )
    parser.add_argument(
        "--study",
        choices=["nhanes", "adni", "sprint", "all"],
        required=True,
        help="Which study to generate instances for",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated instances via VaaS after generation",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum rows to generate per datasource (default: 100)",
    )
    args = parser.parse_args()

    studies = list(STUDIES.keys()) if args.study == "all" else [args.study]

    for study in studies:
        generate_study(study, validate=args.validate, limit=args.limit)

        if args.validate:
            validate_study(study)

    print()
    _ok("Done!")


if __name__ == "__main__":
    main()
