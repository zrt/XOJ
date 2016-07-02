from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql
import urllib.parse
from urllib.parse import urljoin,urlencode
import json
import random
import time

class StatusHandler(BaseHandler):

    @web.authenticated
    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)
        user = self.get_argument('user',None)
        problem = self.get_argument('problem',None)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #visible
        sql = "SELECT id,problem_id,problem_name,author,status,\
        tim_use,mem_use,submit_date FROM judge WHERE id >0 "

        param = [] #visible
        if user:
            sql+=" AND author=%s "
            param.append(user)
        if problem:
            sql+=" AND problem_id = %s "
            param.append(problem)
        sql+="ORDER BY id DESC LIMIT %s,%s"
        param.append((page_now-1)*conf.STATUS_PER_PAGE)
        param.append(conf.STATUS_PER_PAGE)
        yield cur.execute(sql,tuple(param))
        records = [row for row in cur]
        cur.close()
        conn.close()
        
        url=urljoin('/status','?'+urlencode({'user':user or '','problem':problem or ''}))

        pages=gen_pages(url,page_now)
        self.render('status.html',msg=msg,records=records,pages=pages,\
            page_type='status',page_title='状态 -XOJ')

class InfoHandler(BaseHandler):

    @web.authenticated
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
        lang,code_len,submit_date,result,visible FROM judge WHERE id = %s"


        yield cur.execute(sql,(judge_id,))
        info = cur.fetchone()
        cur.close()
        conn.close()
        if info == None :
            self.redirect_msg('/status','评测记录未找到')
            return
        user = self.current_user
        auth = self.auth()

        if info[1].encode('utf-8') != self.current_user and auth < info[12]:
            self.redirect_msg('/status','权限不足')
            return
        #if self.current_user != info[1].encode('utf-8') and self.current_user != 'zrt'.encode('utf-8') and self.current_user != 'sys'.encode('utf-8'):
         #   self.redirect_msg('/status','权限不足')
          #  return
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

    @web.authenticated
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
        sql = "SELECT id,name,spj_code,data,mem_limit,tim_limit,visible,author FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/problems','题目编号错误')
            return
        user = self.current_user
        auth = self.auth()

        if problem[7].encode('utf-8') != self.current_user and auth < problem[6]:
            self.redirect_msg('/problems','权限不足')
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
        judger_callback = urljoin(conf.MYURL,'/judger-callback')
        judger_url=random.choice(conf.JUDGER)
        judge_content=json.dumps({'id':judge_id,'prob_id':prob_id,'code':code,\
            'data':problem[3],'spj':problem[2],'lang':lang,\
            'mem_limit':problem[4],'tim_limit':problem[5],'callback':judger_callback,'tim':int(time.time())})
        body_content=urllib.parse.urlencode({'content':judge_content,'key':calc_md5(judge_content,conf.JUDGER_KEY)})
        url = judger_url+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        self.upd(user,problem[0])
        http_client.fetch(url,self.submit_callback)

    @web.authenticated
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
        sql = "SELECT id,tp,name,author,visible FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        user = self.current_user
        auth = self.auth()

        if problem[3].encode('utf-8') != self.current_user and auth < problem[4]:
            self.redirect_msg('/status','权限不足')
            return
        self.render('submit.html',msg=msg,problem=problem,page_type='problem',\
            page_title='提交#'+str(problem[0])+'. '+problem[2]+' -XOJ')
