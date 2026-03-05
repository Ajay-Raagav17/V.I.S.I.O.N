"""
Transcription service using AssemblyAI (FREE tier: 5 hours/month).

AssemblyAI provides:
- High accuracy speech-to-text
- Real-time transcription
- Multiple language support
- Works with Vercel serverless
"""

import os
import time
import requests
from typing import Iterator, Optional

from services.error_handling import (
    ExternalAPIError,
    log_error,
    log_info,
    log_warning,
)


class TranscriptionService:
    """
    Service for transcribing audio using AssemblyAI.
    
    FREE tier includes 5 hours of transcription per month.
    Sign up at: https://www.assemblyai.com/
    """
    
    SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'mp4', 'mpeg'}
    
    BASE_URL = "https://api.assemblyai.com/v2"
    
    def __init__(self):
        """Initialize the AssemblyAI transcription service."""
        self.api_key = os.getenv('ASSEMBLYAI_API_KEY')
        
        if not self.api_key:
            log_warning("ASSEMBLYAI_API_KEY not set. Transcription will not work.")
        
        self.MAX_FILE_SIZE = int(os.getenv('MAX_UPLOAD_SIZE_MB', '100')) * 1024 * 1024
        
        self.headers = {
            "authorization": self.api_key or "",
            "content-type": "application/json"
        }
    
    def validate_audio_format(self, file_path: str) -> bool:
        """Check if audio format is supported."""
        if not file_path:
            return False
        extension = file_path.lower().split('.')[-1]
        return extension in self.SUPPORTED_FORMATS
    
    def validate_file_size(self, file_size: int) -> bool:
        """Check if file size is within limits."""
        return 0 < file_size <= self.MAX_FILE_SIZE
    
    def transcribe_file(self, audio_file: bytes, format: str) -> str:
        """
        Transcribe audio file using AssemblyAI.
        
        Args:
            audio_file: Audio file content as bytes
            format: Audio format (mp3, wav, etc.)
            
        Returns:
            Complete transcript as a string
        """
        if not self.api_key:
            raise ExternalAPIError(
                service="AssemblyAI",
                message="ASSEMBLYAI_API_KEY not configured. Get free API key at https://www.assemblyai.com/"
            )
        
        # Validate format
        if format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}")
        
        # Validate size
        if not self.validate_file_size(len(audio_file)):
            raise ValueError(f"File too large. Max size: {self.MAX_FILE_SIZE} bytes")
        
        try:
            # Step 1: Upload the audio file
            log_info("Uploading audio to AssemblyAI...")
            upload_url = self._upload_file(audio_file)
            
            # Step 2: Request transcription
            log_info("Starting transcription...")
            transcript_id = self._request_transcription(upload_url)
            
            # Step 3: Poll for completion
            log_info("Waiting for transcription to complete...")
            transcript = self._poll_transcription(transcript_id)
            
            log_info(f"Transcription completed. Length: {len(transcript)} chars")
            return transcript
            
        except requests.RequestException as e:
            log_error(e, context={"service": "AssemblyAI"})
            raise ExternalAPIError(
                service="AssemblyAI",
                message=f"API request failed: {str(e)}",
                original_exception=e
            )
    
    def _upload_file(self, audio_data: bytes) -> str:
        """Upload audio file to AssemblyAI and return the upload URL."""
        headers = {
            "authorization": self.api_key,
            "content-type": "application/octet-stream"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/upload",
            headers=headers,
            data=audio_data,
            timeout=300  # 5 min timeout for large files
        )
        
        if response.status_code != 200:
            raise ExternalAPIError(
                service="AssemblyAI",
                message=f"Upload failed: {response.text}"
            )
        
        return response.json()["upload_url"]
    
    def _request_transcription(self, audio_url: str) -> str:
        """Request transcription and return the transcript ID."""
        data = {
            "audio_url": audio_url,
            "language_code": "en",  # Can be changed for other languages
            "punctuate": True,
            "format_text": True,
        }
        
        response = requests.post(
            f"{self.BASE_URL}/transcript",
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise ExternalAPIError(
                service="AssemblyAI",
                message=f"Transcription request failed: {response.text}"
            )
        
        return response.json()["id"]
    
    def _poll_transcription(self, transcript_id: str, max_wait: int = 600) -> str:
        """Poll for transcription completion and return the text."""
        endpoint = f"{self.BASE_URL}/transcript/{transcript_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                raise ExternalAPIError(
                    service="AssemblyAI",
                    message=f"Status check failed: {response.text}"
                )
            
            result = response.json()
            status = result["status"]
            
            if status == "completed":
                return result["text"] or ""
            elif status == "error":
                raise ExternalAPIError(
                    service="AssemblyAI",
                    message=f"Transcription failed: {result.get('error', 'Unknown error')}"
                )
            
            # Wait before polling again
            time.sleep(3)
        
        raise ExternalAPIError(
            service="AssemblyAI",
            message="Transcription timed out"
        )
    
    def transcribe_stream(self, audio_stream: Iterator[bytes]) -> Iterator[str]:
        """
        Process streaming audio.
        
        Note: For real-time, use AssemblyAI's real-time WebSocket API
        or browser Web Speech API for live captioning.
        """
        audio_chunks = list(audio_stream)
        if audio_chunks:
            full_audio = b''.join(audio_chunks)
            transcript = self.transcribe_file(full_audio, 'wav')
            yield transcript
    
    def get_supported_formats(self) -> set:
        """Get supported audio formats."""
        return self.SUPPORTED_FORMATS.copy()


class AssemblyAIRealtime:
    """
    Real-time transcription using AssemblyAI WebSocket.
    
    For live captioning with very low latency.
    """
    
    REALTIME_URL = "wss://api.assemblyai.com/v2/realtime/ws"
    
    def __init__(self):
        self.api_key = os.getenv('ASSEMBLYAI_API_KEY')
    
    def get_websocket_url(self, sample_rate: int = 16000) -> str:
        """Get WebSocket URL for real-time transcription."""
        return f"{self.REALTIME_URL}?sample_rate={sample_rate}"
    
    def get_auth_header(self) -> dict:
        """Get authorization header for WebSocket connection."""
        return {"authorization": self.api_key}
