"""
File readers and parsers for Revenue Intelligence Inbox

Handles CSV and JSON file imports with schema detection and normalization.
"""

import pandas as pd
import json
import hashlib
from typing import Dict, List, Any, Tuple
from pathlib import Path
import io


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def read_csv_file(file_obj) -> Tuple[pd.DataFrame, str]:
    """
    Read CSV file and return DataFrame with file hash.
    
    Args:
        file_obj: File-like object from upload
    
    Returns:
        Tuple of (DataFrame, file_hash)
    """
    # Read file content for hashing
    content = file_obj.read()
    file_hash = calculate_file_hash(content)
    
    # Reset file pointer and read as DataFrame
    file_obj.seek(0)
    df = pd.read_csv(file_obj)
    
    return df, file_hash


def read_json_file(file_obj) -> Tuple[pd.DataFrame, str]:
    """
    Read JSON file and return DataFrame with file hash.
    
    Supports both array of objects and nested structures.
    
    Args:
        file_obj: File-like object from upload
    
    Returns:
        Tuple of (DataFrame, file_hash)
    """
    # Read file content for hashing
    content = file_obj.read()
    file_hash = calculate_file_hash(content)
    
    # Parse JSON
    file_obj.seek(0)
    data = json.load(file_obj)
    
    # Convert to DataFrame
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Handle common wrapping patterns
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        elif 'records' in data:
            df = pd.DataFrame(data['records'])
        elif 'conversations' in data:
            df = pd.DataFrame(data['conversations'])
        else:
            # Treat as single record
            df = pd.DataFrame([data])
    else:
        raise ValueError("Unsupported JSON structure")
    
    return df, file_hash


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and data types from raw input.
    
    Maps common variations to standard field names:
    - source_id, conversation_id, id, call_id → source_id
    - date, timestamp, conversation_date → conversation_date
    - type, call_type, meeting_type → conversation_type
    - owner, sales_rep, rep_name, assigned_to → owner
    - account, company, company_name → account_name
    - contact, contact_name, attendee → contact_name
    """
    # Create a copy to avoid modifying original
    normalized = df.copy()
    
    # Column mapping rules (source_columns → target_column)
    column_mappings = {
        'source_id': ['source_id', 'conversation_id', 'id', 'call_id', 'meeting_id', 'record_id'],
        'conversation_date': ['date', 'timestamp', 'conversation_date', 'call_date', 'meeting_date', 'created_at'],
        'conversation_type': ['type', 'call_type', 'meeting_type', 'conversation_type', 'activity_type'],
        'owner': ['owner', 'sales_rep', 'rep_name', 'assigned_to', 'rep', 'sales_owner'],
        'account_name': ['account', 'company', 'company_name', 'account_name', 'organization'],
        'contact_name': ['contact', 'contact_name', 'attendee', 'participant', 'customer_name'],
        'duration_minutes': ['duration', 'duration_minutes', 'length', 'call_duration'],
        'topic': ['topic', 'subject', 'title', 'call_topic'],
        'transcript': ['transcript', 'recording_transcript', 'call_transcript', 'notes_transcript'],
        'notes': ['notes', 'summary', 'description', 'call_notes', 'meeting_notes'],
        'status': ['status', 'call_status', 'state', 'conversation_status']
    }
    
    # Apply mappings
    for target_col, source_cols in column_mappings.items():
        for source_col in source_cols:
            if source_col in normalized.columns and target_col not in normalized.columns:
                normalized[target_col] = normalized[source_col]
                break
    
    # Ensure source_id exists or create one
    if 'source_id' not in normalized.columns:
        # Generate source_id from available fields
        normalized['source_id'] = normalized.apply(
            lambda row: generate_stable_id(row), axis=1
        )
    
    # Convert source_id to string
    if 'source_id' in normalized.columns:
        normalized['source_id'] = normalized['source_id'].astype(str)
    
    # Standardize date format if present
    if 'conversation_date' in normalized.columns:
        try:
            normalized['conversation_date'] = pd.to_datetime(
                normalized['conversation_date'], errors='coerce'
            ).dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # Convert duration to integer if present
    if 'duration_minutes' in normalized.columns:
        try:
            normalized['duration_minutes'] = pd.to_numeric(
                normalized['duration_minutes'], errors='coerce'
            ).fillna(0).astype(int)
        except:
            pass
    
    return normalized


def generate_stable_id(row: pd.Series) -> str:
    """
    Generate a stable ID from row data when no source_id is available.
    
    Uses combination of date, owner, account, and contact to create unique identifier.
    """
    parts = []
    
    # Use available identifying fields
    for field in ['conversation_date', 'date', 'timestamp', 'owner', 'sales_rep', 
                  'account_name', 'account', 'contact_name', 'contact', 'topic', 'subject']:
        if field in row.index and pd.notna(row[field]):
            parts.append(str(row[field]))
    
    # If we have no parts, use the row's string representation hash
    if not parts:
        parts = [str(row.to_dict())]
    
    # Create hash-based ID
    combined = '|'.join(parts)
    return hashlib.md5(combined.encode()).hexdigest()


def detect_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze DataFrame and return schema information.
    
    Returns:
        Dict with schema details including available fields, data types, and sample values
    """
    schema = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': {},
        'has_source_id': 'source_id' in df.columns,
        'has_transcript': any(col in df.columns for col in ['transcript', 'notes', 'call_notes']),
        'has_date': 'conversation_date' in df.columns,
        'has_type': 'conversation_type' in df.columns,
        'has_owner': 'owner' in df.columns
    }
    
    # Analyze each column
    for col in df.columns:
        null_count = df[col].isna().sum()
        schema['columns'][col] = {
            'dtype': str(df[col].dtype),
            'null_count': int(null_count),
            'null_percentage': round(null_count / len(df) * 100, 2),
            'unique_values': int(df[col].nunique()),
            'sample_values': df[col].dropna().head(3).tolist()
        }
    
    return schema


