from celery import Celery,platforms
import re
from tools import *
import time
import json
import conf
import random
import lorun
import shutil
import os
import urllib.request
backend = 'amqp'
broker = 'amqp://127.0.0.1:5672'

app = Celery('tasks',backend=backend,broker=broker)
platforms.C_FORCE_ROOT = True

'celery -A tasks worker --loglevel=info --pool=solo'

RESULT_STR = [
    'Accepted',
    'Presentation Error',
    'Time Limit Exceeded',
    'Memory Limit Exceeded',
    'Wrong Answer',
    'Runtime Error',
    'Output Limit Exceeded',
    'Compile Error',
    'System Error'
]

@app.task
def prepare(judge_id,prob_id,data,spj):
    judge_id=int(judge_id)
    prob_id=int(prob_id)
    data=json.loads(data)
    #mkdir
    os.makedirs('./%d/data/'%judge_id)
    #download data
    url=conf.DATA_URL
    try:
        for case in data:
            for r in case:
                tim=int(time.time())
                ask=urllib.parse.urlencode({'prob':prob_id,'tim':tim,'name':r[0],'key':calc_md5(str(prob_id)+str(tim)+r[0],conf.DOWNLOAD_KEY)})
                urllib.request.urlretrieve(url+'?'+ask,'./%d/data/%s' % (judge_id,r[0]))
                #file - r[0]
    except Exception as e:
        shutil.rmtree('%d'%judge_id)
        return [2,str(e)]
    else:
        return [1,'success']
    
    
    #TODO SPJ compile spj

@app.task
def compile(judge_id,lang,code):
    judge_id=int(judge_id)
    if lang != 1:
        shutil.rmtree('%d'%judge_id)
        return [2,'其他语言尚未开放提交']

    f = open('./%d/c.cpp'%judge_id,'w')
    f.write(code)
    f.close()
    if os.system('g++ ./%d/c.cpp -o ./%d/c -O2 2>./%d/compile_result'%(judge_id,judge_id,judge_id)) != 0:
        ret= [2,open('./%d/compile_result'%judge_id,'r').read(1000)]
        shutil.rmtree('%d'%judge_id)
        return ret
    return [1,open('./%d/compile_result'%judge_id,'r').read(1000)]
    
def runone(p_path, in_path, out_path, mem_limit, tim_limit):
    fin = open(in_path)
    ftemp = open('temp.out', 'w')
    
    runcfg = {
        'args':[p_path],
        'fd_in':fin.fileno(),
        'fd_out':ftemp.fileno(),
        'timelimit':tim_limit, #in MS
        'memorylimit':mem_limit*1024, #in KB
    }
    
    rst = lorun.run(runcfg)
    fin.close()
    ftemp.close()
    
    if rst['result'] == 0:
        ftemp = open('temp.out')
        fout = open(out_path)
        crst = lorun.check(fout.fileno(), ftemp.fileno())
        fout.close()
        ftemp.close()
        os.remove('temp.out')
        if crst != 0:
            rst['result']=crst
            return rst
    
    return rst


@app.task
def judge(judge_id,mem_limit,tim_limit,data):
    judge_id=int(judge_id)
    data=json.loads(data)
    
    result='详细结果:  \n'
    rst_num=3
    case_num=0
    mem_mx=0
    tim_sum=0
    score=0.0
    for r in data:
        case_num+=1
        in_path = './%d/data/%s'%(judge_id,r[0][0])
        out_path = './%d/data/%s'%(judge_id,r[1][0])
        if os.path.isfile(in_path) and os.path.isfile(out_path):
            rst=runone('./%d/c'%judge_id,in_path,out_path,mem_limit,tim_limit)
            st=''
            if rst['result']!=0:
                if rst['result'] !=1:
                    rst_num=[3,3,5,7,4,6,4,8,9][rst['result']]
            mem_mx=max(mem_mx,rst['memoryused'])
            tim_sum+=rst['timeused']
            st=' time: '+str(rst['timeused'])+'ms mem: '+str(rst['memoryused'])+'kb'
            if rst['result'] == 0 or rst['result']== 1:
                score += 100.0/len(data)
            result+= 'Case#'+str(case_num)+': '+RESULT_STR[rst['result']]+st+'  \n'
            
        else:
            shutil.rmtree('%d'%judge_id)
            return [9,'标准输入或输出文件不存在',mem_mx,tim_sum]
    shutil.rmtree('%d'%judge_id)
    result+= '\n score: $%d$  \n'%int(score)
    return [rst_num,result,mem_mx,tim_sum]






