- Use Python's standard-library unittest only — no pytest, no third-party test libraries.
- Name files test_<module>.py, test classes Test<Thing>, and methods test_<behavior>.
- One behavior per test; make failure messages state the expected vs actual value.
- Tests must not touch the real tasks.json or the network. For anything that
  reads or writes task data, use a temporary file (tempfile) and clean it up.
- Cover the edge cases this domain cares about: empty task list, an unknown
  task id, and malformed/corrupt JSON in the store.
- Keep tests deterministic — no reliance on wall-clock time or task ordering
  beyond what the code guarantees.