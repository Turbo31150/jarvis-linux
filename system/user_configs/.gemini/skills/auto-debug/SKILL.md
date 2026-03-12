---
name: auto-debug
description: "Use when debugging an issue or error to iteratively reproduce the bug, investigate, fix it, and re-execute verification until successful."
---

# Auto-Debug Skill

This skill guides the agent on how to aggressively and iteratively debug an issue until it is verified fixed.

## Debugging Workflow

When asked to debug or fix a bug, follow this strict loop:

1. **Reproduce the Bug**: First, figure out how to reproduce the bug. Run the test, script, or compilation command that triggers the error.
2. **Analyze**: Read the error output and inspect the corresponding files using `grep_search` or `read_file`.
3. **Modify**: Apply a targeted fix using the `replace` or `write_file` tool.
4. **Re-execute & Verify**: Immediately re-run the exact command from step 1 to check if the error is resolved.
5. **Iterate**: If the error persists or a new error appears, go back to step 2. Do NOT stop until the reproduction command succeeds without errors.
6. **Report**: Once verified, provide a concise summary of the fix.
