# AMIT CODING PREFERENCES v1.1.0
Session: 2026-01-04 - MCP Python Auditor & Chrono-Meteoroid Integration

## Learned:

❌ **Rejected Patterns:**
- **Fragile Regex:** `r'(\d+)%'` - Reason: Breaks with warnings or extra formatting in output.
- **Unsafe Context:** Running subprocesses without explicit environment (`PYTHONPATH`).
- **Strict Validation:** `score: int` - Reason: Breaks when tools return floats (e.g., 64.8), leading to 500 errors.
- **Implicit Recursion:** Using `dirs.remove()` in `os.walk` - Reason: Does not prevent descending into directories.

✅ **Approved Principles:**
- **Robust Parsing:** `r'TOTAL\s+.*?\s+(\d+)%'` - Pattern: Match the keyword `TOTAL` and capture the last percentage, ignoring intermediate noise.
- **Environment Isolation:** Always inject `env["PYTHONPATH"] = str(project_path)` for test runners.
- **Graceful Failure:** Accept `result.returncode in [0, 1, 2, 3]` for analysis tools (Vulture/Pytest) to capture partial data despite minor errors.
- **Schema Flexibility:** Use `float` for calculated metrics like `score` to maintain Pydantic validation stability.
- **Explicit Cleanup:** Use `dirs[:] = [d for d in dirs if d != pattern]` for in-place modification of `os.walk`.

## Production Enforcement:
- `pytest` + `coverage` must include `--color=no` on Windows for clean parsing.
- Always verify `pytest-cov` is installed in the target project environment.
- Documentation must sync with current audit findings baseline.
