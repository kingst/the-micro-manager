import logging
import json


class MMRedirect(Exception):
    """Throw an exception to redirect the user"""
    def __init__(self, path):

        super(MMRedirect, self).__init__()
        self.path = path


class MMError(Exception):
    """An error thrown by a request handler """
    def __init__(self, error_dict):

        super(MMError, self).__init__()
        self.error_code = error_dict.get('code', None)
        self.error_message = error_dict.get('message', None)

        logging.warn(self.to_result())

    def to_result(self):
        """ Convert the error into a json string """
        return json.dumps({
            'status': 'error',
            'error_code': self.error_code,
            'error_message': self.error_message
        }, indent=4)
