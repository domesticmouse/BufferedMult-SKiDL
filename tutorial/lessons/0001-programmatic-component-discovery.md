---
title: "Programmatic Part Discovery & Adding `FP_*` / `LCSC_*` Constants"
page_title: "Lesson 0001: Programmatic Part Discovery & Growing Stage 1 Constants | Eurorack SKiDL Tutorial"
nav_id: "0001"
kicker: "Lesson 0001 · Stage 1 (Discovery & Growing the Constants Block)"
lead: "Write a standalone Python discovery script to inspect exact KiCad 10 symbol pinouts, verify `.pretty` footprint files on disk, query live JLCPCB/LCSC stock, and grow our main circuit script with verified `FP_*` and `LCSC_*` constants."
badges:
  - text: "Script Growth: Header → + 14 Footprint & LCSC Constants"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0001 · Stage 1"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "Programmatic Part Discovery & Adding `FP_*` / `LCSC_*` Constants"
  summary: "Write a Python discovery script to inspect KiCad 10 pinouts and footprints, query live JLCPCB stock, and grow our circuit script with verified `FP_*` and `LCSC_*` constants."
  meta:
    - "**Code Grown**: Full `discover_parts.py` + Stage 1 `FP_*` & `LCSC_*` constants"
    - "**Tooling Skill**: `part.pins`, `u.p[n]` vs `u[\"V+\"]`, `part.fields[\"LCSC\"]`"
  app_dir: "./apps/0001-programmatic-component-discovery"
pager_prev:
  href: "0000-environment-and-kicad-bootstrap.html"
  label: "← Previous Lesson"
  title: "0000: From Empty File to KiCad 10 Bootstrap"
pager_next:
  href: "0002-eurorack-power-subcircuit.html"
  label: "Next Lesson →"
  title: "0002: Growing the Script — Adding eurorack_power()"
---

## How Do We Know Which Symbol, Pin Number, Footprint, and LCSC Part to Write?

In traditional GUI schematic capture, you hunt through nested menus to find a symbol, drop it on a sheet, and cross your fingers that its pin numbers match your footprint when you finally open the PCB layout editor.

But, when we're designing circuits from scratch in Python with SKiDL, we don't have to guess symbol names or pin numbers. Instead, we can treat KiCad 10's symbol libraries and the JLCPCB parts catalogue like any other API—write a small Python inspection script to query the exact pinouts and verify that the `.kicad_mod` footprint files actually exist on disk, then copy those verified constants straight into our growing circuit script.

```mermaid caption="The four-step discovery pipeline that feeds verified constants into Stage 1 of our growing circuit script."
flowchart TD
  Q1["1. Symbol Search<br/>search('TL074') / search('AudioJack2_SwitchT')"] --> Q2["2. Pinout Inspection<br/>Part(lib, sym, dest=TEMPLATE).pins"]
  Q2 --> Q3["3. Footprint Verification<br/>Check <Lib>.pretty/<Footprint>.kicad_mod"]
  Q3 --> Q4["4. Live JLCPCB Catalog Query<br/>jlcpcb_search.py --in-stock-only"]
  Q4 --> Q5["5. Grow buffered_multiple.py<br/>Add FP_* & LCSC_* constants + part.fields"]
```

## Step 1. Write the Symbol, Pinout & Footprint Discovery Script

Starting with the exact same 34-line pre-import environment header we wrote in [Lesson 0000](0000-environment-and-kicad-bootstrap.md), we can load any KiCad 10 symbol as a **Template Part (`dest=TEMPLATE`)** and iterate over `part_t.pins` to print every pin's exact `.num`, `.name`, and electrical function (`PASSIVE`, `INPUT`, `OUTPUT`, `PWRIN`).

Here is the complete, runnable 131-line discovery script (`tutorial/apps/0001-programmatic-component-discovery/discover_parts.py`):

