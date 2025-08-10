"""
Tests for utility modules
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import get_logger, FileManager, DataValidator
from utils.validators import DataQualityChecker
import pandas as pd


class TestLogger:
    """Test logging functionality"""
    
    def test_get_logger(self):
        """Test logger creation"""
        logger = get_logger("test")
        assert logger.name == "test"
    
    def test_logger_different_names(self):
        """Test different logger names"""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        assert logger1.name != logger2.name


class TestFileManager:
    """Test file management utilities"""
    
    def test_ensure_directory(self, tmp_path):
        """Test directory creation"""
        test_dir = tmp_path / "test_directory"
        result = FileManager.ensure_directory(test_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_file_exists(self, tmp_path):
        """Test file existence check"""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        
        assert FileManager.file_exists(test_file) is True
        assert FileManager.file_exists(tmp_path / "nonexistent.txt") is False


class TestDataValidator:
    """Test data validation utilities"""
    
    def test_validate_email(self):
        """Test email validation"""
        validator = DataValidator()
        
        # Valid emails
        assert validator.validate_email("test@example.com") is True
        assert validator.validate_email("user.name@domain.co.uk") is True
        
        # Invalid emails
        assert validator.validate_email("invalid-email") is False
        assert validator.validate_email("@domain.com") is False
    
    def test_validate_phone_uk(self):
        """Test UK phone number validation"""
        validator = DataValidator()
        
        # Valid UK numbers
        assert validator.validate_phone_uk("07123456789") is True
        assert validator.validate_phone_uk("+447123456789") is True
        assert validator.validate_phone_uk("0207123456") is True
        
        # Invalid numbers
        assert validator.validate_phone_uk("123") is False
        assert validator.validate_phone_uk("invalid") is False
    
    def test_validate_postcode_uk(self):
        """Test UK postcode validation"""
        validator = DataValidator()
        
        # Valid postcodes
        assert validator.validate_postcode_uk("SW1A 1AA") is True
        assert validator.validate_postcode_uk("M1 1AA") is True
        assert validator.validate_postcode_uk("B33 8TH") is True
        
        # Invalid postcodes
        assert validator.validate_postcode_uk("INVALID") is False
        assert validator.validate_postcode_uk("12345") is False
    
    def test_validate_solicitor_number(self):
        """Test solicitor number validation"""
        validator = DataValidator()
        
        # Valid solicitor numbers
        assert validator.validate_solicitor_number("123456") is True
        assert validator.validate_solicitor_number("1234567") is True
        
        # Invalid solicitor numbers
        assert validator.validate_solicitor_number("12345") is False
        assert validator.validate_solicitor_number("12345678") is False
        assert validator.validate_solicitor_number("abc123") is False
    
    def test_validate_rating(self):
        """Test rating validation"""
        validator = DataValidator()
        
        # Valid ratings
        assert validator.validate_rating(3.5) is True
        assert validator.validate_rating(5) is True
        assert validator.validate_rating(0) is True
        
        # Invalid ratings
        assert validator.validate_rating(-1) is False
        assert validator.validate_rating(6) is False
        assert validator.validate_rating("invalid") is False
    
    def test_validate_required_fields(self):
        """Test required fields validation"""
        validator = DataValidator()
        
        data = {
            "field1": "value1",
            "field2": "",
            "field3": None
        }
        
        required_fields = ["field1", "field2", "field3", "field4"]
        results = validator.validate_required_fields(data, required_fields)
        
        assert results["field1"] is True  # Present and not empty
        assert results["field2"] is False  # Present but empty
        assert results["field3"] is False  # Present but None
        assert results["field4"] is False  # Missing


class TestDataQualityChecker:
    """Test data quality assessment"""
    
    def test_check_duplicates(self):
        """Test duplicate detection"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 2, 4],
            'name': ['A', 'B', 'C', 'B', 'D']
        })
        
        result = DataQualityChecker.check_duplicates(df, ['id'])
        
        assert result['has_duplicates'] is True
        assert result['duplicate_count'] == 2  # Two rows with id=2
    
    def test_check_missing_data(self):
        """Test missing data analysis"""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['A', None, 'C', None, 'E'],
            'col3': [1, 2, 3, 4, 5]  # No missing values
        })
        
        result = DataQualityChecker.check_missing_data(df)
        
        assert result['total_rows'] == 5
        assert 'col1' in result['missing_data']
        assert 'col2' in result['missing_data']
        assert 'col3' not in result['missing_data']
    
    def test_assess_data_quality(self):
        """Test overall data quality assessment"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['A', 'B', None, 'D', 'E'],
            'score': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        result = DataQualityChecker.assess_data_quality(df, ['id'])
        
        assert result['total_records'] == 5
        assert result['total_columns'] == 3
        assert 'quality_score' in result
        assert 'quality_rating' in result
        assert result['duplicates']['has_duplicates'] is False