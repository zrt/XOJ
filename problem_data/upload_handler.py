from tornado import httpserver,ioloop,web,gen,httpclient
from base_handler import BaseHandler
from tools import *
import time
from urllib.parse import urljoin
import json
import os
import shutil
import zipfile

class UpHandler(BaseHandler):

    def post(self):
        if os.path.isdir('./tmp'):
            shutil.rmtree('tmp')
        prob_id = self.get_argument('prob_id')
        user = self.get_argument('user')
        tim = self.get_argument('tim')
        key = self.get_argument('key')
        cover = self.get_argument('cover',None)
        
        #verify
        if calc_md5(user+tim+prob_id,conf.DOWNLOAD_KEY) != key:
            self.set_status(400)
            return
        tim = int(tim)
        prob_id = int(prob_id)
        tim_now = int(time.time())
        if tim < tim_now-1000 or tim > tim_now+1000:
            self.redirect(urljoin(conf.SERVER_URL,'/problem/%d/edit/3?msg=页面过期'%prob_id))
            return
        #
        
        os.mkdir('tmp')
        #
        data = self.request.files['zip'][0]
        f = open('./tmp/data.zip','wb')
        f.write(data['body'])
        f.close()
        # ./tmp/data.zip
        if not zipfile.is_zipfile('./tmp/data.zip'):
            self.redirect(urljoin(conf.SERVER_URL,'/problem/%d/edit/3?msg=请上传zip文件'%prob_id))
            shutil.rmtree('tmp')
            return
        if cover and os.path.isdir('./data/%d'%prob_id):
            shutil.rmtree('./data/%d'%prob_id)
        if not os.path.isdir('./data/%d'%prob_id):
            os.makedirs('./data/%d'%prob_id)

        f = zipfile.ZipFile('./tmp/data.zip','r')
        filelist = f.namelist()
        namelist = list(set([os.path.splitext(s)[0] for s in filelist]))
        for name in namelist:
            infile = None
            outfile = None
            if (name+'.in') in filelist:
                infile = name+'.in'
            if (name+'.out') in filelist:
                outfile = name+'.out'
            if (name+'ans') in filelist:
                outfile = name+'.ans'
            if infile and outfile:
                with open('./data/%d/%s'%(prob_id,name+'.in'),'wb') as fs:
                    fs.write(f.read(infile))
                with open('./data/%d/%s'%(prob_id,name+'.out'),'wb') as fs:
                    fs.write(f.read(outfile))
        f.close()
        #call back
        filelist = os.listdir('./data/%d'%prob_id)
        filelist.sort()
        tot = len(filelist)//2

        data = [[[filelist[i*2],os.path.getsize('./data/%d/'%prob_id+filelist[i*2])],\
        [filelist[i*2+1],os.path.getsize('./data/%d/'%prob_id+filelist[i*2+1])]] for i in range(tot)]
        
        callback = {'id':prob_id,'data':json.dumps(data)}

        callback['tim']=int(time.time())
        json_callback=json.dumps(callback)
        body_content = urllib.parse.urlencode({'content':json_callback,'key':calc_md5(json_callback,conf.DOWNLOAD_KEY)})
        url = urljoin(conf.SERVER_URL,'/data-callback')+'?'+body_content
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url)

        self.redirect(urljoin(conf.SERVER_URL,'/problem/%d/edit/3?msg=文件上传成功'%prob_id))
        shutil.rmtree('tmp')

