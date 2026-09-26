# SHACL Validation Shapes for SDC4 Data Model

This package includes SHACL (Shapes Constraint Language) validation shapes that mirror the constraints defined in your XSD schema. These shapes enable you to validate RDF data against the same structural and semantic rules enforced by the XML Schema.

## Files Included

- **dm-uika42uwtj3ijdbegzw2kcwq.xsd** - XML Schema Definition for the data model
- **dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl** - SHACL shapes in Turtle format (this file's companion)
- **dm-uika42uwtj3ijdbegzw2kcwq.ttl** - RDF triples extracted from XSD (Turtle format)
- **dm-uika42uwtj3ijdbegzw2kcwq.rdf** - RDF triples extracted from XSD (RDF/XML format)
- **dm-uika42uwtj3ijdbegzw2kcwq.xml** - Sample XML instance
- **dm-uika42uwtj3ijdbegzw2kcwq.json** - JSON representation
- **dm-uika42uwtj3ijdbegzw2kcwq.html** - Human-readable documentation

## What is SHACL?

SHACL (Shapes Constraint Language) is a W3C standard for validating RDF graphs. It allows you to:
- Define structural constraints on your RDF data
- Specify cardinality requirements (min/max occurrences)
- Validate data types and value ranges
- Enforce relationships between resources
- Generate human-readable validation error messages

## How to Use the SHACL File

### 1. Python with pySHACL

```python
from pyshacl import validate
from rdflib import Graph

# Load your RDF data
data_graph = Graph()
data_graph.parse("your_data.ttl", format="turtle")

# Load SHACL shapes
shapes_graph = Graph()
shapes_graph.parse("dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl", format="turtle")

# Validate
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',
    abort_on_first=False
)

if conforms:
    print("✓ Data is valid!")
else:
    print("✗ Validation errors:")
    print(results_text)
```

### 2. Apache Jena with SHACL

```bash
# Using Jena shacl command-line tool
shacl validate --shapes dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl --data your_data.ttl
```

### 3. RDF4J with SHACL

```java
import org.eclipse.rdf4j.model.Model;
import org.eclipse.rdf4j.rio.Rio;
import org.eclipse.rdf4j.repository.sail.SailRepository;
import org.eclipse.rdf4j.sail.shacl.ShaclSail;

// Create SHACL-enabled repository
ShaclSail shaclSail = new ShaclSail(new MemoryStore());
SailRepository repository = new SailRepository(shaclSail);
repository.init();

// Load shapes
Model shapesModel = Rio.parse(new FileInputStream("dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl"), "", RDFFormat.TURTLE);
try (RepositoryConnection conn = repository.getConnection()) {
    conn.add(shapesModel, RDF4J.SHACL_SHAPE_GRAPH);

    // Add data - validation happens automatically
    Model dataModel = Rio.parse(new FileInputStream("your_data.ttl"), "", RDFFormat.TURTLE);
    conn.add(dataModel);
}
```

### 4. JavaScript/Node.js with rdf-validate-shacl

```javascript
const factory = require('rdf-ext')
const SHACLValidator = require('rdf-validate-shacl')
const fs = require('fs')

// Load shapes and data
const shapes = await factory.dataset().import(
    fs.createReadStream('dm-uika42uwtj3ijdbegzw2kcwq_shacl.ttl')
)
const data = await factory.dataset().import(
    fs.createReadStream('your_data.ttl')
)

// Validate
const validator = new SHACLValidator(shapes, { factory })
const report = await validator.validate(data)

if (report.conforms) {
    console.log('✓ Data is valid!')
} else {
    console.log('✗ Validation errors:')
    for (const result of report.results) {
        console.log(result.message)
    }
}
```

## SHACL Shape Structure

The SHACL file is organized into two main sections:

### 1. Base SDC4 Shapes

These define validation rules for the core SDC4 component types:
- **XdString** - String data with optional length constraints
- **XdBoolean** - Boolean values
- **XdCount** - Integer counts (requires Units)
- **XdQuantity** - Decimal quantities (requires Units)
- **XdFloat** - Floating-point values (requires Units)
- **XdDouble** - Double-precision values (requires Units)
- **XdTemporal** - Date/time values
- **XdOrdinal** - Ordinal/coded values
- **XdLink** - URI links
- **XdFile** - File references
- **XdToken** - Token values
- **List types** - XdStringList, XdBooleanList, XdIntegerList, etc.
- **Contextual types** - Party, Audit, Attestation, Participation
- **Reference ranges** - ReferenceRange, SimpleReferenceRange

### 2. Model-Specific Shapes

These define validation rules for your specific data model components, including:
- Required vs. optional fields (sh:minCount/sh:maxCount)
- Data type constraints (sh:datatype, sh:class)
- String patterns and lengths (sh:pattern, sh:minLength, sh:maxLength)
- Numeric ranges (sh:minInclusive, sh:maxInclusive)
- Enumerated values (sh:in)
- Fixed values (sh:hasValue)
- Nested component relationships (sh:node)
- Human-readable validation messages (sh:message)

## Understanding Validation Results

When validation fails, SHACL provides detailed error messages including:
- **Focus Node** - The RDF resource that violated the constraint
- **Result Path** - The property that caused the violation
- **Value** - The actual value that violated the constraint
- **Message** - Human-readable explanation of the violation
- **Severity** - sh:Violation, sh:Warning, or sh:Info

Example validation result:
```turtle
[ a sh:ValidationResult ;
  sh:focusNode ex:patient123 ;
  sh:resultPath sdc4:age ;
  sh:value "invalid" ;
  sh:resultMessage "age must be an integer value" ;
  sh:resultSeverity sh:Violation
] .
```

## Best Practices

1. **Version Control** - Keep SHACL files in version control alongside your schemas
2. **Continuous Validation** - Integrate SHACL validation into your CI/CD pipeline
3. **Custom Messages** - Leverage the human-readable messages for user-friendly error reporting
4. **Inference** - Use RDFS or OWL inference for more comprehensive validation
5. **Performance** - For large datasets, consider validating incrementally or in batches

## Differences from XSD Validation

While the SHACL shapes mirror XSD constraints, there are some key differences:

1. **Graph Structure** - SHACL validates RDF graphs, not XML trees
2. **Open World** - RDF follows open-world assumption; SHACL focuses on explicit assertions
3. **Flexibility** - SHACL can validate partial data and provide warnings vs. hard errors
4. **Inference** - SHACL can work with inferred triples from ontologies

## Additional Resources

- **SHACL Specification**: https://www.w3.org/TR/shacl/
- **pySHACL Documentation**: https://github.com/RDFLib/pySHACL
- **SHACL Playground**: https://shacl.org/playground/
- **SDC4 Documentation**: https://semanticdatacharter.com/

## Support

For questions about this SHACL file or the SDC4 data model:
- Review the generated XSD file for authoritative constraint definitions
- Consult the HTML documentation included in this package
- Visit https://semanticdatacharter.com/ for SDC4 reference documentation

---

**Generated by SDCStudio** - https://github.com/Axius-SDC/SDCStudio
