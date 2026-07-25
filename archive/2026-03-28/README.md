# Archived model and application packages — 2026-03-28

These are the FAIR Data Demo model packages (`models/`) and generated application
packages (`apps/`) as they existed on 2026-03-28, retained **unmodified** for
provenance and reproducibility. They are superseded by the current packages in
[`../../models/`](../../models/) and [`../../apps/`](../../apps/), which are
regenerated on `sdcvalidator` 4.4.1 with the corrected XSD 1.1 handling described
below and the restructured SDC component library.

Nothing here is deleted. Each package carries its own permanent CUID2 identities, so
these are a prior *published* state, not scratch files. The exact repository state
before regeneration is also pinned by the git tag `fair-demo-2026-03-28-pre-4.4.1`.

## Contents

- `models/` — 8 SDC4 model packages (BRFSS x1, CMS x4, NHANES x3)
- `apps/` — 8 generated Django application packages (one per model)

## Why these were regenerated: an undocumented XSD 1.1 validator regression

These packages were generated before `sdcvalidator` 4.4.0/4.4.1 corrected an
undocumented regression in XSD 1.1 schema compilation.

SDC4 cluster schemas restrict a content model that references an abstract
substitution-group head (`sdc4:Item`, content `label?, Item*`) down to the specific
member elements a model defines (for example `label?, ms-A?, ms-B?`). This is valid
under **XSD 1.1 Part 1 §3.4.6.4, "Content Type Restricts (Complex Content)"**: a
restriction is valid when every instance sequence valid against the derived type is
also valid against the base type, and a substitution-group member is substitutable
for its head. The XSD 1.0 particle name-matching rules (`NameAndTypeOK` and the
related `Recurse*` checks) that would have rejected this were **removed in XSD 1.1**.
The XSD 1.1 reference processors, Apache Xerces-J and Saxon EE, accept these schemas.

The validator's underlying `xmlschema` dependency (through 4.3.1) still applied the
removed XSD 1.0 rules and rejected the valid construct at schema-compile time
("the derived group is an illegal restriction"). Because the rejection happened
during schema construction, it silently blocked correct generation of the cluster
restriction pattern. That is the regression: not a change in the XSD standard, but a
validator applying a rule the standard had already removed.

`sdcvalidator` 4.4.0 corrected this with `build_xsd11_schema()`, which recognizes
this specific false positive **structurally** (every derived element must match a
base element by name, or be a member of a substitution group whose head is in the
base content model, with compatible occurrences) and only then returns a schema that
still enforces the restriction during instance validation, valid members accepted and
non-members rejected, matching the Xerces-J 1.1 reference behaviour. Any genuine
restriction error stays fatal. 4.4.1 made `build_xsd11_schema()` a drop-in for the
direct schema constructor used by SDCStudio and the VaaS resolver.

See the `sdcvalidator` CHANGELOG (4.4.0, 4.4.1) and `SDCRM/docs/VALIDATORS.md` for
the full specification citations and processor behaviour.

## Retrieving the pre-regeneration state

```
git checkout fair-demo-2026-03-28-pre-4.4.1
```
