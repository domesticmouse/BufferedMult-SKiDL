---
title: "Building the Eurorack Buffered Multiple in Python with SKiDL"
page_title: "Eurorack Buffered Multiple — Interactive SKiDL & KiCad 10 Tutorial"
nav_id: "index"
kicker: "Interactive Hardware-as-Code Course"
lead: "Start from an empty Python file and progressively grow a complete, production-ready 3-channel Eurorack Buffered Multiple (`buffered_multiple.py`), 4HP PCB layout plan, mated 3U front panel generator, and automated pre-fabrication design audit—with every line of Python code, linter check, and verification output shown right on the page."
---

```mermaid caption="How the course progresses from a 0-line script in Lesson 0001 to a complete 3-channel netlist, 4HP PCB & front panel generator, and automated pre-fab design audit in Lesson 0008."
flowchart LR
  L1["0001: Empty File →<br/>Pre-Import Header & ERC"] --> L2["0002: Part Discovery →<br/>+ FP_* & LCSC_* Constants"]
  L2 --> L3["0003: Grow Script →<br/>+ eurorack_power()"]
  L3 --> L4["0004: Grow Script →<br/>+ buffered_channel_1to3()"]
  L4 --> L5["0005: Complete Circuit →<br/>1:3/1:6/1:9 & JLCPCB BOM"]
  L5 --> L6["0006: 4HP PCB Layout →<br/>tstamps & B.Cu/F.Cu Split"]
  L6 --> L7["0007: 4HP Front Panel →<br/>+6.48 mm Bushing Offset"]
  L7 --> L8["0008: Pre-Fab Audit →<br/>5/5 Automated Checks"]
```

## Course Lessons (Start from Nothing & Grow to Production Hardware)

{{widget:lesson-cards}}

## Reference Sheets (Printable)

{{widget:reference-cards}}
