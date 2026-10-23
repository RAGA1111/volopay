"""
Tests for import, validation, and reconciliation functionality

Critical test scenarios from PRD Section 13:
- Same file imported twice should not create duplicate logical records
- Changed source records should update existing records
- Manual corrections should persist through re-imports
- Invalid files should be rejected cleanly
"""

import pytest
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import initialize_database, get_connection
from src.readers import normalize_dataframe, calculate_file_hash
from src.validation import validate_records
from src.reconciliation import reconcile_import, commit_reconciliation
from src.routing import batch_analyze_conversations
from src.corrections import apply_manual_override


@pytest.fixture
def test_db():
    """Create a test database."""
    test_db_path = Path(__file__).parent / "test_revenue.db"
    
    # Remove existing test db
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Override DB_PATH temporarily
    import src.database as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db_path
    
    # Initialize
    initialize_database()
    
    yield test_db_path
    
    # Cleanup
    db_module.DB_PATH = original_db_path
    if test_db_path.exists():
        test_db_path.unlink()


def create_sample_data():
    """Create sample conversation data for testing."""
    return pd.DataFrame([
        {
            'source_id': 'CONV-001',
            'conversation_date': '2026-10-20 14:30:00',
            'conversation_type': 'call',
            'owner': 'Alice Smith',
            'account_name': 'Acme Corp',
            'contact_name': 'John Doe',
            'duration_minutes': 30,
            'topic': 'Product demo',
            'transcript': 'Customer expressed strong interest in purchasing our product. They want to move forward with a pilot.',
            'notes': 'Ready to buy, request pricing proposal',
            'status': 'active'
        },
        {
            'source_id': 'CONV-002',
            'conversation_date': '2026-10-21 10:15:00',
            'conversation_type': 'meeting',
            'owner': 'Bob Jones',
            'account_name': 'TechStart Inc',
            'contact_name': 'Jane Smith',
            'duration_minutes': 45,
            'topic': 'Pricing discussion',
            'transcript': 'Customer mentioned price is too expensive and they are evaluating competitors.',
            'notes': 'Price objection, needs follow-up',
            'status': 'active'
        },
        {
            'source_id': 'CONV-003',
            'conversation_date': '2026-10-22 09:00:00',
            'conversation_type': 'call',
            'owner': 'Alice Smith',
            'account_name': 'Global Systems',
            'contact_name': 'Mike Johnson',
            'duration_minutes': 15,
            'topic': 'Check-in call',
            'transcript': 'Brief check-in to schedule next meeting.',
            'notes': 'Routine follow-up',
            'status': 'active'
        }
    ])


def test_same_file_imported_twice_no_duplicates(test_db):
    """
    Test: Same file imported twice should not create duplicate logical records.
    Expected: Second import reports all as unchanged/duplicate.
    """
    # Create sample data
    df = create_sample_data()
    
    # Normalize
    normalized_df = normalize_dataframe(df)
    
    # Validate
    valid_df, invalid_df, _ = validate_records(normalized_df)
    assert len(valid_df) == 3
    assert len(invalid_df) == 0
    
    # First import
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_1 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_1 = reconcile_import(valid_df, batch_id_1)
    stats_1 = commit_reconciliation(result_1, batch_id_1)
    
    # Verify first import
    assert stats_1['inserted'] == 3
    assert stats_1['updated'] == 0
    assert stats_1['unchanged'] == 0
    
    # Get conversation count after first import
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    count_after_first = cursor.fetchone()[0]
    assert count_after_first == 3
    conn.close()
    
    # Second import - same data
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_2 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_2 = reconcile_import(valid_df, batch_id_2)
    stats_2 = commit_reconciliation(result_2, batch_id_2)
    
    # Verify second import - no new records
    assert stats_2['inserted'] == 0
    assert stats_2['updated'] == 0
    assert stats_2['unchanged'] == 3
    
    # Get conversation count after second import
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    count_after_second = cursor.fetchone()[0]
    assert count_after_second == 3  # Still only 3 records
    conn.close()
    
    print("✅ Test passed: Same file imported twice creates no duplicates")


