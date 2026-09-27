# Getting Started with Your RDF Triplestore

This guide helps you explore the semantic data in your SDC4 application using Apache Jena Fuseki.

## What is a Triplestore?

A triplestore is a database designed for storing and querying RDF (Resource Description Framework) data. Your SDC4 application automatically stores semantic representations of your data as RDF triples, enabling powerful queries and data integration capabilities.

**Key concepts:**
- **Triple**: A data statement in the form: Subject → Predicate → Object (e.g., "Texas" → "hasPopulation" → "29000000")
- **SPARQL**: The query language for RDF data (like SQL for relational databases)
- **Graph**: A collection of related triples

## Accessing Fuseki

Open the Fuseki web interface at: **http://localhost:13030**

**Default credentials:**
- Username: `admin`
- Password: `admin123`

## Quick Start: Your First Query

1. Click on your dataset (e.g., `sdc4_rdf`)
2. Click the **Query** button
3. Try this simple query to see all data:


```sparql
SELECT * WHERE {
  ?subject ?predicate ?object
}
LIMIT 100
```


## Useful SPARQL Queries

### List All Data Model Instances


```sparql
PREFIX sdc4: <https://semanticdatacharter.com/ns/sdc4/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?instance ?type WHERE {
  ?instance rdf:type ?type .
  FILTER(STRSTARTS(STR(?type), "https://semanticdatacharter.com"))
}
```


### Count Records by Type


```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?type (COUNT(?instance) AS ?count) WHERE {
  ?instance rdf:type ?type .
}
GROUP BY ?type
ORDER BY DESC(?count)
```


### Find a Specific Instance


```sparql
PREFIX sdc4: <https://semanticdatacharter.com/ns/sdc4/>

SELECT ?predicate ?object WHERE {
  <YOUR_INSTANCE_URI_HERE> ?predicate ?object .
}
```


### Search by Label or Text


```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subject ?label WHERE {
  ?subject rdfs:label ?label .
  FILTER(CONTAINS(LCASE(?label), "search term"))
}
```


## Understanding the Query Interface

The Fuseki query interface (YASGUI) provides:
- **Syntax highlighting** for SPARQL queries
- **Autocomplete** for common prefixes
- **Multiple result formats**: Table, Raw Response, Pivot Table
- **Download options**: CSV, JSON, XML

## Common Prefixes

Add these at the top of your queries:


```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX sdc4: <https://semanticdatacharter.com/ns/sdc4/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
```


## Data Loaded Automatically

On startup, your application loads:
- **SDC4 Core Ontology** (`sdc4.ttl`) - Defines the SDC4 data types and structures
- **SDC4 Metadata Ontology** (`sdc4-meta.ttl`) - Defines metadata properties
- **Data Model Schema** (`dm-*.ttl`) - Your specific data model definition in Turtle format

## Tips for Beginners


1. **Start simple**: Use `SELECT * WHERE { ?s ?p ?o } LIMIT 10` to see sample data

2. **Use LIMIT**: Always add `LIMIT` when exploring to avoid overwhelming results
3. **Check prefixes**: Most URIs can be shortened with prefixes for readability
4. **Export results**: Use the download button to export query results as CSV for Excel

## Programmatic Access

### Python (using SPARQLWrapper)


```python
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:13030/sdc4_rdf/sparql")
sparql.setQuery("""
    SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

for result in results["results"]["bindings"]:
    print(result)
```


### cURL (Command Line)


```bash
curl -X POST http://localhost:13030/sdc4_rdf/sparql \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/json" \
  -d "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
```


## Business Intelligence Tools

Your triplestore data can also be accessed by external business intelligence and visualization tools such as [Tableau](https://www.tableau.com/), Power BI, and others. These tools can connect to SPARQL endpoints via ODBC/JDBC bridges or by consuming exported data formats (CSV, JSON) from SPARQL queries. This enables integration of your semantic data into corporate reporting workflows and advanced visualizations. Configuring these connectors is beyond the scope of this guide, but the SPARQL endpoint at `http://localhost:13030/sdc4_rdf/sparql` is compatible with standard connector tools.

## Further Reading

- [SPARQL Tutorial (W3C)](https://www.w3.org/TR/sparql11-query/)
- [Apache Jena Fuseki Documentation](https://jena.apache.org/documentation/fuseki2/)
- [SDC4 Specification](https://semanticdatacharter.com)

## Troubleshooting

**"No data returned"**: Check that your application has created records and that Fuseki initialization completed successfully.

**"Connection refused"**: Ensure Docker containers are running (`docker compose ps`).

**"Authentication required"**: Use the credentials above or check your `.env` file.
