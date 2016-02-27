from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import json
import re

user_rule=r'^[a-zA-Z][0-9a-zA-Z\-]{0,19}$'
email_rule=r'^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,3}|[0-9]{1,3})(\]?)$'

class LoginHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('login.html',msg=msg,page_type='login',page_title='登录 -XOJ')

    
    @gen.coroutine
    def post(self):
        user = self.get_argument('user')
        password = self.get_argument('password')

        if not re.match(user_rule,user):
            self.redirect_msg('/login','用户名格式错误')
            return

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT user FROM user WHERE user = %s AND password = %s LIMIT 1"
        yield cur.execute(sql,(user,gen_pw(user,password)))
        user=cur.fetchone()
        cur.close()
        conn.close()

        if user :
            user=user[0]
            self.set_secure_cookie('user',user)
            log('user: %s login %s'%(user,self.request.remote_ip))
            jump = self.get_argument('next','/')
            self.redirect_msg(jump,'登录成功')
            return
        else:
            self.redirect_msg(jump,'用户名或密码错误')
            return


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

    
    @gen.coroutine
    def post(self):
        user,pw,email,school,invitecode= [self.get_argument(s) for s in \
        ['user','password','email','school','invitecode']]
        now=datetime.now()

        if not re.match(user_rule,user):
            self.redirect_msg('/register','用户名格式错误('+user_rule+')')
            return
        if len(pw)<6 :
            self.redirect_msg('/register','密码太短')
            return
        if not re.match(email_rule,email):
            self.redirect_msg('/register','邮件格式错误')
            return
        if len(email) > 50:
            self.redirect_msg('/register','邮件太长')
            return
        if len(school)<2 :
            self.redirect_msg('/register','请填写学校')
            return
        if len(school)>20 :
            self.redirect_msg('/register','学校太长')
            return

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur=conn.cursor()
        sql = "SELECT user FROM user WHERE user=%s LIMIT 1"
        yield cur.execute(sql,(user,))
        result = cur.fetchone()
        if result != None:
            cur.close()
            conn.close()
            self.redirect_msg('/register','用户名已存在')
            return
        #InviteCode
        if invitecode != 'test':
            return [2,'邀请码错误']

        sql = "INSERT INTO user (user,password,email,school,\
            motto,admin,ac_num,submit_num,msg_num,tongji,ac_list,gen_date) VALUES \
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        yield cur.execute(sql,(user,gen_pw(user,pw),email,school,\
            'Write the code. Change the world.',0,0,0,0,json.dumps([0]*7),json.dumps([]),str(now),))
        yield conn.commit()
        cur.close()
        conn.close()

        self.redirect_msg('/login','注册成功')
        


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
        if user.encode('utf-8') == self.current_user :
            pgtp='setting'
        else:
            pgtp='user'
        self.render('show_user.html',msg=msg,page_type=pgtp,user=user_info,get_pic=get_pic,page_title='用户:'+user+' -XOJ')

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
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],user))
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

