"""
Data reconciliation for Revenue Intelligence Inbox

Handles matching, deduplication, and conflict resolution for imports.
"""

import sqlite3
import pandas as pd
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.database import get_connection, log_audit_entry


class ReconciliationResult:
    """Container for reconciliation results."""
    
    def __init__(self):
        self.new = []
        self.unchanged = []
        self.updated = []
        self.duplicates = []
        self.conflicts = []
    
    def get_counts(self) -> Dict[str, int]:
        """Get counts by category."""
        return {
            'new': len(self.new),
            'unchanged': len(self.unchanged),
            'updated': len(self.updated),
            'duplicate': len(self.duplicates),
            'conflict': len(self.conflicts)
        }
    
    def total_processed(self) -> int:
        """Get total records processed."""
        return sum(self.get_counts().values())


def calculate_row_hash(row: pd.Series, content_fields: List[str]) -> str:
    """
    Calculate hash of row content fields for change detection.
    
    Args:
        row: DataFrame row
        content_fields: Fields to include in hash
    
    Returns:
        SHA256 hash string
    """
    values = []
    for field in content_fields:
        if field in row.index:
            val = row[field]
            if pd.notna(val):
                values.append(str(val))
            else:
                values.append('')
    
    combined = '|'.join(values)
    return hashlib.sha256(combined.encode()).hexdigest()


