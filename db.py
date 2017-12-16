from dateutil.parser import parse
import datetime
import json
import os
import sqlite3

_columns = {}
db_init = False
db_name = 'micromanager.db'


def create_uuid():
    uuid = os.urandom(24).encode('base64').replace("\n","")
    uuid = uuid.replace("/", "_").replace("+","-")

    return uuid


def _init_db(cursor, db):
    for table in _columns.keys():
        col_names = map(lambda x: '_db_id UNIQUE' if x[0] == '_db_id' else x[0], _columns[table])
        name_str = ','.join(col_names)
        query = 'CREATE TABLE IF NOT EXISTS {}({})'.format(table, name_str)
        cursor.execute(query)
    db.commit()


def get_cursor():
    global db_init

    db = sqlite3.connect(db_name)
    
    cursor = db.cursor()
    if not db_init:
        _init_db(cursor, db)
        db_init = True

    return (cursor, db)


def _add_column(base_type, table, name, default):
    if not table in _columns:
        _columns[table] = [('_db_id', 'string')]

    column = (name, base_type)
    if column in _columns[table]:
        raise Exception('column already exists')
    
    _columns[table].append(column)
    return default


def string_property(table, name, default=None):
    return _add_column('string', table, name, default)


def datetime_property(table, name, default=None):
    return _add_column('datetime', table, name, default)


def json_property(table, name, default=None):
    return _add_column('json', table, name, default)


def key_property(table, name, default=None):
    return _add_column('key', table, name, default)


class Key():
    @staticmethod
    def from_json_str(json_str):
        data = json.loads(json_str)
        return Key(data['class_name'], data['db_id'])

    def __init__(self, class_name, db_id):
        self.class_name = class_name
        self.db_id = db_id


    def get(self, cls):
        result = cls()
        return result.load_from_db(self.db_id)


    def to_string(self):
        return json.dumps({'class_name': self.class_name,
                           'db_id': self.db_id})
    

class Model(object):
    _db_id = None


    def __init__(self, *args, **kwargs):
        self._db_id = kwargs.get('id', create_uuid())


    @staticmethod
    def to_user_type(col_type, value):
        if col_type == 'string':
            return value
        elif col_type == 'key':
            return Key.from_json_str(value)
        elif col_type == 'datetime':
            return parse(value)
        elif col_type == 'json':
            return json.loads(value)
        else:
            raise Exception('type ' + col_type + ' not found')


    @staticmethod
    def query(cls, table, where_str, order_str):
        col_names = map(lambda x: x[0], _columns[table])
        name_str = ','.join(col_names)
        query = "SELECT {} FROM {} WHERE {} ORDER BY {}".format(name_str,
                                                                table,
                                                                where_str,
                                                                order_str)

        (cursor, db) = get_cursor()
        cursor.execute(query)

        results = []
        for result in cursor.fetchall():
            c = cls()
            c.from_db_result(result)
            results.append(c)

        db.close();

        return results


    def load_from_db(self, id):
        col_names = map(lambda x: x[0], _columns[self.__table__])
        name_str = ','.join(col_names)
        query = "SELECT {} FROM {} WHERE _db_id = '{}'".format(name_str,
                                                               self.__table__,
                                                               id)

        (cursor, db) = get_cursor()
        cursor.execute(query)

        result = cursor.fetchone()

        db.close()

        if result is None:
            return None

        self.from_db_result(result)

        return self


    def from_db_result(self, result):
        for ((name, col_type), value) in zip(_columns[self.__table__], result):
            setattr(self, name, Model.to_user_type(col_type, value))        


    def put(self):
        cols = _columns[self.__table__]
        values = []

        for col in cols:
            value = getattr(self, col[0])
            if col[1] == 'string':
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                elif not isinstance(value, str):
                    value = str(value)
            elif col[1] == 'datetime':
                # XXX FIXME we should convert to UST before storing
                value = value.isoformat()
            elif col[1] == 'json':
                value = json.dumps(value)
            elif col[1] == 'key':
                value = value.to_string()
            else:
                raise Exception('unknown user type ' + col[1])

            values.append(value)
            
        (cursor, db) = get_cursor()
        
        query = 'INSERT OR REPLACE INTO {} VALUES ({})'.format(self.__table__,
                                                               ','.join(map(lambda x: '?', values)))
        cursor.execute(query, values)

        db.commit()
        db.close()

        return Key(self.__table__, self._db_id)
