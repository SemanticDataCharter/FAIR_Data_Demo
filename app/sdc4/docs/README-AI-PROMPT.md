# Civil Registry

**Model ID**: `dm-uika42uwtj3ijdbegzw2kcwq`
**Project**: Cordova
**Description**: Maintain the authoritative identity record for every person in Cordova.

### Dublin Core Metadata
- **Language**: en-US
- **Rights**: CC-BY http://creativecommons.org/licenses/by/3.0/
- **Coverage**: Universal

## Package Contents

- `dm-uika42uwtj3ijdbegzw2kcwq.xsd` -- XML Schema Definition (data model structure)
- `dm-uika42uwtj3ijdbegzw2kcwq.xml` -- XML instance example with sample data
- `dm-uika42uwtj3ijdbegzw2kcwq-instance.json` -- JSON instance example (same structure as XML)
- `dm-uika42uwtj3ijdbegzw2kcwq.jsonld` -- JSON-LD semantic schema description
- `dm-uika42uwtj3ijdbegzw2kcwq.html` -- Human-readable model documentation
- `dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl` -- SHACL shapes for RDF validation
- `dm-uika42uwtj3ijdbegzw2kcwq.ttl` -- RDF triples extracted from XSD (Turtle format)
- `dm-uika42uwtj3ijdbegzw2kcwq.rdf` -- RDF triples extracted from XSD (RDF/XML format)
- `dm-uika42uwtj3ijdbegzw2kcwq.gql` -- GQL CREATE statements for property graph databases
- `SHACL_README.md` -- SHACL usage guide
- `README-AI-PROMPT.md` -- This file

## XML Template Placeholders

The XML instance file (`dm-uika42uwtj3ijdbegzw2kcwq.xml`) is a **maximal template** containing every
element defined in the schema. Placeholder markers indicate where data should go:

- **`_PH_`** -- Required placeholder. This element MUST be replaced with valid data
  matching the schema constraints.
- **`_OPT_PH_`** -- Optional placeholder. This element CAN be replaced with data,
  or the entire enclosing element can be removed from the instance.
- **Fixed values** (labels, language, encoding) are pre-filled from the schema and
  should be kept as-is.

When using this template with an AI assistant, instruct it to:
1. Replace all `_PH_` markers with appropriate data
2. Replace `_OPT_PH_` markers with data or remove the element
3. Keep all fixed values unchanged

## Component Inventory

| Label | Type | CT ID | Constraints |
|-------|------|-------|-------------|
| **Civil Registry Record** | Cluster | `bgjt4mvgvkxcn6hurg37u21b` | 11 components; 3 sub-cluster(s) |
|   National ID (CID) | XdString | `nj7s1gk45tfgyooxpz0qaha3` | exactLen=16; pattern=`COR-(AL|BR|CE)0[1-3]-[0-9]{6}` |
|   Country of Birth | XdString | `cfg2l8ym4ve833ritrxu765t` | minLen=1; maxLen=200 |
|   Given Name (Person) | XdString | `kfyzf8u8gdafcpt5kfh2qg3q` | minLen=1; maxLen=100 |
|   Middle Name (Person) | XdString | `oit0ueglhjfcyq80z22kl2z3` | minLen=1; maxLen=100 |
|   Surname (Person) | XdString | `v8jgjo2sml12jo7zrb8swoxi` | minLen=1; maxLen=100 |
|   City | XdToken | `atdtdfzruh7tya0iv5cz365l` | 9 enum(s) |
|   Marital Status (Cordova) | XdToken | `vjfgimlbb90ds2xg55tfn941` | 5 enum(s) |
|   Province | XdToken | `kv5qqs3o4jwcwz9javgw1pzh` | 3 enum(s) |
|   Gender Identity | XdToken | `cymq16em5zb20whgtfzki6n5` | 9 enum(s) |
|   Sex | XdToken | `mw9qdn71urog8egjbp5t3y00` | 4 enum(s) |
|   Birth Date | XdTemporal | `g3k6bj8su3rvkszg2700dhyh` | -- |
|   **Contact Information** | Cluster | `sv48g8am8vqs46nodiugripz` | 3 components |
|     Cordova Email Address | XdString | `x0na649n17if0ukul82cmrx3` | minLen=5; maxLen=254; pattern=`[-a-zA-Z0-9._%+]+@(cordomail|novamail|portocorreo)\.co` |
|     Cordova Phone Number | XdString | `nfrvvp87c5imu5h9ups92kgy` | exactLen=16; pattern=`\+99-[123][012]0-[0-9]{3}-[0-9]{4}` |
|     Preferred Contact Method | XdToken | `zlz64jydsmhb5zmytcm2ewyg` | 5 enum(s) |
|   **Current Address** | Cluster | `ytctcqbr30kxsmvx4jk7lae2` | 4 components |
|     Address (Line 1) | XdString | `l338k7nlvnq2am0owa19yxfc` | maxLen=200 |
|     Address (Line 2) | XdString | `ek5h6dsqpd9kz0l4mcckmxpt` | maxLen=200 |
|     City | XdToken | `atdtdfzruh7tya0iv5cz365l` | 9 enum(s) |
|     Province | XdToken | `kv5qqs3o4jwcwz9javgw1pzh` | 3 enum(s) |
|   **Family Relationships** | Cluster | `l9k2fmlc5vn477r3kpi1ufal` | 1 assert(s); 3 components |
|     Relationship Type | XdToken | `be9apjt8mvjjv86qzycorcjl` | 7 enum(s) |
|     Relationship End Date | XdTemporal | `o7vjxwswi0pxo543hq504jjx` | -- |
|     Relationship Start Date | XdTemporal | `k9ptlhkq3j41p6umlg3tc80x` | -- |

