"""Views for the FAIR Data Demo landing page and SPARQL interface."""

import json
from pathlib import Path

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

# Pre-built SPARQL queries loaded from sparql/ directory
SPARQL_DIR = Path(__file__).resolve().parent.parent.parent / "sparql"

CANNED_QUERIES = []
if SPARQL_DIR.exists():
    for rq_file in sorted(SPARQL_DIR.glob("*.rq")):
        CANNED_QUERIES.append(
            {
                "name": rq_file.stem.replace("_", " ").title(),
                "filename": rq_file.name,
                "query": rq_file.read_text(),
            }
        )

STUDIES = [
    {
        "name": "NHANES",
        "full_name": "National Health and Nutrition Examination Survey",
        "funder": "CDC / NCHS",
        "type": "Population Survey",
        "domains": [
            "Demographics",
            "Vital Signs",
            "Lab Results",
            "Biospecimens",
            "Medications",
            "Substance Use",
            "SDOH",
            "Physical Function",
            "Pain",
            "Medical History",
        ],
    },
    {
        "name": "ADNI",
        "full_name": "Alzheimer's Disease Neuroimaging Initiative",
        "funder": "NIA",
        "type": "Longitudinal Cohort",
        "domains": [
            "Demographics",
            "Vital Signs",
            "Lab Results",
            "Biospecimens",
            "Medications",
            "Adverse Events",
            "Cognitive Assessment",
            "Medical History",
        ],
    },
    {
        "name": "SPRINT",
        "full_name": "Systolic Blood Pressure Intervention Trial",
        "funder": "NHLBI",
        "type": "Randomized Trial",
        "domains": [
            "Demographics",
            "Vital Signs",
            "Lab Results",
            "Medications",
            "Adverse Events",
            "Cognitive Assessment",
            "Medical History",
        ],
    },
]

# All 12 NIH CDE domains
ALL_DOMAINS = sorted(
    set(domain for study in STUDIES for domain in study["domains"])
)


def landing(request):
    """Landing page showing study overview and CDE coverage matrix."""
    # Build coverage matrix
    coverage = {}
    for domain in ALL_DOMAINS:
        coverage[domain] = {
            study["name"]: domain in study["domains"] for study in STUDIES
        }

    shared_count = sum(
        1 for domain in ALL_DOMAINS if all(coverage[domain].values())
    )

    context = {
        "studies": STUDIES,
        "all_domains": ALL_DOMAINS,
        "coverage": coverage,
        "shared_count": shared_count,
        "canned_queries": CANNED_QUERIES,
    }
    return render(request, "demo/landing.html", context)


def sparql_query(request):
    """Execute a SPARQL query against GraphDB and return results."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    query = request.POST.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "Empty query"}, status=400)

    endpoint = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"

    try:
        resp = requests.post(
            endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30,
        )
        resp.raise_for_status()
        return JsonResponse(resp.json())
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)