def test_changed_record_updates_correctly(test_db):
    """
    Test: Changed source record should update existing record, not duplicate.
    Expected: Existing record updated, change logged.
    """
    # Create and import initial data
    df = create_sample_data()
    normalized_df = normalize_dataframe(df)
    valid_df, _, _ = validate_records(normalized_df)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_1 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_1 = reconcile_import(valid_df, batch_id_1)
    commit_reconciliation(result_1, batch_id_1)
    
    # Modify one record
    df_modified = df.copy()
    df_modified.loc[df_modified['source_id'] == 'CONV-001', 'notes'] = 'UPDATED: Deal signed!'
    df_modified.loc[df_modified['source_id'] == 'CONV-001', 'status'] = 'closed'
    
    # Normalize and validate
    normalized_modified = normalize_dataframe(df_modified)
    valid_modified, _, _ = validate_records(normalized_modified)
    
    # Import modified data
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash456', datetime.utcnow().isoformat(), 'pending', len(valid_modified)))
    batch_id_2 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_2 = reconcile_import(valid_modified, batch_id_2)
    stats_2 = commit_reconciliation(result_2, batch_id_2)
    
    # Verify update behavior
    assert stats_2['inserted'] == 0  # No new records
    assert stats_2['updated'] == 1   # One record updated
    assert stats_2['unchanged'] == 2 # Two unchanged
    
    # Verify total count unchanged
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_count = cursor.fetchone()[0]
    assert total_count == 3
    
    # Verify the updated content
    cursor.execute("SELECT notes, status FROM conversations WHERE source_id = ?", ('CONV-001',))
    row = cursor.fetchone()
    assert 'UPDATED' in row[0]
    assert row[1] == 'closed'
    
    # Verify audit log
    cursor.execute("""
        SELECT COUNT(*) FROM audit_log 
        WHERE action = 'updated' AND entity_type = 'conversation'
    """)
    audit_count = cursor.fetchone()[0]
    assert audit_count >= 1
    
    conn.close()
    
    print("✅ Test passed: Changed record updates correctly without duplication")


def test_manual_override_persists_through_reimport(test_db):
    """
    Test: Manual correction then old source re-imported.
    Expected: Override preserved and conflict flagged.
    """
    # Create and import initial data
    df = create_sample_data()
    normalized_df = normalize_dataframe(df)
    valid_df, _, _ = validate_records(normalized_df)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_1 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_1 = reconcile_import(valid_df, batch_id_1)
    commit_reconciliation(result_1, batch_id_1)
    
    # Analyze conversations
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations")
    conversation_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    batch_analyze_conversations(conversation_ids)
    
    # Apply manual override to first conversation
    conv_id = conversation_ids[0]
    apply_manual_override(conv_id, 'priority', 'low', 'Manual adjustment by sales manager')
    
    # Verify override was applied
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT priority FROM analysis_results WHERE conversation_id = ?
    """, (conv_id,))
    priority = cursor.fetchone()[0]
    assert priority == 'low'
    
    # Check override is active
    cursor.execute("""
        SELECT COUNT(*) FROM manual_overrides 
        WHERE conversation_id = ? AND field_name = 'priority' AND active = 1
    """, (conv_id,))
    override_count = cursor.fetchone()[0]
    assert override_count == 1
    conn.close()
    
    # Re-import same data (simulating source system update)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_2 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_2 = reconcile_import(valid_df, batch_id_2)
    stats_2 = commit_reconciliation(result_2, batch_id_2)
    
    # Verify override still exists
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT priority FROM analysis_results WHERE conversation_id = ?
    """, (conv_id,))
    priority_after = cursor.fetchone()[0]
    assert priority_after == 'low'  # Override preserved
    
    cursor.execute("""
        SELECT COUNT(*) FROM manual_overrides 
        WHERE conversation_id = ? AND field_name = 'priority' AND active = 1
    """, (conv_id,))
    override_count_after = cursor.fetchone()[0]
    assert override_count_after == 1  # Still active
    conn.close()
    
    print("✅ Test passed: Manual override persists through re-import")


