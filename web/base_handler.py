from tornado import httpserver,ioloop,web,gen,httpclient

class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')
    