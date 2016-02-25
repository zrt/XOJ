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
