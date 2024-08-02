# next steps

## python 프로젝트에서 celery 쓰기
프로젝트 구조  
```
src/
    proj/__init__.py
        /celery.py
        /tasks.py
```
proj/celery.py  
```
from celery import Celery

app = Celery('proj',
             broker='amqp://localhost',
             backend='rpc://localhost',
             include=['proj.tasks']) ## include는 포함할 task정의모듈

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
```

proj/tasks.py
```
from .celery import app

# @app.task(ignore.result=True) 
# 결과를 처리하지 않을 수 있음. 
@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)
```

celery worker시작하기 (src폴더에서 수행)
```
$ celery -A proj worker -l INFO
```

출력메시지 분석

```
--------------- celery@halcyon.local v4.0 (latentcall)
--- ***** -----
-- ******* ---- [Configuration]
- *** --- * --- . broker:      amqp://guest@localhost:5672//
- ** ---------- . app:         __main__:0x1012d8590
- ** ---------- . concurrency: 8 (processes)
- ** ---------- . events:      OFF (enable -E to monitor this worker)
- ** ----------
- *** --- * --- [Queues]
-- ******* ---- . celery:      exchange:celery(direct) binding:celery
--- ***** -----

[2012-06-08 16:23:51,078: WARNING/MainProcess] celery@halcyon.local has started.
```

* broker : -b 옵션과 동일 redis or rabbitmq url
* concurrency : worker프로세스 수, 기본설정은 cpu코어수와 동일 -c옵션과 동일효과  
* Events : celery  worker가 내부상태를 보고하는 이벤트를 보낼지여부  
celeryevents나 Folower같은 실시간 모니터링 프로그램사용시 ON
* Queues : Task가 큐잉될 큐 목록, 워커들이 특정 큐의 TASK만 처리하게하는등의 옵션을 걸 수 있다.  

워커 정지 : control + c  

백그라운드 워커 실행, 재실행, 정지(async), 정지(sync) (daemonization)
```
$ celery multi start w1 -A proj -l INFO
$ celery  multi restart w1 -A proj -l INFO
$ celery multi stop w1 -A proj -l INFO
$ celery multi stopwait w1 -A proj -l INFO
```
a정지, 정지, 재시작시 start에 사용한 옵션을 그대로 써야함  
백그라운드 워커 실행시 pid파일과 log파일을 현재폴더에 생성함  
중복실행을 방지하기 위해 아래와 같이 pid파일과 log파일을 지정해주면 좋음  
```
mkdir -p /var/run/celery
mkdir -p /var/log/celery
celery multi start w1 -A proj -l INFO \
--pidfile=/var/run/celery/%n.pid \
--logfile=/var/log/celery/%n%I.log
```

멀티워커를 다음과 같은 명령어로 시작할 수 있음. 
```
$ celery multi start 10 -A proj -l INFO \
-Q:1-3 images,video \
-Q:4,5 data \
-Q default \
-L:4,5 debug
```
* 10개의 워커를 실행
* -A proj 폴더를 사용해서
* -l INFO 로그는 INFO레벨로
* -Q:1-3 images, video : 1~3번 워커는 images, video큐를 처리
* -Q:4,5 data : 4,5번 워커는 data 큐 처리
* -Q default : 나머지 워커는 default 큐를 처리
* -L:4,5 debug :4,5워커는 로그시 debug레벨로 설정 

## --app 의 아규먼트
기본설정으로는 --app 모듈경로:변수(attribute) 형태  
패키지이름만 --app의 인자로 넣으면 다음과 같은 순서로 app인스턴스를 찾음
* proj.app 변수
* proj.celery 변수
* proj 모듈에 있는 Celery객체
* proj.celery.app 변수 
* proj.celery.celery 변수
* proj.celery 모듈에 있는 Celery객체

## task 호출

```
from proj.tasks import add

add.delay(2, 2)
```
apply_async()의 shortcut

```
add.apply_async((2, 2))
add.apply_async((2, 2), queue='lopri', countdown=10)
```
apply_async를 사용하면 어떤 큐를 사용할지, 최소 몇초후에 실행되어야 할지 지정가능  

```
add(2, 2)
```
그냥 호출하면 큐잉되지 않음. 현재 프로세스에서 실행됨
큐잉된 TASK는 유니크한 ID를 부여받음 (UUID)  

delay, apply_async는 AsyncResult반환

AsyncResult이용해 id조회가능 AsyncResult.id  
result backend가 설정되었으면 AsyncResult로 상태조회가능
```
res.failed() # bool
res.successful() # bool
res.state # 'PENDING' -> 'STARTED' -> 'SUCCESS' or 'FAILURE'
```

