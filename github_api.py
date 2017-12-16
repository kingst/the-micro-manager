import json
import urllib
import urllib2

import creds

def _get_or_post(user, path_or_url, post_data, token):
    if path_or_url.startswith('https://'):
        url = path_or_url
    else:
        url = 'https://api.github.com' + path_or_url
        
    headers = {'Accept': 'application/vnd.github.cloak-preview, application/json'}
    if token is None and not user is None:
        token = user.access_token
        if not user.personal_token is None:
            token = user.personal_token

    if not token is None:
        headers['Authorization'] = 'token ' + token

    if not post_data is None:
        post_data = urllib.urlencode(post_data)

    request = urllib2.Request(url, post_data, headers)
    response = urllib2.urlopen(request)
    #headers = response.info()

    return json.loads(response.read())


def _get(user, path_or_url, token=None):
    return _get_or_post(user, path_or_url, None, token)


def _post(user, path_or_url, data):
    return _get_or_post(user, path_or_url, data, None)


def user(token):
    return _get(None, '/user', token)


def member(user, handle):
    return _get(user, '/users/' + handle)


def commit(user, url):
    return _get(user, url)


def repos(user, org):
    page = 1
    repos = []

    while True:
        path = '/orgs/{}/repos?per_page=100&page={}'.format(org, page)
        result = _get(user, path)

        if len(result) == 0:
            return repos

        for repo in result:
            repos.append(repo)

        page += 1


def commits(user, author, start_date, end_date):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # XXX FIXME link header handling for pagination, generalize

    query_string = 'author:{}+author-date:{}..{}'.format(author,
                                                         start_date_str,
                                                         end_date_str)
    page = 1
    results = []
    while True:
        path = '/search/commits?q={}&page={}&per_page=100'.format(query_string,
                                                                  page)
        result = _get(user, path)
        
        if len(result['items']) == 0:
            print('len(results) = ' + str(len(results)))
            return results
                                                              
        for item in result['items']:
            results.append(item)

        page += 1


def access_token_from_code(code):
    url = 'https://github.com/login/oauth/access_token'
    data = {'client_id': creds.CLIENT_ID,
            'client_secret': creds.CLIENT_SECRET,
            'code': code}
    return _post(None, url, data)
