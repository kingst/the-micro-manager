from google.appengine.ext import ndb


class Session(ndb.Model):
    user = ndb.KeyProperty()
    ctime = ndb.DateTimeProperty(auto_now_add=True)


class User(ndb.Model):
    """ We use the github id for our model IDs """
    access_token = ndb.TextProperty()
    github_user = ndb.JsonProperty()
    ctime = ndb.DateTimeProperty(auto_now_add=True)
    mtime = ndb.DateTimeProperty(auto_now=True)
    team = ndb.JsonProperty(default=[])
    personal_token = ndb.TextProperty(default=None)
