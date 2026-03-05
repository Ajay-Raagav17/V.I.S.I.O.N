"""
Unit tests for AI analysis service.

Tests API connection, initialization, and study notes structure validation.
Requirements: 3.1, 3.3, 3.5
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from services.ai_analysis_service import AIAnalysisService, Topic, StudyNotesData
import json


@pytest.fixture
def mock_genai():
    """Mock the genai module."""
    with patch('services.ai_analysis_service.genai') as mock:
        yield mock


@pytest.fixture
def ai_service(mock_genai):
    """Create an AIAnalysisService with mocked API."""
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    # Mock the GenerativeModel
    mock_model_instance = Mock()
    mock_genai.GenerativeModel.return_value = mock_model_instance
    
    service = AIAnalysisService()
    service._mock_model = mock_model_instance
    
    yield service
    
    # Cleanup
    os.environ.pop('GEMINI_API_KEY', None)


def test_initialization_requires_api_key(mock_genai):
    """
    Test that AIAnalysisService initialization requires GEMINI_API_KEY.
    
    Requirements: 8.5
    """
    # Remove API key if it exists
    os.environ.pop('GEMINI_API_KEY', None)
    
    # Should raise ValueError when API key is missing
    with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable not set"):
        AIAnalysisService()


def test_initialization_configures_api(mock_genai):
    """
    Test that AIAnalysisService properly configures the Gemini API.
    
    Requirements: 8.5
    """
    os.environ['GEMINI_API_KEY'] = 'test_key_123'
    
    service = AIAnalysisService()
    
    # Verify API was configured with the key
    mock_genai.configure.assert_called_once_with(api_key='test_key_123')
    
    # Verify model was initialized
    mock_genai.GenerativeModel.assert_called_once_with('gemini-pro')
    
    # Cleanup
    os.environ.pop('GEMINI_API_KEY', None)


def test_extract_topics_with_valid_response(ai_service):
    """
    Test extract_topics with a valid JSON response.
    
    Requirements: 3.1, 3.3
    """
    # Mock response
    mock_response = Mock()
    mock_response.text = json.dumps([
        {
            "title": "Introduction to Python",
            "subtopics": ["Variables", "Data Types"],
            "keywords": ["python", "programming"],
            "definitions": {"variable": "A named storage location"},
            "formulas": [],
            "content": "Python is a programming language."
        },
        {
            "title": "Control Flow",
            "subtopics": ["If statements", "Loops"],
            "keywords": ["if", "for", "while"],
            "definitions": {"loop": "Repeated execution"},
            "formulas": ["for i in range(n)"],
            "content": "Control flow manages execution order."
        }
    ])
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    transcript = "This is a lecture about Python programming."
    topics = ai_service.extract_topics(transcript)
    
    # Assertions
    assert len(topics) == 2
    assert isinstance(topics[0], Topic)
    assert topics[0].title == "Introduction to Python"
    assert "Variables" in topics[0].subtopics
    assert "python" in topics[0].keywords
    assert "variable" in topics[0].definitions
    assert topics[0].content == "Python is a programming language."
    
    assert topics[1].title == "Control Flow"
    assert len(topics[1].formulas) == 1


def test_extract_topics_with_markdown_wrapped_json(ai_service):
    """
    Test extract_topics handles JSON wrapped in markdown code blocks.
    
    Requirements: 3.1, 3.3
    """
    # Mock response with markdown
    mock_response = Mock()
    mock_response.text = """```json
[
    {
        "title": "Test Topic",
        "subtopics": ["Sub1"],
        "keywords": ["key1"],
        "definitions": {},
        "formulas": [],
        "content": "Test content"
    }
]
```"""
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    topics = ai_service.extract_topics("Test transcript")
    
    # Assertions
    assert len(topics) == 1
    assert topics[0].title == "Test Topic"


def test_extract_topics_with_empty_transcript(ai_service):
    """
    Test extract_topics with empty transcript returns empty list.
    
    Requirements: 3.1, 3.3
    """
    # Test with empty string
    topics = ai_service.extract_topics("")
    assert topics == []
    
    # Test with whitespace only
    topics = ai_service.extract_topics("   \n  \t  ")
    assert topics == []


def test_extract_topics_handles_api_error(ai_service):
    """
    Test extract_topics handles API errors gracefully.
    
    Requirements: 3.1, 7.2
    """
    from services.error_handling import ExternalAPIError
    
    # Mock API error
    ai_service._mock_model.generate_content.side_effect = Exception("API Error")
    
    # Should raise ExternalAPIError
    with pytest.raises(ExternalAPIError, match="Gemini AI"):
        ai_service.extract_topics("Test transcript")


def test_extract_topics_handles_invalid_json(ai_service):
    """
    Test extract_topics handles invalid JSON response.
    
    Requirements: 3.1, 7.2
    """
    from services.error_handling import ExternalAPIError
    
    # Mock response with invalid JSON
    mock_response = Mock()
    mock_response.text = "This is not valid JSON"
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Should raise ExternalAPIError
    with pytest.raises(ExternalAPIError, match="Failed to parse response as JSON"):
        ai_service.extract_topics("Test transcript")


def test_generate_summary_with_valid_response(ai_service):
    """
    Test generate_summary returns a summary string.
    
    Requirements: 3.1, 3.5
    """
    # Mock response
    mock_response = Mock()
    mock_response.text = "This lecture covered Python basics including variables and control flow."
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    transcript = "Python lecture content here."
    summary = ai_service.generate_summary(transcript)
    
    # Assertions
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert summary == "This lecture covered Python basics including variables and control flow."


def test_generate_summary_with_empty_transcript(ai_service):
    """
    Test generate_summary with empty transcript returns empty string.
    
    Requirements: 3.1, 3.5
    """
    # Test with empty string
    summary = ai_service.generate_summary("")
    assert summary == ""
    
    # Test with whitespace only
    summary = ai_service.generate_summary("   \n  ")
    assert summary == ""


def test_generate_summary_handles_api_error(ai_service):
    """
    Test generate_summary handles API errors.
    
    Requirements: 3.1, 7.2
    """
    from services.error_handling import ExternalAPIError
    
    # Mock API error
    ai_service._mock_model.generate_content.side_effect = Exception("API Error")
    
    # Should raise ExternalAPIError
    with pytest.raises(ExternalAPIError, match="Gemini AI"):
        ai_service.generate_summary("Test transcript")


def test_stitch_segments_with_multiple_segments(ai_service):
    """
    Test stitch_segments combines segments properly.
    
    Requirements: 4.3
    """
    # Mock response
    mock_response = Mock()
    mock_response.text = "This is a cleaned transcript with smooth transitions."
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    segments = [
        "This is segment one.",
        "This is segment two.",
        "This is segment three."
    ]
    result = ai_service.stitch_segments(segments)
    
    # Assertions
    assert isinstance(result, str)
    assert len(result) > 0


def test_stitch_segments_with_single_segment(ai_service):
    """
    Test stitch_segments with single segment returns it directly.
    
    Requirements: 4.3
    """
    # Single segment should be returned without API call
    segments = ["This is the only segment."]
    result = ai_service.stitch_segments(segments)
    
    assert result == "This is the only segment."


def test_stitch_segments_with_empty_list(ai_service):
    """
    Test stitch_segments with empty list returns empty string.
    
    Requirements: 4.3
    """
    result = ai_service.stitch_segments([])
    assert result == ""


def test_stitch_segments_handles_api_error(ai_service):
    """
    Test stitch_segments falls back to simple concatenation on API error.
    
    Requirements: 4.3, 7.2
    """
    # Mock API error - the _call_gemini_api method is what gets called
    ai_service._mock_model.generate_content.side_effect = Exception("API Error")
    
    # Should fall back to simple concatenation due to graceful degradation
    segments = ["Segment one.", "Segment two."]
    result = ai_service.stitch_segments(segments)
    
    # Should return concatenated segments (fallback behavior)
    assert isinstance(result, str)
    assert "Segment one" in result
    assert "Segment two" in result


def test_create_study_notes_complete_structure(ai_service):
    """
    Test create_study_notes returns complete StudyNotesData structure.
    
    Requirements: 3.1, 3.3, 3.5
    """
    # Mock responses for all three API calls
    mock_topic_response = Mock()
    mock_topic_response.text = json.dumps([
        {
            "title": "Test Topic",
            "subtopics": ["Sub1", "Sub2"],
            "keywords": ["key1", "key2"],
            "definitions": {"term1": "def1"},
            "formulas": ["f=ma"],
            "content": "Topic content"
        }
    ])
    
    mock_summary_response = Mock()
    mock_summary_response.text = "This is the summary."
    
    mock_key_points_response = Mock()
    mock_key_points_response.text = json.dumps([
        "Key point 1",
        "Key point 2",
        "Key point 3"
    ])
    
    # Set up side_effect to return different responses
    ai_service._mock_model.generate_content.side_effect = [
        mock_topic_response,
        mock_summary_response,
        mock_key_points_response
    ]
    
    # Test
    transcript = "This is a test lecture transcript."
    study_notes = ai_service.create_study_notes(transcript)
    
    # Assertions - verify complete structure
    assert isinstance(study_notes, StudyNotesData)
    
    # Check topics
    assert isinstance(study_notes.topics, list)
    assert len(study_notes.topics) == 1
    assert isinstance(study_notes.topics[0], Topic)
    assert study_notes.topics[0].title == "Test Topic"
    assert len(study_notes.topics[0].subtopics) == 2
    assert len(study_notes.topics[0].keywords) == 2
    assert "term1" in study_notes.topics[0].definitions
    assert len(study_notes.topics[0].formulas) == 1
    assert study_notes.topics[0].content == "Topic content"
    
    # Check summary
    assert isinstance(study_notes.summary, str)
    assert study_notes.summary == "This is the summary."
    
    # Check key points
    assert isinstance(study_notes.key_points, list)
    assert len(study_notes.key_points) == 3
    assert "Key point 1" in study_notes.key_points


def test_create_study_notes_with_empty_transcript(ai_service):
    """
    Test create_study_notes with empty transcript returns empty structure.
    
    Requirements: 3.1, 3.3, 3.5
    """
    # Test with empty transcript
    study_notes = ai_service.create_study_notes("")
    
    # Should return valid but empty structure
    assert isinstance(study_notes, StudyNotesData)
    assert study_notes.topics == []
    assert study_notes.summary == ""
    assert study_notes.key_points == []


def test_topic_dataclass_structure():
    """
    Test Topic dataclass has all required fields.
    
    Requirements: 3.3
    """
    topic = Topic(
        title="Test",
        subtopics=["Sub1"],
        keywords=["key1"],
        definitions={"term": "def"},
        formulas=["f=ma"],
        content="Content"
    )
    
    assert topic.title == "Test"
    assert topic.subtopics == ["Sub1"]
    assert topic.keywords == ["key1"]
    assert topic.definitions == {"term": "def"}
    assert topic.formulas == ["f=ma"]
    assert topic.content == "Content"


def test_study_notes_data_structure():
    """
    Test StudyNotesData dataclass has all required fields.
    
    Requirements: 3.3, 3.5
    """
    topic = Topic(
        title="Test",
        subtopics=[],
        keywords=[],
        definitions={},
        formulas=[],
        content=""
    )
    
    notes = StudyNotesData(
        topics=[topic],
        summary="Summary",
        key_points=["Point 1"]
    )
    
    assert len(notes.topics) == 1
    assert notes.summary == "Summary"
    assert notes.key_points == ["Point 1"]


def test_extract_key_points_with_valid_json(ai_service):
    """
    Test _extract_key_points with valid JSON response.
    
    Requirements: 3.5
    """
    # Mock response
    mock_response = Mock()
    mock_response.text = json.dumps([
        "Key point 1",
        "Key point 2",
        "Key point 3"
    ])
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    key_points = ai_service._extract_key_points("Test transcript")
    
    # Assertions
    assert isinstance(key_points, list)
    assert len(key_points) == 3
    assert "Key point 1" in key_points


def test_extract_key_points_with_markdown_wrapped_json(ai_service):
    """
    Test _extract_key_points handles markdown-wrapped JSON.
    
    Requirements: 3.5
    """
    # Mock response with markdown
    mock_response = Mock()
    mock_response.text = """```json
["Point 1", "Point 2"]
```"""
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    key_points = ai_service._extract_key_points("Test transcript")
    
    # Assertions
    assert len(key_points) == 2
    assert "Point 1" in key_points


def test_extract_key_points_fallback_on_json_error(ai_service):
    """
    Test _extract_key_points uses fallback on JSON parse error.
    
    Requirements: 3.5
    """
    # Mock response with non-JSON format
    mock_response = Mock()
    mock_response.text = """
