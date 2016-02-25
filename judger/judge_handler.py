from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import json
import urllib.parse
import tcelery
import tasks

class JudgeHandler(BaseHandler):
    

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
        content = json.loads(content)
        #{'id':,'code':,'data':,'spj':,'lang':,'mem_limit':,'tim_limit':,'callback':}

        # callback: id,status,mem_use,tim_use,result(ADD形式) & key
        
        callback = {'id':content['id'],'status':2,'mem_use':0,'tim_use':0,'result':''}
        callback['result'] = '####评测机收到评测请求，正在准备评测...'

        json_callback=json.dumps(callback)
        body_content = urllib.parse.urlencode({'content':json_callback,'key':calc_md5(json_callback,conf.JUDGER_KEY)})
        url = content['callback']+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url)


        r = yield gen.Task(tasks.prepare.apply_async,args=[content['id'],content['data'],content['spj']])
        r = r.result

        if r[0] == 1:
            callback['result'] = '####评测机准备完毕,开始编译程序...\n'+r[1]
        else:
            callback['status'] = 9
            callback['result'] = '####评测机准备失败...\n'+r[1]

        json_callback=json.dumps(callback)
        body_content = urllib.parse.urlencode({'content':json_callback,'key':calc_md5(json_callback,conf.JUDGER_KEY)})
        url = content['callback']+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url)

        if callback['status'] != 2:
            return

        r = yield gen.Task(tasks.compile.apply_async,args=[content['id'],content['lang'],content['code']])
        r = r.result

        if r[0] == 1:
            callback['result'] = '####编译成功,开始评测...\n'+r[1]
        else:
            callback['status'] = 8
            callback['result'] = '####编译失败...\n'+r[1]

        json_callback=json.dumps(callback)
        body_content = urllib.parse.urlencode({'content':json_callback,'key':calc_md5(json_callback,conf.JUDGER_KEY)})
        url = content['callback']+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url)

        if callback['status'] != 2:
            return

        r = yield gen.Task(tasks.judge.apply_async,args=[content['id'],content['mem_limit'],content['tim_limit']])
        r = r.result

        callback['status'] = r[0]
        callback['result'] = r[1]
        callback['mem_use'] = r[2]
        callback['tim_use'] = r[3]

        json_callback=json.dumps(callback)
        body_content = urllib.parse.urlencode({'content':json_callback,'key':calc_md5(json_callback,conf.JUDGER_KEY)})
        url = content['callback']+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url)
        return




