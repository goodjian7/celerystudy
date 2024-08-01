from celery import Celery

##redis 사용시
#app=Celery('tasks', backend='redis://localhost', broker='redis://localhost')

#rabbitmq 사용시
app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task
def add(x,y):
    return x+y

