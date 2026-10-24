---
name: tutorial-pipeline
description: >-
  Run, validate, stage, and preview the local Markdown-to-HTML static site pipeline
  for the Eurorack Buffered Multiple course in ./tutorial/ (tutorial/build.py).
  Use this skill whenever the user asks to convert tutorial Markdown files to HTML,
  run or debug the tutorial build pipeline, check quiz option word counts or frontmatter,
  stage the _site/ GitHub Pages bundle locally, or serve the tutorial locally for previewing.
---

# Tutorial Markdown-to-HTML Development Pipeline (`tutorial-pipeline`)

This skill manages the local Markdown-to-HTML static site build, validation, staging, and local preview workflow for the interactive course in [`tutorial/`](../../../tutorial).

## Pipeline Overview

- **Source of Truth (Tracked in Git)**:
  - [`tutorial/index.md`](../../../tutorial/index.md) — Course landing page (`type: index`)
  - [`tutorial/lessons/*.md`](../../../tutorial/lessons) — Lesson modules `0000`–`0007` (`type: lesson`)
  - [`tutorial/reference/*.md`](../../../tutorial/reference) — Reference sheets and [`GLOSSARY.md`](../../../tutorial/reference/GLOSSARY.md) (`type: reference`)
  - [`tutorial/assets/`](../../../tutorial/assets) — Shared stylesheet (`style.css`) and interactive client runtime (`course.js`)
- **Compiler & Validator**:
  - [`tutorial/build.py`](../../../tutorial/build.py) — Python 3.14 static site generator (`markdown-it-py` + `pyyaml`).
- **Generated Outputs (Gitignored)**:
  - `tutorial/index.html`, `tutorial/lessons/*.html`, `tutorial/reference/*.html` (built in-place for local browsing)
  - `_site/` (clean GitHub Pages artifact directory when `--out-dir _site` is passed)

---

## Quick Runbook

You can run the helper script [dev_pipeline.sh](./scripts/dev_pipeline.sh) or invoke `tutorial/build.py` directly using the workspace `.venv`.

### 1. Build In-Place & Validate (`build`)

Compile all Markdown sources into `tutorial/*.html`, `tutorial/lessons/*.html`, and `tutorial/reference/*.html` while enforcing all frontmatter, link, and quiz checks:

```bash
.agents/skills/tutorial-pipeline/scripts/dev_pipeline.sh build
```

Or directly via `.venv`:

```bash
.venv/bin/python tutorial/build.py --check
```

### 2. Stage Clean GitHub Pages Bundle (`stage`)

Replicate the exact GitHub Actions deployment step from [`.github/workflows/pages.yml`](../../../.github/workflows/pages.yml) into `_site/` (excluding `tutorial/apps/` and internal `.md` files):

```bash
.agents/skills/tutorial-pipeline/scripts/dev_pipeline.sh stage
```

### 3. Build & Serve for Local Browser Preview (`serve`)

Build all HTML files in-place with validation and launch a local HTTP server (default port `8000`):

```bash
.agents/skills/tutorial-pipeline/scripts/dev_pipeline.sh serve 8000
```

Then open `http://127.0.0.1:8000/index.html`.

### 4. Clean Generated HTML Files (`clean`)

Remove all generated `.html` files in `tutorial/` and the `_site/` staging directory:

```bash
.agents/skills/tutorial-pipeline/scripts/dev_pipeline.sh clean
```

---

## Validation Checks Enforced by `--check`

When `.venv/bin/python tutorial/build.py --check` runs, it verifies:

1. **YAML Frontmatter Completeness**:
   - Every lesson (`tutorial/lessons/*.md`) must define `type: lesson`, `id`, `title`, `kicker`, `lead`, `badge`, `summary`, `app_dir`, and `meta`.
   - Every reference sheet (`tutorial/reference/*.md`) must define `type: reference`, `id`, `title`, `nav_label`, `kicker`, `lead`, `card_title`, and `card_desc`.
2. **Equal-Word-Count Quiz Rule**:
   - Every `:::quiz` question must have at least 2 options, exactly 1 correct option (`- [x]`), and **every option within the same question must have the exact same word count** so option length never leaks the answer.
   - If `--check` reports a word-count mismatch, adjust the phrasing of the flagged option in the `.md` source file and re-run `build`.
3. **Internal Link Resolution**:
   - Relative links between `.md` files (e.g., `[Lesson 0005](0005-kicad-pcb-layout-and-assembly.md)` or `[Glossary](../reference/GLOSSARY.md)`) are automatically rewritten to `.html` (`glossary.html` for `GLOSSARY.md`) and checked against the set of generated HTML pages and static assets.

---

## Authoring & Directive Reference

When editing or creating Markdown files in `tutorial/`, consult [DIRECTIVES.md](./references/DIRECTIVES.md) for the exact syntax of:
- YAML frontmatter schemas (`index`, `lesson`, `reference`)
- Callout blocks (`:::callout`, `:::callout-warn`, `:::callout-success`)
- Fenced code blocks (`title="..."`, `copy=false`) and Mermaid diagrams (```` ```mermaid ````)
- Captioned tables (`Table: Caption text`)
- Retrieval exercises (`:::exercise` and `{{blank:answer|hint|aria_label|size}}`)
- Retrieval quizzes (`:::quiz`)
- Interactive widgets (`{{widget:lesson-cards}}`, `{{widget:reference-cards}}`, `{{widget:part-explorer}}`, `{{widget:normalling-sim}}`, `{{widget:panel-bushing-calc}}`)
