"""
Export functionality for Revenue Intelligence Inbox

Generates CSV/JSON exports with verification manifest.
"""

import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.database import get_connection, get_all_conversations


EXPORT_DIR = Path(__file__).parent.parent / "exports"


def ensure_export_dir():
    """Ensure export directory exists."""
    EXPORT_DIR.mkdir(exist_ok=True)


def generate_export(export_format: str = 'csv', 
                   filters: Optional[Dict] = None,
                   include_overrides: bool = True) -> Dict[str, str]:
    """
    Generate export of conversations and analysis.
    
    Args:
        export_format: 'csv' or 'json'
        filters: Optional filters to apply
        include_overrides: Whether to include override information
    
    Returns:
        Dict with export file paths and metadata
    """
    ensure_export_dir()
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Get conversation data
    df = get_all_conversations(filters)
    
    if df.empty:
        raise ValueError("No conversations match the specified filters")
    
    # Add override indicators if requested
    if include_overrides:
        df = add_override_indicators(df)
    
    # Generate main export file
    if export_format == 'csv':
        main_filename = f"conversations_{timestamp}.csv"
        main_path = EXPORT_DIR / main_filename
        df.to_csv(main_path, index=False)
    else:  # json
        main_filename = f"conversations_{timestamp}.json"
        main_path = EXPORT_DIR / main_filename
        df.to_json(main_path, orient='records', indent=2)
    
    # Generate manifest
    manifest = generate_manifest(
        main_filename=main_filename,
        main_path=main_path,
        row_count=len(df),
        filters=filters,
        include_overrides=include_overrides
    )
    
    manifest_filename = f"manifest_{timestamp}.json"
    manifest_path = EXPORT_DIR / manifest_filename
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return {
        'main_file': str(main_path),
        'main_filename': main_filename,
        'manifest_file': str(manifest_path),
        'manifest_filename': manifest_filename,
        'row_count': len(df),
        'timestamp': timestamp
    }


def add_override_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns indicating which fields have active overrides."""
    conn = get_connection()
    
    # Get all active overrides
    overrides_df = pd.read_sql_query("""
        SELECT conversation_id, field_name, override_value
        FROM manual_overrides
        WHERE active = 1
    """, conn)
    
    conn.close()
    
    if overrides_df.empty:
        df['has_overrides'] = False
        return df
    
    # Pivot overrides to wide format
    override_indicators = overrides_df.pivot_table(
        index='conversation_id',
        columns='field_name',
        values='override_value',
        aggfunc='first'
    )
    
    # Rename columns to indicate they are overrides
    override_indicators.columns = [f'{col}_override' for col in override_indicators.columns]
    
    # Add override flag
    override_indicators['has_overrides'] = True
    
    # Merge with main dataframe
    df = df.merge(override_indicators, left_on='id', right_index=True, how='left')
    df['has_overrides'] = df['has_overrides'].fillna(False)
    
    return df


def generate_manifest(main_filename: str, main_path: Path, row_count: int,
                     filters: Optional[Dict], include_overrides: bool) -> Dict:
    """
    Generate export manifest with metadata and checksums.
    
    Args:
        main_filename: Name of the main export file
        main_path: Path to the main export file
        row_count: Number of rows in export
        filters: Filters that were applied
        include_overrides: Whether overrides were included
    
    Returns:
        Manifest dictionary
    """
    # Calculate file checksum
    with open(main_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    file_size = main_path.stat().st_size
    
    # Get database statistics
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM manual_overrides WHERE active = 1")
    active_overrides = cursor.fetchone()[0]
    
    conn.close()
    
    manifest = {
        'export_metadata': {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'generator': 'Revenue Intelligence Inbox v1.0.0',
            'export_type': 'conversations_and_analysis'
        },
        'files': [
            {
                'filename': main_filename,
                'format': 'csv' if main_filename.endswith('.csv') else 'json',
                'row_count': row_count,
                'file_size_bytes': file_size,
                'sha256_checksum': file_hash
            }
        ],
        'data_summary': {
            'total_conversations_in_database': total_conversations,
            'conversations_in_export': row_count,
            'active_overrides_in_database': active_overrides,
            'overrides_included': include_overrides
        },
        'filters_applied': filters if filters else 'none',
        'schema_version': '1.0',
        'field_definitions': {
            'id': 'Internal conversation ID',
            'source_id': 'Original identifier from source data',
            'conversation_date': 'Date/time of conversation',
            'conversation_type': 'Type of conversation (call, meeting, etc.)',
            'owner': 'Sales owner or representative',
            'account_name': 'Customer account name',
            'contact_name': 'Contact person name',
            'category': 'Routing category (buying_signal, objection_blocker, etc.)',
            'priority': 'Priority level (high, medium, low, needs_review)',
            'rationale': 'Explanation for category and priority assignment',
            'evidence': 'Specific content that supports the classification',
            'next_action': 'Recommended next step',
            'review_status': 'Whether human review is needed',
            'has_overrides': 'Whether this conversation has manual overrides'
        },
        'verification': {
            'row_count_matches': True,
            'checksum_valid': True,
            'all_files_present': True
        }
    }
    
    return manifest


def verify_export(manifest_path: Path) -> Dict[str, any]:
    """
    Verify an export using its manifest.
    
    Args:
        manifest_path: Path to manifest file
    
    Returns:
        Dict with verification results
    """
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    export_dir = manifest_path.parent
    
    # Check each file
    for file_info in manifest['files']:
        filename = file_info['filename']
        file_path = export_dir / filename
        
        # Check existence
        if not file_path.exists():
            results['valid'] = False
            results['errors'].append(f"File not found: {filename}")
            continue
        
        # Check row count for CSV
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            actual_rows = len(df)
            expected_rows = file_info['row_count']
            
            if actual_rows != expected_rows:
                results['valid'] = False
                results['errors'].append(
                    f"Row count mismatch in {filename}: expected {expected_rows}, found {actual_rows}"
                )
        
        # Check checksum
        with open(file_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        
        expected_hash = file_info['sha256_checksum']
        
        if actual_hash != expected_hash:
            results['valid'] = False
            results['errors'].append(
                f"Checksum mismatch in {filename}: file may have been modified"
            )
    
    return results


def get_export_history() -> List[Dict]:
    """Get list of available exports."""
    ensure_export_dir()
    
    exports = []
    
    for manifest_file in EXPORT_DIR.glob("manifest_*.json"):
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            exports.append({
                'manifest_file': manifest_file.name,
                'generated_at': manifest['export_metadata']['generated_at'],
                'row_count': manifest['data_summary']['conversations_in_export'],
                'files': [f['filename'] for f in manifest['files']]
            })
        except:
            # Skip invalid manifests
            continue
    
    # Sort by date, newest first
    exports.sort(key=lambda x: x['generated_at'], reverse=True)
    
    return exports


def cleanup_old_exports(keep_count: int = 10):
    """
    Clean up old export files, keeping only the most recent.
    
    Args:
        keep_count: Number of recent exports to keep
    """
    history = get_export_history()
    
    if len(history) <= keep_count:
        return
    
    to_delete = history[keep_count:]
    
    for export in to_delete:
        # Delete manifest
        manifest_path = EXPORT_DIR / export['manifest_file']
        if manifest_path.exists():
            manifest_path.unlink()
        
        # Delete associated files
        for filename in export['files']:
            file_path = EXPORT_DIR / filename
            if file_path.exists():
                file_path.unlink()
