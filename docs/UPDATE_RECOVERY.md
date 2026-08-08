# SonicTrace update recovery

`SONICTRACE_UPDATE.cmd` now detects a dirty working tree and creates a Git stash containing tracked and untracked local files before pulling `origin/main`.

For older local clones that cannot pull because the new launcher files themselves are untracked, use `SONICTRACE_RESCUE_UPDATE.cmd` once. It copies itself to `%TEMP%`, stashes the dirty working tree, fetches `origin/main`, resets local `main` to the remote commit, then starts SonicTrace.

The rescue flow intentionally does **not** re-apply the old stash automatically. This prevents outdated local files from being layered back over the current SonicTrace code. The backup remains recoverable with `git stash list` / `git stash pop` if it is ever needed.
