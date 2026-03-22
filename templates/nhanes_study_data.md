# NHANES Study Data Model

**template_version**: "4.0.0"

NHANES (National Health and Nutrition Examination Survey) is a continuous cross-sectional survey conducted by the CDC's National Center for Health Statistics (NCHS). It combines interviews and physical examinations to assess the health and nutritional status of the U.S. population.

This template defines the NHANES study data model for the FAIR Data Demo, reusing existing NIH-CDE catalog components where applicable and minting study-specific components for NHANES-only domains.

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

---

## NHANES-Specific Components (Cluster)

**Description**: Components specific to the NHANES population survey covering substance use, social determinants, physical function, and pain assessment domains.

### Alcohol Use Frequency

**Type**: XdToken

**Definition**: Frequency of alcohol consumption over the past 12 months.

**Predicate**: alcohol consumption Q24634210

**Enumerations**:
- Never
- Monthly or less
- 2-4 times per month
- 2-3 times per week
- 4+ times per week

### Alcohol Drinks Per Day

**Type**: XdCount

**Definition**: Average number of alcoholic drinks consumed per day on days when drinking occurred.

**Predicate**: alcohol consumption Q24634210

**Min Inclusive**: 0
**Max Inclusive**: 50

### Drug Use History

**Type**: XdToken

**Definition**: Self-reported history of recreational or illicit drug use.

**Predicate**: substance abuse Q15708034

**Enumerations**:
- Never
- Former
- Current

### Tobacco Use Duration Years

**Type**: XdCount

**Definition**: Number of years of tobacco use for current or former tobacco users.

**Predicate**: tobacco use Q917235

**Min Inclusive**: 0
**Max Inclusive**: 100

### Income to Poverty Ratio

**Type**: XdQuantity

**Definition**: Ratio of family income to the federal poverty level threshold.

**Predicate**: poverty threshold Q7236513

**Units**: ratio
**Min Inclusive**: 0
**Max Inclusive**: 10

### Health Insurance Coverage

**Type**: XdToken

**Definition**: Type of health insurance coverage reported by participant.

**Predicate**: health insurance Q171447

**Enumerations**:
- Private
- Medicare
- Medicaid
- Military
- None
- Other

### Food Security Status

**Type**: XdToken

**Definition**: Household food security status based on USDA Food Security Survey Module.

**Predicate**: food security Q5464817

**Enumerations**:
- Full food security
- Marginal food security
- Low food security
- Very low food security

### Housing Type

**Type**: XdToken

**Definition**: Type of housing structure where participant currently resides.

**Predicate**: housing Q1247867

**Enumerations**:
- Single-family detached
- Single-family attached
- Apartment
- Mobile home
- Other

### Grip Strength Right Hand

**Type**: XdQuantity

**Definition**: Maximum grip strength measured in the right hand using a dynamometer.

**Predicate**: grip strength Q60689

**Units**: kg
**Min Inclusive**: 0
**Max Inclusive**: 150

### Grip Strength Left Hand

**Type**: XdQuantity

**Definition**: Maximum grip strength measured in the left hand using a dynamometer.

**Predicate**: grip strength Q60689

**Units**: kg
**Min Inclusive**: 0
**Max Inclusive**: 150

### Gait Speed

**Type**: XdQuantity

**Definition**: Timed gait speed measured over a standardized walking course.

**Predicate**: gait Q308684

**Units**: m/s
**Min Inclusive**: 0
**Max Inclusive**: 5

### Chair Stand Test Count

**Type**: XdCount

**Definition**: Number of chair stands completed in 30 seconds for lower extremity strength assessment.

**Predicate**: physical functional status Q7187896

**Min Inclusive**: 0
**Max Inclusive**: 50

### Pain Severity Score

**Type**: XdCount

**Definition**: Self-reported pain severity on a 0-10 numeric rating scale.

**Predicate**: pain Q81938

**Min Inclusive**: 0
**Max Inclusive**: 10

### Pain Location

**Type**: XdToken

**Definition**: Primary anatomical location of reported pain.

**Predicate**: pain Q81938

**Enumerations**:
- Head
- Neck
- Back
- Chest
- Abdomen
- Upper extremity
- Lower extremity
- Joint
- Other

### Pain Interference Score

**Type**: XdCount

**Definition**: Degree to which pain interferes with daily activities on a 0-10 scale.

**Predicate**: pain Q81938

**Min Inclusive**: 0
**Max Inclusive**: 10
