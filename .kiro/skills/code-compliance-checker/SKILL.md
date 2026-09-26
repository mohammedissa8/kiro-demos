---
name: code-compliance-checker
description: Reviews code against organization compliance standards and generates reports. Use when asked to check code compliance, review code quality, or audit the codebase before deployment.
metadata:
  author: workshop-participant
  version: "1.0"
---

# Code Compliance Checker

## Overview
Reviews code against defined compliance standards and produces a report of passed and failed checks.

## How to Use

### Step 1: Run Compliance Check
Run the project's compliance checker (Python shown; use your generated checker for other stacks):

```bash
python3 .kiro/skills/code-compliance-checker/scripts/check_compliance.py .
```

### Step 2: Review Results
The script outputs an overall score, a pass/fail count, and each failed rule.

### Step 3: Address Failures
For each failure:
1. Consult references/compliance-rules.md for the rule details
2. Explain the fix the author should make (do not edit code yourself)
3. Re-run to verify

## Compliance Categories
See references/compliance-rules.md for the complete rules, including
organization-specific conventions such as ORG-042.