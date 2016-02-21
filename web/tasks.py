from celery import Celery
import time
backend = 'amqp'
broker = 'amqp://'

app = Celery('tasks',backend=backend,broker=broker)

'celery -A tasks worker --loglevel=info --pool=solo'

@app.task
def login(user,password):
    if user=='zrt' and password=='zrt':
        return 1
    else:
        return 2

@app.task
def register(user,pw,email,school,invitecode,now):
    return [1,'success']