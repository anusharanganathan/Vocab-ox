#!/usr/bin/python
# -*- coding: utf8 -*-
# This code is taken from SpecGen v5 and modified for vocab.ox.ac.uk 
# Modified by Anusha Ranganathan
#
# Details about SpecGen v5
# SpecGen v5, ontology specification generator tool
# <http://forge.morfeo-project.org/wiki_en/index.php/SpecGen>
# 
# Copyright (c) 2003-2008 Christopher Schmidt <crschmidt@crschmidt.net>
# Copyright (c) 2005-2008 Uldis Bojars <uldis.bojars@deri.org>
# Copyright (c) 2007-2008 Sergio Fernández <sergio.fernandez@fundacionctic.org>
#
# Previous versions of SpecGen:
#     v1,2,3 by Christopher Schmidt <http://crschmidt.net/semweb/redland>
#     v4 by Uldis Bojars <http://sioc-project.org/specgen>
# 
# This software is licensed under the terms of the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import time
import re
import RDF
import codecs

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class SpecGen():
    """
    Usage: 
    from specgen import SpecGen
    s = SpecGen(ontology, prefix, vocaburi, template, destination)
    s.create_file()
    or
    s = SpecGen(ontology, prefix, vocaburi, template, destination, instances=True)
    s.create_file()
    where 
        ontology    : path to ontology file
        prefix      : prefix for CURIEs
        vocaburi    : namespace uri of the vocabulary
        template    : HTML template path
        destination : specification destination (by default)
        instances   : True / False. Add instances on the specification (disabled by default)
    examples:
        ontology = "/opt/internalVocabularies/bibo/bibo.xml.owl"
        prefix = "bibo"
        vocaburi = "http://purl.org/ontology/bibo/"
        template = "template.html" 
        destination = "/opt/webui/webui/public/onto/bibo_example.html"
    """
    __version__ = "5.4.2"
    __authors__ = "Christopher Schmidt, Uldis Bojars, Sergio Fernández"
    __license__ = "MIT License <http://www.opensource.org/licenses/mit-license.php>"
    __contact__ = "specgen-devel@lists.morfeo-project.org"
    __date__    = "2008-12-02"
 
    def __init__(self, vocabfile, prefix, uri, templatefile, outputfile, instances=False):
        self.classranges = {}
        self.classdomains = {}
        self.spec_url = None
        self.spec_ns = None
        self.ns_list = { "http://www.w3.org/1999/02/22-rdf-syntax-ns#"   : "rdf",
            "http://www.w3.org/2000/01/rdf-schema#"         : "rdfs",
            "http://www.w3.org/2002/07/owl#"                : "owl",
            "http://www.w3.org/2001/XMLSchema#"             : "xsd",
            "http://rdfs.org/sioc/ns#"                      : "sioc",
            "http://xmlns.com/foaf/0.1/"                    : "foaf", 
            "http://purl.org/dc/elements/1.1/"              : "dc",
            "http://purl.org/dc/terms/"                     : "dct",
            "http://usefulinc.com/ns/doap#"                 : "doap",
            "http://www.w3.org/2003/06/sw-vocab-status/ns#" : "status",
            "http://purl.org/rss/1.0/modules/content/"      : "content", 
            "http://www.w3.org/2003/01/geo/wgs84_pos#"      : "geo",
            "http://www.w3.org/2004/02/skos/core#"          : "skos"
          }

        self.rdf = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.rdfs = RDF.NS('http://www.w3.org/2000/01/rdf-schema#')
        self.owl = RDF.NS('http://www.w3.org/2002/07/owl#')
        self.dc =  RDF.NS('http://purl.org/dc/elements/1.1/')
        self.dct = RDF.NS('http://purl.org/dc/terms/')
        self.skos = RDF.NS('http://www.w3.org/2004/02/skos/core#')
        self.vann = RDF.NS('http://purl.org/vocab/vann/')
        self.vs = RDF.NS('http://www.w3.org/2003/06/sw-vocab-status/ns#')

        self.termdir = './doc' #TODO

        #ontology
        self.specloc = "file:" + vocabfile
        self.spec_pre = prefix
        self.ns_url = uri
        if (self.ns_url[-1]!="/" and self.ns_url[-1]!="#"):
            self.ns_url += "#"
        #template
        self.temploc = templatefile
        self.template = None
        try:
            f = open(self.temploc, "r")
            self.template = f.read()
        except Exception, e:
            raise Usage("Error reading from template %s: %s"%(self.temploc, str(e)))

        #destination
        self.dest = outputfile
 
        #flags
        self.instances = instances       
        return


    def getOntologyNS(self, m):
        ns = None
        o = m.find_statements(RDF.Statement(None, self.rdf.type, self.owl.Ontology))
        if o.current():
            s = o.current().subject
            if (not s.is_blank()):
                ns = str(s.uri)
                if (ns[-1]!="/" and ns[-1]!="#"):
                    ns += "#"

        if (ns == None):
            return self.ns_url
        else:
            return ns


    def niceName(self, uri):
        regexp = re.compile( "^(.*[/#])([^/#]+)$" )
        rez = regexp.search( uri )
        pref = None
        if rez:
            try:
                pref = rez.group(1)
            except:
                return uri
            if self.ns_list.has_key(pref):
                return self.ns_list.get(pref, pref) + ":" + rez.group(2)
            else:
                return uri
        else:
            return uri


    def termlink(self, string):
        """FOAF specific: function which replaces <code>foaf:*</code> with a 
        link to the term in the document."""
        return re.sub(r"<code>" + self.spec_pre + r":(\w+)</code>", r"""<code><a href="#term_\1">""" + self.spec_pre + r""":\1</a></code>""", string)    


    def get_rdfs(self, m, urinode):
        "Returns label and comment given an RDF.Node with a URI in it"
        comment = ''
        label = ''
        if (type(urinode)==str):
            urinode = RDF.Uri(urinode)
        l = m.find_statements(RDF.Statement(urinode, self.rdfs.label, None))
        if l.current():
            label = l.current().object.literal_value['string']
        c = m.find_statements(RDF.Statement(urinode, self.rdfs.comment, None))
        if c.current():
            comment = c.current().object.literal_value['string']
        return label, comment


    def get_status(self, m, urinode):
        "Returns the status text for a term."
        status = ''
        s = m.find_statements(RDF.Statement(urinode, self.vs.term_status, None))
        if s.current():
            return s.current().object.literal_value['string']


    def htmlDocInfo(self, t):
        """Opens a file based on the term name (t) and termdir directory (global).
           Reads in the file, and returns a linkified version of it."""
        doc = ""
        try:
            f = open("%s/%s.en" % (self.termdir, t), "r")
            doc = f.read()
            doc = self.termlink(doc)
        except:
            return "" 	# "<p>No detailed documentation for this term.</p>"
        return doc


    def owlVersionInfo(self, m):
        v = m.find_statements(RDF.Statement(None, self.owl.versionInfo, None))
        if v.current():
            return v.current().object.literal_value['string']
        else:
            return ""


    def titleInfo(self, m):
        predicates = [self.dc.title, self.dct.title]
        for p in predicates:
            v = m.find_statements(RDF.Statement(None, p, None))
            if v.current():
                return v.current().object.literal_value['string']
        try:
            v = m.find_statements(RDF.Statement(RDF.Uri(self.spec_url), self.rdfs.label, None))
            if v.current():
                return v.current().object.literal_value['string']
        except:
            pass
        try:
            v = m.find_statements(RDF.Statement(RDF.Uri(self.ns_url), self.rdfs.label, None))
            if v.current():
                return v.current().object.literal_value['string']
        except:
            pass
        return ""


    def descInfo(self, m):
        predicates = [self.dc.description, self.dct.description, self.rdfs.comment, self.dct.abstract]
        for p in predicates:
            try:
                v = m.find_statements(RDF.Statement(RDF.Uri(self.spec_url), p, None))
                if v.current():
                    return v.current().object.literal_value['string']
            except:
                pass
        for p in predicates:
            try:
                v = m.find_statements(RDF.Statement(RDF.Uri(self.ns_url), p, None))
                if v.current():
                    return v.current().object.literal_value['string']
            except:
                pass
        for p in predicates:
            v = m.find_statements(RDF.Statement(None, p, None))
            if v.current():
                return v.current().object.literal_value['string']
        return ""


    def authorInfo(self, m):
        authors = {'creator':[], 'contributor':[]}
        predicates = [self.dc.creator, self.dct.creator]
        for p in predicates:
            v = m.find_statements(RDF.Statement(None, p, None))
            #if v.current() and not v.current().object.literal_value['string'] in authors['creator']:
            #    authors['creator'].append(v.current().object.literal_value['string'])
            if v.current() and not v.current().object in authors['creator']:
                authors['creator'].append(str(v.current().object))
        predicates = [self.dc.contributor, self.dct.contributor]
        for p in predicates:
            v = m.find_statements(RDF.Statement(None, p, None))
            #if v.current() and not v.current().object.literal_value['string'] in authors['contributor']:
            #    authors['contributor'].append(v.current().object.literal_value['string'])
            if v.current() and not v.current().object in authors['contributor']:
                authors['contributor'].append(str(v.current().object))
        return authors


    def prefferredNs(self, m):
        prefns = {'uri':[], 'prefix':[]}
        v = m.find_statements(RDF.Statement(None, self.vann.preferredNamespaceUri, None))
        if v.current():
            try:
                prefns['uri'] = v.current().object.literal_value['string']
            except:
                prefns['uri'] = str(v.current().object.uri)
        v = m.find_statements(RDF.Statement(None, self.vann.preferredNamespacePrefix, None))
        if v.current():
            prefns['prefix'] = v.current().object.literal_value['string']
        return prefns


    def formatInfo(self, m):
        pass


    def rdfsPropertyInfo(self, term,m):
        """Generate HTML for properties: Domain, range, status."""
        #global classranges
        #global classdomains
        doc = ""
        range = ""
        domain = ""

        try:
            term.uri
        except:
            term = RDF.Node(RDF.Uri(term))

        #find subPropertyOf information
        o = m.find_statements( RDF.Statement(term, self.rdfs.subPropertyOf, None) )
        if o.current():
            rlist = ''
            for st in o:
                k = self.getTermLink(str(st.object.uri))
                rlist += "<dd>%s</dd>" % k
            doc += "<dt>sub-property-of:</dt> %s" % rlist

        #domain stuff
        domains = m.find_statements(RDF.Statement(term, self.rdfs.domain, None))
        domainsdoc = ""
        for d in domains:
            collection = m.find_statements(RDF.Statement(d.object, self.owl.unionOf, None))
            if collection.current():
                uris = self.parseCollection(m, collection)
                for uri in uris:
                    domainsdoc += "<dd>%s</dd>" % self.getTermLink(uri)
                    self.add(self.classdomains, uri, term.uri)
            else:
                if not d.object.is_blank():
                    domainsdoc += "<dd>%s</dd>" % self.getTermLink(str(d.object.uri))
        if (len(domainsdoc)>0):
            doc += "<dt>Domain:</dt> %s" % domainsdoc

        #range stuff
        ranges = m.find_statements(RDF.Statement(term, self.rdfs.range, None))
        rangesdoc = ""
        for r in ranges:
            collection = m.find_statements(RDF.Statement(r.object, self.owl.unionOf, None))
            if collection.current():
                uris = self.parseCollection(m, collection)
                for uri in uris:
                    rangesdoc += "<dd>%s</dd>" % self.getTermLink(uri)
                    self.add(self.classranges, uri, term.uri)
            else:
                if not r.object.is_blank():
                    rangesdoc += "<dd>%s</dd>" % self.getTermLink(str(r.object.uri))
        if (len(rangesdoc)>0):
            doc += "<dt>Range:</dt> %s" % rangesdoc

        return doc


    def parseCollection(self, model, collection):
        # #propertyA a rdf:Property ;
        #   rdfs:domain [
        #      a owl:Class ;
        #      owl:unionOf [
        #        rdf:parseType Collection ;
        #        #Foo a owl:Class ;
        #        #Bar a owl:Class
        #     ]
        #   ]
        # 
        # seeAlso "Collections in RDF"

        uris = []

        rdflist = model.find_statements(RDF.Statement(collection.current().object, None, None))
        while rdflist and rdflist.current() and not rdflist.current().object.is_blank():
            one = rdflist.current()
            if not one.object.is_blank():
                uris.append(str(one.object.uri))
            rdflist.next()
            one = rdflist.current()
            if one.predicate == self.rdf.rest:
                rdflist = model.find_statements(RDF.Statement(one.object, None, None))
        return uris


    def getTermLink(self, uri):
        uri = str(uri)
        nice_name = self.niceName(uri)
        if (uri.startswith(self.spec_url)):
            return '<a href="#term_%s" style="font-family: monospace;">%s</a>' % (uri.replace(self.spec_url, ""), nice_name)
        elif (uri.startswith(self.ns_url)):
            return '<a href="#term_%s" style="font-family: monospace;">%s</a>' % (uri.replace(self.ns_url, ""), nice_name)
        else:
            return '<a href="%s" style="font-family: monospace;">%s</a>' % (uri, nice_name)


    def rdfsClassInfo(self, term,m):
        """Generate rdfs-type information for Classes: ranges, and domains."""
        #global classranges
        #global classdomains
        doc = ""

        #patch to control incoming strings (FIXME, why??? drop it!)
        try:
            term.uri
        except:
            term = RDF.Node(RDF.Uri(term))

        # Find subClassOf information
        o = m.find_statements( RDF.Statement(term, self.rdfs.subClassOf, None) )
        if o.current():
            doc += "<dt>sub-class-of:</dt>"
            superclasses = []
            for st in o:
                if not st.object.is_blank():
                    try:
                        uri = str(st.object.uri)
                    except:
                        uri = str(st.object)
                    if (not uri in superclasses):
                        superclasses.append(uri)
            for superclass in superclasses:
                doc += "<dd>%s</dd>" % self.getTermLink(superclass)

        # Find out about properties which have self.rdfs:domain of t
        d = self.classdomains.get(str(term.uri), "")
        if d:
            dlist = ''
            for k in d:
                dlist += "<dd>%s</dd>" % self.getTermLink(k)
            doc += "<dt>in-domain-of:</dt>" + dlist

        # Find out about properties which have self.rdfs:range of t
        r = self.classranges.get(str(term.uri), "")
        if r:
            rlist = ''
            for k in r:
                rlist += "<dd>%s</dd>" % self.getTermLink(k)
            doc += "<dt>in-range-of:</dt>" + rlist

        return doc

    def rdfsInstanceInfo(self, term,m):
        """Generate rdfs-type information for instances"""
        #try:
        #    term.uri
        #except:
        #    term = RDF.Node(RDF.Uri(term))

        doc = ""
        t = m.find_statements( RDF.Statement(RDF.Node(RDF.Uri(term)), self.rdf.type, None) )
        if t.current():
            doc += "<dt>RDF Type:</dt>"
        while t.current():
            doc += "<dd>%s</dd>" % self.getTermLink(str(t.current().object.uri))
            t.next()

        return doc


    def owlInfo(self, term,m):
        """Returns an extra information that is defined about a term (an RDF.Node()) using OWL."""
        res = ''

        # FIXME: refactor this code
    
        # Inverse properties ( self.owl:inverseOf )
        o = m.find_statements( RDF.Statement(term, self.owl.inverseOf, None) )
        if o.current():
            res += "<dt>Inverse:</dt>"
            for st in o:
                res += "<dd>%s</dd>" % self.getTermLink(str(st.object.uri))
    
        # Datatype Property ( self.owl.DatatypeProperty )
        o = m.find_statements( RDF.Statement(term, self.rdf.type, self.owl.DatatypeProperty) )
        if o.current():
            res += "<dt>OWL Type:</dt><dd>DatatypeProperty</dd>\n"
	
        # Object Property ( self.owl.ObjectProperty )
        o = m.find_statements( RDF.Statement(term, self.rdf.type, self.owl.ObjectProperty) )
        if o.current():
            res += "<dt>OWL Type:</dt><dd>ObjectProperty</dd>\n"

        # Annotation Property ( self.owl.AnnotationProperty )
        o = m.find_statements( RDF.Statement(term, self.rdf.type, self.owl.AnnotationProperty) )
        if o.current():
            res += "<dt>OWL Type:</dt><dd>AnnotationProperty</dd>\n"

        # IFPs ( self.owl.InverseFunctionalProperty )
        o = m.find_statements( RDF.Statement(term, self.rdf.type, self.owl.InverseFunctionalProperty) )
        if o.current():
            res += "<dt>OWL Type:</dt><dd>InverseFunctionalProperty (uniquely identifying property)</dd>\n"

        # Symmertic Property ( self.owl.SymmetricProperty )
        o = m.find_statements( RDF.Statement(term, self.rdf.type, self.owl.SymmetricProperty) )
        if o.current():
            res += "<dt>OWL Type:</dt><dd>SymmetricProperty</dd>\n"
	
        return res


    def docTerms(self, category, list, m):
        """
        A wrapper class for listing all the terms in a specific class (either
        Properties, or Classes. Category is 'Property' or 'Class', list is a 
        list of term names (strings), return value is a chunk of HTML.
        """
        doc = ""
        nspre = self.spec_pre
        for t in list:
            if (t.startswith(self.spec_url)) and (len(t[len(self.spec_url):].split("/"))<2):
                term = t
                #t = t.split(self.spec_url[-1])[1]
                t = t.replace(self.spec_url, "")
                curie = "%s:%s" % (nspre, t)
                term_uri =  RDF.Uri("%s%s"%(self.spec_url, t))
            elif (t.startswith(self.ns_url)) and (len(t[len(self.ns_url):].split("/"))<2):
                #t = t.split(self.ns_url[-1])[1]
                t = t.replace(self.ns_url, "")
                term = RDF.Uri("%s%s"%(self.ns_url, t))
                curie = "%s:%s" % (nspre, t)
                term_uri = term
            else:
                if t.startswith("http://"):
                    term = t
                    curie = self.getShortName(t)
                    t = self.getAnchor(t)
                else:
                    term = self.spec_ns[t]
                    curie = "%s:%s" % (nspre, t)
                try:
                    term_uri = term.uri
                except:
                    term_uri = term
        
            doc += """<div class="specterm" id="term_%s">\n<h3>%s: %s</h3>\n""" % (t, category, curie)
            doc += """<p style="font-family:monospace; font-size:0.em;">URI: <a href="%s">%s</a></p>""" % (term_uri, term_uri)
            label, comment = self.get_rdfs(m, term)    
            status = self.get_status(m, term)
            doc += "<p><em>%s</em> - %s </p>" % (label, comment)
            terminfo = ""
            if category=='Property':
                terminfo += self.owlInfo(term,m)
                terminfo += self.rdfsPropertyInfo(term,m)
            if category=='Class':
                terminfo += self.rdfsClassInfo(term,m)
            if category=='Instance':
                terminfo += self.rdfsInstanceInfo(term,m)
            if (len(terminfo)>0): #to prevent empty list (bug #882)
                doc += "\n<dl>%s</dl>\n" % terminfo
            doc += self.htmlDocInfo(t)
            doc += "<p style=\"float: right; font-size: small;\">[<a href=\"#sec-glance\">back to top</a>]</p>\n\n"
            doc += "\n\n</div>\n\n"
    
        return doc


    def getShortName(self, uri):
        if ("#" in uri):
            return uri.split("#")[-1]
        else:
            return uri.split("/")[-1]


    def getAnchor(self, uri):
        if (uri.startswith(self.spec_url)):
            return uri[len(self.spec_url):].replace("/","_")
        elif (uri.startswith(self.ns_url)):
            return uri[len(self.ns_url):].replace("/","_")
        else:
            return self.getShortName(uri)


    def buildazlist(self, classlist, proplist, instalist=None):
        """
        Builds the A-Z list of terms. Args are a list of classes (strings) and 
        a list of props (strings)
        """
        azlist = '<div style="padding: 1em; border: dotted; background-color: #ddd;">'

        if (len(classlist)>0):
            azlist += "<p>Classes: "
            classlist.sort()
            for c in classlist:
                if c.startswith(self.spec_url):
                    ct = c.replace(self.spec_url, "")
                elif c.startswith(self.ns_url):
                    ct = c.replace(self.ns_url, "")
                azlist = """%s <a href="#term_%s">%s</a>, """ % (azlist, ct, ct)
            azlist = """%s\n</p>""" % azlist

        if (len(proplist)>0):
            azlist += "<p>Properties: "
            proplist.sort()
            for p in proplist:
                if p.startswith(self.spec_url):
                    pt = p.replace(self.spec_url, "")
                elif p.startswith(self.ns_url):
                    pt = p.replace(self.ns_url, "")
                azlist = """%s <a href="#term_%s">%s</a>, """ % (azlist, pt, pt)
            azlist = """%s\n</p>""" % azlist

        if (instalist!=None and len(instalist)>0):
            azlist += "<p>Instances: "
            for i in instalist:
                p = self.getShortName(i)
                anchor = self.getAnchor(i)
                azlist = """%s <a href="#term_%s">%s</a>, """ % (azlist, anchor, p)
            azlist = """%s\n</p>""" % azlist

        azlist = """%s\n</div>""" % azlist
        return azlist


    def build_simple_list(self, classlist, proplist, instalist=None):
        """
        Builds a simple <ul> A-Z list of terms. Args are a list of classes (strings) and 
        a list of props (strings)
        """

        azlist = """<div style="padding: 5px; border: dotted; background-color: #ddd;">"""
        azlist = """%s\n<p>Classes:""" % azlist
        azlist += """\n<ul>"""

        classlist.sort()
        for c in classlist:
            azlist += """\n  <li><a href="#term_%s">%s</a></li>""" % (c.replace(" ", ""), c)
        azlist = """%s\n</ul></p>""" % azlist

        azlist = """%s\n<p>Properties:""" % azlist
        azlist += """\n<ul>"""
        proplist.sort()
        for p in proplist:
            azlist += """\n  <li><a href="#term_%s">%s</a></li>""" % (p.replace(" ", ""), p)
        azlist = """%s\n</ul></p>""" % azlist

        #FIXME: instances

        azlist = """%s\n</div>""" % azlist
        return azlist


    def add(self, where, key, value):
        if not where.has_key(key):
            where[key] = []
        if not value in where[key]:
            where[key].append(value)


    def specInformation(self, m, ns):
        """
        Read through the spec (provided as a Redland model) and return classlist
        and proplist. Global variables classranges and classdomains are also filled
        as appropriate.
        """
        #global classranges
        #global classdomains

        # Find the class information: Ranges, domains, and list of all names.
        classtypes = [self.rdfs.Class, self.owl.Class]
        classlist = []
        for onetype in classtypes:
            for classStatement in  m.find_statements(RDF.Statement(None, self.rdf.type, onetype)):
                for range in m.find_statements(RDF.Statement(None, self.rdfs.range, classStatement.subject)):
                    if not m.contains_statement( RDF.Statement( range.subject, self.rdf.type, self.owl.DeprecatedProperty )):
                        if not classStatement.subject.is_blank():
                            self.add(self.classranges, str(classStatement.subject.uri), str(range.subject.uri))
                for domain in m.find_statements(RDF.Statement(None, self.rdfs.domain, classStatement.subject)):
                    if not m.contains_statement( RDF.Statement( domain.subject, self.rdf.type, self.owl.DeprecatedProperty )):
                        if not classStatement.subject.is_blank():
                            self.add(self.classdomains, str(classStatement.subject.uri), str(domain.subject.uri))
                if not classStatement.subject.is_blank():
                    uri = str(classStatement.subject.uri)
                    if (not uri in classlist) and (uri.startswith(self.spec_url) or uri.startswith(self.ns_url)):
                        classlist.append(uri)

        # Create a list of properties in the schema.
        proptypes = [self.rdf.Property, self.owl.ObjectProperty, self.owl.DatatypeProperty, self.owl.AnnotationProperty]
        proplist = []
        for onetype in proptypes: 
            for propertyStatement in m.find_statements(RDF.Statement(None, self.rdf.type, onetype)):
                uri = str(propertyStatement.subject.uri)
                if (not uri in proplist) and (uri.startswith(ns) or uri.startswith(self.ns_url)):
                    proplist.append(uri)

        return classlist, proplist

    def getInstances(self, model, classes, properties):
        """
        Extract all resources instanced in the ontology
        (aka "everything that is not a class or a property")
        """
        instances = []
        for one in classes:
            for i in model.find_statements(RDF.Statement(None, self.rdf.type, self.spec_ns[one])):
                uri = str(i.subject.uri)
                if not uri in instances:
                    instances.append(uri)
        if not instances:
            for one in classes:
                for i in model.find_statements(RDF.Statement(None, self.rdf.type, RDF.NS(self.ns_url)[one])):
                    uri = str(i.subject.uri)
                    if not uri in instances:
                        instances.append(uri)
        count = len(instances)
        for i in model.find_statements(RDF.Statement(None, self.rdfs.isDefinedBy, RDF.Uri(self.spec_url))):
            uri = str(i.subject.uri)
            #if (uri.startswith(self.spec_url)):
            #    uri = uri[len(self.spec_url):]
            if ((not uri in instances) and (not uri in classes)):
                instances.append(uri)
        if len(instances) == count:
            for i in model.find_statements(RDF.Statement(None, self.rdfs.isDefinedBy, RDF.Uri(self.ns_url))):
                uri = str(i.subject.uri)
                #if uri.startswith(self.ns_url):
                #    uri = uri[len(self.ns_url):]
                if ((not uri in instances) and (not uri in classes)):
                    instances.append(uri)
        return instances
   
 
    def specgen(self, mode="spec"):
        """The meat and potatoes: Everything starts here."""

        m = RDF.Model()
        p = RDF.Parser()
        try:
            p.parse_into_model(m, self.specloc)
        except IOError, e:
            raise Usage("Error reading from ontology: %s"%str(e))
        except RDF.RedlandError, e:
            raise Usage("Error parsing the ontology: %s"%str(e))

        self.spec_url = self.getOntologyNS(m)
        self.spec_ns = RDF.NS(self.spec_url)
        self.ns_list[self.spec_url] = self.spec_pre
        self.ns_list[self.ns_url] = self.spec_pre

        classlist, proplist = self.specInformation(m, self.spec_url)
        classlist = sorted(classlist)
        proplist = sorted(proplist)

        instalist = None
        if self.instances:
            instalist = self.getInstances(m, classlist, proplist)
            instalist.sort(lambda x, y: cmp(self.getShortName(x).lower(), self.getShortName(y).lower()))
        if mode == "spec":
            # Build HTML list of terms.
            azlist = self.buildazlist(classlist, proplist, instalist)
        elif mode == "list":
            # Build simple <ul> list of terms.
            azlist = self.build_simple_list(classlist, proplist, instalist)

        # Generate Term HTML
        termlist = self.docTerms('Property', proplist, m)
        termlist = self.docTerms('Class', classlist, m) + termlist
        if self.instances:
            termlist += self.docTerms('Instance', instalist, m)

        if not (classlist or proplist) and termlist:
            raise Usage("Could not generate list of terms (classes, properties) or term information for the vocabulary")

        #Get vocabulary deatils
        title = self.titleInfo(m)
        try:
            title = unicode(title)
        except UnicodeDecodeError, e:
            title = unicode(title.decode('utf-8'))

        desc = self.descInfo(m)
        try:
            desc = unicode(desc)
        except UnicodeDecodeError, e:
            desc = unicode(desc.decode('utf-8'))

        authors = self.authorInfo(m)

        creator = ', '.join(authors['creator'])
        try:
            creator = unicode(creator)
        except UnicodeDecodeError, e:
            creator = unicode(creator.decode('utf-8'))

        contributor = ', '.join(authors['contributor'])
        try:
            contributor = unicode(contributor)
        except UnicodeDecodeError, e:
            contributor = unicode(contributor.decode('utf-8'))

        prefns = self.prefferredNs(m)
        try:
            prefns = unicode(prefns)
        except UnicodeDecodeError, e:
            prefns = unicode(prefns.decode('utf-8'))

        #formats = self.formatInfo(m)

        try:
            self.template = unicode(self.template)
        except UnicodeDecodeError, e:
            self.template = unicode(self.template.decode('utf-8'))
    
        try:
            self.template = self.template % {'t':title, 'a':creator, 'c':contributor, 'd':desc, 's':unicode(azlist), 'i':unicode(termlist)}
            self.template += "<!-- HTML generated by vocab.ox.ac.uk at %s -->" % time.strftime('%X %x %Z')
        except TypeError, e:
            raise Usage("Error filling the template!")
        return True


    def save(self):
        try:
            f = codecs.open(self.dest, "w", "utf-8")
            f.write(self.template)
            #f.write(self.template.encode("utf-8"))
            f.close()
        except Exception, e:
            raise Usage("Error writting in file %s: %s" % (self.dest, e))
        return

    def create_file(self):
        self.specgen()
        self.save()
        return

