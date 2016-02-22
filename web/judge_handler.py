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
        tim_use,mem_use,submit_date FROM judge LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.STATUS_PER_PAGE,conf.STATUS_PER_PAGE))
        records = [row for row in cur]
        cur.close()
        conn.close()
        
        url='/status'

        pages=gen_pages(url,page_now)
        self.render('status.html',msg=msg,records=records,pages=pages,\
            page_type='status',page_title='状态 -XOJ')

