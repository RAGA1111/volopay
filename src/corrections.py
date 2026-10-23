"""
Manual corrections and override management

Handles user corrections with full audit trail and conflict resolution.
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from src.database import get_connection, log_audit_entry


# Fields that can be manually overridden
EDITABLE_FIELDS = [
    'category',
    'priority',
    'review_status',
    'next_action',
    'status',
    'owner'
]


def apply_manual_override(conversation_id: int, field_name: str, 
                         new_value: str, reason: str) -> bool:
    """
    Apply a manual override to a conversation field.
    
    Args:
        conversation_id: ID of conversation to override
        field_name: Name of field to override
        new_value: New value to set
        reason: Reason for the override
    
    Returns:
        True if successful, False otherwise
    """
    if field_name not in EDITABLE_FIELDS:
        raise ValueError(f"Field '{field_name}' cannot be manually overridden. "
                        f"Allowed fields: {', '.join(EDITABLE_FIELDS)}")
    
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Get current value
        if field_name in ['category', 'priority', 'review_status', 'next_action']:
            # These are in analysis_results table
            cursor.execute("""
                SELECT {} FROM analysis_results WHERE conversation_id = ?
            """.format(field_name), (conversation_id,))
            result = cursor.fetchone()
            current_value = result[0] if result else None
            
            # Update the value
            cursor.execute("""
                UPDATE analysis_results 
                SET {} = ?, updated_at = ?
                WHERE conversation_id = ?
            """.format(field_name), (new_value, timestamp, conversation_id))
            
        else:
            # These are in conversations table
            cursor.execute("""
                SELECT {} FROM conversations WHERE id = ?
            """.format(field_name), (conversation_id,))
            result = cursor.fetchone()
            current_value = result[0] if result else None
            
            # Update the value
            cursor.execute("""
                UPDATE conversations 
                SET {} = ?, updated_at = ?
                WHERE id = ?
            """.format(field_name), (new_value, timestamp, conversation_id))
        
        # Deactivate any existing override for this field
        cursor.execute("""
            UPDATE manual_overrides 
            SET active = 0
            WHERE conversation_id = ? AND field_name = ?
        """, (conversation_id, field_name))
        
        # Record the new override
        cursor.execute("""
            INSERT INTO manual_overrides (
                conversation_id, field_name, override_value, 
                source_value_at_override, reason, timestamp, active
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (conversation_id, field_name, new_value, current_value, reason, timestamp))
        
        # Log audit entry
        log_audit_entry(
            'manual_override', conversation_id, 'override_applied',
            field_name=field_name,
            old_value=str(current_value),
            new_value=str(new_value),
            reason=reason
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_override_history(conversation_id: int) -> List[Dict]:
    """
    Get all override history for a conversation.
    
    Args:
        conversation_id: ID of conversation
    
    Returns:
        List of override records
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            field_name,
            override_value,
            source_value_at_override,
            reason,
            timestamp,
            active
        FROM manual_overrides
        WHERE conversation_id = ?
        ORDER BY timestamp DESC
    """, (conversation_id,))
    
    overrides = []
    for row in cursor.fetchall():
        overrides.append({
            'field_name': row[0],
            'override_value': row[1],
            'source_value': row[2],
            'reason': row[3],
            'timestamp': row[4],
            'active': bool(row[5])
        })
    
    conn.close()
    return overrides


def get_all_active_overrides() -> pd.DataFrame:
    """Get all active overrides across all conversations."""
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            mo.conversation_id,
            c.source_id,
            c.account_name,
            mo.field_name,
            mo.override_value,
            mo.source_value_at_override,
            mo.reason,
            mo.timestamp
        FROM manual_overrides mo
        JOIN conversations c ON mo.conversation_id = c.id
        WHERE mo.active = 1
        ORDER BY mo.timestamp DESC
    """, conn)
    
    conn.close()
    return df


def revert_override(conversation_id: int, field_name: str) -> bool:
    """
    Revert a manual override back to the source value.
    
    Args:
        conversation_id: ID of conversation
        field_name: Field to revert
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Get the active override
        cursor.execute("""
            SELECT override_value, source_value_at_override
            FROM manual_overrides
            WHERE conversation_id = ? AND field_name = ? AND active = 1
        """, (conversation_id, field_name))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        override_value, source_value = result
        
        # Revert to source value
        if field_name in ['category', 'priority', 'review_status', 'next_action']:
            cursor.execute("""
                UPDATE analysis_results 
                SET {} = ?, updated_at = ?
                WHERE conversation_id = ?
            """.format(field_name), (source_value, timestamp, conversation_id))
        else:
            cursor.execute("""
                UPDATE conversations 
                SET {} = ?, updated_at = ?
                WHERE id = ?
            """.format(field_name), (source_value, timestamp, conversation_id))
        
        # Deactivate the override
        cursor.execute("""
            UPDATE manual_overrides 
            SET active = 0
            WHERE conversation_id = ? AND field_name = ? AND active = 1
        """, (conversation_id, field_name))
        
        # Log audit entry
        log_audit_entry(
            'manual_override', conversation_id, 'override_reverted',
            field_name=field_name,
            old_value=str(override_value),
            new_value=str(source_value),
            reason='User reverted override'
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def check_override_conflicts(conversation_id: int) -> List[Dict]:
    """
    Check if any active overrides conflict with recent source updates.
    
    Args:
        conversation_id: ID of conversation to check
    
    Returns:
        List of potential conflicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get active overrides
    cursor.execute("""
        SELECT field_name, source_value_at_override, timestamp
        FROM manual_overrides
        WHERE conversation_id = ? AND active = 1
    """, (conversation_id,))
    
    overrides = cursor.fetchall()
    
    if not overrides:
        conn.close()
        return []
    
    # Check if conversation was updated since override
    cursor.execute("""
        SELECT source_updated_at
        FROM conversations
        WHERE id = ?
    """, (conversation_id,))
    
    result = cursor.fetchone()
    source_updated_at = result[0] if result and result[0] else None
    
    conflicts = []
    
    for field_name, source_value, override_timestamp in overrides:
        if source_updated_at and source_updated_at > override_timestamp:
            conflicts.append({
                'field_name': field_name,
                'override_timestamp': override_timestamp,
                'source_updated_at': source_updated_at,
                'message': f'Source data was updated after manual override on {field_name}'
            })
    
    conn.close()
    return conflicts


def get_correction_statistics() -> Dict:
    """Get statistics about manual corrections."""
    conn = get_connection()
    
    stats = {
        'total_overrides': 0,
        'active_overrides': 0,
        'by_field': {},
        'conversations_with_overrides': 0
    }
    
    # Total and active counts
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM manual_overrides")
    stats['total_overrides'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM manual_overrides WHERE active = 1")
    stats['active_overrides'] = cursor.fetchone()[0]
    
    # By field
    df = pd.read_sql_query("""
        SELECT field_name, COUNT(*) as count
        FROM manual_overrides
        WHERE active = 1
        GROUP BY field_name
    """, conn)
    stats['by_field'] = df.set_index('field_name')['count'].to_dict()
    
    # Unique conversations
    cursor.execute("""
        SELECT COUNT(DISTINCT conversation_id)
        FROM manual_overrides
        WHERE active = 1
    """)
    stats['conversations_with_overrides'] = cursor.fetchone()[0]
    
    conn.close()
    return stats
