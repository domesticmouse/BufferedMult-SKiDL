#!/usr/bin/env python3
"""
Markdown-to-HTML static site builder for the Eurorack Buffered Multiple SKiDL tutorial.

Compiles:
  - `tutorial/index.md` -> `index.html`
  - `tutorial/lessons/*.md` -> `lessons/*.html`
  - `tutorial/reference/*.md` -> `reference/*.html` (with `GLOSSARY.md` -> `glossary.html`)

Usage:
  # Build HTML in-place inside `tutorial/` for local previewing:
  .venv/bin/python tutorial/build.py --check

  # Build a standalone `_site/` directory for GitHub Pages deployment:
  .venv/bin/python tutorial/build.py --out-dir _site --check
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt

TUTORIAL_DIR = Path(__file__).resolve().parent

REFERENCE_ORDER = [
    ("skidl-cheatsheet.md", "skidl-cheatsheet.html", "SKiDL Ref"),
    ("kicad-jlcpcb-lookup.md", "kicad-jlcpcb-lookup.html", "Lookup Ref"),
    (
        "eurorack-power-and-normalling.md",
        "eurorack-power-and-normalling.html",
        "Eurorack Ref",
    ),
    ("GLOSSARY.md", "glossary.html", "Glossary"),
]

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FENCE_ATTR_RE = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')
BLANK_TOKEN_RE = re.compile(r"\{\{blank:([^}]+)\}\}")
CALLOUT_BLOCK_RE = re.compile(
    r"^:::(callout(?:-warn|-success|-info)?)(?:[ \t]+([^\n]+))?\n(.*?)^:::[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
EXERCISE_BLOCK_RE = re.compile(
    r"^:::exercise[ \t]+([^\n]+)\n(.*?)^:::[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
QUIZ_BLOCK_RE = re.compile(
    r"^:::quiz[ \t]+([^\n]+)\n(.*?)^:::[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
FENCED_CODE_RE = re.compile(
    r"^```([^\n]*)\n(.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
TABLE_CAPTION_RE = re.compile(
    r"<p>Table:\s*(.*?)</p>\s*<table>",
    re.DOTALL,
)
HREF_MD_RE = re.compile(r'href="([^":#]+?)\.md(#[^"]*)?"')


def create_md_parser() -> MarkdownIt:
    """Create a MarkdownIt parser with GFM tables enabled."""
    return MarkdownIt("commonmark", {"html": True, "typographer": False}).enable(
        "table"
    )


MD = create_md_parser()


def render_inline_md(text: str) -> str:
    """Render inline Markdown (such as `code`, **bold**, *em*, links) without <p> tags."""
    rendered = MD.renderInline(str(text).strip())
    return rewrite_md_links(rendered)


def rewrite_md_links(html_text: str) -> str:
    """Rewrite relative `.md` links (including `GLOSSARY.md`) to `.html`."""

    def _replace(match: re.Match[str]) -> str:
        stem_path = match.group(1)
        anchor = match.group(2) or ""
        if stem_path.endswith("GLOSSARY"):
            stem_path = stem_path[: -len("GLOSSARY")] + "glossary"
        return f'href="{stem_path}.html{anchor}"'

    return HREF_MD_RE.sub(_replace, html_text)


def parse_kv_attrs(attr_str: str) -> dict[str, str]:
    """Parse `key="value" flag=false` attribute strings on directives or code fences."""
    attrs: dict[str, str] = {}
    for match in FENCE_ATTR_RE.finditer(attr_str):
        key = match.group(1)
        val = match.group(2) if match.group(2) is not None else match.group(3)
        attrs[key] = val
    return attrs


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and Markdown body from a file."""
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta = yaml.safe_load(match.group(1)) or {}
    body = raw[match.end() :]
    return meta, body


def expand_blank_tokens(escaped_code: str) -> str:
    """
    Replace `{{blank:answer|hint|aria_label|size}}` inside an HTML-escaped code block
    with `<input type="text" class="code-blank" ...>`.
    Supports `/` inside `answer` for multi-answer alternatives (`128.5/128.50` -> `128.5|128.50`).
    """

    def _sub(match: re.Match[str]) -> str:
        raw_spec = html.unescape(match.group(1))
        parts = [p.strip() for p in raw_spec.split("|")]
        answer = parts[0].replace("/", "|") if len(parts) > 0 else ""
        hint = parts[1] if len(parts) > 1 else ""
        aria_label = parts[2] if len(parts) > 2 else "Code blank"
        size = (
            parts[3] if len(parts) > 3 else str(max(len(answer.split("|")[0]) + 1, 4))
        )
        return (
            f'<input type="text" class="code-blank" '
            f'aria-label="{html.escape(aria_label, quote=True)}" '
            f'data-answer="{html.escape(answer, quote=True)}" '
            f'data-hint="{html.escape(hint, quote=True)}" '
            f'size="{html.escape(size, quote=True)}">'
        )

    return BLANK_TOKEN_RE.sub(_sub, escaped_code)