## Structural Hierarchy

```
DM: Civil Registry
  [Cluster] Civil Registry Record
    [XdString] National ID (CID)
    [XdString] Country of Birth
    [XdString] Given Name (Person)
    [XdString] Middle Name (Person)
    [XdString] Surname (Person)
    [XdToken] City
    [XdToken] Marital Status (Cordova)
    [XdToken] Province
    [XdToken] Gender Identity
    [XdToken] Sex
    [XdTemporal] Birth Date
    [Cluster] Contact Information
      [XdString] Cordova Email Address
      [XdString] Cordova Phone Number
      [XdToken] Preferred Contact Method
    [Cluster] Current Address
      [XdString] Address (Line 1)
      [XdString] Address (Line 2)
      [XdToken] City
      [XdToken] Province
    [Cluster] Family Relationships
      [XdToken] Relationship Type
      [XdTemporal] Relationship End Date
      [XdTemporal] Relationship Start Date
```

## Semantic Links

| Component | Predicate | Object URI |
|-----------|-----------|------------|
| Civil Registry Record | `skos:broadMatch` | `https://schema.org/ItemList` |
| Civil Registry Record | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q18562479` |
| Civil Registry Record | `rdfs:isDefinedBy` | `https://www.who.int/data/data-collection-tools/civil-registration-and-vital-statistics-(crvs)` |
| National ID (CID) | `rdfs:isDefinedBy` | `http://schema.org/identifier` |
| National ID (CID) | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q1140371` |
| National ID (CID) | `skos:broadMatch` | `https://schema.org/identifier` |
| Country of Birth | `rdfs:isDefinedBy` | `https://uts.nlm.nih.gov/uts/umls/concept/C1300001` |
| Country of Birth | `rdf:type` | `https://schema.org/Text` |
| Given Name (Person) | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q202444` |
| Given Name (Person) | `rdf:type` | `https://schema.org/Text` |
| Middle Name (Person) | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q245025` |
| Middle Name (Person) | `rdf:type` | `https://schema.org/Text` |
| Surname (Person) | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q101352` |
| Surname (Person) | `rdf:type` | `https://schema.org/Text` |
| City | `rdfs:isDefinedBy` | `http://schema.org/City` |
| City | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| City | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Marital Status (Cordova) | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q11920938` |
| Marital Status (Cordova) | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Marital Status (Cordova) | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Province | `rdfs:isDefinedBy` | `http://schema.org/AdministrativeArea` |
| Province | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Province | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Province | `rdfs:isDefinedBy` | `https://schema.org/State` |
| Gender Identity | `rdfs:isDefinedBy` | `https://uts.nlm.nih.gov/uts/umls/concept/C0017249` |
| Gender Identity | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Gender Identity | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Sex | `rdfs:isDefinedBy` | `https://uts.nlm.nih.gov/uts/umls/concept/C5236503` |
| Sex | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Sex | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Birth Date | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q2389905` |
| Birth Date | `rdf:type` | `https://schema.org/DateTime` |
| Contact Information | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q2996679` |
| Contact Information | `skos:broadMatch` | `https://schema.org/ItemList` |
| Cordova Email Address | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q1273217` |
| Cordova Email Address | `skos:broadMatch` | `https://schema.org/name` |
| Cordova Phone Number | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q214995` |
| Cordova Phone Number | `skos:relatedMatch` | `https://www.wikidata.org/wiki/Q214995` |
| Preferred Contact Method | `skos:relatedMatch` | `https://www.wikidata.org/wiki/Q2336001` |
| Preferred Contact Method | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Preferred Contact Method | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Current Address | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q75618710` |
| Current Address | `skos:broadMatch` | `https://schema.org/ItemList` |
| Address (Line 1) | `rdf:type` | `https://schema.org/Text` |
| Address (Line 1) | `rdfs:isDefinedBy` | `https://schema.org/streetAddress` |
| Address (Line 2) | `rdf:type` | `https://schema.org/Text` |
| Address (Line 2) | `rdfs:isDefinedBy` | `https://schema.org/streetAddress` |
| City | `rdfs:isDefinedBy` | `http://schema.org/City` |
| City | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| City | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Province | `rdfs:isDefinedBy` | `http://schema.org/AdministrativeArea` |
| Province | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Province | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Province | `rdfs:isDefinedBy` | `https://schema.org/State` |
| Family Relationships | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q69901743` |
| Family Relationships | `skos:broadMatch` | `https://schema.org/ItemList` |
| Relationship Type | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q69901743` |
| Relationship Type | `skos:exactMatch` | `https://schema.org/DefinedTermSet` |
| Relationship Type | `rdf:type` | `http://www.w3.org/2004/02/skos/core#ConceptScheme` |
| Relationship End Date | `skos:broadMatch` | `https://schema.org/Date` |
| Relationship End Date | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q121875611` |
| Relationship Start Date | `rdfs:isDefinedBy` | `https://www.wikidata.org/wiki/Q3406134` |
| Relationship Start Date | `skos:broadMatch` | `https://schema.org/Date` |

