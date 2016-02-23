from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

class StatusHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #visible
        sql = "SELECT id,problem_id,problem_name,author,status,\
        tim_use,mem_use,submit_date FROM judge ORDER BY id DESC LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.STATUS_PER_PAGE,conf.STATUS_PER_PAGE))
        records = [row for row in cur]
        cur.close()
        conn.close()
        
        url='/status'

        pages=gen_pages(url,page_now)
        self.render('status.html',msg=msg,records=records,pages=pages,\
            page_type='status',page_title='状态 -XOJ')

class InfoHandler(BaseHandler):

    @gen.coroutine
    def get(self,judge_id):
        judge_id=int(judge_id)
        if judge_id < 1 :
            self.redirect_msg('/status','评测记录未找到')
            return
        judge_id = norm_page(judge_id)
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,author,code,problem_id,problem_name,status,mem_use,tim_use,\
        lang,code_len,submit_date,result FROM judge WHERE id = %s"
        yield cur.execute(sql,(judge_id,))
        info = cur.fetchone()
        cur.close()
        conn.close()
        if info == None :
            self.redirect_msg('/status','评测记录未找到')
            return
        self.render('status_info.html',msg=msg,info=info,page_type='status',\
            page_title='评测记录 -XOJ')