def render_code_figure(
    info_line: str, code_body: str, *, allow_blanks: bool = False
) -> str:
    """Render a fenced code block or Mermaid diagram into its course HTML figure."""
    stripped_info = info_line.strip()
    parts = stripped_info.split(None, 1)
    lang = parts[0] if parts else "text"
    attr_str = parts[1] if len(parts) > 1 else ""
    attrs = parse_kv_attrs(attr_str)

    if lang == "mermaid":
        caption_raw = attrs.get("caption", "")
        escaped_mermaid = html.escape(code_body.rstrip("\n"), quote=False)
        caption_html = (
            f"\n  <figcaption>{render_inline_md(caption_raw)}</figcaption>"
            if caption_raw
            else ""
        )
        return (
            f'<figure class="diagram-card">\n'
            f'  <pre class="mermaid">{escaped_mermaid}</pre>{caption_html}\n'
            f"</figure>"
        )

    title = attrs.get("title", "")
    copy_enabled = attrs.get("copy", "true").lower() != "false"
    wrapper_tag = "div" if allow_blanks else "figure"
    escaped_code = html.escape(code_body.rstrip("\n"), quote=False)
    if allow_blanks:
        escaped_code = expand_blank_tokens(escaped_code)

    header_html = ""
    if title:
        copy_btn = (
            '\n    <button type="button" class="copy-btn">Copy</button>'
            if copy_enabled and not allow_blanks
            else ""
        )
        header_html = (
            f'  <div class="code-header">\n'
            f"    <span>{html.escape(title)}</span>{copy_btn}\n"
            f"  </div>\n"
        )

    return (
        f'<{wrapper_tag} class="code-figure">\n'
        f"{header_html}"
        f'  <pre><code class="language-{html.escape(lang)}">{escaped_code}</code></pre>\n'
        f"</{wrapper_tag}>"
    )


def render_exercise_block(attr_line: str, inner_md: str) -> str:
    """Render a `:::exercise` directive into an interactive `.exercise-box` section."""
    attrs = parse_kv_attrs(attr_line)
    ex_id = attrs.get("id", "ex-title")
    ex_title = render_inline_md(attrs.get("title", "Retrieval Practice"))

    code_figures: list[str] = []

    def _extract_code(match: re.Match[str]) -> str:
        idx = len(code_figures)
        code_figures.append(
            render_code_figure(match.group(1), match.group(2), allow_blanks=True)
        )
        return f"\n\n@@EXERCISE_CODE_{idx}@@\n\n"

    processed_md = FENCED_CODE_RE.sub(_extract_code, inner_md.strip())
    rendered_inner = rewrite_md_links(MD.render(processed_md).strip())
    for idx, fig_html in enumerate(code_figures):
        rendered_inner = rendered_inner.replace(
            f"<p>@@EXERCISE_CODE_{idx}@@</p>", fig_html
        )
        rendered_inner = rendered_inner.replace(f"@@EXERCISE_CODE_{idx}@@", fig_html)

    return (
        f'<section class="exercise-box" aria-labelledby="{html.escape(ex_id, quote=True)}">\n'
        f'  <h3 id="{html.escape(ex_id, quote=True)}">{ex_title}</h3>\n'
        f"  {rendered_inner}\n"
        f'  <div class="exercise-actions">\n'
        f'    <button type="button" class="btn btn-primary" data-action="check">Check Answers</button>\n'
        f'    <button type="button" class="btn" data-action="hint">Show Hint</button>\n'
        f'    <button type="button" class="btn" data-action="reset">Reset</button>\n'
        f"  </div>\n"
        f'  <div class="feedback-msg" role="status" aria-live="polite"></div>\n'
        f"</section>"
    )


def render_quiz_block(
    attr_line: str, yaml_body: str, *, source_name: str, errors: list[str]
) -> str:
    """Render a `:::quiz` YAML directive into `.quiz-section` and validate quiz rules."""
    attrs = parse_kv_attrs(attr_line)
    quiz_id = attrs.get("id", "quiz-title")
    quiz_title = render_inline_md(attrs.get("title", "Knowledge Check"))
    questions = yaml.safe_load(yaml_body) or []

    cards_html: list[str] = []
    for q_idx, q_item in enumerate(questions, start=1):
        q_text = render_inline_md(q_item.get("question", ""))
        options = q_item.get("options", [])
        if len(options) != 4:
            errors.append(
                f"{source_name}: Quiz question {q_idx} has {len(options)} options (expected 4)."
            )

        word_counts: list[int] = []
        correct_count = 0
        opts_html: list[str] = []

        for opt in options:
            letter = str(opt.get("letter", "")).strip()
            text_raw = str(opt.get("text", "")).strip()
            is_correct = bool(opt.get("correct", False))
            explain = str(opt.get("explain", "")).strip()
            if is_correct:
                correct_count += 1
            word_counts.append(len(text_raw.split()))

            opts_html.append(
                f'      <button type="button" class="quiz-option" '
                f'data-correct="{"true" if is_correct else "false"}" '
                f'data-explain="{html.escape(explain, quote=True)}">\n'
                f"        <span>{html.escape(letter)}.</span>\n"
                f"        <span>{render_inline_md(text_raw)}</span>\n"
                f"      </button>"
            )

        if len(set(word_counts)) > 1:
            errors.append(
                f"{source_name}: Quiz question {q_idx} option word counts are unequal: {word_counts}"
            )
        if correct_count != 1:
            errors.append(
                f"{source_name}: Quiz question {q_idx} has {correct_count} correct options (expected 1)."
            )

        cards_html.append(
            f'  <div class="quiz-card">\n'
            f'    <p class="quiz-question">{q_text}</p>\n'
            f'    <div class="quiz-options">\n'
            + "\n".join(opts_html)
            + "\n    </div>\n"
            '    <div class="feedback-msg" role="status" aria-live="polite"></div>\n'
            "  </div>"
        )

    return (
        f'<section class="quiz-section" aria-labelledby="{html.escape(quiz_id, quote=True)}">\n'
        f'  <h2 id="{html.escape(quiz_id, quote=True)}" style="margin-top:0;">{quiz_title}</h2>\n'
        + "\n\n".join(cards_html)
        + "\n</section>"
    )


