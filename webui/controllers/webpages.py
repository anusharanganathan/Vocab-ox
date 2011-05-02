from webui.lib.base import BaseController, render

class WebpagesController(BaseController):
    """Renders all the static html pages of the website.
    """
    def index(self):
        """Render the index page"""
        return render('/index.html')

    def about(self):
        """Render the about page"""
        return render('/about.html')

    def help(self):
        """Render the help (guidelines + faq) page"""
        return render('/help.html')

    def contact(self):
        """Render the contact page"""
        return render('/contact.html')

    def privacy(self):
        """Render the privacy page"""
        return render('/privacy.html')
