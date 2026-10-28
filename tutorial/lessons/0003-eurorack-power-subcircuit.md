---
title: "Growing the Script: Adding `eurorack_power(vcc, vee, gnd)`"
page_title: "Lesson 0003: Growing the Script — Adding eurorack_power(vcc, vee, gnd) | Eurorack SKiDL Tutorial"
nav_id: "0003"
kicker: "Lesson 0003 · Stage 3 (68 → 155 Lines)"
lead: "Take our Stage 2 foundation (pre-import header + footprint and LCSC constants) and grow it into a working, ERC-verified Eurorack power supply script with a 10-pin Doepfer IDC header, `1N5819WS` Schottky reverse-polarity protection, and `10uF` bulk electrolytic capacitors."
badges:
  - text: "Script Growth: Stage 2 → 155 Lines (5 Parts)"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0003 · Stage 3"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "Growing the Script: Adding `eurorack_power(vcc, vee, gnd)`"
  summary: "Add the `@subcircuit` power block with the 10-pin IDC header, `1N5819WS` Schottky reverse-polarity protection, and `10uF` bulk caps."
  meta:
    - "**Code Grown**: `Stage 2 → 155 lines` (Full runnable `power_subcircuit.py` inline)"
    - "**Tooling Skill**: `@subcircuit`, multi-pin slice `j_pwr[3..8]`, `.net`/`.xml` export"
  app_dir: "./apps/0003-eurorack-power-subcircuit"
pager_prev:
  href: "0002-programmatic-component-discovery.html"
  label: "← Previous Lesson"
  title: "0002: Programmatic Part Discovery & Constants"
pager_next:
  href: "0004-single-buffered-channel.html"
  label: "Next Lesson →"
  title: "0004: Growing the Script — Adding buffered_channel_1to3()"
---

## How `@subcircuit` Maps a Python Function to KiCad Hierarchy

In [Lesson 0002](0002-programmatic-component-discovery.md), we grew our script to include the pre-import environment setup and our verified `FP_*` and `LCSC_*` constants. Now, let's add our first hierarchical circuit block: `@subcircuit def eurorack_power(vcc, vee, gnd):`.

If you've spent any time around modular synthesisers, you know that plugging a 10-pin Eurorack power cable in backwards is a rite of passage—and a fast way to let the magic smoke out of your little noise maker if the rails aren't protected. So, building our power input and reverse-polarity protection as a dedicated, reusable function makes a lot of sense.

Decorating a function with SKiDL's **Subcircuit Decorator (`@subcircuit`)** does two really helpful things for us:

1. **Interface Nets vs. Private Local Nets**: The protected module rails (`vcc`, `vee`, `gnd`) are passed in as function arguments so downstream op-amp channels can attach to them later, while the raw header nets (`vcc_raw = Net("+12V_RAW")` and `vee_raw = Net("-12V_RAW")`) remain private inside `eurorack_power`.
2. **Deterministic Hierarchical Path Tags**: When the top-level circuit calls `eurorack_power(vcc, vee, gnd, tag="pwr")` and each internal part defines a `tag` (such as `tag="j_pwr"`, `tag="d_prot"`, `tag="c_bulk"`), SKiDL hashes the hierarchical path (`/pwr/c_bulk`) into a deterministic KiCad `tstamp` UUID. Re-running your Python script never scrambles component associations in KiCad's PCB editor!

```mermaid caption="Signal and current return topology inside `eurorack_power(vcc, vee, gnd)`."
flowchart LR
  subgraph HDR["J1: Conn_02x05_Odd_Even (10-Pin IDC)"]
    P910["Pins 9, 10<br/>+12V Header"]
    P38["Pins 3..8<br/>GND Centre"]
    P12["Pins 1, 2<br/>-12V (Red Stripe)"]
  end

  P910 -- "+12V_RAW" --> D1["D1: 1N5819WS<br/>A (2) → K (1)"]
  D1 --> VCC["+12V Rail (vcc)"]
  VCC --> C1P["C1: 10uF Bulk<br/>Pin 1 (+) → Pin 2 (-)"]
  C1P --> GND["GND Plane (gnd)"]

  P38 --> GND

  P12 -- "-12V_RAW" --> D2["D2: 1N5819WS<br/>K (1) ← A (2)"]
  D2 --> VEE["-12V Rail (vee)"]
  GND --> C2N["C2: 10uF Bulk<br/>Pin 1 (+) → Pin 2 (-)"]
  C2N --> VEE
```

