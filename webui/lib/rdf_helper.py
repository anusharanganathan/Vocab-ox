import uuid, codecs, os, mimetypes
from collections import defaultdict
from rdflib.Graph import ConjunctiveGraph as Graph
from rdflib import Literal, URIRef
from webui.config.rdfconfig import namespaces, vocab_description, vocab_description_uri, vocab_editorial_descriptions 
from webui.lib.utils import get_file_mimetype
from pylons import app_globals as ag

#======================================================================================
#Functions below operate on the vocab status file and the mediator/owner file
#======================================================================================

def add_mediator(params):
    #Write user metadata and save the rdf file
    graph = Graph()
    for prefix, url in namespaces.iteritems():
        graph.bind(prefix, URIRef(url))
    uri = URIRef("http://vocab.ox.ac.uk/owner/uuid:%s"%uuid.uuid4())
    graph.add((uri, namespaces['foaf']['firstName'], Literal(params['firstname'])))
    graph.add((uri, namespaces['foaf']['lastName'], Literal(params['lastname'])))
    graph.add((uri, namespaces['foaf']['mbox'], Literal(params['email'])))
    graph.add((uri, namespaces['foaf']['account'], Literal(params['username'])))
    if 'title' in params and params['title']:
        graph.add((uri, namespaces['foaf']['title'], Literal(params['title'])))
    if 'department' in params and params['department']:
        department = department.split(';')
        for d in deparmtnet:
            graph.add((uri, namespaces['dcterms']['isPartOf'], Literal(d.strip())))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(os.path.join(ag.mediatorsdir, '%s.rdf'%params['username']), 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    graph2 = Graph()
    graph2.parse(ag.mediatorslist)
    for prefix, url in namespaces.iteritems():
        graph2.bind(prefix, URIRef(url))
    graph2.add((uri, namespaces['foaf']['account'], Literal(params['username'])))
    rdf_str = None
    rdf_str = graph2.serialize()
    f = codecs.open(ag.mediatorslist, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def update_mediator(params):
    #Write user metadata and save the rdf file
    if not ('username' in params and params['username']):
        return False
    det = get_mediator_details(params['username'])
    graph = Graph()
    graph.parse(os.path.join(ag.mediatorsdir, '%s.rdf'%params['username']))
    for prefix, url in namespaces.iteritems():
        graph.bind(prefix, URIRef(url))
    uri = URIRef(det['uri'])
    if 'firstname' in params and params['firstname']:
        graph.remove((uri, namespaces['foaf']['firstName'], None))
        graph.add((uri, namespaces['foaf']['firstName'], Literal(params['firstname'])))
    if 'lastname' in params and params['lastname']:
        graph.remove((uri, namespaces['foaf']['lastName'], None))
        graph.add((uri, namespaces['foaf']['lastName'], Literal(params['lastname'])))
    if 'email' in params and params['email']:
        graph.remove((uri, namespaces['foaf']['mbox'], None))
        graph.add((uri, namespaces['foaf']['mbox'], Literal(params['email'])))
    if 'title' in params and params['title']:
        graph.remove((uri, namespaces['foaf']['title'], None))
        graph.add((uri, namespaces['foaf']['title'], Literal(params['title'])))
    if 'department' in params and params['department']:
        graph.remove((uri, namespaces['dcterms']['isPartOf'], None))
        department = params['department'].split(';')
        for d in department:
            graph.add((uri, namespaces['dcterms']['isPartOf'], Literal(d.strip())))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(os.path.join(ag.mediatorsdir, '%s.rdf'%params['username']), 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def get_mediator_account(user_uuid):
    uri = URIRef("http://vocab.ox.ac.uk/owner/%s"%user_uuid)
    graph = Graph()
    graph.parse(ag.mediatorslist)
    for account in graph.objects(uri, namespaces['foaf']['account']):
        if account:
            return account
    return False

def get_mediator_details(userid):
    #Get mediator_details - firstname, lastname, department, email
    details = {}
    details['userid'] = userid
    details['uri'] = None
    details['name'] = None
    details['fname'] = None
    details['lname'] = None
    details['title'] = None
    details['email'] = None
    details['dept'] = []
    if userid.startswith('uuid'):
        userid = get_mediator_account(userid)
        details['userid'] = userid
        if not userid:
            return details
    if not os.path.isfile(os.path.join(ag.mediatorsdir, '%s.rdf'%userid)):
        return details
    graph = Graph()
    graph.parse(os.path.join(ag.mediatorsdir, '%s.rdf'%userid))
    t = ''
    f = ''
    l = ''
    for title in graph.objects(None, namespaces['foaf']['title']):
        if title.strip():
            t = title
            details['title'] = t
    for fname in graph.objects(None, namespaces['foaf']['firstName']):
        if fname.strip():
            f = fname
            details['fname'] = fname
    for lname in graph.objects(None, namespaces['foaf']['lastName']):
        if lname.strip():
            l = lname
            details['lname'] = lname
    details['name'] = "%s %s %s"%(t, f, l)
    details['name'] = details['name'].strip()
    if not details['name']:
        details['name'] = userid
    for email in graph.objects(None, namespaces['foaf']['mbox']):
        details['email'] = email
    for dept in graph.objects(None, namespaces['dcterms']['isPartOf']):
        details['dept'].append(dept)
    for uri in graph.subjects(namespaces['foaf']['account'], None):
        details['uri'] = uri
    return details

def get_mediator_vocabs(userid):
    vocabs = {}
    if not os.path.isfile(os.path.join(ag.mediatorsdir, '%s.rdf'%userid)):
        "Cannot find file %s"%os.path.join(ag.mediatorsdir, '%s.rdf'%userid)
        return vocabs
    #Get list of vocabularies created by userid
    graph = Graph()
    graph.parse(os.path.join(ag.mediatorsdir, '%s.rdf'%userid))
    for v in graph.subjects(namespaces['dcterms']['mediator'], None):
        k = v.split('/')[-1]
        svn_src = "http://damssupport.ouls.ox.ac.uk/trac/vocab/browser/trunks/internalVocabularies/%s"%k
        vocabs[k] = (v, svn_src)
    return vocabs

def create_vocab_statusfile(userid, vocabprefix, vocabfile, baseuri, update=False, using_uuid=False, refvocab=False):
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    vocabdir = os.path.join(ag.vocabulariesdir, str(vocabprefix))
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    vocab_file_name = os.path.basename(vocabfile)
    vocabfile_uri = URIRef("http://vocab.ox.ac.uk/%s/%s"%(vocabprefix, vocab_file_name))

    #Add vocab in mediator file
    graph = Graph()
    mediatorfile = os.path.join(ag.mediatorsdir, '%s.rdf'%userid)
    graph.parse(mediatorfile)
    user_uri = []
    for uri in graph.subjects(namespaces['foaf']['account'], Literal(userid)):
        if not uri in user_uri:
            user_uri.append(uri)
    user_uri = URIRef(user_uri[0])
    graph.add((vocab_uri, namespaces['dcterms']['mediator'], URIRef(user_uri)))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(mediatorfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()

    #Add vocab in vocab status file
    graph = Graph()
    if update and os.path.isfile(vocabstatusfile):
        graph.parse(vocabstatusfile)
    for prefix, url in namespaces.iteritems():
        graph.bind(prefix, URIRef(url))
    graph.add((vocab_uri, namespaces['dcterms']['mediator'], URIRef(user_uri)))
    graph.add((user_uri, namespaces['foaf']['account'], Literal(userid)))
    graph.add((vocab_uri, namespaces['dcterms']['hasFormat'], URIRef(vocabfile_uri)))
    graph.add((vocab_uri, namespaces['vann']['preferredNamespaceUri'], URIRef(baseuri)))
    graph.add((vocab_uri, namespaces['vann']['preferredNamespacePrefix'], Literal(vocabprefix)))
    graph.add((vocab_uri, namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[0])))
    if refvocab:
        add_ref_vocab(vocabprefix, refvocab)
        graph.add((vocab_uri, namespaces['dcterms']['isVersionOf'], URIRef(refvocab)))
    # get mimetype of file
    if os.path.isfile(vocabfile):
        graph.add((vocabfile_uri, namespaces['nfo']['fileUrl'], Literal('file://%s'%vocabfile)))
        graph.add((vocabfile_uri, namespaces['nfo']['fileName'], Literal(vocab_file_name)))
        mt = None
        if check_rdf(vocabfile):
            mt = 'application/rdf+xml'
            graph.add((vocabfile_uri, namespaces['dcterms']['conformsTo'], Literal(mt)))
            graph.add((vocabfile_uri, namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[3])))
        elif check_n3(vocabfile):
            mt = 'text/rdf+nt'
            root, ext = os.path.splitext(vocabfile)
            if ext == '.rdf':
                rdffile = "%s_2.rdf"%root
            else:
                rdffile = "%s.rdf"%root
            converttordf = convert_n3_rdf(vocabfile, rdffile)
            if converttordf and os.path.isfile(rdffile):
                rdf_file_name = os.path.basename(rdffile)
                rdffile_uri = URIRef("http://vocab.ox.ac.uk/%s/%s"%(vocabprefix, rdf_file_name))
                graph.add((vocab_uri, namespaces['dcterms']['hasFormat'], URIRef(rdffile_uri)))
                graph.add((rdffile_uri, namespaces['nfo']['fileUrl'], Literal('file://%s'%rdffile)))
                graph.add((rdffile_uri, namespaces['nfo']['fileName'], Literal(rdf_file_name)))
                graph.add((rdffile_uri, namespaces['dcterms']['conformsTo'], Literal('application/rdf+xml')))
                graph.add((rdffile_uri, namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[3])))
                graph.add((rdffile_uri, namespaces['dcterms']['format'], Literal('application/rdf+xml')))
        else:
            mt1 = mimetypes.guess_type(vocabfile)
            mt2 = get_file_mimetype(vocabfile)
            if mt1[0]:
                mt = mt1[0]
            else:
                mt = mt2
            if str(mt) == 'application/rdf+xml':
                graph.add((vocabfile_uri, namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[2])))
            else:
                graph.add((vocab_uri, namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[1])))
        if mt:
            graph.add((vocabfile_uri, namespaces['dcterms']['format'], Literal(mt)))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(vocabstatusfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def add_file_to_vocab_status(vocabprefix, properties, addHasFormat=True):
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    vocaburi = "http://vocab.ox.ac.uk/%s"%vocabprefix
    
    if not 'name' in properties or not properties['name'] or not 'path' in properties or not properties['path']:
        return False
    if not 'uri' in properties or not properties['uri']:
        properties['uri'] = URIRef("http://vocab.ox.ac.uk/%s/%s"%(vocabprefix, properties['name']))
    if not 'format' in properties or not properties['format']:
        # get mimetype of file
        mt = None
        if os.path.isfile(vocabfile):
            if check_rdf(vocabfile):
                properties['format'] = 'application/rdf+xml'
            else:
                mt1 = mimetypes.guess_type(vocabfile)
                if mt1[0]:
                    properties['format'] = mt1[0]
                else:
                    properties['format'] = get_file_mimetype(vocabfile)
    graph = Graph()
    if os.path.isfile(vocabstatusfile):
        graph.parse(vocabstatusfile)
    else:
        return False
    for prefix, url in namespaces.iteritems():
        graph.bind(prefix, URIRef(url))
    if addHasFormat:
        graph.add((URIRef(vocaburi), namespaces['dcterms']['hasFormat'], URIRef(properties['uri'])))
    if properties['format']:
        graph.add((URIRef(properties['uri']), namespaces['dcterms']['format'], Literal(properties['format'])))
    if os.path.isfile(properties['path']):
        graph.add((URIRef(properties['uri']), namespaces['nfo']['fileUrl'], Literal('file://%s'%properties['path'])))
        graph.add((URIRef(properties['uri']), namespaces['nfo']['fileName'], Literal(properties['name'])))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(vocabstatusfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def update_vocab_uri_in_statusfile(userid, oldprefix, newprefix, oldvocabdir, newvocabdir):
    olduri = "http://vocab.ox.ac.uk/%s"%oldprefix
    newuri = "http://vocab.ox.ac.uk/%s"%newprefix

    mediatorfile = os.path.join(ag.mediatorsdir, '%s.rdf'%userid)
    vocabstatusfile = os.path.join(newvocabdir, 'status.rdf')
    if not os.path.isfile(mediatorfile) or not os.path.isfile(vocabstatusfile):
        return False

    #update uri in mediator file
    rdf_str = None
    f = codecs.open(mediatorfile, 'r', 'utf-8')
    rdf_str = f.read()
    f.close() 
    rdf_str = rdf_str.replace(olduri, newuri)
    rdf_str = rdf_str.replace(oldvocabdir, newvocabdir)
    f = codecs.open(mediatorfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    
    #update uri in vocab status file
    rdf_str = None
    f = codecs.open(vocabstatusfile, 'r', 'utf-8')
    rdf_str = f.read()
    f.close()
    rdf_str = rdf_str.replace(olduri, newuri)
    rdf_str = rdf_str.replace(oldvocabdir, newvocabdir)
    f = codecs.open(vocabstatusfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()

    #Remove editorial note 0
    graph = Graph()
    graph.parse(vocabstatusfile)
    for s, p, o in graph.triples((URIRef(newuri), namespaces['skos']['editorialNote'], Literal(vocab_editorial_descriptions[0]))):
        graph.remove((s, p, o))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(vocabstatusfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def change_status(vocabprefix, uri, predicate, message, action):
    if not action in ['add', 'remove']:
        return False
    vocab_uri = URIRef(uri)
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    if not os.path.isfile(vocabstatusfile):
        return False
    graph = Graph()
    graph.parse(vocabstatusfile)
    predicate = predicate.split(':')
    ns = predicate[0]
    term = predicate[1]
    if message and (message.startswith('http://') or message.startswith('file://')):
        message = URIRef(message)
    elif message:
        message = Literal(message)
    if action == 'add':
        for prefix, url in namespaces.iteritems():
            graph.bind(prefix, URIRef(url))
        graph.add((vocab_uri, namespaces[ns][term], message))
    elif action == 'remove':
        graph.remove((vocab_uri, namespaces[ns][term], message))
     
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(vocabstatusfile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def add_status(vocabprefix, uri, predicate, message):
    change_status(vocabprefix, uri, predicate, message, 'add')
    return True

def del_status(vocabprefix, uri, predicate, message):
    change_status(vocabprefix, uri, predicate, message, 'remove')
    return True

def check_rdf(rdffile):
    if not os.path.isfile(rdffile):
        return False
    graph = Graph()
    try:
        graph.parse(rdffile)
        return True
    except:
        return False

def check_n3(rdffile):
    if not os.path.isfile(rdffile):
        return False
    graph = Graph()
    try:
        graph.parse(rdffile, format="n3")
        return True
    except:
        return False

def convert_n3_rdf(n3file, rdffile):
    if not os.path.isfile(n3file):
        return False
    graph = Graph()
    try:
        graph.parse(n3file, format="n3")
    except:
        return False
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(rdffile, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def get_vocab_files(vocabprefix):
    #Get list of files for vocabulary
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    vocab_files = {}
    if not os.path.isfile(vocabstatusfile):
        return vocab_files
    graph = Graph()
    graph.parse(vocabstatusfile)
    for v in graph.objects(None, namespaces['dcterms']['hasFormat']):
        v_str = str(v)
        vocab_files[v_str] = {'name':'', 'format':'', 'path':''}

        for f in graph.objects(URIRef(v), namespaces['dcterms']['format']):
            vocab_files[v_str]['format'] = str(f)
        for n in graph.objects(URIRef(v), namespaces['nfo']['fileName']):
            vocab_files[v_str]['name'] = str(n)
        for p in graph.objects(URIRef(v), namespaces['nfo']['fileUrl']):
            vocab_files[v_str]['path'] = str(p).replace('file://', '')
    return vocab_files

def get_vocab_editorial_note(vocabprefix):
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    msgs = []
    if not os.path.isfile(vocabstatusfile):
        return msgs
    graph = Graph()
    graph.parse(vocabstatusfile)
    for s, p, o in graph.triples((None, namespaces['skos']['editorialNote'], None)):
        nm = None
        for n in graph.objects(URIRef(s), namespaces['nfo']['fileName']):
            nm = str(n)
        msgs.append((str(o), nm))
    return msgs

def get_vocab_mediator(vocabprefix):
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    mediators = {}
    if not os.path.isfile(vocabstatusfile):
        return mediators
    graph = Graph()
    graph.parse(vocabstatusfile)
    for o in graph.objects(None, namespaces['foaf']['account']):
        mediators[str(o)] = get_mediator_details(str(o))
    return mediators

def get_vocab_properties(vocabprefix):
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    vocabdir = os.path.join(ag.vocabulariesdir, vocabprefix)
    vocabstatusfile = os.path.join(vocabdir, "status.rdf")
    properties = {}
    properties['uri'] = vocab_uri
    if not os.path.isfile(vocabstatusfile):
        return properties
    properties['path'] = vocabdir
    properties['preferredNamespaceUri'] = None
    properties['preferredNamespacePrefix'] = None
    graph = Graph()
    graph.parse(vocabstatusfile)
    for o in graph.objects(None, namespaces['vann']['preferredNamespaceUri']):
        properties['preferredNamespaceUri'] = o
    for o in graph.objects(None, namespaces['vann']['preferredNamespacePrefix']):
        properties['preferredNamespacePrefix'] = o
    return properties

def add_ref_vocab(vocabprefix, source_uri):
    vocab_uri = URIRef("http://vocab.ox.ac.uk/%s"%vocabprefix)
    graph = Graph()
    if os.path.isfile(ag.vocabulariesref):
        graph.parse(ag.vocabulariesref)
    for prefix, url in namespaces.iteritems():
        graph.bind(prefix, URIRef(url))
    graph.add((URIRef(vocab_uri), namespaces['dcterms']['isVersionOf'], URIRef(source_uri)))
    rdf_str = None
    rdf_str = graph.serialize()
    f = codecs.open(ag.vocabulariesref, 'w', 'utf-8')
    f.write(rdf_str)
    f.close()
    return True

def get_ref_vocabs():
    reflist = {}
    if not os.path.isfile(ag.vocabulariesref):
        return reflist
    graph = Graph()
    graph.parse(ag.vocabulariesref)
    for s, p, o in graph.triples((None, namespaces['dcterms']['isVersionOf'], None)):
        reflist[str(s)] = str(o)
    return reflist

#======================================================================================
#Functions below operate on the rdf file of the uploaded vocab
#======================================================================================

def get_vocab_base(vocabfile):
    graph = Graph()
    try:
        graph.parse(vocabfile)
    except:
        graph = None
        graph = Graph()
        try:
            graph.parse(vocabfile, format="n3")
        except:
            return (None, None, None)
    identifier = None
    for v in graph.objects(None, namespaces['dc']['identifier']):
        identifier = v
    if not identifier:
        for v in graph.objects(None, namespaces['dcterms']['identifier']):
            identifier = v

    base = None
    if not base:
        for s in graph.subjects(namespaces['rdf']['type'], namespaces['owl']['Ontology']):
            base = s
            break
    if not base:
        for s in graph.subjects(namespaces['dc']['title'], None):
            base = s
            break
    if not base:
        for s in graph.subjects(namespaces['dcterms']['title'], None):
            base = s
            break
    if not base:
        for s in graph.subjects(namespaces['dc']['creator'], None):
            base = s
            break
    if not base:
        for s in graph.subjects(namespaces['dcterms']['creator'], None):
            base = s
            break
    if not base:
        for v in graph.objects(None, namespaces['vann']['preferredNamespaceUri']):
            base = v
            break
    if not base:
        for v in graph.namespaces():
            if v[0] == '':
                base = v[1]
                break

    prefix = None
    vocab_prefixes = graph.objects(None, namespaces['vann']['preferredNamespacePrefix'])
    for vp in vocab_prefixes:
        prefix = vp
    if not prefix and base:
        for v in graph.namespaces():
            if str(v[1]) == str(base):
                prefix = v[0]
                break
    if not prefix and base:
        prefix = base.strip().strip('/').split('/')[-1].strip('#').strip(' ')
    if base:
        base = base.strip()
        if (base[-1]!="/" and base[-1]!="#"):
            base += "#"
    return (identifier, base, prefix)

def get_vocab_description(vocabfile, vocabprefix):
    if not os.path.isfile(vocabfile):
        return {}
    graph = Graph()
    try:
        graph.parse(vocabfile)
    except:
        graph = None
        graph = Graph()
        try:
            graph.parse(vocabfile, format="n3")
        except:
            return {}
    descriptions = defaultdict(list)
    base = None
    properties = get_vocab_properties(vocabprefix)
    if 'preferredNamespaceUri' in properties and properties['preferredNamespaceUri']:
        base = properties['preferredNamespaceUri']
    else:
        (id, base, prefix) = get_vocab_base(vocabfile)
    if base:
        for k, predicates in vocab_description_uri.iteritems():
            for p in predicates:
                vals = None
                vals = graph.objects(URIRef(base), p)
                for val in vals:
                    if not val in descriptions[k]:
                        descriptions[k].append(val)
    for k, predicates in vocab_description.iteritems():
        if not k in descriptions or not descriptions[k]:
            for p in predicates:
                vals = graph.objects(None, p)
                for val in vals:
                    if not val in descriptions[k]:
                        descriptions[k].append(val)
    return dict(descriptions)

