from django.contrib import admin
from .models import SpeakingTask, AudioRecording, SpeechAnalysis, UserAssessment, ProgressSession, ImpromptuTopic

@admin.register(ImpromptuTopic)
class ImpromptuTopicAdmin(admin.ModelAdmin):
    list_display = ['topic', 'category', 'difficulty_level', 'is_active', 'created_at']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['topic']

@admin.register(SpeakingTask)
class SpeakingTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_id', 'time_limit', 'created_at']
    search_fields = ['title', 'task_id']

@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    list_display = ['user', 'filename', 'task', 'virtual_scene', 'duration', 'uploaded_at']
    list_filter = ['uploaded_at', 'task', 'virtual_scene']
    search_fields = ['user__username', 'filename', 'topic']

@admin.register(SpeechAnalysis)
class SpeechAnalysisAdmin(admin.ModelAdmin):
    list_display = ['recording', 'speech_rate', 'pause_count', 'volume_variation', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['recording__filename', 'recording__user__username']

@admin.register(UserAssessment)
class UserAssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'recording', 'confidence', 'clarity', 'pace', 'average_score', 'submitted_at']
    list_filter = ['submitted_at', 'confidence', 'clarity', 'pace']
    search_fields = ['user__username', 'recording__filename']

@admin.register(ProgressSession)
class ProgressSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_date', 'recording']
    list_filter = ['session_date']
    search_fields = ['user__username']