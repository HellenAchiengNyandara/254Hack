import os
import numpy as np
import librosa
from pydub import AudioSegment

# Setup AudioSegment (you'll need to adjust these paths)
try:
    AudioSegment.converter = r"C:\Users\Hellen\Downloads\ffmpeg-7.1.1-full_build\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\Users\Hellen\Downloads\ffmpeg-7.1.1-full_build\ffmpeg-7.1.1-full_build\bin\ffprobe.exe"
except:
    pass  # FFmpeg paths might not be available in all environments

def convert_numpy_types(obj):
    """Convert numpy types to JSON-serializable types"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    return obj

def analyze_audio(filepath):
    """
    Basic audio analysis using librosa
    You can expand this based on your original analysis.py file
    """
    try:
        # Load audio file
        y, sr = librosa.load(filepath, sr=16000)
        
        # Basic analysis
        duration = len(y) / sr
        
        # Speech rate (words per minute estimate)
        # This is a simplified estimation
        rms = librosa.feature.rms(y=y)[0]
        speech_segments = len(rms[rms > np.mean(rms)])
        speech_rate = (speech_segments * 60) / duration if duration > 0 else 0
        
        # Pause detection (simplified)
        pause_threshold = np.mean(rms) * 0.1
        pauses = rms < pause_threshold
        pause_count = len([1 for i in range(1, len(pauses)) if pauses[i] and not pauses[i-1]])
        
        # Volume variation
        volume_variation = np.std(rms)
        
        # Pitch analysis
        pitches = librosa.yin(y, fmin=50, fmax=300)
        pitch_variation = np.std(pitches[pitches > 0]) if len(pitches[pitches > 0]) > 0 else 0
        
        # Energy level
        energy_level = np.mean(rms)
        
        return {
            "duration": duration,
            "speech_rate": float(speech_rate),
            "pause_count": int(pause_count),
            "volume_variation": float(volume_variation),
            "pitch_variation": float(pitch_variation),
            "energy_level": float(energy_level)
        }
    except Exception as e:
        print(f"Audio analysis error: {e}")
        return None

def generate_feedback_from_analysis(analysis):
    """Generate feedback based on analysis results"""
    suggestions = []
    
    # Speech rate feedback
    if analysis["speech_rate"] < 100:
        suggestions.append("Try speaking a bit faster to maintain engagement.")
    elif analysis["speech_rate"] > 200:
        suggestions.append("Consider slowing down slightly for better clarity.")
    else:
        suggestions.append("Your speaking pace is good!")
    
    # Pause feedback
    if analysis["pause_count"] < 3:
        suggestions.append("Add more strategic pauses to emphasize key points.")
    elif analysis["pause_count"] > 15:
        suggestions.append("Try to reduce unnecessary pauses for smoother delivery.")
    
    # Volume feedback
    if analysis["volume_variation"] < 0.1:
        suggestions.append("Try varying your volume more to add emphasis.")
    
    # Chart data for visualization
    chart_data = {
        "speech_rate": analysis["speech_rate"],
        "pause_count": analysis["pause_count"],
        "volume_variation": analysis["volume_variation"],
        "pitch_variation": analysis["pitch_variation"],
        "energy_level": analysis["energy_level"]
    }
    
    return {
        "suggestions": suggestions,
        "chart_data": chart_data
    }
