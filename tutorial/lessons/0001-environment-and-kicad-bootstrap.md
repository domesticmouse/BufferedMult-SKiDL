---
title: "From an Empty File to KiCad 10 Bootstrap & First `ERC()`"
page_title: "Lesson 0001: From Empty File to KiCad 10 Bootstrap & First ERC() | Eurorack SKiDL Tutorial"
nav_id: "0001"
kicker: "Lesson 0001 · Stage 1 (0 → 72 Lines)"
lead: "Start from a completely blank Python file, set up a deterministic Python 3.14 + SKiDL environment with `uv`, write the pre-import KiCad 10 library configuration header that every script in this course builds on, and run your first zero-warning `ERC()` check."
badges:
  - text: "Script Growth: 0 → 72 Lines"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0001 · Stage 1"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "From Empty File to KiCad 10 Bootstrap & First `ERC()`"
  summary: "Start with a blank script, configure Python 3.14 with `uv`, write the pre-import KiCad 10 environment header, and run a 0-warning `ERC()` smoke check."
  meta:
    - "**Code Grown**: `0 → 72 lines` (Pre-import `os.environ`, `TEMPLATE`, `POWER`, `ERC()`)"
    - "**Tooling Skill**: `uv venv --python 3.14`, `# noqa: E402`, post-run `ruff`"
  app_dir: "./apps/0001-environment-and-kicad-bootstrap"
pager_prev:
  href: "../index.html"
  label: "← Course Home"
  title: "Course Index & Roadmap"
pager_next:
  href: "0002-programmatic-component-discovery.html"
  label: "Next Lesson →"
  title: "0002: Programmatic Part Discovery & FP_*/LCSC_* Constants"
---

## Starting from Nothing: How Our Python Script Will Grow

The joy of exploring synthesisers and Eurorack hardware as a software engineer is that you get to build physical little noise makers you can patch with real cables. The pain is traditional GUI schematic capture—hunting through nested menus, dragging wires around a canvas, and hoping a visual inspection catches a floating pin before you order boards.

But, what if our circuit was just Python code? Thanks to Dave Vandenbout's ([`devbisme`](https://github.com/devbisme/skidl)) brilliant [SKiDL](https://devbisme.github.io/skidl/) library, we can treat hardware design the exact same way we treat software: version-controlled in Git, checked with a linter (`ruff`), and verified programmatically with Electrical Rules Checking (`ERC()`).

So, you do not need any existing Python file open to follow this course. Across Lessons `0001` through `0005`, we will write the entire 3-channel Eurorack Buffered Multiple circuit script right here on the page—starting from an empty file today and adding one verified layer per lesson:

```mermaid caption="We write the pre-import header once in Stage 1 and carry it forward into every subsequent stage."
flowchart LR
  S1["Stage 1 (This Lesson)<br/>Pre-import os.environ header<br/>+ First ERC() smoke check"] --> S2["Stage 2 (Lesson 0002)<br/>+ Discovered FP_* footprints<br/>& LCSC_* catalog constants"]
  S2 --> S3["Stage 3 (Lesson 0003)<br/>+ @subcircuit eurorack_power()<br/>(10-pin IDC, 1N5819WS, 10uF)"]
  S3 --> S4["Stage 4 (Lesson 0004)<br/>+ @subcircuit buffered_channel_1to3()<br/>(TL074H, TVS, 3× 470R outputs)"]
  S4 --> S5["Stage 5 (Lesson 0005)<br/>+ 1:3→1:6→1:9 Cascade,<br/>NetClasses & JLCPCB BOM CSV"]
```

## Step 1. Create the `uv` Virtual Environment (Python 3.14)

First up, environment setup. Turns out, SKiDL depends on `inspice` → `h5py`. If you grab an unreleased bleeding-edge Python build, `pip` often won't find prebuilt binary wheels for `h5py` and will grind to a halt trying to compile `libhdf5` from C source. Targeting **Python 3.14** with `uv venv --clear` guarantees fast, prebuilt binary wheel installation in seconds:

```bash title="Terminal · Create .venv and install SKiDL"
uv venv --clear --python 3.14 .venv
uv pip install skidl
```

## Step 2. Write the Pre-Import Environment Header (Lines 1–31)

