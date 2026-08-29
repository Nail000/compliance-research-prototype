import pytest
from planner.detect_interactions import find_candidate_interactions, assess_disruption_risk

def test_find_candidate_interactions():
    controls = [
        {
            'rule_id': 'rule_A',
            'touches': [
                {'type': 'service', 'name': 'sshd'},
                {'type': 'file', 'name': '/etc/ssh/sshd_config'}
            ]
        },
        {
            'rule_id': 'rule_B',
            'touches': [
                {'type': 'file', 'name': '/etc/ssh/sshd_config'},
                {'type': 'package', 'name': 'openssh-server'}
            ]
        },
        {
            'rule_id': 'rule_C',
            'touches': [
                {'type': 'package', 'name': 'chrony'}
            ]
        },
        {
            'rule_id': 'rule_D',
            'touches': [
                {'type': 'service', 'name': 'sshd'}
            ]
        }
    ]
    
    interactions = find_candidate_interactions(controls)
    
    # Interactions should be:
    # rule_A and rule_B on /etc/ssh/sshd_config
    # rule_A and rule_D on sshd
    assert len(interactions) == 2
    
    # Check that both expected interactions are present
    assert ('rule_A', 'rule_B', '/etc/ssh/sshd_config') in interactions or ('rule_B', 'rule_A', '/etc/ssh/sshd_config') in interactions
    assert ('rule_A', 'rule_D', 'sshd') in interactions or ('rule_D', 'rule_A', 'sshd') in interactions


def test_assess_disruption_risk():
    # Test service (high)
    control_service = {
        'rule_id': 'rule_1',
        'touches': [{'type': 'service', 'name': 'sshd'}]
    }
    assert assess_disruption_risk(control_service) == 'high'
    
    # Test package (medium), overrides low file
    control_package = {
        'rule_id': 'rule_2',
        'touches': [
            {'type': 'package', 'name': 'chrony'}, 
            {'type': 'file', 'name': '/etc/chrony.conf'}
        ]
    }
    assert assess_disruption_risk(control_package) == 'medium'
    
    # Test high risk file overrides medium package
    control_file_high = {
        'rule_id': 'rule_3',
        'touches': [
            {'type': 'package', 'name': 'sudo'},
            {'type': 'file', 'name': '/etc/sudoers.d/custom'}
        ]
    }
    assert assess_disruption_risk(control_file_high) == 'high'
    
    # Test low risk file
    control_file_low = {
        'rule_id': 'rule_4',
        'touches': [{'type': 'file', 'name': '/etc/motd'}]
    }
    assert assess_disruption_risk(control_file_low) == 'low'
    
    # Test unknown touch
    control_unknown = {
        'rule_id': 'rule_5',
        'touches': [{'touches': 'unknown'}]
    }
    assert assess_disruption_risk(control_unknown) == 'low'