## Step 1. Add the 10-Pin Eurorack IDC Header & Multi-Pin Slices

Instead of writing ten separate `+=` statements for the 10-pin (`2×5`) Eurorack power header, SKiDL lets you index multiple pins in a single tuple subscript:

- `vee_raw += j_pwr[1, 2]` wires pins 1 and 2 (the `-12V` red-stripe end) to `-12V_RAW`.
- `gnd += j_pwr[3, 4, 5, 6, 7, 8]` wires all six centre ground pins to `GND` in one statement.
- `vcc_raw += j_pwr[9, 10]` wires pins 9 and 10 to `+12V_RAW`.

```python title="New Code Added · eurorack_power() Part 1: 10-Pin IDC Header"
@subcircuit
def eurorack_power(vcc, vee, gnd):
    """
    10-pin Eurorack power input with Schottky reverse-polarity protection
    and bulk electrolytic filtering on +12V and -12V rails.
    """
    j_pwr = Part(
        "Connector_Generic",
        "Conn_02x05_Odd_Even",
        value="EURORACK_PWR_10PIN",
        footprint=FP_PWR_HEADER_10P,
        tag="j_pwr",
    )
    j_pwr.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"

    vcc_raw = Net("+12V_RAW")
    vee_raw = Net("-12V_RAW")

    # Standard 10-pin Eurorack pinout:
    # Pins 1, 2: -12V (Red stripe)
    # Pins 3..8: GND
    # Pins 9, 10: +12V
    vee_raw += j_pwr[1, 2]
    gnd += j_pwr[3, 4, 5, 6, 7, 8]
    vcc_raw += j_pwr[9, 10]
```

## Step 2. Add Bipolar Schottky Diode & Bulk Capacitor Polarity

Next, inside `eurorack_power()`, we add two `1N5819WS` Schottky diodes (`d_pos`, `d_neg`) and two `10uF` radial electrolytic bulk capacitors (`c_bulk_pos`, `c_bulk_neg`) cloned from templates.

Now, if you're used to single-supply digital boards (`+3.3V` or `+5V` and `GND`), bipolar `±12V` analog rails have a classic trap on the negative side. Because both pins on `Device:D_Schottky` and `Device:C_Polarized` are marked `PASSIVE` in KiCad's symbol library, `ERC()` won't yell at you if you wire a diode or electrolytic cap backwards! Turning that into code requires paying close attention to current return paths with pin names (`"A"`, `"K"`) and numbers (`1`, `2`):

Table: Pin-by-pin polarity in `eurorack_power(vcc, vee, gnd)`

| Component | Rail | SKiDL Wiring | Electrical Reason |
| --- | --- | --- | --- |
| `d_pos` (`D1`, `1N5819WS`) | `+12V` | `vcc_raw += d_pos["A"]`<br>`vcc += d_pos["K"]` | Conventional current flows out of the header (`+12V_RAW`) into the Anode (`A`) and exits the Cathode (`K`) into the module's `+12V` rail. |
| `d_neg` (`D2`, `1N5819WS`) | `-12V` | `vee_raw += d_neg["K"]`<br>`vee += d_neg["A"]` | On the negative rail, conventional current returns *from* the module's `-12V` rail (`vee`) into the Anode (`A`) and exits the Cathode (`K`) back into the header (`-12V_RAW`). |
| `c_bulk_pos` (`C1`, `10uF`) | `+12V` to `GND` | `vcc += c_bulk_pos[1]`<br>`gnd += c_bulk_pos[2]` | `+12V` is positive relative to `0V`, so pin `1` (`+` anode) connects to `vcc` and pin `2` (`-` cathode) connects to `gnd`. |
| `c_bulk_neg` (`C2`, `10uF`) | `GND` to `-12V` | `gnd += c_bulk_neg[1]`<br>`vee += c_bulk_neg[2]` | `0V` (`GND`) sits at a **higher potential** than `-12V`! Therefore pin `1` (`+` anode) must connect to `gnd` and pin `2` (`-` cathode) to `vee`. |