Now, let's begin our Python script from line 1. If you're anything like me, your first instinct is to type `from skidl import ...` on the very first line and start instantiating parts.

However, if you try that on macOS with KiCad 10 installed, SKiDL immediately complains that it can't find any symbol libraries. The reason this happens is interesting: the moment Python imports `skidl`, SKiDL immediately initialises its global `SkidlConfig` singleton and pulls in `matplotlib`. During that import, two things happen right under our feet:

1. **Writable cache directories**: SKiDL and Matplotlib attempt to create config and cache folders in your home directory. Setting `XDG_DATA_HOME` and `MPLCONFIGDIR` to `/tmp/...` before importing `skidl` prevents permission errors in sandboxed shells or CI runners.
2. **KiCad 10 symbol & footprint discovery**: In SKiDL, the default tool `KICAD` aliases `KICAD10`. On macOS, KiCad 10 bundles its symbols and footprints inside `/Applications/KiCad/KiCad.app/Contents/SharedSupport/`, but does not export `KICAD10_SYMBOL_DIR` to your shell automatically. Setting `KICAD10_SYMBOL_DIR`, `KICAD_SYMBOL_DIR`, and `KICAD10_FOOTPRINT_DIR` in `os.environ` **before** `from skidl import ...` ensures SKiDL finds every KiCad 10 library on the first try.

So, here is the exact 31-line foundation header that starts our script:

```python title="New Code Added · Pre-import KiCad 10 environment header (Lines 1–31)"
#!/usr/bin/env python3
import os
from pathlib import Path
import sys

# Keep generated .erc, .log, and _sklib.py artifacts inside this script's directory
os.chdir(Path(__file__).resolve().parent)

# 1. Configure writable cache directories and KiCad 10 library paths BEFORE importing skidl
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

from skidl import ERC, KICAD, POWER, TEMPLATE, Net, Part, get_default_tool  # noqa: E402
```

:::callout-warn Why `# noqa: E402` Is Placed on the `from skidl import ...` Line
I'm a big fan of strict linters because they keep codebases evergreen and let us focus on semantics instead of formatting. Python's linter (`ruff` rule `E402`) normally flags module imports that appear below executable statements like `os.environ.setdefault(...)`. Adding `# noqa: E402` on the `from skidl import ...` line tells `ruff` that configuring `os.environ` before importing `skidl` is completely deliberate.
:::

## Step 3. Add a Minimal Circuit & `ERC()` Smoke Check (Lines 34–76)

Next, let's add a function `run_bootstrap_check()` to test three core SKiDL building blocks we will use throughout the Buffered Multiple:

- **Template Part (`dest=TEMPLATE`)**: Passing `dest=TEMPLATE` to `Part("Device", "R", dest=TEMPLATE, ...)` creates a reusable blueprint that does *not* enter the circuit until we call it: `r_top, r_bot = r_t(2, tag="r_boot")` instantiates two concrete `100K` resistors (`R1` and `R2`).
- **Power Drive Flag (`net.drive = POWER`)**: Marking `vcc.drive = POWER` and `gnd.drive = POWER` tells SKiDL's Electrical Rules Checker (`ERC()`) that `+12V` and `GND` are energised by an external power supply.
- **Series Network Operator (`&`)**: For two-pin passives, `vcc & c_dec & gnd` wires `C1` across `+12V` and `GND`, while `vcc & r_top & mid & r_bot & gnd` wires `R1` and `R2` as a voltage divider so every net has at least 2 connected pins.

```python title="New Code Added · run_bootstrap_check() (Lines 34–76)"
def run_bootstrap_check():
    """Verify Python, SKiDL default tool, KiCad 10 paths, and a zero-warning ERC."""
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version.split()[0]}")
    print(f"SKiDL default tool: {get_default_tool()} (aliases {KICAD})")
    print(f"KICAD10_SYMBOL_DIR: {os.environ.get('KICAD10_SYMBOL_DIR', 'NOT SET')}")

    # Instantiate two 100K 0603 resistors and a 100nF bypass capacitor from templates
    r_t = Part(
        "Device",
        "R",
        dest=TEMPLATE,
        value="100K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    c_t = Part(
        "Device",
        "C",
        dest=TEMPLATE,
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r_top, r_bot = r_t(2, tag="r_boot")
    c_dec = c_t(tag="c_boot")

    vcc = Net("+12V")
    mid = Net("DIV_MID")
    gnd = Net("GND")

    # Mark external rails as POWER-driven so ERC knows they have an active source
    vcc.drive = POWER
    gnd.drive = POWER

    # Parallel bypass cap + series voltage divider (every net has >= 2 pins)
    vcc & c_dec & gnd
    vcc & r_top & mid & r_bot & gnd

    ERC()
    print(f"Verified parts    : {[p.ref for p in (r_top, r_bot, c_dec)]}")


if __name__ == "__main__":
    run_bootstrap_check()
```

