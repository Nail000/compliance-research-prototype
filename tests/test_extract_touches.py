import pytest
from planner.extract_touches import extract_touches_from_playbook, _extract_from_task

def test_extract_touches_from_playbook():
    touches = extract_touches_from_playbook("tests/fixtures/playbook_snippet.yml")
    
    assert len(touches) == 4
    
    assert touches[0] == {"task_name": "Ensure aide is installed", "module": "ansible.builtin.package", "type": "package", "name": "aide"}
    assert touches[1] == {"task_name": "Enable systemd-journald Service - Enable Service systemd-journald", "module": "ansible.builtin.systemd", "type": "service", "name": "systemd-journald"}
    assert touches[2] == {"task_name": "Ensure use_pty is enabled in /etc/sudoers", "module": "ansible.builtin.lineinfile", "type": "file", "name": "/etc/sudoers"}
    assert touches[3] == {"task_name": "Ensure permission u-xs,g-xws,o-xwt on /etc/issue", "module": "ansible.builtin.file", "type": "file", "name": "/etc/issue"}

def test_extract_touches_from_mocked_tasks():
    touches = []
    
    _extract_from_task({
        "name": "Copy custom configuration",
        "ansible.builtin.copy": {"src": "custom.conf", "dest": "/etc/custom.conf"}
    }, touches)
    
    _extract_from_task({
        "name": "Enforce SSH Protocol 2",
        "ansible.builtin.replace": {"path": "/etc/ssh/sshd_config", "regexp": "^Protocol.*", "replace": "Protocol 2"}
    }, touches)
    
    _extract_from_task({
        "name": "Run unparseable setup script",
        "ansible.builtin.shell": "/usr/local/bin/setup.sh"
    }, touches)
    
    assert len(touches) == 3
    assert touches[0] == {"task_name": "Copy custom configuration", "module": "ansible.builtin.copy", "type": "file", "name": "/etc/custom.conf"}
    assert touches[1] == {"task_name": "Enforce SSH Protocol 2", "module": "ansible.builtin.replace", "type": "file", "name": "/etc/ssh/sshd_config"}
    assert touches[2] == {"task_name": "Run unparseable setup script", "touches": "unknown"}
