from tornado import httpserver,ioloop,web,gen,httpclient
import user_handler
import tcelery
import tasks
from base_handler import BaseHandler
from tools import *

tcelery.setup_nonblocking_producer()


class MainHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('index.html',msg=msg,page_title='XOJ',page_type='index')

class TestHandler(BaseHandler):
    def get(self):
        self.render('test.html',msg=None,page_title='测试页 -XOJ',page_type='test')
        
if __name__ == '__main__':

    settings={
        'cookie_secret':'topsecret',
        'template_path':'./templates',
        'static_path':'./static',
        'debug':True,
        'login_url':'/login',
        'xsrf_cookies':True,
    }

    application = web.Application(handlers=[
        (r'/',MainHandler),
        (r'/login',user_handler.LoginHandler),
        (r'/logout',user_handler.LogoutHandler),
        (r'/register',user_handler.RegisterHandler),
        (r'/test',TestHandler),
    ],**settings)

    application.listen(5000)
    ioloop.IOLoop.instance().start()
