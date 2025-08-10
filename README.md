# UK Solicitors Data Processing

A comprehensive Python environment for collecting, processing, and managing data for the UK Solicitors Directory web application.

## 🎯 Project Overview

This project provides a complete data processing pipeline to collect and process solicitor information from multiple sources:

- **SRA API**: Official solicitor registration data
- **Google Places**: Business location and review data  
- **Review Platforms**: Trustpilot, Yelp, ReviewSolicitors
- **Web Scraping**: Additional website data

## 🏗️ Project Structure

```
uk-solicitors-data-processing/
├── config/                     # Configuration files
│   ├── settings.yaml          # Main application settings
│   └── .env.example          # Environment variables template
├── src/                       # Source code
│   ├── collectors/           # Data collection modules
│   │   ├── __init__.py
│   │   ├── sra_collector.py
│   │   ├── google_places_collector.py
│   │   ├── review_collector.py
│   │   └── website_scraper.py
│   ├── processors/          # Data processing modules
│   │   ├── __init__.py
│   │   ├── data_cleaner.py
│   │   ├── entity_resolver.py
│   │   └── sentiment_analyzer.py
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py       # Logging configuration
│   │   ├── file_manager.py # File operations
│   │   └── validators.py   # Data validation
│   └── __init__.py
├── data/                   # Data storage
│   ├── raw/               # Raw collected data
│   │   ├── sra/
│   │   ├── google_places/
│   │   ├── reviews/
│   │   └── websites/
│   ├── processed/         # Processed data
│   │   ├── cleaned/
│   │   ├── enhanced/
│   │   └── validated/
│   └── output/           # Final output data
├── logs/                 # Application logs
├── reports/              # Generated reports
├── tests/               # Test files
├── scripts/             # Utility scripts
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for version control)

### 1. Environment Setup

#### Option A: Using venv (Recommended)

```bash
# Clone or navigate to the project directory
cd uk-solicitors-data-processing

# Create virtual environment
python3 -m venv uk-solicitors-data

# Activate virtual environment
# On Linux/macOS:
source uk-solicitors-data/bin/activate
# On Windows:
uk-solicitors-data\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n uk-solicitors-data python=3.9
conda activate uk-solicitors-data

# Install dependencies
pip install -r requirements.txt
playwright install
```

### 2. Configuration Setup

```bash
# Copy environment template
cp config/.env.example config/.env

# Edit the .env file with your API keys
nano config/.env  # or use your preferred editor
```

Required API keys:
- `SRA_API_KEY`: From SRA developer portal
- `GOOGLE_PLACES_API_KEY`: From Google Cloud Console
- `TRUSTPILOT_API_KEY`: From Trustpilot Business
- `OPENAI_API_KEY`: From OpenAI (optional, for AI processing)

### 3. Verification

Run the setup verification script:

```bash
python scripts/verify_setup.py
```

This will check:
- ✅ Python environment
- ✅ Package installations
- ✅ Configuration files
- ✅ Directory structure
- ✅ API connectivity (if keys provided)

## 📚 Usage Examples

### Basic Data Collection

```python
from src.utils import setup_logging, get_logger
from src.collectors import SRACollector

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize collector
collector = SRACollector()

# Collect data
solicitors = collector.search_solicitors(
    location="London",
    practice_area="Commercial Law"
)

logger.info(f"Collected {len(solicitors)} solicitor records")
```

### Data Processing Pipeline

```python
from src.processors import DataCleaner, EntityResolver
from src.utils import DataValidator, OutputManager

# Load raw data
raw_data = DataLoader.load_json("data/raw/sra/solicitors.json")

# Clean data
cleaner = DataCleaner()
cleaned_data = cleaner.clean_dataset(raw_data)

# Validate data
validator = DataValidator()
validation_result = validator.validate_dataset(cleaned_data, "sra_record")

# Save processed data
output_manager = OutputManager()
output_manager.save_data(cleaned_data, "processed_solicitors", format="json")
```

### Configuration Management

```python
from src.utils import ConfigLoader

# Load configuration
config = ConfigLoader()

# Get specific settings
api_rate_limit = config.get_setting("api_rate_limits.sra_api.requests_per_minute")
batch_size = config.get_setting("processing.batch_size", default=100)

# Load environment variables
env_vars = config.load_env_vars()
api_key = env_vars.get("SRA_API_KEY")
```

## 🔧 Configuration Guide

### Settings.yaml Structure

The main configuration file contains:

- **API Rate Limits**: Control request frequency
- **File Paths**: Define data storage locations
- **Processing Parameters**: Batch sizes, timeouts, etc.
- **Logging Configuration**: Log levels, file rotation
- **Data Validation Rules**: Field requirements and types
- **Data Sources**: API endpoints and URLs

### Environment Variables

Key environment variables to configure:

```env
# Required API Keys
SRA_API_KEY=your_sra_api_key_here
GOOGLE_PLACES_API_KEY=your_google_api_key_here

