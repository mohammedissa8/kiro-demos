# Task Manager CLI — Release Notes v1.0

Task Manager CLI is a small, fast command-line tool for tracking your tasks. This release lets you add tasks, see what's on your plate, mark work done, and clear out tasks you no longer need — all from the terminal. It uses only the Python standard library, so there is nothing extra to install, pin, or patch.

Your tasks are saved automatically to a local `tasks.json` file in the directory you run the tool from, so your list is always right where you left it.

---

## For CLI Users

### What's New

Everything you need to manage tasks from the command line is here: `add`, `list`, `complete`, and `delete`, with optional per-task priority. Tasks persist to `tasks.json` automatically — no configuration or setup required.

### Commands

You interact with the tool through `python main.py` followed by a command.

**Add a task** — create a new task, optionally setting its priority:

```
python main.py add "Write the quarterly report" --priority high
```

- `--priority` accepts a priority level: `low`, `medium`, or `high`.

**List your tasks** — show all of your current tasks:

```
python main.py list
```

**Complete a task** — mark a task as done by its number:

```
python main.py complete 1
```

**Delete a task** — remove a task by its number:

```
python main.py delete 1
```

### Installation & Upgrade

There is nothing extra to install. The tool uses only the Python standard library, so as long as you have Python 3 available, you can run it directly:

```
python main.py list
```

To upgrade, replace your existing copy of the tool with the new version. Your `tasks.json` file is not touched by the update, so your saved tasks carry over.

### Behavior to Know

- Your tasks are stored in a file named `tasks.json` in the current directory. If you run the tool from a different folder, it will look for (or create) a separate task list there.
- Because the task list is tied to the directory you run from, run the commands from the same folder each time to see the same list.

---

## For Operators

*Audience: engineers and operators who deploy and run this tool. Focus: rollout risk, blast radius, backout, and data impact.*

### What This Release Is

Task Manager CLI v1.0 is a self-contained command-line tool that stores tasks in a local JSON file (`tasks.json`) in the current working directory. It runs on the Python standard library only — there are no external dependencies to install, pin, or patch.

Supported commands:

- `python main.py add "<title>" --priority <low|medium|high>`
- `python main.py list`
- `python main.py complete <id>`
- `python main.py delete <id>`

### Deployment / Rollout Considerations

- **Distribution unit:** the source tree plus a Python 3 runtime. There is no build step, package, or service to deploy. "Rolling out" means placing the code where operators/users can invoke `python main.py`.
- **Runtime prerequisite:** a working Python 3 interpreter on each host. Verify `python` resolves to Python 3 before rollout; the tool assumes it is invoked as `python main.py`.
- **No install/dependency phase:** because the tool is standard-library only, there is no `pip install`, no lockfile, and no dependency supply-chain surface to review for this release.
- **No shared/central state:** each invocation reads and writes `tasks.json` in the *current working directory*. There is no server, database, network endpoint, or shared datastore. Rollout is effectively per-host (and per-directory).
- **Working-directory sensitivity (operational gotcha):** because state lives in `tasks.json` relative to the current working directory, the same user running the tool from different directories will see different task lists. Document a canonical working directory for operators to avoid confusion.

### Risk Assessment

| Risk | What could go wrong | Blast radius | Severity |
|------|---------------------|--------------|----------|
| Wrong Python version | `python` points to Python 2 or is missing; tool fails to run | Single host | Medium — tool unusable on that host, no data impact |
| Working-directory drift | Tool run from unexpected CWD reads/writes a different `tasks.json` | Single user/host | Medium — user sees "missing" or unexpected tasks; underlying files are intact |
| `tasks.json` corruption / hand-editing | Malformed JSON from manual edits or interrupted write | The affected `tasks.json` only | Medium–High — that task list may fail to load until repaired |
| File permissions | User lacks write permission to CWD | Single host/user | Low–Medium — `add`/`complete`/`delete` fail; no corruption |
| Concurrent invocations | Two processes write the same `tasks.json` at once | One `tasks.json` file | Low–Medium — last-writer-wins could drop a concurrent change |

**Overall blast radius:** contained. There is no shared infrastructure, so any failure is isolated to a single host, user, or `tasks.json` file. No network-facing or multi-tenant exposure is described.

### Backout / Rollback Procedure

Because there is no packaged artifact or service, rollback is reverting the code and preserving data:

1. **Restore the previous code:** replace the deployed source tree with the prior version (e.g., `git checkout <previous-tag>` or redeploy the earlier copy).
2. **Preserve task data:** back up any existing `tasks.json` before swapping code — copy it aside (`cp tasks.json tasks.json.bak`). The data file is independent of the code version.
3. **Verify:** run `python main.py list` from the canonical working directory and confirm existing tasks appear as expected.

No database migration or teardown is required to back out.

### Data & Persistence Impact

- **On-disk state:** a single JSON file, `tasks.json`, created in the current directory on first use. This is the only persistent artifact.
- **File format:** JSON. Any migration, backup, or recovery is a plain file-level operation (copy, restore, inspect with standard JSON tooling).
- **Migrations:** none are described for this release. Operators should treat `tasks.json` as the authoritative state and back it up before code changes.
- **Recovery:** if `tasks.json` becomes unreadable, restore from a backup copy; the code itself holds no state.
- **Locality:** state is not centralized or replicated. Each directory/host maintains its own `tasks.json`.

### Operator Checklist

- [ ] Confirm `python` is Python 3 on each target host.
- [ ] Agree on and document a canonical working directory for `tasks.json`.
- [ ] Back up any existing `tasks.json` before deploying or rolling back.
- [ ] Smoke test: `add`, `list`, `complete`, `delete` a throwaway task in the target directory.
