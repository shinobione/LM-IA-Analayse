# Update recovery test cases

Manual Windows validation targets:

1. Clean clone: `SONICTRACE_UPDATE.cmd` should fast-forward normally without creating a stash.
2. Modified tracked files: updater should stash them, fast-forward, and leave the stash intact.
3. Untracked files colliding with files now tracked on `main`: updater should stash them before pull, avoiding the `would be overwritten by merge` failure.
4. Old clone where the updater itself collides: copy `SONICTRACE_RESCUE_UPDATE.cmd` into the repository and run it once. It self-copies to `%TEMP%` before stashing the working tree, then hard-syncs local `main` to `origin/main` and starts SonicTrace.
5. Failure before sync: updater must stop without applying or deleting the stash.

The old stash is not automatically re-applied because doing so could overwrite newer SonicTrace code with obsolete local versions.
