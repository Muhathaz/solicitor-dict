#!/usr/bin/env python3
"""
Simplified SRA Data Collection Script
Direct collection without complex dependencies
"""

import json
import requests
import yaml
import time
from datetime import datetime
from pathlib import Path

def load_config():
    """Load configuration from settings.yaml"""
    config_path = Path("config/settings.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def collect_sra_data():
    """Collect SRA data directly"""
    print("Starting SRA data collection...")
    
    # Load configuration
    config = load_config()
    sra_config = config['data_sources']['sra_api']
    
    base_url = sra_config['base_url']
    endpoint = sra_config['endpoints']['organizations']
    api_key = sra_config['api_key']
    
    full_url = f"{base_url.rstrip('/')}{endpoint}"
    
    print(f"Collecting from: {full_url}")
    
    # Make API request
    headers = {'Ocp-Apim-Subscription-Key': api_key}
    
    try:
        response = requests.get(full_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        org_count = data.get('Count', 0)
        organizations = data.get('Organisations', [])
        
        print(f"✅ Successfully retrieved {len(organizations)} organizations")
        print(f"   API reports total count: {org_count}")
        
        # Create output directories
        output_dir = Path("data/raw/sra")
        org_dir = output_dir / "organizations"
        metadata_dir = output_dir / "metadata"
        
        org_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main data
        main_file = org_dir / f"organizations_complete_{timestamp}.json"
        with open(main_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Organizations data saved to: {main_file}")
        
        # Save metadata
        metadata = {
            'collection_timestamp': datetime.now().isoformat(),
            'api_endpoint': full_url,
            'total_organizations': org_count,
            'organizations_retrieved': len(organizations),
            'file_size_bytes': main_file.stat().st_size,
            'api_response_time': response.elapsed.total_seconds()
        }
        
        metadata_file = metadata_dir / f"organizations_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata saved to: {metadata_file}")
        
        # Create summary
        print("\n" + "="*60)
        print("COLLECTION SUMMARY")
        print("="*60)
        print(f"Total Organizations: {org_count}")
        print(f"Organizations Retrieved: {len(organizations)}")
        print(f"File Size: {main_file.stat().st_size:,} bytes")
        print(f"Collection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Show sample data
        if organizations:
            print("\nSample Organization:")
            sample = organizations[0]
            print(f"  ID: {sample.get('Id')}")
            print(f"  SRA Number: {sample.get('SraNumber')}")
            print(f"  Practice Name: {sample.get('PracticeName')}")
            print(f"  Offices: {len(sample.get('Offices', []))}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        return False

if __name__ == "__main__":
    success = collect_sra_data()
    print("\n" + "="*80)
    print("SRA DATA ATTRIBUTION REQUIREMENT")
    print("="*80)
    print("This application uses data from the Solicitors Regulation Authority.")
    print("Source: http://www.sra.org.uk/sra/how-we-work/web-service/attribution.page")
    print("="*80)
    
    if success:
        print("\n✅ Data collection completed successfully!")
    else:
        print("\n❌ Data collection failed!")