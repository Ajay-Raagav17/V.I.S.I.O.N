"""Notes endpoints for retrieving processed notes and generating PDFs."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import json

from database.connection import get_db
from models.lecture import Lecture
from models.study_notes import StudyNotes
from services.pdf_service import PDFService

router = APIRouter(prefix="/api/notes", tags=["notes"])
pdf_service = PDFService()


@router.get("/{lecture_id}")
async def get_notes(lecture_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieve processed notes for a specific lecture.
    
    Args:
        lecture_id: UUID of the lecture
        db: Database session
        
    Returns:
        Dictionary containing lecture and study notes data
        
    Raises:
        HTTPException: 404 if lecture or notes not found
        
    Requirements: 5.5
    """
    # Retrieve lecture
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Retrieve study notes
    notes = db.query(StudyNotes).filter(StudyNotes.lecture_id == lecture_id).first()
    if not notes:
        raise HTTPException(status_code=404, detail="Study notes not found for this lecture")
    
    # Parse JSON fields
    topics = json.loads(notes.topics) if isinstance(notes.topics, str) else notes.topics
    key_points = json.loads(notes.key_points) if isinstance(notes.key_points, str) else notes.key_points
    
    return {
        "lecture": {
            "id": str(lecture.id),
            "title": lecture.title,
            "lecture_type": lecture.lecture_type.value if hasattr(lecture.lecture_type, 'value') else lecture.lecture_type,
            "created_at": lecture.created_at.isoformat(),
            "duration_seconds": lecture.duration_seconds,
            "processing_status": lecture.processing_status.value if hasattr(lecture.processing_status, 'value') else lecture.processing_status
        },
        "notes": {
            "id": str(notes.id),
            "topics": topics,
            "summary": notes.summary,
            "key_points": key_points,
            "created_at": notes.created_at.isoformat()
        }
    }


@router.get("/{lecture_id}/pdf")
async def download_pdf(lecture_id: str, db: Session = Depends(get_db)):
    """
    Generate and download PDF for a specific lecture's notes.
    
    Args:
        lecture_id: UUID of the lecture
        db: Database session
        
    Returns:
        PDF file as bytes with appropriate headers
        
    Raises:
        HTTPException: 404 if lecture or notes not found
        HTTPException: 500 if PDF generation fails
        
    Requirements: 5.5
    """
    from fastapi.responses import Response
    
    # Retrieve lecture
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Retrieve study notes
    notes = db.query(StudyNotes).filter(StudyNotes.lecture_id == lecture_id).first()
    if not notes:
        raise HTTPException(status_code=404, detail="Study notes not found for this lecture")
    
    try:
        # Parse JSON fields
        topics = json.loads(notes.topics) if isinstance(notes.topics, str) else notes.topics
        key_points = json.loads(notes.key_points) if isinstance(notes.key_points, str) else notes.key_points
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            topics=topics,
            summary=notes.summary,
            key_points=key_points,
            title=lecture.title,
            date=lecture.created_at
        )
        
        # Create filename
        safe_title = "".join(c for c in lecture.title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}_{lecture.created_at.strftime('%Y%m%d')}.pdf"
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
