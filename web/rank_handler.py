from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

class RankHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #visible
        sql = "SELECT user,school,motto,ac_num,submit_num,email FROM user ORDER BY ac_num DESC LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.USERS_PER_PAGE,conf.USERS_PER_PAGE))
        users = [[*row,int((row[3]+1)/(row[4]+1)*100)] for row in cur]
        cur.close()
        conn.close()

        url='/rank'

        pages=gen_pages(url,page_now)
        self.render('rank.html',msg=msg,users=users,pages=pages,\
            page_type='user',page_title='用户排名 -XOJ',num_from=(page_now-1)*conf.USERS_PER_PAGE)
