from django.views import View
from ..tasks import test_task
from django.http import HttpResponse
from celery.result import AsyncResult
from django.shortcuts import render

class TestView(View):
    def get(self, request, *args, **kwargs):
        aresult = test_task.delay(1,2)        
        context={}
        context['task_id'] = aresult.id
        print(aresult.id)                
        return render(request, 'myapp/index.html', context=context)
    
class TestResultView(View):
    def get(self, request, *args, **kwargs):
        task_id=kwargs['task_id']
        aresult = AsyncResult(task_id)        
        context={}
        context['task_id'] = aresult.id
        context['task_state']=aresult.state
        context['task_result']=aresult.result
        return HttpResponse(f'task_id:{task_id}, status : {aresult.state}, get:{aresult.result}')