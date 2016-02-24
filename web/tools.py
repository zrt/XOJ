from tornado import ioloop,gen,escape
from datetime import datetime
import tornado_mysql
import hashlib
import urllib.parse
import conf

def log(s):
    print(str(datetime.now())+' - '+str(s))

def escape(s):
    return  escape.xhtml_escape(s)

def gen_pw(user,pw):
    m = hashlib.md5()
    m.update((user+'XOJ233333333333333- -.#'+pw).encode('utf-8'))
    return m.hexdigest()

def calc_md5(a,b):
    m = hashlib.md5()
    m.update((a+b).encode('utf-8'))
    return m.hexdigest()

def add_param(url,a,b):
    params = {a:b}
    url_parts = list(urllib.parse.urlparse(url))
    query = dict(url_parts[4])
    query.update(params)
    url_parts[4] = urllib.parse.urlencode(query)
    url = urllib.parse.urlunparse(url_parts)
    return url

def norm_page(page_now):
    if page_now < 1:
        page_now=1
    if page_now > 10000000:
        page_now=10000000
    return page_now

def gen_pages(url,now):
    fanye=[1,1,add_param(url,'page',now-1),add_param(url,'page',now+1)]
    if now == 1:
        fanye[0]=0
    pages=[]
    for i in range(max(1,now-3),now):
        pages.append([i,add_param(url,'page',i),0])
    pages.append([now,add_param(url,'page',now),1])
    for i in range(now+1,now+4):
        pages.append([i,add_param(url,'page',i),0])
    return [fanye,pages]

def get_pic(email,siz):
    url = 'http://cn.gravatar.com/avatar/'+ hashlib.md5(email.lower().encode('utf-8')).hexdigest()+'?'
    url += urllib.parse.urlencode({'d':'mm','s':str(siz)})
    return url

@gen.coroutine
def CREATE_DATABASE_func():
    'CREATE DATABASE xojdb DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;'
    conn = yield tornado_mysql.connect(host=conf.DBHOST,\
            port=conf.DBPORT,user=conf.DBUSER,passwd=conf.DBPW,db=conf.DBNAME,charset='utf8')
    cur = conn.cursor()
    print('create user table...')
    yield cur.execute('create table user(\
        user varchar(22) NOT NULL PRIMARY KEY,\
        password varchar(32),\
        email varchar(52),\
        school varchar(22),\
        motto varchar(52),\
        admin int,\
        ac_num int,\
        submit_num int,\
        gen_date datetime,\
        msg_num int,\
        tongji text,\
        ac_list text,\
        UNIQUE(user))')
    print('create friend table...')
    yield cur.execute('create table friend(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        user1 varchar(22),\
        user2 varchar(22),\
        gen_date datetime,\
        dead_date datetime\
        )')
    print('create problems table...')
    yield cur.execute('create table problems(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        tp int,\
        name varchar(22),\
        content text,\
        data text,\
        images text,\
        visible int,\
        std_code text,\
        val_code text,\
        gen_code text,\
        spj_code text,\
        mem_limit int,\
        tim_limit int,\
        author varchar(22),\
        ac_num int,\
        submit_num int,\
        gen_date datetime,\
        tongji text\
        )')
    print('create problem_tags table...')
    yield cur.execute('create table problem_tags(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        tagname varchar(22),\
        problem_id int,\
        problem_name varchar(22)\
        )')
    print('create judge table...')
    yield cur.execute('create table judge(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        author varchar(22),\
        code text,\
        problem_id int,\
        problem_name varchar(22),\
        status int,\
        visible int,\
        mem_use int,\
        tim_use int,\
        lang int,\
        code_len int,\
        submit_date datetime,\
        result text\
        )')
    print('create contests table...')
    yield cur.execute('create table contests(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        name varchar(22),\
        author varchar(22),\
        problems text,\
        gen_date datetime,\
        begin_date datetime,\
        end_date datetime,\
        visible int,\
        status int,\
        content text,\
        result text,\
        images text\
        )')
    print('create join_contest table...')
    yield cur.execute('create table join_contest(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        user varchar(22),\
        contest_id int,\
        gen_date datetime,\
        data text\
        )')
    print('create posts table...')
    yield cur.execute('create table posts(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        name varchar(22),\
        author varchar(22),\
        problem_id int,\
        problem_name varchar(22),\
        contest_id int,\
        contest_name varchar(22),\
        content text,\
        modify_date datetime,\
        gen_date datetime\
        )')
    print('create post_tags table...')
    yield cur.execute('create table post_tags(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        tagname varchar(22),\
        post_id int,\
        post_name varchar(22)\
        )')
    print('create post_comments table...')
    yield cur.execute('create table post_comments(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        author varchar(22),\
        post_id int,\
        content text,\
        gen_date datetime\
        )')
    print('create msg table...')
    yield cur.execute('create table msg(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        send_user varchar(22),\
        to_user varchar(22),\
        see int,\
        gen_date datetime,\
        content text\
        )')
    print('create invitecode table...')
    yield cur.execute('create table invitecode(\
        id int NOT NULL AUTO_INCREMENT PRIMARY KEY,\
        code varchar(22),\
        times int,\
        tp int,\
        gen_date datetime,\
        gen_user varchar(22),\
        use_date datetime,\
        content text\
        )')
    conn.commit()
    '''
    CREATE UNIQUE INDEX index_name
    ON table_name (column_name)
    '''

    'AUTO_INCREMENT '
    # conn.commit()
    cur.close()
    conn.close()


def CREATE_DATABASE():
    ioloop.IOLoop.current().run_sync(CREATE_DATABASE_func)