## Using This Model with AI Assistants

### Quick Start Prompt

Copy and customize this prompt for your AI assistant:

```
I have an SDC4-compliant data model called "Civil Registry" and need help
creating a data entry application.

**Attached Files:**
- XML Schema (dm-uika42uwtj3ijdbegzw2kcwq.xsd)
- Example instance (dm-uika42uwtj3ijdbegzw2kcwq.xml)
- HTML documentation (dm-uika42uwtj3ijdbegzw2kcwq.html)

**What I Need:**
I need a [specify framework: Python Reflex / React / Django / etc.] application that:

1. **Data Import**: Import data from CSV files
2. **Data Storage**: Store in [SQLite / PostgreSQL / MySQL / etc.] database
3. **Data Entry**: Forms for creating/editing records with validation
4. **Data Browser**: View, filter, and search records
5. **Export**: Export data back to CSV or XML

**Database Design:**
Each SDC4 Cluster in the schema should map to a database table with
appropriate relationships.

**My Specific Requirements:**
[Add your specific needs here]

Please analyze the schema and propose an application architecture.
```

### Example Use Cases

**Python Reflex Data Entry App:**
```
Create a Python Reflex application for data entry based on the
"Civil Registry" SDC4 schema (dm-uika42uwtj3ijdbegzw2kcwq.xsd).
Include CSV import, SQLite storage, forms with validation, and a data browser.
Use the sdcvalidator library for full SDC4 XML validation.
```

**React/Next.js Web App:**
```
Build a React/Next.js application with a REST API backend for the
"Civil Registry" schema (dm-uika42uwtj3ijdbegzw2kcwq.xsd).
Frontend: data entry forms and browser using the schema structure.
Backend: Node.js/Express with PostgreSQL for storage.
```

**Django Admin Interface:**
```
Generate Django models from the "Civil Registry" SDC4 schema (dm-uika42uwtj3ijdbegzw2kcwq.xsd)
with a custom admin interface.
Each cluster should be a Django model with appropriate field types.
Include CSV import/export via Django admin actions.
```

