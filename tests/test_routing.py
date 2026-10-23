"""
Tests for routing and classification logic

Verifies that conversations are correctly categorized with explainable rationale.
"""

import pandas as pd
from src.routing import analyze_conversation, classify_conversation, determine_priority


def test_buying_signal_detection():
    """Test detection of buying signals."""
    # Create conversation with buying intent
    row = pd.Series({
        'source_id': 'TEST-001',
        'topic': 'Pricing discussion',
        'transcript': 'We are interested in purchasing your product and would like to request a proposal.',
        'notes': 'Ready to move forward'
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'buying_signal'
    assert analysis['priority'] in ['high', 'medium']
    assert 'request' in analysis['evidence'].lower() or 'proposal' in analysis['evidence'].lower()
    assert len(analysis['rationale']) > 0
    
    print("✅ Buying signal detected correctly")


def test_objection_blocker_detection():
    """Test detection of objections and blockers."""
    row = pd.Series({
        'source_id': 'TEST-002',
        'topic': 'Feature discussion',
        'transcript': 'The price is too expensive for our budget. We need to evaluate alternatives.',
        'notes': 'Price objection raised'
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'objection_blocker'
    assert 'expensive' in analysis['evidence'].lower() or 'price' in analysis['evidence'].lower()
    assert len(analysis['rationale']) > 0
    
    print("✅ Objection/blocker detected correctly")


def test_customer_risk_detection():
    """Test detection of customer risk situations."""
    row = pd.Series({
        'source_id': 'TEST-003',
        'topic': 'Urgent issue',
        'transcript': 'This is urgent and critical. Our system is not working and we need escalation immediately.',
        'notes': 'Escalate to management'
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'customer_risk'
    assert analysis['priority'] == 'high'
    assert 'urgent' in analysis['evidence'].lower() or 'critical' in analysis['evidence'].lower()
    
    print("✅ Customer risk detected correctly")


def test_product_feedback_detection():
    """Test detection of product feedback."""
    row = pd.Series({
        'source_id': 'TEST-004',
        'topic': 'Feature request',
        'transcript': 'It would be great if you could add a feature for bulk export.',
        'notes': 'Customer suggestion'
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'product_feedback'
    assert 'feature' in analysis['evidence'].lower() or 'great if' in analysis['evidence'].lower()
    
    print("✅ Product feedback detected correctly")


def test_routine_conversation_detection():
    """Test detection of routine conversations."""
    row = pd.Series({
        'source_id': 'TEST-005',
        'topic': 'Calendar update',
        'transcript': 'Thanks for the call. Let me reschedule our next meeting for next week.',
        'notes': 'Rescheduling'
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'routine'
    assert analysis['priority'] == 'low'
    
    print("✅ Routine conversation detected correctly")


def test_needs_review_for_ambiguous():
    """Test that ambiguous content is flagged for review."""
    row = pd.Series({
        'source_id': 'TEST-006',
        'topic': 'Call',
        'transcript': 'Some discussion.',
        'notes': ''
    })
    
    analysis = analyze_conversation(row)
    
    assert analysis['category'] == 'needs_review' or analysis['review_status'] == 'pending'
    
    print("✅ Ambiguous content flagged for review")


def test_evidence_always_provided():
    """Test that every classification includes evidence."""
    test_cases = [
        {
            'source_id': 'E-001',
            'transcript': 'We want to buy your product now.',
            'notes': 'Buying signal'
        },
        {
            'source_id': 'E-002',
            'transcript': 'The pricing is too high.',
            'notes': 'Price concern'
        },
        {
            'source_id': 'E-003',
            'transcript': 'Thanks for checking in.',
            'notes': 'Routine'
        }
    ]
    
    for case in test_cases:
        row = pd.Series(case)
        analysis = analyze_conversation(row)
        
        # Every analysis should have evidence and rationale
        assert analysis['evidence'] is not None
        assert len(analysis['evidence']) > 0
        assert analysis['rationale'] is not None
        assert len(analysis['rationale']) > 0
        
        # Should have a next action
        assert analysis['next_action'] is not None
        assert len(analysis['next_action']) > 0
    
    print("✅ All classifications include evidence and rationale")


def test_priority_escalation_for_urgency():
    """Test that urgent keywords elevate priority."""
    # Buying signal with urgency
    row_urgent = pd.Series({
        'source_id': 'URGENT-001',
        'transcript': 'We need this urgently and want to sign the contract asap.',
        'notes': 'Urgent purchase'
    })
    
    analysis_urgent = analyze_conversation(row_urgent)
    
    # Should be buying_signal with high priority
    assert analysis_urgent['category'] == 'buying_signal'
    assert analysis_urgent['priority'] == 'high'
    
    # Same buying signal without urgency
    row_normal = pd.Series({
        'source_id': 'NORMAL-001',
        'transcript': 'We are interested in purchasing your product.',
        'notes': 'Purchase interest'
    })
    
    analysis_normal = analyze_conversation(row_normal)
    
    # Should be buying_signal but medium priority
    assert analysis_normal['category'] == 'buying_signal'
    assert analysis_normal['priority'] == 'medium'
    
    print("✅ Priority correctly escalated for urgency")


if __name__ == '__main__':
    print("Running routing tests...")
    print("=" * 60)
    
    test_buying_signal_detection()
    test_objection_blocker_detection()
    test_customer_risk_detection()
    test_product_feedback_detection()
    test_routine_conversation_detection()
    test_needs_review_for_ambiguous()
    test_evidence_always_provided()
    test_priority_escalation_for_urgency()
    
    print("=" * 60)
    print("✅ All routing tests passed!")
