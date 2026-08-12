# Project Claude Instructions

## Git Commits

- **Commit after every unit task** (e.g. one function docstring, one API page).
- For tasks larger than a unit, use **multiple commits** — one per sub-unit.
- Commit message format: `[AI][Claude] <description>` — e.g. `[AI][Claude] Add NumPy docstring for watts_ratio_to_dB`.
- **Each git command must be its own individual Bash tool call** — never chain with `&&`, `;`, or newlines in a single call. This is required by the bash permission system.
  - Correct: Bash call 1 → `git add <file>`, Bash call 2 → `git commit -m "..."`
  - Wrong: `git add <file> && git commit -m "..."` in one Bash call

## Docstrings

- When rewriting a docstring, begin the summary line with `Docstring by Claude.` — e.g.:
  ```python
  """Docstring by Claude. Short one-line summary."""
  ```

## Documentation

- **Always run `mkdocs build` after editing any documentation files** to check for build errors before committing.
  ```bash
  cd optomechanics_documentation && /c/Users/seanh/miniconda3/envs/exp/python.exe -m mkdocs build 2>&1 | grep -E "ERROR|WARNING|INFO.*done"
  ```
- Fix all `ERROR` lines before committing. `WARNING` lines may be acceptable but should be reviewed.
- **Do not use `:::` mkdocstrings autodoc directives** for modules that have broken imports,
  missing dependencies (e.g. PyQt5, zhinst), or no `__init__.py`. Use manual documentation instead.

## TODO.md

- **Never delete or remove items** from `TODO.md`.
- When completing a task, tick its checkbox (`- [x]`) and append a one-line summary
  of what was done, including the relevant commit hash if applicable.
  Example:
  ```
  - [x] `attenuation_accounter.py` — added api_reference page (abc1234)
  ```
