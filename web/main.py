from tornado import httpserver,ioloop,web,gen,httpclient
import tcelery
import tasks
from base_handler import BaseHandler
from tools import *
import user_handler
import problem_handler
import contest_handler
import judge_handler
import post_handler
import rank_handler

tcelery.setup_nonblocking_producer()


class MainHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('index.html',msg=msg,page_title='XOJ',page_type='index')

class TestHandler(BaseHandler):

    def get(self):
        self.render('test.html',msg=None,page_title='测试页 -XOJ',page_type='test')
        

if __name__ == '__main__':

    settings={
        'cookie_secret': conf.COOKIESECRET,
        'template_path':'./templates',
        'static_path':'./static',
        'debug':True,
        'login_url':'/login',
        'xsrf_cookies':True,
    }

    application = web.Application(handlers=[
        (r'/',MainHandler),
        (r'/login',user_handler.LoginHandler),
        (r'/logout',user_handler.LogoutHandler),
        (r'/register',user_handler.RegisterHandler),
        (r'/test',TestHandler),
        (r'/problems',problem_handler.ProblemsHandler),
        (r'/contests',contest_handler.ContestsHandler),
        (r'/status',judge_handler.StatusHandler),
        (r'/posts',post_handler.PostsHandler),
        (r'/rank',rank_handler.RankHandler),
        (r'/notice',post_handler.NoticeHandler),
        (r'/user/([a-zA-Z][0-9a-zA-Z\-]{0,19})',user_handler.ShowUserHandler),
        (r'/problem/(\d+)',problem_handler.ProblemHandler),
        (r'/contest/(\d+)',contest_handler.ContestHandler),
        (r'/status/(\d+)',judge_handler.InfoHandler),
        (r'/problem/(\d+)/edit/0',problem_handler.EditProblemHandler0),
        (r'/problem/(\d+)/edit/1',problem_handler.EditProblemHandler1),
        (r'/problem/(\d+)/edit/2',problem_handler.EditProblemHandler2),
        (r'/problem/(\d+)/submit',judge_handler.SubmitHandler),
        (r'/problem/(\d+)/status',problem_handler.StatusHandler),
        (r'/problem/new',problem_handler.NewProblemHandler),
        (r'/user/([a-zA-Z][0-9a-zA-Z\-]{0,19})/edit/0',user_handler.EditHandler0),
        (r'/user/([a-zA-Z][0-9a-zA-Z\-]{0,19})/edit/1',user_handler.EditHandler1),
    ],**settings)

    application.listen(5000)
    ioloop.IOLoop.instance().start()
