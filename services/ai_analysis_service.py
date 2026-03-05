"""AI Analysis service for content analysis using Gemini AI."""

import os
from typing import List, Dict, Optional
import google.generativeai as genai
from dataclasses import dataclass, asdict
import json

from services.error_handling import (
    ExternalAPIError,
    GracefulDegradation,
    retry_with_backoff,
    log_error,
    log_info,
    log_warning
)


@dataclass
class Topic:
    """Represents a topic extracted from transcript."""
    title: str
    subtopics: List[str]
    keywords: List[str]
    definitions: Dict[str, str]
    formulas: List[str]
    content: str


@dataclass
class StudyNotesData:
    """Represents complete study notes structure."""
    topics: List[Topic]
    summary: str
    key_points: List[str]


class AIAnalysisService:
    """
    Service for AI-powered content analysis using Gemini AI.
    
    Provides methods for:
    - Topic extraction from transcripts
    - Content summarization
    - Segment stitching with context preservation
    - Complete study notes generation
    """
    
    def __init__(self):
        """
        Initialize the AI analysis service.
        
        Configures Gemini API credentials from environment variables.
        Requirements: 8.5
        """
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model (using gemini-1.5-flash for better availability)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(Exception,))
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Call Gemini API with retry logic.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Response text from Gemini
            
        Requirements: 7.1, 7.2
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    def extract_topics(self, transcript: str) -> List[Topic]:
        """
        Extract topics, subtopics, and keywords from transcript.
        
        Args:
            transcript: The transcribed text to analyze
            
        Returns:
            List of Topic objects with extracted information
            
        Requirements: 3.1, 3.3
        """
        if not transcript or not transcript.strip():
            return []
        
        # Create prompt for topic extraction
        prompt = f"""Analyze the following lecture transcript and extract structured topics.

For each main topic, identify:
1. Topic title
2. Subtopics (list of related sub-themes)
3. Keywords (important terms)
4. Definitions (key terms and their meanings as a dictionary)
5. Formulas (any mathematical or scientific formulas)
6. Content (detailed explanation of the topic)

Return the result as a JSON array of topics with this exact structure:
[
  {{
    "title": "Topic Title",
    "subtopics": ["Subtopic 1", "Subtopic 2"],
    "keywords": ["keyword1", "keyword2"],
    "definitions": {{"term1": "definition1", "term2": "definition2"}},
    "formulas": ["formula1", "formula2"],
    "content": "Detailed content about this topic"
  }}
]

Transcript:
{transcript}

Return ONLY the JSON array, no additional text."""
        
        try:
            # Generate content with retry logic
            response_text = self._call_gemini_api(prompt)
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Find the first newline after ```
                start = response_text.find('\n') + 1
                # Find the last ```
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
            
            # Parse JSON
            topics_data = json.loads(response_text)
            
            # Convert to Topic objects
            topics = []
            for topic_dict in topics_data:
                topic = Topic(
                    title=topic_dict.get('title', ''),
                    subtopics=topic_dict.get('subtopics', []),
                    keywords=topic_dict.get('keywords', []),
                    definitions=topic_dict.get('definitions', {}),
                    formulas=topic_dict.get('formulas', []),
                    content=topic_dict.get('content', '')
                )
                topics.append(topic)
            
            log_info(f"Successfully extracted {len(topics)} topics from transcript")
            return topics
        
        except json.JSONDecodeError as e:
            log_error(e, context={"operation": "topic_extraction", "stage": "json_parsing"})
            raise ExternalAPIError(
                service="Gemini AI",
                message=f"Failed to parse response as JSON: {str(e)}",
                original_exception=e
            )
        except Exception as e:
            log_error(e, context={"operation": "topic_extraction"})
            raise ExternalAPIError(
                service="Gemini AI",
                message=str(e),
                original_exception=e
            )
    
    def generate_summary(self, transcript: str) -> str:
        """
        Generate concise summary of main points.
        
        Args:
            transcript: The transcribed text to summarize
            
        Returns:
            Summary text highlighting key learning points
            
        Requirements: 3.1, 3.5
        """
        if not transcript or not transcript.strip():
            return ""
        
        # Create prompt for summarization
        prompt = f"""Summarize the following lecture transcript into a concise summary that highlights the main learning points and key concepts.

The summary should:
- Be 3-5 paragraphs long
- Focus on the most important concepts
- Be clear and easy to understand
- Help students review the material quickly

Transcript:
{transcript}

Summary:"""
        
        try:
            # Generate content with retry logic
            summary = self._call_gemini_api(prompt)
            log_info("Successfully generated summary from transcript")
            return summary
        
        except Exception as e:
            log_error(e, context={"operation": "summarization"})
            raise ExternalAPIError(
                service="Gemini AI",
                message=str(e),
                original_exception=e
            )
    
    def stitch_segments(self, segments: List[str]) -> str:
        """
        Combine segmented transcripts with context preservation.
        
        Uses graceful degradation - if AI fails, returns simple concatenation.
        
        Args:
            segments: List of transcript segments to combine
            
        Returns:
            Combined transcript with smooth transitions
            
        Requirements: 4.3, 7.2
        """
        if not segments:
            return ""
        
        # If only one segment, return it directly
        if len(segments) == 1:
            return segments[0]
        
        # Join segments with spaces
        combined = ' '.join(segment.strip() for segment in segments if segment.strip())
        
        # Create prompt for context-aware stitching
        prompt = f"""The following text is a transcript that was processed in segments. 
Please clean it up by:
1. Removing any duplicate phrases at segment boundaries
2. Ensuring smooth transitions between segments
3. Maintaining the original meaning and content
4. Fixing any obvious transcription errors or awkward phrasing

Original segmented transcript:
{combined}

Cleaned transcript:"""
        
        # Use graceful degradation - if AI fails, return simple concatenation
        stitched = None
        with GracefulDegradation(
            service_name="Gemini AI Stitching",
            fallback_value=combined,
            notify_user=False
        ) as degradation:
            stitched = self._call_gemini_api(prompt)
            log_info("Successfully stitched transcript segments")
        
        result = degradation.get_result(stitched if stitched is not None else combined)
        if result["degraded"]:
            log_warning("Using fallback concatenation for segment stitching")
        
        return result["value"]
    
    def create_study_notes(self, transcript: str) -> StudyNotesData:
        """
        Generate complete structured study notes.
        
        Uses graceful degradation - if AI fails for some components,
        returns partial results with available data.
        
        Args:
            transcript: The transcribed text to process
            
        Returns:
            StudyNotesData object with topics, summary, and key points
            
        Requirements: 3.1, 3.3, 3.5, 7.2
        """
        if not transcript or not transcript.strip():
            return StudyNotesData(topics=[], summary="", key_points=[])
        
        topics = []
        summary = ""
        key_points = []
        
        # Extract topics with graceful degradation
        with GracefulDegradation(
            service_name="Topic Extraction",
            fallback_value=[],
            notify_user=True
        ) as topic_degradation:
            topics = self.extract_topics(transcript)
        
        topic_result = topic_degradation.get_result(topics)
        topics = topic_result["value"]
        
        # Generate summary with graceful degradation
        with GracefulDegradation(
            service_name="Summary Generation",
            fallback_value="",
            notify_user=True
        ) as summary_degradation:
            summary = self.generate_summary(transcript)
        
        summary_result = summary_degradation.get_result(summary)
        summary = summary_result["value"]
        
        # Extract key points with graceful degradation
        with GracefulDegradation(
            service_name="Key Points Extraction",
            fallback_value=[],
            notify_user=True
        ) as keypoints_degradation:
            key_points = self._extract_key_points(transcript)
        
        keypoints_result = keypoints_degradation.get_result(key_points)
        key_points = keypoints_result["value"]
        
        log_info(
            "Study notes generation completed",
            context={
                "topics_count": len(topics),
                "summary_length": len(summary),
                "key_points_count": len(key_points),
                "topics_degraded": topic_result.get("degraded", False),
                "summary_degraded": summary_result.get("degraded", False),
                "keypoints_degraded": keypoints_result.get("degraded", False)
            }
        )
        
        return StudyNotesData(
            topics=topics,
            summary=summary,
            key_points=key_points
        )
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """
        Extract key learning points from transcript.
        
        Args:
            transcript: The transcribed text to analyze
            
        Returns:
            List of key points as strings
        """
        if not transcript or not transcript.strip():
            return []
        
        # Create prompt for key points extraction
        prompt = f"""Extract 5-10 key learning points from the following lecture transcript.

Each key point should be:
- A single, clear statement
- Focused on important concepts or takeaways
- Useful for quick review

Return the result as a JSON array of strings:
["Key point 1", "Key point 2", "Key point 3", ...]

Transcript:
{transcript}

Return ONLY the JSON array, no additional text."""
        
        try:
            # Generate content
            response = self.model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                start = response_text.find('\n') + 1
                end = response_text.rfind('```')
                if end > start:
                    response_text = response_text[start:end].strip()
            
            # Parse JSON
            key_points = json.loads(response_text)
            
            return key_points if isinstance(key_points, list) else []
        
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract points manually
            return self._fallback_extract_key_points(response.text)
        except Exception as e:
            # Return empty list on error
            return []
    
    def _fallback_extract_key_points(self, text: str) -> List[str]:
        """
        Fallback method to extract key points from text.
        
        Args:
            text: Text containing key points
            
        Returns:
            List of extracted key points
        """
        # Try to find numbered or bulleted lists
        lines = text.strip().split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Look for lines starting with numbers, bullets, or dashes
            if line and (
                line[0].isdigit() or 
                line.startswith('-') or 
                line.startswith('•') or
                line.startswith('*')
            ):
                # Remove the prefix
                cleaned = line.lstrip('0123456789.-•* ').strip()
                if cleaned:
                    key_points.append(cleaned)
        
        return key_points[:10]  # Limit to 10 points
