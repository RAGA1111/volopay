"""
Data validation for Revenue Intelligence Inbox

Validates individual records and identifies issues before database import.
"""

import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime


def validate_records(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Validate all records and separate valid from invalid.
    
    Args:
        df: Normalized DataFrame to validate
    
    Returns:
        Tuple of (valid_df, invalid_df, error_summary)
    """
    validation_results = []
    
    for idx, row in df.iterrows():
        errors = validate_single_record(row, idx)
        validation_results.append({
            'index': idx,
            'errors': errors,
            'is_valid': len(errors) == 0
        })
    
    # Separate valid and invalid records
    valid_indices = [r['index'] for r in validation_results if r['is_valid']]
    invalid_indices = [r['index'] for r in validation_results if not r['is_valid']]
    
    valid_df = df.loc[valid_indices].copy() if valid_indices else pd.DataFrame()
    invalid_df = df.loc[invalid_indices].copy() if invalid_indices else pd.DataFrame()
    
    # Add error messages to invalid records
    if not invalid_df.empty:
        error_map = {r['index']: '; '.join(r['errors']) 
                    for r in validation_results if not r['is_valid']}
        invalid_df['validation_errors'] = invalid_df.index.map(error_map)
    
    # Create error summary
    error_summary = []
    if invalid_indices:
        error_summary.append(f"Found {len(invalid_indices)} invalid records")
        
        # Count error types
        error_types = {}
        for r in validation_results:
            if not r['is_valid']:
                for error in r['errors']:
                    error_types[error] = error_types.get(error, 0) + 1
        
        for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
            error_summary.append(f"  - {error}: {count} records")
    
    return valid_df, invalid_df, error_summary


def validate_single_record(row: pd.Series, index: int) -> List[str]:
    """
    Validate a single record and return list of errors.
    
    Args:
        row: Single row from DataFrame
        index: Row index for error reporting
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check for required source_id
    if 'source_id' not in row.index or pd.isna(row['source_id']) or str(row['source_id']).strip() == '':
        errors.append("Missing or empty source_id")
    
    # Validate date if present
    if 'conversation_date' in row.index and pd.notna(row['conversation_date']):
        if not is_valid_date(row['conversation_date']):
            errors.append("Invalid date format")
    
    # Check for at least some content
    content_fields = ['transcript', 'notes', 'topic', 'account_name', 'contact_name']
    has_any_content = any(
        field in row.index and pd.notna(row[field]) and str(row[field]).strip() != ''
        for field in content_fields
    )
    
    if not has_any_content:
        errors.append("No content in any content fields")
    
    # Validate duration if present
    if 'duration_minutes' in row.index and pd.notna(row['duration_minutes']):
        try:
            duration = int(row['duration_minutes'])
            if duration < 0:
                errors.append("Negative duration not allowed")
            elif duration > 1440:  # 24 hours
                errors.append("Duration exceeds reasonable limit (1440 minutes)")
        except (ValueError, TypeError):
            errors.append("Invalid duration value")
    
    return errors


def is_valid_date(date_value) -> bool:
    """Check if a value can be interpreted as a valid date."""
    if pd.isna(date_value):
        return False
    
    try:
        # Try parsing as ISO format
        if isinstance(date_value, str):
            datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return True
        # Check if it's already a datetime
        elif isinstance(date_value, (pd.Timestamp, datetime)):
            return True
        else:
            return False
    except:
        return False


def check_duplicates_in_batch(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify duplicate source_ids within a single batch.
    
    Args:
        df: DataFrame to check for duplicates
    
    Returns:
        Tuple of (deduplicated_df, warnings)
    """
    warnings = []
    
    if 'source_id' not in df.columns:
        return df, ["Cannot check duplicates: source_id missing"]
    
    # Find duplicates
    duplicates = df[df.duplicated(subset=['source_id'], keep='first')]
    
    if not duplicates.empty:
        warnings.append(f"Found {len(duplicates)} duplicate source_ids in batch (keeping first occurrence)")
        
        # List some duplicate IDs for reference
        dup_ids = duplicates['source_id'].head(5).tolist()
        warnings.append(f"  Example duplicate IDs: {', '.join(map(str, dup_ids))}")
    
    # Keep only first occurrence of each source_id
    deduplicated = df.drop_duplicates(subset=['source_id'], keep='first')
    
    return deduplicated, warnings


def preview_data_quality(df: pd.DataFrame) -> Dict[str, any]:
    """
    Generate data quality report for preview.
    
    Returns:
        Dict with quality metrics and warnings
    """
    report = {
        'total_records': len(df),
        'completeness': {},
        'warnings': []
    }
    
    # Check completeness of key fields
    key_fields = ['source_id', 'conversation_date', 'conversation_type', 'owner', 
                  'account_name', 'transcript', 'notes']
    
    for field in key_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            report['completeness'][field] = {
                'count': int(non_null),
                'percentage': round(non_null / len(df) * 100, 2)
            }
            
            # Add warning if completeness is low
            if non_null / len(df) < 0.5:
                report['warnings'].append(
                    f"Low completeness for '{field}': only {non_null}/{len(df)} records"
                )
    
    # Check for missing critical fields
    if 'transcript' not in df.columns and 'notes' not in df.columns:
        report['warnings'].append("No conversation content fields (transcript/notes) available")
    
    # Check date range if available
    if 'conversation_date' in df.columns:
        valid_dates = pd.to_datetime(df['conversation_date'], errors='coerce').dropna()
        if not valid_dates.empty:
            report['date_range'] = {
                'earliest': valid_dates.min().strftime('%Y-%m-%d'),
                'latest': valid_dates.max().strftime('%Y-%m-%d'),
                'span_days': (valid_dates.max() - valid_dates.min()).days
            }
    
    return report
