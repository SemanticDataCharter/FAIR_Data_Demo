# Data Conversion Pipeline

This directory will contain scripts to convert source study data (CSV/XPT) into validated XML instances conforming to the SDCStudio-generated XSD schemas.

## Prerequisites

The conversion pipeline requires:
1. Generated XSD schemas in `models/` (from SDCStudio)
2. Downloaded source data in `source_data/` (see `source_data/README.md`)

## Status

Conversion scripts will be built after models are generated in SDCStudio. The scripts will:
- Read source CSV/XPT files from `source_data/`
- Validate against XSD schemas from `models/`
- Write validated XML instances to `output/instances/`