def validate_required_fields(df: pd.DataFrame) -> List[str]:
    """
    Validate that DataFrame has minimum required fields after normalization.
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # After normalization, we should always have source_id
    if 'source_id' not in df.columns:
        errors.append("Missing unique identifier field (expected 'source_id' or similar)")
    
    # Check for at least some content
    content_fields = ['transcript', 'notes', 'topic', 'account_name', 'contact_name']
    has_content = any(field in df.columns for field in content_fields)
    
    if not has_content:
        errors.append("No content fields found (expected transcript, notes, topic, or contact info)")
    
    return errors


def create_data_dictionary(df: pd.DataFrame, schema: Dict[str, Any]) -> str:
    """
    Generate a human-readable data dictionary from the detected schema.
    
    Returns:
        Formatted string describing the data structure
    """
    lines = [
        "DATA DICTIONARY",
        "=" * 60,
        f"Total Records: {schema['total_rows']}",
        f"Total Fields: {schema['total_columns']}",
        "",
        "AVAILABLE FIELDS:",
        ""
    ]
    
    for col, info in schema['columns'].items():
        lines.append(f"• {col}")
        lines.append(f"  Type: {info['dtype']}")
        lines.append(f"  Completeness: {100 - info['null_percentage']:.1f}%")
        lines.append(f"  Unique Values: {info['unique_values']}")
        if info['sample_values']:
            samples = ", ".join(str(v)[:50] for v in info['sample_values'][:2])
            lines.append(f"  Sample: {samples}")
        lines.append("")
    
    lines.extend([
        "CAPABILITIES:",
        f"✓ Unique ID available: {'Yes' if schema['has_source_id'] else 'Generated'}",
        f"✓ Conversation content: {'Yes' if schema['has_transcript'] else 'Limited'}",
        f"✓ Date tracking: {'Yes' if schema['has_date'] else 'No'}",
        f"✓ Type classification: {'Yes' if schema['has_type'] else 'No'}",
        f"✓ Owner tracking: {'Yes' if schema['has_owner'] else 'No'}",
    ])
    
    return "\n".join(lines)
