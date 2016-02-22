from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

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
        problems = [[*row,int((row[2]+1)/(row[3]+1)*100)] for row in cur]
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
        sql = "SELECT id,tp,name,content,tim_limit,mem_limit,author,ac_num,submit_num FROM problems WHERE id = %s"
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
        sql = "SELECT id,tp,name,tim_limit,mem_limit,author,visible,ac_num,submit_num,gen_date FROM problems WHERE id = %s"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        self.render('edit_problem_0.html',msg=msg,problem=problem,page_type='problem',\
            page_title='编辑#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class EditProblemHandler1(BaseHandler):

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
        sql = "SELECT id,tp,name,content,images FROM problems WHERE id = %s"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        self.render('edit_problem_1.html',msg=msg,problem=problem,page_type='problem',\
            page_title='编辑#'+str(problem[0])+'. '+problem[2]+' -XOJ')

class EditProblemHandler2(BaseHandler):

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
        sql = "SELECT id,tp,name,data,std_code,val_code,gen_code,spj_code FROM problems WHERE id = %s"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        self.render('edit_problem_2.html',msg=msg,problem=problem,page_type='problem',\
            page_title='编辑#'+str(problem[0])+'. '+problem[2]+' -XOJ')
