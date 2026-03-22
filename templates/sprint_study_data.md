# SPRINT Study Data Model

**template_version**: "4.0.0"

SPRINT (Systolic Blood Pressure Intervention Trial) is a randomized, controlled, open-label trial funded by the National Heart, Lung, and Blood Institute (NHLBI). It demonstrated that targeting a systolic blood pressure of less than 120 mmHg (intensive treatment) compared with less than 140 mmHg (standard treatment) significantly reduced cardiovascular events and mortality in adults at high cardiovascular risk.

This template defines the SPRINT study data model for the FAIR Data Demo, reusing existing NIH-CDE catalog components where applicable and minting study-specific components for SPRINT-only domains.

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

## SPRINT-Specific Components (Cluster)

**Description**: Components specific to the SPRINT randomized trial covering treatment randomization, blood pressure protocol, and cognitive assessment domains.

### Randomization Arm

**Type**: XdToken

**Definition**: Treatment group assignment in the SPRINT trial.

**Predicate**: randomized controlled trial Q1436668

**Enumerations**:
- Intensive (SBP < 120 mmHg)
- Standard (SBP < 140 mmHg)

### Randomization Date

**Type**: XdTemporal

**Definition**: Date of participant randomization into treatment arm.

**Predicate**: randomized controlled trial Q1436668

### BP Measurement Position

**Type**: XdToken

**Definition**: Patient position during automated blood pressure measurement per SPRINT protocol.

**Predicate**: blood pressure measurement Q3630446

**Enumerations**:
- Seated
- Standing
- Supine

### BP Measurement Count

**Type**: XdCount

**Definition**: Number of automated blood pressure readings taken at this visit (SPRINT protocol requires 3 readings after 5-minute rest).

**Predicate**: blood pressure measurement Q3630446

**Min Inclusive**: 1
**Max Inclusive**: 5

### BP Average Systolic

**Type**: XdQuantity

**Definition**: Average of the last 2 automated systolic blood pressure readings at this visit per SPRINT protocol.

**Predicate**: systolic blood pressure Q3560505

**Units**: mmHg
**Min Inclusive**: 50
**Max Inclusive**: 300

### BP Average Diastolic

**Type**: XdQuantity

**Definition**: Average of the last 2 automated diastolic blood pressure readings at this visit per SPRINT protocol.

**Predicate**: diastolic blood pressure Q3560507

**Units**: mmHg
**Min Inclusive**: 20
**Max Inclusive**: 200

### Antihypertensive Medication Count

**Type**: XdCount

**Definition**: Total number of distinct antihypertensive medications prescribed at current visit.

**Predicate**: antihypertensive Q903783

**Min Inclusive**: 0
**Max Inclusive**: 10

### Primary Outcome Event

**Type**: XdToken

**Definition**: Composite primary cardiovascular outcome event (myocardial infarction, acute coronary syndrome, stroke, heart failure, or cardiovascular death).

**Predicate**: cardiovascular disease Q389735

**Enumerations**:
- Myocardial Infarction
- Acute Coronary Syndrome
- Stroke
- Heart Failure
- Cardiovascular Death
- None

### Primary Outcome Date

**Type**: XdTemporal

**Definition**: Date of primary cardiovascular outcome event, if one occurred.

**Predicate**: cardiovascular disease Q389735

### MoCA Total Score

**Type**: XdCount

**Definition**: Montreal Cognitive Assessment total score. Screens for mild cognitive impairment. Scores of 26+ are considered normal.

**Predicate**: Montreal Cognitive Assessment Q1948727

**Min Inclusive**: 0
**Max Inclusive**: 30

### MoCA Visuospatial Score

**Type**: XdCount

**Definition**: MoCA visuospatial/executive subscore (trail-making, cube copy, clock drawing).

**Predicate**: Montreal Cognitive Assessment Q1948727

**Min Inclusive**: 0
**Max Inclusive**: 5

### MoCA Delayed Recall Score

**Type**: XdCount

**Definition**: MoCA delayed recall subscore assessing short-term memory.

**Predicate**: Montreal Cognitive Assessment Q1948727

**Min Inclusive**: 0
**Max Inclusive**: 5

### Orthostatic Hypotension Flag

**Type**: XdBoolean

**Definition**: Whether orthostatic hypotension was detected (SBP drop >= 20 mmHg or DBP drop >= 10 mmHg within 3 minutes of standing).

**Predicate**: orthostatic hypotension Q745076

### Serious Adverse Event Flag

**Type**: XdBoolean

**Definition**: Whether the adverse event met criteria for a Serious Adverse Event (death, life-threatening, hospitalization, disability, or other medically important condition).

**Predicate**: adverse event Q4677587
