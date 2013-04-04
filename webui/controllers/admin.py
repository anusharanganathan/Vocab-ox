from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from webui.lib.base import BaseController, render
from pylons.controllers.util import redirect
from webui.lib.rdf_helper import get_mediator_vocabs, get_vocab_files, get_vocab_editorial_note, get_vocab_base, get_vocab_properties, check_rdf, check_n3
from webui.lib.rdf_helper import create_vocab_statusfile, add_status, del_status, update_vocab_uri_in_statusfile, add_file_to_vocab_status
from webui.lib.svn_helper import svn_add, svn_remove, svn_commit
from webui.lib.specgen import SpecGen
from webui.config.rdfconfig import vocab_editorial_descriptions

import os, shutil, uuid
from paste.fileapp import FileApp
from urlparse import urljoin
from urllib import urlretrieve

class AdminController(BaseController):
    """Create, rename and generateb the html view for a vocab."""

    def create(self):
        identity = request.environ.get("repoze.who.identity")
        if not identity:
            session['login_flash'] = "Please login to add new vocabularies"
            session.save()
            destination = "/login?came_from=/vocabs/create"
            return redirect(destination, code=303)

        userid = identity['repoze.who.userid']
        mediatorfile = os.path.join(ag.mediatorsdir, '%s.rdf'%userid)
        params = request.POST
        #if not (params.has_key('retrieveurl') and not (params.has_key('vocabfile'):
        #    session['welcome_flash'] = """Please upload a file for the vocabulary"""
        #    session.save()
        #    return redirect(url(controller='vocabs', action='publish'), code=303)

        #if not params.has_key('prefix') or not params['prefix']:
        #    #Create a random prefix
        #    using_uuid = True
        #    c.vocabprefix = uuid.uuid4()
        #else:
        #    c.vocabprefix = params.get('prefix')
        #    using_uuid = False

        #vocabdir = "%s/%s"%(ag.vocabulariesdir, c.vocabprefix)

        #Check if the prefix exists (only needed if accepting prefix in create form)
        #if os.path.isdir(vocabdir):
        #    session['welcome_flash'] = """A vocabulary with this prefix exists.
        #        See <a href="http://vocab.ox.ac.uk/%s">%s</a>"""%(c.vocabprefix, c.vocabprefix)
        #    session.save()
        #    return redirect(url(controller='vocabs', action='publish'), code=303)

        #Create a random prefix
        using_uuid = True
        c.vocabprefix = uuid.uuid4()
        vocabdir = "%s/%s"%(ag.vocabulariesdir, c.vocabprefix)
        os.mkdir(vocabdir)

        vocabfile = None
        refvocab = False
        if params.has_key('vocabfile'):
            #Copy the uploaded file to vocabdir
            try:
                filename = params['vocabfile'].filename
            except:
                session['welcome_flash'] = """Please upload a file for the vocabulary"""
                session.save()
                return redirect(url(controller='vocabs', action='publish'), code=303)
            upload = params.get('vocabfile')
            vocabfile = os.path.join(vocabdir, filename.lstrip(os.sep))
            vocabfile_obj = open(vocabfile, 'w')
            shutil.copyfileobj(upload.file, vocabfile_obj)
            upload.file.close()
            vocabfile_obj.close()
        elif params.has_key('retrieveurl') and params['retrieveurl']:
            filename = params['retrieveurl'].strip().rstrip('/')
            filename = os.path.split(filename)[1]
            if '#' in filename:
                filename = filename.split('#')[0]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename:
                filename = 'vocab'
            vocabfile = os.path.join(vocabdir, filename.lstrip(os.sep))
            #Retrieve the file using urllib
            #Use HTTPLib rather than urllib and pass accept headers
            try:
                urlretrieve(params['retrieveurl'], vocabfile)
            except Exception, e:
                shutil.rmtree(vocabdir)     
                session['welcome_flash'] = """Error retrieving the file %s: %s"""%(params['retrieveurl'], e)
                session.save()
                return redirect(url(controller='vocabs', action='publish'), code=303)
            #urlretrieve(params['retrieveurl'], vocabfile)
            refvocab = params['retrieveurl']
        else:
            session['welcome_flash'] = """Please upload a file for the vocabulary"""
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        #Check file exists
        if not os.path.isfile(vocabfile):
            shutil.rmtree(vocabdir)     
            session['welcome_flash'] = """Error uploading the file %s"""%filename
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)
        message = []
        #======================================================
        #Get the prefix and namespace uri from the vocab
        identifier = None
        ns_prefix = None
        c.base_URI = None
        if check_rdf(vocabfile) or check_n3(vocabfile):
            (identifier, c.base_URI, ns_prefix) = get_vocab_base(vocabfile)
        if ns_prefix:
            if refvocab and filename == 'vocab':
                filename = ns_prefix
                newvocabfile = os.path.join(vocabdir, filename.lstrip(os.sep))
                os.rename(vocabfile, newvocabfile)
                vocabfile = newvocabfile
            newvocabdir = "%s/%s"%(ag.vocabulariesdir, ns_prefix)
            if os.path.isdir(newvocabdir):
                message = []
                message.append("""Vocabulary added to <a href="http://vocab.ox.ac.uk/%s">%s</a>"""%c.vocabprefix)
                message.append("""Extracted the namespace prefix <b>%s</b> from the \
vocabulary file. A vocabulary already exists with this obtained prefix. \
See <a href="http://vocab.ox.ac.uk/%s">%s</a>"""%(ns_prefix, ns_prefix, ns_prefix))
            else:
                using_uuid = False
                os.rename(vocabdir, newvocabdir)
                vocabdir = newvocabdir
                vocabfile = os.path.join(vocabdir, filename.lstrip(os.sep))
                c.vocabprefix = ns_prefix
                message = []
        else:
            message = []

        #Create the rdf status file for the vocab and add the vocab in the mediators rdf file
        create_vocab_statusfile(userid, c.vocabprefix, vocabfile, c.base_URI, using_uuid=using_uuid, refvocab=refvocab)

        #Commit svn changes
        (status1, msg1) = svn_add(vocabdir, "New vocabulary added by user %s"%userid)
        if not status1:
            message.append("""Error committing to SVN: %s"""%msg1)

        (status2, msg2) = svn_commit([vocabdir, mediatorfile], "New vocabulary %s added by user %s"%(c.vocabprefix, userid))
        if not status2:
            message.append("""Error committing to SVN: %s"""%msg2)
        c.message = "<br />".join(message)
        return render('rename.html')

    def rename(self, prefix):
        identity = request.environ.get("repoze.who.identity")
        if not identity:
            session['login_flash'] = "Please login to modify vocabularies published and managed by you"
            session.save()
            destination = "/login?came_from=rename/%s"%prefix
            return redirect(destination, code=303)
        
        #Check if userid has permissions for this vocab
        userid = identity['repoze.who.userid']
        mediatorfile = os.path.join(ag.mediatorsdir, '%s.rdf'%userid)
        vocablist = get_mediator_vocabs(userid)
        if vocablist and not prefix in vocablist.keys():
            session['welcome_flash'] = "You are not authorized to make any changes to %s"%prefix
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        vocabs =  os.listdir(ag.vocabulariesdir)
        mediators_dir_name = ag.mediatorsdir.strip('/').split('/')[-1]
        if not prefix in vocabs:
            session['welcome_flash'] = "Vocab %s does not exist"%prefix
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)
        
        params = request.params
        c.vocabprefix = None
        c.base_URI = None
        if params.has_key('ns_prefix') and params['ns_prefix']:
            c.vocabprefix = params['ns_prefix']
        if params.has_key('base_URI') and params['base_URI']:
            c.base_URI = params['base_URI']
            if c.base_URI:
                c.base_URI = c.base_URI.strip()
                if (c.base_URI[-1]!="/" and c.base_URI[-1]!="#"):
                    c.base_URI += "#"
        if not c.vocabprefix or not c.base_URI:    
            c.message = 'Enter the preferred namespace prefix and namespace URI for the vocab'
            properties = get_vocab_properties(prefix)
            c.base_URI = properties['preferredNamespaceUri']
            c.vocabprefix = prefix
            return render('rename.html')
        vocabdir = "%s/%s"%(ag.vocabulariesdir, prefix)
        newvocabdir = "%s/%s"%(ag.vocabulariesdir, c.vocabprefix)
        if c.vocabprefix != prefix:
            if os.path.isdir(newvocabdir):
                message = []
                message.append("""A vocabulary already exists with the namespace prefix <a href="http://vocab.ox.ac.uk/%s">%s</a>"""%(c.vocabprefix, c.vocabprefix))
                message.append("Please select another preferred namespace prefix")
                c.message = "<br />".join(message)
                properties = get_vocab_properties(prefix)
                c.base_URI = properties['preferredNamespaceUri']
                c.vocabprefix = prefix
                return render('rename.html')
        
            os.rename(vocabdir, newvocabdir)

            #Change the rdf status file for the vocab and the mediator file
            update_vocab_uri_in_statusfile(userid, prefix, c.vocabprefix, vocabdir, newvocabdir)
        vocab_uri = "http://vocab.ox.ac.uk/%s"%c.vocabprefix
        del_status(c.vocabprefix, vocab_uri, 'skos:editorialNote', vocab_editorial_descriptions[0])
        del_status(c.vocabprefix, vocab_uri, 'vann:preferredNamespaceUri', None)
        del_status(c.vocabprefix, vocab_uri, 'vann:preferredNamespacePrefix', None)
        add_status(c.vocabprefix, vocab_uri, 'vann:preferredNamespaceUri', c.base_URI)
        add_status(c.vocabprefix, vocab_uri, 'vann:preferredNamespacePrefix', c.vocabprefix)
 
        message = ["Successfully added the properties and changed the preferred namespace prefix from %s to %s"%(prefix, c.vocabprefix)] 

        #Commit svn changes
        (status1, msg1) = svn_add(newvocabdir, "Renamed vocabulary. Added %s"%c.vocabprefix)
        if not status1:
            message.append("""Error committing to SVN: %s"""%msg1)

        #(status2, msg2) = svn_remove(vocabdir, "Removed vocabulary. removed %s"%prefix)
        #if not status2:
        #    message.append("""Error committing to SVN: %s"""%msg2)
       
        (status2, msg2) = svn_commit([newvocabdir, mediatorfile], "New vocabulary %s added by user %s"%(c.vocabprefix, userid))
        if not status2:
            message.append("""Error committing to SVN: %s"""%msg2)

        session['welcome_flash'] = "<br />".join(message)
        session.save()
        return redirect(url(controller='vocabs', action='publish'), code=303)

    def generate(self, prefix):
        came_from = "/publish"
        identity = request.environ.get("repoze.who.identity")
        if not identity:
            session['login_flash'] = "Please login to convert vocabularies published and managed by you"
            session.save()
            destination = "/login?came_from=%s"%came_from
            return redirect(destination, code=303)
            
        #Check if userid has permissions for this vocab
        userid = identity['repoze.who.userid']
        vocablist = get_mediator_vocabs(userid)
        if vocablist and not prefix in vocablist.keys():
            session['welcome_flash'] = "You are not authorized to make any changes to %s"%prefix
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        params = request.params
        if not 'file' in params or not params['file']:
            session['welcome_flash'] = """No file was selected to modify"""
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        c.vocabprefix = prefix
        c.filename = params.get('file')

        #Get vocab properties
        vocab_properties = get_vocab_properties(c.vocabprefix)

        #Get vocab rdf file properties
        files = get_vocab_files(c.vocabprefix)
        rdf_vocab_properties = None
        for f, val in files.iteritems():
            if val['name'] == c.filename and val['format'] == 'application/rdf+xml':
                rdf_vocab_properties = val
                rdf_vocab_properties['uri'] = f    
                break
        #Check file exists
        if not rdf_vocab_properties or not os.path.isfile(rdf_vocab_properties['path']):
            session['welcome_flash'] = """Could not locate the file %s for %s"""%(c.filename, c.vocabprefix)
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        #Get editorial notes
        notes = get_vocab_editorial_note(c.vocabprefix)
        vocab_msgs = []
        for (msg, recepient) in notes:
            if (not recepient) or recepient == c.filename:
                vocab_msgs.append(msg)
                #vocab_file_msgs.append(msg)

        if vocab_editorial_descriptions[5] in vocab_msgs:
            #TODO: Get the URI for the html file
            session['welcome_flash'] = "HTML file exists for %s"%c.vocabprefix
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        if not vocab_editorial_descriptions[3] in vocab_msgs:
            if vocab_editorial_descriptions[1] in vocab_msgs:
                session['welcome_flash'] = "%s in %s"%(vocab_editorial_descriptions[1], c.vocabprefix)
                session.save()
                return redirect(url(controller='vocabs', action='publish'), code=303)
            if vocab_editorial_descriptions[2] in vocab_msgs:
                session['welcome_flash'] = "%s in %s"%(vocab_editorial_descriptions[2], c.filename)
                session.save()
                return redirect(url(controller='vocabs', action='publish'), code=303)
            if vocab_editorial_descriptions[4] in vocab_msgs:
                session['welcome_flash'] = "%s in %s"%(vocab_editorial_descriptions[4], c.filename)
                session.save()
                return redirect(url(controller='vocabs', action='publish'), code=303)

        del_status(c.vocabprefix, rdf_vocab_properties['uri'], 'skos:editorialNote', vocab_editorial_descriptions[3])

        #Check if file is rdf
        if not check_rdf(rdf_vocab_properties['path']):
            add_status(c.vocabprefix, rdf_vocab_properties['uri'], 'skos:editorialNote', vocab_editorial_descriptions[2])
            session['welcome_flash'] = "Could not parse %s as an rdf file"%c.filename
            session.save()
            return redirect(url(controller='vocabs', action='publish'), code=303)

        html_vocab_properties = {}
        html_vocab_properties['format'] = 'text/html'
        html_vocab_properties['name'] = "%s.html"%os.path.splitext(rdf_vocab_properties['name'])[0]
        (head, tail) = os.path.split(rdf_vocab_properties['path'])
        html_vocab_properties['path'] = os.path.join(head, html_vocab_properties['name'])
        uri_parts = rdf_vocab_properties['uri'].split('/')
        for i in range(len(uri_parts)-1, -1, -1):
            if uri_parts[i] == rdf_vocab_properties['name']:
                uri_parts[i] = html_vocab_properties['name']
                break
        html_vocab_properties['uri'] = '/'.join(uri_parts)

        loc = rdf_vocab_properties['path']
        dest = html_vocab_properties['path']
        #try:
        #    s = SpecGen(loc, c.vocabprefix, vocab_properties['preferredNamespaceUri'], ag.conversion_template, dest)
        #    s.create_file()
        #except Exception, e:
        #    add_status(c.vocabprefix, rdf_vocab_properties['uri'], 'skos:editorialNote', vocab_editorial_descriptions[4])
        #    add_status(c.vocabprefix, rdf_vocab_properties['uri'], 'skos:note', str(e))
        #    session['welcome_flash'] = """%s <br>%s"""%(vocab_editorial_descriptions[4], str(e))
        #    session.save()
        #    return redirect(url(controller='vocabs', action='publish'), code=303)        
        s = SpecGen(loc, c.vocabprefix, vocab_properties['preferredNamespaceUri'], ag.conversion_template, dest)
        s.create_file()

        add_file_to_vocab_status(c.vocabprefix, html_vocab_properties)
        add_status(c.vocabprefix, rdf_vocab_properties['uri'], 'skos:editorialNote', vocab_editorial_descriptions[5])
        add_status(c.vocabprefix, html_vocab_properties['uri'], 'dcterms:isFormatOf', rdf_vocab_properties['uri'])

        message = ["""Generated the html file %s"""%html_vocab_properties['uri']]   
        #Commit svn changes
        (status1, msg1) = svn_add(dest, "Created HTML file")
        if not status1:
            message.append("""Error committing to SVN: %s"""%msg1)
       
        (status2, msg2) = svn_commit([dest], "Generated HTML file. Committing changes")
        if not status2:
            message.append("""Error committing to SVN: %s"""%msg2)
        
        session['welcome_flash'] = '<br>'.join(message)
        session.save()
        return redirect(url(controller='vocabs', action='publish'), code=303)


