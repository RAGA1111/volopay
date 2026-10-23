"""
Conversation routing and classification

Implements transparent, evidence-based routing logic with explainable priorities.
"""

import re
from typing import Dict, Optional, Tuple, List
import pandas as pd
from datetime import datetime
from src.database import get_connection


RULE_VERSION = "1.0.0"


def analyze_conversation(row: pd.Series) -> Dict[str, str]:
    """
    Analyze a conversation and assign category, priority, rationale, and next action.
    
    Args:
        row: Conversation record with normalized fields
    
    Returns:
        Dict with category, priority, rationale, evidence, next_action, review_status
    """
    # Gather available content
    content = collect_content(row)
    
    # Classify the conversation
    category, evidence, rationale = classify_conversation(content, row)
    
    # Determine priority
    priority, priority_rationale = determine_priority(category, content, row)
    
    # Suggest next action
    next_action = suggest_next_action(category, priority, row)
    
    # Determine if human review is needed
    review_status = 'completed' if category != 'needs_review' else 'pending'
    
    # Combine rationale
    full_rationale = f"{rationale} {priority_rationale}".strip()
    
    return {
        'category': category,
        'priority': priority,
        'rationale': full_rationale,
        'evidence': evidence,
        'next_action': next_action,
        'review_status': review_status
    }


def collect_content(row: pd.Series) -> str:
    """Collect all available text content from a conversation."""
    parts = []
    
    for field in ['topic', 'transcript', 'notes']:
        if field in row.index and pd.notna(row[field]):
            parts.append(str(row[field]))
    
    return ' '.join(parts).lower()


def classify_conversation(content: str, row: pd.Series) -> Tuple[str, str, str]:
    """
    Classify conversation into a category based on content analysis.
    
    Returns:
        Tuple of (category, evidence, rationale)
    """
    # Insufficient content check
    if not content or len(content.strip()) < 10:
        return 'needs_review', 'Insufficient content', 'No meaningful content available for classification'
    
    # Buying signal patterns
    buying_patterns = [
        (r'\b(interested in|want to|ready to)\s+(buy|purchase|subscribe|sign up|get started)', 'expressed purchase intent'),
        (r'\b(demo|proposal|quote|pricing|contract|agreement)\b.*\brequest', 'requested commercial materials'),
        (r'\b(budget|approved|sign|close|move forward|next step)\b', 'mentioned commercial commitment'),
        (r'\bwhen can we (start|begin|go live|launch)\b', 'asked about implementation timeline'),
    ]
    
    for pattern, evidence_text in buying_patterns:
        if re.search(pattern, content):
            match = re.search(pattern, content)
            excerpt = content[max(0, match.start()-30):min(len(content), match.end()+30)]
            return 'buying_signal', f'"{excerpt.strip()}"', f'Detected {evidence_text}'
    
    # Objection/blocker patterns
    objection_patterns = [
        (r'\b(too expensive|too costly|price is high|can\'t afford)', 'pricing concern'),
        (r'\b(doesn\'t support|missing feature|need|required)\b.*\b(feature|capability|integration)', 'feature gap'),
        (r'\b(competitor|alternative|comparing|evaluation)\b', 'competitive evaluation'),
        (r'\b(concern|worried|hesitant|unsure|risk)\b', 'expressed concern'),
        (r'\b(procurement|legal|security review|compliance)\b.*\b(process|approval|clearance)\b', 'organizational blocker'),
    ]
    
    for pattern, evidence_text in objection_patterns:
        if re.search(pattern, content):
            match = re.search(pattern, content)
            excerpt = content[max(0, match.start()-30):min(len(content), match.end()+30)]
            return 'objection_blocker', f'"{excerpt.strip()}"', f'Identified {evidence_text}'
    
    # Customer risk patterns
    risk_patterns = [
        (r'\b(urgent|emergency|critical|broken|down|not working)\b', 'urgent issue'),
        (r'\b(escalate|escalation|manager|executive)\b', 'escalation requested'),
        (r'\b(cancel|churn|leaving|switch|unhappy|dissatisfied)\b', 'retention risk'),
        (r'\b(deadline|due date|must have by)\b', 'time-sensitive requirement'),
    ]
    
    for pattern, evidence_text in risk_patterns:
        if re.search(pattern, content):
            match = re.search(pattern, content)
            excerpt = content[max(0, match.start()-30):min(len(content), match.end()+30)]
            return 'customer_risk', f'"{excerpt.strip()}"', f'Detected {evidence_text}'
    
    # Product feedback patterns
    feedback_patterns = [
        (r'\b(feature request|would be great if|suggestion|recommend)\b', 'feature request'),
        (r'\b(usability|user experience|ux|confusing|difficult to)\b', 'usability feedback'),
        (r'\b(bug|issue|problem|error)\b(?!.*\b(urgent|critical)\b)', 'product issue reported'),
    ]
    
    for pattern, evidence_text in feedback_patterns:
        if re.search(pattern, content):
            match = re.search(pattern, content)
            excerpt = content[max(0, match.start()-30):min(len(content), match.end()+30)]
            return 'product_feedback', f'"{excerpt.strip()}"', f'Contains {evidence_text}'
    
    # Routine/informational patterns
    routine_patterns = [
        (r'\b(schedule|reschedule|calendar|meeting time)\b', 'scheduling discussion'),
        (r'\b(thank|thanks|appreciate|followup|follow up|checking in)\b', 'courtesy communication'),
        (r'\b(introduction|intro|getting to know)\b', 'introductory conversation'),
    ]
    
    for pattern, evidence_text in routine_patterns:
        if re.search(pattern, content):
            return 'routine', evidence_text, f'Appears to be {evidence_text}'
    
    # Default: needs review if no clear pattern
    return 'needs_review', 'No clear pattern detected', 'Content does not match defined classification patterns'