```python title="New Code Added · eurorack_power() Part 2: 1N5819WS Diodes & 10uF Bulk Caps"
    # Reverse-polarity protection Schottky diodes (1N5819WS in SOD-323)
    d_t = Part(
        "Device",
        "D_Schottky",
        dest=TEMPLATE,
        value="1N5819WS",
        footprint=FP_DIODE_SOD323,
    )
    d_t.fields["LCSC"] = LCSC_D_1N5819WS_SOD323
    d_t.fields["MPN"] = "1N5819WS"
    d_t.fields["JLCPCB_Class"] = "Basic"
    d_t.fields["Notes"] = (
        "40V 1A Schottky diode in Diode_SMD:D_SOD-323; Alt larger package: B5819W in Diode_SMD:D_SOD-123 (LCSC C8598, Basic)"
    )
    d_pos, d_neg = d_t(2, tag="d_prot")

    # +12V protection: Anode (A) at header -> Cathode (K) at +12V rail
    vcc_raw += d_pos["A"]
    vcc += d_pos["K"]

    # -12V protection: Cathode (K) at header <- Anode (A) at -12V rail
    vee_raw += d_neg["K"]
    vee += d_neg["A"]

    # Bulk electrolytic bypass capacitors (10uF / 25V radial through-hole, Panasonic ECEA1EKS100)
    c_bulk_t = Part(
        "Device",
        "C_Polarized",
        dest=TEMPLATE,
        value="10uF",
        footprint=FP_C_ELEC,
    )
    c_bulk_t.fields["MPN"] = "ECEA1EKS100"
    c_bulk_t.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"
    c_bulk_pos, c_bulk_neg = c_bulk_t(2, tag="c_bulk")

    # +12V bulk cap: (+) to +12V, (-) to GND
    vcc += c_bulk_pos[1]
    gnd += c_bulk_pos[2]

    # -12V bulk cap: (+) to GND, (-) to -12V (since GND is positive relative to -12V)
    gnd += c_bulk_neg[1]
    vee += c_bulk_neg[2]
```

## Step 3. Add Top-Level Power Net Wiring, `ERC()` & Export

Finally, we add a top-level function `run_power_subcircuit()` that creates the three global power nets (`vcc`, `vee`, `gnd`), sets `.drive = POWER` on each, calls `eurorack_power(vcc, vee, gnd, tag="pwr")`, runs `ERC()`, and exports our first KiCad 10 netlist (`.net`) and XML BOM (`.xml`):

```python title="New Code Added · Top-Level Runner & Netlist/XML Export"
def run_power_subcircuit():
    """Instantiate `eurorack_power`, verify with `ERC()`, and export `.net` / `.xml`."""
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")

    # Mark protected rails as POWER-driven for ERC verification
    vcc.drive = POWER
    vee.drive = POWER
    gnd.drive = POWER

    eurorack_power(vcc, vee, gnd, tag="pwr")

    ERC()
    generate_netlist(file_="power_subcircuit.net")
    generate_xml(file_="power_subcircuit_bom.xml")

    print("=== Eurorack Power Subcircuit Verification ===")
    for part in builtins.default_circuit.parts:
        lcsc = part.fields.get("LCSC", "—")
        jlc_cls = part.fields.get("JLCPCB_Class", "—")
        print(f"  {part.ref:<4} | {part.value:<18} | LCSC: {lcsc:<8} | {jlc_cls}")

    for rail in (vcc, vee, gnd):
        sorted_pins = sorted(rail.pins, key=lambda p: (p.part.ref, int(p.num)))
        pin_list = ", ".join(f"{p.part.ref}.{p.num}" for p in sorted_pins)
        print(f"  Net {rail.name:<5} -> {pin_list}")


if __name__ == "__main__":
    run_power_subcircuit()
```