```python title="Complete Discovery Script · tutorial/apps/0001-programmatic-component-discovery/discover_parts.py"
#!/usr/bin/env python3
"""
Lesson 0001: Programmatic Component, Pinout, Footprint & JLCPCB Discovery.

Demonstrates how to inspect KiCad 10 symbols, pin numbers/names/types, `.pretty`
footprints, and custom `part.fields` BOM metadata programmatically in Python
for the parts used in `buffered_multiple.py`.
"""

import os
from pathlib import Path

# Keep generated .erc, .log, and _sklib.py artifacts inside this lesson's app directory
os.chdir(Path(__file__).resolve().parent)

# Configure writable cache directories and KiCad 10 library paths BEFORE importing skidl
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

from skidl import ERC, POWER, TEMPLATE, Net, Part  # noqa: E402

# Core symbols we need for our Eurorack Buffered Multiple
BUFFERED_MULT_SYMBOLS = [
    ("Connector_Generic", "Conn_02x05_Odd_Even", "10-pin Eurorack IDC power header"),
    ("Device", "D_Schottky", "1N5819WS reverse-polarity protection diode"),
    ("Device", "C_Polarized", "10uF radial electrolytic bulk capacitor"),
    ("Amplifier_Operational", "TL074", "TL074H quad JFET/CMOS op-amp"),
    ("Connector_Audio", "AudioJack2_SwitchT", "WQP-PJ398SM switched 3.5mm mono jack"),
    ("Device", "D_TVS", "PESD12VL1BA bidirectional ESD/TVS protection diode"),
    ("Device", "R", "0603 SMD resistor (100K, 1K, 470R)"),
    ("Device", "C", "0603 SMD ceramic decoupling capacitor (100nF)"),
]

# Target `<Library>:<FootprintName>` strings
BUFFERED_MULT_FOOTPRINTS = [
    "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "Resistor_SMD:R_0603_1608Metric",
    "Capacitor_SMD:C_0603_1608Metric",
    "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "Diode_SMD:D_SOD-323",
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles",
    "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical",
]


def inspect_symbols():
    """Load each symbol as a TEMPLATE and print its exact pin numbers, names, and types."""
    print("=== 1. KiCad 10 Symbol & Pinout Inspection ===")
    for lib_name, sym_name, role in BUFFERED_MULT_SYMBOLS:
        part_t = Part(lib_name, sym_name, dest=TEMPLATE)
        sorted_pins = sorted(
            part_t.pins,
            key=lambda pin: (
                (0, int(pin.num)) if str(pin.num).isdigit() else (1, str(pin.num))
            ),
        )
        pins_summary = ", ".join(
            f"pin {p.num} ('{p.name}', {p.func.name})" for p in sorted_pins
        )
        print(f"\n[{lib_name}:{sym_name}] — {role}")
        print(f"  Pin count: {len(part_t.pins)}")
        print(f"  Pins     : {pins_summary}")


def verify_footprints():
    """Verify every `<Lib>:<Footprint>` resolves to a `.kicad_mod` file on disk."""
    print("\n=== 2. KiCad 10 Footprint Verification ===")
    fp_root = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", ""))
    for fp_id in BUFFERED_MULT_FOOTPRINTS:
        lib_nick, fp_name = fp_id.split(":", 1)
        mod_path = fp_root / f"{lib_nick}.pretty" / f"{fp_name}.kicad_mod"
        status = "FOUND" if mod_path.is_file() else "MISSING"
        print(f"  [{status}] {fp_id} -> {mod_path.name}")


def verify_template_fields_and_erc():
    """Demonstrate why custom BOM metadata belongs in `part.fields` and run ERC."""
    print("\n=== 3. Template Metadata (`part.fields`) & ERC Smoke Check ===")
    r_t = Part(
        "Device",
        "R",
        dest=TEMPLATE,
        value="100K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # Correct pattern: store catalog keys in `part.fields` so clones and BOM exports inherit them
    r_t.fields["LCSC"] = "C25803"
    r_t.fields["MPN"] = "0603WAF1003T5E"
    r_t.fields["JLCPCB_Class"] = "Basic"

    r_pd = r_t(tag="r_pd_test")
    d_tvs = Part(
        "Device",
        "D_TVS",
        value="PESD12VL1BA",
        footprint="Diode_SMD:D_SOD-323",
        tag="d_tvs_test",
    )
    d_tvs.fields["LCSC"] = "C38558"
    d_tvs.fields["MPN"] = "PESD12VL1BA,115"
    d_tvs.fields["JLCPCB_Class"] = "Extended"
    print(f"  Instantiated {r_pd.ref} ({r_pd.value}) with fields: {r_pd.fields}")
    print(f"  Instantiated {d_tvs.ref} ({d_tvs.value}) with fields: {d_tvs.fields}")

    in_jack = Net("CH1_JACK_IN")
    gnd = Net("GND")
    in_jack.drive = POWER
    gnd.drive = POWER
    in_jack & (d_tvs | r_pd) & gnd

    ERC()


if __name__ == "__main__":
    inspect_symbols()
    verify_footprints()
    verify_template_fields_and_erc()
```

### Run the Discovery Script & Read Its Output

