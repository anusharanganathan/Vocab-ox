import pysvn
import os
from pylons import app_globals as ag

def svn_add(path, message, commit=False):
    client = pysvn.Client('/home/vocabadmin/.svn')
    client.callback_get_login = lambda realm, username, may_save:(True, ag.svnusername, ag.svnpassword, True)
    try:
        client.add(path)
        added = True
    except Exception, e:
        added = False
        msg = e
        return(added, msg)
    if not commit:
        return(added, 'File added')
    #Committing changes
    try:
        if message:
            client.checkin(['%s'%path], message)
        else:
            client.checkin(['%s'%path], "Adding %s"%path)
        added = True
        message = None
    except Exception, e:
        added = False
        message = e
    return (added, message)
    
def svn_remove(path, message, commit=False):
    client = pysvn.Client('/home/vocabadmin/.svn')
    client.callback_get_login = lambda realm, username, may_save:(True, ag.svnusername, ag.svnpassword, True)
    try:
        client.remove(path)
        added = True
    except Exception, e:
        added = False
        msg = e
        return(added, msg)
    if not commit:
        return(added, 'File removed')
    #Committing changes
    try:
        if message:
            client.checkin(['%s'%path], message)
        else:
            client.checkin(['%s'%path], "Adding %s"%path)
        added = True
        message = None
    except Exception, e:
        added = False
        message = e
    return (added, message)

def svn_commit(commitfilelist, message):
    client = pysvn.Client('/home/vocabadmin/.svn')
    client.callback_get_login = lambda realm, username, may_save:(True, ag.svnusername, ag.svnpassword, True)
    try:
        if message:
            client.checkin(commitfilelist, message)
        else:
            client.checkin(commitfilelist, "Adding %s"%path)
        added = True
        message = None
    except Exception, e:
        added = False
        message = e
    return (added, message)

