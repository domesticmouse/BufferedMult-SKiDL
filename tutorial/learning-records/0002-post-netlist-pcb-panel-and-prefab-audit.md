# Extending the Course to 4HP PCB Layout, Front Panel Generation & Pre-Fab Audits

After completing the core 5-lesson progression (`0000`–`0004`) that grows `buffered_multiple.py` from an empty file, we expanded the course with three post-netlist hardware-as-code lessons (`0005`–`0007`) and switched the landing page `.lesson-grid` to a 2-wide card stack (forming 4 rows of 2 lesson cards and 2 rows of 2 printable reference cards).

## Evidence
- Requested directly by the user when reviewing `tutorial/index.html`: build all three post-netlist lessons (`0005` PCB layout & assembly split, `0006` automated 4HP front panel generator, `0007` programmatic pre-fab design review & DRC audit) and format `.lesson-grid` as a 2-column stack.

## Implications
- Every stage of the hardware lifecycle—from `uv` bootstrap (`0000`) and live LCSC discovery (`0001`) through subcircuit authoring (`0002`–`0004`), deterministic `tstamps` PCB layout (`0005`), `+6.48 mm` Thonkiconn bushing offset front-panel generation (`0006`), and pre-fabrication verification (`0007`)—is now backed by a self-contained HTML lesson in `tutorial/lessons/` and a `ruff`-clean runnable Python script in `tutorial/apps/`.