1. First key point
2. Second key point
- Third key point
"""
    
    ai_service._mock_model.generate_content.return_value = mock_response
    
    # Test
    key_points = ai_service._extract_key_points("Test transcript")
    
    # Should use fallback extraction
    assert isinstance(key_points, list)
    assert len(key_points) > 0


def test_extract_key_points_with_empty_transcript(ai_service):
    """
    Test _extract_key_points with empty transcript returns empty list.
    
    Requirements: 3.5
    """
    key_points = ai_service._extract_key_points("")
    assert key_points == []


def test_fallback_extract_key_points():
    """
    Test _fallback_extract_key_points extracts from formatted text.
    
    Requirements: 3.5
    """
    os.environ['GEMINI_API_KEY'] = 'test_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel'):
            service = AIAnalysisService()
    
    os.environ.pop('GEMINI_API_KEY', None)
    
    # Test with numbered list
    text = """
1. First point
2. Second point
3. Third point
"""
    points = service._fallback_extract_key_points(text)
    assert len(points) == 3
    assert "First point" in points
    
    # Test with bullet points
    text = """
- Point A
- Point B
• Point C
* Point D
"""
    points = service._fallback_extract_key_points(text)
    assert len(points) == 4
    
    # Test limiting to 10 points
    text = "\n".join([f"{i}. Point {i}" for i in range(1, 20)])
    points = service._fallback_extract_key_points(text)
    assert len(points) <= 10
