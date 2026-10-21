---
name: skidl
description: >-
  Design electronic circuits in Python and generate KiCad netlists, PCBs,
  schematics, SVGs, and BOMs using SKiDL. Use this skill whenever a developer
  asks to write, modify, debug, or understand SKiDL circuit scripts, search
  KiCad symbol or footprint libraries from Python, run Electrical Rules
  Checking (ERC), create hierarchical subcircuits, or export circuits to KiCad.
---

# SKiDL Circuit & KiCad PCB Design

SKiDL is a Python library for describing electronic circuits as code and outputting netlists, PCB files, and schematics for KiCad (versions 5 through 10, defaulting to `KICAD10`).

## 1. Environment & Tool Configuration

* **Virtual Environment Setup (`uv`)**: `skidl` depends on `inspice` -> `h5py`. Avoid unreleased/bleeding-edge Python versions (such as Python 3.15) that lack prebuilt `h5py` binary wheels and fail compiling `libhdf5` from source. Target Python 3.12–3.14 and pass `--clear` so `uv venv` never blocks on an interactive prompt:
  ```bash
  uv venv --clear --python 3.14 .venv
  uv pip install skidl
  ```
* **Pre-Import Environment Variables (Sandbox & macOS Paths)**: Importing `skidl` immediately initializes `SkidlConfig` and `matplotlib`, which attempt to create `~/Library/Application Support/skidl` and `~/.matplotlib`. In restricted sandboxes or macOS environments without shell-exported KiCad variables, configure these **before** importing `skidl`:
  ```python
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
  ```
* **Default Tool**: `KICAD` aliases `KICAD10`. Switch versions at the top of a script if targeting an older KiCad installation:
  ```python
  from skidl import KICAD9, set_default_tool

  set_default_tool(KICAD9)  # Options: KICAD5, KICAD6, KICAD7, KICAD8, KICAD9, KICAD10
  ```
* **Symbol Libraries**: Controlled by `KICAD_SYMBOL_DIR` or versioned `KICAD<N>_SYMBOL_DIR` (e.g., `KICAD10_SYMBOL_DIR`). You can also append paths in code:
  ```python
  lib_search_paths[KICAD].append("/path/to/custom/symbols")
  ```
* **Footprint Libraries**: Resolved automatically from KiCad's global `fp-lib-table` or customized via `footprint_search_paths[KICAD]`.

## 2. Discovering Parts & Footprints

Before instantiating parts, query local KiCad libraries using Python one-liners to verify exact library names, symbol names, pin names/numbers, and footprint strings:

```python
from skidl import *

# Search symbols by keywords/regex (uses a cached SQLite DB)
search("linear regulator 3.3V")

# Inspect exact pin numbers, names, and electrical types of a symbol
show("Regulator_Linear", "AMS1117-3.3")

# Search footprints across .pretty libraries
search_footprints("SOT-223")
```

## 3. Instantiating Parts

Every physical component destined for a PCB **must** have a `footprint` attribute formatted as `"<Library>:<FootprintName>"`:

```python
from skidl import *

# Single part instance (automatically added to the circuit)
u1 = Part(
    "Regulator_Linear",
    "AMS1117-3.3",
    footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    tag="u1_reg",  # Optional stable tag for deterministic KiCad UUIDs
)

# Template pattern for instantiating multiple copies
r_t = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0805_2012Metric")
c_t = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0805_2012Metric")

r1, r2 = r_t(2, value="10K")  # Two 10K resistors
c_in, c_out = c_t(values=["10uF", "22uF"])
```

* **Custom Fields & Properties**: Pass arbitrary keyword arguments (e.g., `mpn="...", dnp=True, exclude_from_bom=True`) to `Part()` or assign attributes directly (`r1.value = "4.7K"`). They export as component fields/properties in the KiCad netlist.
* **Custom On-the-Fly Parts**: See [Advanced Patterns](./references/advanced_patterns.md) for creating schematic-less parts with `SkidlPart` and `Pin`.

## 4. Selecting Pins & Wiring Nets

### Pin Indexing (`part[...]`)
* **By number or name**: `u1[1]`, `u1["VI"]`, or attribute access `u1.VI` / `u1.p1`.
* **Multiple pins**: Space/comma-separated string `u1["VI VO"]`, tuple `u1[1, 2]`, or slice `mcu[1:8]`.
* **Disambiguating names vs. numbers**: Use `u1.p[1]` (numbers only) or `u1.n["1"]` (names only).
* **Regex matching**: Enable `u1.match_pin_regex = True` or wrap with `Rgx`: `mcu[Rgx("PA[0-7]")]`.

