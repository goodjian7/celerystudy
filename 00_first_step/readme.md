# celery

## 개념
* 클라이언트 : TASK를 브로커에게 요청
* 브로커 : 클라이언트가 요청한 TASK를 저장/분배
* worker(celery) : 브로커에서 태스크를 가져가서 처리

## 브로커 선택
* rabbitmq : docker run -d -p 5672:5672 --name rabbitmq rabbitmq
* redis : docker run -d -p 6379:6379 --name redis redis 

## celery 설치
* pip install celery

## celery task application 정의
* tasks.py 

## celery task worker 서버 시작
* celery --app=tasks worker --loglevel=INFO  
  --app=tasks : task 파이썬 모듈의 app을 찾아서 워커생성  
  worker : 명령어  
  --loglevel=INFO : INFO레벨 부터 로그  

## main.py에서 task 생성
* main.py

## worker의 결과를 처리하기 위한 result backend 설정
* tasks.py
* rabbitmq의 rpc 또는 redis의 redis를 backend로 사용

## AsyncResult의 함수들
* aresult.get이나 forget 함수를 반드시 호출해야 브로커의 result 관련 자원을 해제시킴 

## Configuration
* app객체에 지정하거나 별도의 파이썬모듈을 이용해 지정가능
* app객체에 지정하는 방법  
```
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Europe/Oslo',
    enable_utc=True,
)
```
* 별도의 파이썬 모듈을 이용해 지정하는 방법  
app.config_fron_object('celeryconfig')  
이름을 꼭 celeryconfig로 해야 하는건 아님.

```
# celeryconfig.py
# syntax error없는지 확인하려면 import해보면 됨

broker_url = 'pyamqp://localhost'
result_backend = 'rpc://localhost'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Seoul'
enable_utc = True
```

## 주요 configuration
```
task_routes = {
    'tasks.add': 'low-priority',
}
```
* task.add는 low-priority 큐로 라우팅  

```
task_annotations = {
    'tasks.add': {'rate_limit': '10/m'}
}
```  
* task.add는 분당 10개까지만 처리됨
* celery -A tasks control rate_limit tasks.add 10/m 명령어로 런타임설정 가능 (redis나 rabbitmq사용시)  






