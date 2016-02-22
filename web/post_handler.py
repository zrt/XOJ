from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

class PostsHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('posts.html',msg=msg,page_title='讨论 -XOJ',page_type='post')

class NoticeHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('notice.html',msg=msg,page_title='公告 -XOJ',page_type='notice')