# Optional Settings
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=5
ENABLE_RATE_LIMITING=true
DEBUG_MODE=false
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_collectors.py -v
```

## 📊 Logging and Monitoring

### Log Files

- `logs/app.log`: General application logs
- `logs/error.log`: Error-specific logs
- `logs/collectors.log`: Data collection logs
- `logs/processors.log`: Data processing logs

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened
- `ERROR`: Serious problem occurred
- `CRITICAL`: Very serious error occurred

### Monitoring Features

- Colored console output for better readability
- Progress bars for long-running operations
- Performance metrics logging
- Structured JSON logging for analysis tools
- Log rotation to prevent disk space issues

## 🛡️ Data Validation

### Built-in Validators

- Email address format validation
- UK phone number validation
- UK postcode validation
- SRA solicitor number validation
- Date format validation
- Rating value validation (0-5 scale)

### Quality Assessment

- Duplicate detection
- Missing data analysis
- Data type validation
- Completeness scoring
- Quality rating system (Excellent/Good/Fair/Poor)

### Schema Validation

JSON Schema validation for:
- SRA records
- Google Places records  
- Review records
- Custom data formats

## 🔄 Data Processing Pipeline

### Collection Phase

1. **SRA Data Collection**: Official solicitor records
2. **Google Places Collection**: Business information and reviews
3. **Review Platform Collection**: Trustpilot, Yelp, ReviewSolicitors
4. **Website Scraping**: Additional firm information

### Processing Phase

1. **Data Cleaning**: Remove duplicates, standardize formats
2. **Entity Resolution**: Match records across sources
3. **Enhancement**: Add computed fields, geocoding
4. **Validation**: Ensure data quality and completeness
5. **Output Generation**: Multiple formats (JSON, CSV, Parquet)

## 🚨 Error Handling

### Common Issues and Solutions

**Issue**: API rate limit exceeded
```python
# Solution: Implement exponential backoff
import time
from src.utils import get_logger

logger = get_logger(__name__)

for attempt in range(max_retries):
    try:
        response = api_call()
        break
    except RateLimitError:
        wait_time = 2 ** attempt
        logger.warning(f"Rate limit hit, waiting {wait_time}s")
        time.sleep(wait_time)
```

**Issue**: Invalid data format
```python
# Solution: Use validation before processing
from src.utils import DataValidator

validator = DataValidator()
result = validator.validate_record(record, "sra_record")

if not result["valid"]:
    logger.error(f"Invalid record: {result['errors']}")
    continue
```

## 📈 Performance Optimization

### Best Practices

1. **Batch Processing**: Process data in configurable chunks
2. **Rate Limiting**: Respect API limits with built-in throttling
3. **Concurrent Processing**: Use thread pools for I/O operations
4. **Caching**: Cache API responses to reduce redundant calls
5. **Progress Tracking**: Monitor long-running operations

### Memory Management

```python
# Process large datasets in chunks
from src.utils import ConfigLoader

config = ConfigLoader()
chunk_size = config.get_setting("processing.chunk_size", 1000)

for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    process_chunk(chunk)
```

## 🔒 Security Considerations

- **API Keys**: Store in environment variables, never commit to git
- **Data Anonymization**: Remove or hash PII where appropriate
- **Access Control**: Limit file permissions on sensitive data
- **Logging**: Avoid logging sensitive information
- **HTTPS**: Use secure connections for all API calls

## 🤝 Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep functions focused and testable

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-collector

# Make changes and commit
git add .
git commit -m "Add new data collector for XYZ API"

# Push and create pull request
git push origin feature/new-collector
```

### Adding New Collectors

1. Create new file in `src/collectors/`
2. Implement base collector interface
3. Add configuration to `settings.yaml`
4. Write tests in `tests/test_collectors.py`
5. Update documentation

## 📞 Support and Troubleshooting

### Common Commands

```bash
# Check Python version
python --version

# List installed packages
pip list

# Check virtual environment
which python

# View logs
tail -f logs/app.log

# Run in debug mode
LOG_LEVEL=DEBUG python scripts/run_collection.py
```

### Getting Help

1. Check the logs for error messages
2. Verify configuration settings
3. Test API connectivity
4. Review data validation results
5. Check system resources (memory, disk space)

## 📄 License

This project is proprietary software developed for the UK Solicitors Directory application.

## 🔄 Next Steps

After completing the setup:

1. **Configure API Keys**: Add your API credentials to `.env`
2. **Test Collectors**: Run individual collector tests
3. **Process Sample Data**: Try the validation and processing pipeline
4. **Set Up Monitoring**: Configure log aggregation and alerting
5. **Scale Processing**: Implement distributed processing for large datasets
6. **Integrate with Supabase**: Connect processed data to the main database

---

**Note**: This environment serves as the data processing backbone for the UK Solicitors Directory. All processed data will eventually be integrated with the Supabase database powering the main web application.