def render_callout_block(kind: str, title_raw: str, body_md: str) -> str:
    """Render a `:::callout`, `:::callout-warn`, or `:::callout-success` block."""
    cls = "callout" if kind == "callout" else f"callout {kind}"
    title_html = render_inline_md(title_raw or "")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body_md.strip()) if p.strip()]
    rendered_paras = [
        f'<p style="margin:0;">{render_inline_md(p)}</p>' for p in paragraphs
    ]
    return (
        f'<div class="{cls}">\n'
        f'  <div class="callout-title">{title_html}</div>\n'
        + "\n".join(f"  {p}" for p in rendered_paras)
        + "\n</div>"
    )


def widget_part_explorer() -> str:
    """Return the interactive Component & Pinout Explorer widget for Lesson 0001."""
    return """<section id="part-explorer" class="exercise-box" aria-labelledby="explorer-heading">
  <h3 id="explorer-heading">Buffered Multiple Component &amp; Pinout Explorer</h3>
  <div class="explorer-toolbar">
    <label for="explorer-filter" class="visually-hidden">Filter components by keyword, pin, or LCSC number</label>
    <input id="explorer-filter" type="search" class="explorer-input" placeholder="Filter by part, symbol, pin (e.g. TL074, TN, SOD-323, C25803)…">
    <label for="explorer-class" class="visually-hidden">Filter by JLCPCB assembly class</label>
    <select id="explorer-class" class="btn">
      <option value="all">All Classes (SMT + THT)</option>
      <option value="Basic">JLCPCB Basic ($0 Feeder)</option>
      <option value="Extended">JLCPCB Extended</option>
      <option value="THT">Manual THT (Hand-Soldered)</option>
    </select>
  </div>
  <p id="explorer-count" style="font-family:var(--font-mono);font-size:0.82rem;color:var(--text-muted);margin:0 0 0.6rem;" aria-live="polite"></p>
  <div class="table-wrap scroller" style="margin:0;">
    <table>
      <caption>Verified KiCad 10 symbol pins, footprints, and LCSC numbers</caption>
      <thead>
        <tr>
          <th scope="col">Value / MPN</th>
          <th scope="col">KiCad 10 Symbol</th>
          <th scope="col">SKiDL Pin Indexing</th>
          <th scope="col">Footprint</th>
          <th scope="col">LCSC &amp; Class</th>
        </tr>
      </thead>
      <tbody>
        <tr data-part="tl074" data-class="Extended">
          <td><code>TL074H</code><br><small>TL074HIDR</small></td>
          <td><code>Amplifier_Operational:TL074</code></td>
          <td><code>u["V+"]</code> (4), <code>u["V-"]</code> (11)<br><code>u.p[1..3]</code>, <code>u.p[5..10]</code>, <code>u.p[12..14]</code></td>
          <td><code>Package_SO:SOIC-14_3.9x8.7mm_P1.27mm</code></td>
          <td><code>C2878713</code> · <span class="badge badge-warn">Extended</span></td>
        </tr>
        <tr data-part="1n5819ws" data-class="Basic">
          <td><code>1N5819WS</code><br><small>Schottky 40V 1A</small></td>
          <td><code>Device:D_Schottky</code></td>
          <td><code>d["K"]</code> (pin 1), <code>d["A"]</code> (pin 2)</td>
          <td><code>Diode_SMD:D_SOD-323</code></td>
          <td><code>C191023</code> · <span class="badge badge-success">Basic</span></td>
        </tr>
        <tr data-part="pesd12vl1ba" data-class="Extended">
          <td><code>PESD12VL1BA</code><br><small>12V Bidir TVS</small></td>
          <td><code>Device:D_TVS</code></td>
          <td><code>in_jack &amp; d_tvs &amp; gnd</code> (pins 1/A1, 2/A2)</td>
          <td><code>Diode_SMD:D_SOD-323</code></td>
          <td><code>C38558</code> · <span class="badge badge-warn">Extended</span></td>
        </tr>
        <tr data-part="100nf" data-class="Basic">
          <td><code>100nF</code><br><small>CC0603KRX7R9BB104</small></td>
          <td><code>Device:C</code></td>
          <td><code>vcc &amp; c_dec &amp; gnd</code> (pins 1, 2)</td>
          <td><code>Capacitor_SMD:C_0603_1608Metric</code></td>
          <td><code>C14663</code> · <span class="badge badge-success">Basic</span></td>
        </tr>
        <tr data-part="100k" data-class="Basic">
          <td><code>100K</code><br><small>0603WAF1003T5E</small></td>
          <td><code>Device:R</code></td>
          <td><code>in_jack &amp; r_pd &amp; gnd</code> (pins 1, 2)</td>
          <td><code>Resistor_SMD:R_0603_1608Metric</code></td>
          <td><code>C25803</code> · <span class="badge badge-success">Basic</span></td>
        </tr>
        <tr data-part="1k" data-class="Basic">
          <td><code>1K</code><br><small>0603WAF1001T5E</small></td>
          <td><code>Device:R</code></td>
          <td><code>in_jack &amp; r_in &amp; in_sig</code> (pins 1, 2)</td>
          <td><code>Resistor_SMD:R_0603_1608Metric</code></td>
          <td><code>C21190</code> · <span class="badge badge-success">Basic</span></td>
        </tr>
        <tr data-part="470r" data-class="Basic">
          <td><code>470R</code><br><small>0603WAF4700T5E</small></td>
          <td><code>Device:R</code></td>
          <td><code>op_out &amp; r_out &amp; jack_tip</code> (pins 1, 2)</td>
          <td><code>Resistor_SMD:R_0603_1608Metric</code></td>
          <td><code>C23179</code> · <span class="badge badge-success">Basic</span></td>
        </tr>
        <tr data-part="wqp-pj398sm" data-class="THT">
          <td><code>WQP-PJ398SM</code><br><small>Thonkiconn Jack</small></td>
          <td><code>Connector_Audio:AudioJack2_SwitchT</code></td>
          <td><code>j["S"]</code>, <code>j["T"]</code>, <code>j["TN"]</code></td>
          <td><code>Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles</code></td>
          <td>Manual THT (DNP for SMT)</td>
        </tr>
        <tr data-part="10uf" data-class="THT">
          <td><code>10uF</code><br><small>ECEA1EKS100</small></td>
          <td><code>Device:C_Polarized</code></td>
          <td><code>c_bulk[1]</code> (+), <code>c_bulk[2]</code> (-)</td>
          <td><code>Capacitor_THT:CP_Radial_D5.0mm_P2.00mm</code></td>
          <td>Manual THT (DNP for SMT)</td>
        </tr>
        <tr data-part="eurorack_pwr" data-class="THT">
          <td><code>EURORACK_PWR_10PIN</code><br><small>2x5 Shrouded IDC</small></td>
          <td><code>Connector_Generic:Conn_02x05_Odd_Even</code></td>
          <td><code>j_pwr[1, 2]</code>, <code>j_pwr[3..8]</code>, <code>j_pwr[9, 10]</code></td>
          <td><code>Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical</code></td>
          <td>Manual THT (DNP for SMT)</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>"""


