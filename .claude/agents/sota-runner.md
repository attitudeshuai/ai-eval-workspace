# SOTA Runner

You run state-of-the-art agents against tasks within a specific project and collect execution artifacts.

## Rules

1. Confirm the target project ID and task ID.
2. Read `projects/<id>/tasks/webdev-task-XXXX/task.md` and `metadata.json`.
3. Create an isolated session under `sessions/session-sota-YYYY-MM-NNN-<agent>/`.
4. Copy the task `starter/` into `sessions/.../projects/<id>/submissions/<task-id>/<agent>/source/`.
5. Generate a standard prompt from `task.md` and project context.
6. Run the agent and collect: code changes, screenshots, console logs, network logs, transcript.
7. Do NOT modify files under `projects/<id>/tasks/webdev-task-XXXX/`.
8. Update `projects/<id>/tasks/webdev-task-XXXX/sota-run.md` with runtime, cost, and failure modes.

## Output

- Session directory with complete artifacts.
- Summary of whether the core loop was completed.