```bash title="Terminal · Run discover_parts.py and lint with ruff"
.venv/bin/python tutorial/apps/0001-programmatic-component-discovery/discover_parts.py
ruff check --fix tutorial/apps/0001-programmatic-component-discovery/*.py
ruff format tutorial/apps/0001-programmatic-component-discovery/*.py
```

```bash title="Verified Output · discover_parts.py" copy=false
=== 1. KiCad 10 Symbol & Pinout Inspection ===

[Connector_Generic:Conn_02x05_Odd_Even] — 10-pin Eurorack IDC power header
  Pin count: 10
  Pins     : pin 1 ('Pin_1', PASSIVE), pin 2 ('Pin_2', PASSIVE), pin 3 ('Pin_3', PASSIVE), pin 4 ('Pin_4', PASSIVE), pin 5 ('Pin_5', PASSIVE), pin 6 ('Pin_6', PASSIVE), pin 7 ('Pin_7', PASSIVE), pin 8 ('Pin_8', PASSIVE), pin 9 ('Pin_9', PASSIVE), pin 10 ('Pin_10', PASSIVE)

[Device:D_Schottky] — 1N5819WS reverse-polarity protection diode
  Pin count: 2
  Pins     : pin 1 ('K', PASSIVE), pin 2 ('A', PASSIVE)

[Device:C_Polarized] — 10uF radial electrolytic bulk capacitor
  Pin count: 2
  Pins     : pin 1 ('', PASSIVE), pin 2 ('', PASSIVE)

[Amplifier_Operational:TL074] — TL074H quad JFET/CMOS op-amp
  Pin count: 14
  Pins     : pin 1 ('', OUTPUT), pin 2 ('-', INPUT), pin 3 ('+', INPUT), pin 4 ('V+', PWRIN), pin 5 ('+', INPUT), pin 6 ('-', INPUT), pin 7 ('', OUTPUT), pin 8 ('', OUTPUT), pin 9 ('-', INPUT), pin 10 ('+', INPUT), pin 11 ('V-', PWRIN), pin 12 ('+', INPUT), pin 13 ('-', INPUT), pin 14 ('', OUTPUT)

[Connector_Audio:AudioJack2_SwitchT] — WQP-PJ398SM switched 3.5mm mono jack
  Pin count: 3
  Pins     : pin S ('', PASSIVE), pin T ('', PASSIVE), pin TN ('', PASSIVE)

[Device:D_TVS] — PESD12VL1BA bidirectional ESD/TVS protection diode
  Pin count: 2
  Pins     : pin 1 ('A1', PASSIVE), pin 2 ('A2', PASSIVE)

[Device:R] — 0603 SMD resistor (100K, 1K, 470R)
  Pin count: 2
  Pins     : pin 1 ('', PASSIVE), pin 2 ('', PASSIVE)

[Device:C] — 0603 SMD ceramic decoupling capacitor (100nF)
  Pin count: 2
  Pins     : pin 1 ('', PASSIVE), pin 2 ('', PASSIVE)

=== 2. KiCad 10 Footprint Verification ===
  [FOUND] Package_SO:SOIC-14_3.9x8.7mm_P1.27mm -> SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod
  [FOUND] Resistor_SMD:R_0603_1608Metric -> R_0603_1608Metric.kicad_mod
  [FOUND] Capacitor_SMD:C_0603_1608Metric -> C_0603_1608Metric.kicad_mod
  [FOUND] Capacitor_THT:CP_Radial_D5.0mm_P2.00mm -> CP_Radial_D5.0mm_P2.00mm.kicad_mod
  [FOUND] Diode_SMD:D_SOD-323 -> D_SOD-323.kicad_mod
  [FOUND] Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles -> Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles.kicad_mod
  [FOUND] Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical -> IDC-Header_2x05_P2.54mm_Vertical.kicad_mod

=== 3. Template Metadata (`part.fields`) & ERC Smoke Check ===
  Instantiated R1 (100K) with fields: {'LCSC': 'C25803', 'MPN': '0603WAF1003T5E', 'JLCPCB_Class': 'Basic'}
  Instantiated D1 (PESD12VL1BA) with fields: {'LCSC': 'C38558', 'MPN': 'PESD12VL1BA,115', 'JLCPCB_Class': 'Extended'}
ERC INFO: No errors or warnings found while running ERC.
```

## Step 2. Three Hardware Insights from the Discovery Output

Look closely at the pinout output printed above. Turns out, inspecting those eight symbols upfront reveals three critical details about how we need to index pins when we write our subcircuits in Lessons 0002 and 0003:

