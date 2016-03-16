from tornado import httpserver,ioloop,web,gen,httpclient
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
        sql = "SELECT id,name,begin_date,author,content FROM contests ORDER BY id DESC LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.CONTESTS_PER_PAGE,conf.CONTESTS_PER_PAGE))
        contests = [row for row in cur]
        cur.close()
        conn.close()
        
        pages=gen_pages('\contests',page_now)
        self.render('contests.html',msg=msg,contests=contests,\
            page_type='contest',page_title='比赛 -XOJ',pages=pages)

class ContestHandler(BaseHandler):

    @gen.coroutine
    def get(self,contest_id):
        contest_id=int(contest_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,name,author,begin_date,end_date,status,content,problems FROM contests WHERE id = %s"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        cur.close()
        conn.close()
        if contest == None:
            self.redirect_msg('/contests','比赛编号错误')
            return
        self.render('contest.html',msg=msg,contest=contest,\
            page_type='contest',page_title='比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')


class NewContestHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('new_contest.html',msg=msg,page_type='contest',page_title='新建比赛 -XOJ')