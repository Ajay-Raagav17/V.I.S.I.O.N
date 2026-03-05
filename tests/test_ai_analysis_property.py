"""
Property-based tests for AI analysis service.

**Feature: vision-accessibility, Property 3: Study notes structure completeness**
**Validates: Requirements 3.3, 3.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from services.ai_analysis_service import AIAnalysisService, Topic, StudyNotesData


# Strategy for generating transcript text
transcript_strategy = st.text(min_size=50, max_size=2000).filter(
    lambda x: len(x.strip()) > 0
)

# Strategy for generating topic titles
topic_title_strategy = st.text(min_size=3, max_size=100).filter(
    lambda x: len(x.strip()) > 0
)

# Strategy for generating lists of strings
string_list_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: len(x.strip()) > 0),
    min_size=0,
    max_size=10
)

# Strategy for generating dictionaries
definition_dict_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=30).filter(lambda x: len(x.strip()) > 0),
    values=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
    min_size=0,
    max_size=5
)


def create_mock_topic_response(num_topics: int = 2) -> str:
    """Create a mock JSON response for topic extraction."""
    topics = []
    for i in range(num_topics):
        topics.append({
            "title": f"Topic {i+1}",
            "subtopics": [f"Subtopic {i+1}.1", f"Subtopic {i+1}.2"],
            "keywords": [f"keyword{i+1}a", f"keyword{i+1}b"],
            "definitions": {f"term{i+1}": f"definition{i+1}"},
            "formulas": [f"formula{i+1}"],
            "content": f"Content for topic {i+1}"
        })
    
    import json
    return json.dumps(topics)


def create_mock_summary_response() -> str:
    """Create a mock summary response."""
    return "This is a summary of the lecture covering key concepts and main ideas."


def create_mock_key_points_response() -> str:
    """Create a mock JSON response for key points."""
    key_points = [
        "Key point 1: Important concept",
        "Key point 2: Another important idea",
        "Key point 3: Critical takeaway"
    ]
    import json
    return json.dumps(key_points)


@pytest.fixture
def mock_ai_service():
    """Create an AIAnalysisService with mocked Gemini API."""
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key_for_testing'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            # Create mock response object
            mock_response = Mock()
            mock_response.text = create_mock_topic_response()
            
            # Configure mock model
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
            service._mock_model_instance = mock_instance
            service._mock_response = mock_response
    
    # Restore original key
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    return service


@settings(max_examples=100, deadline=None)
@given(transcript=transcript_strategy)
def test_study_notes_structure_completeness(transcript):
    """
    Property 3: Study notes structure completeness
    
    For any processed transcript, the generated study notes should contain all 
    required structural elements: topics with subtopics, keywords, definitions, 
    formulas, and content text.
    
    **Feature: vision-accessibility, Property 3: Study notes structure completeness**
    **Validates: Requirements 3.3, 3.5**
    """
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            # Create mock responses for different calls
            mock_topic_response = Mock()
            mock_topic_response.text = create_mock_topic_response(num_topics=2)
            
            mock_summary_response = Mock()
            mock_summary_response.text = create_mock_summary_response()
            
            mock_key_points_response = Mock()
            mock_key_points_response.text = create_mock_key_points_response()
            
            # Configure mock to return different responses based on call order
            mock_instance = Mock()
            mock_instance.generate_content.side_effect = [
                mock_topic_response,
                mock_summary_response,
                mock_key_points_response
            ]
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
    
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    # Generate study notes
    study_notes = service.create_study_notes(transcript)
    
    # Property 1: Study notes should be a StudyNotesData object
    assert isinstance(study_notes, StudyNotesData), \
        "create_study_notes should return a StudyNotesData object"
    
    # Property 2: Study notes should have topics field (list)
    assert hasattr(study_notes, 'topics'), \
        "StudyNotesData should have 'topics' attribute"
    assert isinstance(study_notes.topics, list), \
        "topics should be a list"
    
    # Property 3: Study notes should have summary field (string)
    assert hasattr(study_notes, 'summary'), \
        "StudyNotesData should have 'summary' attribute"
    assert isinstance(study_notes.summary, str), \
        "summary should be a string"
    
    # Property 4: Study notes should have key_points field (list)
    assert hasattr(study_notes, 'key_points'), \
        "StudyNotesData should have 'key_points' attribute"
    assert isinstance(study_notes.key_points, list), \
        "key_points should be a list"
    
    # Property 5: Each topic should have all required fields
    for i, topic in enumerate(study_notes.topics):
        assert isinstance(topic, Topic), \
            f"Topic {i} should be a Topic object"
        
        # Check all required fields exist
        assert hasattr(topic, 'title'), \
            f"Topic {i} should have 'title' attribute"
        assert isinstance(topic.title, str), \
            f"Topic {i} title should be a string"
        
        assert hasattr(topic, 'subtopics'), \
            f"Topic {i} should have 'subtopics' attribute"
        assert isinstance(topic.subtopics, list), \
            f"Topic {i} subtopics should be a list"
        
        assert hasattr(topic, 'keywords'), \
            f"Topic {i} should have 'keywords' attribute"
        assert isinstance(topic.keywords, list), \
            f"Topic {i} keywords should be a list"
        
        assert hasattr(topic, 'definitions'), \
            f"Topic {i} should have 'definitions' attribute"
        assert isinstance(topic.definitions, dict), \
            f"Topic {i} definitions should be a dictionary"
        
        assert hasattr(topic, 'formulas'), \
            f"Topic {i} should have 'formulas' attribute"
        assert isinstance(topic.formulas, list), \
            f"Topic {i} formulas should be a list"
        
        assert hasattr(topic, 'content'), \
            f"Topic {i} should have 'content' attribute"
        assert isinstance(topic.content, str), \
            f"Topic {i} content should be a string"


@settings(max_examples=100, deadline=None)
@given(transcript=transcript_strategy)
def test_extract_topics_returns_valid_structure(transcript):
    """
    Property: extract_topics should return a list of Topic objects with all required fields.
    
    For any transcript, the extracted topics should have the complete structure
    defined in the Topic dataclass.
    
    **Feature: vision-accessibility, Property 3: Study notes structure completeness**
    **Validates: Requirements 3.3**
    """
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = create_mock_topic_response(num_topics=3)
            
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
    
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    # Extract topics
    topics = service.extract_topics(transcript)
    
    # Property: Should return a list
    assert isinstance(topics, list), \
        "extract_topics should return a list"
    
    # Property: Each element should be a Topic object with all required fields
    for i, topic in enumerate(topics):
        assert isinstance(topic, Topic), \
            f"Element {i} should be a Topic object"
        
        # Verify all fields exist and have correct types
        assert isinstance(topic.title, str), \
            f"Topic {i} title should be a string"
        assert isinstance(topic.subtopics, list), \
            f"Topic {i} subtopics should be a list"
        assert isinstance(topic.keywords, list), \
            f"Topic {i} keywords should be a list"
        assert isinstance(topic.definitions, dict), \
            f"Topic {i} definitions should be a dict"
        assert isinstance(topic.formulas, list), \
            f"Topic {i} formulas should be a list"
        assert isinstance(topic.content, str), \
            f"Topic {i} content should be a string"


@settings(max_examples=100, deadline=None)
@given(transcript=transcript_strategy)
def test_generate_summary_returns_string(transcript):
    """
    Property: generate_summary should always return a string.
    
    For any transcript, the summary should be a non-None string value.
    
    **Feature: vision-accessibility, Property 3: Study notes structure completeness**
    **Validates: Requirements 3.5**
    """
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = create_mock_summary_response()
            
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
    
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    # Generate summary
    summary = service.generate_summary(transcript)
    
    # Property: Should return a string
    assert isinstance(summary, str), \
        "generate_summary should return a string"
    assert summary is not None, \
        "generate_summary should not return None"


@settings(max_examples=100, deadline=None)
@given(
    segments=st.lists(
        st.text(min_size=10, max_size=200).filter(lambda x: len(x.strip()) > 0),
        min_size=1,
        max_size=10
    )
)
def test_stitch_segments_returns_string(segments):
    """
    Property: stitch_segments should always return a string.
    
    For any list of transcript segments, the stitched result should be a string.
    
    **Feature: vision-accessibility, Property 3: Study notes structure completeness**
    **Validates: Requirements 4.3**
    """
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = ' '.join(segments)
            
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
    
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    # Stitch segments
    result = service.stitch_segments(segments)
    
    # Property: Should return a string
    assert isinstance(result, str), \
        "stitch_segments should return a string"
    assert result is not None, \
        "stitch_segments should not return None"


@settings(max_examples=100, deadline=None)
@given(transcript=st.just(""))
def test_empty_transcript_returns_empty_structure(transcript):
    """
    Property: Empty transcripts should return empty but valid structure.
    
    For an empty transcript, the service should return a valid StudyNotesData
    object with empty fields rather than failing.
    
    **Feature: vision-accessibility, Property 3: Study notes structure completeness**
    **Validates: Requirements 3.3, 3.5**
    """
    import os
    original_key = os.environ.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = 'test_api_key'
    
    with patch('services.ai_analysis_service.genai.configure'):
        with patch('services.ai_analysis_service.genai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_model.return_value = mock_instance
            
            service = AIAnalysisService()
    
    if original_key:
        os.environ['GEMINI_API_KEY'] = original_key
    else:
        os.environ.pop('GEMINI_API_KEY', None)
    
    # Generate study notes for empty transcript
    study_notes = service.create_study_notes(transcript)
    
    # Property: Should return valid structure even for empty input
    assert isinstance(study_notes, StudyNotesData), \
        "Should return StudyNotesData even for empty transcript"
    assert isinstance(study_notes.topics, list), \
        "topics should be a list"
    assert isinstance(study_notes.summary, str), \
        "summary should be a string"
    assert isinstance(study_notes.key_points, list), \
        "key_points should be a list"
    
    # For empty transcript, fields should be empty
    assert len(study_notes.topics) == 0, \
        "Empty transcript should have no topics"
    assert study_notes.summary == "", \
        "Empty transcript should have empty summary"
    assert len(study_notes.key_points) == 0, \
        "Empty transcript should have no key points"
