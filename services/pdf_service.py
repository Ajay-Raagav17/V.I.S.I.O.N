"""PDF generation service for creating formatted study notes PDFs."""

from typing import List, Dict, Optional
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import html

from services.error_handling import (
    ProcessingError,
    log_error,
    log_info
)


class PDFService:
    """
    Service for generating formatted PDF documents from study notes.
    
    Provides methods for:
    - PDF generation from study notes
    - Topic formatting for PDF layout
    - Lecture metadata inclusion
    
    Requirements: 5.1, 5.2, 5.3, 5.4
    """
    
    def __init__(self):
        """Initialize the PDF service."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text for PDF generation by escaping HTML special characters.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text safe for PDF generation
        """
        if not text:
            return ""
        # Escape HTML special characters
        return html.escape(str(text))
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for PDF formatting."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Lecture metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Topic title style
        self.styles.add(ParagraphStyle(
            name='TopicTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Subtopic style
        self.styles.add(ParagraphStyle(
            name='Subtopic',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#555555'),
            spaceAfter=6,
            leftIndent=20,
            fontName='Helvetica-Bold'
        ))
        
        # Content style
        self.styles.add(ParagraphStyle(
            name='Content',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=14
        ))
        
        # Keyword style
        self.styles.add(ParagraphStyle(
            name='Keyword',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2980b9'),
            spaceAfter=4,
            leftIndent=20
        ))
        
        # Definition style
        self.styles.add(ParagraphStyle(
            name='CustomDefinition',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#444444'),
            spaceAfter=6,
            leftIndent=30
        ))
        
        # Formula style
        self.styles.add(ParagraphStyle(
            name='Formula',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#8e44ad'),
            spaceAfter=6,
            leftIndent=20,
            fontName='Courier'
        ))
        
        # Key point style
        self.styles.add(ParagraphStyle(
            name='KeyPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#27ae60'),
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10
        ))
    
    def generate_pdf(
        self,
        topics: List[Dict],
        summary: str,
        key_points: List[str],
        title: str,
        date: datetime
    ) -> bytes:
        """
        Create formatted PDF from study notes.
        
        Args:
            topics: List of topic dictionaries with structure
            summary: Summary text of the lecture
            key_points: List of key learning points
            title: Lecture title
            date: Lecture date
            
        Returns:
            PDF file as bytes
            
        Raises:
            ProcessingError: If PDF generation fails
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 7.4
        """
        try:
            # Create a BytesIO buffer to hold the PDF
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Add header with lecture metadata
            elements.extend(self._create_header(title, date))
            
            # Add summary section
            if summary:
                elements.extend(self._create_summary_section(summary))
            
            # Add key points section
            if key_points:
                elements.extend(self._create_key_points_section(key_points))
            
            # Add topic-wise notes section
            if topics:
                elements.extend(self._create_topics_section(topics))
            
            # Build the PDF
            doc.build(elements)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            log_info(
                "PDF generated successfully",
                context={
                    "title": title,
                    "topics_count": len(topics),
                    "key_points_count": len(key_points),
                    "pdf_size_bytes": len(pdf_bytes)
                }
            )
            
            return pdf_bytes
            
        except Exception as e:
            log_error(e, context={
                "operation": "pdf_generation",
                "title": title,
                "topics_count": len(topics) if topics else 0
            })
            raise ProcessingError(
                operation="PDF",
                message=f"Failed to generate PDF: {str(e)}",
                details={"title": title},
                original_exception=e
            )
    
    def _create_header(self, title: str, date: datetime) -> List:
        """
        Create PDF header with lecture metadata.
        
        Args:
            title: Lecture title
            date: Lecture date
            
        Returns:
            List of flowable elements for the header
        """
        elements = []
        
        # Add title
        title_para = Paragraph(self._sanitize_text(title), self.styles['CustomTitle'])
        elements.append(title_para)
        
        # Add date
        date_str = date.strftime("%B %d, %Y")
        date_para = Paragraph(f"Date: {date_str}", self.styles['Metadata'])
        elements.append(date_para)
        
        # Add spacer
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_summary_section(self, summary: str) -> List:
        """
        Create summary section for PDF.
        
        Args:
            summary: Summary text
            
        Returns:
            List of flowable elements for the summary section
            
        Requirements: 5.3
        """
        elements = []
        
        # Add section heading
        heading = Paragraph("Summary", self.styles['SectionHeading'])
        elements.append(heading)
        
        # Add summary content
        summary_para = Paragraph(self._sanitize_text(summary), self.styles['Content'])
        elements.append(summary_para)
        
        # Add spacer
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_key_points_section(self, key_points: List[str]) -> List:
        """
        Create key points section for PDF.
        
        Args:
            key_points: List of key learning points
            
        Returns:
            List of flowable elements for the key points section
            
        Requirements: 5.4
        """
        elements = []
        
        # Add section heading
        heading = Paragraph("Key Points", self.styles['SectionHeading'])
        elements.append(heading)
        
        # Add each key point
        for i, point in enumerate(key_points, 1):
            point_text = f"{i}. {self._sanitize_text(point)}"
            point_para = Paragraph(point_text, self.styles['KeyPoint'])
            elements.append(point_para)
        
        # Add spacer
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_topics_section(self, topics: List[Dict]) -> List:
        """
        Create topic-wise notes section for PDF.
        
        Args:
            topics: List of topic dictionaries
            
        Returns:
            List of flowable elements for the topics section
            
        Requirements: 5.2
        """
        elements = []
        
        # Add section heading
        heading = Paragraph("Topic-Wise Notes", self.styles['SectionHeading'])
        elements.append(heading)
        
        # Add each topic
        for topic in topics:
            elements.extend(self.format_topics(topic))
        
        return elements
    
    def format_topics(self, topic: Dict) -> List:
        """
        Format topics for PDF layout.
        
        Args:
            topic: Topic dictionary with structure
            
        Returns:
            List of flowable elements for the topic
            
        Requirements: 5.2
        """
        elements = []
        
        # Add topic title
        title = topic.get('title', 'Untitled Topic')
        title_para = Paragraph(self._sanitize_text(title), self.styles['TopicTitle'])
        elements.append(title_para)
        
        # Add content
        content = topic.get('content', '')
        if content:
            content_para = Paragraph(self._sanitize_text(content), self.styles['Content'])
            elements.append(content_para)
            elements.append(Spacer(1, 0.1 * inch))
        
        # Add subtopics
        subtopics = topic.get('subtopics', [])
        if subtopics:
            subtopic_heading = Paragraph("<b>Subtopics:</b>", self.styles['Content'])
            elements.append(subtopic_heading)
            for subtopic in subtopics:
                subtopic_para = Paragraph(f"• {self._sanitize_text(subtopic)}", self.styles['Subtopic'])
                elements.append(subtopic_para)
            elements.append(Spacer(1, 0.1 * inch))
        
        # Add keywords
        keywords = topic.get('keywords', [])
        if keywords:
            keyword_heading = Paragraph("<b>Keywords:</b>", self.styles['Content'])
            elements.append(keyword_heading)
            keywords_text = ", ".join(self._sanitize_text(k) for k in keywords)
            keywords_para = Paragraph(keywords_text, self.styles['Keyword'])
            elements.append(keywords_para)
            elements.append(Spacer(1, 0.1 * inch))
        
        # Add definitions
        definitions = topic.get('definitions', {})
        if definitions:
            def_heading = Paragraph("<b>Definitions:</b>", self.styles['Content'])
            elements.append(def_heading)
            for term, definition in definitions.items():
                def_text = f"<b>{self._sanitize_text(term)}:</b> {self._sanitize_text(definition)}"
                def_para = Paragraph(def_text, self.styles['CustomDefinition'])
                elements.append(def_para)
            elements.append(Spacer(1, 0.1 * inch))
        
        # Add formulas
        formulas = topic.get('formulas', [])
        if formulas:
            formula_heading = Paragraph("<b>Formulas:</b>", self.styles['Content'])
            elements.append(formula_heading)
            for formula in formulas:
                formula_para = Paragraph(self._sanitize_text(formula), self.styles['Formula'])
                elements.append(formula_para)
            elements.append(Spacer(1, 0.1 * inch))
        
        # Add spacer between topics
        elements.append(Spacer(1, 0.15 * inch))
        
        return elements
