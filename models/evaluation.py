"""
Evaluation DTO for handling evaluation data.
"""

from dataclasses import dataclass
from typing import Optional, Union, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json
from .base import BaseDTO
from .utils import DateTimeUtils


@dataclass
class EvaluationDTO(BaseDTO):
    """
    Data Transfer Object for Evaluation entities.
    
    Attributes:
        id: Unique identifier for the evaluation
        submission_id: ID of the associated submission
        evaluator_id: ID of the evaluator
        evaluator_name: Name of the evaluator
        evaluation_type: Type of evaluation (e.g., 'automated', 'manual', 'peer')
        score: Evaluation score (using Decimal for precision)
        criteria_json: JSON string containing evaluation criteria
        created_at: Timestamp when evaluation was created
        evaluation_date: Timestamp when evaluation was performed
        team_name: Helper field for display purposes
        assignment_title: Helper field for display purposes
        class_id: ID of the class (optional)
        class_name: Name of the class (optional)
    """
    
    id: Optional[int] = None
    submission_id: Optional[int] = None
    evaluator_id: Optional[int] = None
    evaluator_name: Optional[str] = None
    evaluation_type: Optional[str] = None
    score: Optional[Decimal] = None
    criteria_json: Optional[str] = None
    created_at: Optional[datetime] = None
    evaluation_date: Optional[datetime] = None
    team_name: Optional[str] = None
    assignment_title: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing for date and score conversion."""
        # Convert dates if they're in array format
        if isinstance(self.created_at, list):
            self.created_at = DateTimeUtils.from_array(self.created_at)
        elif isinstance(self.created_at, str):
            self.created_at = DateTimeUtils.from_iso_string(self.created_at)
            
        if isinstance(self.evaluation_date, list):
            self.evaluation_date = DateTimeUtils.from_array(self.evaluation_date)
        elif isinstance(self.evaluation_date, str):
            self.evaluation_date = DateTimeUtils.from_iso_string(self.evaluation_date)
        
        # Convert score to Decimal if it's a number
        if isinstance(self.score, (int, float)):
            self.score = Decimal(str(self.score))
    
    @classmethod
    def create_legacy(cls, id: int, submission_id: int, evaluator_id: int, evaluator_name: str,
                     evaluation_type: str, score: Union[Decimal, float, int], criteria_json: str,
                     created_at: Union[datetime, List[int], str],
                     evaluation_date: Union[datetime, List[int], str],
                     team_name: str, assignment_title: str) -> 'EvaluationDTO':
        """
        Factory method for backward compatibility with existing code.
        
        Args:
            id: Evaluation ID
            submission_id: Submission ID
            evaluator_id: Evaluator ID
            evaluator_name: Evaluator name
            evaluation_type: Type of evaluation
            score: Evaluation score
            criteria_json: Criteria as JSON string
            created_at: Creation timestamp
            evaluation_date: Evaluation timestamp
            team_name: Team name
            assignment_title: Assignment title
            
        Returns:
            EvaluationDTO instance
        """
        return cls(
            id=id,
            submission_id=submission_id,
            evaluator_id=evaluator_id,
            evaluator_name=evaluator_name,
            evaluation_type=evaluation_type,
            score=Decimal(str(score)) if score is not None else None,
            criteria_json=criteria_json,
            created_at=DateTimeUtils.parse_flexible_datetime(created_at),
            evaluation_date=DateTimeUtils.parse_flexible_datetime(evaluation_date),
            team_name=team_name,
            assignment_title=assignment_title
        )
    
    @property
    def is_complete(self) -> bool:
        """Check if evaluation has all required fields."""
        return all([
            self.submission_id is not None,
            self.evaluator_id is not None,
            self.evaluation_type is not None,
            self.score is not None,
            self.evaluation_date is not None
        ])
    
    @property
    def criteria(self) -> Optional[Dict[str, Any]]:
        """Parse criteria JSON into dictionary."""
        if not self.criteria_json:
            return None
        try:
            return json.loads(self.criteria_json)
        except json.JSONDecodeError:
            return None
    
    @criteria.setter
    def criteria(self, value: Dict[str, Any]) -> None:
        """Set criteria from dictionary."""
        if value is None:
            self.criteria_json = None
        else:
            self.criteria_json = json.dumps(value, ensure_ascii=False)
    
    @property
    def score_percentage(self) -> Optional[float]:
        """Get score as percentage (assuming score is out of 100)."""
        if self.score is None:
            return None
        return float(self.score)
    
    @property
    def score_out_of_ten(self) -> Optional[float]:
        """Get score out of 10 (assuming original score is out of 100)."""
        if self.score is None:
            return None
        return float(self.score) / 10.0
    
    def get_criteria_summary(self) -> str:
        """Get a summary of evaluation criteria."""
        criteria = self.criteria
        if not criteria:
            return "No criteria specified"
        
        if isinstance(criteria, dict):
            summary_parts = []
            for key, value in criteria.items():
                if isinstance(value, (int, float)):
                    summary_parts.append(f"{key}: {value}")
                elif isinstance(value, str) and len(value) < 50:
                    summary_parts.append(f"{key}: {value}")
                else:
                    summary_parts.append(f"{key}: [Complex criteria]")
            return "; ".join(summary_parts[:3])  # Limit to first 3 items
        
        return str(criteria)[:100] + "..." if len(str(criteria)) > 100 else str(criteria)
    
    def get_evaluation_summary(self) -> str:
        """Get a human-readable summary of the evaluation."""
        date_str = self.evaluation_date.strftime('%Y-%m-%d %H:%M') if self.evaluation_date else 'Unknown Date'
        score_str = f"{self.score}" if self.score is not None else "No Score"
        
        return (f"Evaluation {self.id or 'New'}: {score_str} points "
                f"by {self.evaluator_name or 'Unknown Evaluator'} "
                f"for {self.assignment_title or 'Unknown Assignment'} "
                f"({self.team_name or 'Unknown Team'}) on {date_str}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Override to handle Decimal serialization."""
        result = super().to_dict()
        if 'score' in result and result['score'] is not None:
            result['score'] = float(result['score'])
        return result
