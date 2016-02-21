from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *


class LoginHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('login.html',msg=msg,page_type='login',page_title='登录 -XOJ')

    @web.asynchronous
    @gen.coroutine
    def post(self):
        user = self.get_argument('user')
        password = self.get_argument('password')

        r = yield gen.Task(tasks.login.apply_async,args=[user,password])

        if r.result==1 :
            self.set_secure_cookie('user',user)
            log('user: %s login'%user)
            jump = self.get_argument('next','/')
            self.redirect_msg(jump,'登录成功')
        elif r.result==2 :
            self.render('login.html',msg='用户名或密码格式错误',page_type='login',page_title='登录 -XOJ')
        elif r.result==3 :
            self.render('login.html',msg='用户名或密码错误',page_type='login',page_title='登录 -XOJ')
        else:
            log('login error user:%s pass:%s val:%s'%(user,password,str(r.result)))
            self.render('login.html',msg='未知错误',page_type='login',page_title='登录 -XOJ')


class LogoutHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('logout.html',msg=msg,page_type='logout',page_title='注销 -XOJ')
    def post(self):
        self.clear_cookie('user')
        self.redirect_msg('/','注销成功')


class RegisterHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('register.html',msg=msg,page_type='register',page_title='注册 -XOJ')

    @web.asynchronous
    @gen.coroutine
    def post(self):
        user,pw,email,school,invitecode= [self.get_argument(s) for s in \
        ['user','password','email','school','invitecode']]
        now=datetime.now()
        r = yield gen.Task(tasks.register.apply_async,args=[user,pw,email,school,invitecode,now])
        r=r.result
        if r[0]==1 :
            log('user: %s register'%user)
            self.redirect_msg('/login','注册成功')
        elif r[0]==2 :
            self.render('register.html',msg=r[1],page_type='register',page_title='注册 -XOJ')
        else:
            log('register error user: %s r0: %d r1: %s',user,r[0],r[1])
            self.render('register.html',msg='未知错误',page_type='register',page_title='注册 -XOJ')

