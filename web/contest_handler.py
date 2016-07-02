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
import pymysql
import time

class ContestsHandler(BaseHandler):

    @web.authenticated
    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        #auth
        user=self.current_user
        auth = self.auth()

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')

        cur = conn.cursor()
        sql = "SELECT id,name,begin_date,author,info,visible FROM contests ORDER BY id DESC LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.CONTESTS_PER_PAGE,conf.CONTESTS_PER_PAGE))
        contests = []
        for row in cur:
            if auth>=row[5] or row[3].encode('utf-8')==user:
                contests.append(row)
        cur.close()
        conn.close()
        pages=gen_pages('\contests',page_now)
        self.render('contests.html',msg=msg,contests=contests,\
            page_type='contest',page_title='比赛 -XOJ',pages=pages)

class EditContestHandler(BaseHandler):

    @web.authenticated
    @gen.coroutine
    def post(self,contest_id):
        contest_id=int(contest_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        user=self.current_user
        auth = self.auth()

        sql = "SELECT id,author FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return
        if contest[1].encode('utf-8')!=user and auth < 250:
            self.redirect_msg('/contests','权限不足')
            return

        p=[self.get_argument(s) for s in ['name','info','content','problems','begin_date','end_date','author','visible','status'] ]
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "UPDATE contests SET name=%s,info=%s,content=%s,problems=%s,begin_date=%s,end_date=%s,author=%s,visible=%s,status=%s WHERE id = %s"
        try:
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],contest_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/contest/%d/edit'%contest_id,'数据库错误')
        else:
            self.redirect_msg('/contest/%d/edit'%contest_id,'编辑比赛成功')
        finally:
            cur.close()
            conn.close()

    #管理比赛
    @web.authenticated
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

        sql = "SELECT id,name,author,begin_date,end_date,status,content,problems,info,visible FROM contests WHERE id = %s"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        cur.close()
        conn.close()
        if contest == None:
            self.redirect_msg('/contests','比赛编号错误')
            return
        user=self.current_user
        auth = self.auth()

        if contest[2].encode('utf-8')!=user and auth < 250:
            self.redirect_msg('/contests','权限不足')
            return

        self.render('contest_edit.html',msg=msg,contest=contest,\
            page_type='contest',page_title='编辑比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')


class ContestStatusHandler(BaseHandler):#TODO
    pass

class ContestProblemStatusHandler(BaseHandler):#TODO
    pass




class ContestProblemHandler(BaseHandler):#TODO

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

        sql = "SELECT id,problems,visible,author,begin_date FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        
        user=self.current_user
        auth = self.auth()

        
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        if contest[3].encode('utf-8')!=user and auth < contest[2]:
            self.redirect_msg('/contests','权限不足')
            return

        if datetime.now() < contest[4]:
            self.redirect_msg('/contests','权限不足')
            return

        problems=json.loads(contest[1])
        if prob_id < 0 or prob_id >= len(problems):
            self.redirect_msg('/problems','题目编号错误')
            return
        contest_prob_id=prob_id
        prob_id=problems[prob_id]

        sql = "SELECT id,tp,name,content,tim_limit,mem_limit,author,ac_num,submit_num FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        problem = cur.fetchone()
        problem=[r for r in problem]
        cur.close()
        conn.close()
        if problem == None :
            self.redirect_msg('/problems','题目编号错误')
            return
        problem[0]=contest_prob_id
        self.render('contest_problem.html',msg=msg,problem=problem,contest_id=contest_id,page_type='contest',\
            page_title='比赛题目# '+problem[2]+' -XOJ')