def reconcile_import(df: pd.DataFrame, batch_id: int) -> ReconciliationResult:
    """
    Reconcile imported data with existing database records.
    
    Identifies:
    - New records (source_id not in database)
    - Unchanged records (source_id exists, hash unchanged)
    - Updated records (source_id exists, hash changed)
    - Duplicates (within batch)
    - Conflicts (has active manual overrides that might be affected)
    
    Args:
        df: Validated and normalized DataFrame to import
        batch_id: Import batch ID for audit trail
    
    Returns:
        ReconciliationResult with categorized records
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    result = ReconciliationResult()
    
    # Content fields for hash calculation
    content_fields = ['conversation_date', 'conversation_type', 'owner', 'account_name',
                     'contact_name', 'duration_minutes', 'topic', 'transcript', 'notes', 'status']
    
    # Get existing conversations by source_id
    cursor.execute("SELECT source_id, source_hash, id FROM conversations")
    existing = {row[0]: {'hash': row[1], 'id': row[2]} for row in cursor.fetchall()}
    
    # Check for active overrides
    cursor.execute("""
        SELECT conversation_id, field_name
        FROM manual_overrides
        WHERE active = 1
    """)
    overrides = {}
    for row in cursor.fetchall():
        if row[0] not in overrides:
            overrides[row[0]] = []
        overrides[row[0]].append(row[1])
    
    # Process each record
    for idx, row in df.iterrows():
        source_id = str(row['source_id'])
        row_hash = calculate_row_hash(row, content_fields)
        
        if source_id in existing:
            existing_record = existing[source_id]
            existing_hash = existing_record['hash']
            conversation_id = existing_record['id']
            
            if row_hash == existing_hash:
                # No changes detected
                result.unchanged.append({
                    'source_id': source_id,
                    'conversation_id': conversation_id,
                    'row': row
                })
            else:
                # Changes detected
                if conversation_id in overrides:
                    # Has active overrides - potential conflict
                    result.conflicts.append({
                        'source_id': source_id,
                        'conversation_id': conversation_id,
                        'row': row,
                        'row_hash': row_hash,
                        'override_fields': overrides[conversation_id]
                    })
                else:
                    # Normal update
                    result.updated.append({
                        'source_id': source_id,
                        'conversation_id': conversation_id,
                        'row': row,
                        'row_hash': row_hash
                    })
        else:
            # New record
            result.new.append({
                'source_id': source_id,
                'row': row,
                'row_hash': row_hash
            })
    
    conn.close()
    return result


def commit_reconciliation(result: ReconciliationResult, batch_id: int, 
                         source_type: str = 'csv') -> Dict[str, int]:
    """
    Commit reconciled records to database.
    
    Args:
        result: ReconciliationResult from reconcile_import
        batch_id: Import batch ID for audit trail
        source_type: File type ('csv' or 'json')
    
    Returns:
        Dict with operation counts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {'inserted': 0, 'updated': 0, 'conflicts_flagged': 0, 'unchanged': 0}
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Insert new conversations
        for item in result.new:
            row = item['row']
            row_hash = item['row_hash']
            
            cursor.execute("""
                INSERT INTO conversations (
                    source_id, source_type, source_hash, source_payload,
                    conversation_date, conversation_type, owner, account_name,
                    contact_name, duration_minutes, topic, transcript, notes, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['source_id'], source_type, row_hash, json.dumps(row.to_dict()),
                row.get('conversation_date'), row.get('conversation_type'),
                row.get('owner'), row.get('account_name'), row.get('contact_name'),
                row.get('duration_minutes'), row.get('topic'),
                row.get('transcript'), row.get('notes'), row.get('status'),
                timestamp, timestamp
            ))
            
            conversation_id = cursor.lastrowid
            stats['inserted'] += 1
            
            log_audit_entry('conversation', conversation_id, 'created', 
                          batch_id=batch_id, reason='import')
        
        # Update changed conversations
        for item in result.updated:
            row = item['row']
            row_hash = item['row_hash']
            conversation_id = item['conversation_id']
            
            cursor.execute("""
                UPDATE conversations SET
                    source_hash = ?,
                    source_payload = ?,
                    conversation_date = ?,
                    conversation_type = ?,
                    owner = ?,
                    account_name = ?,
                    contact_name = ?,
                    duration_minutes = ?,
                    topic = ?,
                    transcript = ?,
                    notes = ?,
                    status = ?,
                    updated_at = ?,
                    source_updated_at = ?
                WHERE id = ?
            """, (
                row_hash, json.dumps(row.to_dict()),
                row.get('conversation_date'), row.get('conversation_type'),
                row.get('owner'), row.get('account_name'), row.get('contact_name'),
                row.get('duration_minutes'), row.get('topic'),
                row.get('transcript'), row.get('notes'), row.get('status'),
                timestamp, timestamp, conversation_id
            ))
            
            stats['updated'] += 1
            
            log_audit_entry('conversation', conversation_id, 'updated',
                          batch_id=batch_id, reason='import_changed')
        
        # Handle conflicts - update source but flag for review
        for item in result.conflicts:
            row = item['row']
            row_hash = item['row_hash']
            conversation_id = item['conversation_id']
            override_fields = item['override_fields']
            
            # Update the source data
            cursor.execute("""
                UPDATE conversations SET
                    source_hash = ?,
                    source_payload = ?,
                    conversation_date = ?,
                    conversation_type = ?,
                    owner = ?,
                    account_name = ?,
                    contact_name = ?,
                    duration_minutes = ?,
                    topic = ?,
                    transcript = ?,
                    notes = ?,
                    status = ?,
                    updated_at = ?,
                    source_updated_at = ?
                WHERE id = ?
            """, (
                row_hash, json.dumps(row.to_dict()),
                row.get('conversation_date'), row.get('conversation_type'),
                row.get('owner'), row.get('account_name'), row.get('contact_name'),
                row.get('duration_minutes'), row.get('topic'),
                row.get('transcript'), row.get('notes'), row.get('status'),
                timestamp, timestamp, conversation_id
            ))
            
            stats['conflicts_flagged'] += 1
            
            log_audit_entry('conversation', conversation_id, 'conflict_detected',
                          reason=f"Source changed but has active overrides on fields: {', '.join(override_fields)}",
                          batch_id=batch_id)
        
        stats['unchanged'] = len(result.unchanged)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    
    return stats


def get_conflict_details(conversation_id: int) -> Optional[Dict]:
    """
    Get detailed information about conflicts for a conversation.
    
    Args:
        conversation_id: Conversation ID to check
    
    Returns:
        Dict with conflict details or None if no conflicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check for recent conflict audit entries
    cursor.execute("""
        SELECT timestamp, reason
        FROM audit_log
        WHERE entity_id = ? AND action = 'conflict_detected'
        ORDER BY timestamp DESC
        LIMIT 1
    """, (conversation_id,))
    
    conflict_entry = cursor.fetchone()
    
    if not conflict_entry:
        conn.close()
        return None
    
    # Get active overrides
    cursor.execute("""
        SELECT field_name, override_value, reason, timestamp
        FROM manual_overrides
        WHERE conversation_id = ? AND active = 1
        ORDER BY timestamp DESC
    """, (conversation_id,))
    
    overrides = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'detected_at': conflict_entry[0],
        'reason': conflict_entry[1],
        'active_overrides': overrides
    }
