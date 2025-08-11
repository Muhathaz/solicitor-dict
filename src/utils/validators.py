"""
Data validation utilities for UK Solicitors Data Processing
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import jsonschema
import pandas as pd

from .logger import get_logger
from .file_manager import ConfigLoader

logger = get_logger(__name__)


class DataValidator:
    """Comprehensive data validation utilities"""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self.config_loader = config_loader or ConfigLoader()
        self.validation_rules = self.config_loader.get_setting('validation', {})
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone_uk(self, phone: str) -> bool:
        """Validate UK phone number format"""
        # Remove spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # UK phone patterns
        patterns = [
            r'^(\+44|0044|44)?[1-9]\d{8,9}$',  # Standard UK numbers
            r'^(\+44|0044|44)?[78]\d{9}$',     # Mobile numbers
            r'^(\+44|0044|44)?[12]\d{8}$',     # Geographic numbers
        ]
        
        return any(re.match(pattern, cleaned) for pattern in patterns)
    
    def validate_postcode_uk(self, postcode: str) -> bool:
        """Validate UK postcode format"""
        # UK postcode pattern
        pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
        return bool(re.match(pattern, postcode.upper().strip()))
    
    def validate_solicitor_number(self, number: str) -> bool:
        """Validate SRA solicitor number format"""
        # SRA numbers are typically 6-7 digits
        pattern = r'^\d{6,7}$'
        return bool(re.match(pattern, str(number)))
    
    def validate_date(self, date_str: str, format_str: str = "%Y-%m-%d") -> bool:
        """Validate date string format"""
        try:
            datetime.strptime(date_str, format_str)
            return True
        except (ValueError, TypeError):
            return False
    
    def validate_rating(self, rating: Union[int, float], min_val: float = 0, max_val: float = 5) -> bool:
        """Validate rating value within range"""
        try:
            rating = float(rating)
            return min_val <= rating <= max_val
        except (ValueError, TypeError):
            return False
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, bool]:
        """Validate that required fields are present and not empty"""
        results = {}
        
        for field in required_fields:
            if field not in data:
                results[field] = False
                logger.warning(f"Missing required field: {field}")
            elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                results[field] = False
                logger.warning(f"Empty required field: {field}")
            else:
                results[field] = True
        
        return results
    
    def validate_field_types(self, data: Dict[str, Any], field_types: Dict[str, str]) -> Dict[str, bool]:
        """Validate field types"""
        results = {}
        
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        
        for field, expected_type in field_types.items():
            if field not in data:
                results[field] = True  # Skip validation for missing fields
                continue
            
            if expected_type not in type_map:
                logger.warning(f"Unknown type specification: {expected_type}")
                results[field] = True
                continue
            
            expected_python_type = type_map[expected_type]
            
            if isinstance(data[field], expected_python_type):
                results[field] = True
            else:
                results[field] = False
                logger.warning(f"Field {field} has incorrect type: expected {expected_type}, got {type(data[field]).__name__}")
        
        return results
    
    def validate_record(self, record: Dict[str, Any], record_type: str) -> Dict[str, Any]:
        """Validate a complete record based on configured rules"""
        validation_config = self.validation_rules.get(record_type, {})
        
        if not validation_config:
            logger.warning(f"No validation rules found for record type: {record_type}")
            return {"valid": True, "errors": [], "warnings": []}
        
        errors = []
        warnings = []
        
        # Validate required fields
        required_fields = validation_config.get('required_fields', [])
        required_results = self.validate_required_fields(record, required_fields)
        
        for field, is_valid in required_results.items():
            if not is_valid:
                errors.append(f"Missing or empty required field: {field}")
        
        # Validate field types
        field_types = validation_config.get('field_types', {})
        type_results = self.validate_field_types(record, field_types)
        
        for field, is_valid in type_results.items():
            if not is_valid:
                errors.append(f"Invalid type for field: {field}")
        
        # Record-specific validations
        if record_type == "sra_record":
            if 'solicitor_number' in record:
                if not self.validate_solicitor_number(record['solicitor_number']):
                    errors.append("Invalid solicitor number format")
        
        elif record_type == "sra_organization":
            if 'SraNumber' in record:
                if not self.validate_solicitor_number(str(record['SraNumber'])):
                    errors.append("Invalid SRA organization number format")
            
            # Validate offices array exists and is valid
            if 'Offices' in record:
                if not isinstance(record['Offices'], list):
                    errors.append("Offices field must be a list")
                elif len(record['Offices']) == 0:
                    warnings.append("Organization has no offices")
        
        elif record_type == "sra_office":
            # Validate postcode if present
            if record.get('Postcode'):
                if not self.validate_postcode_uk(record['Postcode']):
                    warnings.append("Invalid postcode format")
            
            # Validate email if present
            if record.get('Email'):
                if not self.validate_email(record['Email']):
                    warnings.append("Invalid email format")
            
            # Validate phone if present
            if record.get('PhoneNumber'):
                if not self.validate_phone_uk(record['PhoneNumber']):
                    warnings.append("Invalid phone number format")
        
        elif record_type == "review_record":
            if 'rating' in record:
                if not self.validate_rating(record['rating']):
                    errors.append("Invalid rating value")
            
            if 'date' in record:
                if not self.validate_date(record['date']):
                    warnings.append("Date format may be incorrect")
        
        # Check for common issues
        if 'email' in record and record['email']:
            if not self.validate_email(record['email']):
                warnings.append("Email format appears invalid")
        
        if 'phone' in record and record['phone']:
            if not self.validate_phone_uk(record['phone']):
                warnings.append("Phone number format appears invalid")
        
        if 'postcode' in record and record['postcode']:
            if not self.validate_postcode_uk(record['postcode']):
                warnings.append("Postcode format appears invalid")
        
        is_valid = len(errors) == 0
        
        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "required_fields_valid": required_results,
            "field_types_valid": type_results
        }
    
    def validate_dataset(self, data: List[Dict[str, Any]], record_type: str) -> Dict[str, Any]:
        """Validate entire dataset"""
        logger.info(f"Validating dataset with {len(data)} records of type: {record_type}")
        
        valid_count = 0
        invalid_count = 0
        all_errors = []
        all_warnings = []
        
        for i, record in enumerate(data):
            result = self.validate_record(record, record_type)
            
            if result['valid']:
                valid_count += 1
            else:
                invalid_count += 1
                record_errors = [f"Record {i+1}: {error}" for error in result['errors']]
                all_errors.extend(record_errors)
            
            record_warnings = [f"Record {i+1}: {warning}" for warning in result['warnings']]
            all_warnings.extend(record_warnings)
        
        validation_summary = {
            "total_records": len(data),
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "validation_rate": (valid_count / len(data)) * 100 if data else 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "error_count": len(all_errors),
            "warning_count": len(all_warnings)
        }
        
        logger.info(f"Validation complete: {valid_count}/{len(data)} records valid ({validation_summary['validation_rate']:.1f}%)")
        
        if all_errors:
            logger.warning(f"Found {len(all_errors)} validation errors")
        
        if all_warnings:
            logger.info(f"Found {len(all_warnings)} validation warnings")
        
        return validation_summary


class SchemaValidator:
    """JSON Schema-based validation"""
    
    def __init__(self):
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load validation schemas"""
        return {
            "sra_record": {
                "type": "object",
                "required": ["solicitor_number", "first_name", "last_name", "organisation", "status"],
                "properties": {
                    "solicitor_number": {"type": "string", "pattern": "^\\d{6,7}$"},
                    "first_name": {"type": "string", "minLength": 1},
                    "last_name": {"type": "string", "minLength": 1},
                    "organisation": {"type": "string", "minLength": 1},
                    "status": {"type": "string", "enum": ["Practising", "Non-practising", "Suspended"]},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"}
                }
            },
            "google_places_record": {
                "type": "object",
                "required": ["place_id", "name", "address"],
                "properties": {
                    "place_id": {"type": "string", "minLength": 1},
                    "name": {"type": "string", "minLength": 1},
                    "address": {"type": "string", "minLength": 1},
                    "rating": {"type": "number", "minimum": 0, "maximum": 5},
                    "review_count": {"type": "integer", "minimum": 0},
                    "phone": {"type": "string"},
                    "website": {"type": "string", "format": "uri"}
                }
            },
            "review_record": {
                "type": "object",
                "required": ["reviewer_name", "rating", "review_text", "date"],
                "properties": {
                    "reviewer_name": {"type": "string", "minLength": 1},
                    "rating": {"type": "number", "minimum": 1, "maximum": 5},
                    "review_text": {"type": "string", "minLength": 1},
                    "date": {"type": "string"},
                    "platform": {"type": "string", "enum": ["trustpilot", "yelp", "reviewsolicitors", "google"]},
                    "helpful_count": {"type": "integer", "minimum": 0}
                }
            }
        }
    
    def validate_with_schema(self, data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """Validate data against JSON schema"""
        if schema_name not in self.schemas:
            return {
                "valid": False,
                "errors": [f"Unknown schema: {schema_name}"],
                "warnings": []
            }
        
        schema = self.schemas[schema_name]
        
        try:
            jsonschema.validate(data, schema)
            return {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }


class DataQualityChecker:
    """Advanced data quality assessment"""
    
    @staticmethod
    def check_duplicates(df: pd.DataFrame, key_columns: List[str]) -> Dict[str, Any]:
        """Check for duplicate records"""
        if not key_columns:
            return {"has_duplicates": False, "duplicate_count": 0}
        
        duplicates = df.duplicated(subset=key_columns, keep=False)
        duplicate_count = duplicates.sum()
        
        return {
            "has_duplicates": duplicate_count > 0,
            "duplicate_count": int(duplicate_count),
            "duplicate_percentage": (duplicate_count / len(df)) * 100 if len(df) > 0 else 0,
            "duplicate_rows": df[duplicates].index.tolist() if duplicate_count > 0 else []
        }
    
    @staticmethod
    def check_missing_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing data patterns"""
        missing_counts = df.isnull().sum()
        total_rows = len(df)
        
        missing_info = {}
        for column, count in missing_counts.items():
            if count > 0:
                missing_info[column] = {
                    "count": int(count),
                    "percentage": (count / total_rows) * 100
                }
        
        return {
            "total_rows": total_rows,
            "missing_data": missing_info,
            "columns_with_missing": list(missing_info.keys()),
            "overall_completeness": ((total_rows * len(df.columns) - missing_counts.sum()) / (total_rows * len(df.columns))) * 100 if total_rows > 0 else 100
        }
    
    @staticmethod
    def assess_data_quality(df: pd.DataFrame, key_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        quality_report = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "missing_data": DataQualityChecker.check_missing_data(df),
            "duplicates": DataQualityChecker.check_duplicates(df, key_columns or []),
            "data_types": df.dtypes.to_dict(),
            "summary_stats": df.describe(include='all').to_dict() if not df.empty else {}
        }
        
        # Calculate overall quality score
        completeness_score = quality_report["missing_data"]["overall_completeness"]
        duplicate_penalty = quality_report["duplicates"]["duplicate_percentage"]
        
        quality_score = max(0, completeness_score - duplicate_penalty)
        quality_report["quality_score"] = quality_score
        
        # Quality rating
        if quality_score >= 90:
            quality_rating = "Excellent"
        elif quality_score >= 80:
            quality_rating = "Good"
        elif quality_score >= 70:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        quality_report["quality_rating"] = quality_rating
        
        return quality_report