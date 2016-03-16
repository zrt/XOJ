from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import json
import time

class CallbackHandler(BaseHandler):
    @gen.coroutine
    def upd(self,callback):
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "SELECT author,problem_id FROM judge WHERE id = %s"
        yield cur.execute(sql,(callback['id'],))
        user,prob_id=cur.fetchone()

        #user ac_num,ac_list,tongji
        #problems ac_num,tongji
        newac=False
        sql = "SELECT ac_num,ac_list,tongji FROM user WHERE user = %s LIMIT 1"
        yield cur.execute(sql,(user,))
        info = cur.fetchone()
        ac_num = info[0]
        ac_list = json.loads(info[1])
        if callback['status'] == 3 and (prob_id not in ac_list):
            ac_list.append(prob_id)
            newac = True
        if callback['status'] == 3 and newac:
            ac_num=ac_num+1
        
        tongji = json.loads(info[2])
        tongji[[0,0,0,1,2,3,5,4,6][callback['status']]]=tongji[[0,0,0,1,2,3,5,4,6][callback['status']]]+1
        sql = "UPDATE user SET ac_num = %s,ac_list = %s,tongji=%s WHERE user = %s"
        yield cur.execute(sql,(ac_num,json.dumps(ac_list),json.dumps(tongji),user))
        yield conn.commit()

        sql = "SELECT ac_num,tongji FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(prob_id,))
        info = cur.fetchone()
        ac_num = info[0]
        if callback['status'] == 3 and newac:
            ac_num=ac_num+1
        tongji = json.loads(info[1])
        tongji[[0,0,0,1,2,3,5,4,6][callback['status']]]=tongji[[0,0,0,1,2,3,5,4,6][callback['status']]]+1
        sql = "UPDATE problems SET ac_num = %s,tongji=%s WHERE id = %s"
        yield cur.execute(sql,(ac_num,json.dumps(tongji),prob_id))
        yield conn.commit()

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
        sql = "SELECT id,result FROM judge WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(callback['id'],))
        judge = cur.fetchone()

        if judge == None :
            cur.close()
            conn.close()
            return
        callback['result']=judge[1]+'\n'+callback['result']
        sql = "UPDATE judge SET status=%s,mem_use=%s,tim_use=%s,result=%s WHERE id = %s"
        yield cur.execute(sql,(callback['status'],callback['mem_use'],callback['tim_use'],callback['result'],callback['id']))
        yield conn.commit()
        
        cur.close()
        conn.close()
        if 3 <= callback['status'] <=8:
            self.upd(callback)

