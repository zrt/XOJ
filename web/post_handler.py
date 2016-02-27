from tornado import httpserver,ioloop,web,gen,httpclient
from datetime import datetime
from base_handler import BaseHandler
from tools import *
import conf
import tornado_mysql

class PostsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        msg = self.get_argument('msg',None)
        page_now = int(self.get_argument('page','1'))
        page_now=norm_page(page_now)

        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #visible
        sql = "SELECT id,name,author,gen_date FROM posts ORDER BY id DESC LIMIT %s,%s"
        yield cur.execute(sql,((page_now-1)*conf.POSTS_PER_PAGE,conf.POSTS_PER_PAGE))
        posts = [row for row in cur]
        cur.close()
        conn.close()
        
        url='/posts'

        pages=gen_pages(url,page_now)
        self.render('posts.html',msg=msg,posts=posts,pages=pages,\
            page_type='post',page_title='讨论 -XOJ')

class NewPostHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        p=[self.get_argument(s) for s in ['name','content','invitecode'] ]
        if p[2] != 'addpost':
            self.redirect_msg('/post/new','邀请码错误')
            return
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()

        sql = "INSERT INTO posts (name,author,content,gen_date,modify_date) VALUES (%s,%s,%s,%s,%s)"
        try:
            yield cur.execute(sql,(p[0],self.current_user,p[1],datetime.now(),datetime.now()))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/post/new','数据库错误')
            raise
        else:
            sql = "SELECT id FROM posts ORDER BY id DESC LIMIT 1"
            yield cur.execute(sql)
            p=cur.fetchone()
            self.redirect_msg('/post/%d'%p[0],'发布文章成功')
        finally:
            cur.close()
            conn.close()

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('new_post.html',msg=msg,page_type='post',page_title='新文章 -XOJ')


class PostHandler(BaseHandler):

    @gen.coroutine
    def get(self,post_id):
        post_id=int(post_id)
        if post_id < 1 :
            self.redirect_msg('/posts','文章编号错误')
            return
        post_id=norm_page(post_id)
        msg = self.get_argument('msg',None)
        
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT id,name,author,content,gen_date,modify_date FROM posts WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(post_id,))
        post = cur.fetchone()
        cur.close()
        conn.close()
        if post == None :
            self.redirect_msg('/posts','题目编号错误')
            return
        self.render('post.html',msg=msg,post=post,page_type='post',\
            page_title='文章:'+post[1]+' -XOJ')

class EditHandler(BaseHandler):

    @gen.coroutine
    def get(self,post_id):
        post_id=int(post_id)
        if post_id < 1 :
            self.redirect_msg('/posts','文章编号错误')
            return
        post_id=norm_page(post_id)
        msg = self.get_argument('msg',None)
        
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        #
        sql = "SELECT name,content FROM posts WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(post_id,))
        post = cur.fetchone()
        cur.close()
        conn.close()
        if post == None :
            self.redirect_msg('/posts','题目编号错误')
            return
        self.render('edit_post.html',msg=msg,post=post,page_type='post',\
            page_title='修改文章:'+post[0]+' -XOJ')

    @gen.coroutine
    def post(self,post_id):
        post_id=int(post_id)
        if post_id < 1 :
            self.redirect_msg('/posts','文章编号错误')
            return
        post_id=norm_page(post_id)
        msg = self.get_argument('msg',None)
        
        conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
        cur = conn.cursor()
        sql = "SELECT id FROM posts WHERE id = %s LIMIT 1"
        yield cur.execute(sql,(post_id,))
        post = cur.fetchone()

        if post == None :
            cur.close()
            conn.close()
            self.redirect_msg('/posts','题目编号错误')
            return

        p=[self.get_argument(s) for s in ['name','content'] ]
        
        sql = "UPDATE posts SET name = %s ,content = %s ,modify_date = %s WHERE id = %s"
        try:
            yield cur.execute(sql,(p[0],p[1],datetime.now(),post_id))
            yield conn.commit()
        except BaseException as e:
            self.redirect_msg('/post/%d/edit'%post_id,'数据库错误')
            raise
        else:
            self.redirect_msg('/post/%d'%post_id,'修改成功')
        finally:
            cur.close()
            conn.close()


class NoticeHandler(BaseHandler):

    def get(self):
        msg = self.get_argument('msg',None)
        self.render('notice.html',msg=msg,page_title='公告 -XOJ',page_type='notice')
