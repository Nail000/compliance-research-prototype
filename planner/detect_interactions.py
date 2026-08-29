HIGH_RISK_FILE_PATTERNS = [
    '/etc/ssh/', 
    '/etc/sudoers', 
    '/boot/', 
    '/etc/crontab', 
    '/etc/cron', 
    '/etc/at.allow'
]

def find_candidate_interactions(controls: list) -> list:
    """
    Return a candidate matrix of interacting Rule IDs based on overlapped touched resources.
    
    Returns a list of tuples: (rule_id_1, rule_id_2, resource_name)
    """
    interactions = set()
    
    # Map resource names to the rule_ids that touch them
    resource_map = {}
    
    for control in controls:
        rule_id = control['rule_id']
        touches = control.get('touches', [])
        
        for touch in touches:
            res_name = touch.get('name')
            if res_name:
                if res_name not in resource_map:
                    resource_map[res_name] = []
                
                if rule_id not in resource_map[res_name]:
                    resource_map[res_name].append(rule_id)
                    
    # Find any resource touched by more than 1 rule
    for res_name, rule_ids in resource_map.items():
        if len(rule_ids) > 1:
            for i in range(len(rule_ids)):
                for j in range(i + 1, len(rule_ids)):
                    r1, r2 = sorted([rule_ids[i], rule_ids[j]])
                    interactions.add((r1, r2, res_name))
                    
    return list(interactions)

def assess_disruption_risk(control: dict) -> str:

    highest_risk = 'low'
    risk_levels = {'low': 1, 'medium': 2, 'high': 3}
    
    touches = control.get('touches', [])
    for touch in touches:
        res_type = touch.get('type')
        res_name = touch.get('name', '')
        
        current_risk = 'low'
        
        if res_type == 'service':
            current_risk = 'high'
        elif res_type == 'package':
            current_risk = 'medium'
        elif res_type == 'file':
            if any(pattern in res_name for pattern in HIGH_RISK_FILE_PATTERNS):
                current_risk = 'high'
            else:
                current_risk = 'low'
                
        if risk_levels[current_risk] > risk_levels[highest_risk]:
            highest_risk = current_risk
            
    return highest_risk
