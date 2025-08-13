"""
Utility classes for data conversion and handling.
"""

from datetime import datetime
from typing import List, Optional, Union
import json


class DateTimeUtils:
    """
    Utility class for handling datetime conversions between different formats.
    Handles the array format: [year, month, day, hour, minute, second, nanoseconds]
    """
    
    @staticmethod
    def from_array(date_array: List[int]) -> datetime:
        """
        Convert datetime array format to Python datetime object.
        
        Args:
            date_array: List in format [year, month, day, hour, minute, second, nanoseconds]
            
        Returns:
            datetime object
            
        Example:
            >>> DateTimeUtils.from_array([2025, 8, 3, 9, 35, 0, 574404200])
            datetime(2025, 8, 3, 9, 35, 0, 574404)
        """
        if not date_array or len(date_array) < 6:
            raise ValueError("Date array must have at least 6 elements")
            
        year, month, day, hour, minute, second = date_array[:6]
        microsecond = date_array[6] // 1000 if len(date_array) > 6 else 0
        
        return datetime(year, month, day, hour, minute, second, microsecond)
    
    @staticmethod
    def to_array(dt: datetime) -> List[int]:
        """
        Convert Python datetime object to array format.
        
        Args:
            dt: datetime object
            
        Returns:
            List in format [year, month, day, hour, minute, second, nanoseconds]
        """
        nanoseconds = dt.microsecond * 1000
        return [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, nanoseconds]
    
    @staticmethod
    def from_iso_string(iso_string: str) -> datetime:
        """
        Convert ISO datetime string to Python datetime object.
        
        Args:
            iso_string: ISO format datetime string
            
        Returns:
            datetime object
        """
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    @staticmethod
    def to_iso_string(dt: datetime) -> str:
        """
        Convert Python datetime object to ISO string format.
        
        Args:
            dt: datetime object
            
        Returns:
            ISO format datetime string
        """
        return dt.isoformat()
    
    @staticmethod
    def parse_flexible_datetime(value: Union[str, List[int], datetime]) -> Optional[datetime]:
        """
        Parse datetime from various formats (string, array, or datetime object).
        
        Args:
            value: Datetime in various formats
            
        Returns:
            datetime object or None if parsing fails
        """
        if value is None:
            return None
            
        if isinstance(value, datetime):
            return value
            
        if isinstance(value, str):
            try:
                return DateTimeUtils.from_iso_string(value)
            except ValueError:
                return None
                
        if isinstance(value, list):
            try:
                return DateTimeUtils.from_array(value)
            except (ValueError, IndexError):
                return None
                
        return None
