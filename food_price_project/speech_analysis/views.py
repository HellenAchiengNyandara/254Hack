import os
import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from pydub import AudioSegment

from .models import AudioRecording, SpeechAnalysis, UserAssessment, SpeakingTask, ProgressSession, ImpromptuTopic
from .utils import analyze_audio, generate_feedback_from_analysis, convert_numpy_types
import random

# Create upload directory
UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, "speech_recordings")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Default speaking tasks
SPEAKING_TASKS = [
    {
        "id": "short-presentation", 
        "title": "Short Presentation",
        "description": "Practice delivering a focused presentation on a topic of your choice",
        "instructions": "Prepare and deliver a 3-5 minute presentation on any topic you're passionate about. Structure your talk with a clear introduction, main points, and conclusion. Focus on engaging your audience and speaking with confidence.",
        "time_limit": 5
    },
    {
        "id": "elevator-pitch", 
        "title": "Elevator Pitch",
        "description": "Perfect your 60-second personal pitch",
        "instructions": "Create a compelling 60-second pitch about yourself, your skills, or your business idea. Imagine you're in an elevator with someone important - make every second count!",
        "time_limit": 1
    },
    {
        "id": "storytelling", 
        "title": "Storytelling Challenge",
        "description": "Tell an engaging story that captivates your audience",
        "instructions": "Share a personal story, anecdote, or fictional tale. Focus on using vivid details, emotional connection, and a clear narrative arc to keep your audience engaged.",
        "time_limit": 4
    },
    {
        "id": "impromptu-speech", 
        "title": "Impromptu Speech",
        "description": "Speak spontaneously on a random topic",
        "instructions": "You'll be given a random topic and have 30 seconds to think before delivering a 2-3 minute impromptu speech. Practice thinking on your feet and organizing your thoughts quickly.",
        "time_limit": 3
    },
    {
        "id": "product-demo", 
        "title": "Product Demo",
        "description": "Demonstrate and sell a product or service",
        "instructions": "Choose a product (real or imaginary) and give a compelling demonstration. Explain its features, benefits, and why your audience should buy it. Focus on persuasion and clarity.",
        "time_limit": 4
    },
]

# Impromptu speech topics
IMPROMPTU_TOPICS = [
    "If you could have dinner with anyone from history, who would it be and why?",
    "What skill do you wish you could master instantly?",
    "Describe your ideal vacation destination",
    "What's the most important lesson you've learned in life?",
    "If you could solve one world problem, what would it be?",
    "What technology from the future would you most want to use?",
    "Describe a moment that changed your perspective",
    "What advice would you give to your younger self?",
    "If you could start a new tradition, what would it be?",
    "What's the best compliment you've ever received?",
    "Describe your dream job",
    "What book or movie has influenced you the most?",
    "If you could live in any time period, when would it be?",
    "What's your definition of success?",
    "Describe a challenge that made you stronger",
]

def init_speaking_tasks():
    """Initialize default speaking tasks and topics in the database"""
    for task_data in SPEAKING_TASKS:
        SpeakingTask.objects.get_or_create(
            task_id=task_data["id"],
            defaults={
                "title": task_data["title"],
                "description": task_data["description"],
                "instructions": task_data["instructions"],
                "time_limit": task_data["time_limit"]
            }
        )
    
    # Initialize impromptu topics
    for topic in IMPROMPTU_TOPICS:
        ImpromptuTopic.objects.get_or_create(
            topic=topic,
            defaults={"category": "general", "is_active": True}
        )

@login_required
def speech_dashboard(request):
    """Main dashboard for speech analysis"""
    init_speaking_tasks()
    tasks = SpeakingTask.objects.all()
    recent_sessions = ProgressSession.objects.filter(user=request.user)[:5]
    
    context = {
        'tasks': tasks,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'speech_analysis/dashboard.html', context)

@login_required
@csrf_exempt
def upload_recording(request):
    """Handle audio file upload"""
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    if "audio" not in request.FILES:
        return JsonResponse({"error": "No audio file uploaded"}, status=400)

    audio_file = request.FILES["audio"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"recording_{request.user.id}_{timestamp}.webm"
    
    # Save file
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)
    
    # Get additional data from request
    task_id = request.POST.get('taskId', '')
    duration = request.POST.get('duration', 0)
    virtual_scene = request.POST.get('virtualScene', 'small-audience')
    topic = request.POST.get('topic', '')
    
    # Get task object if provided
    task = None
    if task_id:
        task = SpeakingTask.objects.filter(task_id=task_id).first()
    
    # Create database record
    recording = AudioRecording.objects.create(
        user=request.user,
        task=task,
        filename=filename,
        original_filename=audio_file.name,
        file_path=filepath,
        file_size=audio_file.size,
        duration=float(duration) if duration else None,
        virtual_scene=virtual_scene,
        topic=topic
    )

    return JsonResponse({
        "message": "Audio uploaded", 
        "filename": filename,
        "recording_id": recording.id
    })