## Step 4. Complete Stage 1 Script & Terminal Verification

Putting Steps 2 and 3 together gives us the complete, self-contained 72-line Python script for Lesson 0001 (saved in the workspace at `tutorial/apps/0001-environment-and-kicad-bootstrap/bootstrap_check.py`):

```python title="Complete Stage 1 Script · tutorial/apps/0001-environment-and-kicad-bootstrap/bootstrap_check.py"
#!/usr/bin/env python3
"""
Lesson 0001: Environment, `uv` & KiCad 10 Bootstrap Smoke Check.

Verifies that:
1. Pre-import environment variables (`XDG_DATA_HOME`, `MPLCONFIGDIR`, `KICAD10_SYMBOL_DIR`,
   `KICAD_SYMBOL_DIR`, `KICAD10_FOOTPRINT_DIR`) are configured before importing `skidl`.
2. SKiDL's default tool resolves to `KICAD10` (`kicad10`) and can load KiCad 10 symbols.
3. A minimal decoupling + voltage-divider test circuit passes `ERC()` with 0 errors and 0 warnings.
"""

import os
from pathlib import Path
import sys

# Keep generated .erc, .log, and _sklib.py artifacts inside this lesson's app directory
os.chdir(Path(__file__).resolve().parent)

# 1. Configure writable cache directories and KiCad 10 library paths BEFORE importing skidl
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

from skidl import ERC, KICAD, POWER, TEMPLATE, Net, Part, get_default_tool  # noqa: E402


def run_bootstrap_check():
    """Verify Python, SKiDL default tool, KiCad 10 paths, and a zero-warning ERC."""
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version.split()[0]}")
    print(f"SKiDL default tool: {get_default_tool()} (aliases {KICAD})")
    print(f"KICAD10_SYMBOL_DIR: {os.environ.get('KICAD10_SYMBOL_DIR', 'NOT SET')}")

    # Instantiate two 100K 0603 resistors and a 100nF bypass capacitor from templates
    r_t = Part(
        "Device",
        "R",
        dest=TEMPLATE,
        value="100K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    c_t = Part(
        "Device",
        "C",
        dest=TEMPLATE,
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r_top, r_bot = r_t(2, tag="r_boot")
    c_dec = c_t(tag="c_boot")

    vcc = Net("+12V")
    mid = Net("DIV_MID")
    gnd = Net("GND")

    # Mark external rails as POWER-driven so ERC knows they have an active source
    vcc.drive = POWER
    gnd.drive = POWER

    # Parallel bypass cap + series voltage divider (every net has >= 2 pins)
    vcc & c_dec & gnd
    vcc & r_top & mid & r_bot & gnd

    ERC()
    print(f"Verified parts    : {[p.ref for p in (r_top, r_bot, c_dec)]}")


if __name__ == "__main__":
    run_bootstrap_check()
```

### Run and Lint from Your Terminal

Now, here is a quirky SKiDL detail that caught me off guard the first time I wired up a CI linter. Whenever a SKiDL script exports a netlist or caches symbols, it writes a **Backup Symbol Library (`<script>_sklib.py`)** right next to your script containing raw, auto-generated, decidedly unformatted Python code. So, to keep your working tree clean and `ruff` happy, always run `ruff check --fix` and `ruff format` **after** executing a SKiDL script:

```bash title="Terminal · Execute bootstrap_check.py and lint with ruff"
.venv/bin/python tutorial/apps/0001-environment-and-kicad-bootstrap/bootstrap_check.py
ruff check --fix tutorial/apps/0001-environment-and-kicad-bootstrap/*.py
ruff format tutorial/apps/0001-environment-and-kicad-bootstrap/*.py
```

