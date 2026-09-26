#!/usr/bin/env python3
"""Code compliance checker script"""
import re
from pathlib import Path

__audit_id__ = "task-manager-cli"

def check_hardcoded_secrets(file_path):
    """Check for hardcoded secrets"""
    patterns = [r'api_key\s*=', r'password\s*=', r'token\s*=', r'secret\s*=']
    with open(file_path) as f:
        content = f.read()
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
    return True

def check_docstrings(file_path):
    """Check if functions have docstrings"""
    with open(file_path) as f:
        content = f.read()
        functions = re.findall(r'def \w+\([^)]*\):', content)
        docstrings = re.findall(r'def \w+\([^)]*\):\s*"""', content)
        return len(docstrings) >= len(functions) * 0.7

def check_audit_id(file_path):
    """ORG-042: module must declare a module-level __audit_id__ constant"""
    with open(file_path) as f:
        content = f.read()
        return re.search(r'^__audit_id__\s*=', content, re.MULTILINE) is not None

def scan_project(project_path):
    """Scan project and return compliance results"""
    results = {'passed': [], 'failed': [], 'score': 0}

    if (Path(project_path) / 'README.md').exists():
        results['passed'].append('DOC-001: README.md exists')
    else:
        results['failed'].append('DOC-001: README.md missing')

    for py_file in Path(project_path).rglob('*.py'):
        if 'test' in str(py_file):
            continue
        if check_hardcoded_secrets(py_file):
            results['passed'].append(f'SEC-001: No secrets in {py_file.name}')
        else:
            results['failed'].append(f'SEC-001: Potential secrets in {py_file.name}')
        if check_docstrings(py_file):
            results['passed'].append(f'QUAL-001: Good docstring coverage in {py_file.name}')
        else:
            results['failed'].append(f'QUAL-001: Missing docstrings in {py_file.name}')
        if check_audit_id(py_file):
            results['passed'].append(f'ORG-042: __audit_id__ present in {py_file.name}')
        else:
            results['failed'].append(f'ORG-042: __audit_id__ missing in {py_file.name}')

    total = len(results['passed']) + len(results['failed'])
    results['score'] = int((len(results['passed']) / total * 100)) if total > 0 else 0
    return results

if __name__ == '__main__':
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else '.'
    results = scan_project(project)
    print(f"Compliance Score: {results['score']}%")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")
    for item in results['failed']:
        print(f"  FAIL: {item}")