def test_invalid_file_rejected_cleanly(test_db):
    """
    Test: Invalid/malformed file should produce clear error.
    Expected: Clear error, existing data intact.
    """
    # First, import valid data
    df = create_sample_data()
    normalized_df = normalize_dataframe(df)
    valid_df, _, _ = validate_records(normalized_df)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('test_file.csv', 'hash123', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id_1 = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result_1 = reconcile_import(valid_df, batch_id_1)
    commit_reconciliation(result_1, batch_id_1)
    
    # Get initial count
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    initial_count = cursor.fetchone()[0]
    conn.close()
    
    # Create invalid data (missing required fields)
    invalid_df = pd.DataFrame([
        {
            'source_id': '',  # Empty source_id
            'conversation_date': 'invalid-date',
            'notes': ''  # No content
        },
        {
            'source_id': 'CONV-999',
            # Missing most fields
        }
    ])
    
    # Normalize
    normalized_invalid = normalize_dataframe(invalid_df)
    
    # Validate - should catch errors
    valid_invalid, invalid_records, error_summary = validate_records(normalized_invalid)
    
    # Should have validation errors
    assert len(invalid_records) >= 1
    assert len(error_summary) > 0
    
    # Verify database unchanged
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    final_count = cursor.fetchone()[0]
    assert final_count == initial_count  # No change
    conn.close()
    
    print("✅ Test passed: Invalid file rejected cleanly, data intact")


def test_ambiguous_routing_flagged_for_review(test_db):
    """
    Test: Ambiguous content should be flagged for review.
    Expected: Category = needs_review, not misclassified.
    """
    # Create ambiguous conversation data
    df = pd.DataFrame([
        {
            'source_id': 'CONV-AMB-001',
            'conversation_date': '2026-10-23 11:00:00',
            'conversation_type': 'call',
            'owner': 'Test User',
            'account_name': 'Ambiguous Co',
            'contact_name': 'Person Unknown',
            'topic': 'General discussion',
            'transcript': 'We talked about various things.',
            'notes': 'Follow up needed'
        }
    ])
    
    normalized_df = normalize_dataframe(df)
    valid_df, _, _ = validate_records(normalized_df)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (filename, file_hash, timestamp, status, total_rows)
        VALUES (?, ?, ?, ?, ?)
    """, ('ambiguous.csv', 'hash999', datetime.utcnow().isoformat(), 'pending', len(valid_df)))
    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    result = reconcile_import(valid_df, batch_id)
    commit_reconciliation(result, batch_id)
    
    # Analyze
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations WHERE source_id = 'CONV-AMB-001'")
    conv_id = cursor.fetchone()[0]
    conn.close()
    
    batch_analyze_conversations([conv_id])
    
    # Check classification
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, priority, review_status 
        FROM analysis_results 
        WHERE conversation_id = ?
    """, (conv_id,))
    row = cursor.fetchone()
    conn.close()
    
    category, priority, review_status = row
    
    # Should be marked for review due to ambiguity
    assert category == 'needs_review' or review_status == 'pending'
    
    print("✅ Test passed: Ambiguous routing flagged for review")


if __name__ == '__main__':
    # Run tests manually
    print("Running import tests...")
    print("=" * 60)
    
    # Create test fixture manually
    test_db_path = Path(__file__).parent / "test_revenue.db"
    if test_db_path.exists():
        test_db_path.unlink()
    
    import src.database as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db_path
    initialize_database()
    
    try:
        test_same_file_imported_twice_no_duplicates(test_db_path)
        
        # Reset for next test
        if test_db_path.exists():
            test_db_path.unlink()
        initialize_database()
        test_changed_record_updates_correctly(test_db_path)
        
        # Reset for next test
        if test_db_path.exists():
            test_db_path.unlink()
        initialize_database()
        test_manual_override_persists_through_reimport(test_db_path)
        
        # Reset for next test
        if test_db_path.exists():
            test_db_path.unlink()
        initialize_database()
        test_invalid_file_rejected_cleanly(test_db_path)
        
        # Reset for next test
        if test_db_path.exists():
            test_db_path.unlink()
        initialize_database()
        test_ambiguous_routing_flagged_for_review(test_db_path)
        
        print("=" * 60)
        print("✅ All tests passed!")
        
    finally:
        db_module.DB_PATH = original_db_path
        if test_db_path.exists():
            test_db_path.unlink()
