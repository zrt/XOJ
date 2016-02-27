from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import json
import time

class CallbackHandler(BaseHandler):
        
    @gen.coroutine
    def get(self):
        content = self.get_argument('content')
        key = self.get_argument('key')
        if key != calc_md5(content,conf.DOWNLOAD_KEY):
            self.set_status(400)
            return
        else:
            self.set_status(200)
            self.finish()
        callback = json.loads(content)

        tim_now = int(time.time())
        if callback['tim'] >tim_now+20 or callback['tim'] <tim_now-20:
            return
        # callback: prob_id,data

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id FROM problems WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(callback['id'],))
        problem = cur.fetchone()

        if problem == None :
            cur.close()
            conn.close()
            return
        sql = "UPDATE problems SET data=%s WHERE id = %s"
        yield cur.execute(sql,(callback['data'],callback['id']))
        yield conn.commit()
        
        cur.close()
        conn.close()


