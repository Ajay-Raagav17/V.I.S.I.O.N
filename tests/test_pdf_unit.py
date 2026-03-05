"""Unit tests for PDF generation service."""

import pytest
from datetime import datetime
from services.pdf_service import PDFService
from io import BytesIO
from PyPDF2 import PdfReader


class TestPDFService:
    """Unit tests for PDFService."""
    
    @pytest.fixture
    def pdf_service(self):
        """Create a PDFService instance."""
        return PDFService()
    
    @pytest.fixture
    def sample_topics(self):
        """Sample topics data for testing."""
        return [
            {
                'title': 'Introduction to Python',
                'subtopics': ['Variables', 'Data Types', 'Functions'],
                'keywords': ['python', 'programming', 'syntax'],
                'definitions': {
                    'Variable': 'A named storage location in memory',
                    'Function': 'A reusable block of code'
                },
                'formulas': ['def function_name(parameters):'],
                'content': 'Python is a high-level programming language known for its simplicity and readability.'
            },
            {
                'title': 'Object-Oriented Programming',
                'subtopics': ['Classes', 'Objects', 'Inheritance'],
                'keywords': ['OOP', 'class', 'object', 'inheritance'],
                'definitions': {
                    'Class': 'A blueprint for creating objects',
                    'Object': 'An instance of a class'
                },
                'formulas': ['class ClassName:', '    def __init__(self):'],
                'content': 'OOP is a programming paradigm based on the concept of objects.'
            }
        ]
    
    @pytest.fixture
    def sample_summary(self):
        """Sample summary for testing."""
        return "This lecture covered the fundamentals of Python programming, including variables, data types, and functions. We also explored object-oriented programming concepts such as classes and objects."
    
    @pytest.fixture
    def sample_key_points(self):
        """Sample key points for testing."""
        return [
            "Python is a high-level, interpreted programming language",
            "Variables store data in memory",
            "Functions are reusable blocks of code",
            "Classes are blueprints for creating objects",
            "OOP promotes code reusability and organization"
        ]
    
    def test_pdf_service_initialization(self, pdf_service):
        """
        Test that PDFService initializes correctly.
        
        Requirements: 5.1
        """
        assert pdf_service is not None
        assert pdf_service.styles is not None
        assert 'CustomTitle' in pdf_service.styles
        assert 'SectionHeading' in pdf_service.styles
        assert 'TopicTitle' in pdf_service.styles
    
    def test_generate_pdf_creates_valid_pdf(self, pdf_service, sample_topics, sample_summary, sample_key_points):
        """
        Test PDF creation from study notes.
        
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=sample_topics,
            summary=sample_summary,
            key_points=sample_key_points,
            title="Python Programming Basics",
            date=datetime(2024, 1, 15)
        )
        
        # Verify PDF was created
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify it's a valid PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        assert len(pdf_reader.pages) > 0
    
    def test_pdf_structure_contains_all_sections(self, pdf_service, sample_topics, sample_summary, sample_key_points):
        """
        Test PDF structure and sections.
        
        Requirements: 5.2, 5.3, 5.4
        """
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=sample_topics,
            summary=sample_summary,
            key_points=sample_key_points,
            title="Python Programming Basics",
            date=datetime(2024, 1, 15)
        )
        
        # Parse PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        
        # Extract all text
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Verify all required sections are present
        # Requirement 5.2: Topic-wise notes
        assert "Topic-Wise Notes" in full_text
        assert "Introduction to Python" in full_text
        assert "Object-Oriented Programming" in full_text
        
        # Requirement 5.3: Summary section
        assert "Summary" in full_text
        assert "fundamentals of Python" in full_text or "Python programming" in full_text
        
        # Requirement 5.4: Key points list
        assert "Key Points" in full_text
        assert "high-level" in full_text or "interpreted" in full_text
    
    def test_pdf_contains_lecture_metadata(self, pdf_service, sample_topics, sample_summary, sample_key_points):
        """
        Test that PDF includes lecture title and date in header.
        
        Requirements: 5.1
        """
        title = "Advanced Python Concepts"
        date = datetime(2024, 3, 20)
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=sample_topics,
            summary=sample_summary,
            key_points=sample_key_points,
            title=title,
            date=date
        )
        
        # Parse PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        first_page_text = pdf_reader.pages[0].extract_text()
        
        # Verify title is in the PDF
        assert title in first_page_text
        
        # Verify date is in the PDF
        assert "March 20, 2024" in first_page_text
    
    def test_pdf_topic_formatting(self, pdf_service, sample_topics, sample_summary, sample_key_points):
        """
        Test that topics are properly formatted in PDF.
        
        Requirements: 5.2
        """
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=sample_topics,
            summary=sample_summary,
            key_points=sample_key_points,
            title="Test Lecture",
            date=datetime(2024, 1, 1)
        )
        
        # Parse PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Verify topic components are present
        # Topic titles
        assert "Introduction to Python" in full_text
        assert "Object-Oriented Programming" in full_text
        
        # Subtopics
        assert "Variables" in full_text or "Subtopics" in full_text
        
        # Keywords
        assert "python" in full_text.lower() or "Keywords" in full_text
        
        # Definitions
        assert "Variable" in full_text or "Definitions" in full_text
        
        # Content
        assert "programming language" in full_text.lower()
    
    def test_format_topics_method(self, pdf_service):
        """
        Test the format_topics method directly.
        
        Requirements: 5.2
        """
        topic = {
            'title': 'Test Topic',
            'subtopics': ['Subtopic 1', 'Subtopic 2'],
            'keywords': ['keyword1', 'keyword2'],
            'definitions': {'Term': 'Definition'},
            'formulas': ['formula = x + y'],
            'content': 'This is test content.'
        }
        
        # Format the topic
        elements = pdf_service.format_topics(topic)
        
        # Verify elements were created
        assert elements is not None
        assert len(elements) > 0
        assert isinstance(elements, list)
    
    def test_pdf_with_empty_optional_fields(self, pdf_service):
        """
        Test PDF generation with minimal data (empty optional fields).
        
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        # Create topic with minimal data
        minimal_topics = [
            {
                'title': 'Minimal Topic',
                'subtopics': [],
                'keywords': [],
                'definitions': {},
                'formulas': [],
                'content': 'Minimal content.'
            }
        ]
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=minimal_topics,
            summary="Minimal summary.",
            key_points=["One key point"],
            title="Minimal Lecture",
            date=datetime(2024, 1, 1)
        )
        
        # Verify PDF was created successfully
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify it's a valid PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        assert len(pdf_reader.pages) > 0
    
    def test_pdf_with_multiple_topics(self, pdf_service):
        """
        Test PDF generation with multiple topics.
        
        Requirements: 5.2
        """
        # Create multiple topics
        topics = [
            {
                'title': f'Topic {i}',
                'subtopics': [f'Subtopic {i}.1', f'Subtopic {i}.2'],
                'keywords': [f'keyword{i}'],
                'definitions': {f'Term{i}': f'Definition{i}'},
                'formulas': [f'formula{i}'],
                'content': f'Content for topic {i}.'
            }
            for i in range(1, 6)
        ]
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=topics,
            summary="Summary of multiple topics.",
            key_points=["Point 1", "Point 2", "Point 3"],
            title="Multi-Topic Lecture",
            date=datetime(2024, 1, 1)
        )
        
        # Verify PDF was created
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Parse and verify content
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Verify at least some topics are present
        assert "Topic 1" in full_text
        assert "Topic" in full_text  # At least the word "Topic" should appear
    
    def test_pdf_with_special_characters(self, pdf_service):
        """
        Test PDF generation with special characters in content.
        
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        topics = [
            {
                'title': 'Special Characters: & < > " \'',
                'subtopics': ['Math: α β γ δ'],
                'keywords': ['special', 'unicode'],
                'definitions': {'Symbol': 'A special character like © or ®'},
                'formulas': ['E = mc²', 'π ≈ 3.14159'],
                'content': 'Content with special chars: & < > " \' © ® ™'
            }
        ]
        
        # Generate PDF (should not crash)
        pdf_bytes = pdf_service.generate_pdf(
            topics=topics,
            summary="Summary with special chars: & < > \" '",
            key_points=["Point with © symbol"],
            title="Special Characters Test",
            date=datetime(2024, 1, 1)
        )
        
        # Verify PDF was created
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify it's a valid PDF
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        assert len(pdf_reader.pages) > 0
