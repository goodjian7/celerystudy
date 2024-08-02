from django.contrib import admin
from django.urls import path, include
from .views.testViews import TestView, TestResultView

app_name='myapp'
urlpatterns = [    
    path('', TestView.as_view(), name='index'),
    path('result/<str:task_id>/', TestResultView.as_view(), name='task_result'),
]