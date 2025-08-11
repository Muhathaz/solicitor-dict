#!/usr/bin/env python3
"""
Output Generation Script - Phase 4

Generates multiple output formats from the processed UK solicitors dataset:
- JSON (compact and formatted)
- CSV (organizations and offices)
- Database-ready formats
- Summary statistics
- Data quality reports
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter

class OutputGenerator:
    """Generates multiple output formats from processed data"""
    
    def __init__(self, input_file: Path, output_dir: Path):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load processed data
        with open(input_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.organizations = self.data.get('Organisations', [])
        self.processing_info = self.data.get('ProcessingInfo', {})
        
    def generate_compact_json(self):
        """Generate compact JSON format for production use"""
        print("📄 Generating compact JSON format...")
        
        compact_data = {
            'version': '1.0',
            'generated': datetime.now().isoformat(),
            'count': len(self.organizations),
            'organizations': []
        }
        
        for org in self.organizations:
            # Create compact organization record
            compact_org = {
                'id': org.get('Id'),
                'sra_number': org.get('SraNumber'),
                'name': org.get('PracticeName'),
                'type': org.get('OrganisationType'),
                'quality_score': org.get('DataQualityScore', 0),
                'quality_category': org.get('DataQualityCategory', 'Unknown'),
                'offices': []
            }
            
            # Add optional fields if present
            if org.get('AuthorisationType'):
                compact_org['authorization_type'] = org.get('AuthorisationType')
            if org.get('Regulator'):
                compact_org['regulator'] = org.get('Regulator')
            
            # Process offices
            for office in org.get('Offices', []):
                compact_office = {
                    'id': office.get('OfficeId'),
                    'name': office.get('Name'),
                    'type': office.get('OfficeType'),
                    'address': {
                        'line1': office.get('Address1'),
                        'line2': office.get('Address2') if office.get('Address2') else None,
                        'town': office.get('Town'),
                        'county': office.get('County') if office.get('County') else None,
                        'postcode': office.get('Postcode'),
                        'country': office.get('Country')
                    },
                    'contact': {}
                }
                
                # Add contact info if present
                if office.get('PhoneNumber'):
                    compact_office['contact']['phone'] = office.get('PhoneNumber')
                if office.get('Email'):
                    compact_office['contact']['email'] = office.get('Email')
                if office.get('Website'):
                    compact_office['contact']['website'] = office.get('Website')
                
                # Remove empty contact object if no contact info
                if not compact_office['contact']:
                    del compact_office['contact']
                
                compact_org['offices'].append(compact_office)
            
            compact_data['organizations'].append(compact_org)
        
        # Save compact JSON
        output_file = self.output_dir / 'uk_solicitors_compact.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(compact_data, f, ensure_ascii=False, separators=(',', ':'))
        
        print(f"   ✅ Compact JSON saved: {output_file}")
        return output_file
    
    def generate_csv_outputs(self):
        """Generate CSV formats for data analysis"""
        print("📊 Generating CSV formats...")
        
        # Organizations CSV
        org_file = self.output_dir / 'organizations.csv'
        office_file = self.output_dir / 'offices.csv'
        
        # Organizations CSV
        with open(org_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Id', 'SraNumber', 'PracticeName', 'OrganisationType', 
                'AuthorisationType', 'Regulator', 'Constitution', 'Type',
                'NoOfOffices', 'DataQualityScore', 'DataQualityCategory'
            ])
            
            # Data rows
            for org in self.organizations:
                writer.writerow([
                    org.get('Id', ''),
                    org.get('SraNumber', ''),
                    org.get('PracticeName', ''),
                    org.get('OrganisationType', ''),
                    org.get('AuthorisationType', ''),
                    org.get('Regulator', ''),
                    org.get('Constitution', ''),
                    org.get('Type', ''),
                    org.get('NoOfOffices', ''),
                    org.get('DataQualityScore', ''),
                    org.get('DataQualityCategory', '')
                ])
        
        # Offices CSV
        with open(office_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'OrganizationId', 'OfficeId', 'Name', 'OfficeType',
                'Address1', 'Address2', 'Address3', 'Address4',
                'Town', 'County', 'Postcode', 'Country',
                'PhoneNumber', 'Email', 'Website'
            ])
            
            # Data rows
            for org in self.organizations:
                org_id = org.get('Id', '')
                for office in org.get('Offices', []):
                    writer.writerow([
                        org_id,
                        office.get('OfficeId', ''),
                        office.get('Name', ''),
                        office.get('OfficeType', ''),
                        office.get('Address1', ''),
                        office.get('Address2', ''),
                        office.get('Address3', ''),
                        office.get('Address4', ''),
                        office.get('Town', ''),
                        office.get('County', ''),
                        office.get('Postcode', ''),
                        office.get('Country', ''),
                        office.get('PhoneNumber', ''),
                        office.get('Email', ''),
                        office.get('Website', '')
                    ])
        
        print(f"   ✅ Organizations CSV saved: {org_file}")
        print(f"   ✅ Offices CSV saved: {office_file}")
        return org_file, office_file
    
    def generate_database_ready_format(self):
        """Generate database-ready JSON format for Supabase"""
        print("🗄️  Generating database-ready format...")
        
        db_organizations = []
        db_offices = []
        
        for org in self.organizations:
            # Organization record for database
            db_org = {
                'id': org.get('Id'),
                'sra_number': org.get('SraNumber'),
                'practice_name': org.get('PracticeName'),
                'organization_type': org.get('OrganisationType'),
                'authorization_type': org.get('AuthorisationType'),
                'authorization_status': org.get('AuthorisationStatus'),
                'regulator': org.get('Regulator'),
                'constitution': org.get('Constitution'),
                'type': org.get('Type'),
                'number_of_offices': org.get('NoOfOffices'),
                'data_quality_score': org.get('DataQualityScore'),
                'data_quality_category': org.get('DataQualityCategory'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Handle optional fields
            if org.get('AuthorisationDate'):
                db_org['authorization_date'] = org.get('AuthorisationDate')
            if org.get('FreelanceBasis'):
                db_org['freelance_basis'] = org.get('FreelanceBasis')
            
            db_organizations.append(db_org)
            
            # Office records for database
            for office in org.get('Offices', []):
                db_office = {
                    'id': office.get('OfficeId'),
                    'organization_id': org.get('Id'),
                    'name': office.get('Name'),
                    'office_type': office.get('OfficeType'),
                    'address_line_1': office.get('Address1'),
                    'address_line_2': office.get('Address2'),
                    'address_line_3': office.get('Address3'),
                    'address_line_4': office.get('Address4'),
                    'town': office.get('Town'),
                    'county': office.get('County'),
                    'postcode': office.get('Postcode'),
                    'country': office.get('Country'),
                    'phone_number': office.get('PhoneNumber'),
                    'email': office.get('Email'),
                    'website': office.get('Website'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                db_offices.append(db_office)
        
        # Save database-ready formats
        db_org_file = self.output_dir / 'db_organizations.json'
        db_office_file = self.output_dir / 'db_offices.json'
        
        with open(db_org_file, 'w', encoding='utf-8') as f:
            json.dump(db_organizations, f, ensure_ascii=False, indent=2)
        
        with open(db_office_file, 'w', encoding='utf-8') as f:
            json.dump(db_offices, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Database organizations saved: {db_org_file}")
        print(f"   ✅ Database offices saved: {db_office_file}")
        return db_org_file, db_office_file
    
    def generate_statistics_report(self):
        """Generate comprehensive statistics report"""
        print("📈 Generating statistics report...")
        
        stats = {
            'dataset_info': {
                'total_organizations': len(self.organizations),
                'total_offices': sum(len(org.get('Offices', [])) for org in self.organizations),
                'generated_date': datetime.now().isoformat(),
                'source_file': str(self.input_file),
                'processing_info': self.processing_info
            },
            'quality_distribution': {},
            'geographic_distribution': {},
            'organization_types': {},
            'office_types': {},
            'contact_completeness': {},
            'data_completeness': {}
        }
        
        # Quality distribution
        quality_counter = Counter()
        score_sum = 0
        for org in self.organizations:
            quality_cat = org.get('DataQualityCategory', 'Unknown')
            quality_counter[quality_cat] += 1
            score_sum += org.get('DataQualityScore', 0)
        
        stats['quality_distribution'] = {
            'distribution': dict(quality_counter),
            'average_score': score_sum / len(self.organizations) if self.organizations else 0
        }
        
        # Geographic distribution
        country_counter = Counter()
        county_counter = Counter()
        for org in self.organizations:
            for office in org.get('Offices', []):
                country = office.get('Country', 'Unknown')
                county = office.get('County', 'Unknown')
                country_counter[country] += 1
                if county != 'Unknown':
                    county_counter[county] += 1
        
        stats['geographic_distribution'] = {
            'by_country': dict(country_counter.most_common()),
            'by_county': dict(county_counter.most_common(20))  # Top 20 counties
        }
        
        # Organization and office types
        org_type_counter = Counter()
        office_type_counter = Counter()
        
        for org in self.organizations:
            org_type = org.get('OrganisationType', 'Unknown')
            org_type_counter[org_type] += 1
            
            for office in org.get('Offices', []):
                office_type = office.get('OfficeType', 'Unknown')
                office_type_counter[office_type] += 1
        
        stats['organization_types'] = dict(org_type_counter)
        stats['office_types'] = dict(office_type_counter)
        
        # Contact completeness
        total_offices = stats['dataset_info']['total_offices']
        phone_count = 0
        email_count = 0
        website_count = 0
        
        for org in self.organizations:
            for office in org.get('Offices', []):
                if office.get('PhoneNumber'):
                    phone_count += 1
                if office.get('Email'):
                    email_count += 1
                if office.get('Website'):
                    website_count += 1
        
        stats['contact_completeness'] = {
            'phone_numbers': {
                'count': phone_count,
                'percentage': (phone_count / total_offices * 100) if total_offices else 0
            },
            'email_addresses': {
                'count': email_count,
                'percentage': (email_count / total_offices * 100) if total_offices else 0
            },
            'websites': {
                'count': website_count,
                'percentage': (website_count / total_offices * 100) if total_offices else 0
            }
        }
        
        # Save statistics
        stats_file = self.output_dir / 'dataset_statistics.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Statistics report saved: {stats_file}")
        return stats_file
    
    def generate_quality_dashboard_data(self):
        """Generate data for quality dashboard"""
        print("📊 Generating quality dashboard data...")
        
        dashboard_data = {
            'summary': {
                'total_organizations': len(self.organizations),
                'total_offices': sum(len(org.get('Offices', [])) for org in self.organizations),
                'average_quality_score': 0,
                'processing_date': self.processing_info.get('processed_date', '')
            },
            'quality_metrics': [],
            'geographic_breakdown': [],
            'top_quality_organizations': [],
            'improvement_areas': []
        }
        
        # Calculate quality metrics
        quality_scores = []
        quality_categories = Counter()
        
        for org in self.organizations:
            score = org.get('DataQualityScore', 0)
            quality_scores.append(score)
            category = org.get('DataQualityCategory', 'Unknown')
            quality_categories[category] += 1
        
        dashboard_data['summary']['average_quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Quality distribution for charts
        total_orgs = len(self.organizations)
        for category, count in quality_categories.items():
            dashboard_data['quality_metrics'].append({
                'category': category,
                'count': count,
                'percentage': (count / total_orgs * 100) if total_orgs else 0
            })
        
        # Geographic quality breakdown
        country_quality = {}
        for org in self.organizations:
            score = org.get('DataQualityScore', 0)
            for office in org.get('Offices', []):
                country = office.get('Country', 'Unknown')
                if country not in country_quality:
                    country_quality[country] = {'scores': [], 'count': 0}
                country_quality[country]['scores'].append(score)
                country_quality[country]['count'] += 1
        
        for country, data in country_quality.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            dashboard_data['geographic_breakdown'].append({
                'country': country,
                'office_count': data['count'],
                'average_quality': round(avg_score, 1)
            })
        
        # Top quality organizations (sample)
        sorted_orgs = sorted(self.organizations, 
                           key=lambda x: x.get('DataQualityScore', 0), 
                           reverse=True)
        
        for org in sorted_orgs[:20]:  # Top 20
            dashboard_data['top_quality_organizations'].append({
                'name': org.get('PracticeName', '')[:50],
                'quality_score': org.get('DataQualityScore', 0),
                'office_count': len(org.get('Offices', [])),
                'location': org.get('Offices', [{}])[0].get('Town', 'Unknown') if org.get('Offices') else 'Unknown'
            })
        
        # Save dashboard data
        dashboard_file = self.output_dir / 'quality_dashboard.json'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Quality dashboard data saved: {dashboard_file}")
        return dashboard_file
    
    def generate_all_outputs(self):
        """Generate all output formats"""
        print("🚀 GENERATING ALL OUTPUT FORMATS")
        print("="*80)
        
        outputs = {}
        
        # Generate all formats
        outputs['compact_json'] = self.generate_compact_json()
        outputs['csv_files'] = self.generate_csv_outputs()
        outputs['database_files'] = self.generate_database_ready_format()
        outputs['statistics'] = self.generate_statistics_report()
        outputs['dashboard'] = self.generate_quality_dashboard_data()
        
        # Generate summary
        summary = {
            'generation_date': datetime.now().isoformat(),
            'source_file': str(self.input_file),
            'output_directory': str(self.output_dir),
            'files_generated': {
                'compact_json': str(outputs['compact_json'].name),
                'organizations_csv': str(outputs['csv_files'][0].name),
                'offices_csv': str(outputs['csv_files'][1].name),
                'database_organizations': str(outputs['database_files'][0].name),
                'database_offices': str(outputs['database_files'][1].name),
                'statistics_report': str(outputs['statistics'].name),
                'quality_dashboard': str(outputs['dashboard'].name)
            },
            'dataset_summary': {
                'organizations': len(self.organizations),
                'offices': sum(len(org.get('Offices', [])) for org in self.organizations),
                'average_quality_score': sum(org.get('DataQualityScore', 0) for org in self.organizations) / len(self.organizations) if self.organizations else 0
            }
        }
        
        # Save generation summary
        summary_file = self.output_dir / 'generation_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Generation summary saved: {summary_file}")
        
        return outputs, summary

def main():
    """Main output generation function"""
    input_file = Path("data/processed/sra/uk_solicitors_cleaned.json")
    output_dir = Path("data/output")
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("   Please run Phase 3 processing first")
        return
    
    generator = OutputGenerator(input_file, output_dir)
    outputs, summary = generator.generate_all_outputs()
    
    # Print summary
    print(f"\n📈 OUTPUT GENERATION COMPLETE")
    print("="*80)
    print(f"✅ Organizations processed: {summary['dataset_summary']['organizations']:,}")
    print(f"✅ Offices processed: {summary['dataset_summary']['offices']:,}")
    print(f"✅ Average quality score: {summary['dataset_summary']['average_quality_score']:.1f}")
    print(f"📁 Output directory: {output_dir}")
    
    print(f"\n📋 FILES GENERATED:")
    for file_type, filename in summary['files_generated'].items():
        file_path = output_dir / filename
        file_size_mb = file_path.stat().st_size / (1024 * 1024) if file_path.exists() else 0
        print(f"   • {file_type}: {filename} ({file_size_mb:.1f} MB)")
    
    print(f"\n✅ Phase 4 output generation complete!")
    print(f"🎯 Ready for database integration and application deployment")

if __name__ == "__main__":
    main()