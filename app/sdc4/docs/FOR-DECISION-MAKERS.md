# CordovaOS: what to look at, and what to ask

A guide for the person who signs, not the person who builds. It takes about
fifteen minutes at the screen and assumes no technical background.

CordovaOS is a working demonstration of a fictional nation's data platform: ten
government domains, from civil registry to healthcare to the port authority,
built on one shared foundation. The data is invented. **The processes are not.**
Everything below is something you can click.

You do not need anything installed to read this, but it is worth seeing on a
screen. Anyone on your team can have it running in a few minutes on one laptop:
clone the repository, run `make demo`, open `http://localhost:18000/console/`.
There is no account to create, no vendor to call, no data to send anywhere, and
after the first download it does not need the internet at all. That last point
is not a detail. It means everything in this guide can be checked by your own
people, on your own hardware, before anyone signs anything.

---

## The three questions worth asking about any data platform

**What am I paying for now?** Most organisations do not book it as one line.
It is spread across integration projects, mapping tables, version migrations,
onboarding each new partner, reconciliation, and the analyst who is the only one
who knows what a column really holds. Every one of those is the cost of working
out, again, what your own data means.

**What breaks if I do nothing?** The bill recurs, and it grows. Each new system
is mapped onto the workarounds the last one left.

**What am I actually signing?** This is the one this demonstration is built to
answer, and the answer should be checkable before signature rather than argued
after it.

---

## The fifteen minute walk-through

### 1. Start at the front door, `/console/`

Ten domains, 1,460 records, generated from one model. Note the third figure:
**seven records refused**. We will come back to those, and the fact that a
demonstration shows you its failures is itself the point.

### 2. Open any record, and switch the three tabs

Table, Document, Graph. **This is the same record shown three ways.** Not three
copies kept in step by a nightly job. Not a warehouse extract. One validated
record, projected.

Ask your own team what it would cost you today to guarantee that the report, the
exchange file and the graph all say the same thing at the same moment. That
answer is the first line of the bill.

### 3. Select a field, and read "Governed by"

Click Body Temperature in a healthcare record. The panel tells you it must be a
quantity between 30.0 and 45.0, in degrees Celsius, that a value is required,
that an absence must state its reason, and it links to the external clinical
reference the definition is bound to.

**That is not a data dictionary somebody maintains separately.** It is read from
the same published file any counterparty validates against. The distinction
matters: a data dictionary describes intent, and drifts. This *is* the rule.

### 4. Look at a refused record

From the front page, open one of the seven. Validation says failed. A medication
is recorded, and the dose says **Asked but Unknown**.

The record was refused *and it explains why*. Compare that with what most
systems do with a missing dose: write zero, or a blank, or the date 1900-01-01,
all of which travel downstream as if they were real. A zero dose is averaged
into a report. A 1900 date sorts, filters and charts.

This dataset originally did exactly that: 508 magic dates and 501 "N/A" strings.
We fixed the generator and left the seven deliberate failures in, because a
platform that cannot say "I do not know" will eventually tell you something
false with great confidence.

### 5. Ask the cross-domain question, `/console/question/`

Eight separately built government systems. 250 people, 1,308 records, joined in
a quarter of a second. **217 of those people appear in four or more of them, and
one appears in all eight.**

The figure to hold onto is the third one: **zero mapping tables consulted.** The
eight systems agree on what identifies a person because they compose the same
published component, not eight local conventions that somebody reconciles later.
Scroll down: the second question on the page follows exposed people to their
employers, and the employers to the business registry and the tax office, on one
more shared component, the business registry number.

In most estates this question is a project. Here it is a query, and the query is
printed on the page so nobody has to take our word for it.

---

## What this demonstration deliberately does not do

The console tells you where its own edges are, because that is the behaviour
you should require from anyone selling you a data platform. Until this release
the question a minister would rather ask, which businesses employ exposed people
and what trade is at risk, was not answerable from the data, and the page said
so and named the reason: employment records carried the employer as free text.
The models now carry the employer as the same registered identifier the business
registry and the tax office use, so the page answers it, and shows the query.
Where a chain still cannot run, the page will say so rather than stage it: the
port authority's crew lists carry a name and a birth date, not the national
identifier, so a crew member is matched to a resident by those and not by the
identifier component. That is a modelling decision in the maritime standard the
model follows, and it is recorded rather than papered over.

The data is synthetic throughout. Cordova is not a country.

---

## What to put in your next procurement document

One line, and it separates a substrate from a subscription:

> Hand us the constraint set that makes the data operable, in a form we can
> validate without you, and let us test it before signature.

A vendor who can answer that has given you something that keeps working if the
relationship ends. A vendor who cannot has told you that the meaning of your
data lives inside their platform.

Three questions in the same family, for the same reason:

1. Can we validate a record **without calling your service?**
2. Does the model survive **your next release**, and our next one?
3. Can a party who has never met us **verify the result on their own hardware?**

Every one of those is answerable in this demonstration, on your own machine,
with the network unplugged.

---

## The one sentence

Most data platforms make your data useful **while you are inside them**. The
question worth asking is what your data can still say on the day you are not.
