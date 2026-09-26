"""
Six-beat walk-through: three federal studies, one component library.
"""

BEATS = [
    {
        'number': 1,
        'title': 'The audit: what the studies share',
        'query_number': 1,
        'icon': 'bi-diagram-3',
        'color': 'primary',
        'narrative': (
            'Three federal studies, three agencies, three file formats. The first build of this '
            'demonstration could not make them share a single component. This one composes them from '
            'the same component libraries, so the store can be asked directly: which components do '
            'records of more than one study carry, and how many records carry each? The answer is a '
            'table the query computes, not a claim a README makes.'
        ),
        'query_label': 'Run the audit',
    },
    {
        'number': 2,
        'title': 'Smoking status, two questionnaires, one component',
        'query_number': 2,
        'icon': 'bi-fire',
        'color': 'warning',
        'narrative': (
            'NHANES asks whether you have smoked a hundred cigarettes and whether you smoke now. BRFSS '
            'asks the same two questions in its own words. Both records carry the same Smoking Status '
            'component on the LOINC answer list, derived from those answers, and the agency\'s own '
            'variables stay on the record beside it. One query, one distribution per study.'
        ),
        'query_label': 'Compare smoking status',
    },
    {
        'number': 3,
        'title': 'Blood pressure: what was measured and what was asked',
        'query_number': 3,
        'icon': 'bi-heart-pulse',
        'color': 'danger',
        'narrative': (
            'NHANES measured blood pressure at the examination center, three readings each as the FHIR '
            'blood pressure cluster. BRFSS never measured it; it asked whether a professional ever said '
            'it was high. Both models compose the same FHIR components, so the query joins on them and '
            'the store shows which study has readings, with their ranges, and which has an indicator.'
        ),
        'query_label': 'Compare blood pressure',
    },
    {
        'number': 4,
        'title': 'Chronic conditions, and the basis each study has for them',
        'query_number': 4,
        'icon': 'bi-clipboard2-pulse',
        'color': 'info',
        'narrative': (
            'A self-reported "ever told you had diabetes" and a claims-based diabetes flag are not the '
            'same measurement. They are the same concept. Each condition is one component every study '
            'composes, and every record states the basis it was established on, so the comparison is '
            'honest about what it compares: NHANES and BRFSS by self-report, CMS by claims.'
        ),
        'query_label': 'Compare conditions',
    },
    {
        'number': 5,
        'title': 'Medications: where the join does not exist, and why',
        'query_number': 5,
        'icon': 'bi-capsule',
        'color': 'secondary',
        'narrative': (
            'NHANES identifies a medication by its own drug code and a generic name. CMS identifies a '
            'dispensed product by its National Drug Code. Neither is RxNorm, and mapping one onto the '
            'other would be a modeling decision made in silence. The models keep each agency\'s coding '
            'as it is, and the query shows the two systems side by side, joined by nothing.'
        ),
        'query_label': 'Show the gap',
    },
    {
        'number': 6,
        'title': 'Demographics side by side',
        'query_number': 6,
        'icon': 'bi-people',
        'color': 'success',
        'narrative': (
            'Gender from the Default library, race and ethnicity from the NIH CDE catalog, on every '
            'record of every study. The agency\'s own coding is kept beside each harmonized value, '
            'and where the codings do not nest (income) nothing was harmonized. Open any row to the '
            'record and read both.'
        ),
        'query_label': 'Compare demographics',
    },
]
