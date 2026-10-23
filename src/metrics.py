"""
Metrics calculation for Revenue Intelligence Inbox

Provides dashboard metrics based on actual data.
"""

import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from src.database import get_connection


def calculate_overview_metrics(filters: Optional[Dict] = None) -> Dict:
    """
    Calculate all overview dashboard metrics.
    
    Args:
        filters: Optional filters to apply
    
    Returns:
        Dict with all metrics
    """
    conn = get_connection()
    
    # Build filter conditions
    where_conditions = ["1=1"]
    params = []
    
    if filters:
        if filters.get('owner'):
            where_conditions.append("c.owner = ?")
            params.append(filters['owner'])
        if filters.get('date_from'):
            where_conditions.append("c.conversation_date >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            where_conditions.append("c.conversation_date <= ?")
            params.append(filters['date_to'])
    
    where_clause = " AND ".join(where_conditions)
    
    metrics = {}
    
    # Unique conversations count
    query = f"SELECT COUNT(DISTINCT c.id) as count FROM conversations c WHERE {where_clause}"
    result = pd.read_sql_query(query, conn, params=params if params else None)
    metrics['unique_conversations'] = int(result.iloc[0]['count']) if not result.empty else 0
    
    # Activity by type (if type field exists)
    query = f"""
        SELECT conversation_type, COUNT(*) as count
        FROM conversations c
        WHERE {where_clause} AND conversation_type IS NOT NULL AND conversation_type != ''
        GROUP BY conversation_type
        ORDER BY count DESC
    """
    metrics['activity_by_type'] = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Priority distribution
    query = f"""
        SELECT a.priority, COUNT(*) as count
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        WHERE {where_clause} AND a.priority IS NOT NULL
        GROUP BY a.priority
        ORDER BY 
            CASE a.priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                WHEN 'needs_review' THEN 4
                ELSE 5
            END
    """
    metrics['priority_distribution'] = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Category distribution
    query = f"""
        SELECT a.category, COUNT(*) as count
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        WHERE {where_clause} AND a.category IS NOT NULL
        GROUP BY a.category
        ORDER BY count DESC
    """
    metrics['category_distribution'] = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Activity by owner
    query = f"""
        SELECT owner, COUNT(*) as count
        FROM conversations c
        WHERE {where_clause} AND owner IS NOT NULL AND owner != ''
        GROUP BY owner
        ORDER BY count DESC
        LIMIT 10
    """
    metrics['activity_by_owner'] = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Activity over time (by date)
    query = f"""
        SELECT 
            DATE(conversation_date) as date,
            COUNT(*) as count
        FROM conversations c
        WHERE {where_clause} AND conversation_date IS NOT NULL
        GROUP BY DATE(conversation_date)
        ORDER BY date DESC
        LIMIT 30
    """
    metrics['activity_over_time'] = pd.read_sql_query(query, conn, params=params if params else None)
    
    conn.close()
    return metrics


def calculate_import_health() -> Dict:
    """Calculate metrics about import quality and history."""
    conn = get_connection()
    
    health = {}
    
    # Recent imports summary
    df = pd.read_sql_query("""
        SELECT 
            id,
            filename,
            timestamp,
            status,
            total_rows,
            new_count,
            unchanged_count,
            updated_count,
            duplicate_count,
            invalid_count,
            conflict_count
        FROM import_batches
        ORDER BY timestamp DESC
        LIMIT 10
    """, conn)
    
    health['recent_imports'] = df
    
    # Overall stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM import_batches")
    health['total_batches'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_rows) FROM import_batches WHERE status = 'success'")
    result = cursor.fetchone()[0]
    health['total_rows_processed'] = result if result else 0
    
    cursor.execute("SELECT SUM(invalid_count) FROM import_batches")
    result = cursor.fetchone()[0]
    health['total_invalid_rows'] = result if result else 0
    
    # Last import
    cursor.execute("""
        SELECT filename, timestamp, status, total_rows
        FROM import_batches
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    last = cursor.fetchone()
    if last:
        health['last_import'] = {
            'filename': last[0],
            'timestamp': last[1],
            'status': last[2],
            'total_rows': last[3]
        }
    
    conn.close()
    return health


def get_priority_summary() -> Dict:
    """Get summary of conversations by priority with key stats."""
    conn = get_connection()
    
    summary = {}
    
    priorities = ['high', 'medium', 'low', 'needs_review']
    
    for priority in priorities:
        cursor = conn.cursor()
        
        # Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM analysis_results
            WHERE priority = ?
        """, (priority,))
        count = cursor.fetchone()[0]
        
        # Category breakdown
        df = pd.read_sql_query("""
            SELECT category, COUNT(*) as count
            FROM analysis_results
            WHERE priority = ?
            GROUP BY category
            ORDER BY count DESC
        """, conn, params=[priority])
        
        summary[priority] = {
            'count': count,
            'categories': df.to_dict('records') if not df.empty else []
        }
    
    conn.close()
    return summary


def get_category_summary() -> Dict:
    """Get summary of conversations by category."""
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            category,
            COUNT(*) as count,
            SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_priority,
            SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium_priority,
            SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low_priority
        FROM analysis_results
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """, conn)
    
    conn.close()
    
    return df.to_dict('records') if not df.empty else []


def get_owner_workload() -> pd.DataFrame:
    """Get workload distribution by owner."""
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            c.owner,
            COUNT(*) as total_conversations,
            SUM(CASE WHEN a.priority = 'high' THEN 1 ELSE 0 END) as high_priority,
            SUM(CASE WHEN a.priority = 'medium' THEN 1 ELSE 0 END) as medium_priority,
            SUM(CASE WHEN a.review_status = 'pending' THEN 1 ELSE 0 END) as pending_review
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        WHERE c.owner IS NOT NULL AND c.owner != ''
        GROUP BY c.owner
        ORDER BY high_priority DESC, total_conversations DESC
    """, conn)
    
    conn.close()
    return df


def format_metric(value: any, metric_type: str = 'count') -> str:
    """Format a metric value for display."""
    if value is None:
        return 'N/A'
    
    if metric_type == 'count':
        return f"{int(value):,}"
    elif metric_type == 'percentage':
        return f"{float(value):.1f}%"
    elif metric_type == 'currency':
        return f"${float(value):,.2f}"
    else:
        return str(value)
