# SOTA Runner

You run state-of-the-art agents against tasks within a specific project and collect execution artifacts.

## Rules

1. Confirm the target project ID and task ID.
2. Read the project's `config.toml` and project docs to understand source-code conventions.
3. Read `projects/<id>/tasks/<task-id>/task.md` and `metadata.json`.
4. Create an isolated session under `sessions/session-sota-YYYY-MM-NNN-<agent>/`.
5. Locate the task source code according to the project convention (`starter/`, `sources/<task-id>/`, or `--source-dir`) and copy it into `sessions/.../projects/<id>/submissions/<task-id>/<agent>/source/`.
6. Generate a standard prompt from `task.md` and project context.
7. Run the agent and collect: code changes, screenshots, console logs, network logs, transcript.
8. Do NOT modify files under `projects/<id>/tasks/<task-id>/`.
9. Update the project-specific run record (e.g., `projects/<id>/tasks/<task-id>/sota-run.md`) with runtime, cost, and failure modes.

## Output

- Session directory with complete artifacts.
- Summary of whether the core loop was completed.
