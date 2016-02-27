from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql
import urllib.parse
from urllib.parse import urljoin
import json
import random
import time

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


#提交时对submit_num,tongji信息进行更改
class SubmitHandler(BaseHandler):

    @gen.coroutine
    def submit_callback(self,response):
        if response.error:
            conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
            cur = conn.cursor()
            sql = "UPDATE judge SET status=%s,result=%s WHERE id = %s LIMIT 1"
            yield cur.execute(sql,(9,'####访问评测机时错误\n'+str(response.error),self.j_id,))
            yield conn.commit()
            cur.close()
            conn.close()

    @gen.coroutine
    def upd(self,user,prob_id):
        #user submit_num+1
        #user tongji[0]+1
        #problems submit_num+1
        #problems tongji[0]+1
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT submit_num,tongji FROM user WHERE user = %s LIMIT 1"
        yield cur.execute(sql,(user,))
        info = cur.fetchone()
        tongji = json.loads(info[1])
        tongji[0]=tongji[0]+1
        sql = "UPDATE user SET submit_num = %s,tongji=%s WHERE user = %s"
        yield cur.execute(sql,(info[0]+1,json.dumps(tongji),user))
        yield conn.commit()

        sql = "SELECT submit_num,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        info = cur.fetchone()
        tongji = json.loads(info[1])
        tongji[0]=tongji[0]+1
        sql = "UPDATE problems SET submit_num = %s,tongji=%s WHERE id = %s"
        yield cur.execute(sql,(info[0]+1,json.dumps(tongji),prob_id))
        yield conn.commit()

        cur.close()
        conn.close()


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
        sql = "SELECT id,name,spj_code,data,mem_limit,tim_limit FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/problems','题目编号错误')
            return
        user = self.current_user
        lang = 1
        code = self.get_argument('code')
        sql = "INSERT INTO judge (author,code,problem_id,problem_name,status,visible,mem_use,\
            tim_use,lang,code_len,submit_date,result) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            yield cur.execute(sql,(user,code,problem[0],problem[1],1,1000,0,0,lang,len(code),datetime.now(),'等待评测..'))
            judge_id=conn.insert_id()
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/problem/%d/submit'%prob_id,'数据库错误')
            raise
            return
        finally:
            cur.close()
            conn.close()
        self.j_id=judge_id
        self.redirect_msg('/status/%d'%judge_id,'提交成功')
        judger_callback = urljoin(conf.MYURL,'/judger-callbck')
        judger_url=random.choice(conf.JUDGER)
        judge_content=json.dumps({'id':judge_id,'code':code,\
            'data':problem[3],'spj':problem[2],'lang':lang,\
            'mem_limit':problem[4],'tim_limit':problem[5],'callback':judger_callback,'tim':int(time.time())})
        body_content=urllib.parse.urlencode({'content':judge_content,'key':calc_md5(judge_content,conf.JUDGER_KEY)})
        url = judger_url+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url,self.submit_callback)
        self.upd(user,problem[0])

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
        sql = "SELECT id,tp,name FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        self.render('submit.html',msg=msg,problem=problem,page_type='problem',\
            page_title='提交#'+str(problem[0])+'. '+problem[2]+' -XOJ')