## Step 4. Complete Stage 3 Script & Terminal Verification

Here is the **complete, standalone 155-line Stage 3 Python script** combining our pre-import header, constants, `eurorack_power` subcircuit, and verification runner (saved at `tutorial/apps/0003-eurorack-power-subcircuit/power_subcircuit.py`):

```python title="Complete Stage 3 Script · tutorial/apps/0003-eurorack-power-subcircuit/power_subcircuit.py"
#!/usr/bin/env python3
"""
Lesson 0003: Eurorack Power Supply `@subcircuit` & Reverse-Polarity Protection.

Builds and verifies `eurorack_power(vcc, vee, gnd)` with:
- 10-pin (2x5) shrouded IDC header (`Connector_Generic:Conn_02x05_Odd_Even`)
- 1N5819WS Schottky reverse-polarity protection diodes (`Device:D_Schottky`, SOD-323)
- 10uF radial electrolytic bulk bypass capacitors (`Device:C_Polarized`)
"""

import builtins
import os
from pathlib import Path

# Keep generated .erc, .log, .net, .xml, and _sklib.py files inside this lesson's app directory
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
    Part,
    generate_netlist,
    generate_xml,
    subcircuit,
)

FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD323 = "Diode_SMD:D_SOD-323"
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"

LCSC_D_1N5819WS_SOD323 = "C191023"  # CJ 1N5819WS (40V 1A Schottky SOD-323, Basic Part)


@subcircuit
def eurorack_power(vcc, vee, gnd):
    """
    10-pin Eurorack power input with Schottky reverse-polarity protection
    and bulk electrolytic filtering on +12V and -12V rails.
    """
    j_pwr = Part(
        "Connector_Generic",
        "Conn_02x05_Odd_Even",
        value="EURORACK_PWR_10PIN",
        footprint=FP_PWR_HEADER_10P,
        tag="j_pwr",
    )
    j_pwr.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"

    vcc_raw = Net("+12V_RAW")
    vee_raw = Net("-12V_RAW")

    # Standard 10-pin Eurorack pinout:
    # Pins 1, 2: -12V (Red stripe)
    # Pins 3..8: GND
    # Pins 9, 10: +12V
    vee_raw += j_pwr[1, 2]
    gnd += j_pwr[3, 4, 5, 6, 7, 8]
    vcc_raw += j_pwr[9, 10]

    # Reverse-polarity protection Schottky diodes (1N5819WS in SOD-323)
    d_t = Part(
        "Device",
        "D_Schottky",
        dest=TEMPLATE,
        value="1N5819WS",
        footprint=FP_DIODE_SOD323,
    )
    d_t.fields["LCSC"] = LCSC_D_1N5819WS_SOD323
    d_t.fields["MPN"] = "1N5819WS"
    d_t.fields["JLCPCB_Class"] = "Basic"
    d_t.fields["Notes"] = (
        "40V 1A Schottky diode in Diode_SMD:D_SOD-323; Alt larger package: B5819W in Diode_SMD:D_SOD-123 (LCSC C8598, Basic)"
    )
    d_pos, d_neg = d_t(2, tag="d_prot")

    # +12V protection: Anode (A) at header -> Cathode (K) at +12V rail
    vcc_raw += d_pos["A"]
    vcc += d_pos["K"]

    # -12V protection: Cathode (K) at header <- Anode (A) at -12V rail
    vee_raw += d_neg["K"]
    vee += d_neg["A"]

    # Bulk electrolytic bypass capacitors (10uF / 25V radial through-hole, Panasonic ECEA1EKS100)
    c_bulk_t = Part(
        "Device",
        "C_Polarized",
        dest=TEMPLATE,
        value="10uF",
        footprint=FP_C_ELEC,
    )
    c_bulk_t.fields["MPN"] = "ECEA1EKS100"
    c_bulk_t.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"
    c_bulk_pos, c_bulk_neg = c_bulk_t(2, tag="c_bulk")

    # +12V bulk cap: (+) to +12V, (-) to GND
    vcc += c_bulk_pos[1]
    gnd += c_bulk_pos[2]

    # -12V bulk cap: (+) to GND, (-) to -12V (since GND is positive relative to -12V)
    gnd += c_bulk_neg[1]
    vee += c_bulk_neg[2]


def run_power_subcircuit():
    """Instantiate `eurorack_power`, verify with `ERC()`, and export `.net` / `.xml`."""
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")

    # Mark protected rails as POWER-driven for ERC verification
    vcc.drive = POWER
    vee.drive = POWER
    gnd.drive = POWER

    eurorack_power(vcc, vee, gnd, tag="pwr")

    ERC()
    generate_netlist(file_="power_subcircuit.net")
    generate_xml(file_="power_subcircuit_bom.xml")

    print("=== Eurorack Power Subcircuit Verification ===")
    for part in builtins.default_circuit.parts:
        lcsc = part.fields.get("LCSC", "—")
        jlc_cls = part.fields.get("JLCPCB_Class", "—")
        print(f"  {part.ref:<4} | {part.value:<18} | LCSC: {lcsc:<8} | {jlc_cls}")

    for rail in (vcc, vee, gnd):
        sorted_pins = sorted(rail.pins, key=lambda p: (p.part.ref, int(p.num)))
        pin_list = ", ".join(f"{p.part.ref}.{p.num}" for p in sorted_pins)
        print(f"  Net {rail.name:<5} -> {pin_list}")


if __name__ == "__main__":
    run_power_subcircuit()
```

