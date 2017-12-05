"""
Main entry point for the top level app.
"""
import jinja2
import os
import webapp2
from webapp2_extras.routes import RedirectRoute


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def _create_uuid():
    uuid = os.urandom(24).encode('base64').replace("\n","")
    uuid = uuid.replace("/", "_").replace("+","-")

    return uuid


class HomeHtml(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(template.render({}))


app = webapp2.WSGIApplication(
    [RedirectRoute(r'/', HomeHtml)],
     debug=False)


def main():
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
