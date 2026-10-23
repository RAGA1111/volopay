"""
Tests for export and manifest functionality

Verifies export generation, manifest accuracy, and verification.
"""

import pandas as pd
import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import initialize_database, get_connection
from src.readers import normalize_dataframe
from src.validation import validate_records
from src.reconciliation import reconcile_import, commit_reconciliation
from src.exports import generate_export, verify_export, EXPORT_DIR


def setup_test_data():
    """Set up test database with sample data."""
    test_db_path = Path(__file__).parent / "test_export.db"
    
    if test_db_path.exists():
        test_db_path.unlink()
    
    import src.database as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db_path
    
    # Also update EXPORT_DIR
    import src.exports as export_module
    original_export_dir = export_module.EXPORT_DIR
    test_export_dir = Path(__file__).parent / "test_exports"
    export_module.EXPORT_DIR = test_export_dir
    test_export_dir.mkdir(exist_ok=True)
    
    initialize_database()
    
    # Create sample data
    df = pd.DataFrame([
        {
            'source_id': 'EXP-001',
            'conversation_date': '2026-10-20 10:00:00',
            'conversation_type': 'call',
            'owner': 'Alice',
            'account_name': 'TestCo',
            'contact_name': 'Bob',
            'transcript': 'Test conversation',
            'notes': 'Test notes'
        }
    ])
    
    normalized_df = normalize_dataframe(df)
    valid_df, _, _ = validate_records(normalized_df)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test.csv', 'hash', '2026-10-23', 'pending', 1))
    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result = reconcile_import(valid_df, batch_id)
    commit_reconciliation(result, batch_id)
    
    return test_db_path, test_export_dir, original_db_path, original_export_dir


def cleanup_test_data(test_db_path, test_export_dir, original_db_path, original_export_dir):
    """Clean up test files."""
    import src.database as db_module
    import src.exports as export_module
    
    db_module.DB_PATH = original_db_path
    export_module.EXPORT_DIR = original_export_dir
    
    if test_db_path.exists():
        test_db_path.unlink()
    
    if test_export_dir.exists():
        for file in test_export_dir.glob('*'):
            file.unlink()
        test_export_dir.rmdir()


def test_export_generation_creates_files():
    """Test that export generates both data file and manifest."""
    test_db, test_export_dir, orig_db, orig_export = setup_test_data()
    
    try:
        result = generate_export(export_format='csv', filters=None, include_overrides=False)
        
        # Verify files were created
        assert result['main_file']
        assert result['manifest_file']
        assert Path(result['main_file']).exists()
        assert Path(result['manifest_file']).exists()
        
        # Verify row count
        assert result['row_count'] == 1
        
        print("✅ Export files created successfully")
        
    finally:
        cleanup_test_data(test_db, test_export_dir, orig_db, orig_export)


def test_manifest_contains_required_fields():
    """Test that manifest contains all required metadata."""
    test_db, test_export_dir, orig_db, orig_export = setup_test_data()
    
    try:
        result = generate_export(export_format='json', filters=None, include_overrides=True)
        
        # Read manifest
        with open(result['manifest_file'], 'r') as f:
            manifest = json.load(f)
        
        # Check required fields
        assert 'export_metadata' in manifest
        assert 'generated_at' in manifest['export_metadata']
        assert 'files' in manifest
        assert len(manifest['files']) > 0
        
        # Check file info
        file_info = manifest['files'][0]
        assert 'filename' in file_info
        assert 'row_count' in file_info
        assert 'sha256_checksum' in file_info
        
        # Check data summary
        assert 'data_summary' in manifest
        assert 'total_conversations_in_database' in manifest['data_summary']
        assert 'conversations_in_export' in manifest['data_summary']
        
        # Check schema
        assert 'schema_version' in manifest
        assert 'field_definitions' in manifest
        
        print("✅ Manifest contains all required fields")
        
    finally:
        cleanup_test_data(test_db, test_export_dir, orig_db, orig_export)


def test_export_verification_succeeds():
    """Test that export verification passes for valid export."""
    test_db, test_export_dir, orig_db, orig_export = setup_test_data()
    
    try:
        result = generate_export(export_format='csv', filters=None, include_overrides=False)
        
        # Verify export
        verification = verify_export(Path(result['manifest_file']))
        
        assert verification['valid'] == True
        assert len(verification['errors']) == 0
        
        print("✅ Export verification passed")
        
    finally:
        cleanup_test_data(test_db, test_export_dir, orig_db, orig_export)


def test_filtered_export_matches_count():
    """Test that filtered export row count matches manifest."""
    test_db, test_export_dir, orig_db, orig_export = setup_test_data()
    
    try:
        # Export with no filters
        result = generate_export(export_format='csv', filters=None, include_overrides=False)
        
        # Read the CSV
        df = pd.read_csv(result['main_file'])
        
        # Read manifest
        with open(result['manifest_file'], 'r') as f:
            manifest = json.load(f)
        
        # Verify counts match
        assert len(df) == manifest['files'][0]['row_count']
        assert len(df) == result['row_count']
        
        print("✅ Export row counts match manifest")
        
    finally:
        cleanup_test_data(test_db, test_export_dir, orig_db, orig_export)


if __name__ == '__main__':
    print("Running export tests...")
    print("=" * 60)
    
    test_export_generation_creates_files()
    test_manifest_contains_required_fields()
    test_export_verification_succeeds()
    test_filtered_export_matches_count()
    
    print("=" * 60)
    print("✅ All export tests passed!")
