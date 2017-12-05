"""
Main entry point for the top level app.
"""
import datetime
import jinja2
import json
import os
import urllib
import urllib2
import webapp2
from webapp2_extras.routes import RedirectRoute

import creds
from models import Session
from models import User

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def _create_uuid():
    uuid = os.urandom(24).encode('base64').replace("\n","")
    uuid = uuid.replace("/", "_").replace("+","-")

    return uuid


def github_api(path, access_token, data=None):
    url = 'https://api.github.com' + path
    headers = {'Accept': 'application/vnd.github.v3+json',
               'Authorization': 'token ' + access_token}

    if data is None:
        data = {}

    request = urllib2.Request(url, None, headers)
    return json.loads(urllib2.urlopen(request).read())
    


class HomeHtml(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(template.render({'client_id': creds.CLIENT_ID}))


class Auth(webapp2.RequestHandler):
    def get(self):
        # XXX FIXME ignore state for now since we're going to rely on
        # GitHub to track users
        code = self.request.get('code')

        url = 'https://github.com/login/oauth/access_token'
        data = urllib.urlencode({'client_id': creds.CLIENT_ID,
                                 'client_secret': creds.CLIENT_SECRET,
                                 'code': code})
        headers = {'Accept': 'application/json'}
        request = urllib2.Request(url, data, headers)
        
        response = urllib2.urlopen(request)
        result = json.loads(response.read())

        access_token = result['access_token']
        
        result = github_api('/user', access_token)
        print(json.dumps(result, indent=4))

        user = User.get_by_id(result['id'])
        if user is None:
            user = User(id=result['id'])

        user.access_token = access_token
        user.github_user = result

        user_key = user.put()
        session_token = _create_uuid()
        session = Session(id=session_token)
        session.user = user_key
        session.put()

        expires = datetime.datetime.now() + datetime.timedelta(days=20*365.25)

        self.response.set_cookie('session_token', session_token, httponly=False,
                                 overwrite=True, expires=expires)
        self.redirect('/team')


app = webapp2.WSGIApplication(
    [RedirectRoute(r'/', HomeHtml),
     RedirectRoute(r'/auth', Auth)],
     debug=False)


def main():
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
