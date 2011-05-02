from pylons import url
from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from webui.lib.base import BaseController, render
from pylons.controllers.util import abort, redirect
from webui.lib.rdf_helper import add_mediator, get_mediator_details, update_mediator

class AccountController(BaseController):
    """Handles register, login and logout of users """
    def register(self):
        params = request.POST
        if 'firstname' in params and params['firstname'] and \
            'lastname' in params and params['lastname'] and \
            'email' in params and params['email'] and \
            'username' in params and params['username'] and \
            'password' in params and params['password']:
            # Check if user id exists. Write new user into passwd file
            for entry in ag.passwdfile.entries:
                if entry[0] == params['username']:
                    c.message= "This userid exists"
                    return render('/register.html')
            ag.passwdfile.update(params['username'], params['password'])
            ag.passwdfile.save()
            #Write user metadata and save the rdf file
            add_mediator(params)
            session['login_flash'] = "%s you have been registered!"%params['username']
            session.save()  
            return redirect('login', code=303)
        return render('/register.html')

    def update(self, userid):
        identity = request.environ.get("repoze.who.identity")
        came_from = "/update/%s"%userid
        if not identity:
            session['login_flash'] = "Please login to update your details"
            session.save()
            destination = "/login?came_from=%s"%came_from
            return redirect(destination, code=303)
        if not (identity['repoze.who.userid'] == userid):
            session['browse_flash'] = "You are not authorized to change the registration details for %s"%userid
            session.save()
            return redirect(url(controller='vocabs', action='index'), code=303)
        params = request.POST
        if not ('firstname' in params and params['firstname']) and \
           not ('lastname' in params and params['lastname']) and \
           not ('title' in params and params['title']) and \
           not ('email' in params and params['email']) and \
           not ('dept' in params and params['dept']) and \
           not ('password' in params and params['password']):
           c.userid = userid
           c.user_det = get_mediator_details(c.userid)
           return render('/update.html')
        if not ('username' in params and params['username']) or not (params['username'] == userid):
           c.message = "The userid on record did not match the one sent"
           c.userid = userid
           c.user_det = get_mediator_details(c.userid)
           return render('/update.html')
        if 'username' in params and params['username'] and \
           'password' in params and params['password']:
            ag.passwdfile.update(params['username'], params['password'])
            ag.passwdfile.save()
        #Write user metadata and save the rdf file
        update_mediator(params)
        c.message = "Your details have been updated!"
        c.userid = userid
        c.user_det = get_mediator_details(c.userid)
        return render('/update.html')

    def login(self):
        c.userid = None
        c.login_counter = request.environ['repoze.who.logins']
        if c.login_counter > 0:
            session['login_flash'] = """Wrong credentials. Have you registered? <a href="register">Register</a>"""
            session.save()
        c.came_from = request.params.get("came_from") or "/"
        return render('/login.html')

    def welcome(self):
        identity = request.environ.get("repoze.who.identity")
        came_from = request.params.get('came_from', '') or "/"
        if identity:
            # Login succeeded
            userid = identity['repoze.who.userid']
            user_det = get_mediator_details(userid)
            if user_det['name']:
                session['user_name'] = user_det['name']
            if user_det['uri']:
                session['user_uri'] = str(user_det['uri'])
            session['user_id'] = userid
            session.save()
            return redirect(came_from, code=303)
        else:
            # Login failed
            try:
                login_counter = request.environ['repoze.who.logins'] + 1
            except:
                login_counter = 0
            destination = "/login?came_from=%s&logins=%s" % (came_from, login_counter)
            return redirect(destination, code=303)

    def logout(self):
        c.userid = None
        c.message = "We hope to see you soon!"
        #display_message("We hope to see you soon!", status="success")
        came_from = request.params.get('came_from', '') or "/"
        if session.has_key('user_name'):
            del session['user_name']
        if session.has_key('user_uri'):
            del session['user_uri']
        if session.has_key('user_id'):
            del session['user_id']
        if session.has_key('user_dept'):
            del session['user_dept']
        if session.has_key('user_email'):
            del session['user_email']
        session.save()
        #return redirect(came_from, code=303)
        return render('/logout.html')

