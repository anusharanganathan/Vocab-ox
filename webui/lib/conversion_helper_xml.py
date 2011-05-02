import subprocess
import os
import xml.etree.ElementTree as ET
from rdflib.Graph import ConjunctiveGraph as Graph
from webui.config.rdfconfig import namespaces

def validate(vocabfile):
    cwd = os.getcwd()
    os.chdir('/opt/eyeball-2.3-validator')
    p = subprocess.Popen("java jena.eyeball -assume owl -check /opt/internalVocabularies/test_vocab/index.rdf", shell=True, stdout=subprocess.PIPE)
    p.wait()
    returncode = p.returncode
    output = p.stdout.read()
    os.chdir(cwd)
    return (returncode, output)

def get_type_definitions(vocabfile):
    tree = ET.ElementTree(file=vocabfile)
    def_tags = [
        "{http://www.w3.org/2000/01/rdf-schema#}Class".lower(),
        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Property".lower(),
        "{http://www.w3.org/2002/07/owl#}ObjectProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}DatatypeProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}Class".lower()
    ]

    roottag = tree.getroot()
    type_definitions = []
    vocabs = roottag.getiterator()
    definition = True
    for vocab in vocabs:
        if vocab.tag.lower().strip() in def_tags:
            if not vocab.tag in type_definitions:
                type_definitions.append(vocab.tag)
            defby = None
            defby = vocab.find("{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy")
            if not defby:
                definition = False
    return (definition, type_definitions)

def get_terms(vocabfile):
    tree = ET.ElementTree(file=vocabfile)
    def_tags = [
        "{http://www.w3.org/2000/01/rdf-schema#}Class".lower(),
        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Property".lower(),
        "{http://www.w3.org/2002/07/owl#}ObjectProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}DatatypeProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}Class".lower()
    ]

    roottag = tree.getroot()
    subjects = []
    vocabs = roottag.getiterator()
    for vocab in vocabs:
        if vocab.tag.lower().strip() in def_tags:
            s = None
            s = vocab.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
            defby = None
            defby = vocab.find("{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy")
            if not defby and not s in subjects:
                subjects.append(s)
    return subjects

