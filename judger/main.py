from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import judge_handler
import tcelery
import tasks

tcelery.setup_nonblocking_producer()

if __name__ == "__main__":
    settings={
        'debug':True,
    }
    application = web.Application(handlers=[
        (r'/judger',judge_handler.JudgeHandler),
    ],**settings)

    application.listen(8088)
    ioloop.IOLoop.instance().start()
