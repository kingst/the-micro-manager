import datetime

import db

class Session(db.Model):
    __table__ = 'Session'
    user = db.key_property(__table__, 'user')
    ctime = db.datetime_property(__table__, 'ctime', datetime.datetime.utcnow())

    @staticmethod
    def get_by_id(id):
        session = Session()
        return session.load_from_db(id)


class User(db.Model):
    """ We use the github id for our model IDs """
    __table__ = 'User'
    access_token = db.string_property(__table__, 'access_token')
    github_user = db.json_property(__table__, 'github_user')
    ctime = db.datetime_property(__table__, 'ctime', datetime.datetime.utcnow())
    team = db.json_property(__table__, 'team', [])
    personal_token = db.string_property(__table__, 'personal_token')

    @staticmethod
    def get_by_id(id):
        user = User()
        return user.load_from_db(id)


class Commit(db.Model):    
    """ We use the URL of the commit as the model ID """
    __table__ = 'CommitModel'
    github_commit = db.json_property(__table__, 'github_commit')
    author = db.string_property(__table__, 'author')
    date = db.datetime_property(__table__, 'date')
    html_url = db.string_property(__table__, 'html_url')

    @staticmethod
    def query_by_author(author, start_date, end_date):
        if not isinstance(start_date, datetime.datetime) or not isinstance(end_date, datetime.datetime):
            raise Exception('start and end date must be of type datetime')

        # this isn't ideal, too much implementation at this level
        where_str = "date >= '{}' AND date <= '{}' AND author = '{}'"        
        where_str = where_str.format(start_date.isoformat(),
                                     end_date.isoformat(),
                                     author)
        order_str = 'date DESC'

        return db.Model.query(Commit, 'CommitModel', where_str, order_str)
