from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *


class LoginHandler(BaseHandler):

    def get(self):
        self.render('login.html',error=None)

    @web.asynchronous
    @gen.coroutine
    def post(self):
        user=self.get_argument('user')
        password=self.get_argument('password')

        r = yield gen.Task(tasks.login.apply_async,args=[user,password])
        if r.result==1 :
            self.set_secure_cookie('username',user)
            log('%s  user: %s login'%(datetime.now(),user))

            jump=self.get_argument('next','/')
            
            self.redirect(jump)
        elif r.result==2 :
            self.render('login.html',error='用户名或密码格式错误')
        elif r.result==3 :
            self.render('login.html',error='用户名或密码错误')
        else:
            log('%s  user:%s pass:%s val:%s'%(datetime.now(),user,password,str(r.result)))
            self.render('login.html',error='未知错误')

class LogoutHandler(BaseHandler):

    def get(self):
        self.clear_cookie('username')
        self.redirect('/')