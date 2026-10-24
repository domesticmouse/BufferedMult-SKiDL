# Mission: Designing & Manufacturing Eurorack Modules in Python with SKiDL

## Why
Design and manufacture custom Eurorack synthesizer modules and analog audio circuits in Python using SKiDL, KiCad 10, and JLCPCB PCBA—replacing error-prone manual schematic clicking with repeatable, version-controlled, linted Python code and automated BOM generation.

## Success looks like
- Programmatically discover KiCad 10 symbols, pinouts, footprints, and live in-stock JLCPCB/LCSC part numbers (`Basic` vs. `Extended`) from Python and CLI scripts without manual library browsing.
- Construct and verify the complete 3-channel Eurorack Buffered Multiple (`buffered_multiple.py`) from scratch using reusable `@subcircuit` blocks, `TEMPLATE` parts, `part.fields` metadata, and cascaded switched-jack normalling (`1:3` → `1:6` → `1:9`).
- Pass Electrical Rules Checking (`ERC()`) with `0` errors and `0` warnings and pass `ruff` lint/format checks on both circuit scripts and generated `*_sklib.py` libraries.
- Export fabrication-ready KiCad 10 netlists (`.net` with `Power` and `Signal` `NetClass` rules), XML BOMs (`.xml`), and SMT-filtered JLCPCB PCBA BOMs (`.csv`).
- Bridge the exported `.net` netlist into a 4HP (`20.0 × 108.0 mm`) single-sided `B.Cu` SMT / `F.Cu` THT KiCad 10 PCB layout (`0005`), generate a mated Doepfer A-100 3U × 4HP (`20.0 × 128.5 mm`) front panel PCB accounting for the `+6.48 mm` `WQP-PJ398SM` bushing offset (`0006`), and run a programmatic 5-stage pre-fabrication design review and DRC audit (`0007`).

## Constraints
- Target the local macOS KiCad 10 installation (`/Applications/KiCad/KiCad.app/Contents/SharedSupport/`) and Python 3.14 via `uv` (`.venv/bin/python`).
- Prioritize Python/SKiDL idioms, programmatic part discovery, and KiCad/JLCPCB dataflow over elementary analog theory (since the learner is already familiar with op-amps, decoupling, `±12V` rails, and switched jacks).
- Keep lessons focused, interactive, and backed by runnable, lint-clean scripts in `tutorial/apps/`.

## Out of scope
- Introductory analog electronics primers (Ohm's law, how an op-amp voltage follower works from first principles).
- Digital DSP firmware or microcontroller programming.