def widget_normalling_sim() -> str:
    """Return the interactive 1:3 / 1:6 / 1:9 Cascaded Normalling Simulator for Lesson 0004."""
    return """<section id="normalling-sim" class="exercise-box" aria-labelledby="sim-heading">
  <div class="norm-ch-header">
    <h3 id="sim-heading" style="margin:0;">Interactive <code>1:3 / 1:6 / 1:9</code> Normalling Simulator</h3>
    <span id="sim-topology-badge" class="badge badge-accent">Active Topology: 1-to-9 Cascaded Multiple</span>
  </div>
  <p id="sim-summary" style="font-family:var(--font-mono);font-size:0.82rem;color:var(--text-muted);margin:0 0 0.85rem;" aria-live="polite"></p>

  <div class="norm-sim-grid">
    <!-- Channel 1 -->
    <div class="norm-ch-card">
      <div class="norm-ch-header">
        <label for="sim-patch-1" class="norm-patch-label">
          <input type="checkbox" id="sim-patch-1" checked>
          <span>Patch Cable in <code>IN_1</code> (<code>J2</code>)</span>
        </label>
        <span id="sim-tn-1" class="badge badge-accent">TN Switch: OPEN</span>
      </div>
      <div class="norm-cv-row">
        <label for="sim-cv-1"><code>IN_1</code> CV:</label>
        <input type="range" id="sim-cv-1" min="-10" max="10" step="0.25" value="5.0">
        <span id="sim-cv-val-1">+5.00V</span>
      </div>
      <div style="font-size:0.8rem;color:var(--text-secondary);">
        Source into <code>U1A</code>: <code id="sim-buf-1">IN_1 Tip (+5.00V)</code>
      </div>
      <ul class="norm-outputs-list" role="list">
        <li><span><code>OUT_1A</code> (<code>J3</code>)</span><strong id="sim-out-1A">+5.00V</strong></li>
        <li><span><code>OUT_1B</code> (<code>J4</code>)</span><strong id="sim-out-1B">+5.00V</strong></li>
        <li><span><code>OUT_1C</code> (<code>J5</code>)</span><strong id="sim-out-1C">+5.00V</strong></li>
      </ul>
    </div>

    <!-- Channel 2 -->
    <div class="norm-ch-card">
      <div class="norm-ch-header">
        <label for="sim-patch-2" class="norm-patch-label">
          <input type="checkbox" id="sim-patch-2">
          <span>Patch Cable in <code>IN_2</code> (<code>J6</code>)</span>
        </label>
        <span id="sim-tn-2" class="badge badge-success">TN Switch: CLOSED</span>
      </div>
      <div class="norm-cv-row">
        <label for="sim-cv-2"><code>IN_2</code> CV:</label>
        <input type="range" id="sim-cv-2" min="-10" max="10" step="0.25" value="-2.5">
        <span id="sim-cv-val-2">-2.50V</span>
      </div>
      <div style="font-size:0.8rem;color:var(--text-secondary);">
        Source into <code>U2A</code>: <code id="sim-buf-2">J6.TN ← CH1_BUF (+5.00V)</code>
      </div>
      <ul class="norm-outputs-list" role="list">
        <li><span><code>OUT_2A</code> (<code>J7</code>)</span><strong id="sim-out-2A">+5.00V</strong></li>
        <li><span><code>OUT_2B</code> (<code>J8</code>)</span><strong id="sim-out-2B">+5.00V</strong></li>
        <li><span><code>OUT_2C</code> (<code>J9</code>)</span><strong id="sim-out-2C">+5.00V</strong></li>
      </ul>
    </div>

    <!-- Channel 3 -->
    <div class="norm-ch-card">
      <div class="norm-ch-header">
        <label for="sim-patch-3" class="norm-patch-label">
          <input type="checkbox" id="sim-patch-3">
          <span>Patch Cable in <code>IN_3</code> (<code>J10</code>)</span>
        </label>
        <span id="sim-tn-3" class="badge badge-success">TN Switch: CLOSED</span>
      </div>
      <div class="norm-cv-row">
        <label for="sim-cv-3"><code>IN_3</code> CV:</label>
        <input type="range" id="sim-cv-3" min="-10" max="10" step="0.25" value="2.0">
        <span id="sim-cv-val-3">+2.00V</span>
      </div>
      <div style="font-size:0.8rem;color:var(--text-secondary);">
        Source into <code>U3A</code>: <code id="sim-buf-3">J10.TN ← CH2_BUF (+5.00V)</code>
      </div>
      <ul class="norm-outputs-list" role="list">
        <li><span><code>OUT_3A</code> (<code>J11</code>)</span><strong id="sim-out-3A">+5.00V</strong></li>
        <li><span><code>OUT_3B</code> (<code>J12</code>)</span><strong id="sim-out-3B">+5.00V</strong></li>
        <li><span><code>OUT_3C</code> (<code>J13</code>)</span><strong id="sim-out-3C">+5.00V</strong></li>
      </ul>
    </div>
  </div>
</section>"""


