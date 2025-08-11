"""
SRA Data Collector for UK Solicitors Data Processing

Collects comprehensive organization and office data from the SRA API,
including data validation, progress tracking, and error recovery.
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib

try:
    from .sra_api_client import SRAAPIClient, SRAAPIError
    from ..utils import get_logger, ProgressLogger, log_exception, log_performance, FileManager, DataLoader, ConfigLoader, DataValidator
except ImportError:
    from sra_api_client import SRAAPIClient, SRAAPIError
    from utils import get_logger, ProgressLogger, log_exception, log_performance, FileManager, DataLoader, ConfigLoader, DataValidator

logger = get_logger(__name__)


class SRACollector:
    """Main collector for SRA organization and office data"""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None, output_dir: Optional[str] = None):
        self.config = config_loader or ConfigLoader()
        self.output_dir = Path(output_dir) if output_dir else Path("data/raw/sra")
        self.validator = DataValidator()
        
        # Collection state
        self.collection_stats = {
            'start_time': None,
            'end_time': None,
            'total_organizations': 0,
            'organizations_processed': 0,
            'total_offices': 0,
            'offices_processed': 0,
            'errors': 0,
            'validation_errors': 0,
            'api_calls': 0,
            'data_size_bytes': 0
        }
        
        self.errors_log = []
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.output_dir / "organizations",
            self.output_dir / "metadata", 
            self.output_dir / "collection_reports"
        ]
        
        for directory in directories:
            FileManager.ensure_directory(directory)
            logger.debug(f"Directory ensured: {directory}")
    
    def _generate_filename(self, base_name: str, extension: str = "json") -> str:
        """Generate timestamped filename"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{timestamp}_{base_name}.{extension}"
    
    def _save_collection_state(self, state: Dict[str, Any]):
        """Save collection state for resumption"""
        state_file = self.output_dir / "metadata" / "collection_state.json"
        DataLoader.save_json(state, state_file)
        logger.debug("Collection state saved")
    
    def _load_collection_state(self) -> Optional[Dict[str, Any]]:
        """Load previous collection state"""
        state_file = self.output_dir / "metadata" / "collection_state.json"
        
        if state_file.exists():
            try:
                state = DataLoader.load_json(state_file)
                logger.info("Previous collection state loaded")
                return state
            except Exception as e:
                logger.error(f"Failed to load collection state: {e}")
        
        return None
    
    def _validate_organization(self, org: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate organization data"""
        try:
            result = self.validator.validate_record(org, "sra_organization")
            return result.get('valid', False), result.get('errors', [])
        except Exception as e:
            logger.error(f"Validation error for organization {org.get('Id', 'unknown')}: {e}")
            return False, [str(e)]
    
    def _validate_office(self, office: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate office data"""
        try:
            result = self.validator.validate_record(office, "sra_office")
            return result.get('valid', False), result.get('errors', [])
        except Exception as e:
            logger.error(f"Validation error for office {office.get('OfficeId', 'unknown')}: {e}")
            return False, [str(e)]
    
    def _process_organization_data(self, organizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and validate organization data"""
        processed_data = {
            'metadata': {
                'collection_date': datetime.now().isoformat(),
                'total_organizations': len(organizations),
                'total_offices': 0,
                'validation_summary': {
                    'valid_organizations': 0,
                    'invalid_organizations': 0,
                    'valid_offices': 0,
                    'invalid_offices': 0,
                    'validation_errors': []
                }
            },
            'organizations': []
        }
        
        progress = ProgressLogger(logger, "Processing Organizations", len(organizations))
        
        for org in organizations:
            try:
                # Validate organization
                org_valid, org_errors = self._validate_organization(org)
                
                if not org_valid:
                    self.collection_stats['validation_errors'] += 1
                    processed_data['metadata']['validation_summary']['invalid_organizations'] += 1
                    processed_data['metadata']['validation_summary']['validation_errors'].extend([
                        {
                            'organization_id': org.get('Id'),
                            'type': 'organization',
                            'errors': org_errors
                        }
                    ])
                    logger.warning(f"Invalid organization {org.get('Id')}: {org_errors}")
                else:
                    processed_data['metadata']['validation_summary']['valid_organizations'] += 1
                
                # Process offices for this organization
                offices = org.get('Offices', [])
                if offices:
                    processed_data['metadata']['total_offices'] += len(offices)
                    self.collection_stats['total_offices'] += len(offices)
                    
                    valid_offices = []
                    for office in offices:
                        office_valid, office_errors = self._validate_office(office)
                        
                        if office_valid:
                            processed_data['metadata']['validation_summary']['valid_offices'] += 1
                            valid_offices.append(office)
                            self.collection_stats['offices_processed'] += 1
                        else:
                            self.collection_stats['validation_errors'] += 1
                            processed_data['metadata']['validation_summary']['invalid_offices'] += 1
                            processed_data['metadata']['validation_summary']['validation_errors'].append({
                                'organization_id': org.get('Id'),
                                'office_id': office.get('OfficeId'),
                                'type': 'office', 
                                'errors': office_errors
                            })
                            logger.warning(f"Invalid office {office.get('OfficeId')} for org {org.get('Id')}: {office_errors}")
                    
                    # Update organization with validated offices
                    org['Offices'] = valid_offices
                
                processed_data['organizations'].append(org)
                self.collection_stats['organizations_processed'] += 1
                
                progress.update(1, f"Processed org {org.get('Id')} with {len(offices)} offices")
                
            except Exception as e:
                self.collection_stats['errors'] += 1
                error_info = {
                    'organization_id': org.get('Id'),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                self.errors_log.append(error_info)
                log_exception(logger, e, f"Error processing organization {org.get('Id')}")
        
        progress.complete("All organizations processed")
        
        # Log validation summary
        val_summary = processed_data['metadata']['validation_summary']
        logger.info(f"Validation Summary: {val_summary['valid_organizations']}/{len(organizations)} orgs valid, "
                   f"{val_summary['valid_offices']}/{processed_data['metadata']['total_offices']} offices valid")
        
        return processed_data
    
    def _save_data(self, data: Dict[str, Any]) -> Dict[str, Path]:
        """Save collected data to files"""
        saved_files = {}
        
        try:
            # Save main organizations data
            main_file = self.output_dir / "organizations" / self._generate_filename("organizations_complete")
            DataLoader.save_json(data, main_file)
            saved_files['main_data'] = main_file
            logger.info(f"Organizations data saved to {main_file}")
            
            # Save metadata separately
            metadata_file = self.output_dir / "metadata" / self._generate_filename("organizations_metadata")
            DataLoader.save_json(data['metadata'], metadata_file)
            saved_files['metadata'] = metadata_file
            logger.info(f"Metadata saved to {metadata_file}")
            
            # Calculate and update data size
            self.collection_stats['data_size_bytes'] = sum(
                FileManager.get_file_size(path) for path in saved_files.values()
            )
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise
    
    def _generate_collection_report(self, saved_files: Dict[str, Path]) -> Path:
        """Generate comprehensive collection report"""
        
        duration = 0
        if self.collection_stats['start_time'] and self.collection_stats['end_time']:
            duration = self.collection_stats['end_time'] - self.collection_stats['start_time']
        
        report = {
            'collection_summary': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'total_organizations': self.collection_stats['total_organizations'],
                'organizations_processed': self.collection_stats['organizations_processed'],
                'total_offices': self.collection_stats['total_offices'],
                'offices_processed': self.collection_stats['offices_processed'],
                'success_rate': (
                    self.collection_stats['organizations_processed'] / 
                    max(self.collection_stats['total_organizations'], 1) * 100
                )
            },
            'data_quality': {
                'validation_errors': self.collection_stats['validation_errors'],
                'processing_errors': self.collection_stats['errors'],
                'error_rate': (
                    self.collection_stats['errors'] / 
                    max(self.collection_stats['total_organizations'], 1) * 100
                )
            },
            'api_performance': {
                'api_calls': self.collection_stats['api_calls'],
                'average_response_time': duration / max(self.collection_stats['api_calls'], 1)
            },
            'data_files': {
                str(key): str(path) for key, path in saved_files.items()
            },
            'data_size': {
                'total_bytes': self.collection_stats['data_size_bytes'],
                'total_mb': round(self.collection_stats['data_size_bytes'] / 1024 / 1024, 2)
            },
            'errors': self.errors_log[-10:]  # Last 10 errors for reference
        }
        
        # Save collection report
        report_file = self.output_dir / "collection_reports" / self._generate_filename("collection_summary")
        DataLoader.save_json(report, report_file)
        
        logger.info(f"Collection report saved to {report_file}")
        return report_file
    
    def collect_organizations(self, resume: bool = False) -> Dict[str, Any]:
        """Collect all organizations from SRA API"""
        
        self.collection_stats['start_time'] = time.time()
        logger.info("Starting SRA organizations collection...")
        
        try:
            # Check for resume capability
            if resume:
                saved_state = self._load_collection_state()
                if saved_state:
                    logger.info("Resuming from previous collection state")
                    # Implementation for resume would go here
                    # For now, we'll do a fresh collection
            
            # Initialize API client
            with SRAAPIClient(self.config) as api_client:
                
                # Test connection first
                if not api_client.test_connection():
                    raise SRAAPIError("Failed to establish connection to SRA API")
                
                self.collection_stats['api_calls'] += 1
                
                # Get all organizations data
                logger.info("Requesting organizations data from SRA API...")
                raw_data = api_client.get_all_organizations()
                
                self.collection_stats['total_organizations'] = raw_data.get('Count', 0)
                organizations = raw_data.get('Organisations', [])
                
                if not organizations:
                    raise SRAAPIError("No organizations data received from API")
                
                logger.info(f"Received {len(organizations)} organizations "
                           f"(API reports {self.collection_stats['total_organizations']} total)")
                
                # Process and validate data
                processed_data = self._process_organization_data(organizations)
                
                # Save data
                saved_files = self._save_data(processed_data)
                
                # Update collection state
                collection_state = {
                    'last_collection': datetime.now().isoformat(),
                    'organizations_count': len(organizations),
                    'collection_completed': True,
                    'files_saved': {str(k): str(v) for k, v in saved_files.items()}
                }
                self._save_collection_state(collection_state)
                
                self.collection_stats['end_time'] = time.time()
                
                # Generate collection report
                report_file = self._generate_collection_report(saved_files)
                
                # Log final summary
                duration = self.collection_stats['end_time'] - self.collection_stats['start_time']
                log_performance(logger, "SRA Collection", duration, 
                               organizations=self.collection_stats['organizations_processed'],
                               offices=self.collection_stats['offices_processed'],
                               errors=self.collection_stats['errors'])
                
                return {
                    'success': True,
                    'organizations_collected': self.collection_stats['organizations_processed'],
                    'offices_collected': self.collection_stats['offices_processed'],
                    'duration': duration,
                    'files_saved': saved_files,
                    'report_file': report_file,
                    'collection_stats': self.collection_stats
                }
                
        except Exception as e:
            self.collection_stats['end_time'] = time.time()
            log_exception(logger, e, "SRA collection failed")
            
            return {
                'success': False,
                'error': str(e),
                'organizations_collected': self.collection_stats['organizations_processed'],
                'offices_collected': self.collection_stats['offices_processed'],
                'collection_stats': self.collection_stats
            }
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status"""
        state = self._load_collection_state()
        
        status = {
            'has_previous_collection': state is not None,
            'current_stats': self.collection_stats
        }
        
        if state:
            status.update({
                'last_collection_date': state.get('last_collection'),
                'last_collection_completed': state.get('collection_completed', False),
                'last_organizations_count': state.get('organizations_count', 0),
                'files_from_last_collection': state.get('files_saved', {})
            })
        
        return status
    
    def validate_existing_data(self, data_file: Optional[Path] = None) -> Dict[str, Any]:
        """Validate existing collected data"""
        if not data_file:
            # Find most recent data file
            org_files = FileManager.get_files_by_pattern(
                self.output_dir / "organizations", "*_organizations_complete.json"
            )
            
            if not org_files:
                return {'error': 'No existing data files found'}
            
            data_file = sorted(org_files)[-1]  # Most recent file
        
        logger.info(f"Validating data from {data_file}")
        
        try:
            data = DataLoader.load_json(data_file)
            organizations = data.get('organizations', [])
            
            validation_results = {
                'file_path': str(data_file),
                'total_organizations': len(organizations),
                'valid_organizations': 0,
                'invalid_organizations': 0,
                'total_offices': 0,
                'valid_offices': 0,
                'invalid_offices': 0,
                'validation_errors': []
            }
            
            for org in organizations:
                org_valid, org_errors = self._validate_organization(org)
                
                if org_valid:
                    validation_results['valid_organizations'] += 1
                else:
                    validation_results['invalid_organizations'] += 1
                    validation_results['validation_errors'].append({
                        'organization_id': org.get('Id'),
                        'type': 'organization',
                        'errors': org_errors
                    })
                
                offices = org.get('Offices', [])
                validation_results['total_offices'] += len(offices)
                
                for office in offices:
                    office_valid, office_errors = self._validate_office(office)
                    
                    if office_valid:
                        validation_results['valid_offices'] += 1
                    else:
                        validation_results['invalid_offices'] += 1
                        validation_results['validation_errors'].append({
                            'organization_id': org.get('Id'),
                            'office_id': office.get('OfficeId'),
                            'type': 'office',
                            'errors': office_errors
                        })
            
            logger.info(f"Validation complete: {validation_results['valid_organizations']}/{validation_results['total_organizations']} orgs valid, "
                       f"{validation_results['valid_offices']}/{validation_results['total_offices']} offices valid")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate data: {e}")
            return {'error': str(e)}