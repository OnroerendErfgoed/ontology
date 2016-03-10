rapper ontology.ttl -i turtle -o rdfxml-abbrev > ontology.rdf
rapper ontology.ttl -i turtle -o ntriples > ontology.nt
# curl --form "mimetypeFile=text/turtle" --form "datafile=@ontology.ttl" -X POST -L http://ontorule-project.eu/parrot/parrot > ontology.html
rapper licences.ttl -i turtle -o rdfxml-abbrev > licences.rdf
rapper licences.ttl -i turtle -o ntriples > licences.nt
