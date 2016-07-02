from tornado import httpserver,ioloop,web,gen,httpclient
import urllib.parse
from tools import *
class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('user')
    def auth(self):
        return int(self.get_secure_cookie('auth'))
    def redirect_msg(self,url,msg):
        self.redirect(add_param(url,'msg',msg.encode('utf-8')))
