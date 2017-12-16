from error import MMRedirect
import logging
from models import Session
from models import User

def web_page(auth_required=True):
    """Decorator for requests to web pages.
    
    Loads the user object for any authenticated users, throws an error
    if they try to access a page that requires authentication and the
    user isn't authenticated.
    """
    def decorator_generator(function):
        def decoration(self, *args, **kwargs):
            auth_user = None
            if 'session_token' in self.request.cookies:
                session_token = self.request.cookies['session_token']
                session = Session.get_by_id(session_token)
                # XXX fixme we should be able to do this without
                # passing in User explicitly
                auth_user = session.user.get(User)

            if auth_required and auth_user is None:
                self.redirect('/')
                return
            
            self.request.user = auth_user

            try:
                function(self, *args, **kwargs)
            except MMRedirect as redir:
                self.redirect(redir.path)
            except Exception as e:
                logging.exception(e)
                raise e

        return decoration
    return decorator_generator
