from typing import Dict, Any

class AudioTranscriber:
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        return {
            "text": "Transcribed speech from audio recording.",
            "duration_seconds": 12.5,
            "segments": []
        }
