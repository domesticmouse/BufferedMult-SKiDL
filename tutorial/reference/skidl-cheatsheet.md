---
title: "SKiDL API & Pin Indexing Cheat Sheet"
page_title: "SKiDL API & Pin Indexing Cheat Sheet | Eurorack SKiDL Tutorial"
nav_id: "skidl-cheatsheet"
nav_label: "SKiDL Ref"
kicker: "Reference Sheet · Printable"
lead: "Compressed syntax reference for writing, wiring, checking, and linting SKiDL circuit scripts targeting KiCad 10."
card:
  title: "SKiDL API & Pin Indexing Cheat Sheet"
  summary: "Pre-import environment setup, `dest=TEMPLATE`, `part.fields`, `u.p[n]` vs `u[\"V+\"]`, network operators, `@subcircuit`, `NetClass`, and `ERC()`."
---

## 1. Mandatory Pre-Import Environment Header

Importing `skidl` immediately initialises `SkidlConfig` and `matplotlib`. Always configure writable cache directories and KiCad 10 symbol/footprint paths **before** the `from skidl import ...` statement, and tag the import with `# noqa: E402` so `ruff` allows top-of-file environment setup:

```python title="Pre-import header (buffered_multiple.py)"
import builtins
import os

os.environ.setdefault("XDG_DATA_HOME", "/tmp/xdg_data")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_config")
if os.path.isdir("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"):
    os.environ.setdefault(
        "KICAD10_SYMBOL_DIR",
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
    )
    os.environ.setdefault(
        "KICAD_SYMBOL_DIR",
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
    )
if os.path.isdir("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"):
    os.environ.setdefault(
        "KICAD10_FOOTPRINT_DIR",
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
    )

from skidl import (  # noqa: E402
    ERC,
    POWER,
    TEMPLATE,
    Net,
    NetClass,
    Part,
    generate_netlist,
    generate_xml,
    subcircuit,
)
```

## 2. Instantiating Parts, Templates & `part.fields`

Table: Part instantiation and BOM metadata patterns

| Pattern | Python Syntax | Why It Matters |
| --- | --- | --- |
| Single concrete part | `u = Part("Amplifier_Operational", "TL074", value="TL074H", footprint=FP_OPAMP_SOIC14, tag="u_ch1")` | Immediately adds `U1` to `builtins.default_circuit` with a deterministic hierarchical `tag`. |
| Reusable template part | `r_t = Part("Device", "R", dest=TEMPLATE, footprint=FP_R_0603)` | Does **not** enter the netlist until called: `r1 = r_t(value="100K", tag="r_pd_ch1")` or `d_pos, d_neg = d_t(2, tag="d_prot")`. |
| Custom BOM fields | `r_t.fields["LCSC"] = "C25803"`<br>`r_t.fields["JLCPCB_Class"] = "Basic"` | `Part.__setattr__` ignores unknown attribute names during XML/netlist export unless they live in `part.fields`. Clones inherit a copy of `fields`. |

## 3. Pin Indexing & Disambiguation

Table: Selecting pins on KiCad 10 symbols in SKiDL

| Syntax | Meaning | Example in `buffered_multiple.py` |
| --- | --- | --- |
| `part[1, 2]` | Match multiple pins by number or name | `vee_raw += j_pwr[1, 2]` and `gnd += j_pwr[3, 4, 5, 6, 7, 8]` |
| `part["K"]`, `part["T"]` | Match pin by symbol pin name or string pin ID | `vcc_raw += d_pos["A"]`, `in_jack += j_in["T"]`, `norm_in += j_in["TN"]` |
| `part.p[num]` | Strictly index by **pin number only** (essential when multiple units share names like `"+"` and `"-"`) | `in_sig += u.p[3]`, `buffered_tap_out += u.p[1], u.p[2]` on `TL074` |
| `part.n["name"]` | Strictly index by **pin name only** | `u.n["V+"]` (or `u["V+"]` when unambiguous) |

## 4. Wiring Nets, `@subcircuit`, `NetClass`, `builtins.NC` & Post-Run `ruff`

- **Never use `=` to wire nets or pins** — always use `+=` (`vcc += u["V+"]`) or 2-pin series/parallel network operators (`in_jack & r_in & in_sig`, `in_jack & (d_tvs | r_pd) & gnd`).
- **Hierarchical subcircuits (`@subcircuit`)**: Decorate reusable circuit functions with `@subcircuit` and pass a deterministic `tag="..."` on each call (e.g., `buffered_channel_1to3(..., ch_num=1, tag="ch1")`) so KiCad 10 component `tstamps` stay stable across re-runs.
- **PCB routing rules (`NetClass`)**: Assign trace width and clearance metadata directly to nets via `rail.netclasses = NetClass("Power", priority=1, trace_width=0.5, clearance=0.25)`.
- **Unused pins (`builtins.NC`)**: `NC` and `default_circuit` are injected into Python's `builtins` module at import time and are not in `skidl.__all__`. Wire unconnected pins with the pin on the left: `j_out["TN"] += builtins.NC`.
- **External power rails**: Set `vcc.drive = POWER`, `vee.drive = POWER`, and `gnd.drive = POWER` so `ERC()` verifies that all `PWRIN` pins on op-amps are driven.
- **Mandatory post-run linting**: Running a SKiDL script generates or overwrites `<script>_sklib.py` with unformatted code. Always run `ruff check --fix` and `ruff format` **after** executing the script.
