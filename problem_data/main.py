from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import download_handler
import upload_handler

#阻塞IO

if __name__ == "__main__":
    settings={
        'debug':True,
    }
    application = web.Application(handlers=[
        (r'/upload',upload_handler.UpHandler),
        (r'/download',download_handler.DownHandler),
    ],**settings)

    application.listen(5088)
    ioloop.IOLoop.instance().start()