**REST API Only:**
```
Create a FastAPI REST API for the "Civil Registry" data model (dm-uika42uwtj3ijdbegzw2kcwq.xsd).
Endpoints for CRUD operations on each cluster.
Include XML validation using sdcvalidator.
Return both JSON and XML responses.
```

## SDC4 Validation (Optional but Recommended)

For full SDC4 compliance with XML validation, use the `sdcvalidator` Python library.

### Installation

```bash
pip install sdcvalidator
```

### Basic Usage

```python
from sdcvalidator import SDC4Validator

# Initialize validator with your SDC4 data model schema
validator = SDC4Validator('dm-uika42uwtj3ijdbegzw2kcwq.xsd')

# Validate and get a detailed report
report = validator.validate_and_report('data.xml')

if report['valid']:
    print('Valid SDC4 XML instance')
else:
    print('Validation errors:')
    for error in report['errors']:
        print(f"  - {error['xpath']}: {error['reason']}")
```

### ExceptionalValue Recovery

When validation errors occur, sdcvalidator can quarantine invalid data
with ISO 21090 ExceptionalValue elements:

```python
validator = SDC4Validator('dm-uika42uwtj3ijdbegzw2kcwq.xsd')
recovered_tree = validator.validate_with_recovery('data.xml')
validator.save_recovered_xml('recovered_data.xml', 'data.xml')
```

**Note**: XML validation is completely optional. You can build applications
using only JSON, implement custom validation, or add sdcvalidator later.

## GQL Graph Database Usage

The `dm-uika42uwtj3ijdbegzw2kcwq.gql` file contains GQL CREATE statements for property
graph databases (e.g., Neo4j, Amazon Neptune, TigerGraph).

### Loading into Neo4j

```cypher
// Load the GQL file content
// Copy the CREATE statements from dm-uika42uwtj3ijdbegzw2kcwq.gql into the Neo4j browser
```

### Example Queries

```cypher
// Find all components in this data model
MATCH (n:ModelComponent) RETURN n.label, n.sdcType

// Show the structural hierarchy
MATCH (dm:DataModel)-[:HAS_ROOT_CLUSTER]->(c:Cluster)-[:CONTAINS_COMPONENT]->(comp)
RETURN dm.label, c.label, comp.label, comp.sdcType

// Find components with specific constraints
MATCH (n:ModelComponent) WHERE n.minLength IS NOT NULL
RETURN n.label, n.minLength, n.maxLength
```

## Tips for Working with AI Assistants

### 1. Start with Architecture Discussion

Before asking for code, ask the AI to:
- Analyze the schema structure
- Identify complex relationships
- Recommend database design
- Suggest appropriate frameworks

### 2. Iterate in Phases

- **Phase 1**: Basic data models and storage
- **Phase 2**: Data entry forms
- **Phase 3**: Data browser and search
- **Phase 4**: CSV import/export
- **Phase 5**: Advanced features (auth, reporting, etc.)

### 3. Leverage the Documentation

The `dm-uika42uwtj3ijdbegzw2kcwq.html` file contains human-readable descriptions,
constraint definitions, business rules, and semantic links.
Share this with the AI for better understanding.

### 4. Database Schema Mapping

**Option 1: Normalized Tables (Traditional)**
```
Cluster -> Database Table
Sub-Cluster -> Separate Table with Foreign Key
Component -> Table Column
```

**Option 2: JSON Embedding (Simpler)**
```
Main Cluster -> Table
Sub-Clusters -> JSON Column
Components -> Mixed (simple types as columns, complex as JSON)
```

Ask your AI assistant which approach fits your use case.

## Additional Resources

**SDC4 Specification:**
- [Semantic Data Charter](https://semanticdatacharter.org)

**sdcvalidator Documentation:**
- [PyPI Package](https://pypi.org/project/sdcvalidator/)

**Framework Documentation:**
- [Python Reflex](https://reflex.dev)
- [Django](https://www.djangoproject.com)
- [React](https://react.dev)
- [FastAPI](https://fastapi.tiangolo.com)

---

**Generated by SDCStudio** -- Your SDC4-compliant data modeling platform
