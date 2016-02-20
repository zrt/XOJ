import tornado.escape
def log(s):
    print(s)
def escape(s):
    return  tornado.escape.xhtml_escape(s)