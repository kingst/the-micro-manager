from google.appengine.ext import ndb


class Session(ndb.Model):
    user = ndb.KeyProperty()
    ctime = ndb.DateTimeProperty(auto_now_add=True)


class User(ndb.Model):
    github_access_token = ndb.TextProperty()
    github_email = ndb.StringProperty()
    ctime = ndb.DateTimeProperty(auto_now_add=True)
    mtime = ndb.DateTimeProperty(auto_now=True)
