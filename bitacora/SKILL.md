---
name: bitacora
description: Prepend and query a lab-notebook log (LABNOTEBOOK.md) of work done in the current project. Run before /clear to record what was done this session.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash
---

# /bitacora — Lab Notebook Log

Maintain a `LABNOTEBOOK.md` in the current project directory: a chronological, searchable record of work sessions, decisions, and findings. Run before `/clear` to capture the session.

---

## Actions

Parse `$ARGUMENTS` to select the action:

| Invocation | Action |
|-----------|--------|
| *(empty)* or `log` | Draft a new entry from conversation context, show for review, then write on confirmation |
| `log "..."` | Pre-fill Summary with the quoted text; still show draft for review |
| `show [N]` | Print the last N entries (default 5) |
| `search <term>` | Find entries containing the term |
| `init` | Create LABNOTEBOOK.md if it doesn't exist |

---

## Entry Format

Each entry uses this structure (omit optional sections when empty):

```
## YYYY-MM-DD — <project or tag>

**Summary**: One or two sentences describing what was done this session.

**Details**:
- Step, finding, or result

**Decisions**:
- Rationale for non-obvious choices

**Files touched**:
- relative/path/to/file

**Figures**: *(optional)*
- ![caption](../analysis/notebooks/figure.png)

**Next**: *(optional)*
- What to pick up next session
```

Figures use relative paths to files already in `analysis/` — no copying or embedding.

Entries are **prepended** (newest first) so the most recent entry appears at the top of the file.

---

## Action: `log` (default)

1. **Infer a draft entry** from the current conversation:
   - Summary: what was accomplished this session
   - Details: concrete steps taken, commands run, outputs observed
   - Decisions: any non-obvious choices made and why
   - Files touched: files created or modified (use paths relative to cwd)
   - Figures: any plots or images mentioned or produced (suggest paths, do not auto-include all)
   - Next: any explicit next steps mentioned

2. **Show the draft** in a fenced markdown block.

3. **Ask the user**: *"Write this entry to LABNOTEBOOK.md? You can confirm, request edits (e.g. 'drop figures', 'remove file X', 'add ...'), or discard."*

4. **Apply any edits** and show the revised draft if changes were requested.

5. **On confirmation**: prepend the entry to `LABNOTEBOOK.md` by inserting it immediately after the header block (the `---` separator line). Create the file first if it doesn't exist using the `init` template. Report the date and line count written.

If `log "..."` was used, pre-populate the Summary field with the quoted text before inferring the rest.

---

## Action: `show [N]`

Read `LABNOTEBOOK.md` and extract the last N entries (entries start with `## YYYY-MM-DD`). Render them. Default N = 5.

If the file doesn't exist, say so and suggest `/bitacora init`.

---

## Action: `search <term>`

Read `LABNOTEBOOK.md` and return all entries whose text contains `<term>` (case-insensitive). Show matching entries in full. Report how many entries matched.

---

## Action: `init`

If `LABNOTEBOOK.md` does not exist in the current directory, create it with this header:

```markdown
# Lab Notebook

Lab notebook log for [project name]. Each entry records what was done in a session,
key decisions made, and files or figures produced.

Run `/bitacora` at the end of a session (before `/clear`) to add an entry.

---
```

If the file already exists, say so and skip creation.

---

## Notes

- **Use before `/clear`**: entries are inferred from the current conversation context; once cleared, that context is gone.
- **Git-trackable**: `LABNOTEBOOK.md` lives in the project root alongside `TODO.md` and `CHECKPOINT.md`. Add it to git tracking manually if desired.
- **Secondary inference**: if running at the start of a new session with no conversation context, suggest using `git log --since="<last entry date>"` to reconstruct what changed.
