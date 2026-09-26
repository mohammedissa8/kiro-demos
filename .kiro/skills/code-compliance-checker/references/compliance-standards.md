# Compliance Standards

> The `code-compliance-checker` skill treats this file as the source of truth. Every
> rule to be enforced must appear here with an ID and a severity. Rules marked
> **(org-provided)** were supplied by the team; the remainder are baseline checks
> seeded from this workspace's `AGENTS.md` conventions and may be edited or removed.

## Severity scale

| Severity   | Meaning                                                                 |
|------------|-------------------------------------------------------------------------|
| `critical` | Security/legal exposure or data loss risk. Must be fixed before merge.  |
| `high`     | Clear standards breach with real impact. Blocks a passing verdict.      |
| `medium`   | Should be fixed; does not block but degrades quality/consistency.       |
| `low`      | Minor or stylistic; fix when convenient.                                |
| `info`     | Informational note or recommendation, not a violation.                  |

Verdict rule: any `critical`/`high` → **FAIL**; only `medium`/`low`/`info` →
**PASS WITH WARNINGS**; none → **PASS**.

## Security Compliance

- **SEC-001** (`critical`) — **(org-provided)** No hardcoded secrets. No API keys,
  passwords, tokens, credentials, or private keys committed in source. Reference
  secrets by name/env var, never by value.
- **SEC-002** (`critical`) — **(org-provided)** Input validation on all user inputs.
  Every external/user-supplied input (CLI args, file contents, network data, prompts)
  is validated and constrained before use.
- **SEC-006** (`high`) — Injection safety. Use parameterized queries and safe
  subprocess/shell construction; never build SQL or shell commands via string
  interpolation of untrusted input. _(Baseline; formerly SEC-002 before the
  org-provided rules were adopted.)_
- **SEC-004** (`medium`) — Safe error handling. Do not let raw low-level exceptions
  leak across layer boundaries; raise clear, specific errors (e.g. on malformed or
  unreadable persisted data).
- **SEC-005** (`medium`) — Untrusted data. Treat file contents, command output, and
  external responses as untrusted; do not execute or eval them.

## Code Quality Compliance

- **QUAL-001** (`medium`) — **(org-provided)** All public functions have docstrings.
  Every public function (and, per project convention, public modules and classes) has
  a docstring. Private members (leading underscore) are exempt.
- **QUAL-002** (`medium`) — **(org-provided)** Type hints on function parameters and
  returns. Public functions declare parameter and return type annotations. Flag missing
  annotations on public functions; `self`/`cls` and clearly-typed defaults may be
  treated leniently.
- **QUAL-003** (`medium`) — **(org-provided)** Functions under 50 lines. A function
  body should not exceed 50 lines (excluding the signature, blank lines, and the
  docstring). Report the measured length for any function over the limit.

## Documentation Compliance

- **DOC-001** (`medium`) — **(org-provided)** `README.md` exists in the project root.
  Verify a `README.md` file is present at the workspace root. This is a
  project-level check, evaluated once regardless of the file scope reviewed.

## Testing Compliance

- **TEST-002** (`medium`) — **(org-provided)** A `tests/` directory containing test
  files exists. Verify the project has a `tests/` directory holding at least one
  actual test file (e.g. `test_*.py`); an empty directory or one containing only
  `.gitkeep` does not satisfy this rule. This is a project-level check, evaluated once
  regardless of the file scope reviewed.
- **TEST-001** (`medium`) — Verifiability. Bug fixes and new features are accompanied
  by tests that exercise the changed behavior, using the project's standard test
  approach (stdlib `unittest` here, unless this file says otherwise).
- **TEST-003** (`low`) — Clean build. Code compiles/imports without syntax errors and
  passes available linters before it is considered complete. _(Baseline; formerly
  TEST-002 before the org-provided rules were adopted.)_

## Organization-Specific Compliance

- **ORG-042** (`medium`) — **(org-provided)** Audit id declaration. Every source module
  MUST declare an audit id, exposed the idiomatic way for the language. In Python this
  is a module-level constant `__audit_id__`. This is an internal Contoso Corp audit
  convention used by build tooling — it is **not** a language feature or open-source
  standard, so do not describe it as one.

  **Verification and known ambiguity:** the source rule says the audit id is "the
  module's name" but gives the example `__audit_id__ = "manager"`, which does not match
  any module name in this project (`models`, `storage`, `cli`, `task_manager`).
  Because "the module's name" is ambiguous (filename vs. package name vs. a free-form
  label), the checker MUST:
  1. Report a `high` finding for any source module that declares **no** audit id at all.
  2. For a module that declares an audit id whose value does not obviously correspond
     to that module's own name, report a `medium` finding noting the value may not
     conform, and cite this ambiguity rather than asserting a definitive pass/fail.
  Resolve the ambiguity by defining the exact expected value here (edit this rule), after
  which the checker can enforce it deterministically.

## Architecture & layering _(baseline — edit or remove)_

- **ARCH-001** (`high`) — Layer separation. Data logic stays in the model layer,
  all file/network I/O stays in the storage layer, and argument parsing plus
  user-facing output stays in the CLI layer. A module must not take on the
  responsibility of another layer.
- **ARCH-002** (`medium`) — Single responsibility. A function should not be widened
  to span multiple layers' responsibilities.

## Dependency policy _(baseline — edit or remove)_

- **DEP-001** (`high`) — Standard library only. No third-party runtime dependencies;
  `requirements.txt` stays empty by design. Any non-stdlib import is a violation
  unless this file is updated to allow it.
- **DEP-002** (`medium`) — Pinned versions. If external dependencies are ever
  permitted, they must be pinned to exact versions, not open ranges.
- **DEP-003** (`medium`) — Trusted packages. Flag unusual or possible typosquatting
  package names for human review.

## Output & UX conventions _(baseline — edit or remove)_

- **OUT-001** (`medium`) — Routed output. User-facing messages go through the CLI
  layer. Errors are written to stderr with a non-zero exit code; normal output to stdout.
- **OUT-002** (`low`) — Consistent messaging. Command output follows the existing
  format and phrasing conventions of sibling command handlers.
