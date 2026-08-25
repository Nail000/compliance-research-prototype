import pytest
from pathlib import Path
from planner.parser import parse_failed_controls

def test_parse_failed_controls():
    fixture_path = Path("tests/fixtures/real_scan_small.xml")
    failed_controls = parse_failed_controls(fixture_path)
    
    assert len(failed_controls) == 2
    assert "xccdf_org.ssgproject.content_rule_partition_for_tmp" in failed_controls
    assert "xccdf_org.ssgproject.content_rule_no_empty_passwords" in failed_controls
