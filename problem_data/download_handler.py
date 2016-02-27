from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import time
import json
import os

class DownHandler(BaseHandler):

    def get(self):
        prob_id = self.get_argument('prob')
        tim = self.get_argument('tim')
        name = self.get_argument('name')
        key = self.get_argument('key')
        if calc_md5(prob_id+tim+name,conf.DOWNLOAD_KEY) != key :
            self.set_status(400)
            return
        tim = int(tim)
        tim_now =int(time.time())
        if tim >tim_now+20 or tim < tim_now-20:
            self.set_status(400)
            return
        path = os.path.join('./data/',prob_id+'/'+name)
        with open(path,'rb') as f:
            self.set_header('Content-Type','application/octet-stream')
            self.write(f.read())