def widget_panel_bushing_calc() -> str:
    """Return the interactive WQP-PJ398SM Bushing Offset & Panel Coordinate Calculator for Lesson 0006."""
    return """<section class="exercise-box" id="panel-bushing-calc" aria-labelledby="calc-0006-title">
  <h3 id="calc-0006-title">Interactive <code>WQP-PJ398SM</code> Bushing Offset &amp; Panel Coordinate Calculator</h3>
  <p>
    Select any of the 12 jacks (<code>J2</code>–<code>J13</code>) and inspect how its main-PCB footprint coordinate transforms into the bushing center, panel-local drill hole, and silkscreen label safe zones (outside the <code>9.5 mm</code> M6 nut diameter):
  </p>
  <div class="explorer-toolbar">
    <label style="flex:1 1 240px;">
      <span class="visually-hidden">Select Jack</span>
      <select id="calc-jack-select" class="explorer-input" style="width:100%;">
        <option value="J2|IN 1|25.00|27.00">J2 (IN 1) — Row 1 Left @ (25.00, 27.00 mm)</option>
        <option value="J3|OUT 1A|35.00|27.00">J3 (OUT 1A) — Row 1 Right @ (35.00, 27.00 mm)</option>
        <option value="J4|OUT 1B|25.00|40.50">J4 (OUT 1B) — Row 2 Left @ (25.00, 40.50 mm)</option>
        <option value="J5|OUT 1C|35.00|40.50">J5 (OUT 1C) — Row 2 Right @ (35.00, 40.50 mm)</option>
        <option value="J6|IN 2|25.00|59.00">J6 (IN 2) — Row 3 Left @ (25.00, 59.00 mm)</option>
        <option value="J7|OUT 2A|35.00|59.00">J7 (OUT 2A) — Row 3 Right @ (35.00, 59.00 mm)</option>
        <option value="J8|OUT 2B|25.00|72.50">J8 (OUT 2B) — Row 4 Left @ (25.00, 72.50 mm)</option>
        <option value="J9|OUT 2C|35.00|72.50">J9 (OUT 2C) — Row 4 Right @ (35.00, 72.50 mm)</option>
        <option value="J10|IN 3|25.00|91.00">J10 (IN 3) — Row 5 Left @ (25.00, 91.00 mm)</option>
        <option value="J11|OUT 3A|35.00|91.00">J11 (OUT 3A) — Row 5 Right @ (35.00, 91.00 mm)</option>
        <option value="J12|OUT 3B|25.00|104.50">J12 (OUT 3B) — Row 6 Left @ (25.00, 104.50 mm)</option>
        <option value="J13|OUT 3C|35.00|104.50">J13 (OUT 3C) — Row 6 Right @ (35.00, 104.50 mm)</option>
      </select>
    </label>
    <label style="flex:0 1 220px;">
      <span class="visually-hidden">Footprint Rotation</span>
      <select id="calc-rot-select" class="explorer-input" style="width:100%;">
        <option value="0">Rotation: 0° (Standard Vertical)</option>
        <option value="90">Rotation: 90° CCW</option>
        <option value="180">Rotation: 180° Inverted</option>
        <option value="270">Rotation: 270° CCW</option>
      </select>
    </label>
  </div>
  <ul class="norm-outputs-list">
    <li><span>1. Main PCB Footprint Origin (Pad S)</span><strong id="calc-out-fp">J2 (IN 1) @ (25.00, 27.00 mm)</strong></li>
    <li><span>2. Rotated Bushing Offset (dX, dY)</span><strong id="calc-out-delta">(+0.00, +6.48 mm) [rot=0°]</strong></li>
    <li><span>3. Main PCB Bushing Shaft Center</span><strong id="calc-out-bush">(25.00, 33.48 mm)</strong></li>
    <li><span>4. Panel-Local 6.2 mm Hole Center</span><strong id="calc-out-panel">(5.00, 23.73 mm)</strong></li>
    <li><span>5. Recommended Silkscreen Label Y</span><strong id="calc-out-nut">Y = 17.50 mm (above) or Y = 29.96 mm (below)</strong></li>
  </ul>
</section>"""


