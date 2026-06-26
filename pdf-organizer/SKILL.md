---
name: pdf-organizer
description: Organize PDF journal articles from ~/Downloads into ~/Documents/Work/Articles/ using heuristic classification. Renames files to firstauthor-year.pdf and applies Finder tags.
triggers:
  - /pdf-organizer
---

Run the PDF organizer script to classify and move journal articles from ~/Downloads.

The script `organize_papers.py` is bundled in this skill directory.

- Script: `~/.claude/skills/pdf-organizer/organize_papers.py`
- Requires Python 3 with `pypdf` (`pip install pypdf`); `ghostscript`/`xattr` are
  used optionally for text fallback and Finder tags.

## Usage

**Always dry-run first:**
```bash
python3 ~/.claude/skills/pdf-organizer/organize_papers.py \
  --dry-run --limit 20 --verbose
```

**Full dry-run (all files, review CSV before committing):**
```bash
python3 ~/.claude/skills/pdf-organizer/organize_papers.py \
  --dry-run
```

**Full run:**
```bash
python3 ~/.claude/skills/pdf-organizer/organize_papers.py
```

## What it does
- Classifies each PDF as article or not using heuristics (DOI, abstract, section headers, journal name patterns)
- Extracts first author last name and publication year
- Renames to `firstauthor-year.pdf` (conflicts get letter suffixes: `smith-2024a.pdf`, etc.)
- Moves articles to `~/Documents/Work/Articles/`
- Assigns up to 2 Finder tags from the configured vocabulary (IDP, LLPS, Simulation, Folding, etc.)
- Logs all actions to `~/Downloads/organize_papers.csv`

## Options
- `--dry-run` — preview only, no files moved
- `--limit N` — process only first N files
- `--verbose` — show detected signals per file
- `--min-confidence [high|medium|low]` — default: medium
- `--log FILE` — custom CSV log path

## After a run
- Files that errored (author not extracted) remain in ~/Downloads — check the CSV:
  ```bash
  grep ",error," ~/Downloads/organize_papers.csv
  ```
- No API key required — classification is fully heuristic
