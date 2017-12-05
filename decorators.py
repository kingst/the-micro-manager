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
                auth_user = session.user.get()

            if auth_required and auth_user is None:
                # throw a 503 or permission error
                pass
            
            self.request.user = auth_user

            try:
                context = function(self, *args, **kwargs)
            except Exception as e:
                logging.exception(e)
                # throw a 500 of some sort
                pass

            if context is None:
                context = {}

            # do something to serve the web page

        return decoration
    return decorator_generator
