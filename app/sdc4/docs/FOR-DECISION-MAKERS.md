# FAIR Data Demo: what to look at, and what to ask

A guide for the person who signs, not the person who builds. It takes about
fifteen minutes at the screen and assumes no technical background.

The FAIR Data Demo is a working demonstration built on three federal health
data releases your agencies already publish: the CDC's NHANES examination
survey, the CDC's BRFSS telephone survey, and CMS's synthetic Medicare claims
sample. Three studies, two agencies, three file formats, and one question that
every data-sharing mandate assumes is easy and never is: **when two of them
record the same thing, can you ask both at once?** Everything below is
something you can click.

You do not need anything installed to read this, but it is worth seeing on a
screen. Anyone on your team can have it running on one laptop: clone the
repository, download the three public files, run `make demo`, open
`http://localhost:18100/console/`. There is no account to create, no vendor to
call, no data to send anywhere, and after the first download it does not need
the internet at all. That last point is not a detail. It means everything in
this guide can be checked by your own people, on your own hardware, with your
own copy of the public data, before anyone signs anything.

---

## The three questions worth asking about any data platform

**What am I paying for now?** Every research group that uses these files
starts by parsing the codebook, deciding which column means what, and
reconciling it with the last study's columns. The work is repeated per group,
per study, per year, and none of it is reusable by the next group. It is never
booked as one line, and it is the largest line.

**What breaks if I do nothing?** "FAIR" has been mandated. The files are
findable and accessible. They are not interoperable, and every mandate that
assumes they are pushes the reconciliation cost onto the people least able to
refuse it.

**What am I actually signing?** This is the one this demonstration is built
to answer, and the answer should be checkable before signature rather than
argued after it.

---

## The fifteen minute walk-through

### 1. Start at the front door, `/console/`

Seven models, 84,352 records, every one generated from a row of the public
files. Note the third figure: **zero records refused**, and it is
not because the data is complete. A survey respondent who refused to answer is
recorded as a refusal by the agency, coded 7 or 9 in the file. Most pipelines
carry that 7 into an average. Here the refusal is left out of the record and
counted, and the count is printed when the data is generated. Nothing in this
store is a number that was never an answer.

### 2. Open any record, and switch the three tabs

Table, Document, Graph. **This is the same record shown three ways.** Not three
copies kept in step by a nightly job. Not a warehouse extract. One validated
record, projected.

Open an NHANES participant. The table shows the person's blood pressure, their
cholesterol, their smoking status and their answer to "has a doctor ever told
you that you had diabetes," beside the survey weight the statistician needs and
the agency's own code for every answer. Ask your own team what it would cost
today to guarantee that the report, the exchange file and the graph all say the
same thing at the same moment. That answer is the first line of the bill.

### 3. Select a field, and read "Governed by"

Click Systolic Blood Pressure in the NHANES record. The panel tells you it is a
quantity, its range, its unit, and that it is the FHIR library's component,
identified by a permanent identifier. Now open a BRFSS respondent and click
Smoking Status. Same panel, and the component it names is the same one the
NHANES record carries, with the LOINC answer list both studies were mapped
onto.

**That is not a data dictionary somebody maintains separately.** It is read
from the same published file any counterparty validates against. A data
dictionary describes intent, and drifts. This *is* the rule.

### 4. Look at where it came from

Every record carries its provenance beside its data: which federal file, at
which URL, in which release, which row. Not in a log somewhere else. In the
record. A reviewer who doubts a value can go to the row.

### 5. Ask the cross-study question, `/console/question/`

The page asks the store which components records of more than one study
carry. It answers with a table: 20 components carried by more than
one study, 8 of them by all three. Smoking status, the
chronic conditions, gender, race and ethnicity, age, marital status, veteran
status. Each row opens a record.

The figure to hold onto is the third one: **zero mapping tables consulted.**
The three studies agree on what a diabetes indicator is because they compose
the same published component, not three local conventions that somebody
reconciles later. Scroll down: the second question asks what each study says
about each condition, and on what basis. A survey records that a doctor said
so. A claims file records that a claim was paid. Both are answers to the same
component, and the record says which kind it is, so nobody has to remember
that a CMS "yes" and a BRFSS "yes" were established differently.

In most estates this question is a project. Here it is a query, and the query
is printed on the page so nobody has to take our word for it.

---

## What this demonstration deliberately does not do

The console tells you where its own edges are, because that is the behaviour
you should require from anyone selling you a data platform.

The first build of this demonstration, in March 2026, could not answer the
question in step 5. It ran an automated pipeline over the same files, and the
pipeline could not tell from the agencies' thin metadata that two columns
measured the same thing, so each study got its own components and the studies
shared none. The page said so. This build makes that decision the way it has
to be made, by people, as reviewed records, once, and the studies compose the
result. The earlier components remain published and are marked as superseded,
so nothing anyone downloaded stops working.

Where a join still does not exist, the page says so rather than staging it.
NHANES names a medication and CMS records a product code, and neither is the
standard vocabulary that would let them meet, so the medication beat of the
walk-through shows the gap. BRFSS did not ask about blood pressure in 2022, so
that comparison shows one study's measurements and the other's silence. The
three studies are three different populations, so there is no person who
appears in two of them; what they share is the component, and the graph draws
it as one.

The Medicare data is synthetic, built by CMS to have the shape of claims with
no beneficiary in it. The two surveys are real, de-identified public releases.

---

## What to put in your next procurement document

One line, and it separates a substrate from a subscription:

> Hand us the constraint set that makes the data operable, in a form we can
> validate without you, and let us test it on our own data before signature.

A vendor who can answer that has given you something that keeps working if the
relationship ends. A vendor who cannot has told you that the meaning of your
data lives inside their platform.

Three questions in the same family, for the same reason:

1. Can we validate a record **without calling your service?**
2. Does the model survive **your next release**, and our next one?
3. Can a party who has never met us **verify the result on their own hardware?**

Every one of those is answerable in this demonstration, on your own machine,
with public data you already pay for, with the network unplugged.

---

## The one sentence

Most data platforms make your data useful **while you are inside them**. The
question worth asking is what your data can still say on the day you are not.
