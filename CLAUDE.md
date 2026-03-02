# Project Claude Instructions

## Git Commits

- **Commit after every unit task** (e.g. one function docstring, one API page).
- For tasks larger than a unit, use **multiple commits** — one per sub-unit.
- Commit message format: `[AI][Claude] <description>` — e.g. `[AI][Claude] Add NumPy docstring for watts_ratio_to_dB`.
- Always use **separate** `git add` and `git commit` Bash calls. Never chain with `&&`.

## Docstrings

- When rewriting a docstring, begin the summary line with `Made by Claude.` — e.g.:
  ```python
  """Made by Claude. Short one-line summary."""
  ```

## TODO.md

- **Never delete or remove items** from `TODO.md`.
- When completing a task, tick its checkbox (`- [x]`) and append a one-line summary
  of what was done, including the relevant commit hash if applicable.
  Example:
  ```
  - [x] `attenuation_accounter.py` — added api_reference page (abc1234)
  ```