def check_conversion_readiness(vocabfile):
    tree = ET.ElementTree(file=vocabfile)
    status = {}
    status['identifier'] = None
    status['title'] = None
    status['isVersionOf'] = None
    status['hasFormat'] = {}
    status['hasFormat']['html'] = None
    status['hasFormat']['rdf'] = None
    status['isDefinedBy'] = True

    def_tags = [
        "{http://www.w3.org/2000/01/rdf-schema#}Class".lower(),
        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Property".lower(),
        "{http://www.w3.org/2002/07/owl#}ObjectProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}DatatypeProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}Class".lower(),
    ]

    message = {} 
    message['identifier'] = "Need to add the property dc:identifier 'vocaburi/schema' as a child of owl:Ontology"
    message['title'] = "Need to add the property dc:title as a child of owl:Ontology"
    message['isVersionOf'] = "Need to add the property dcterms:isVersionOf 'vocabprefix' as a child of owl:Ontology"
    message['hasFormat'] = {}
    message['hasFormat']['html'] = "Need to add the property dcterms:hasFormat 'text/html' as a child of owl:Ontology"
    message['hasFormat']['rdf'] = "Need to add the property dcterms:hasFormat 'application/rdf+xml' as a child of owl:Ontology"
    message['isDefinedBy'] = "Need to add the property rdfs:isDefineBy 'vocabprefix' for each property and class definition"

    vocabs = tree.findall("{http://www.w3.org/2002/07/owl#}Ontology")
    for vocab in vocabs:
        terms = vocab.getiterator()
        for term in terms:
            k = term.tag.split('}')[-1]
            if term.tag in ["{http://purl.org/dc/elements/1.1/}identifier",
                        "{http://purl.org/dc/elements/1.1/}title",
                        "{http://purl.org/dc/terms/}isVersionOf"]:
                if term.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"):
                    status[k] = term.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                elif term.text:
                    status[k] = term.text
            elif term.tag == "{http://purl.org/dc/terms/}hasFormat":
                fname = None
                ftype = None
                fn_tag = term.find("{http://purl.org/dc/dcmitype/}Text")
                if fn_tag:
                    fname = fn_tag.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
                    ft_tags = fn_tag.findall(".//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
                    for ft_tag in ft_tags:
                        if ft_tag.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"):
                            ftype = ft_tag.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                        elif ft_tag.text:
                            ftype = ft_tag.text
                if ftype and fname and 'html' in ftype.lower():
                    status['hasFormat']['html'] =  fname
                elif ftype and fname and 'rdf' in ftype.lower():
                    status['hasFormat']['rdf'] = fname
            elif term.tag.lower().strip() in def_tags:
                defby = None
                defby = term.find("{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy")
                if not defby:
                    status['isDefinedBy'] = False
    changes = []
    for k, v in status.iteritems():
        if k == 'hasFormat':
            if not v['html']:
                changes.append(message[k]['html'])
            if not v['rdf']:
                changes.append(message[k]['rdf'])
        else:
            if not v:
                changes.append(message[k])
    return changes

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def update_rdf_for_conversion(vocabprefix, vocab_properties, rdf_vocab_properties):
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
    graph_ns = []
    for nsprefix, nsurl in graph.namespaces():
        graph_ns.append(str(nsurl))
        ET._namespace_map[str(nsurl)] = str(nsprefix)
    for prefix, url in namespaces.iteritems():
        if not str(url) in graph_ns:
            ET._namespace_map[str(url)] = str(prefix)

    def_tags = [
        "{http://www.w3.org/2000/01/rdf-schema#}Class".lower(),
        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Property".lower(),
        "{http://www.w3.org/2002/07/owl#}ObjectProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}DatatypeProperty".lower(),
        "{http://www.w3.org/2002/07/owl#}Class".lower(),
    ]

    tree = ET.ElementTree(file=rdf_vocab_properties['path'])
    ns_uri = vocab_properties['preferredNamespaceUri']
    html_uri = html_vocab_properties['uri']
    rdf_uri = rdf_vocab_properties['uri']

    tree_root = tree.getroot()
    #vocab= tree_root.findall("{http://www.w3.org/2002/07/owl#}Ontology")
    vocab= tree_root.find("{http://www.w3.org/2002/07/owl#}Ontology")
    if vocab:
        #for vocab in vocabs:
        if not vocab.findall("{http://purl.org/dc/elements/1.1/}identifier"):
            se0 = ET.SubElement(vocab, "{http://purl.org/dc/elements/1.1/}identifier")
            se0.text = rdf_uri
        if not vocab.findall("{http://purl.org/dc/terms/}isVersionOf"):
            se1 = ET.SubElement(vocab, "{http://purl.org/dc/terms/}isVersionOf", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":ns_uri})
        if not vocab.findall("{http://purl.org/vocab/vann/}preferredNamespacePrefix"):
            se2a = ET.SubElement(vocab, "{http://purl.org/vocab/vann/}preferredNamespacePrefix")
            se2a.text = vocab_properties['preferredNamespacePrefix']
        if not vocab.findall("{http://purl.org/vocab/vann/}preferredNamespaceUri"):
            se2b = ET.SubElement(vocab, "{http://purl.org/vocab/vann/}preferredNamespaceUri")
            se2b.text = vocab_properties['preferredNamespaceUri']
        if not vocab.findall("{http://purl.org/dc/terms/}hasFormat"):
            #Add html uri - html_vocab_properties['uri']
            se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
            se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":html_uri})
            se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
            se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
            se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
            se3e.text = 'text/html'
            #ET.TreeBuilder.data('text/html')
            se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
            se3f.text = 'HTML'
            #ET.TreeBuilder.data('HTML')
            #Add rdf uri - rdf_vocab_properties['uri']
            se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
            se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":rdf_uri})
            se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
            se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
            se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
            se3e.text = 'application/rdf+xml'
            #ET.TreeBuilder.data('application/rdf+xml')
            se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
            se3f.text = 'RDF'
            #ET.TreeBuilder.data('RDF')
        else:
            #Check the formats available and add if necessary
            formats = vocab.findall("{http://purl.org/dc/terms/}hasFormat")
            available_types = []
            for f in formats:
                type_tags = f.findall(".//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
                for type_tag in type_tags:
                    if type_tag.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"):
                        ftype = type_tag.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                    elif type_tag.text:
                        ftype = type_tag.text
                    if ftype and 'html' in ftype.lower():
                        available_types.append('html')
                    elif ftype and 'rdf' in ftype.lower():
                        available_types.append('rdf')
            if not 'html' in available_types:
                #Add html file - vocabfile_html
                se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
                se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":html_uri})
                se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
                se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
                se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
                se3e.text = 'text/html'
                #ET.TreeBuilder.data('text/html')
                se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
                se3f.text = 'HTML'
                #ET.TreeBuilder.data('HTML')
            if not 'rdf' in available_types:
                #Add rdf file - vocabfile
                se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
                se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":rdf_uri})
                se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
                se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
                se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
                se3e.text = 'application/rdf+xml'
                #ET.TreeBuilder.data('application/rdf+xml')
                se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
                se3f.text = 'RDF'
                #ET.TreeBuilder.data('RDF')
    else:
        vocab = ET.SubElement(tree_root, "{http://www.w3.org/2002/07/owl#}Ontology", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":ns_uri})
        se0 = ET.SubElement(vocab, "{http://purl.org/dc/elements/1.1/}identifier")
        se0.text = rdf_uri
        se1 = ET.SubElement(vocab, "{http://purl.org/dc/terms/}isVersionOf", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":ns_uri})
        se2a = ET.SubElement(vocab, "{http://purl.org/vocab/vann/}preferredNamespacePrefix")
        se2a.text = vocab_properties['preferredNamespacePrefix']
        se2b = ET.SubElement(vocab, "{http://purl.org/vocab/vann/}preferredNamespaceUri")
        se2b.text = vocab_properties['preferredNamespaceUri']
        #Add html uri - html_vocab_properties['uri']
        se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
        se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":html_uri})
        se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
        se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
        se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
        se3e.text = 'text/html'
        se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
        se3f.text = 'HTML'
        #Add rdf uri - rdf_vocab_properties['uri']
        se3a = ET.SubElement(vocab, "{http://purl.org/dc/terms/}hasFormat")
        se3b = ET.SubElement(se3a, "{http://purl.org/dc/dcmitype/}Text", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":rdf_uri})
        se3c = ET.SubElement(se3b, "{http://purl.org/dc/elements/1.1/}format")
        se3d = ET.SubElement(se3c, "{http://purl.org/dc/terms/}IMT")
        se3e = ET.SubElement(se3d, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value")
        se3e.text = 'application/rdf+xml'
        se3f = ET.SubElement(se3d, "{http://www.w3.org/2000/01/rdf-schema#}label", attrib={"{http://www.w3.org/XML/1998/namespace}lang":"en"})
        se3f.text = 'RDF'
    terms = tree_root.getiterator()
    #terms = vocab.getiterator()
    for term in terms:
        if term.tag.lower().strip() in def_tags:
            defby = None
            defby = term.find("{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy")
            if not defby:
                se4 = ET.SubElement(term, "{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy", attrib={"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":ns_uri})

    #Move ontology to the first element
    tree_root.remove(vocab)
    tree_root.insert(0, vocab)

    tree.write(newrdf_vocab_properties['path'])
    #tree_root.write(newrdf_vocab_properties['path'])
    return (newrdf_vocab_properties, html_vocab_properties)