### Making Connections
Never use `=` to assign to pins, nets, or buses; **always use `+=`** or network operators (`&` and `|`):

```python
vin, vout, gnd = Net("VIN"), Net("3V3"), Net("GND")

# 1. Explicit net attachment (+=)
vin += u1["VI"]
vout += u1["VO"]
gnd += u1["GND"]

# 2. Algebraic series (&) and parallel (|) networks (for 2-pin parts or 2-port pin slices)
vin & c_in & gnd
vout & (c_out | (r1 & led)) & gnd

# Multi-pin parts in a series network: specify [in_pin, out_pin]
vin & u1["VI VO"] & vout

# Branching a network with tee()
vin & r1 & tee(c_in & gnd) & r2 & vout
```

* **Unconnected Pins (`NC`)**: Attach intentionally unused pins to the built-in `NC` net to suppress ERC warnings. Inside functions or `@subcircuit` blocks, always place the pin on the left (`u1["NC"] += NC`) rather than `NC += u1["NC"]`—the latter causes Python to treat `NC` as an unassigned local variable and raises `UnboundLocalError`.
* **Buses**: Create multi-bit signals with `bus = Bus("DATA", 8)` and connect slices with `bus[0:7] += mcu["PA[0:7]"]`.

## 5. Electrical Rules Checking (ERC)

Always run `ERC()` before generating outputs:

```python
# Mark external power rails as driven so ERC doesn't flag "No drivers for net"
vin.drive = POWER
gnd.drive = POWER

# Disable ERC on specific nets/pins/parts if needed
test_point_net.do_erc = False

# Custom assertions evaluated during ERC()
erc_assert("len(vout) >= 2", "3V3 output rail has no load!")

ERC()
```

## 6. Exporting to KiCad

Choose the output method that matches the user's workflow:

```python
# 1. KiCad Netlist (.net) — Primary workflow for KiCad PCB Editor
# In KiCad PCB Editor (pcbnew): File -> Import -> Netlist... -> Update PCB
generate_netlist(file_="my_board.net")

# 2. Direct KiCad PCB (.kicad_pcb)
# Requires `kinet2pcb` and KiCad's `pcbnew` Python module in the active Python environment
generate_pcb(fp_libs=["/path/to/footprints.pretty"])

# 3. Hyperlinked SVG (.svg) or Placed-and-routed KiCad Schematic (.kicad_sch)
# Prefer generate_svg() for visual diagrams; generate_schematic() uses schematizer's
# global router, which can raise skidl.errors.RoutingFailure on dense multi-pin connectors.
generate_svg(filepath="output_dir", top_name="my_board", flatness=0.0)
generate_schematic(filepath="output_dir", top_name="my_board")

# 4. XML BOM (.xml) or Graphviz DOT (.dot)
generate_xml(file_="my_board_bom.xml")
generate_dot(file_="circuit.dot")
```

## 7. Code Quality & Linting (`ruff`)

* **Explicit Imports**: In saved circuit scripts, prefer explicit imports (`from skidl import ERC, NC, POWER, TEMPLATE, Net, NetClass, Part, generate_netlist, generate_svg, generate_xml, subcircuit`) over `from skidl import *`. Add `# noqa: E402` if `os.environ` setup precedes the import.
* **Executable Shebangs**: If including `#!/usr/bin/env python3`, run `chmod +x <script>.py` so `ruff` (`EXE001`) passes.
* **Auto-Generated Backup Library (`*_sklib.py`)**: Running a SKiDL script emits a `<script>_sklib.py` backup symbol library in the working directory. Always run `ruff check --fix . && ruff format .` **after** executing the circuit script so both your script and `*_sklib.py` pass linting and formatting.

## 8. Hierarchy, Design Classes & SPICE

For hierarchical subcircuits (`@subcircuit`, `SubCircuit`, `Interface`), PCB routing classes (`NetClass`, `PartClass`), missing footprint handlers, and converting existing KiCad netlists to SKiDL (`netlist_to_skidl`), read [Advanced Patterns](./references/advanced_patterns.md).