@login_required
def analyze_recording(request, recording_id):
    """Analyze a specific recording"""
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    
    # Convert to WAV if needed
    input_path = recording.file_path
    wav_filename = os.path.splitext(recording.filename)[0] + ".wav"
    wav_path = os.path.join(UPLOAD_FOLDER, wav_filename)

    try:
        # Convert audio format
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(wav_path, format="wav")
        
        # Analyze audio
        analysis_result = analyze_audio(wav_path)
        if not analysis_result:
            return JsonResponse({"error": "Analysis failed"}, status=500)

        # Save analysis to database
        analysis, created = SpeechAnalysis.objects.get_or_create(
            recording=recording,
            defaults={
                'speech_rate': analysis_result['speech_rate'],
                'pause_count': analysis_result['pause_count'],
                'volume_variation': analysis_result['volume_variation'],
                'pitch_variation': analysis_result['pitch_variation'],
                'energy_level': analysis_result['energy_level'],
                'detailed_analysis': analysis_result
            }
        )

        # Generate feedback
        feedback = generate_feedback_from_analysis(analysis_result)

        response_data = convert_numpy_types({
            "analysis": analysis_result,
            "chart_data": feedback["chart_data"],
            "feedback": feedback["suggestions"]
        })

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": f"Analysis error: {str(e)}"}, status=500)

@login_required
@csrf_exempt
def submit_assessment(request):
    """Submit user self-assessment"""
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        required_fields = ["recordingId", "confidence", "clarity", "pace", "reflection"]

        if not all(field in data for field in required_fields):
            return JsonResponse({"error": "Missing fields"}, status=400)

        recording = get_object_or_404(AudioRecording, id=data["recordingId"], user=request.user)
        
        # Get task if specified
        task = None
        if "taskId" in data:
            task = SpeakingTask.objects.filter(task_id=data["taskId"]).first()

        # Create assessment
        assessment = UserAssessment.objects.create(
            user=request.user,
            recording=recording,
            task=task,
            confidence=data["confidence"],
            clarity=data["clarity"],
            pace=data["pace"],
            reflection=data["reflection"]
        )

        # Create progress session
        analysis = SpeechAnalysis.objects.filter(recording=recording).first()
        ProgressSession.objects.create(
            user=request.user,
            recording=recording,
            assessment=assessment,
            analysis=analysis
        )

        return JsonResponse({"message": "Assessment submitted successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def get_progress_sessions(request):
    """Get user's progress sessions"""
    sessions = ProgressSession.objects.filter(user=request.user)
    
    session_data = []
    for session in sessions:
        task_name = session.assessment.task.title if session.assessment and session.assessment.task else "Free Practice"
        
        session_data.append({
            "id": session.id,
            "recording_id": session.recording.id,
            "task_name": task_name,
            "date": session.session_date.strftime("%Y-%m-%d"),
            "timestamp": session.session_date.isoformat(),
            "average_score": session.assessment.average_score if session.assessment else None,
            "confidence": session.assessment.confidence if session.assessment else None,
            "clarity": session.assessment.clarity if session.assessment else None,
            "pace": session.assessment.pace if session.assessment else None,
        })
    
    return JsonResponse({"sessions": session_data})

@login_required
def get_metric_history(request):
    """Get user's metric history for charts"""
    sessions = ProgressSession.objects.filter(
        user=request.user,
        analysis__isnull=False
    ).order_by('session_date')
    
    history = []
    for session in sessions:
        if session.analysis:
            history.append({
                "date": session.session_date.strftime("%Y-%m-%d"),
                "speech_rate": session.analysis.speech_rate or 0,
                "pause_count": session.analysis.pause_count or 0,
                "volume_variation": session.analysis.volume_variation or 0,
                "pitch_variation": session.analysis.pitch_variation or 0,
                "energy_level": session.analysis.energy_level or 0,
            })
    
    return JsonResponse({"history": history})

@login_required
def practice_task(request, task_id):
    """Practice a specific speaking task"""
    init_speaking_tasks()  # Ensure tasks are initialized
    task = get_object_or_404(SpeakingTask, task_id=task_id)
    
    # Get random impromptu topic if this is an impromptu speech task
    impromptu_topic = None
    if task_id == "impromptu-speech":
        topics = list(ImpromptuTopic.objects.filter(is_active=True))
        if topics:
            impromptu_topic = random.choice(topics).topic
    
    # Virtual scene options
    virtual_scenes = {
        'interview': 'Job Interview',
        'small-audience': 'Small Audience',
        'workshop': 'Workshop/Training',
    }
    
    context = {
        'task': task,
        'impromptu_topic': impromptu_topic,
        'virtual_scenes': virtual_scenes,
    }
    return render(request, 'speech_analysis/practice_enhanced.html', context)

@login_required
def get_random_topic(request):
    """API endpoint to get a random impromptu topic"""
    topics = list(ImpromptuTopic.objects.filter(is_active=True))
    if topics:
        topic = random.choice(topics)
        return JsonResponse({'topic': topic.topic})
    return JsonResponse({'error': 'No topics available'}, status=404)