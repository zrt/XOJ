from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

class ContestsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')

        cur = conn.cursor()
        sql = "SELECT id,name,begin_date,author,content FROM contests LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.CONTESTS_PER_PAGE,conf.CONTESTS_PER_PAGE))
        contests = [row for row in cur]
        cur.close()
        conn.close()
        
        pages=gen_pages('\contests',page_now)
        self.render('contests.html',msg=msg,contests=contests,\
            page_type='contest',page_title='比赛 -XOJ',pages=pages)

class ContestHandler(BaseHandler):

    def get(self):
        pass