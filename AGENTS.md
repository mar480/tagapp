## Context management

Treat context as a limited working set. Optimise for retaining information that affects the current task, not for retaining everything you encounter.

### Read selectively
- Inspect only the files, code, documentation and command output needed for the current task.
- Do not read the whole repository, large directories, generated files, logs, lockfiles or large data files unless the task specifically requires them.
- Before opening a large file, search for the relevant symbol, section or text and inspect the smallest useful range.
- Do not repeatedly reread unchanged files. Reuse what you have already established unless there is reason to believe it has changed.
- Follow references to additional files only when they are relevant to the current decision or implementation.

### Keep context compact
- Prefer concise summaries of discoveries over retaining large raw outputs.
- When command output is large, extract the relevant errors, warnings, results or lines rather than carrying the entire output forward.
- Do not reproduce large source files in your responses or working notes.
- Avoid verbose narration of routine actions.
- Do not restate requirements that are already clear.

### Maintain working state
For substantial multi-step work, maintain a concise mental/workspace state containing:
- current objective;
- relevant files and components;
- important constraints;
- decisions already made and why;
- changes completed;
- tests/checks completed;
- unresolved issues;
- next action.

Update this state when something material changes. Discard exploratory details that no longer affect the task.

If durable project state needs to survive across sessions, prefer updating an appropriate small project document rather than relying on conversation history. Do not create such a document unless it would genuinely help future work.

### Work incrementally
- Investigate first, then edit.
- Prefer focused changes over broad rewrites.
- After an edit, inspect/test the affected area rather than rereading the entire repository.
- Batch related searches, inspections and tests where practical.
- Avoid repeating commands whose result is already known unless the underlying state has changed.

### Protect important context
Never discard or summarise away:
- explicit user requirements;
- architectural constraints relevant to the task;
- public interfaces or schemas being changed;
- decisions that constrain later work;
- known failing tests or unresolved errors;
- exact identifiers, paths, commands or values needed to continue safely.

When context becomes crowded, prioritise in this order:
1. current task and acceptance criteria;
2. relevant code and interfaces;
3. decisions and constraints;
4. current implementation/test state;
5. supporting investigation;
6. obsolete exploration and verbose tool output.

### Autonomy
Use judgement. These rules are intended to reduce unnecessary context use, not to prevent you from inspecting additional material when doing so is necessary for correctness.

Do not sacrifice correctness, testing, or understanding merely to save tokens.