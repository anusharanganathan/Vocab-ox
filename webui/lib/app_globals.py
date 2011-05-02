"""The application's Globals object"""
#from repoze.who.config import make_api_factory_with_config
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from webui.lib.htpasswd import HtpasswdFile
class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.cache = CacheManager(**parse_cache_config_options(config))
        if config.has_key("htpasswd.file"):
            self.passwdfile = HtpasswdFile(config['htpasswd.file'])
            self.passwdfile.load()

        if config.has_key("mediators.dir"):
            self.mediatorsdir = config['mediators.dir']

        if config.has_key("mediators.list"):
            self.mediatorslist = config['mediators.list']

        if config.has_key("vocabularies.dir"):
            self.vocabulariesdir = config['vocabularies.dir']

        if config.has_key("vocabularies.ref"):
            self.vocabulariesref = config['vocabularies.ref']

        if config.has_key("ext_vocabularies.dir"):
            self.extvocabulariesdir = config['ext_vocabularies.dir']

        if config.has_key("svn.username"):
            self.svnusername = config['svn.username']

        if config.has_key("svn.password"):
            self.svnpassword = config['svn.password']

        if config.has_key("conversion_template"):
            self.conversion_template = config['conversion_template']

        #if config.has_key("conversion_toolset.xsl"):
        #    self.conversion_xsl = config['conversion_toolset.xsl']
        #if config.has_key("who.config_file"):
        #    self.who_api_factory = make_api_factory_with_config(config, config['who.config_file'])


