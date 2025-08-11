#!/usr/bin/env python3
"""
Final Validation Script - Phase 4

Comprehensive validation of all generated outputs to ensure data integrity
and readiness for production deployment.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

class FinalValidator:
    """Comprehensive validator for all generated outputs"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.validation_results = {
            'files_checked': 0,
            'issues_found': 0,
            'validations_passed': 0,
            'errors': [],
            'warnings': []
        }
    
    def validate_file_exists(self, filename: str) -> bool:
        """Check if file exists and is readable"""
        file_path = self.output_dir / filename
        if not file_path.exists():
            self.validation_results['errors'].append(f"Missing file: {filename}")
            return False
        
        if file_path.stat().st_size == 0:
            self.validation_results['errors'].append(f"Empty file: {filename}")
            return False
        
        self.validation_results['files_checked'] += 1
        return True
    
    def validate_json_format(self, filename: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate JSON file format and structure"""
        if not self.validate_file_exists(filename):
            return False, {}
        
        try:
            with open(self.output_dir / filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.validation_results['validations_passed'] += 1
            return True, data
            
        except json.JSONDecodeError as e:
            self.validation_results['errors'].append(f"Invalid JSON in {filename}: {str(e)}")
            return False, {}
    
    def validate_csv_format(self, filename: str) -> bool:
        """Validate CSV file format"""
        if not self.validate_file_exists(filename):
            return False
        
        try:
            with open(self.output_dir / filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                row_count = sum(1 for _ in reader)
            
            if row_count == 0:
                self.validation_results['warnings'].append(f"Empty CSV data in {filename}")
            else:
                self.validation_results['validations_passed'] += 1
            
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"CSV error in {filename}: {str(e)}")
            return False
    
    def validate_compact_json(self) -> bool:
        """Validate compact JSON format"""
        print("🔍 Validating compact JSON format...")
        
        is_valid, data = self.validate_json_format('uk_solicitors_compact.json')
        if not is_valid:
            return False
        
        # Check structure
        required_fields = ['version', 'generated', 'count', 'organizations']
        for field in required_fields:
            if field not in data:
                self.validation_results['errors'].append(f"Missing field '{field}' in compact JSON")
                return False
        
        # Validate count matches data
        if data['count'] != len(data.get('organizations', [])):
            self.validation_results['errors'].append("Count mismatch in compact JSON")
            return False
        
        # Sample organization structure check
        if data.get('organizations'):
            sample_org = data['organizations'][0]
            org_required = ['id', 'sra_number', 'name', 'quality_score', 'offices']
            for field in org_required:
                if field not in sample_org:
                    self.validation_results['warnings'].append(f"Missing '{field}' in organization structure")
        
        print("   ✅ Compact JSON validation passed")
        return True
    
    def validate_csv_files(self) -> bool:
        """Validate CSV files"""
        print("🔍 Validating CSV files...")
        
        # Validate organizations CSV
        if not self.validate_csv_format('organizations.csv'):
            return False
        
        # Validate offices CSV
        if not self.validate_csv_format('offices.csv'):
            return False
        
        # Check data consistency
        try:
            # Count organizations
            with open(self.output_dir / 'organizations.csv', 'r', encoding='utf-8') as f:
                org_reader = csv.DictReader(f)
                org_count = sum(1 for _ in org_reader)
            
            # Count offices
            with open(self.output_dir / 'offices.csv', 'r', encoding='utf-8') as f:
                office_reader = csv.DictReader(f)
                office_count = sum(1 for _ in office_reader)
            
            print(f"   ✅ Organizations CSV: {org_count:,} records")
            print(f"   ✅ Offices CSV: {office_count:,} records")
            
            # Basic sanity check
            if org_count == 0 or office_count == 0:
                self.validation_results['errors'].append("Empty CSV files detected")
                return False
                
        except Exception as e:
            self.validation_results['errors'].append(f"CSV data validation error: {str(e)}")
            return False
        
        return True
    
    def validate_database_files(self) -> bool:
        """Validate database-ready files"""
        print("🔍 Validating database-ready files...")
        
        # Validate organizations database file
        is_valid, org_data = self.validate_json_format('db_organizations.json')
        if not is_valid:
            return False
        
        # Validate offices database file
        is_valid, office_data = self.validate_json_format('db_offices.json')
        if not is_valid:
            return False
        
        # Check database structure
        if org_data:
            sample_org = org_data[0]
            db_org_fields = ['id', 'sra_number', 'practice_name', 'data_quality_score', 'created_at']
            for field in db_org_fields:
                if field not in sample_org:
                    self.validation_results['warnings'].append(f"Missing database field '{field}' in organizations")
        
        if office_data:
            sample_office = office_data[0]
            db_office_fields = ['id', 'organization_id', 'name', 'postcode', 'created_at']
            for field in db_office_fields:
                if field not in sample_office:
                    self.validation_results['warnings'].append(f"Missing database field '{field}' in offices")
        
        # Check referential integrity
        org_ids = {org['id'] for org in org_data} if org_data else set()
        office_org_ids = {office['organization_id'] for office in office_data} if office_data else set()
        
        orphaned_offices = office_org_ids - org_ids
        if orphaned_offices:
            self.validation_results['errors'].append(f"Found {len(orphaned_offices)} orphaned offices")
            return False
        
        print(f"   ✅ Database organizations: {len(org_data):,} records")
        print(f"   ✅ Database offices: {len(office_data):,} records")
        print("   ✅ Referential integrity maintained")
        
        return True
    
    def validate_statistics_report(self) -> bool:
        """Validate statistics report"""
        print("🔍 Validating statistics report...")
        
        is_valid, data = self.validate_json_format('dataset_statistics.json')
        if not is_valid:
            return False
        
        # Check required sections
        required_sections = [
            'dataset_info', 'quality_distribution', 'geographic_distribution',
            'organization_types', 'contact_completeness'
        ]
        
        for section in required_sections:
            if section not in data:
                self.validation_results['errors'].append(f"Missing statistics section: {section}")
                return False
        
        # Validate key metrics
        dataset_info = data.get('dataset_info', {})
        if not dataset_info.get('total_organizations') or not dataset_info.get('total_offices'):
            self.validation_results['errors'].append("Invalid dataset counts in statistics")
            return False
        
        print("   ✅ Statistics report validation passed")
        return True
    
    def validate_quality_dashboard(self) -> bool:
        """Validate quality dashboard data"""
        print("🔍 Validating quality dashboard data...")
        
        is_valid, data = self.validate_json_format('quality_dashboard.json')
        if not is_valid:
            return False
        
        # Check dashboard structure
        required_sections = ['summary', 'quality_metrics', 'geographic_breakdown', 'top_quality_organizations']
        for section in required_sections:
            if section not in data:
                self.validation_results['errors'].append(f"Missing dashboard section: {section}")
                return False
        
        # Validate summary data
        summary = data.get('summary', {})
        required_summary = ['total_organizations', 'total_offices', 'average_quality_score']
        for field in required_summary:
            if field not in summary:
                self.validation_results['warnings'].append(f"Missing summary field: {field}")
        
        print("   ✅ Quality dashboard validation passed")
        return True
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 COMPREHENSIVE OUTPUT VALIDATION")
        print("="*80)
        
        # Run all validations
        validations = [
            self.validate_compact_json(),
            self.validate_csv_files(),
            self.validate_database_files(),
            self.validate_statistics_report(),
            self.validate_quality_dashboard()
        ]
        
        # Check for generation summary
        if self.validate_file_exists('generation_summary.json'):
            is_valid, summary_data = self.validate_json_format('generation_summary.json')
            if is_valid:
                print("   ✅ Generation summary validation passed")
        
        # Overall results
        all_passed = all(validations)
        
        print(f"\n📈 VALIDATION RESULTS:")
        print("-" * 80)
        print(f"Files checked:              {self.validation_results['files_checked']:>10}")
        print(f"Validations passed:         {self.validation_results['validations_passed']:>10}")
        print(f"Errors found:               {len(self.validation_results['errors']):>10}")
        print(f"Warnings:                   {len(self.validation_results['warnings']):>10}")
        
        if self.validation_results['errors']:
            print(f"\n❌ ERRORS:")
            for error in self.validation_results['errors']:
                print(f"   • {error}")
        
        if self.validation_results['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.validation_results['warnings']:
                print(f"   • {warning}")
        
        # Overall status
        if all_passed and not self.validation_results['errors']:
            status = "PASSED"
            grade = "A"
            print(f"\n✅ OVERALL STATUS: {status} (Grade: {grade})")
        elif all_passed and self.validation_results['warnings']:
            status = "PASSED WITH WARNINGS"
            grade = "B"
            print(f"\n⚠️  OVERALL STATUS: {status} (Grade: {grade})")
        else:
            status = "FAILED"
            grade = "F"
            print(f"\n❌ OVERALL STATUS: {status} (Grade: {grade})")
        
        return {
            'status': status,
            'grade': grade,
            'details': self.validation_results,
            'all_validations_passed': all_passed
        }

def main():
    """Main validation function"""
    output_dir = Path("data/output")
    
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        print("   Please run the output generation script first")
        return
    
    validator = FinalValidator(output_dir)
    results = validator.run_comprehensive_validation()
    
    print(f"\n✅ Final validation complete!")
    print(f"🎯 Status: {results['status']}")
    
    if results['all_validations_passed'] and not results['details']['errors']:
        print("🚀 All outputs are ready for production deployment!")

if __name__ == "__main__":
    main()