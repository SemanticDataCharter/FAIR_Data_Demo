# ADNI Study Data Model

**template_version**: "4.0.0"

ADNI (Alzheimer's Disease Neuroimaging Initiative) is a longitudinal multicenter study funded by the National Institute on Aging (NIA). It tracks the progression of Alzheimer's disease through clinical, imaging, genetic, and biomarker data collection across cognitively normal, mildly impaired, and Alzheimer's disease participants.

This template defines the ADNI study data model for the FAIR Data Demo, reusing existing NIH-CDE catalog components where applicable and minting study-specific components for ADNI-only domains.

---

## Shared CDE Components (Cluster)

**Description**: Core NIH Common Data Element components shared across all three FAIR Demo studies.

### Participant ID

**Reuse**: sdt9aiqjdbjjaafgjzzwygf8

### Age in Years

**Reuse**: c1nr0ykdr4w99ss7dty1iaug

### Birth Date

**Reuse**: g3k6bj8su3rvkszg2700dhyh

### Sex

**Reuse**: mw9qdn71urog8egjbp5t3y00

### Race

**Reuse**: iiwx1rakgy3wfytyskre0v3x

### Ethnicity

**Reuse**: ltobu9ek54hcnrjxk16jk8qk

### Education Level

**Reuse**: dbv7fgfi67iztx00lgv1vxni

### Marital Status

**Reuse**: w3bw02ebbrrs7mzu3ztkb8od

### Systolic Blood Pressure

**Reuse**: v15kv8dnd9th63hmccqetmki

### Diastolic Blood Pressure

**Reuse**: b0qfvgagjyebeuizpe900a93

### Heart Rate

**Reuse**: wmjt38l5le7u3ro7qjmkaaz7

### Respiratory Rate

**Reuse**: zseky2lf0pcuc7rsjtj49dm9

### Body Temperature

**Reuse**: s0yyyjcuu3l4ra93p5lktzig

### BMI

**Reuse**: wpojnsuwae37rfsnj9xpbcun

### Person Weight Value

**Reuse**: scjotdd5kp3yovkvjgsc5a7v

### Person Height Value

**Reuse**: mkelab9gci43xj7akjy8w7h3

### Smoking Status

**Reuse**: pcqb6t8q1g9e0fagm55fkhf2

### AE Description

**Reuse**: pp5v32ipc0xbva1hi5l3r91g

### AE Term

**Reuse**: fbfqzhm0es37p5rtrtw2wh0n

### AE Start Date

**Reuse**: w0qi4triqgeeg0oodhy75p8h

### AE End Date

**Reuse**: andj4gpkessj3z0koheyc7gj

---

## ADNI-Specific Components (Cluster)

**Description**: Components specific to the ADNI longitudinal cohort study covering cognitive assessment, CSF biomarkers, and neuroimaging domains.

### ADAS-Cog Total Score

**Type**: XdCount

**Definition**: Alzheimer's Disease Assessment Scale — Cognitive Subscale total score. Higher scores indicate greater cognitive impairment.

**Predicate**: cognitive test Q5141583

**Min Inclusive**: 0
**Max Inclusive**: 70

### ADAS-Cog Word Recall Score

**Type**: XdCount

**Definition**: ADAS-Cog word recall task score measuring immediate memory for a 10-word list across 3 trials.

**Predicate**: cognitive test Q5141583

**Min Inclusive**: 0
**Max Inclusive**: 10

### CDR Global Score

**Type**: XdQuantity

**Definition**: Clinical Dementia Rating global score derived from semi-structured interview assessing six domains of cognitive and functional performance.

**Predicate**: clinical dementia rating Q5132750

**Units**: score
**Min Inclusive**: 0
**Max Inclusive**: 3

### CDR Sum of Boxes

**Type**: XdQuantity

**Definition**: Clinical Dementia Rating Sum of Boxes — sum of individual domain box scores providing finer granularity than the global CDR.

**Predicate**: clinical dementia rating Q5132750

**Units**: score
**Min Inclusive**: 0
**Max Inclusive**: 18

### MMSE Total Score

**Type**: XdCount

**Definition**: Mini-Mental State Examination total score. Assesses orientation, registration, attention, recall, and language.

**Predicate**: mini-mental state examination Q593744

**Min Inclusive**: 0
**Max Inclusive**: 30

### Diagnosis Category

**Type**: XdToken

**Definition**: Participant diagnostic category at current visit.

**Predicate**: diagnosis Q16644043

**Enumerations**:
- Cognitively Normal
- Subjective Memory Concern
- Early Mild Cognitive Impairment
- Late Mild Cognitive Impairment
- Alzheimer's Disease

### CSF Amyloid Beta 42

**Type**: XdQuantity

**Definition**: Cerebrospinal fluid amyloid beta 1-42 concentration. Low levels associated with amyloid plaque deposition.

**Predicate**: amyloid beta Q408747

**Units**: pg/mL
**Min Inclusive**: 0
**Max Inclusive**: 2000

### CSF Total Tau

**Type**: XdQuantity

**Definition**: Cerebrospinal fluid total tau protein concentration. Elevated levels indicate neurodegeneration.

**Predicate**: tau protein Q422879

**Units**: pg/mL
**Min Inclusive**: 0
**Max Inclusive**: 2000

### CSF Phosphorylated Tau

**Type**: XdQuantity

**Definition**: Cerebrospinal fluid phosphorylated tau (p-tau181) concentration. Specific marker for Alzheimer's pathology.

**Predicate**: tau protein Q422879

**Units**: pg/mL
**Min Inclusive**: 0
**Max Inclusive**: 500

### Hippocampal Volume

**Type**: XdQuantity

**Definition**: Total hippocampal volume measured from structural MRI using automated segmentation (FreeSurfer).

**Predicate**: hippocampus Q48360

**Units**: mm3
**Min Inclusive**: 1000
**Max Inclusive**: 12000

### Entorhinal Cortex Thickness

**Type**: XdQuantity

**Definition**: Mean cortical thickness of the entorhinal cortex from structural MRI. Early atrophy site in Alzheimer's disease.

**Predicate**: entorhinal cortex Q527706

**Units**: mm
**Min Inclusive**: 0.5
**Max Inclusive**: 6

### Whole Brain Volume

**Type**: XdQuantity

**Definition**: Total brain parenchyma volume from structural MRI, normalized by intracranial volume.

**Predicate**: brain Q1073

**Units**: mm3
**Min Inclusive**: 500000
**Max Inclusive**: 2000000

### Ventricular Volume

**Type**: XdQuantity

**Definition**: Total lateral ventricular volume from structural MRI. Enlargement indicates cerebral atrophy.

**Predicate**: lateral ventricle Q2878043

**Units**: mm3
**Min Inclusive**: 5000
**Max Inclusive**: 200000

### APOE Genotype

**Type**: XdToken

**Definition**: Apolipoprotein E genotype. APOE e4 allele is the strongest genetic risk factor for late-onset Alzheimer's disease.

**Predicate**: apolipoprotein E Q424624

**Enumerations**:
- e2/e2
- e2/e3
- e2/e4
- e3/e3
- e3/e4
- e4/e4