```bash title="Verified Output · bootstrap_check.py" copy=false
Python executable : /Users/brett/Documents/GitHub/BufferedMult-SKiDL/.venv/bin/python
Python version    : 3.14.9
SKiDL default tool: kicad10 (aliases kicad10)
KICAD10_SYMBOL_DIR: /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols
ERC INFO: No errors or warnings found while running ERC.

Verified parts    : ['R1', 'R2', 'C1']
```

:::exercise id="ex-0001-title" title="Retrieval Practice: Complete the Bootstrap & `ERC()` Snippet"
Fill in the four blanks below from memory to configure KiCad 10's symbol variable, suppress Ruff's top-of-file import warning, create a reusable template part, and mark the `+12V` rail as driven before running `ERC()`:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
import os

os.environ.setdefault(
    "{{blank:KICAD10_SYMBOL_DIR|Versioned KiCad 10 symbol env var: KICAD10_SYMBOL_DIR|KiCad 10 symbol directory variable|19}}",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
)

from skidl import ERC, POWER, TEMPLATE, Net, Part  # noqa: {{blank:E402|4-character Ruff code for module import below statements: E402|Ruff rule code for module import not at top of file|6}}

r_t = Part("Device", "R", dest={{blank:TEMPLATE|SKiDL constant that prevents immediate netlist insertion: TEMPLATE|SKiDL constant for a blueprint template part|10}}, value="100K")
vcc = Net("+12V")
vcc.drive = {{blank:POWER|SKiDL drive constant for power rails: POWER|SKiDL drive constant for energised rails|7}}
```
:::

:::quiz id="quiz-0001-title" title="Knowledge Check"
- question: "1. Why must we configure `KICAD10_SYMBOL_DIR` and `XDG_DATA_HOME` in `os.environ` before `from skidl import ...`?"
  options:
    - letter: A
      text: "Python clears all exported shell variables whenever external circuit packages first load."
      correct: false
      explain: "Python does not clear shell variables on import; rather, SKiDL reads os.environ immediately when its module loads."
    - letter: B
      text: "Importing skidl immediately configures library paths and cache folders during module import."
      correct: true
      explain: "Importing skidl immediately initialises SkidlConfig and matplotlib using the environment variables active at import time."
    - letter: C
      text: "KiCad ten refuses netlist files unless environment paths appear inside comment headers."
      correct: false
      explain: "KiCad .net files do not require environment variable paths inside comment headers."
    - letter: D
      text: "Ruff automatically removes every import line placed above system environment setup calls."
      correct: false
      explain: "Ruff never deletes import statements unless unused (F401); E402 only warns when imports follow statements."
- question: "2. Why must you run `ruff check --fix` and `ruff format` **after** executing a SKiDL circuit script?"
  options:
    - letter: A
      text: "Ruff translates generated electrical rules logs into valid KiCad layout footprints."
      correct: false
      explain: "Ruff is a Python linter and formatter; it does not read .erc logs or generate KiCad footprints."
    - letter: B
      text: "Executing Python scripts strips executable permission bits from local source files."
      correct: false
      explain: "Running a script with .venv/bin/python never modifies the file's chmod executable bit."
    - letter: C
      text: "SKiDL disables automatic Electrical Rules Checking inside unformatted Python circuit files."
      correct: false
      explain: "SKiDL's ERC() inspects in-memory Net and Pin objects regardless of source formatting."
    - letter: D
      text: "Running SKiDL overwrites the generated backup library file with unformatted Python."
      correct: true
      explain: "Running a SKiDL script writes or overwrites <script>_sklib.py with unformatted auto-generated Python code."
:::

:::callout-success Primary Sources & Follow-Up Questions
**Primary Sources**: [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md) · [SKiDL & Eurorack Hardware Glossary](../reference/GLOSSARY.md) · [Official SKiDL Documentation](https://devbisme.github.io/skidl/).<br>**Ask the Agent**: Have a question about how `KICAD10_SYMBOL_DIR` interacts with custom project libraries, or ready to move to **Lesson 0002** where we discover every symbol, pinout, footprint, and LCSC part number from Python? Ask right in chat!
:::
