# Generated Models

This directory holds SDCStudio-generated output for each study.

## Structure

After model generation in SDCStudio, each study directory will contain:

```
models/
├── NHANES/
│   ├── *.xsd          # XSD schemas
│   ├── *.xml          # XML instance documents
│   ├── *.json         # JSON instance data
│   ├── *.jsonld       # JSON-LD semantic descriptions
│   ├── *.html         # HTML documentation
│   ├── *.rdf          # RDF triples
│   ├── *.shacl        # SHACL constraint files
│   └── *.gql          # GQL CREATE statements
├── ADNI/
│   └── (same formats)
└── SPRINT/
    └── (same formats)
```

## How to Populate

1. Use SDC_Agents API to create/reuse NIH-CDE catalog components and assemble clusters
2. In SDCStudio, approve draft components and build study-level data models
3. Generate all 8 output formats (XSD, XML, JSON, JSON-LD, HTML, RDF, SHACL, GQL)
4. Download and place output files in the appropriate study directory

The RDF files are loaded into GraphDB for cross-study SPARQL queries.
