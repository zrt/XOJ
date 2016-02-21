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
        page_num = int(self.get_argument('page','1'))
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME)
        cur = conn.cursor()
        sql = "SELECT id,name,ac_num,submit_num FROM problems"
        yield cur.execute(sql)
        problems = [[*row,int(row[2]/row[3]*100)] for row in cur]
        cur.close()
        conn.close()
        self.render('problems.html',msg=msg,problems=problems,page_num=page_num,\
            page_type='problem',page_title='题库 -XOJ')

class ProblemHandler(BaseHandler):

    def get(self):
        pass