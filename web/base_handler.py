from tornado import httpserver,ioloop,web,gen,httpclient
import urllib.parse

class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('user')
    def redirect_msg(self,url,msg):
        self.redirect(url+'?'+urllib.parse.urlencode({'msg':msg}))