```bash title="Terminal · Run power_subcircuit.py and format with ruff"
.venv/bin/python tutorial/apps/0003-eurorack-power-subcircuit/power_subcircuit.py
ruff check --fix tutorial/apps/0003-eurorack-power-subcircuit/*.py
ruff format tutorial/apps/0003-eurorack-power-subcircuit/*.py
```

```bash title="Verified Output · power_subcircuit.py" copy=false
ERC INFO: No errors or warnings found while running ERC.

INFO: 0 errors found while generating netlist.
INFO: 0 errors found while generating XML.

=== Eurorack Power Subcircuit Verification ===
  J1   | EURORACK_PWR_10PIN | LCSC: —        | Manual THT (DNP for SMT)
  D1   | 1N5819WS           | LCSC: C191023  | Basic
  D2   | 1N5819WS           | LCSC: C191023  | Basic
  C1   | 10uF               | LCSC: —        | Manual THT (DNP for SMT)
  C2   | 10uF               | LCSC: —        | Manual THT (DNP for SMT)
  Net +12V  -> C1.1, D1.1
  Net -12V  -> C2.2, D2.2
  Net GND   -> C1.2, C2.1, J1.3, J1.4, J1.5, J1.6, J1.7, J1.8
```

:::exercise id="ex-0003-title" title="Retrieval Practice: Complete the `eurorack_power` Subcircuit"
Fill in the four blanks below to decorate the subcircuit function, instantiate two Schottky diodes from the `d_t` template, wire the `-12V` diode's Cathode (`"K"`) to `vee_raw`, and connect the `-12V` bulk capacitor's positive anode (pin `1`) to `gnd`:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
@{{blank:subcircuit|SKiDL decorator imported from skidl: subcircuit|SKiDL decorator for hierarchical subcircuit functions|11}}
def eurorack_power(vcc, vee, gnd):
    d_t = Part("Device", "D_Schottky", dest=TEMPLATE, value="1N5819WS", footprint=FP_DIODE_SOD323)
    d_pos, d_neg = d_t({{blank:2|Integer count of diodes to clone from d_t: 2|Number of Schottky diodes to instantiate from template|3}}, tag="d_prot")

    # -12V protection: Cathode at header, Anode at -12V rail
    vee_raw += d_neg["{{blank:K|Single-letter pin name for Cathode: K|Pin name for Cathode on D_Schottky|3}}"]
    vee += d_neg["A"]

    # -12V bulk cap: (+) pin 1 to GND, (-) pin 2 to -12V
    gnd += c_bulk_neg[{{blank:1|Positive anode pin number on Device:C_Polarized: 1|Pin number for positive anode on C_Polarized|3}}]
    vee += c_bulk_neg[2]
