import uuid, codecs, os, mimetypes
from collections import defaultdict
import subprocess
from rdflib.Graph import ConjunctiveGraph as Graph
from rdflib import Literal, BNode, URIRef
from webui.config.rdfconfig import namespaces
from webui.config.rdfconfig import vocab_properties, vocab_type_definitions_rdfs, vocab_type_definitions_owl, vocab_type_definitions_test
from webui.lib.conversion_helper import get_terms
from pylons import app_globals as ag

#======================================================================================
#Functions below operate on the vocab status file and the mediator/owner file
#======================================================================================
def del_vocab_from_creator(userid, vocab):
    if not os.path.isfile(os.path.join(ag.creatorsdir, '%s.rdf'%userid)):
        return False
    graph = Graph()
    graph.parse(os.path.join(ag.creatorsdir, '%s.rdf'%userid))
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    for s, p, o in graph.triples((URIRef(vocab_uri), namespaces['dcterms']['mediator'], None)):
        graph.remove((s, p, o))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(creatorfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True 

#======================================================================================
#Functions below operate on the rdf file of the uploaded vocab
#======================================================================================

def check_propeties(vocabfile):
    graph = Graph()
    try:
        graph.parse(vocabfile)
    except:
        return {}

    subject = none
    for s in graph.subjects(namespaces['dc']['title'], None):
        subject = s
    if not subject:
        for s in graph.subjects(namespaces['dcterms']['title'], None):
            subject = s
    if not subject:
        for s in graph.subjects(namespaces['dc']['creator'], None):
            subject = s
    if not subject:
        for s in graph.subjects(namespaces['dcterms']['creator'], None):
            subject = s

    properties = {}

    #Identifier
    identifier = []
    ids = graph.objects(subject, namespaces['dc']['identifier'])
    for id in ids:
        identifier = id
    if not identifier:
        ids = graph.objects(subject, namespaces['dcterms']['identifier'])
        for id in ids:
            identifier.append(id)
    properties['identifier'] = [id]
    
    #hasFormat
    format = False
    
    prop1 = True
    prop2 = False
    prop3 = False
    properties['format'] = []
    for fm in graph.objects(subject, namespaces['dcterms']['hasFormat']):
        properties['format'].append(fm)
        bnodes = graph.objects(fm, namespaces['dc']['format'])
        for b in bnodes:
            for value in graph.objects(b, namespaces['rdf']['value']):
                prop1 = True
            for value in graph.objects(b, namespaces['rdfs']['label']):
                prop2 = True
            for value in graph.objects(b, namespaces['rdfs']['type']):
                prop3 = True
        if not 'all' in properties:
            properties['all'] = prop1 and prop2 and prop3
        else:
            properties['all'] = properties['all'] and prop1 and prop2 and prop3

    conforms = False
    if identifier and properties['format'] and properties['all']:
         conforms = True
    
    return (conforms, properties)

def check_type_definitions(vocabfile):
    graph = Graph()
    try:
        graph.parse(vocabfile)
    except:
        return False
    all_definitions = True
    
    testo = vocab_type_definitions_test['rdfs']
    subjects = []
    subs = graph.subjects(namespaces['rdf']['type'], URIRef(testo))
    for s in subs:
        subjects.append(s)
    if subjects:
        objects = vocab_type_definitions_rdfs
    else:
        objects = vocab_type_definitions_owl
    for o in objects: 
        subs = graph.subjects(namespaces['rdf']['type'], o)
        done = []
        for s in subs:
            if s in done:
               continue
            done.append(s) 
            definition = False
            vals = graph.objects(s, namespaces['rdfs']['isDefinedBy'])
            for val in vals:
               definition = True
            all_definitions = all_definitions and definition
    return all_definitions

def update_rdf_for_conversion(prefix, vocab_properties, rdf_vocab_properties):

    #(id, base, prefix) = get_vocab_base(vocabfile)
    html_vocab_properties = {}
    html_vocab_properties['format'] = 'text/html'
    html_vocab_properties['name'] = "%s.html"%os.path.splitext(rdf_vocab_properties['name'])[0]
    html_vocab_properties['path'] = rdf_vocab_properties['path'].replace(rdf_vocab_properties['name'], html_vocab_properties['name'])
    html_vocab_properties['uri'] = rdf_vocab_properties['uri'].replace(rdf_vocab_properties['name'], html_vocab_properties['name'])

    newrdf_vocab_properties = {}
    newrdf_vocab_properties['format'] = 'application/rdf+xml'
    newrdf_vocab_properties['name'] = "%s_modified.rdf"%os.path.splitext(rdf_vocab_properties['name'])[0]
    newrdf_vocab_properties['path'] = rdf_vocab_properties['path'].replace(rdf_vocab_properties['name'], newrdf_vocab_properties['name'])
    newrdf_vocab_properties['uri'] = rdf_vocab_properties['uri'].replace(rdf_vocab_properties['name'], newrdf_vocab_properties['name'])

    graph = Graph()
    graph.parse(rdf_vocab_properties['path'])

    subject = None
    for s in graph.subjects(namespaces['rdf']['type'], URIRef(namespaces['owl']['Ontology'])):
        subject = s

    #graph2 = Graph()
    graph_ns = []
    for nsprefix, nsurl in graph.namespaces():
        graph_ns.append(str(nsurl))
    for prefix, url in namespaces.iteritems():
        if not str(url) in graph_ns:
            graph.bind(prefix, URIRef(url))

    
    #properties = get_vocab_properties(prefix)
    #subject = None
    #for s in graph.subjects(namespaces['dc']['title'], None):
    #    subject = s
    #if not subject:
    #    for s in graph.subjects(namespaces['dcterms']['title'], None):
    #        subject = s
    #if not subject:
    #    for s in graph.subjects(namespaces['dc']['creator'], None):
    #        subject = s
    #if not subject:
    #    for s in graph.subjects(namespaces['dcterms']['creator'], None):
    #        subject = s

    formatNode1 = BNode()
    formatNode2 = BNode()

    #Add vocabulary properties identifier and format
    graph.add((subject, namespaces['dc']['identifier'], URIRef(rdf_vocab_properties['uri'])))
    graph.add((subject, namespaces['dcterms']['isVersionOf'], URIRef(vocab_properties['preferredNamespaceUri'])))
    graph.add((subject, namespaces['dcterms']['hasFormat'], URIRef(rdf_vocab_properties['uri'])))
    graph.add((subject, namespaces['dcterms']['hasFormat'], URIRef(html_vocab_properties['uri'])))
    graph.add((subject, namespaces['vann']['preferredNamespaceUri'], URIRef(vocab_properties['preferredNamespaceUri'])))
    graph.add((subject, namespaces['vann']['preferredNamespacePrefix'], URIRef(vocab_properties['preferredNamespacePrefix'])))

    graph.add((URIRef(html_vocab_properties['uri']), namespaces['rdf']['type'], URIRef(namespaces['dctype']['Text'])))
    graph.add((URIRef(html_vocab_properties['uri']), namespaces['dc']['format'], formatNode1))
    graph.add((formatNode1, namespaces['rdf']['value'], Literal('text/html')))
    graph.add((formatNode1, namespaces['rdfs']['label'], Literal('HTML')))
    graph.add((formatNode1, namespaces['rdf']['type'], URIRef(namespaces['dcterms']['IMT'])))

    graph.add((URIRef(rdf_vocab_properties['uri']), namespaces['rdf']['type'], URIRef(namespaces['dctype']['Text'])))
    graph.add((URIRef(rdf_vocab_properties['uri']), namespaces['dc']['format'], formatNode2))
    graph.add((formatNode2, namespaces['rdf']['value'], Literal('application/rdf+xml')))
    graph.add((formatNode2, namespaces['rdfs']['label'], Literal('RDF')))
    graph.add((formatNode2, namespaces['rdf']['type'], URIRef(namespaces['dcterms']['IMT'])))

    #Add rdfs:isDefinedBy for each class / property / term of the vocabulary
    #Find if schema is rdfs / owl. This defines the possible types (rdf:type) for each class / property / term
    #testo = vocab_type_definitions_test['rdfs']
    #subjects = []
    #subs = graph.subjects(namespaces['rdf']['type'], URIRef(testo))
    #for s in subs:
    #    subjects.append(s)
    #if subjects:
    #    objects = vocab_type_definitions_rdfs
    #else:
    #    objects = vocab_type_definitions_owl

    #For all subjects that are of the type found above, add rdfs:isDefinedBy
    #for o in objects: 
    #    subs = graph.subjects(namespaces['rdf']['type'], o)
    #    for s in subs:
    #        graph.add((s, namespaces['rdfs']['isDefinedBy'], URIRef(vocab_properties['preferredNamespaceUri'])))

    list_of_terms = get_terms(rdf_vocab_properties['path'])
    for s in list_of_terms:
        graph.add((URIRef(s), namespaces['rdfs']['isDefinedBy'], URIRef(vocab_properties['preferredNamespaceUri'])))

    rdf_str = None
    rdf_str = graph.serialize(format="pretty-xml")
    #f = codecs.open(newrdf_vocab_properties['path'], 'w', 'utf-8')
    f = codecs.open(newrdf_vocab_properties['path'], 'w')
    f.write(rdf_str)
    f.close()
    return (newrdf_vocab_properties, html_vocab_properties)

def convert_to_html(new_rdf_file, new_html_file):
    command = "xsltproc %s %s > %s"%(ag.conversion_xsl, new_rdf_file, new_html_file)
    p = subprocess.Popen(command, shell=True)
    (stdoutdata, stderrdata) = p.communicate()
    return (stdoutdata, stderrdata)
