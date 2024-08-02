# first step with django

## celery instance 추가

django 프로젝트 구조
```
- proj/
  - manage.py
  - config/
    - __init__.py
    - settings.py
    - urls.py
    - celery.py
```

config폴더에 celery.py 수정
```
# proj/config/celery.py
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

config/__init__.py에 celery app을 추가  
config 패키지 importtl 함께 celery app이 추가되도록 
```
# proj/config/__init__.py
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
```
config/settings.py수정  
(CELERY_프리픽스를 붙여서 입력)  
```
from kombu import Exchange, Queue

CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'
CELERY_RESULT_BACKEND = 'rpc://'
# celery큐가 default 큐임
CELERY_TASK_QUEUES = (
    Queue('celery', Exchange('default'), routing_key='celery'),
    Queue('high', Exchange('default'), routing_key='high'),
)
# task함수별 기본 라우팅 될 큐 설정
# CELERY_TASK_ROUTES = {
#     'tasks.high_priority_tasks.high_priority_task': {'queue': 'high'},
#     'tasks.default_tasks.default_task': {'queue': 'celery'},
# }
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Seoul'
CELERY_ENABLE_UTC = True
```

app폴더의 tasks들에 task함수 지정
```
- demoapp1/
    - tasks.py
    - models.py
- demoapp2/
    - tasks.py
    - models.py
```
task 예시 : demoapp1  
shared_task를 사용하면 app을 portable하게 관리가능
```
from demoapp1.models import Widget
from celery import shared_task

@shared_task
def add(x, y):
    return x + y

@shared_task
def mul(x, y):
    return x * y

@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def count_widgets():
    return Widget.objects.count()

@shared_task
def rename_widget(widget_id, name):
    w = Widget.objects.get(id=widget_id)
    w.name = name
    w.save()
```

## celery worker process 시작
celery --app config worker -l INFO  
* 기본설정으로 cpu코어 개수만큼 서브 프로세스가 설정됨. 
* --concurrency or -c 옵션으로 서브프로세스 개수를 설정할 수 있음. 
* --autoscale=10,3 으로 최소 3최대 10개의 서브프로세스를 유지할 수 있음. 

## db transaction과 celery task
```
# views.py
def create_user(request):
    # Note: simplified example, use a form to validate input
    user = User.objects.create(username=request.POST['username'])
    send_email.delay(user.pk)
    return HttpResponse('User created')

# task.py
@shared_task
def send_email(user_pk):
    user = User.objects.get(pk=user_pk)
    # send email ...
```
위와 같은 코드에서 이메일 전송 task가 db트랜젝션보다 일찍 수행될 수 있다.  
결과적으로 task에선 user객체를 얻지 못해 에러가 날 수 있음.   
이 문제를 해결하려면 아래와 같이 transaction콜백을 써야 한다.

```
- send_email.delay(user.pk)
+ transaction.on_commit(lambda: send_email.delay(user.pk))

celery 5.4이후로는 아래와 같은 shorcut도 사용가능함
- send_email.delay(user.pk)
+ send_email.delay_on_commit(user.pk)
```

## django의 celery 3rd party apps

### django-celery-results
result 백엔드로 django db와 orm이 사용됨.  
redis, rabbitmq에서 제공하지 않는 데이터 영속성을 제공할 수 있음. 
```
pip install django-celery-results
```
settings.py
```
INSTALLED_APPS = (
    ...,
    'django_celery_results',
)
```
```
python manage.py migrate
```
```
CELERY_RESULT_BACKEND = 'django-db'
```
```
# 캐시 백엔드는 동일 작업에 대한 결과를 캐시하는데 사용됨.
CELERY_CACHE_BACKEND = 'django-cache'

# 장고의 캐쉬세팅을 가져다가 쓰도록 설정할 수도 있음. 
CELERY_CACHE_BACKEND = 'default'
# django setting.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}
```
### django-celery-beat
일정주기로 수행되어야 하는 task를 설정.  
admin 페이지에서 task 설정가능

