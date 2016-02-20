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
        user = self.current_user
        self.render('index.html',user=user,msg=msg)


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
    ],**settings)

    application.listen(5000)
    ioloop.IOLoop.instance().start()
