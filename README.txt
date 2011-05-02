Vocab-ox

Overview
========

RDF-enhanced web based store for controlled vocabularies, ontologies, taxonomies and thesauri produced at the University of Oxford.

Installation and dependancies
=============================

-  [I would advise using virtualenv]

Dependancies:

pylons==1.0
repoze.who==2.0a3
simplejson
solrpy
pysvn

This project uses svn to manage the vocabularies

-  Change the settings in development.ini to suit your uses, specifically:

htpasswd.file = location of password file (uses basic http auth)
mediators.dir = the directory where the rdf file for each of the users would be created and used to manage access
vocabularies.dir = directory where all the vocabularies would be saved. This should be a local svn working directory

Setup:
======
Setup a svn repository, create the vocabularies directory and check it out
Sym link the vocabularies directory to application_root/webui/templates/ 
Create the 'passwd' file in the root directory of the application using 'htpasswd' or similar:

$ htpasswd -c passwd admin
[enter admin password]

Add any users you wish to access or work with this application.

You should be able to start the application now (as long as the application has access to r+w to the aforementioned 'vocabularies' directory.)

paster serve development.ini

Then, go to localhost/publish, and try to log in as the 'admin' account. You should then be able to upload and manage vocabularies, browse existing vocabularies and register new users.

WGSI deployment:
================
Create a folder called 'egg-cache' and make sure that is writable by the web-server user too.
Modify the file 'dispatch.wsgi' within mod-wsgi folder. Set the path to the application root, egg-cache directory and the path to the production.ini file:

copy the contents of apache-config/vocab_wsgi to your apache2 configuration. 
Note the WSGIScriptAlias points to the dispatch.wsgi file. Modify the path of dispatch.wsgi to match your application root directory,
Make sure the log files defined in there are writable by the web-server user.

