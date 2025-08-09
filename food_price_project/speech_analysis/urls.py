from django.urls import path
from . import views

app_name = 'speech_analysis'

urlpatterns = [
    path('', views.speech_dashboard, name='dashboard'),
    path('upload/', views.upload_recording, name='upload_recording'),
    path('analyze/<int:recording_id>/', views.analyze_recording, name='analyze_recording'),
    path('submit-assessment/', views.submit_assessment, name='submit_assessment'),
    path('sessions/', views.get_progress_sessions, name='progress_sessions'),
    path('metrics/', views.get_metric_history, name='metric_history'),
    path('practice/<str:task_id>/', views.practice_task, name='practice_task'),
    path('api/random-topic/', views.get_random_topic, name='random_topic'),
]
