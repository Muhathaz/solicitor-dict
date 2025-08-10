"""
File management utilities for UK Solicitors Data Processing
"""

import json
import os
import shutil
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import csv
import yaml
import pandas as pd
from datetime import datetime

from .logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """Utility class for file operations"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if it doesn't"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return path
    
    @staticmethod
    def file_exists(path: Union[str, Path]) -> bool:
        """Check if file exists"""
        return Path(path).exists()
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        return Path(path).stat().st_size
    
    @staticmethod
    def get_file_age(path: Union[str, Path]) -> float:
        """Get file age in seconds"""
        stat = Path(path).stat()
        return datetime.now().timestamp() - stat.st_mtime
    
    @staticmethod
    def backup_file(path: Union[str, Path], backup_suffix: str = ".backup") -> Path:
        """Create a backup of a file"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        backup_path = path.with_suffix(path.suffix + backup_suffix)
        shutil.copy2(path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    @staticmethod
    def safe_delete(path: Union[str, Path], backup: bool = True) -> bool:
        """Safely delete a file with optional backup"""
        path = Path(path)
        if not path.exists():
            logger.warning(f"File not found for deletion: {path}")
            return False
        
        try:
            if backup:
                FileManager.backup_file(path)
            
            path.unlink()
            logger.info(f"File deleted: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False
    
    @staticmethod
    def get_files_by_pattern(directory: Union[str, Path], pattern: str) -> List[Path]:
        """Get files matching a pattern"""
        directory = Path(directory)
        files = list(directory.glob(pattern))
        logger.debug(f"Found {len(files)} files matching pattern '{pattern}' in {directory}")
        return files
    
    @staticmethod
    def get_directory_size(path: Union[str, Path]) -> int:
        """Get total size of directory in bytes"""
        path = Path(path)
        total_size = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        logger.debug(f"Directory size for {path}: {total_size} bytes")
        return total_size
    
    @staticmethod
    def clean_directory(path: Union[str, Path], keep_subdirs: bool = True) -> int:
        """Clean directory contents, optionally keeping subdirectories"""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Directory not found: {path}")
            return 0
        
        deleted_count = 0
        
        for item in path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
                elif item.is_dir() and not keep_subdirs:
                    shutil.rmtree(item)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {item}: {e}")
        
        logger.info(f"Cleaned directory {path}: {deleted_count} items deleted")
        return deleted_count


class DataLoader:
    """Utility class for loading various data formats"""
    
    @staticmethod
    def load_json(path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON file"""
        path = Path(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded JSON from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {path}: {e}")
            raise
    
    @staticmethod
    def save_json(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> bool:
        """Save data as JSON"""
        path = Path(path)
        try:
            FileManager.ensure_directory(path.parent)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            logger.debug(f"Saved JSON to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to {path}: {e}")
            return False
    
    @staticmethod
    def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML file"""
        path = Path(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.debug(f"Loaded YAML from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load YAML from {path}: {e}")
            raise
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save data as YAML"""
        path = Path(path)
        try:
            FileManager.ensure_directory(path.parent)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"Saved YAML to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save YAML to {path}: {e}")
            return False
    
    @staticmethod
    def load_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load CSV file as pandas DataFrame"""
        path = Path(path)
        try:
            df = pd.read_csv(path, **kwargs)
            logger.debug(f"Loaded CSV from {path}: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV from {path}: {e}")
            raise
    
    @staticmethod
    def save_csv(df: pd.DataFrame, path: Union[str, Path], **kwargs) -> bool:
        """Save DataFrame as CSV"""
        path = Path(path)
        try:
            FileManager.ensure_directory(path.parent)
            df.to_csv(path, index=False, **kwargs)
            logger.debug(f"Saved CSV to {path}: {len(df)} rows")
            return True
        except Exception as e:
            logger.error(f"Failed to save CSV to {path}: {e}")
            return False
    
    @staticmethod
    def load_pickle(path: Union[str, Path]) -> Any:
        """Load pickle file"""
        path = Path(path)
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"Loaded pickle from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load pickle from {path}: {e}")
            raise
    
    @staticmethod
    def save_pickle(data: Any, path: Union[str, Path]) -> bool:
        """Save data as pickle"""
        path = Path(path)
        try:
            FileManager.ensure_directory(path.parent)
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Saved pickle to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save pickle to {path}: {e}")
            return False


class ConfigLoader:
    """Utility class for loading configuration files"""
    
    def __init__(self, config_dir: Union[str, Path] = "config"):
        self.config_dir = Path(config_dir)
        self.cache: Dict[str, Dict[str, Any]] = {}
        
    def load_settings(self, reload: bool = False) -> Dict[str, Any]:
        """Load main settings.yaml file"""
        if 'settings' not in self.cache or reload:
            settings_path = self.config_dir / "settings.yaml"
            self.cache['settings'] = DataLoader.load_yaml(settings_path)
        return self.cache['settings']
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Get nested setting using dot notation (e.g., 'api_rate_limits.sra_api.requests_per_minute')"""
        settings = self.load_settings()
        keys = key_path.split('.')
        
        value = settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_path = self.config_dir / ".env"
        env_vars = {}
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        return env_vars


class OutputManager:
    """Utility class for managing output files"""
    
    def __init__(self, output_dir: Union[str, Path] = "data/output"):
        self.output_dir = Path(output_dir)
        FileManager.ensure_directory(self.output_dir)
        
    def save_data(self, data: Union[pd.DataFrame, Dict, List], 
                  filename: str, format: str = "json") -> Path:
        """Save data in specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{timestamp}_{filename}"
        
        if format.lower() == "json":
            path = self.output_dir / f"{base_name}.json"
            if isinstance(data, pd.DataFrame):
                data = data.to_dict('records')
            DataLoader.save_json(data, path)
            
        elif format.lower() == "csv":
            path = self.output_dir / f"{base_name}.csv"
            if isinstance(data, pd.DataFrame):
                DataLoader.save_csv(data, path)
            else:
                df = pd.DataFrame(data)
                DataLoader.save_csv(df, path)
                
        elif format.lower() == "parquet":
            path = self.output_dir / f"{base_name}.parquet"
            if isinstance(data, pd.DataFrame):
                data.to_parquet(path)
            else:
                df = pd.DataFrame(data)
                df.to_parquet(path)
                
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Data saved to {path}")
        return path
    
    def create_report(self, report_name: str, content: str) -> Path:
        """Create a text report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{report_name}.txt"
        path = self.output_dir / filename
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Report created: {path}")
        return path