from rdflib import Namespace

namespaces = {
'dc': Namespace("http://purl.org/dc/elements/1.1/"),
'dcterms':Namespace("http://purl.org/dc/terms/"),
'dctype':Namespace("http://purl.org/dc/dcmitype/"),
'foaf':Namespace("http://xmlns.com/foaf/0.1/"),
'vs':Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#"),
'nfo':Namespace("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#"),
'owl':Namespace("http://www.w3.org/2002/07/owl#"),
'rdfs':Namespace("http://www.w3.org/2000/01/rdf-schema#"),
'rdf':Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
'skos':Namespace("http://www.w3.org/2004/02/skos/core#"),
'vann':Namespace("http://purl.org/vocab/vann/")
}

user_details_map = {
'title':'foaf:title',
'firstname':'foaf:firstName',
'lastname':'foaf:lastName',
'email':'foaf:mbox',
'department':'dcterms:isPartOf'
}

vocab_description = {
'date':[namespaces['dc']['date'], namespaces['dcterms']['date']],
'title':[namespaces['dc']['title'],namespaces['dcterms']['title']],
'rights':[namespaces['dc']['rights'],namespaces['dcterms']['rights']],
'creator':[namespaces['dc']['creator'],namespaces['dcterms']['creator']],
'contributor':[namespaces['dc']['contributor'], namespaces['dcterms']['contributor']],
'desc':[namespaces['dc']['description'],namespaces['dcterms']['description']],
'version':[namespaces['owl']['versionInfo'],namespaces['dc']['version'],namespaces['dcterms']['version']]
}

vocab_description_uri = {
'date':[namespaces['dc']['date'], namespaces['dcterms']['date']],
'title':[namespaces['dc']['title'],namespaces['dcterms']['title'],namespaces['rdfs']['label']],
'rights':[namespaces['dc']['rights'],namespaces['dcterms']['rights']],
'creator':[namespaces['dc']['creator'],namespaces['dcterms']['creator']],
'contributor':[namespaces['dc']['contributor'], namespaces['dcterms']['contributor']],
'desc':[namespaces['dc']['description'],namespaces['dcterms']['description'],namespaces['rdfs']['comment']],
'version':[namespaces['owl']['versionInfo'],namespaces['dc']['version'],namespaces['dcterms']['version']]
}

vocab_properties = {
'Identifier':namespaces['dc']['identifier'],
'Vocabulary namespace URI':namespaces['dcterms']['isVersionOf'],
'Vesrions of schema':namespaces['dcterms']['hasFormat']
}

vocab_editorial_descriptions = (
"Change vocab properties",
"RDF format not available",
"Check RDF: RDF parse error",
"Generate HTML",
"HTML conversion error",
"Conversion to HTML successful"
)

