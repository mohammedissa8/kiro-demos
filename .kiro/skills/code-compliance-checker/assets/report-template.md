# Code Compliance Report

- **Date:** <YYYY-MM-DD>
- **Scope reviewed:** <files / directories / diff range actually reviewed>
- **Standards version:** <from references/compliance-standards.md, if versioned>
- **Overall verdict:** <PASS | PASS WITH WARNINGS | FAIL>

## Summary

| Severity  | Count |
|-----------|-------|
| critical  | <n>   |
| high      | <n>   |
| medium    | <n>   |
| low       | <n>   |
| info      | <n>   |

<One or two sentences summarizing the state of the reviewed code.>

## Findings

> Sorted by severity, critical first. Omit this note in the final report.

### <SEVERITY> — <RULE-ID>: <Rule title>

- **Location:** `<path>:<line(s)>`
- **Evidence:**
  ```
  <short snippet of the offending code>
  ```
- **Why it violates the standard:** <one or two sentences tied to the rule>
- **Remediation:** <concrete, minimal fix>

<Repeat the block above for each finding. If there are no findings, write "No violations found.">

## Not verified

<Rules that could not be checked in this review, and why (e.g. required running a tool
not available). Omit the section if everything applicable was verified.>

- **<RULE-ID>:** <reason not verified>

## Recommendations

<Optional improvements or suggested new standards. These are not violations. Omit if none.>

- <recommendation>
