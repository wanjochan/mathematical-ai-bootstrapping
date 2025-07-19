"""Data persistence utilities for saving and loading results"""

import os
import json
import glob
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple
import difflib


class DataPersistence:
    """Handles saving and loading data with timestamped files"""
    
    def __init__(self, base_dir: str = "var"):
        """Initialize DataPersistence
        
        Args:
            base_dir: Base directory for data files (relative to module)
        """
        self.var_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), base_dir)
        os.makedirs(self.var_dir, exist_ok=True)
        
    def save_json(self, data: Any, prefix: str = "data", 
                  timestamp_format: str = "%Y%m%d_%H%M%S") -> str:
        """Save data as JSON with timestamp
        
        Args:
            data: Data to save
            prefix: File prefix
            timestamp_format: Format for timestamp
            
        Returns:
            Full path to saved file
        """
        timestamp = datetime.now().strftime(timestamp_format)
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(self.var_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return filepath
        
    def save_text(self, content: str, prefix: str = "output",
                  timestamp_format: str = "%Y%m%d_%H%M%S") -> str:
        """Save text content with timestamp
        
        Args:
            content: Text content to save
            prefix: File prefix
            timestamp_format: Format for timestamp
            
        Returns:
            Full path to saved file
        """
        timestamp = datetime.now().strftime(timestamp_format)
        filename = f"{prefix}_{timestamp}.txt"
        filepath = os.path.join(self.var_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return filepath
        
    def load_json(self, filepath: str) -> Any:
        """Load JSON file
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def load_latest(self, prefix: str) -> Optional[Any]:
        """Load most recent file with prefix
        
        Args:
            prefix: File prefix to search for
            
        Returns:
            Loaded data from most recent file, None if no files found
        """
        pattern = os.path.join(self.var_dir, f"{prefix}_*.json")
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        
        return self.load_json(files[0])
        
    def list_files(self, prefix: str = "*", extension: str = "json") -> List[str]:
        """List files matching pattern
        
        Args:
            prefix: File prefix pattern
            extension: File extension
            
        Returns:
            List of file paths
        """
        pattern = os.path.join(self.var_dir, f"{prefix}*.{extension}")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)
        return files
        
    def get_file_info(self, prefix: str = "*", extension: str = "json") -> List[Dict[str, Any]]:
        """Get information about files
        
        Args:
            prefix: File prefix pattern
            extension: File extension
            
        Returns:
            List of file information dictionaries
        """
        files = self.list_files(prefix, extension)
        
        file_info = []
        for filepath in files:
            stat = os.stat(filepath)
            file_info.append({
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
            
        return file_info
        
    def compare_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """Compare two JSON files for differences
        
        Args:
            file1: Path to first file
            file2: Path to second file
            
        Returns:
            Dictionary with comparison results
        """
        data1 = self.load_json(file1)
        data2 = self.load_json(file2)
        
        # Convert to strings for comparison
        str1 = json.dumps(data1, indent=2, sort_keys=True, ensure_ascii=False)
        str2 = json.dumps(data2, indent=2, sort_keys=True, ensure_ascii=False)
        
        # Generate diff
        diff = list(difflib.unified_diff(
            str1.splitlines(keepends=True),
            str2.splitlines(keepends=True),
            fromfile=os.path.basename(file1),
            tofile=os.path.basename(file2)
        ))
        
        return {
            'identical': str1 == str2,
            'diff': ''.join(diff),
            'added_lines': sum(1 for line in diff if line.startswith('+')),
            'removed_lines': sum(1 for line in diff if line.startswith('-'))
        }
        
    def cleanup_old_files(self, prefix: str = "*", keep_count: int = 10):
        """Clean up old files, keeping only the most recent
        
        Args:
            prefix: File prefix pattern
            keep_count: Number of files to keep
        """
        files = self.list_files(prefix)
        
        if len(files) > keep_count:
            # Delete older files
            for filepath in files[keep_count:]:
                try:
                    os.remove(filepath)
                except Exception:
                    pass  # Ignore errors during cleanup
                    
    def save_with_metadata(self, data: Any, metadata: Dict[str, Any], 
                          prefix: str = "data") -> str:
        """Save data with additional metadata
        
        Args:
            data: Main data to save
            metadata: Additional metadata
            prefix: File prefix
            
        Returns:
            Full path to saved file
        """
        wrapped_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'prefix': prefix,
                **metadata
            },
            'data': data
        }
        
        return self.save_json(wrapped_data, prefix)
        
    def load_with_metadata(self, filepath: str) -> Tuple[Any, Dict[str, Any]]:
        """Load data and metadata from file
        
        Args:
            filepath: Path to file
            
        Returns:
            Tuple of (data, metadata)
        """
        wrapped_data = self.load_json(filepath)
        
        if isinstance(wrapped_data, dict) and 'metadata' in wrapped_data:
            return wrapped_data.get('data'), wrapped_data.get('metadata', {})
        else:
            # Legacy format without metadata
            return wrapped_data, {}