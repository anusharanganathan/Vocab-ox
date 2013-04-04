import os
import codecs
from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect
from paste.fileapp import FileApp
from webui.lib.base import BaseController, render
from webui.lib.conneg import MimeType as MT, parse as conneg_parse
from webui.lib.rdf_helper import get_vocab_files, get_vocab_description, get_vocab_editorial_note, get_vocab_properties, get_ref_vocabs
from webui.lib.rdf_helper import get_mediator_details, get_mediator_vocabs, get_vocab_mediator

class VocabsController(BaseController):
    """Generates the list of vocabs in the vocab page.
    Displays the detailed view for each vocab.
    """
    def index(self):
        """Generates the list of vocabs in the browse page."""
        vocabs =  os.listdir(ag.vocabulariesdir)
        c.ox_vocab_list = {}
        c.ref_vocab_list = {}
        mediators_dir_name = ag.mediatorsdir.strip('/').split('/')[-1]
        reference_vocabs = get_ref_vocabs().keys()
        for v in vocabs:
            vocab_dict = {}
            if v.startswith('.') or v == mediators_dir_name or v == os.path.split(ag.vocabulariesref)[1]:
                continue
            #Get the list of files
            files = get_vocab_files(v)
            if not files:
                continue
            description = {}
            for f, vals in files.iteritems():
                if vals['format'] == 'application/rdf+xml':
                    description = get_vocab_description(vals['path'], v)
            vocab_dict = description
            vocab_dict['files'] = files
            vocab_dict['mediators'] = get_vocab_mediator(v)
            properties = get_vocab_properties(v)
            vocab_dict['uri'] = properties['uri']
            vocab_dict['pref_uri'] = properties['preferredNamespaceUri']
            vocab_dict['pref_prefix'] = properties['preferredNamespacePrefix']
            if str(properties['uri']) in reference_vocabs:
                c.ref_vocab_list[v] = vocab_dict
            else:
                c.ox_vocab_list[v] = vocab_dict
        return render('/browse.html')

    def render_vocab(self, vocab):
        """Render the page for each vocab"""
        c.vocab = vocab
        files = get_vocab_files(vocab)
        if not files:
            session['browse_flash'] = "Could not find any file for %s"%vocab
            session.save()
            return redirect(url(controller='vocabs', action='index'), code=303)
        formats = []
        for f, v in files.iteritems():
            if not v['format'].lower() in formats:
                formats.append(v['format'].lower())
        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]
        mimetype = accept_list.pop()
        while(mimetype):
            if str(mimetype).lower() in formats:
                if str(mimetype).lower() in ['text/html', "text/xhtml"]:
                    for f, v in files.iteritems():
                        if v['format'].lower() == 'text/html':
                            c.format = v['format']
                            c.vocabfile = v['path'].replace('/opt', '')
                            return render('/vocab.html')
                elif str(mimetype).lower() in ['application/rdf+xml', "text/xml", "text/rdf+n3", "application/x-turtle", \
                "text/rdf+ntriples", "text/rdf+nt", "text/plain"]:
                    for f, v in files.iteritems():
                        if v['format'].lower() in ['application/rdf+xml', 'text/xml', "text/rdf+n3", "application/x-turtle", \
                        "text/rdf+ntriples", "text/rdf+nt", "text/plain"]:
                            response.content_type = '%s; charset="UTF-8"'%str(mimetype)
                            response.status_int = 200
                            response.status = "200 OK"
                            f = codecs.open(v['path'], 'r', 'utf-8')
                            return_str = f.read()
                            f.close()
                            return return_str
                else:
                    response.content_type = '%s; charset="UTF-8"'%str(mimetype)
                    response.status_int = 200
                    response.status = "200 OK"
                    for f, v in files.iteritems():
                        if v['format'].lower() == str(mimetype).lower() and os.path.isfile(v['path']):
                            fileserve_app = FileApp(v['path'])
                            return fileserve_app(request.environ, self.start_response)
            try:
                mimetype = accept_list.pop()
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return one of the formats available - 1. text/html, 2. other
        if 'text/html' in formats:
            for f, v in files.iteritems():
                if v['format'].lower() == 'text/html':
                    c.format = v['format']
                    c.vocabfile = v['path'].replace('/opt', '')
                    return render('/vocab.html')
        elif 'application/rdf+xml' in formats or "text/xml" in formats or "text/rdf+n3" in formats or "text/plain" in formats or \
             "application/x-turtle" in formats or "text/rdf+ntriples" in formats or "text/rdf+nt" in formats:
            for f, v in files.iteritems():
                if v['format'].lower() in ['application/rdf+xml', "text/xml", "text/rdf+n3", "application/x-turtle", \
                                        "text/rdf+ntriples", "text/rdf+nt", "text/plain"]:
                    response.content_type = '%s; charset="UTF-8"'%str(v['format'])
                    response.status_int = 200
                    response.status = "200 OK"
                    f = codecs.open(v['path'], 'r', 'utf-8')
                    return_str = f.read()
                    f.close()
                    return return_str
        else:
            for format in formats:
                response.content_type = '%s; charset="UTF-8"'%str(format)
                response.status_int = 200
                response.status = "200 OK"
                for f, v in files.iteritems():
                    if v['format'].lower() == format and os.path.isfile(v['path']):
                        fileserve_app = FileApp(v['path'])
                        return fileserve_app(request.environ, self.start_response)
        session['browse_flash'] = "Could not find any file for %s"%vocab
        session.save()
        return redirect(url(controller='vocabs', action='index'), code=303)

    def render_vocab_file(self, vocab, filename):
        """Render the file for vocab"""
        files = get_vocab_files(vocab)
        if not files:
            abort(404)
        for f, v in files.iteritems():
            if v['name'] == filename or f == 'http://vocab.ox.ac.uk/%s/%s'%(vocab, filename):
                if v['format'].lower() == 'text/html':
                    c.format = v['format']
                    c.vocabfile = v['path'].replace('/opt', '')
                    return render('/vocab.html')
                elif v['format'].lower() in ['application/rdf+xml', 'text/xml', "text/rdf+n3", "application/x-turtle", \
                                             "text/rdf+ntriples", "text/rdf+nt", "text/plain"]:
                    response.content_type = '%s; charset="UTF-8"'%str(v['format'])
                    response.status_int = 200
                    response.status = "200 OK"
                    f = codecs.open(v['path'], 'r', 'utf-8')
                    return_str = f.read()
                    f.close()
                    return return_str
                else:
                    response.content_type = '%s; charset="utf-8"'%str(v['format'])
                    response.status_int = 200
                    response.status = "200 OK"
                    if os.path.isfile(v['path']):
                        fileserve_app = FileApp(v['path'])
                        return fileserve_app(request.environ, self.start_response)
                    else:
                        session['browse_flash'] = "Could not find the file %s for %s"%(filename, vocab)
                        session.save()
                        return redirect(url(controller='vocabs', action='index'), code=303)
        session['browse_flash'] = "Could not find the file %s for %s"%(filename, vocab)
        session.save()
        return redirect(url(controller='vocabs', action='index'), code=303)

    def render_external_vocab(self, vocab_name):
        """Render the page for each vocab"""
        #redirect(url(controller='vocabs', action='index'), code=303)
        return render('/vocab.html')

    def publish(self):
        identity = request.environ.get("repoze.who.identity")
        if identity:
            #Get list of vocabularies created by userid
            c.userid = identity['repoze.who.userid']
            c.user_det = get_mediator_details(c.userid)
            vocabs = get_mediator_vocabs(c.userid)
            #Get status of vocab - is rdf, ready to convert to html, new rdf check, convert to html, html check
            c.vocab_list = {}

            for k, v in vocabs.iteritems():
                files = get_vocab_files(k)
                description = {}
                for f, vals in files.iteritems():
                    if vals['format'] == 'application/rdf+xml':
                        description = get_vocab_description(vals['path'], k)
                msgs = get_vocab_editorial_note(k)
                c.vocab_list[k] = description
                c.vocab_list[k]['files'] = files
                c.vocab_list[k]['uri'] = v[0]
                c.vocab_list[k]['svn'] = v[1]
                c.vocab_list[k]['note'] = msgs
            return render('/publish.html')
        else:
            session['login_flash'] = "Please login to view vocabularies published and managed by you and to upload new vocabularies"
            session.save()
            destination = "/login?came_from=publish"
            return redirect(destination, code=303)

    def owner(self, owner_uuid):
        c.user_det = get_mediator_details(owner_uuid)
        c.vocab_list = {}
        if 'userid' in c.user_det and c.user_det['userid']:
            c.userid = c.user_det['userid']
            vocabs = get_mediator_vocabs(c.userid)
            #Get status of vocab - is rdf, ready to convert to html, new rdf check, convert to html, html check
            for k, v in vocabs.iteritems():
                files = get_vocab_files(k)
                description = {}
                for f, vals in files.iteritems():
                    if vals['format'] == 'application/rdf+xml':
                        description = get_vocab_description(vals['path'], k)
                c.vocab_list[k] = description
                c.vocab_list[k]['files'] = files
        return render ('/owner.html')
