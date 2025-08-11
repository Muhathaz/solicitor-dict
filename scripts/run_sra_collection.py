#!/usr/bin/env python3
"""
SRA Data Collection Script

Command-line interface for collecting SRA organization and office data.
Supports full collection, resume, status checking, and incremental updates.
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collectors import SRACollector, SRAAPIClient, SRAAPIError
from utils import setup_logging, get_logger, ConfigLoader


def setup_arguments():
    """Setup command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="SRA Data Collection Tool for UK Solicitors Directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode full                    # Full collection of all organizations
  %(prog)s --resume                       # Resume interrupted collection
  %(prog)s --status                       # Check collection status
  %(prog)s --test                         # Test API connection
  %(prog)s --validate                     # Validate existing data
  %(prog)s --mode full --output /tmp/sra  # Custom output directory
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["full", "incremental"],
        help="Collection mode: full (all data) or incremental (updates only)"
    )
    
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="Resume interrupted collection"
    )
    
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show collection status and exit"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test API connection and exit"
    )
    
    parser.add_argument(
        "--validate", 
        action="store_true",
        help="Validate existing data and exit"
    )
    
    parser.add_argument(
        "--output", 
        type=str,
        help="Output directory (default: data/raw/sra)"
    )
    
    parser.add_argument(
        "--config", 
        type=str,
        default="config",
        help="Configuration directory (default: config)"
    )
    
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Minimal output (errors only)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose output (debug level)"
    )
    
    return parser


def test_api_connection(config: ConfigLoader) -> bool:
    """Test SRA API connection"""
    print("Testing SRA API connection...")
    
    try:
        with SRAAPIClient(config) as client:
            if client.test_connection():
                print("✅ API connection successful")
                
                # Get and display API info
                api_info = client.get_api_info()
                print(f"   Base URL: {api_info['base_url']}")
                print(f"   Rate Limit: {api_info['rate_limit']['requests_per_period']} "
                      f"requests per {api_info['rate_limit']['period_seconds']}s")
                print(f"   Timeout: {api_info['timeout']}s")
                
                return True
            else:
                print("❌ API connection failed")
                return False
                
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False


def show_collection_status(collector: SRACollector):
    """Show collection status"""
    print("SRA Collection Status")
    print("=" * 50)
    
    status = collector.get_collection_status()
    
    if status['has_previous_collection']:
        print(f"✅ Previous collection found")
        print(f"   Date: {status['last_collection_date']}")
        print(f"   Completed: {'Yes' if status['last_collection_completed'] else 'No'}")
        print(f"   Organizations: {status['last_organizations_count']}")
        
        if status['files_from_last_collection']:
            print("   Files:")
            for key, path in status['files_from_last_collection'].items():
                print(f"     {key}: {path}")
    else:
        print("❌ No previous collection found")
    
    print(f"\nCurrent Stats:")
    current = status['current_stats']
    print(f"   Organizations processed: {current['organizations_processed']}")
    print(f"   Offices processed: {current['offices_processed']}")
    print(f"   Errors: {current['errors']}")


def run_collection(collector: SRACollector, mode: str, resume: bool = False) -> bool:
    """Run data collection"""
    print(f"Starting SRA data collection (mode: {mode})")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Run collection
        result = collector.collect_organizations(resume=resume)
        
        duration = time.time() - start_time
        
        if result['success']:
            print(f"✅ Collection completed successfully in {duration:.1f}s")
            print(f"   Organizations collected: {result['organizations_collected']}")
            print(f"   Offices collected: {result['offices_collected']}")
            print(f"   Report saved to: {result['report_file']}")
            
            print("\nFiles saved:")
            for key, path in result['files_saved'].items():
                print(f"   {key}: {path}")
            
            return True
            
        else:
            print(f"❌ Collection failed: {result['error']}")
            print(f"   Organizations processed: {result['organizations_collected']}")
            print(f"   Offices processed: {result['offices_collected']}")
            return False
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Collection interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed with error: {e}")
        return False


def validate_existing_data(collector: SRACollector) -> bool:
    """Validate existing data"""
    print("Validating existing SRA data...")
    print("=" * 50)
    
    try:
        result = collector.validate_existing_data()
        
        if 'error' in result:
            print(f"❌ Validation failed: {result['error']}")
            return False
        
        print(f"✅ Validation completed")
        print(f"   File: {result['file_path']}")
        print(f"   Organizations: {result['valid_organizations']}/{result['total_organizations']} valid")
        print(f"   Offices: {result['valid_offices']}/{result['total_offices']} valid")
        
        if result['validation_errors']:
            print(f"   Validation errors: {len(result['validation_errors'])}")
            
            # Show first few errors as examples
            for i, error in enumerate(result['validation_errors'][:5]):
                print(f"     {i+1}. {error['type']} {error.get('organization_id', 'N/A')}: {error['errors']}")
            
            if len(result['validation_errors']) > 5:
                print(f"     ... and {len(result['validation_errors']) - 5} more errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def print_attribution():
    """Print SRA attribution requirement"""
    print("\n" + "=" * 80)
    print("SRA DATA ATTRIBUTION REQUIREMENT")
    print("=" * 80)
    print("This application uses data from the Solicitors Regulation Authority.")
    print("Source: http://www.sra.org.uk/sra/how-we-work/web-service/attribution.page")
    print("=" * 80)


def main():
    """Main entry point"""
    parser = setup_arguments()
    args = parser.parse_args()
    
    # Handle log level
    log_level = "INFO"
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose or args.log_level == "DEBUG":
        log_level = "DEBUG"
    elif args.log_level:
        log_level = args.log_level
    
    # Setup logging
    try:
        config_path = Path(args.config) / "settings.yaml"
        setup_logging(config_path)
        logger = get_logger(__name__)
        logger.info(f"SRA collection script started with args: {vars(args)}")
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        sys.exit(1)
    
    # Load configuration
    try:
        config = ConfigLoader(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize collector
    try:
        collector = SRACollector(config, args.output)
    except Exception as e:
        print(f"Failed to initialize SRA collector: {e}")
        sys.exit(1)
    
    success = True
    
    try:
        # Handle different modes
        if args.test:
            success = test_api_connection(config)
            
        elif args.status:
            show_collection_status(collector)
            
        elif args.validate:
            success = validate_existing_data(collector)
            
        elif args.mode or args.resume:
            mode = args.mode or "full"
            success = run_collection(collector, mode, args.resume)
            
        else:
            parser.print_help()
            print("\nError: Must specify --mode, --resume, --status, --test, or --validate")
            sys.exit(1)
        
        # Always show attribution
        print_attribution()
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        success = False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()