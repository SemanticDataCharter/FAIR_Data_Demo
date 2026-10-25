# Source errata

What the FAIR Data Demo found wrong, or easy to misread, in the libraries and federal files it is built from, and what
it does about each. An error in a source library is corrected in that library, as a revision of the published
component, and the models here compose the correction; a federal file is never edited, and a convention of its own is
carried as the file states it, with what that means written down here.

## From the component libraries

### E-2026-10-01: NIH CDE "Are you pregnant now?" (`LiUWCWluP`), LOINC answer codes one off

**The error.** The NIH CDE Repository's record for Current Pregnancy Indicator binds each answer to the next value's
LOINC code: Yes to LA26683-5 (Not pregnant), No to LA4489-6 (Unknown), Unknown to LA15173-0 (Pregnant). Its own NCI
Thesaurus meanings (C49488 Yes, C49487 No, C17998 Unknown) say otherwise. The NIH CDE library imported the record
faithfully; its `SOURCE-ERRATA.md` (E-2026-10-01) has the evidence.

**How it was found.** 25 October 2026, running HL7's FHIR validator on the FHIR output of `sdc-gdr2fhir` for the NHANES
Participant records: every answer carried a display its LOINC code does not have.

**Effect here.** The NHANES Participant and BRFSS Respondent models compose the component (through NHANES Demographics
and BRFSS Demographics), so every record answering the question bound "Yes" to Not pregnant: 1,980 records in the demo
dataset, and every projection that writes the model's binding (FHIR, OMOP CDM, HL7 v2).

**What we did.**

1. The NIH CDE library published the correction, `zmpqfc6tb0o2hgu8qs6lj8tp`, a revision of `owjt9bcgisxfbco8qnddo2fq`
   (retired), on 25 October 2026.
2. `build/author.py` composes the correction, and the six clusters above it (NHANES Demographics, NHANES Participant,
   NHANES Participant Governed Record, and the three BRFSS clusters) are revisions of their published versions
   (`REVISIONS` in `build/author.py`).
3. `build/oneoff_models_errata.py` revises the NHANES Participant and BRFSS Respondent models onto them.

**Status.** Steps 2 and 3 are prepared; the production load and the release that carries them follow.

## From the federal files: conventions to read correctly

### NHANES 2017-2018 prescription medications (`RXQ_RX_J`): reason-for-use codes

The reasons for use (`RXDRSC1` to `RXDRSC3`) are ICD-10-CM codes with three conventions of NHANES's own, documented in
the file's Data Processing and Editing notes:

- **A trailing `P` means prevention.** "When reported reason was for disease prevention, an appropriate ICD-10-CM code
  followed by a letter 'P' was used (e.g., A49.9P Prevent bacterial infection; D75.9P Prevent blood clots)." 29 such
  codes, 691 of the file's 15,565 reason codes (`I21.P` Prevent heart attack, `D75.9P` Prevent blood clots, ...).
  These are not ICD-10-CM codes: ICD-10-CM has no `I21.P`.
- **55555** is a reason that could not be coded (84 in the file), **77777** refused (5), **99999** don't know (451).

**What the demo does.** The generator carries a reason whose code has the shape of an ICD-10-CM code, the `P` codes
included, in the Diagnosis (ICD-10-CM) component, with NHANES's own description beside it; it leaves out 55555, 77777
and 99999 and counts them (`make generate` prints the count).

**What that means downstream.** A `P` code sits under the ICD-10-CM system, so a target that checks ICD-10-CM refuses
it: HL7's FHIR validator reports `I21.P` and the like as unknown ICD-10-CM codes (9 of the 400 sample Bundles of
`sdc-gdr2fhir`). The record says it as NHANES does; that the code means "prevent" is in NHANES's description, not in
the code system.

**Status.** Open: whether the model should carry a prevention code as the ICD-10-CM code without its `P` and the
prevention as its own value, rather than as NHANES writes it.
