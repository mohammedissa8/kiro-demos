# Task Manager CLI — v1.0 Release Notes (Operator Edition)

Audience: engineers and operators who deploy and run this tool. Focus: rollout risk, blast radius, backout, and data impact.

## What This Release Is

Task Manager CLI v1.0 is a self-contained command-line tool that stores tasks in a local JSON file (`tasks.json`) in the current working directory. It runs on the Python standard library only — there are no external dependencies to install, pin, or patch.

Supported commands:
- `python main.py add "<title>" --priority <low|medium|high>`
- `python main.py list`
- `python main.py complete <id>`
- `python main.py delete <id>`

## Deployment / Rollout Considerations

- **Distribution unit:** the source tree plus a Python 3 runtime. There is no build step, package, or service to deploy. "Rolling out" means placing the code where operators/users can invoke `python main.py`.
- **Runtime prerequisite:** a working Python 3 interpreter on each host. Verify `python` resolves to Python 3 before rollout; the tool assumes it is invoked as `python main.py`.
- **No install/dependency phase:** because the tool is standard-library only, there is no `pip install`, no lockfile, and no dependency supply-chain surface to review for this release.
- **No shared/central state:** each invocation reads and writes `tasks.json` in the *current working directory*. There is no server, database, network endpoint, or shared datastore. Rollout is effectively per-host (and per-directory).
- **Working-directory sensitivity (operational gotcha):** because state lives in `tasks.json` relative to CWD, the same user running the tool from different directories will see different task lists. Document a canonical working directory for operators to avoid confusion.

## Risk Assessment

| Risk | What could go wrong | Blast radius | Severity |
|------|---------------------|--------------|----------|
| Wrong Python version | `python` points to Python 2 or is missing; tool fails to run | Single host | Medium — tool unusable on that host, no data impact |
| Working-directory drift | Tool run from unexpected CWD reads/writes a different `tasks.json` | Single user/host | Medium — user sees "missing" or unexpected tasks; underlying files are intact |
| `tasks.json` corruption / hand-editing | Malformed JSON from manual edits or interrupted write | The affected `tasks.json` only | Medium–High — that task list may fail to load until repaired |
| File permissions | User lacks write permission to CWD | Single host/user | Low–Medium — `add`/`complete`/`delete` fail; no corruption |
| Concurrent invocations | Two processes write the same `tasks.json` at once | One `tasks.json` file | Low–Medium — last-writer-wins could drop a concurrent change |

**Overall blast radius:** contained. There is no shared infrastructure, so any failure is isolated to a single host, user, or `tasks.json` file. No network-facing or multi-tenant exposure is described.

## Backout / Rollback Procedure

Because there is no packaged artifact or service, rollback is reverting the code and preserving data:

1. **Restore the previous code:** replace the deployed source tree with the prior version (e.g., `git checkout <previous-tag>` or redeploy the earlier copy).
2. **Preserve task data:** back up any existing `tasks.json` before swapping code — copy it aside (`cp tasks.json tasks.json.bak`). The data file is independent of the code version.
3. **Verify:** run `python main.py list` from the canonical working directory and confirm existing tasks appear as expected.

No database migration or teardown is required to back out.

## Data & Persistence Impact

- **On-disk state:** a single JSON file, `tasks.json`, created in the current directory on first use. This is the only persistent artifact.
- **File format:** JSON. Any migration, backup, or recovery is a plain file-level operation (copy, restore, inspect with standard JSON tooling).
- **Migrations:** none are described for this release. Operators should treat `tasks.json` as the authoritative state and back it up before code changes.
- **Recovery:** if `tasks.json` becomes unreadable, restore from a backup copy; the code itself holds no state.
- **Locality:** state is not centralized or replicated. Each directory/host maintains its own `tasks.json`.

## Operator Checklist

- [ ] Confirm `python` is Python 3 on each target host.
- [ ] Agree on and document a canonical working directory for `tasks.json`.
- [ ] Back up any existing `tasks.json` before deploying or rolling back.
- [ ] Smoke test: `add`, `list`, `complete`, `delete` a throwaway task in the target directory.

---
*This draft is scoped to the system as described in the project README (standard-library CLI, single local JSON file, no external services). It does not assume infrastructure not present in that documentation.*
