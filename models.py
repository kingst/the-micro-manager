from dateutil.parser import parse
import datetime
import json
import os
import sqlite3

db_init = False

def create_uuid():
    uuid = os.urandom(24).encode('base64').replace("\n","")
    uuid = uuid.replace("/", "_").replace("+","-")

    return uuid


def get_cursor():
    global db_init

    db = sqlite3.connect('micromanager.db')
    
    cursor = db.cursor()
    if not db_init:
        User.create(cursor)
        Session.create(cursor)
        db_init = True

    return (cursor, db)


class Key():
    @staticmethod
    def from_json_str(json_str):
        data = json.loads(json_str)
        return Key(data['class_name'], data['db_id'])

    def __init__(self, class_name, db_id):
        self.class_name = class_name
        self.db_id = db_id


    def get(self):
        if self.class_name == 'User':
            return User.get_by_userid(self.db_id)

        raise Exception('not implemented')


    def to_string(self):
        return json.dumps({'class_name': self.class_name,
                           'db_id': self.db_id})
    


class Session():
    db_id = None
    user = None
    ctime = None

    def __init__(self, *args, **kwargs):
        self.db_id = kwargs.get('id', create_uuid())
        self.ctime = datetime.datetime.utcnow()

    def put(self):
        (cursor, db) = get_cursor()

        user_key = None
        if not self.user is None and not self.user.db_id is None:
            user_key = Key('User', self.user.db_id)

        values = [self.db_id, user_key.to_string(), self.ctime.isoformat()]
        cursor.execute('INSERT INTO Session ' +\
                       'VALUES (?, ?, ?)', values)

        db.commit()
        db.close()

        return Key('Session', self.db_id)

    @staticmethod
    def create(cursor):
        cursor.execute('CREATE TABLE IF NOT EXISTS Session ' +\
                       '(db_id, user, ctime)')

    @staticmethod
    def get_by_token(token):
        (cursor, db) = get_cursor()
        cursor.execute('SELECT * from Session ' +\
                       "where db_id = '" + token + "'")
        result = cursor.fetchone()
        
        db.close()

        if result == None:
            return None

        session = Session()
        session.db_id = result[0]
        if not result[1] is None:
            session.user = Key.from_json_str(result[1])
        else:
            session.user = None
        session.ctime = parse(result[2])

        return session


class User():
    """ We use the github id for our model IDs """
    access_token = None
    github_user = "{}"               #json property
    ctime = None
    team = "[]" #json property
    personal_token = None

    def __init__(self, *args, **kwargs):
        self.db_id = kwargs.get('id', create_uuid())
        self.ctime = datetime.datetime.utcnow()

    def put(self):
        (cursor, db) = get_cursor()

        values = [self.db_id,
                  self.access_token,
                  json.dumps(self.github_user),
                  self.ctime.isoformat(),
                  json.dumps(self.team),
                  self.personal_token]

        res = cursor.execute('INSERT OR REPLACE INTO User ' +\
                             'VALUES (?, ?, ?, ?, ?, ?)',
                             values)

        db.commit()
        db.close()

        return Key('User', self.db_id)

    @staticmethod
    def create(cursor):
        cursor.execute('CREATE TABLE IF NOT EXISTS User ' +\
                       '(db_id PRIMARY_KEY, access_token, github_user, ' +\
                       ' ctime, team, personal_token)')

    @staticmethod
    def get_by_userid(user_id):
        (cursor, db) = get_cursor()
        cursor.execute('SELECT * FROM User ' +\
                       "WHERE db_id = '" + str(user_id) + "'")
        result = cursor.fetchone()
        db.close()

        if result == None:
            return None

        user = User(id=result[0])
        user.access_token = result[1]
        user.github_user = json.loads(result[2])
        user.ctime = parse(result[3])
        user.team = json.loads(result[4])
        user.personal_token = result[5]

        return user
        

class Commit():
    """ We use the URL of the commit as the model ID """
    github_commiit = "{}" #json property
    author = ""
    date = None     #datetime
    html_url =  ""

    @staticmethod
    def query_by_author(author, start_date, end_date):
        return []
