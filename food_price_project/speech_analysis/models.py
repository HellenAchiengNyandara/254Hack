from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class ImpromptuTopic(models.Model):
    topic = models.CharField(max_length=500)
    category = models.CharField(max_length=100, blank=True)
    difficulty_level = models.CharField(max_length=20, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.topic

class SpeakingTask(models.Model):
    task_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    time_limit = models.IntegerField(default=3)  # in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class AudioRecording(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(SpeakingTask, on_delete=models.CASCADE, null=True, blank=True)
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    virtual_scene = models.CharField(max_length=100, default='small-audience')
    topic = models.CharField(max_length=500, blank=True)  # For impromptu speeches
    
    def __str__(self):
        return f"{self.user.username} - {self.filename}"

class SpeechAnalysis(models.Model):
    recording = models.OneToOneField(AudioRecording, on_delete=models.CASCADE)
    speech_rate = models.FloatField(null=True, blank=True)
    pause_count = models.IntegerField(null=True, blank=True)
    volume_variation = models.FloatField(null=True, blank=True)
    pitch_variation = models.FloatField(null=True, blank=True)
    energy_level = models.FloatField(null=True, blank=True)
    
    # Store detailed analysis as JSON
    detailed_analysis = models.JSONField(default=dict, blank=True)
    
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.recording.filename}"

class UserAssessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recording = models.ForeignKey(AudioRecording, on_delete=models.CASCADE)
    task = models.ForeignKey(SpeakingTask, on_delete=models.CASCADE, null=True, blank=True)
    
    # Self-assessment scores (1-10 scale)
    confidence = models.IntegerField()
    clarity = models.IntegerField()
    pace = models.IntegerField()
    
    # User reflection
    reflection = models.TextField()
    
    # Calculated average
    average_score = models.FloatField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calculate average score
        self.average_score = round((self.confidence + self.clarity + self.pace) / 3, 1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - Assessment for {self.recording.filename}"

class ProgressSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recording = models.ForeignKey(AudioRecording, on_delete=models.CASCADE)
    assessment = models.ForeignKey(UserAssessment, on_delete=models.CASCADE, null=True, blank=True)
    analysis = models.ForeignKey(SpeechAnalysis, on_delete=models.CASCADE, null=True, blank=True)
    
    session_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-session_date']
    
    def __str__(self):
        return f"{self.user.username} - Session {self.session_date.date()}"