def render_lesson_cards(lessons: list[dict[str, Any]]) -> str:
    """Render the `.lesson-grid` cards for `tutorial/index.html` from lesson frontmatter."""
    cards: list[str] = []
    for item in lessons:
        meta = item["meta"]
        card = meta.get("card", {})
        href = f"lessons/{item['html_name']}"
        title_html = render_inline_md(card.get("title", meta.get("title", "")))
        summary_html = render_inline_md(card.get("summary", meta.get("lead", "")))
        meta_items = "\n".join(
            f"        <li>{render_inline_md(m)}</li>" for m in card.get("meta", [])
        )
        cards.append(
            f'  <div class="lesson-card">\n'
            f"    <div>\n"
            f'      <div class="meta-bar" style="margin:0 0 0.5rem;">\n'
            f'        <span class="badge badge-accent">{html.escape(card.get("badge", ""))}</span>\n'
            f'        <span class="badge badge-success">{html.escape(card.get("status", ""))}</span>\n'
            f"      </div>\n"
            f'      <h3><a href="{href}">{title_html}</a></h3>\n'
            f"      <p>{summary_html}</p>\n"
            f'      <ul class="lesson-meta-list">\n'
            f"{meta_items}\n"
            f"      </ul>\n"
            f"    </div>\n"
            f'    <div class="card-footer">\n'
            f"      <span>{html.escape(card.get('app_dir', ''))}</span>\n"
            f'      <a href="{href}">Start →</a>\n'
            f"    </div>\n"
            f"  </div>"
        )
    return '<div class="lesson-grid">\n' + "\n\n".join(cards) + "\n</div>"


def render_reference_cards(references: list[dict[str, Any]]) -> str:
    """Render the reference `.lesson-grid` cards for `tutorial/index.html`."""
    cards: list[str] = []
    for item in references:
        meta = item["meta"]
        card = meta.get("card", {})
        href = f"reference/{item['html_name']}"
        title_html = render_inline_md(card.get("title", meta.get("title", "")))
        summary_html = render_inline_md(card.get("summary", meta.get("lead", "")))
        cards.append(
            f'  <div class="lesson-card">\n'
            f"    <div>\n"
            f'      <h3><a href="{href}">{title_html}</a></h3>\n'
            f"      <p>{summary_html}</p>\n"
            f"    </div>\n"
            f'    <div class="card-footer">\n'
            f"      <span>./{href}</span>\n"
            f'      <a href="{href}">Open →</a>\n'
            f"    </div>\n"
            f"  </div>"
        )
    return '<div class="lesson-grid">\n' + "\n\n".join(cards) + "\n</div>"


def enhance_tables(rendered_html: str) -> str:
    """
    Convert `<p>Table: Caption</p><table>...` into `<div class="table-wrap scroller"><table><caption>...`
    and add `scope="col"` on `<th>` elements.
    """
    out = TABLE_CAPTION_RE.sub(
        lambda m: (
            f'<div class="table-wrap scroller">\n<table>\n<caption>{m.group(1)}</caption>'
        ),
        rendered_html,
    )
    out = out.replace("<table>", '<div class="table-wrap scroller">\n<table>')
    out = out.replace(
        '<div class="table-wrap scroller">\n<div class="table-wrap scroller">\n<table>',
        '<div class="table-wrap scroller">\n<table>',
    )
    out = out.replace("</table>", "</table>\n</div>")
    out = out.replace("<th>", '<th scope="col">')
    return out


def render_glossary_body(md_body: str) -> str:
    """
    Compile `GLOSSARY.md` (`**Term**:\nDefinition\n_Avoid_: ...`) into semantic `<dl>/<dt>/<dd>` HTML.
    """
    lines = md_body.strip().splitlines()
    blocks: list[str] = []
    in_dl = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("# "):
            i += 1
            continue
        if line.startswith("## "):
            if in_dl:
                blocks.append("</dl>")
                in_dl = False
            heading_text = render_inline_md(line[3:].strip())
            blocks.append(f"<h2>{heading_text}</h2>")
            i += 1
            continue
        if line.startswith("**") and line.endswith("**:"):
            if not in_dl:
                blocks.append("<dl>")
                in_dl = True
            term_raw = line[:-1]  # Keep `**Term**`
            term_html = render_inline_md(term_raw)
            i += 1
            def_lines: list[str] = []
            avoid_line = ""
            while i < len(lines) and lines[i].strip():
                cur = lines[i].strip()
                if cur.startswith(("_Avoid_:", "*Avoid*:")):
                    avoid_line = cur.split(":", 1)[1].strip()
                else:
                    def_lines.append(cur)
                i += 1
            def_html = render_inline_md(" ".join(def_lines))
            avoid_suffix = ""
            if avoid_line:
                avoid_text = render_inline_md(avoid_line.rstrip("."))
                avoid_suffix = f"<br>\n    <em>Avoid</em>: {avoid_text}."
            blocks.append(
                f"  <dt>{term_html}</dt>\n  <dd>\n    {def_html}{avoid_suffix}\n  </dd>"
            )
            continue
        i += 1

    if in_dl:
        blocks.append("</dl>")

    return "\n\n".join(blocks)