def determine_priority(category: str, content: str, row: pd.Series) -> Tuple[str, str]:
    """
    Determine priority level based on category and content analysis.
    
    Returns:
        Tuple of (priority, rationale)
    """
    # High priority categories
    if category == 'customer_risk':
        return 'high', 'Customer risk requires immediate attention.'
    
    if category == 'buying_signal':
        # Check for urgency indicators
        if any(word in content for word in ['urgent', 'asap', 'immediately', 'today', 'this week']):
            return 'high', 'Time-sensitive buying signal.'
        return 'medium', 'Active buying signal requires timely follow-up.'
    
    if category == 'objection_blocker':
        # Severe blockers get high priority
        if any(word in content for word in ['blocker', 'show-stopper', 'deal-breaker', 'cannot proceed']):
            return 'high', 'Critical blocker preventing progress.'
        return 'medium', 'Objection needs to be addressed.'
    
    # Medium priority categories
    if category == 'product_feedback':
        if 'multiple customers' in content or 'several clients' in content:
            return 'medium', 'Repeated feedback from multiple sources.'
        return 'low', 'Product feedback captured for review.'
    
    # Low priority
    if category == 'routine':
        return 'low', 'Routine conversation with standard follow-up.'
    
    # Needs review
    return 'needs_review', 'Insufficient information for automated priority assignment.'


def suggest_next_action(category: str, priority: str, row: pd.Series) -> str:
    """Suggest appropriate next action based on classification."""
    actions = {
        'buying_signal': 'Confirm next steps with sales owner and schedule follow-up.',
        'objection_blocker': 'Document blocker details and assign owner to address.',
        'customer_risk': 'Escalate to account manager for immediate review.',
        'product_feedback': 'Log feedback in product backlog and acknowledge receipt.',
        'routine': 'File for reference; follow standard workflow.',
        'needs_review': 'Route to human reviewer for manual classification.'
    }
    
    base_action = actions.get(category, 'Review and determine appropriate action.')
    
    # Add owner info if available
    if 'owner' in row.index and pd.notna(row['owner']):
        base_action = f"Assign to {row['owner']}: {base_action}"
    
    return base_action


def batch_analyze_conversations(conversation_ids: List[int]) -> int:
    """
    Analyze multiple conversations and store results.
    
    Args:
        conversation_ids: List of conversation IDs to analyze
    
    Returns:
        Number of conversations analyzed
    """
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    
    analyzed_count = 0
    
    for conv_id in conversation_ids:
        # Get conversation data
        cursor.execute("""
            SELECT * FROM conversations WHERE id = ?
        """, (conv_id,))
        
        row = cursor.fetchone()
        if not row:
            continue
        
        # Convert to Series for analysis
        row_dict = dict(row)
        row_series = pd.Series(row_dict)
        
        # Analyze
        analysis = analyze_conversation(row_series)
        
        # Check if analysis already exists
        cursor.execute("""
            SELECT id FROM analysis_results WHERE conversation_id = ?
        """, (conv_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing analysis
            cursor.execute("""
                UPDATE analysis_results SET
                    category = ?,
                    priority = ?,
                    rationale = ?,
                    evidence = ?,
                    next_action = ?,
                    review_status = ?,
                    rule_version = ?,
                    updated_at = ?
                WHERE conversation_id = ?
            """, (
                analysis['category'], analysis['priority'], analysis['rationale'],
                analysis['evidence'], analysis['next_action'], analysis['review_status'],
                RULE_VERSION, timestamp, conv_id
            ))
        else:
            # Insert new analysis
            cursor.execute("""
                INSERT INTO analysis_results (
                    conversation_id, category, priority, rationale, evidence,
                    next_action, review_status, rule_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conv_id, analysis['category'], analysis['priority'], analysis['rationale'],
                analysis['evidence'], analysis['next_action'], analysis['review_status'],
                RULE_VERSION, timestamp, timestamp
            ))
        
        analyzed_count += 1
    
    conn.commit()
    conn.close()
    
    return analyzed_count


def get_routing_statistics() -> Dict[str, any]:
    """Get statistics about routing and classification."""
    conn = get_connection()
    
    stats = {
        'total_analyzed': 0,
        'by_category': {},
        'by_priority': {},
        'needs_review_count': 0
    }
    
    # Category distribution
    category_df = pd.read_sql_query("""
        SELECT category, COUNT(*) as count
        FROM analysis_results
        WHERE category IS NOT NULL
        GROUP BY category
    """, conn)
    
    stats['by_category'] = category_df.set_index('category')['count'].to_dict()
    stats['total_analyzed'] = category_df['count'].sum()
    
    # Priority distribution
    priority_df = pd.read_sql_query("""
        SELECT priority, COUNT(*) as count
        FROM analysis_results
        WHERE priority IS NOT NULL
        GROUP BY priority
    """, conn)
    
    stats['by_priority'] = priority_df.set_index('priority')['count'].to_dict()
    
    # Needs review count
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM analysis_results
        WHERE review_status = 'pending' OR category = 'needs_review'
    """)
    stats['needs_review_count'] = cursor.fetchone()[0]
    
    conn.close()
    return stats
