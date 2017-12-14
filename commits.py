import datetime
from dateutil.parser import parse
import json
import time

import github_api
from models import Commit

def load_commits(user, author, start_date, end_date):
    print('loading commits for ' + author)
    result = github_api.commits(user, author, start_date, end_date)
    for r in result:        
        print('putting ' + r['sha'])
        commit = Commit(id=r['sha'])
        commit.author = author
        ts = time.mktime(parse(r['commit']['author']['date']).timetuple())
        commit.date = datetime.datetime.utcfromtimestamp(ts)
        commit.html_url = r['html_url']
        commit.put()


def query(user, author, start_date, end_date):
    print()
    print(start_date)
    print(end_date)
    print()
    commit_query = Commit.query(Commit.date >= start_date,
                                Commit.date <= end_date,
                                Commit.author == author).order(-Commit.date)
    result = []
    for commit in commit_query:
        result.append({'author': commit.author,
                       'date': commit.date,
                       'html_url': commit.html_url})

    return result


def summary(user, author, start_date, end_date):
    return {'author': author,
            'commits': len(query(user, author, start_date, end_date)),
            'reviews': 0}
        
