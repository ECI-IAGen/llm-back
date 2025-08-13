"""
Feedback DTO for handling feedback data.
"""

from dataclasses import dataclass
from typing import Optional, Union, List
from datetime import datetime
from .base import BaseDTO
from .utils import DateTimeUtils


@dataclass
class FeedbackDTO(BaseDTO):
    """
    Data Transfer Object for Feedback entities.
    
    Attributes:
        id: Unique identifier for the feedback
        submission_id: ID of the associated submission
        feedback_type: Type of feedback (e.g., 'automated', 'manual', 'peer')
        content: Main feedback content
        feedback_date: Timestamp when feedback was created
        strengths: Strengths identified in the submission
        improvements: Areas for improvement identified
        team_name: Helper field for display purposes
        assignment_title: Helper field for display purposes
    """
    
    id: Optional[int] = None
    submission_id: Optional[int] = None
    feedback_type: Optional[str] = None
    content: Optional[str] = None
    feedback_date: Optional[datetime] = None
    
    # Feedback components
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    
    # Helper fields for display
    team_name: Optional[str] = None
    assignment_title: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing for date conversion."""
        # Convert feedback_date if it's in array format
        if isinstance(self.feedback_date, list):
            self.feedback_date = DateTimeUtils.from_array(self.feedback_date)
        elif isinstance(self.feedback_date, str):
            self.feedback_date = DateTimeUtils.from_iso_string(self.feedback_date)
    
    @classmethod
    def create_structured(cls, submission_id: int, feedback_type: str, content: str,
                         feedback_date: Union[datetime, List[int], str] = None,
                         team_name: str = None, assignment_title: str = None) -> 'FeedbackDTO':
        """
        Factory method for creating structured feedback.
        
        Args:
            submission_id: Associated submission ID
            feedback_type: Type of feedback
            content: Feedback content
            feedback_date: Feedback timestamp
            team_name: Team name for display
            assignment_title: Assignment title for display
            
        Returns:
            FeedbackDTO instance
        """
        return cls(
            submission_id=submission_id,
            feedback_type=feedback_type,
            content=content,
            feedback_date=DateTimeUtils.parse_flexible_datetime(feedback_date) or datetime.now(),
            team_name=team_name,
            assignment_title=assignment_title
        )
    
    @classmethod
    def create_with_components(cls, submission_id: int, strengths: str = None, 
                              improvements: str = None, feedback_type: str = None,
                              feedback_date: Union[datetime, List[int], str] = None,
                              team_name: str = None, assignment_title: str = None) -> 'FeedbackDTO':
        """
        Factory method for creating feedback with strengths and improvements components.
        
        Args:
            submission_id: Associated submission ID
            strengths: Strengths identified
            improvements: Areas for improvement
            feedback_type: Type of feedback
            feedback_date: Feedback timestamp
            team_name: Team name for display
            assignment_title: Assignment title for display
            
        Returns:
            FeedbackDTO instance
        """
        # Combine strengths and improvements into structured content
        content_parts = []
        if strengths:
            content_parts.append(f"**Fortalezas:** {strengths}")
        if improvements:
            content_parts.append(f"**Áreas de Mejora:** {improvements}")
        
        content = "\n\n".join(content_parts) if content_parts else None
        
        return cls(
            submission_id=submission_id,
            feedback_type=feedback_type or "structured",
            content=content,
            feedback_date=DateTimeUtils.parse_flexible_datetime(feedback_date) or datetime.now(),
            strengths=strengths,
            improvements=improvements,
            team_name=team_name,
            assignment_title=assignment_title
        )
    
    @property
    def is_complete(self) -> bool:
        """Check if feedback has all required fields."""
        return all([
            self.submission_id is not None,
            (self.content is not None or any([self.strengths, self.improvements])),
            self.feedback_date is not None
        ])
    
    @property
    def has_components(self) -> bool:
        """Check if feedback uses strengths/improvements components."""
        return any([self.strengths, self.improvements])
    
    def get_consolidated_content(self) -> str:
        """Get consolidated feedback content including component fields."""
        if self.content and not self.has_components:
            return self.content
        
        # If using components or both formats, combine them
        parts = []
        if self.content:
            parts.append(self.content)
        
        if self.strengths:
            parts.append(f"Fortalezas: {self.strengths}")
        if self.improvements:
            parts.append(f"Mejoras: {self.improvements}")
        
        return "\n\n".join(parts)
    
    def get_feedback_summary(self) -> str:
        """Get a human-readable summary of the feedback."""
        date_str = self.feedback_date.strftime('%Y-%m-%d %H:%M') if self.feedback_date else 'Unknown Date'
        return (f"Feedback {self.id or 'New'}: {self.feedback_type or 'Unknown Type'} "
                f"for {self.assignment_title or 'Unknown Assignment'} "
                f"({self.team_name or 'Unknown Team'}) on {date_str}")
