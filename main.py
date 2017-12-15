"""
Main entry point for the top level app.
"""
import datetime
import jinja2
import json
import operator
import os
import time
import urllib
import urllib2
import webapp2

from dateutil.parser import parse

import commits
import creds
import decorators
import github_api
from models import Commit
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


class HomeHtml(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/home.html')
        self.response.write(template.render({'client_id': creds.CLIENT_ID}))


class DataFill(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self):
        for author in self.request.user.team:
            print(author)
            last_pr_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
            prs = commits.query(self.request.user,
                                author,
                                last_pr_date,
                                datetime.datetime.utcnow())
            if len(prs) > 0:
                last_pr_date = prs[0]['date']
            commits.load_commits(self.request.user,
                                 author,
                                 last_pr_date,
                                 datetime.datetime.utcnow())


        template = JINJA_ENVIRONMENT.get_template('templates/datafill.html')
        self.response.write(template.render({'data_fill_active': True}))


class Prs(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self, member):
        start_date = self.request.get('start_date',
                                      str(datetime.date.today() - datetime.timedelta(days=30)))
        end_date = self.request.get('end_date', str(datetime.date.today()))
        today = str(datetime.date.today())

        cs = commits.query(self.request.user, member,
                           start_date, end_date)

        cs = sorted(cs, key=lambda x: x['date'], reverse=True)
        cs = map(lambda x: {'date': x['date'].strftime('%m/%d/%Y'),
                            'url': x['html_url'],
                            'message': x.get('message', '')},
                 cs)

        repo_counts = {}
        for c in cs:
            slash_idx = c['url'].rfind('/')
            c['repo'] = c['url'][19:slash_idx-7]
            if not c['repo'] in repo_counts:
                repo_counts[c['repo']] = 0
            repo_counts[c['repo']] += 1
            
        repo_stats = []
        for key in repo_counts.keys():
            repo_stats.append({'repo': key, 'count': repo_counts[key]})
        repo_stats = sorted(repo_stats, key=lambda x: x['count'], reverse=True)

        template = JINJA_ENVIRONMENT.get_template('templates/member.html')
        self.response.write(template.render({'prs': cs,
                                             'repo_stats': repo_stats,
                                             'member': member,
                                             'start_date': start_date,
                                             'end_date': end_date,
                                             'ninty_days_ago': str(datetime.date.today() - datetime.timedelta(days=90)),
                                             'sixty_days_ago': str(datetime.date.today() - datetime.timedelta(days=60)),
                                             'thirty_days_ago': str(datetime.date.today() - datetime.timedelta(days=30)),
                                             'today': str(datetime.date.today())}))



class Team(webapp2.RequestHandler):
    @decorators.web_page(True)
    def get(self):
        start_date = self.request.get('start_date',
                                      str(datetime.date.today() - datetime.timedelta(days=30)))
        end_date = self.request.get('end_date', str(datetime.date.today()))
        template = JINJA_ENVIRONMENT.get_template('templates/team.html')

        team = []
        for author in self.request.user.team:
            team.append(commits.summary(self.request.user,
                                        author,
                                        parse(start_date),
                                        parse(end_date)))

        team = sorted(team, key=lambda k: k['commits'], reverse=True)
        self.response.write(template.render({'team': team,
                                             'team_active': True,
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
        result = github_api.member(self.request.user, member)
        if not member in self.request.user.team:
            self.request.user.team.append(member)
            self.request.user.put()

            start_date = datetime.date.today() - datetime.timedelta(days=90)
            end_date = datetime.date.today()
            commits.load_commits(self.request.user, member,
                                 start_date, end_date)

        self.redirect('/team')


class CheatCode(webapp2.RequestHandler):

    @decorators.web_page(True)
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/cheat_code.html')
        self.response.write(template.render({}))


    @decorators.web_page(True)
    def post(self):
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
        result = github_api.access_token_from_code(code)
        access_token = result['access_token']
        
        result = github_api.user(access_token)

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
     (r'/team/members/(.*)/prs', Prs),
     (r'/team/members/(.*)/delete', DeleteMember),
     (r'/team/add_member', AddMember),
     (r'/team', Team),
     (r'/cheat_code', CheatCode)],
     debug=True)


def main():
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