1. **Why `TL074` amplifier pins use `u.p[n]` while power pins use `u["V+"]`**: Look at `[Amplifier_Operational:TL074]`: all four op-amp units share identical pin names (`'+'`, `'-'`, and empty `''`). So, if you wrote `u["+"]`, SKiDL would dutifully match all four non-inverting inputs at once! Not quite what we want. Using the **Numeric Pin Accessor (`part.p[n]`)**—such as `u.p[3]`, `u.p[1]`, `u.p[2]`—targets physical SOIC-14 package pin numbers unambiguously, whereas `u["V+"]` (pin 4) and `u["V-"]` (pin 11) are unique and readable by name.
2. **Why `AudioJack2_SwitchT` pins are indexed as `j_in["S"]`, `j_in["T"]`, and `j_in["TN"]`**: Look at `[Connector_Audio:AudioJack2_SwitchT]`: `pin S ('', PASSIVE), pin T ('', PASSIVE), pin TN ('', PASSIVE)`. On this symbol, the letters `S` (Sleeve), `T` (Tip), and `TN` (**Switched Tip Normal Contact (`TN`)**) are the actual pin numbers (`pin.num`) rather than integers `1, 2, 3`!
3. **Why `C_Polarized` bulk caps use `c_bulk[1]` and `c_bulk[2]`**: Look at `[Device:C_Polarized]`: `pin 1 ('', PASSIVE), pin 2 ('', PASSIVE)`—where pin `1` is the positive anode and pin `2` is the negative cathode.

## Step 3. Interactive Component, Pinout & LCSC Explorer

Next, we queried live JLCPCB stock and feeder classes using `jlcpcb_search.py`:

```bash title="Terminal · Query live JLCPCB/LCSC stock and feeder class"
.venv/bin/python .agents/skills/skidl/scripts/jlcpcb_search.py --in-stock-only "100k 0603" "TL074H SOIC-14"
```

:::callout-warn Critical Gotcha: Always Use `part.fields["LCSC"]`, Never `part.LCSC`
Which leads me to an interesting realisation about how SKiDL stores part metadata. If you write `r_pd.LCSC = "C25803"` or pass `LCSC="C25803"` to `Part(...)`, Python happily creates a plain instance attribute—and then `generate_xml()` and `generate_netlist()` **silently ignore it**! The reason this happens is that `SkidlBaseObject.__setattr__` only redirects an attribute write into `part.fields` if that key *already exists* in `part.fields`. So, always assign custom catalogue metadata straight into the **Part Fields Dictionary (`part.fields`)**: `r_pd.fields["LCSC"] = "C25803"`. Better yet, any fields set on a **Template Part (`dest=TEMPLATE`)** are automatically copied to every part cloned from that template.
:::

Use the interactive filter below to explore all 10 component types we discovered, comparing their KiCad 10 symbol pinouts, footprints, and **JLCPCB Basic Part** vs. **JLCPCB Extended Part** assembly classes:

{{widget:part-explorer}}

## Step 4. Growing `buffered_multiple.py` (Stage 1: Header + Constants)

Now, let's take the pre-import header we wrote in Lesson 0000 and **grow our main circuit script** by adding the 7 footprint constants (`FP_*`) and 7 LCSC catalogue constants (`LCSC_*`) we just verified. In Lesson 0002, we will add `@subcircuit def eurorack_power(vcc, vee, gnd):` directly below line 68:

```python title="Growing buffered_multiple.py · Stage 1 (Lines 1–68: Environment Header + Footprint & LCSC Constants)"
#!/usr/bin/env python3
import builtins
import csv
import os
from pathlib import Path

# Keep generated .erc, .log, .net, .xml, .csv, and _sklib.py files inside this script's directory
os.chdir(Path(__file__).resolve().parent)

# Configure writable cache directories and KiCad 10 library paths BEFORE importing skidl
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

# NEW IN STAGE 1: Verified KiCad 10 Footprints (SMD passives & ICs, THT jacks, power header & bulk caps)
FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD323 = "Diode_SMD:D_SOD-323"
FP_JACK_EURORACK = (
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
)
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"

# NEW IN STAGE 1: Verified JLCPCB / LCSC Catalog Part Numbers (SMT assembly)
LCSC_C_100NF_0603 = "C14663"  # YAGEO CC0603KRX7R9BB104 (50V X7R, Basic Part)
LCSC_R_100K_0603 = "C25803"  # UNI-ROYAL 0603WAF1003T5E (100k 1%, Basic Part)
LCSC_R_1K_0603 = "C21190"  # UNI-ROYAL 0603WAF1001T5E (1k 1%, Basic Part)
LCSC_R_470R_0603 = "C23179"  # UNI-ROYAL 0603WAF4700T5E (470R 1%, Basic Part)
LCSC_D_1N5819WS_SOD323 = "C191023"  # CJ 1N5819WS (40V 1A Schottky SOD-323, Basic Part)
LCSC_D_TVS_PESD12VL1BA_SOD323 = "C38558"  # Nexperia PESD12VL1BA,115 (12V Bidir TVS SOD-323, Extended Part)
LCSC_U_TL074H_SOIC14 = "C2878713"  # Texas Instruments TL074HIDR (SOIC-14, Extended Part)
```

