from lxml import etree
from pathlib import Path
from typing import List, Union

def parse_failed_controls(xml_path: Union[Path, str]) -> List[str]:
    """
    Parses OpenSCAP ARF/XCCDF results to extract failed controls.
    Uses local-name() to be resilient to namespace changes between 
    different OpenSCAP versions or test fixtures.
    """
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    
    failed_controls = []

    for rule_result in root.xpath("//*[local-name()='rule-result']"): # type: ignore
        result_elems = rule_result.xpath("*[local-name()='result']")
        if result_elems and result_elems[0].text == "fail":
            idref = rule_result.get("idref")
            if idref:
                failed_controls.append(idref)
                
    return failed_controls
