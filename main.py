"""
Main entry point for the top level app.
"""
import datetime
import jinja2
import json
import operator
import os
import urllib
import urllib2
import webapp2

import google.appengine.api.memcache as memcache

import creds
import decorators
from github import Github
from models import Session
from models import User

ORG = 'lyft'

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
    headers = {'Accept': 'application/vnd.github.cloak-preview',
               'Authorization': 'token ' + access_token}

    if data is None:
        data = {}

    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    headers = response.info()
    return json.loads(response.read())
    


class HomeHtml(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(template.render({'client_id': creds.CLIENT_ID}))


def query_commits(user, author, start_date, end_date):
    # XXX FIXME use link header for pagination
    print(author)
    query_string = 'author:{}+author-date:{}..{}'.format(author,
                                                         start_date,
                                                         end_date)
    
    cached_data = memcache.get(query_string)
    if cached_data is not None:
        return json.loads(cached_data)

    page = 1
    results = []
    token = user.access_token
    if not user.personal_token is None:
        token = user.personal_token
    while True:
        result = github_api('/search/commits?q={}&page={}&per_page=100'.format(query_string, page),
                            token)
        if len(result['items']) == 0:
            memcache.add(query_string, json.dumps(results), 10000)
            return results

        for item in result['items']:
            results.append({'url': item['url'],
                            'message': item['commit']['message'],
                            'date': item['commit']['author']['date']})
        page += 1


class DataFill(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self):
        pass


class Team(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self):
        team = self.request.user.team
        team_template = []
        start_date = self.request.get('start_date',
                                      str(datetime.date.today() - datetime.timedelta(days=30)))
        end_date = self.request.get('end_date', str(datetime.date.today()))
        today = str(datetime.date.today())
                                      
        for member in team:
            commits = query_commits(self.request.user, member,
                                    start_date, end_date)
            team_template.append({'member': member, 'commits': len(commits)})

        team_template = sorted(team_template, key=lambda x: x['commits'], reverse=True)
        template = JINJA_ENVIRONMENT.get_template('templates/team.html')
        self.response.write(template.render({'team': team_template,
                                             'start_date': start_date,
                                             'end_date': end_date,
                                             'ninty_days_ago': str(datetime.date.today() - datetime.timedelta(days=90)),
                                             'sixty_days_ago': str(datetime.date.today() - datetime.timedelta(days=60)),
                                             'thirty_days_ago': str(datetime.date.today() - datetime.timedelta(days=30)),
                                             'today': str(datetime.date.today())}))


class AddMember(webapp2.RequestHandler):
    @decorators.web_page(True)
    def post(self):
        member = self.request.get('handle', None)

        # make sure that it is a valid handle, it'll 404 if it's not
        result = github_api('/users/' + member, self.request.user.access_token)
        if not member in self.request.user.team:
            self.request.user.team.append(member)
            self.request.user.put()

        self.redirect('/team')


class CheatCode(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self):
        personal_token = self.request.get('personal_token', None)
        if not personal_token is None:
            if len(personal_token) == 0:
                personal_token = None
            self.request.user.personal_token = personal_token
            self.request.user.put()

        self.redirect('/team')


class DeleteMember(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self, member):
        if member in self.request.user.team:
            self.request.user.team.remove(member)
            self.request.user.put()

        self.redirect('/team')


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
    [(r'/', HomeHtml),
     (r'/auth', Auth),
     (r'/data_fill', DataFill),
     (r'/team/members/(.*)/delete', DeleteMember),
     (r'/team/add_member', AddMember),
     (r'/team', Team),
     (r'/cheat_code', CheatCode)],
     debug=True)


def main():
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
