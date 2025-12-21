import os
import csv
import json

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass

def validate_file_path(file_path: str, allowed_extensions: list = None) -> bool:
    """
    Validates if a file exists, is a file (not dir), and matches extension.
    
    Args:
        file_path (str): Path to the file.
        allowed_extensions (list): List of allowed extensions (e.g., ['.csv', '.json']).
    
    Raises:
        ValidationError: If any check fails.
    
    Returns:
        bool: True if valid.
    """
    if not os.path.exists(file_path):
        raise ValidationError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValidationError(f"Path is not a file: {file_path}")

    # Check permissions (read access)
    if not os.access(file_path, os.R_OK):
        raise ValidationError(f"File is not readable (permission denied): {file_path}")

    if allowed_extensions:
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in [e.lower() for e in allowed_extensions]:
            raise ValidationError(f"Invalid file extension '{ext}'. Allowed: {allowed_extensions}")

    return True

def validate_csv_format(file_path: str, required_columns: list = None) -> bool:
    """
    Validates if a file is a valid CSV and optionally checks headers.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Attempt to read a sample to detect format issues
            sample = f.read(1024)
            dialect = csv.Sniffer().sniff(sample)
            f.seek(0)
            
            reader = csv.reader(f, dialect)
            header = next(reader, None)
            
            if not header:
                raise ValidationError("CSV file is empty or missing header.")
            
            if required_columns:
                missing = [col for col in required_columns if col not in header]
                if missing:
                    raise ValidationError(f"Missing required columns: {missing}")
                    
    except csv.Error as e:
        raise ValidationError(f"CSV format error: {str(e)}")
    except UnicodeDecodeError:
        raise ValidationError("File encoding is not UTF-8.")
    except Exception as e:
        raise ValidationError(f"Unexpected validation error: {str(e)}")
        
    return True

def validate_json_format(file_path: str) -> bool:
    """Validates if a file contains valid JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Unexpected JSON validation error: {str(e)}")
    return True
