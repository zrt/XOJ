from celery import Celery
import pymysql.cursors
import re
from tools import *
import time
import json
import conf
backend = 'amqp'
broker = 'amqp://'

app = Celery('tasks',backend=backend,broker=broker)

'celery -A tasks worker --loglevel=info --pool=solo'

user_rule=r'^[a-zA-Z][0-9a-zA-Z\-]{0,19}$'
email_rule=r'^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,3}|[0-9]{1,3})(\]?)$'

def sql_conn():
    return pymysql.connect(host=conf.DBHOST,user=conf.DBUSER,\
        password=conf.DBPW,db=conf.DBNAME,charset='utf8mb4',\
        cursorclass=pymysql.cursors.DictCursor)

@app.task
def login(user,pw):
    if isinstance(user,str) and isinstance(pw,str):
        if not re.match(user_rule,user):
            return 2
        conn = sql_conn()
        cursor = conn.cursor()
        sql = "SELECT user,admin FROM user WHERE user=%s AND password=%s LIMIT 1"
        cursor.execute(sql,(user,gen_pw(user,pw),))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result :
            return 1
        else:
            return 3
    else:
        return 2

@app.task
def register(user,pw,email,school,invitecode,now):
    if isinstance(user,str) and isinstance(pw,str) and \
    isinstance(email,str) and isinstance(school,str) and \
    isinstance(invitecode,str):
        if not re.match(user_rule,user):
            return [2,r'用户名格式错误('+user_rule+')']
        if len(pw)<6 :
            return [2,'密码太短']
        if not re.match(email_rule,email):
            return [2,'邮件格式错误']
        if len(email) > 50:
            return [2,'邮件太长']
        if len(school)<2 :
            return [2,'请填写学校']
        if len(school)>20 :
            return [2,'学校太长']
        conn = sql_conn()
        cursor=conn.cursor()
        sql = "SELECT user FROM user WHERE user=%s LIMIT 1"
        cursor.execute(sql,(user,))
        result = cursor.fetchone()
        if result != None:
            cursor.close()
            conn.close()
            return [2,'用户名已存在']
        #InviteCode
        if invitecode != 'test':
            return [2,'邀请码错误']

        sql = "INSERT INTO user (user,password,email,school,\
            motto,admin,ac_num,submit_num,msg_num,tongji,ac_list,gen_date) VALUES \
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql,(user,gen_pw(user,pw),email,school,\
            'Write the code. Change the world.',0,0,0,0,json.dumps([0]*7),json.dumps([]),str(now),))
        conn.commit()
        cursor.close()
        conn.close()
        return [1,'注册成功']
    else:
        return [2,'数据类型错误']