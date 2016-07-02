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
import re
import pymysql


class CallbackHandler(BaseHandler):
    @gen.coroutine
    def upd(self,callback,submit_date,score):
        conn = pymysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT author,problem_id FROM judge WHERE id = %s"
        cur.execute(sql,(callback['id'],))
        user,prob_id=cur.fetchone()

        
        prob_id=-prob_id
        contest_id = prob_id//100
        prob_id = prob_id % 100
        

        sql = "SELECT id,result,begin_date FROM contests WHERE id = %s"
        cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        result=json.loads(contest[1])

        tim=int((submit_date-contest[2]).total_seconds())//60


        for i in range(len(result)):
            if result[i][0] == user:
                if 3 == callback['status']:
                    if result[i][3][prob_id][0] == 0:
                        result[i][1]+=1
                        result[i][3][prob_id][0]=1
                        result[i][2]+=tim-20+result[i][3][prob_id][1]*20
                result[i][3][prob_id][2]=score
        result=json.dumps(result)

        sql = "UPDATE contests SET result=%s WHERE id = %s"

        cur.execute(sql,(result,contest_id))
        conn.commit()
        cur.close()
        conn.close()


        
    @gen.coroutine
    def get(self):
        content = self.get_argument('content')
        key = self.get_argument('key')
        if key != calc_md5(content,conf.JUDGER_KEY):
            self.set_status(400)
            return
        else:
            self.set_status(200)
            self.finish()
        callback = json.loads(content)

        tim_now = int(time.time())
        if callback['tim'] >tim_now+20 or callback['tim'] <tim_now-20:
            return
        # callback: id,status,mem_use,tim_use,result(ADD形式) & key

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id,result,submit_date FROM judge WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(callback['id'],))
        judge = cur.fetchone()

        if judge == None :
            cur.close()
            conn.close()
            return
        m = re.search(r'\$(\d+)\$',callback['result'])
        if m :
            score=int(m.group(1))
        else:
            score=0

        callback['result']=judge[1]+'\n'+callback['result']
        sql = "UPDATE judge SET status=%s,mem_use=%s,tim_use=%s,result=%s WHERE id = %s"
        yield cur.execute(sql,(callback['status'],callback['mem_use'],callback['tim_use'],callback['result'],callback['id']))
        yield conn.commit()
        
        cur.close()
        conn.close()

        
        self.upd(callback,judge[2],score)



#提交时对result信息进行更改
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

    @web.authenticated
    @gen.coroutine
    def post(self,contest_id,prob_id):

        contest_id=int(contest_id)
        prob_id=int(prob_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        
        
        conn = pymysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,problems,result,end_date,begin_date,visible,author FROM contests WHERE id = %s LIMIT 1"
        cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user = self.current_user
        auth = self.auth()

        if  contest[6].encode('utf-8') != user and auth < contest[5]:
            self.redirect_msg('/contests','权限不足')
            return


        if datetime.now() < contest[4]:
            self.redirect_msg('/contests','权限不足')
            return
        if datetime.now() > contest[3]:
            self.redirect_msg('/contest/%d'%contest_id,'提交时间已过')
            return

        problems=json.loads(contest[1])
        result=json.loads(contest[2])
        if prob_id < 0 or prob_id >= len(problems):
            self.redirect_msg('/contest/%d'%contest_id,'题目编号配置错误')
            return
        contest_prob_id=prob_id
        prob_id=problems[prob_id]

        sql = "SELECT id,user FROM join_contest WHERE contest_id = %s AND user = %s LIMIT 1"
        cur.execute(sql,(contest_id,self.current_user,))
        join_id=cur.fetchone()
        if join_id == None:
            self.redirect_msg('/contest/%d'%contest_id,'你未报名该比赛')
            return

        sql = "SELECT id,name,spj_code,data,mem_limit,tim_limit FROM problems WHERE id = %s LIMIT 1"
        cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        if problem == None :
            cur.close()
            conn.close()
            self.redirect_msg('/contest/%d'%contest_id,'题目编号错误')
            return
        user = self.current_user
        lang = 1
        code = self.get_argument('code')
        sql = "INSERT INTO judge (author,code,problem_id,problem_name,status,visible,mem_use,\
            tim_use,lang,code_len,submit_date,result) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            cur.execute(sql,(user,code,-(contest_id*100+contest_prob_id),problem[1],1,1000,0,0,lang,len(code),datetime.now(),'等待评测..'))
            judge_id=conn.insert_id()
            conn.commit()
        except BaseException as e:
            self.redirect_msg('/contest/%d/%d/submit'%(contest_id,contest_prob_id),'数据库错误')
            raise
            return
        self.j_id=judge_id
        self.redirect_msg('/status/%d'%judge_id,'提交成功')
        judger_callback = urljoin(conf.MYURL,'/contest-callback')
        judger_url=random.choice(conf.JUDGER)
        judge_content=json.dumps({'id':judge_id,'prob_id':prob_id,'code':code,\
            'data':problem[3],'spj':problem[2],'lang':lang,\
            'mem_limit':problem[4],'tim_limit':problem[5],'callback':judger_callback,'tim':int(time.time())})
        body_content=urllib.parse.urlencode({'content':judge_content,'key':calc_md5(judge_content,conf.JUDGER_KEY)})
        url = judger_url+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url,self.submit_callback)
        for i in range(len(result)):
            if result[i][0].encode('utf-8') == self.current_user:
                result[i][3][contest_prob_id][1]+=1
                result[i][3][contest_prob_id][2]+=20
        result=json.dumps(result)

        sql = "UPDATE contests SET result=%s WHERE id = %s"

        cur.execute(sql,(result,contest_id))
        conn.commit()
        cur.close()
        conn.close()

    @web.authenticated
    @gen.coroutine
    def get(self,contest_id,prob_id):
        contest_id=int(contest_id)
        prob_id=int(prob_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        
        msg = self.get_argument('msg',None)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,problems,end_date,begin_date,author,visible FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user = self.current_user
        auth = self.auth()

        if  contest[4].encode('utf-8') != user and auth < contest[5]:
            self.redirect_msg('/contests','权限不足')
            return

        if datetime.now() < contest[3]:
            self.redirect_msg('/contests','权限不足')
            return

        if datetime.now() > contest[2]:
            self.redirect_msg('/contest/%d'%contest_id,'提交时间已过')
            return

        problems=json.loads(contest[1])
        if prob_id < 0 or prob_id >= len(problems):
            self.redirect_msg('/contest/%d'%contest_id,'题目编号配置错误')
            return
        contest_prob_id=prob_id
        prob_id=problems[prob_id]

        sql = "SELECT id,tp,name FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/contest/%d'%contest_id,'题目编号错误')
            return
        self.render('contest_submit.html',msg=msg,problem=problem,page_type='contest',\
            page_title='比赛提交#'+problem[2]+' -XOJ')
