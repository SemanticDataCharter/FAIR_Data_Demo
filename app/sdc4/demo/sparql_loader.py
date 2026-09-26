"""
Load SPARQL .rq files from the /sparql/ directory.
"""
from pathlib import Path
from django.conf import settings

# Docker mount at /sparql (see docker-compose.yml), fallback to host path
_docker_path = Path('/sparql')
_host_path = settings.BASE_DIR.parent.parent / 'sparql'
SPARQL_DIR = _docker_path if _docker_path.exists() else _host_path

QUERY_CATALOG = {
    1: {
        'file': '01_shared_component_audit.rq',
        'title': 'Shared Component Audit',
        'description': 'Every component that records of more than one study carry: the label, the models, the records. The join, counted by the store.',
        'domains': ['NHANES', 'BRFSS', 'CMS'],
    },
    2: {
        'file': '02_smoking_status_by_study.rq',
        'title': 'Smoking Status by Study',
        'description': 'One component, two questionnaires, one distribution per study with no mapping table.',
        'domains': ['NHANES', 'BRFSS'],
    },
    3: {
        'file': '03_blood_pressure_by_study.rq',
        'title': 'Blood Pressure by Study',
        'description': 'The FHIR systolic, diastolic and heart rate components across the studies that carry them, with their ranges.',
        'domains': ['NHANES', 'BRFSS'],
    },
    4: {
        'file': '04_chronic_conditions_by_study_and_basis.rq',
        'title': 'Chronic Conditions by Study and Basis',
        'description': 'Twenty-one condition indicators, each one component, by study and by the basis the study established it on.',
        'domains': ['NHANES', 'BRFSS', 'CMS'],
    },
    5: {
        'file': '05_medication_coding_by_study.rq',
        'title': 'Medication Coding by Study',
        'description': 'How NHANES and CMS code a medication, and why those two do not join.',
        'domains': ['NHANES', 'CMS'],
    },
    6: {
        'file': '06_demographics_side_by_side.rq',
        'title': 'Demographics Side by Side',
        'description': 'Gender and race/ethnicity as every study carries them, harmonized on the Default and NIH CDE components.',
        'domains': ['NHANES', 'BRFSS', 'CMS'],
    },
}


def load_query(num):
    """Read a single .rq file and return its text."""
    entry = QUERY_CATALOG.get(num)
    if not entry:
        return None
    path = SPARQL_DIR / entry['file']
    if not path.exists():
        return None
    return path.read_text()


def load_all_queries():
    """Return all queries with metadata and SPARQL text."""
    result = {}
    for num, meta in QUERY_CATALOG.items():
        sparql = load_query(num)
        result[num] = {**meta, 'sparql': sparql or ''}
    return result
