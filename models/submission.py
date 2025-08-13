"""
Submission DTO for handling submission data.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List
from datetime import datetime
from .base import BaseDTO
from .utils import DateTimeUtils


@dataclass
class SubmissionDTO(BaseDTO):
    """
    Data Transfer Object for Submission entities.
    
    Attributes:
        id: Unique identifier for the submission
        assignment_id: ID of the associated assignment
        assignment_title: Title of the assignment
        team_id: ID of the team that made the submission
        team_name: Name of the team
        submitted_at: Timestamp when submission was made
        file_url: URL to the submitted file
        class_id: ID of the class (optional)
        class_name: Name of the class (optional)
    """
    
    id: Optional[int] = None
    assignment_id: Optional[int] = None
    assignment_title: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    file_url: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing for date conversion."""
        # Convert submitted_at if it's in array format
        if isinstance(self.submitted_at, list):
            self.submitted_at = DateTimeUtils.from_array(self.submitted_at)
        elif isinstance(self.submitted_at, str):
            self.submitted_at = DateTimeUtils.from_iso_string(self.submitted_at)
    
    @classmethod
    def create_legacy(cls, id: int, assignment_id: int, assignment_title: str,
                     team_id: int, team_name: str, submitted_at: Union[datetime, List[int], str],
                     file_url: str) -> 'SubmissionDTO':
        """
        Factory method for backward compatibility with existing code.
        
        Args:
            id: Submission ID
            assignment_id: Assignment ID
            assignment_title: Assignment title
            team_id: Team ID
            team_name: Team name
            submitted_at: Submission timestamp (datetime, array, or string)
            file_url: File URL
            
        Returns:
            SubmissionDTO instance
        """
        return cls(
            id=id,
            assignment_id=assignment_id,
            assignment_title=assignment_title,
            team_id=team_id,
            team_name=team_name,
            submitted_at=DateTimeUtils.parse_flexible_datetime(submitted_at),
            file_url=file_url
        )
    
    @property
    def is_complete(self) -> bool:
        """Check if submission has all required fields."""
        return all([
            self.id is not None,
            self.assignment_id is not None,
            self.team_id is not None,
            self.submitted_at is not None,
            self.file_url is not None
        ])
    
    def get_submission_summary(self) -> str:
        """Get a human-readable summary of the submission."""
        return (f"Submission {self.id}: {self.assignment_title or 'Unknown Assignment'} "
                f"by {self.team_name or 'Unknown Team'} "
                f"on {self.submitted_at.strftime('%Y-%m-%d %H:%M') if self.submitted_at else 'Unknown Date'}")
