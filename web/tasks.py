from celery import Celery
import time
backend = 'amqp'
broker = 'amqp://'

app = Celery('tasks',backend=backend,broker=broker)

'celery -A tasks worker --loglevel=info --pool=solo'

@app.task
def login(user,password):
    if user=='233' and password=='233':
        return 1
    else:
        return 2