from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql
import urllib.parse
import json
import random

class ProblemsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #visible
        sql = "SELECT id,name,ac_num,submit_num FROM problems LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.PROBLEMS_PER_PAGE,conf.PROBLEMS_PER_PAGE))
        problems = [[row[0],row[1],row[2],row[3],int((row[2]+1)/(row[3]+1)*100)] for row in cur]
        cur.close()
        conn.close()

        pages=gen_pages('\problems',page_now)
        self.render('problems.html',msg=msg,problems=problems,pages=pages,\
            page_type='problem',page_title='题库 -XOJ')

class ProblemHandler(BaseHandler):

    @gen.coroutine
    def get(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        msg = self.get_argument('msg',None)
        
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,tp,name,content,tim_limit,mem_limit,author,ac_num,submit_num FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        self.render('problem.html',msg=msg,problem=problem,page_type='problem',\
            page_title='#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class EditProblemHandler0(BaseHandler):
    
    @gen.coroutine
    def post(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/problems','题目编号错误')
            return
        p=[self.get_argument(s) for s in ['tp','name','tim_limit','mem_limit','author','visible'] ]
        sql = "UPDATE problems SET tp = %s,name = %s,tim_limit = %s,mem_limit = %s,author = %s,visible = %s WHERE id = %s"

        try:
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],p[4],p[5],prob_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/problem/%d/edit/0'%prob_id,'修改失败，数据库错误')
            raise
        else:
            self.redirect_msg('/problem/%d/edit/0'%prob_id,'修改成功')
        finally:
            cur.close()
            conn.close()


    #管理，提供信息
    @gen.coroutine
    def get(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        msg = self.get_argument('msg',None)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,tp,name,tim_limit,mem_limit,author,visible,gen_date,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        sql = "SELECT id,author,status,tim_use,mem_use,code_len FROM judge WHERE problem_id = %s ORDER BY id DESC LIMIT 10"
        yield cur.execute(sql,(prob_id,))
        status = [row for row in cur]
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        tongji=json.loads(problem[8])
        self.render('edit_problem_0.html',msg=msg,problem=problem,status=status,tongji=tongji,page_type='problem',\
            page_title='管理#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class EditProblemHandler1(BaseHandler):

    @gen.coroutine
    def post(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/problems','题目编号错误')
            return
        p=[self.get_argument(s) for s in ['content','images'] ]
        sql = "UPDATE problems SET content = %s,images = %s WHERE id = %s"

        try:
            yield cur.execute(sql,(p[0],p[1],prob_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/problem/%d/edit/1'%prob_id,'修改失败，数据库错误')
            raise
        else:
            self.redirect_msg('/problem/%d/edit/1'%prob_id,'修改成功')
        finally:
            cur.close()
            conn.close()

    #编辑题目内容
    @gen.coroutine
    def get(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        msg = self.get_argument('msg',None)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,tp,name,content,images,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        sql = "SELECT id,author,status,tim_use,mem_use,code_len FROM judge WHERE problem_id = %s ORDER BY id DESC LIMIT 10"
        yield cur.execute(sql,(prob_id,))
        status = [row for row in cur]
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        tongji=json.loads(problem[5])
        self.render('edit_problem_1.html',msg=msg,problem=problem,tongji=tongji,status=status,page_type='problem',\
            page_title='管理#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class EditProblemHandler2(BaseHandler):

    @gen.coroutine
    def post(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/problems','题目编号错误')
            return
        p=[self.get_argument(s) for s in ['data','std_code','val_code','gen_code','spj_code'] ]
        sql = "UPDATE problems SET data = %s,std_code = %s,val_code = %s,gen_code = %s,spj_code = %s WHERE id = %s"

        try:
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],p[4],prob_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/problem/%d/edit/2'%prob_id,'修改失败，数据库错误')
            raise
        else:
            self.redirect_msg('/problem/%d/edit/2'%prob_id,'修改成功')
        finally:
            cur.close()
            conn.close()

    #编辑评测内容
    @gen.coroutine
    def get(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        msg = self.get_argument('msg',None)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,tp,name,data,std_code,val_code,gen_code,spj_code,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        sql = "SELECT id,author,status,tim_use,mem_use,code_len FROM judge WHERE problem_id = %s ORDER BY id  DESC LIMIT 10"
        yield cur.execute(sql,(prob_id,))
        status = [row for row in cur]
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        tongji=json.loads(problem[8])
        self.render('edit_problem_2.html',msg=msg,problem=problem,tongji=tongji,status=status,page_type='problem',\
            page_title='管理#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class NewProblemHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        p=[self.get_argument(s) for s in ['name','tp','author','visible','invitecode'] ]
        if p[4] != 'addproblem':
            self.redirect_msg('/problem/new','邀请码错误')
            return
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "INSERT INTO problems (name,tp,author,visible,ac_num,submit_num,gen_date,content,tongji) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],0,0,datetime.now(),conf.DEFAULT_CONTENT,json.dumps([0]*7)))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/problem/new','数据库错误')
            raise
        else:
            sql = "SELECT id FROM problems ORDER BY id DESC LIMIT 1"
            yield cur.execute(sql)
            p=cur.fetchone()
            self.redirect_msg('/problem/%d/edit/0'%p[0],'添加题目成功')
        finally:
            cur.close()
            conn.close()

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        self.render('new_problem.html',msg=msg,page_type='problem',page_title='新题目 -XOJ')


class StatusHandler(BaseHandler):

    @gen.coroutine
    def get(self,prob_id):
        prob_id=int(prob_id)
        if prob_id < 1 :
            self.redirect_msg('/problems','题目编号错误')
            return
        prob_id=norm_page(prob_id)
        msg = self.get_argument('msg',None)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,tp,name,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        sql = "SELECT id,author,status,tim_use,mem_use,lang,code_len,submit_date FROM judge WHERE problem_id = %s ORDER BY tim_use  LIMIT 10"
        yield cur.execute(sql,(prob_id,))
        fast = [row for row in cur]
        sql = "SELECT id,author,status,tim_use,mem_use,lang,code_len,submit_date FROM judge WHERE problem_id = %s ORDER BY code_len  LIMIT 10"
        yield cur.execute(sql,(prob_id,))
        short = [row for row in cur]
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        tongji=json.loads(problem[3])
        self.render('problem_status.html',msg=msg,problem=problem,tongji=tongji,page_type='problem',\
            fast=fast,short=short,page_title='统计#'+str(problem[0])+'. '+problem[2]+' -XOJ')
