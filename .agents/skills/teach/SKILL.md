---
name: teach
description: >-
  Interactive, stateful teaching workflow that builds self-contained HTML lessons, 
  reference sheets, learning records, and runnable Python/SKiDL lesson scripts in ./tutorial/.
  Use when the user asks to learn a topic, build or extend the SKiDL/Python
  circuit tutorial, create lessons or reference sheets, or invokes /teach.
---

# Interactive Teaching Workflow (`./tutorial/`)

The user has asked you to teach them something or build out the course materials. This is a stateful request — they intend to learn the topic over multiple sessions.

## Teaching Workspace (`./tutorial/`)

The dedicated teaching workspace lives inside `./tutorial/` at the root of this repository (so root hardware design files like `README.md`, `buffered_multiple.py`, and `BufferedMult.kicad_pcb` remain untouched). All course paths below are relative to `./tutorial/`, while `references/*-FORMAT.md` links resolve from this skill's directory (`.agents/skills/teach/`):

- `tutorial/MISSION.md`: A document capturing the _reason_ the user is interested in the topic. This grounds all teaching. Use the format in [MISSION-FORMAT.md](./references/MISSION-FORMAT.md).
- `tutorial/reference/*.md`: A directory of Markdown reference materials (compiled to `tutorial/reference/*.html` by `tutorial/build.py`, with `GLOSSARY.md` compiling to `glossary.html`). These are the compressed learnings from the lessons — SKiDL syntax cheat sheets, KiCad 10 symbol/footprint lookup patterns, JLCPCB/LCSC catalog rules, Eurorack standards, and glossaries. They are the raw units of learning, designed for quick reference and clean printing.
- `tutorial/RESOURCES.md`: A curated list of trusted resources and repository skills used to ground your teaching in verified knowledge. Use the format in [RESOURCES-FORMAT.md](./references/RESOURCES-FORMAT.md).
- `tutorial/learning-records/*.md`: A directory of learning records capturing what the user has learned. These are loosely equivalent to architectural decision records (ADRs) — they capture non-obvious lessons, prior knowledge, and key insights that drive future sessions and calculate the zone of proximal development. Titled `0001-<dash-case-name>.md`, incrementing sequentially. Use the format in [LEARNING-RECORD-FORMAT.md](./references/LEARNING-RECORD-FORMAT.md).
- `tutorial/lessons/*.md`: A directory of Markdown lesson sources (compiled to `tutorial/lessons/*.html` by `tutorial/build.py`). A **lesson** is a single, self-contained tutorial unit that teaches one tightly-scoped concept or skill tied to the mission. This is the primary unit of teaching in this workspace.
- `tutorial/index.md`: The Markdown course landing page (compiled to `tutorial/index.html` by `tutorial/build.py`) for GitHub Pages hosting, auto-rendering lesson cards via `{{widget:lesson-cards}}` and reference sheet cards via `{{widget:reference-cards}}`.
- `tutorial/build.py`: The Markdown-to-HTML static site builder (`markdown-it-py` + `pyyaml`). Only `.md` source files are tracked in Git (`tutorial/index.html`, `tutorial/lessons/*.html`, and `tutorial/reference/*.html` are gitignored and generated locally via `.venv/bin/python tutorial/build.py --check` or in CI via `.github/workflows/pages.yml`).
- `tutorial/apps/<NNNN-lesson-slug>/`: A series of runnable Python/SKiDL directories where each directory represents the exact runnable scripts and generated outputs after completing the corresponding lesson (`tutorial/lessons/<NNNN-lesson-slug>.md`).
- `tutorial/assets/*`: Reusable **components** shared across lessons (`style.css`, `course.js`, quiz/exercise widgets, interactive simulators). See [Assets](#assets).
- `tutorial/NOTES.md`: A scratchpad for recording user preferences or working notes.

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources (including the repository's `.agents/skills/skidl/`, `.agents/skills/lcsc/`, `.agents/skills/jlcpcb/`, `.agents/skills/bom/`, `.agents/skills/kicad/`, and `.agents/skills/datasheets/` skills, plus official SKiDL and KiCad documentation).
- **Skills**, acquired through highly-relevant interactive lessons devised by you, based on the knowledge.
- **Wisdom**, which comes from interacting with other learners and practitioners.

Before `tutorial/RESOURCES.md` is well-populated, your focus should be to catalog high-quality resources (both external docs and the verified `.agents/skills/*` reference guides in this repo) to help the user acquire knowledge. Never trust unverified parametric knowledge when a skill script or local library lookup can verify it.

### Fluency vs Storage Strength

Always distinguish between two types of learning:

- **Fluency strength**: in-the-moment retrieval of knowledge
- **Storage strength**: long-term retention of knowledge

Fluency can give an illusory sense of mastery, whereas storage strength is the real goal. Design lessons that build long-term retention through desirable difficulty:

- Using retrieval practice (recall from memory via interactive fill-in-the-blank code exercises and quizzes)
- Spacing (distributing practice and revisiting earlier concepts across lessons)
- Interleaving (mixing related skills, such as part lookup, pin indexing, net wiring, and ERC debugging)

## Lessons & Markdown-to-HTML Pipeline (`tutorial/build.py`)

A lesson is the primary artifact you produce: the unit in which knowledge and skills reach the user. Each lesson is authored as a clean Markdown file saved to `tutorial/lessons/` and titled `0001-<dash-case-name>.md`, incrementing sequentially (`0001`, `0002`, …), then compiled to HTML (`tutorial/lessons/<NNNN-slug>.html`) by running `.venv/bin/python tutorial/build.py --check`.

When teaching a programming framework or tool where the course needs a configured environment, start with a `0001-<dash-case-name>.md` bootstrap lesson covering `uv` virtual environment creation (`uv venv --clear --python 3.14 .venv` and `uv pip install skidl`), KiCad 10 symbol/footprint environment variables, and `ruff` linting setup so subsequent lessons have a concrete, runnable foundation.

### Markdown Directives & Frontmatter (`tutorial/build.py`)

All course pages (`tutorial/index.md`, `tutorial/lessons/*.md`, `tutorial/reference/*.md`) use YAML frontmatter (`type`, `id`, `title`, `kicker`, `lead`, plus `badge`, `summary`, `app_dir`, `meta`, `prev`, `next` for lessons or `nav_label`, `card_title`, `card_desc` for reference sheets) and clean Markdown directives:

- **Callouts**: `:::callout Title`, `:::callout-warn Title`, `:::callout-success Title` ... `:::`
- **Code Blocks with Captions**: ```` ```python title="tutorial/apps/..." copy=false ```` (and ```` ```mermaid ```` for `<pre class="mermaid">` diagrams)
- **Tables with Captions**: Precede a pipe table with `Table: Caption text` to wrap it in `<div class="table-wrap">` with `<caption>`.
- **Interactive Fill-in-the-Blank Exercises**: `:::exercise id="ex-NNNN-title" title="Retrieval Practice: ..."` containing a fenced code block with `{{blank:answer|hint|aria_label|size}}` tokens (use `/` inside `answer` for multi-answer alternatives like `128.5/128.50`).
- **Multiple-Choice Quizzes**: `:::quiz id="quiz-NNNN-title" title="Knowledge Check"` with numbered questions (`1. Question text`) and `- [x] Option text | Explanation` / `- [ ] Option text | Explanation`. `tutorial/build.py --check` enforces that all options within each question have identical word counts!
- **Interactive Widgets**: `{{widget:lesson-cards}}`, `{{widget:reference-cards}}`, `{{widget:part-explorer}}`, `{{widget:normalling-sim}}`, `{{widget:panel-bushing-calc}}`.

### Runnable Per-Lesson Python / SKiDL Directories (`tutorial/apps/<NNNN-lesson-slug>/`)

Back every lesson with a real, runnable directory under `tutorial/apps/<NNNN-lesson-slug>/` (matching the lesson filename stem):

1. **Tooling Stack (`uv` + Python 3.14 + `ruff` + `skidl`):**
   - Use the workspace's `.venv` created by `uv` (`.venv/bin/python`) and `ruff` for all lesson scripts, ancillary part-lookup tools, and circuit generators.
   - Include the pre-import environment setup (`XDG_DATA_HOME`, `MPLCONFIGDIR`, `KICAD10_SYMBOL_DIR`, `KICAD_SYMBOL_DIR`, `KICAD10_FOOTPRINT_DIR`) at the top of SKiDL scripts, using `# noqa: E402` on the subsequent `from skidl import ...` line so `ruff` passes cleanly.
   - Remember the macOS sandbox caveat from the `skidl` skill: reading `.kicad_sym` files under `/Applications/KiCad/...` requires running `.venv/bin/python` with `BypassSandbox: true` so SKiDL does not emit `ERROR: Can't open file` or `NO_LIB` netlist entries. `ruff check` and `ruff format` run inside the standard sandbox (`BypassSandbox: false`).
2. **Start from Nothing & Grow the Code Inline (Never Assume External File References):**
   - Never write lesson prose assuming the learner has `buffered_multiple.py` or `tutorial/apps/.../*.py` open in another window, and never link to `../../buffered_multiple.py` or `../apps/...` from lesson HTML (which would also 404 on GitHub Pages).
   - Instead, **start from an empty file in Lesson `0001` and progressively grow the Python script across the lessons**, showing both the newly added code blocks step-by-step AND the **complete, standalone, runnable Python script** (along with its verified terminal output) directly inside each lesson's HTML!
   - Early lessons can include runnable helper scripts in `tutorial/apps/<NNNN-slug>/` (shown in full inside the lesson) that demonstrate SKiDL's `search()`, `show()`, `search_footprints()`, and live JLCPCB/LCSC catalog queries (`.agents/skills/skidl/scripts/jlcpcb_search.py`), while also growing the main circuit script (e.g., adding the verified `FP_*` and `LCSC_*` constants in Stage 2).
   - Subsequent lessons progressively grow the Eurorack Buffered Multiple circuit (`buffered_multiple.py`):
     - `eurorack_power` `@subcircuit` (10-pin IDC header, `1N5819WS` Schottky reverse-polarity protection using `dest=TEMPLATE` and `part.fields`, bulk electrolytic caps).
     - `buffered_channel_1to3` `@subcircuit` (`TL074H` quad op-amp, `PESD12VL1BA` TVS diode, `100K` pull-down, `1K` input resistor, unity-gain input follower, and 3 output followers with `470R` series protection and `builtins.NC` on unused switched jack pins).
     - Cascaded normalling across Channels 1–3 (`1:3` -> `1:6` -> `1:9`), `POWER` drive flags, `NetClass` definitions (`Power` and `Signal`), `ERC()`, `generate_netlist()`, `generate_xml()`, and `generate_jlcpcb_bom()`.
3. **Execute, Lint & Reconcile Lessons with Reality:**
   - Run every script in `tutorial/apps/<NNNN-slug>/` using `.venv/bin/python` to verify that it executes cleanly and produces `0` ERC errors and `0` ERC warnings.
   - Because running a SKiDL script generates or overwrites `<script>_sklib.py` with unformatted code, **always run `ruff` after executing the script**:
     ```bash
     ruff check --fix tutorial/apps/<NNNN-slug>/*.py
     ruff format tutorial/apps/<NNNN-slug>/*.py
     ```
   - If anything does not line up between the runnable script output and the lesson HTML or reference sheets (`tutorial/reference/*.html`), update the HTML and shared assets immediately so the lesson and runnable code are 100% in sync.

### Visual Design, Prism.js & Mermaid.js

A lesson should be **beautiful**, with clean, readable typography and layout (think Tufte), since the user will return to these later to review:

- **Dark mode by default**: Use dark mode across all lessons and `tutorial/reference/*.html` documents (`<meta name="color-scheme" content="dark">` in `<head>` and `:root { color-scheme: dark; }` in the shared stylesheet), paired with a `@media print` light-mode override so lessons and reference documents print cleanly on paper. Pair `scrollbar-color` on `:root` with `scrollbar-width: thin` (required on macOS so custom scrollbars render) and wrap legacy `::-webkit-scrollbar` fallbacks in `@supports not (scrollbar-color: auto)`. Use high-contrast `accent-color` tokens for interactive form controls.
- **Modern web typography, transitions, and accessibility**: Enable cross-document view transitions (`@view-transition { navigation: auto; }` inside `@media (prefers-reduced-motion: no-preference)`), style focus rings with `:focus-visible` and `outline-offset: 2px` via `:where(...)` (never bare `:focus`), apply `text-wrap: balance` to headings/table headers (`h1, h2, h3, th`) and `text-wrap: pretty` to body copy (`p, li, blockquote`), use semantic HTML landmarks (`<header>`, `<nav>`, `<main>`, `<article>`, `<footer>`), and ensure scrollable `<pre>` code blocks receive `tabindex="0"` for keyboard scrolling (handled automatically in `tutorial/assets/course.js`).
- **Prism.js for syntax highlighting**: Format all code blocks with Prism.js (`<pre><code class="language-python">`, `language-bash`, etc.), and load the Prism `keep-markup` plugin when embedding interactive `<input>` blanks inside code blocks. Never hand-roll syntax `<span>` tags.
- **Mermaid.js for diagrams**: Use Mermaid.js (`<pre class="mermaid">` configured with `theme: "dark"`) for circuit signal flow, subcircuit hierarchy, normalling cascades, and BOM/netlist pipeline diagrams instead of ASCII-art diagrams.

### Course Index, Navigation & GitHub Pages Hosting

Keep the course navigable both locally and on GitHub Pages:

1. **Synchronize Navigation & Index via `tutorial/build.py --check` on Every New Lesson:** Whenever you add a lesson (`tutorial/lessons/<NNNN-slug>.md`) or reference sheet (`tutorial/reference/*.md`):
   - Populate its YAML frontmatter (`type: lesson`, `id: "NNNN"`, `title`, `kicker`, `lead`, `badge`, `summary`, `app_dir`, `meta`, `prev`, `next`) and update the previous lesson's `next:` frontmatter field.
   - Run `.venv/bin/python tutorial/build.py --check` so `tutorial/build.py` automatically regenerates `<nav class="course-nav">` across every page, updates the `.lesson-card` grid in `tutorial/index.html`, compiles all `.md` files to `.html`, and validates equal-word-count quiz rules and internal `.md` links (rewritten to `.html`).
   - Preserve the license link (`Apache License, Version 2.0`) and the `This is not an official Google product.` disclaimer in the course footer and `README.md`.
2. **GitHub Pages Deployment (`.github/workflows/pages.yml` & `tutorial/.nojekyll`):**
   - `.github/workflows/pages.yml` runs `python tutorial/build.py --out-dir _site --check` to compile the Markdown sources directly into `_site/` (`index.html`, `.nojekyll`, `assets/`, `lessons/*.html`, `reference/*.html`) so companion Python scripts (`tutorial/apps/`) and internal markdown files (`MISSION.md`, `RESOURCES.md`, `NOTES.md`, `learning-records/`) are excluded from the published web artifact.
   - Pass `env: NODE_OPTIONS: --no-deprecation` on the `actions/deploy-pages@v4` step to suppress the benign Node.js `[DEP0040] DeprecationWarning: The punycode module is deprecated` warning.

Each lesson should be short, focused, and completable quickly within working-memory limits, giving the user a single tangible win directly tied to the mission and within their zone of proximal development.

If possible, open the lesson file for the user or provide a direct clickable link. Every lesson should:
- Link via HTML anchors to adjacent lessons and `tutorial/reference/*.html` documents.
- Recommend a primary source (such as the relevant SKiDL docs page, datasheet, or skill reference).
- Include a reminder to ask follow-up questions to the agent.

## Assets

Lessons are built from reusable **components** stored in `tutorial/assets/`: stylesheets, quiz widgets, interactive circuit/normalling calculators or exercises, diagram helpers, and anything else a second lesson could reuse.

Reuse is the default, not the exception. Before authoring a lesson, read `tutorial/assets/` and build from the components already there. When a lesson needs something new and reusable, write it as a component in `tutorial/assets/` and link to it; never inline code a future lesson would duplicate.

A shared dark-mode stylesheet (`tutorial/assets/style.css`) and a shared script (`tutorial/assets/course.js`) that centrally loads and configures **Prism.js** (including `keep-markup`, `python`, `bash`, `json`, `csv`) and **Mermaid.js** (`theme: "dark"`) alongside reusable quiz and fill-in-the-blank code widgets are the first components the workspace earns: every lesson and reference sheet links them so the tutorial looks like one cohesive site.

## The Mission

Every lesson should be tied into the mission — the reason the user is learning the topic, captured in `tutorial/MISSION.md`.

If the user is unclear about aspects of the mission, or `tutorial/MISSION.md` is not yet populated, ask clarifying questions **one at a time** to confirm their concrete goal, starting point, and what success looks like.

Missions may evolve as the user develops more skills and knowledge. Update `tutorial/MISSION.md` and add a learning record when the mission shifts, confirming with the user first.

## Zone Of Proximal Development

Each lesson should challenge the user "just enough". Determine the next lesson by:

- Reading `tutorial/learning-records/`
- Checking what has already been built in `tutorial/lessons/` and `tutorial/apps/`
- Selecting the next step toward the mission in `tutorial/MISSION.md`

## Knowledge & Skills

- **Knowledge**: Design each lesson around a concrete skill. Present only the knowledge required to acquire that skill, backed by citations to `tutorial/RESOURCES.md` and `tutorial/reference/*.html`. Keep cognitive load low during knowledge acquisition.
- **Skills**: Build durability through effortful retrieval and immediate feedback loops:
  - Interactive fill-in-the-blank Python/SKiDL code blocks (using Prism `keep-markup`)
  - Multiple-choice retrieval quizzes with immediate feedback. **Quiz rule**: Every option within a quiz question must have the exact same word count (and similar character length), with the correct answer position varied across questions so formatting or length never leaks the answer.
  - Hands-on terminal verification steps using `uv`, `.venv/bin/python`, and `ruff`.

## Acquiring Wisdom

Wisdom comes from testing skills in real-world hardware and software communities (e.g., the SKiDL GitHub Discussions / forum, KiCad forum, `r/synthdiy`, ModWiggler DIY forum). Include high-signal communities in `tutorial/RESOURCES.md` while respecting any user preferences regarding community participation.

## Reference Documents

While creating lessons, maintain `tutorial/reference/*.html` cheat sheets — the compressed essence of the lessons designed for quick reference and printing (e.g., SKiDL API & Pin Indexing Cheat Sheet, KiCad 10 Symbol/Footprint & LCSC Lookup Reference, Eurorack Power & Audio Jack Normalling Reference, and Glossary following [GLOSSARY-FORMAT.md](./references/GLOSSARY-FORMAT.md)). Once a glossary is created, adhere to its terminology across every lesson.

## `tutorial/NOTES.md`

Record any teaching preferences or workflow notes expressed by the user in `tutorial/NOTES.md` and consult it before designing each lesson.