class ContestRankHandler(BaseHandler):# TODO


    
    @web.authenticated
    @gen.coroutine
    def post(self,contest_id):
        #重测所有记录并修改result
        #首先result清零
        contest_id=int(contest_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        
        
        conn = pymysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,problems,result,end_date,author FROM contests WHERE id = %s LIMIT 1"
        cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user=self.current_user
        auth = self.auth()

        if contest[4].encode('utf-8')!=user and auth < 250:
            self.redirect_msg('/contests','权限不足')
            return

        problems=json.loads(contest[1])
        result=json.loads(contest[2])
        
        prob_num=len(problems)
        user_num=len(result)

        for i in range(user_num):
            result[i][1]=result[i][2]=0
            for j in range(prob_num):
                result[i][3][j][0]=result[i][3][j][1]=result[i][3][j][2]=0

        sql = "UPDATE contests SET result=%s WHERE id = %s"

        cur.execute(sql,(json.dumps(result),contest_id))
        conn.commit()

        for i in range(prob_num):
            prob_id=problems[i]
            sql = "SELECT id,name,spj_code,data,mem_limit,tim_limit FROM problems WHERE id = %s LIMIT 1"
            cur.execute(sql,(prob_id,))
            problem = cur.fetchone()

            sql = "SELECT id,code,problem_id,lang,author FROM judge WHERE problem_id = %s"
            cur.execute(sql,(-(contest_id*100+i),))
            judges = [row for row in cur]

            sql = "SELECT id,result FROM contests WHERE id = %s LIMIT 1"
            cur.execute(sql,(contest_id,))
            contest=cur.fetchone()
            result = json.loads(contest[1])

            for row in judges:
                #get result
                for j in range(len(result)):
                    if result[j][0] == row[4]:
                        result[j][3][i][1]+=1

            result=json.dumps(result)
            sql = "UPDATE contests SET result=%s WHERE id = %s"
            cur.execute(sql,(result,contest_id))
            conn.commit()

            for row in judges:
                sql = "UPDATE judge SET status = %s, mem_use = %s,tim_use = %s, result= %s WHERE id = %s"
                cur.execute(sql,(1,0,0,'重测于'+str(datetime.now()),row[0]))
                conn.commit()

                judger_callback = urljoin(conf.MYURL,'/contest-callback')
                judger_url=random.choice(conf.JUDGER)
                judge_content=json.dumps({'id':row[0],'prob_id':prob_id,'code':row[1],\
                    'data':problem[3],'spj':problem[2],'lang':row[3],\
                    'mem_limit':problem[4],'tim_limit':problem[5],'callback':judger_callback,'tim':int(time.time())})
                body_content=urllib.parse.urlencode({'content':judge_content,'key':calc_md5(judge_content,conf.JUDGER_KEY)})
                url = judger_url+'?'+body_content
                http_client = httpclient.AsyncHTTPClient()
                http_client.fetch(url)


        
        self.redirect_msg('/status','正在重测')
        

    @web.authenticated
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

        sql = "SELECT problems,result,author,visible FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user=self.current_user
        auth = self.auth()

        if contest[2].encode('utf-8')!=user and auth < contest[3]:
            self.redirect_msg('/contests','权限不足')
            return

        problems=json.loads(contest[0])
        result=json.loads(contest[1])
        # 用户名 过题数 罚时 题目[是否通过，提交次数，罚时]
        p=[]
        sql="SELECT id,name FROM problems WHERE id = %s"
        for i in range(len(problems)):
            yield cur.execute(sql,(problems[i]))
            name=cur.fetchone()[1]
            p.append(name)

        cur.close()
        conn.close()

        OI=self.get_argument('OI',None)

        if OI:
            for i in range(len(result)):
                result[i][1]=0
                for j in range(len(result[i][3])):
                    result[i][1]+=result[i][3][j][2]
        result=sorted(result,key = lambda x: -x[1]*1000000+x[2])

        if OI:
            s='_oi'
        else:
            s=''
        self.render('contest_rank%s.html'%s,msg=msg,problems=p,result=result,contest_id=contest_id,\
            page_type='contest',page_title='排名版#'+str(contest_id)+' -XOJ')


#[user_name,AC数,总罚时,[[是否AC,提交次数,该题罚时],[],[]]],[],[],[],[]
class ContestPrepareHandler(BaseHandler):#TODO
    
    @web.authenticated
    @gen.coroutine
    def get(self,contest_id):
        contest_id=int(contest_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,problems,author FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        problems=json.loads(contest[1])
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user=self.current_user
        auth = self.auth()

        if contest[2].encode('utf-8')!=user and auth < 250:
            self.redirect_msg('/contests','权限不足')
            return

        sql = "SELECT id,user FROM join_contest WHERE contest_id = %s"
        yield cur.execute(sql,(contest_id,))
        register=[row for row in cur]
        
        result=[[r[1],0,0,[[0,0,0] for p in problems ]] for r in register]

        result=json.dumps(result)
        sql = "UPDATE contests SET result=%s,status=%s WHERE id = %s"

        try:
            yield cur.execute(sql,(result,2,contest_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/contest/%d'%contest_id,'数据库错误')
        else:
            self.redirect_msg('/contest/%d'%contest_id,'已停止报名')
        finally:
            cur.close()
            conn.close()



#负数代表比赛题目
class ContestHandler(BaseHandler):

    @web.authenticated
    @gen.coroutine
    def post(self,contest_id):
        contest_id=int(contest_id)
        if contest_id < 1 :
            self.redirect_msg('/contests','比赛编号错误')
            return
        contest_id=norm_page(contest_id)
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT id,author,visible FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        if contest == None:
            cur.close()
            conn.close()
            self.redirect_msg('/contests','比赛编号错误')
            return

        user=self.current_user
        auth = self.auth()

        if contest[1].encode('utf-8')!=user and auth < contest[2]:
            self.redirect_msg('/contests','权限不足')
            return

        sql = "SELECT id FROM join_contest WHERE user=%s AND contest_id=%s"

        yield cur.execute(sql,(self.current_user,contest_id,))
        contest=cur.fetchone()
        if contest != None:
            cur.close()
            conn.close()
            self.redirect_msg('/contest/%d'%contest_id,'您已报名，不要重复报名')
            return
        sql = "INSERT INTO join_contest  (user,contest_id,gen_date,data) VALUES (%s,%s,%s,%s)"
        try:
            yield cur.execute(sql,(self.current_user,contest_id,datetime.now(),''))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/contest/%d'%contest_id,'报名失败')
            raise
        else:
            self.redirect_msg('/contest/%d'%contest_id,'报名成功')
        finally:
            cur.close()
            conn.close()

    @web.authenticated
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

        sql = "SELECT id,name,author,begin_date,end_date,status,content,problems,result,visible FROM contests WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(contest_id,))
        contest=cur.fetchone()
        cur.close()
        conn.close()
        if contest == None:
            self.redirect_msg('/contests','比赛编号错误')
            return

        user=self.current_user
        auth = self.auth()

        if contest[2].encode('utf-8')!=user and auth < contest[9]:
            self.redirect_msg('/contests','权限不足')
            return

        if contest[5] == 1:
            conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
            cur = conn.cursor()

            sql = "SELECT id,user,gen_date FROM join_contest WHERE contest_id = %s"
            yield cur.execute(sql,(contest_id,))
            register=[row for row in cur]
            cur.close()
            conn.close()

            self.render('contest_register.html',msg=msg,contest=contest,now=datetime.now(),register=register,\
                page_type='contest',page_title='比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')
            return
        elif contest[5] == 2 and datetime.now()<contest[3]:
            conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
            cur = conn.cursor()

            sql = "SELECT id,user,gen_date FROM join_contest WHERE contest_id = %s"
            yield cur.execute(sql,(contest_id,))
            register=[row for row in cur]
            cur.close()
            conn.close()

            self.render('contest_wait.html',msg=msg,contest=contest,now=datetime.now(),register=register,\
                page_type='contest',page_title='比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')
            return
        elif contest[5]==2 and datetime.now()<contest[4]:
            problems=json.loads(contest[7])
            conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
            cur = conn.cursor()

            p=[]
            sql="SELECT id,name FROM problems WHERE id = %s"
            for i in range(len(problems)):
                yield cur.execute(sql,(problems[i]))
                name=cur.fetchone()[1]
                p.append([name,0,0])
            result=json.loads(contest[8])
            for i in range(len(result)):
                for j in range(len(problems)):
                    p[j][1]+=result[i][3][j][0]
                    p[j][2]+=result[i][3][j][1]
            self.render('contest.html',msg=msg,contest=contest,problems=p,now=datetime.now(),\
            page_type='contest',page_title='比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')
        else:
            problems=json.loads(contest[7])
            conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
            cur = conn.cursor()

            p=[]
            sql="SELECT id,name FROM problems WHERE id = %s"
            for i in range(len(problems)):
                yield cur.execute(sql,(problems[i]))
                name=cur.fetchone()[1]
                p.append([name,0,0])
            result=json.loads(contest[8])
            for i in range(len(result)):
                for j in range(len(problems)):
                    p[j][1]+=result[i][3][j][0]
                    p[j][2]+=result[i][3][j][1]
            self.render('contest_over.html',msg=msg,contest=contest,problems=p,now=datetime.now(),\
            page_type='contest',page_title='比赛#'+str(contest[0])+'. '+contest[1]+' -XOJ')





#[user_name,AC数,总罚时,[[是否AC,提交次数,该题罚时],[],[]]],[],[],[],[]
#status 添加成功是1，准备开始是2

class NewContestHandler(BaseHandler):

    @web.authenticated
    @gen.coroutine
    def post(self):
        p=[self.get_argument(s) for s in ['name','info','content','problems','begin_date','end_date','author','visible','invitecode'] ]
        if p[-1] != 'addcontest':
            self.redirect_msg('/contest/new','邀请码错误')
            return
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        auth = self.auth()

        if  auth < 25:
            self.redirect_msg('/contests','权限不足')
            return

        sql = "INSERT INTO contests (name,info,content,problems,begin_date,end_date,author,visible,gen_date,status,result) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            yield cur.execute(sql,(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],datetime.now(),1,''))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/contest/new','数据库错误')
        else:
            sql = "SELECT id FROM contests ORDER BY id DESC LIMIT 1"
            yield cur.execute(sql)
            p=cur.fetchone()
            self.redirect_msg('/contest/%d/edit'%p[0],'添加比赛成功')
        finally:
            cur.close()
            conn.close()

    @web.authenticated
    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        auth = self.auth()

        if  auth < 25:
            self.redirect_msg('/contests','权限不足')
            return
        self.render('new_contest.html',msg=msg,page_type='contest',page_title='新建比赛 -XOJ')