def compile_markdown_body(
    md_body: str,
    *,
    source_name: str,
    lessons: list[dict[str, Any]],
    references: list[dict[str, Any]],
    errors: list[str],
) -> str:
    """Compile a Markdown body with custom blocks, fences, widgets, and tables into HTML."""
    placeholders: dict[str, str] = {}

    def _stash(html_fragment: str) -> str:
        token = f"@@HTML_BLOCK_{len(placeholders)}@@"
        placeholders[token] = html_fragment
        return f"\n\n{token}\n\n"

    # 1. Extract `:::exercise` blocks
    text = EXERCISE_BLOCK_RE.sub(
        lambda m: _stash(render_exercise_block(m.group(1), m.group(2))),
        md_body,
    )

    # 2. Extract `:::quiz` blocks
    text = QUIZ_BLOCK_RE.sub(
        lambda m: _stash(
            render_quiz_block(
                m.group(1), m.group(2), source_name=source_name, errors=errors
            )
        ),
        text,
    )

    # 3. Extract `:::callout*` blocks
    text = CALLOUT_BLOCK_RE.sub(
        lambda m: _stash(
            render_callout_block(m.group(1), m.group(2) or "", m.group(3))
        ),
        text,
    )

    # 4. Extract fenced code and Mermaid blocks
    text = FENCED_CODE_RE.sub(
        lambda m: _stash(render_code_figure(m.group(1), m.group(2))),
        text,
    )

    # 5. Extract `{{widget:...}}` shortcodes
    widget_map = {
        "{{widget:part-explorer}}": widget_part_explorer,
        "{{widget:normalling-sim}}": widget_normalling_sim,
        "{{widget:panel-bushing-calc}}": widget_panel_bushing_calc,
        "{{widget:lesson-cards}}": lambda: render_lesson_cards(lessons),
        "{{widget:reference-cards}}": lambda: render_reference_cards(references),
    }
    for shortcode, factory in widget_map.items():
        if shortcode in text:
            text = text.replace(shortcode, _stash(factory()))

    # 6. Render standard Markdown and enhance tables + links
    rendered = MD.render(text)
    rendered = enhance_tables(rendered)
    rendered = rewrite_md_links(rendered)

    # 7. Restore stashed HTML blocks
    for token, fragment in placeholders.items():
        rendered = rendered.replace(f"<p>{token}</p>", fragment)
        rendered = rendered.replace(token, fragment)

    return rendered.strip()


