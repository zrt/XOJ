from celery import Celery,platforms
import pymysql.cursors
import re
from tools import *
import time
import json
import conf
import random
backend = 'amqp'
broker = 'amqp://'

app = Celery('tasks',backend=backend,broker=broker)
platforms.C_FORCE_ROOT = True

'celery -A tasks worker --loglevel=info --pool=solo'

def download_data(judge_id,data):
    time.sleep(random.choice(range(1,5)))
    if random.random()>0.1 :
        return [1,'']
    else:
        return [2,'评测机随机挂']

@app.task
def prepare(judge_id,data,spj):
    r = download_data(judge_id,data)
    if r[0] == 1:
        return [1,r[1]]
    else:
        return [2,r[1]]

@app.task
def compile(judge_id,lang,code):
    r = download_data(judge_id,code)
    if r[0] == 1:
        return [1,r[1]]
    else:
        return [2,r[1]]

@app.task
def judge(judge_id,mem_limit,tim_limit):
    r = download_data(judge_id,mem_limit)
    return [random.choice(range(3,8)),'####评测结果\n由于评测机还没写好，所以由量子态的评测机随机评测。',random.choice(range(10,2000)),random.choice(range(10,2000))]

