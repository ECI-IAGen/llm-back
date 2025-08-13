"""
Base DTO class with common functionality.
"""

from abc import ABC
from typing import Dict, Any, Optional
from datetime import datetime
import json
from .utils import DateTimeUtils


class BaseDTO(ABC):
    """
    Base class for all DTO objects providing common functionality.
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DTO to dictionary representation.
        
        Returns:
            Dictionary representation of the DTO
        """
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, datetime):
                    result[key] = DateTimeUtils.to_iso_string(value)
                elif isinstance(value, BaseDTO):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        return result
    
    def to_json(self) -> str:
        """
        Convert DTO to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['BaseDTO']:
        """
        Create DTO instance from dictionary.
        
        Args:
            data: Dictionary with DTO data
            
        Returns:
            DTO instance or None if creation fails
        """
        try:
            return cls(**data)
        except Exception:
            return None
    
    def __repr__(self) -> str:
        """String representation of the DTO."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith('_'))
        return f"{self.__class__.__name__}({attrs})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on all attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