result backend가 설정되었으면 AsyncResult로 결과조회가능
```
res.get(timeout=1) # 1초이내 완료되지 않으면 TimeoutError throw
# 기본설정으로 수행시 에러발생하면 수행중 발생한 에러를 throw함
# propagate=False 설정하면 throw하지 않고 반환함
res.get(propagate=False)
```

# 비동기 Task 함수호출 자체를 변수로 사용 :signature
```
# add.s((2,2), countdown=10) shorcut도 있음 
#task.add(2,2) 반환
s1 = add.signature((2, 2), countdown=10)
res = s1.delay()
res.get()
```
다음과 같이 일부인자만 넣은 signiture를 사용하는 것도 가능
```
# incomplete partial: add(?, 2)
s2 = add.s(2)
# resolves the partial: add(8, 2)
res = s2.delay(8)
res.get()

s3 = add.s(2, 2, debug=True)
# debug is now False.
s3.delay(debug=False)   
```

## signature사례 : Groups

```
from celery import group
from proj.tasks import add
group(add.s(i, i) for i in range(10))().get()
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

g = group(add.s(i) for i in range(10))
g(10).get()
[10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
```

## signature사례 : Chains
```
from celery import chain
from proj.tasks import add, mul
# (4 + 4) * 8 = 64
chain(add.s(4, 4) | mul.s(8))().get()

# partial chain (? + 4) * 8
g = chain(add.s(4) | mul.s(8))
g(4).get()

# equivalent 
(add.s(4, 4) | mul.s(8))().get()

```

## signature사례 : Chords
콜백이 있는 group 함수로 보면 된다. 
```
from celery import chord
from proj.tasks import add, xsum # xsum은 모두 더하기
chord((add.s(i, i) for i in range(10)), xsum.s())().get()

# equivalent with group and chain
(group(add.s(i, i) for i in range(10)) | xsum.s())().get()
```

## 멀티 큐 사용방법

1. 프로젝트 구조
```
myproject/
├── celeryconfig.py
├── celery.py
├── tasks/
│   ├── __init__.py
│   ├── default_tasks.py
│   └── high_priority_tasks.py
└── run_tasks.py
```

2. celeryconfig.py 설정파일 
```
from kombu import Exchange, Queue

broker_url = 'amqp://guest:guest@localhost//'
result_backend = 'rpc://'

# celery큐가 default 큐임
task_queues = (
    Queue('celery', Exchange('default'), routing_key='celery'),
    Queue('high', Exchange('default'), routing_key='high'),
)

task_routes = {
    'tasks.high_priority_tasks.high_priority_task': {'queue': 'high'},
    'tasks.default_tasks.default_task': {'queue': 'celery'},
}

# Additional configuration (optional)
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Seoul'
enable_utc = True
```

3. celery.py
```
from celery import Celery

app = Celery('myapp')
app.config_from_object('celeryconfig')
app.autodiscover_tasks(['tasks'])
```

4. tasks폴더내 파일들에 task설정
```
# tasks/default_tasks.py
from celery import shared_task

@shared_task
def default_task(x, y):
    return x + y
```

```
# tasks/high_priority_tasks.py
from celery import shared_task

@shared_task
def high_priority_task(x, y):
    return x * y
```

5. run_tasks.py
```
from tasks.default_tasks import default_task
from tasks.high_priority_tasks import high_priority_task

# 기본 큐에 작업 보내기
result = default_task.apply_async((2, 3))
print(result.get())  # 작업 결과를 가져옴

# high 큐에 작업 보내기
result = high_priority_task.apply_async((2, 3), queue='high')
print(result.get())  # 작업 결과를 가져옴
```

6. 워커실행
```

# 워커실행
$ celery multi start w1 -A celery -Q celery,high --loglevel=info --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --detach

#워커 중지
$ celery multi stop w1 -A celery -Q celery,high --loglevel=info --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --detach

#워커 재시작
$ celery multi restart w1 -A celery -Q celery,high --loglevel=info --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --detach
```

* 여러개의 워커를 한커맨드로 실행하고 싶다면 w1, w2 같은 이름대신 숫자를 입력하면 된다.  
* 아래 내용 참고
```
$ celery multi start 10 -A proj -l INFO \
-Q:1-3 images,video \
-Q:4,5 data \
-Q default \
-L:4,5 debug \
--pidfile=/var/run/celery/%n.pid \
--logfile=/var/log/celery/%n%I.log
```
10개의 워커를 실행  
-A proj 폴더를 사용해서  
-l INFO 로그는 INFO레벨로  
-Q:1-3 images, video : 1~3번 워커는 images, video큐를 처리  
-Q:4,5 data : 4,5번 워커는 data 큐 처리  
-Q default : 나머지 워커는 default 큐를 처리  
-L:4,5 debug :4,5워커는 로그시 debug레벨로 설정   

## 런타임때 워커 상태 inspect하기
skip  



