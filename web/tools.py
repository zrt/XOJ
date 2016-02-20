import tornado.escape
from datetime import datetime
def log(s):
    print(str(datetime.now())+' - '+s)
def escape(s):
    return  tornado.escape.xhtml_escape(s)