```
:::

:::quiz id="quiz-0003-title" title="Knowledge Check"
- question: "1. On the `-12V` reverse-polarity protection Schottky diode (`d_neg`), why is the Cathode (`K`) wired to `vee_raw` (the header) and the Anode (`A`) wired to `vee` (the module's `-12V` rail)?"
  options:
    - letter: A
      text: "Conventional current returns from module circuits at negative twelve volts toward the supply header."
      correct: true
      explain: "On the -12V rail, conventional current flows from the module's -12V circuits (Anode) back into the more negative -12V_RAW supply pin (Cathode)."
    - letter: B
      text: "Schottky diodes invert their internal anode and cathode pin numbers whenever placed below ground."
      correct: false
      explain: "KiCad symbol pin numbers and names on D_Schottky are fixed regardless of which net they attach to."
    - letter: C
      text: "KiCad symbols swap anode and cathode labels whenever negative net names attach during export."
      correct: false
      explain: "SKiDL exports pin connections verbatim without swapping symbol pin names based on net polarity."
    - letter: D
      text: "Reverse biasing the negative rail diode during normal operation lowers total power supply ripple."
      correct: false
      explain: "A reverse-biased series diode in normal operation would block the -12V rail completely!"
- question: "2. Why does the `-12V` bulk electrolytic capacitor (`c_bulk_neg`) connect its positive pin (`c_bulk_neg[1]`) to `gnd` (`0V`) and its negative pin (`c_bulk_neg[2]`) to `vee` (`-12V`)?"
  options:
    - letter: A
      text: "Electrolytic capacitors require reverse voltage bias whenever filtering high frequency switching supply rails."
      correct: false
      explain: "Reverse-biasing an aluminium electrolytic capacitor damages its dielectric oxide layer and can cause venting."
    - letter: B
      text: "KiCad assigns pin number one as the negative cathode on polarised capacitor symbols."
      correct: false
      explain: "On KiCad's Device:C_Polarized symbol, pin 1 is the positive (+) anode and pin 2 is the negative (-) cathode."
    - letter: C
      text: "Zero volts ground sits at a higher electric potential than negative twelve volts."
      correct: true
      explain: "Because 0V (GND) is 12V more positive than -12V, the capacitor's positive terminal (pin 1) must sit at GND and its negative terminal (pin 2) at -12V."
    - letter: D
      text: "SKiDL raises an electrical rules error whenever two positive capacitor pins share ground."
      correct: false
      explain: "Both pins on Device:C_Polarized have electrical type PASSIVE, so ERC does not enforce polarity—getting it right is up to the designer!"
:::

:::callout-success Primary Sources & Follow-Up Questions
**Primary Sources**: [Eurorack Power & Audio Jack Normalling Reference](../reference/eurorack-power-and-normalling.md) · [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md).<br>**Ask the Agent**: Curious when to choose `1N5819WS` (`SOD-323`) vs. `B5819W` (`SOD-123`) or series PTC fuses on higher-current digital modules? Ask in chat anytime, or proceed to **Lesson 0004** where we grow this script by adding `buffered_channel_1to3()`!
:::
