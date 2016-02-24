from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import json

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

        r=r.result

        if r==1 :
            self.set_secure_cookie('user',user)
            log('user: %s login %s'%(user,self.request.remote_ip))
            jump = self.get_argument('next','/')
            self.redirect_msg(jump,'登录成功')
        elif r ==2 :
            self.render('login.html',msg='用户名或密码格式错误',page_type='login',page_title='登录 -XOJ')
        elif r ==3 :
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
        r = r.result
        if r[0]==1 :
            log('user: %s register'%user)
            self.redirect_msg('/login','注册成功')
        elif r[0]==2 :
            self.render('register.html',msg=r[1],page_type='register',page_title='注册 -XOJ')
        else:
            log('register error user: %s r0: %d r1: %s',user,r[0],r[1])
            self.render('register.html',msg='未知错误',page_type='register',page_title='注册 -XOJ')

class ShowUserHandler(BaseHandler):

    @gen.coroutine
    def get(self,user):
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT user,email,school,motto,admin,ac_num,submit_num,tongji,ac_list FROM user WHERE user = %s"
        yield cur.execute(sql,(user,))
        user_info=cur.fetchone()
        cur.close()
        conn.close()
        if user_info == None:
            self.redirect_msg('/','用户名错误')
            return
        user_info=list(user_info)
        user_info[7],user_info[8]=json.loads(user_info[7]),json.loads(user_info[8])
        self.render('show_user.html',msg=msg,page_type='user',user=user_info,get_pic=get_pic,page_title='用户:'+user+' -XOJ')

class EditHandler0(BaseHandler):

    @gen.coroutine
    def post(self,user):
        pw = self.get_argument('oldpassword')
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT user FROM user WHERE user = %s AND password = %s LIMIT 1"
        yield cur.execute(sql,(user,gen_pw(user,pw),))
        r = cur.fetchone()
        if r == None:
            cur.close()
            conn.close()
            self.redirect_msg('/user/%s/edit/0'%user,'用户名或密码错误')
            return
        email,school,motto = [self.get_argument(s) for s in ['email','school','motto']]
        newpw = self.get_argument('newpassword',None)
        if newpw:
            pass
        else:
            newpw=pw

        sql = "UPDATE user SET email = %s,school = %s,motto = %s,password = %s  WHERE user = %s"
        try:
            yield cur.execute(sql,(email,school,motto,gen_pw(user,newpw),user))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/user/%s/edit/0'%user,'数据库错误')
            raise
        else:
            self.redirect_msg('/user/%s'%user,'修改资料成功')
        finally:
            cur.close()
            conn.close()


    @gen.coroutine
    def get(self,user):
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT user,email,school,motto FROM user WHERE user = %s"
        yield cur.execute(sql,(user,))
        user_info=cur.fetchone()
        cur.close()
        conn.close()
        if user_info == None:
            self.redirect_msg('/','用户名错误')
            return
        self.render('edit_user_0.html',msg=msg,page_type='user',user=user_info,get_pic=get_pic,page_title='修改资料:'+user+' -XOJ')

class EditHandler1(BaseHandler):


    @gen.coroutine
    def post(self,user):
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        p = [self.get_argument(s) for s in ['email','school','motto','admin']]

        sql = "UPDATE user SET email = %s,school = %s,motto = %s,admin = %s  WHERE user = %s"
        try:
            yield cur.execute(sql,(*p,user))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/user/%s/edit/1'%user,'数据库错误')
            raise
        else:
            self.redirect_msg('/user/%s'%user,'修改资料成功')
        finally:
            cur.close()
            conn.close()

    @gen.coroutine
    def get(self,user):
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT user,email,school,motto,admin,gen_date FROM user WHERE user = %s"
        yield cur.execute(sql,(user,))
        user_info=cur.fetchone()
        cur.close()
        conn.close()
        if user_info == None:
            self.redirect_msg('/','用户名错误')
            return
        self.render('edit_user_1.html',msg=msg,page_type='user',user=user_info,get_pic=get_pic,page_title='管理用户:'+user+' -XOJ')