def build_nav_html(
    *,
    active_id: str,
    rel_root: str,
    lessons: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> str:
    """Build the `<nav class="course-nav">` bar for any page in the tutorial."""
    links: list[str] = []
    idx_current = ' aria-current="page"' if active_id == "index" else ""
    links.append(f'        <a href="{rel_root}index.html"{idx_current}>Index</a>')

    for les in lessons:
        lid = les["nav_id"]
        cur = ' aria-current="page"' if active_id == lid else ""
        href = (
            f"{les['html_name']}"
            if rel_root == "../" and active_id.isdigit()
            else f"{rel_root}lessons/{les['html_name']}"
        )
        links.append(f'        <a href="{href}"{cur}>{html.escape(lid)}</a>')

    links.append('        <span class="nav-sep" aria-hidden="true">|</span>')

    for ref in references:
        rid = ref["nav_id"]
        cur = ' aria-current="page"' if active_id == rid else ""
        href = (
            f"{ref['html_name']}"
            if rel_root == "../" and not active_id.isdigit() and active_id != "index"
            else f"{rel_root}reference/{ref['html_name']}"
        )
        links.append(
            f'        <a href="{href}"{cur}>{html.escape(ref["nav_label"])}</a>'
        )

    return "\n".join(links)


def render_full_page(
    *,
    meta: dict[str, Any],
    body_html: str,
    active_id: str,
    rel_root: str,
    lessons: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> str:
    """Wrap compiled article content in the shared dark-mode HTML5 document shell."""
    page_title = html.escape(
        meta.get("page_title", meta.get("title", "Eurorack SKiDL Tutorial"))
    )
    kicker = html.escape(meta.get("kicker", ""))
    h1_html = render_inline_md(meta.get("title", ""))
    lead_html = render_inline_md(meta.get("lead", ""))

    badges = meta.get("badges", [])
    meta_bar_html = ""
    if badges:
        spans = "\n".join(
            f'        <span class="badge badge-{html.escape(b.get("style", "accent"))}">'
            f"{html.escape(b.get('text', ''))}</span>"
            for b in badges
        )
        meta_bar_html = f'\n      <div class="meta-bar">\n{spans}\n      </div>\n'

    pager_html = ""
    pager_prev = meta.get("pager_prev")
    pager_next = meta.get("pager_next")
    if pager_prev and pager_next:
        pager_html = (
            f'\n      <nav class="pager" aria-label="Lesson pagination">\n'
            f'        <a href="{html.escape(pager_prev["href"], quote=True)}">\n'
            f'          <span class="pager-label">{html.escape(pager_prev["label"])}</span>\n'
            f'          <span class="pager-title">{html.escape(pager_prev["title"])}</span>\n'
            f"        </a>\n"
            f'        <a href="{html.escape(pager_next["href"], quote=True)}">\n'
            f'          <span class="pager-label">{html.escape(pager_next["label"])}</span>\n'
            f'          <span class="pager-title">{html.escape(pager_next["title"])}</span>\n'
            f"        </a>\n"
            f"      </nav>"
        )

    nav_links = build_nav_html(
        active_id=active_id,
        rel_root=rel_root,
        lessons=lessons,
        references=references,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{page_title}</title>
  <link rel="stylesheet" href="{rel_root}assets/style.css">
  <script src="{rel_root}assets/course.js" defer></script>
</head>
<body>
  <header class="site-header">
    <a href="#content" class="skip-link visually-hidden">Skip to main content</a>
    <div class="header-inner">
      <a class="brand-title" href="{rel_root}index.html">
        <span>Buffered Multiple Course</span>
        <span class="brand-badge">KiCad 10 + SKiDL</span>
      </a>
      <nav class="course-nav" aria-label="Course">
{nav_links}
      </nav>
    </div>
  </header>

  <main id="content" class="page-main" tabindex="-1">
    <article>
      <div class="lesson-kicker">{kicker}</div>
      <h1>{h1_html}</h1>
      <p class="lead">
        {lead_html}
      </p>{meta_bar_html}
{body_html}{pager_html}
    </article>
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <span>Licensed under the <a href="https://www.apache.org/licenses/LICENSE-2.0">Apache License, Version 2.0</a>.</span>
      <span>This is not an official Google product.</span>
    </div>
  </footer>
</body>
</html>
"""


def verify_internal_links(
    out_dir: Path, html_files: list[Path], errors: list[str]
) -> None:
    """Verify that every relative `href="..."` or `src="..."` in generated HTML resolves."""
    attr_re = re.compile(r'(?:href|src)="([^"#]+)')
    for html_path in html_files:
        content = html_path.read_text(encoding="utf-8")
        for match in attr_re.finditer(content):
            target = match.group(1).strip()
            if not target or target.startswith(
                ("http://", "https://", "mailto:", "javascript:")
            ):
                continue
            resolved = (html_path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{html_path.relative_to(out_dir)}: Broken relative link '{target}'"
                )


def build_site(out_dir: Path, *, check: bool = False) -> int:
    """Compile all tutorial Markdown files into `out_dir`."""
    errors: list[str] = []
    lessons_dir = TUTORIAL_DIR / "lessons"
    ref_dir = TUTORIAL_DIR / "reference"

    # 1. Discover and parse all lessons in sorted order
    lesson_records: list[dict[str, Any]] = []
    for md_path in sorted(lessons_dir.glob("[0-9][0-9][0-9][0-9]-*.md")):
        meta, body = parse_frontmatter(md_path)
        nav_id = str(meta.get("nav_id", md_path.stem.split("-", 1)[0]))
        lesson_records.append(
            {
                "md_path": md_path,
                "html_name": f"{md_path.stem}.html",
                "nav_id": nav_id,
                "meta": meta,
                "body": body,
            }
        )

    # 2. Discover and parse all reference sheets in canonical order
    ref_records: list[dict[str, Any]] = []
    for md_name, html_name, default_label in REFERENCE_ORDER:
        md_path = ref_dir / md_name
        if not md_path.is_file():
            errors.append(f"Missing reference Markdown file: {md_path}")
            continue
        meta, body = parse_frontmatter(md_path)
        ref_records.append(
            {
                "md_path": md_path,
                "html_name": html_name,
                "nav_id": html_name.removesuffix(".html"),
                "nav_label": meta.get("nav_label", default_label),
                "meta": meta,
                "body": body,
                "is_glossary": md_name == "GLOSSARY.md",
            }
        )

    # Prepare output directories
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lessons").mkdir(parents=True, exist_ok=True)
    (out_dir / "reference").mkdir(parents=True, exist_ok=True)

    # Copy `.nojekyll` and `assets/` when building to an external directory (such as `_site/`)
    if out_dir.resolve() != TUTORIAL_DIR.resolve():
        nojekyll = TUTORIAL_DIR / ".nojekyll"
        if nojekyll.is_file():
            shutil.copy2(nojekyll, out_dir / ".nojekyll")
        out_assets = out_dir / "assets"
        if out_assets.exists():
            shutil.rmtree(out_assets)
        shutil.copytree(TUTORIAL_DIR / "assets", out_assets)

    written_html: list[Path] = []

    # 3. Render `tutorial/index.md` -> `index.html`
    index_md = TUTORIAL_DIR / "index.md"
    if not index_md.is_file():
        errors.append(f"Missing course index file: {index_md}")
    else:
        idx_meta, idx_body = parse_frontmatter(index_md)
        idx_body_html = compile_markdown_body(
            idx_body,
            source_name="index.md",
            lessons=lesson_records,
            references=ref_records,
            errors=errors,
        )
        idx_html = render_full_page(
            meta=idx_meta,
            body_html=idx_body_html,
            active_id="index",
            rel_root="",
            lessons=lesson_records,
            references=ref_records,
        )
        idx_out = out_dir / "index.html"
        idx_out.write_text(idx_html, encoding="utf-8")
        written_html.append(idx_out)

    # 4. Render lessons
    for les in lesson_records:
        body_html = compile_markdown_body(
            les["body"],
            source_name=f"lessons/{les['md_path'].name}",
            lessons=lesson_records,
            references=ref_records,
            errors=errors,
        )
        page_html = render_full_page(
            meta=les["meta"],
            body_html=body_html,
            active_id=les["nav_id"],
            rel_root="../",
            lessons=lesson_records,
            references=ref_records,
        )
        out_path = out_dir / "lessons" / les["html_name"]
        out_path.write_text(page_html, encoding="utf-8")
        written_html.append(out_path)

    # 5. Render reference pages
    for ref in ref_records:
        if ref["is_glossary"]:
            body_html = render_glossary_body(ref["body"])
        else:
            body_html = compile_markdown_body(
                ref["body"],
                source_name=f"reference/{ref['md_path'].name}",
                lessons=lesson_records,
                references=ref_records,
                errors=errors,
            )
        page_html = render_full_page(
            meta=ref["meta"],
            body_html=body_html,
            active_id=ref["nav_id"],
            rel_root="../",
            lessons=lesson_records,
            references=ref_records,
        )
        out_path = out_dir / "reference" / ref["html_name"]
        out_path.write_text(page_html, encoding="utf-8")
        written_html.append(out_path)

    if check:
        verify_internal_links(out_dir, written_html, errors)

    print(
        f"Built {len(written_html)} HTML pages into {out_dir} "
        f"(1 index, {len(lesson_records)} lessons, {len(ref_records)} reference sheets)."
    )
    if errors:
        for err in errors:
            print(f"[ERROR] {err}", file=sys.stderr)
        return 1
    if check:
        print(
            "✓ All Markdown frontmatter, links, and equal-word-count quiz checks passed."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the Eurorack SKiDL tutorial HTML site."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=TUTORIAL_DIR,
        help="Destination directory for built HTML files (default: in-place in tutorial/).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify internal links and quiz option word-count parity.",
    )
    args = parser.parse_args()
    return build_site(args.out_dir.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