:::exercise id="ex-0001-title" title="Retrieval Practice: Assign Template BOM Fields & Wire Pin Indices"
Fill in the four blanks below to store the LCSC part number and JLCPCB class in the template's `fields` dictionary, connect `+12V` to the `TL074` positive supply pin by name, and wire the input signal to Unit A's non-inverting input (pin `3`) using SKiDL's numeric pin accessor:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
c_t = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0603_1608Metric")
c_t.{{blank:fields|Dictionary on a SKiDL Part for custom BOM keys: fields|Dictionary attribute on Part that persists BOM metadata|8}}["LCSC"] = "C14663"
c_t.fields["{{blank:JLCPCB_Class|Field key used in our script: JLCPCB_Class|Custom field key for Basic or Extended status|13}}"] = "Basic"

u = Part("Amplifier_Operational", "TL074", value="TL074H", footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")
vcc += u["{{blank:V+|Positive power pin name on KiCad TL074 symbol: V+|Pin name for positive supply rail on TL074|4}}"]
in_sig += u.{{blank:p|Single-letter attribute on Part for strict pin-number indexing: p|SKiDL numeric pin accessor attribute|3}}[3]
```
:::

:::quiz id="quiz-0001-title" title="Knowledge Check"
- question: "1. Why must we index `TL074` amplifier pins with `u.p[3]` instead of `u[\"+\"]`?"
  options:
    - letter: A
      text: "KiCad ten symbols omit pin names on every operational amplifier library component."
      correct: false
      explain: "KiCad 10's TL074 symbol does define pin names ('+', '-', 'V+', 'V-'), as shown by discover_parts.py."
    - letter: B
      text: "String indexing silently converts passive op-amp inputs into driven power rail pins."
      correct: false
      explain: "Indexing a pin never alters its electrical function (INPUT vs PWRIN)."
    - letter: C
      text: "All four internal amplifier units share identical non-inverting and inverting pin names."
      correct: true
      explain: "Units A, B, C, and D on TL074 all name their inputs '+' and '-', so u['+'] matches all four units at once, whereas u.p[3] selects physical pin 3."
    - letter: D
      text: "Numeric indexing disables ERC warnings when wiring unity-gain op-amp buffer output stages."
      correct: false
      explain: "ERC() checks every pin regardless of whether it was accessed via u.p[n] or u['name']."
- question: "2. Why must LCSC catalog numbers be stored in `part.fields[\"LCSC\"]` rather than `part.LCSC`?"
  options:
    - letter: A
      text: "SKiDL only exports custom keys stored inside the part fields dictionary structure."
      correct: true
      explain: "SkidlBaseObject.__setattr__ only updates part.fields for existing keys; new BOM keys must be assigned into part.fields['LCSC'] so XML/CSV exporters and template clones preserve them."
    - letter: B
      text: "Python forbids setting uppercase attribute names on instantiated circuit part class objects."
      correct: false
      explain: "Python allows uppercase attribute names on objects, but SKiDL's netlist/XML exporters ignore plain attributes."
    - letter: C
      text: "Direct attribute assignment erases the assigned footprint name inside the generated netlist."
      correct: false
      explain: "Setting an unrelated attribute on a Part does not overwrite part.footprint."
    - letter: D
      text: "Template clones only preserve footprint strings when assigned through global environment variables."
      correct: false
      explain: "Footprints are passed directly to Part(..., footprint=...) and are unrelated to os.environ."
:::

:::callout-success Primary Sources & Next Steps
**Primary Sources**: [KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference](../reference/kicad-jlcpcb-lookup.md) · [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md) · [TI `TL074H` Datasheet](https://www.ti.com/lit/ds/symlink/tl074h.pdf).<br>**Ask the Agent**: Want to try searching for another Eurorack component (like an `SSI2164` VCA, `LM13700` OTA, or potentiometer footprint), or ready for **Lesson 0002** where we grow Stage 1 into a working Eurorack power subcircuit? Just ask in chat!
:::
