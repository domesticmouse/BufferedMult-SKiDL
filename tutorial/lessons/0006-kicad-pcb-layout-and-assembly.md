---
title: "From `.net` Netlist to 4HP KiCad 10 PCB Layout & Single-Sided SMT Assembly"
page_title: "Lesson 0006: From .net Netlist to 4HP KiCad 10 PCB Layout & Single-Sided SMT Assembly | Eurorack SKiDL Tutorial"
nav_id: "0006"
kicker: "Lesson 0006 · Stage 6 (Post-Netlist Hardware-as-Code)"
lead: "See how our exported `buffered_multiple.net` file bridges Python into KiCad 10's PCB Editor (`pcbnew`) without a `.kicad_sch` schematic—using deterministic SKiDL `tag` timestamps, a single-sided `B.Cu` SMT vs. `F.Cu` THT assembly split, and a programmatic 4HP (`20.0 × 108.0 mm`) jack placement planner."
badges:
  - text: "Runnable App: inspect_netlist_and_layout.py (357 Lines)"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0006 · Stage 6"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "From `.net` Netlist to 4HP KiCad 10 PCB Layout & Single-Sided SMT Assembly"
  summary: "Parse deterministic SKiDL `tstamps` in `buffered_multiple.net`, partition the 29 `B.Cu` SMD parts from the 15 `F.Cu`/`B.Cu` THT parts, and generate the 4HP (`20 × 108 mm`) 2×6 jack placement grid."
  meta:
    - "**Code Grown**: `inspect_netlist_and_layout.py` (357 lines inline + placement CSV)"
    - "**Tooling Skill**: S-expression `.net` parsing, hierarchical `tag` UUIDs, `B.Cu` vs. `F.Cu` split"
  app_dir: "./apps/0006-kicad-pcb-layout-and-assembly"
pager_prev:
  href: "0005-cascaded-normalling-and-bom-export.html"
  label: "← Previous Lesson"
  title: "0005: Completing buffered_multiple.py — Cascaded Normalling & BOM"
pager_next:
  href: "0007-eurorack-front-panel-generator.html"
  label: "Next Lesson →"
  title: "0007: Automated 4HP Eurorack Front Panel Generation (+6.48 mm Offset)"
---

## Step 1. How SKiDL Replaces `.kicad_sch` with Deterministic `tstamps`

In a traditional KiCad workflow, you draw a visual schematic (`.kicad_sch`) and click **Update PCB from Schematic**. When you design in Python with SKiDL ([Lesson 0005](0005-cascaded-normalling-and-bom-export.md)), there is no `.kicad_sch` file—instead, you open KiCad 10's **PCB Editor (`pcbnew`)** and select **`File → Import → Netlist...`** to load `buffered_multiple.net` directly.

That raises a critical software-engineering question: *what happens when you tweak your Python script and re-import `buffered_multiple.net` into an already-routed PCB?*

If a component's unique identifier changes between runs, KiCad rips up its existing footprint and drops a fresh unplaced copy at the cursor. That is why every subcircuit call and part instantiation in our script passes an explicit `tag=` string (`eurorack_power(..., tag="pwr")`, `buffered_channel_1to3(..., tag="ch1")`, `tag=f"u_ch{ch_num}"`, `tag=f"j_in_ch{ch_num}"`). SKiDL hashes the hierarchical path (`/ch1/u_ch1`) into a deterministic UUID inside the exported `.net` file:

```mermaid caption="How hierarchical SKiDL `tag` strings map to stable KiCad 10 `(tstamps ...)` across iterative Python edits."
flowchart LR
  TAG["Python SKiDL Tags<br/>tag='ch1' + tag='u_ch1'"] --> UUID["Deterministic KiCad tstamps<br/>sheet=/ch1/ · c569285a-52fc-..."]
  UUID --> PCB["KiCad 10 pcbnew Import<br/>Match by Timestamp / Unique ID"]
  PCB --> PLACE["In-Place PCB Update<br/>Preserves Placed U1..U3 & Traces"]
```

## Step 2. The 4HP (`20.0 × 108.0 mm`) Layer & Assembly Partition

A 12-jack Triple 1-to-3 Buffered Multiple arranged in 6 rows × 2 columns fits comfortably on a single-board **4HP** (`20.0 mm` wide × `108.0 mm` tall) PCB. To keep JLCPCB assembly fast and economical, we partition the 44 circuit components across the front (`F.Cu`) and back (`B.Cu`) copper layers by assembly method:

Table: 4HP PCB Layer & Assembly Partition (44 Total Components = 29 SMT + 15 THT)

| Board Side | Assembly Method | Count | Components & Mechanical Clearance Rationale |
| --- | --- | --- | --- |
| **Back (`B.Cu`)** | **JLCPCB Single-Sided SMT** | **29 SMD** | `U1`–`U3` (`TL074H` in `SOIC-14`), `D1`–`D2` (`1N5819WS`), `D3`–`D5` (`PESD12VL1BA`), `C3`–`C8` (`100nF`), and `R1`–`R15` (`100K`, `1K`, `470R`). Keeping every SMD footprint on `B.Cu` means JLCPCB runs a single solder-paste stencil and reflow pass. |
| **Front (`F.Cu`)** | **Bench Hand-Soldered THT** | **14 THT** | 12× `WQP-PJ398SM` (Thonkiconn) switched 3.5mm jacks (`J2`–`J13`) plus the two `10uF` radial electrolytic bulk capacitors (`C1`, `C2`, Panasonic `ECEA1EKS100`). Because Thonkiconn jacks create a `10.5 mm` board-to-panel standoff and `ECEA1EKS100` cans are only `7.0 mm` tall, mounting `C1` and `C2` on `F.Cu` hides them cleanly in the inter-board gap with `3.5 mm` of headroom! |
| **Back (`B.Cu`)** | **Bench Hand-Soldered THT** | **1 THT** | 1× 10-pin (`2×5`) shrouded Eurorack IDC power header (`J1`), facing into the Eurorack case for the ribbon cable. |

:::callout Why `C2`'s Square Pad (`+`) Connects to `GND` on `F.Cu`
When placing the two radial bulk capacitors (`C1` and `C2`) on `F.Cu`, remember the bipolar rail potential rule from [Lesson 0003](0003-eurorack-power-subcircuit.md): on the `+12V` rail, `C1` Pin `1` (`+`, square pad) connects to `+12V` and Pin `2` (`-`) connects to `GND`. On the `-12V` rail, `GND` (`0V`) is 12 volts *more positive* than `-12V`, so `C2` Pin `1` (`+`, square pad) connects to `GND` and Pin `2` (`-`) connects to `-12V`!
:::

## Step 3. Parse the Exported `.net` File & Generate the 4HP Placement Grid in Python

Let's add two functions to our circuit script—`parse_netlist_metadata()` and `compute_4hp_jack_grid()`—so we can inspect the S-expression `.net` file that SKiDL exports and generate a CSV placement coordinate table for all 12 front-panel jacks (`J2`–`J13`) on a `20.0 × 108.0 mm` board spanning `X = 20.0..40.0 mm`, `Y = 20.0..128.0 mm` in KiCad's canvas:

```python title="New Code Added · parse_netlist_metadata() & compute_4hp_jack_grid()"
def parse_netlist_metadata(net_path: Path) -> dict:
    """Parse component tstamps, sheetpaths, and net classes from a KiCad `.net` file."""
    text = net_path.read_text(encoding="utf-8")
    comp_pattern = re.compile(
        r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]+)"\)'
        r'.*?\(footprint\s+"([^"]+)"\)'
        r'.*?\(name\s+"SKiDL Tag"\)\s+"([^"]+)"'
        r'.*?\(sheetpath\s+\(names\s+"([^"]+)"\)\s+\(tstamps\s+"([^"]+)"\)\)'
        r'\s+\(component_classes\)\s+\(tstamps\s+"([^"]+)"\)',
        re.DOTALL,
    )
    components = [
        {
            "ref": m.group(1),
            "value": m.group(2),
            "footprint": m.group(3),
            "skidl_tag": m.group(4),
            "sheet": m.group(5),
            "sheet_tstamp": m.group(6),
            "comp_tstamp": m.group(7),
        }
        for m in comp_pattern.finditer(text)
    ]
    net_pattern = re.compile(
        r'\(net\s+\(code\s+\d+\)\s+\(name\s+"([^"]+)"\)\s+\(class\s+"([^"]+)"\)'
    )
    nets = [
        {"name": m.group(1), "netclass": m.group(2)} for m in net_pattern.finditer(text)
    ]
    return {"components": components, "nets": nets}
```

## Step 4. Complete Runnable Script (`inspect_netlist_and_layout.py`)

Here is the complete, standalone 357-line script in `tutorial/apps/0006-kicad-pcb-layout-and-assembly/inspect_netlist_and_layout.py`. It builds the 3-channel circuit, runs `ERC()`, exports `buffered_multiple.net`, parses the deterministic `tstamps` and `NetClass` rules out of the generated S-expression file, and writes the 2×6 jack placement plan to `layout_placement_plan.csv`:

```python title="tutorial/apps/0006-kicad-pcb-layout-and-assembly/inspect_netlist_and_layout.py (Complete 357-Line Script)"
#!/usr/bin/env python3
"""
Lesson 0006: From .net Netlist to 4HP KiCad 10 PCB Layout & Single-Sided SMT Assembly.

Builds the 3-channel Eurorack Buffered Multiple netlist, parses the exported KiCad 10
S-expression `.net` file to inspect deterministic hierarchical `tstamps` and `NetClass`
routing rules, and prints the 4HP (`20.0 x 108.0 mm`) F.Cu THT vs. B.Cu SMT placement plan.
"""

import builtins
import csv
import os
import re
from pathlib import Path

# Keep generated .erc, .log, .net, .csv, and _sklib.py files inside this lesson's app directory
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

from skidl import (
    ERC,
    POWER,
    TEMPLATE,
    Net,
    NetClass,
    Part,
    generate_netlist,
    subcircuit,
)

# Footprints (SMD passives & ICs, through-hole Eurorack jacks, power header & bulk caps)
FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD323 = "Diode_SMD:D_SOD-323"
FP_JACK_EURORACK = (
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
)
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"

# Verified JLCPCB / LCSC Catalog Part Numbers (SMT assembly only)
LCSC_C_100NF_0603 = "C14663"
LCSC_R_100K_0603 = "C25803"
LCSC_R_1K_0603 = "C21190"
LCSC_R_470R_0603 = "C23179"
LCSC_D_1N5819WS_SOD323 = "C191023"
LCSC_D_TVS_PESD12VL1BA_SOD323 = "C38558"
LCSC_U_TL074H_SOIC14 = "C2878713"


@subcircuit
def eurorack_power(vcc, vee, gnd):
    """10-pin Eurorack power input with Schottky reverse-polarity protection."""
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

    vee_raw += j_pwr[1, 2]
    gnd += j_pwr[3, 4, 5, 6, 7, 8]
    vcc_raw += j_pwr[9, 10]

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
    d_pos, d_neg = d_t(2, tag="d_prot")

    vcc_raw += d_pos["A"]
    vcc += d_pos["K"]
    vee_raw += d_neg["K"]
    vee += d_neg["A"]

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

    vcc += c_bulk_pos[1]
    gnd += c_bulk_pos[2]
    gnd += c_bulk_neg[1]
    vee += c_bulk_neg[2]


@subcircuit
def buffered_channel_1to3(vcc, vee, gnd, norm_in, buffered_tap_out, ch_num=1):
    """Single 1-to-3 buffered multiple channel built around one quad TL074H op-amp."""
    r_t = Part("Device", "R", dest=TEMPLATE, footprint=FP_R_0603)
    c_t = Part("Device", "C", dest=TEMPLATE, footprint=FP_C_0603)
    c_t.fields["LCSC"] = LCSC_C_100NF_0603
    c_t.fields["MPN"] = "CC0603KRX7R9BB104"
    c_t.fields["JLCPCB_Class"] = "Basic"

    jack_t = Part(
        "Connector_Audio",
        "AudioJack2_SwitchT",
        dest=TEMPLATE,
        footprint=FP_JACK_EURORACK,
    )
    jack_t.fields["MPN"] = "WQP-PJ398SM"
    jack_t.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"

    u = Part(
        "Amplifier_Operational",
        "TL074",
        value="TL074H",
        footprint=FP_OPAMP_SOIC14,
        tag=f"u_ch{ch_num}",
    )
    u.fields["LCSC"] = LCSC_U_TL074H_SOIC14
    u.fields["MPN"] = "TL074HIDR"
    u.fields["JLCPCB_Class"] = "Extended"

    vcc += u["V+"]
    vee += u["V-"]

    c_dec_pos, c_dec_neg = c_t(2, value="100nF", tag=f"c_dec_ch{ch_num}")
    vcc & c_dec_pos & gnd
    gnd & c_dec_neg & vee

    j_in = jack_t(value=f"IN_{ch_num}", tag=f"j_in_ch{ch_num}")
    in_jack = Net(f"CH{ch_num}_JACK_IN")
    in_sig = Net(f"CH{ch_num}_IN")

    gnd += j_in["S"]
    norm_in += j_in["TN"]
    in_jack += j_in["T"]

    d_tvs = Part(
        "Device",
        "D_TVS",
        value="PESD12VL1BA",
        footprint=FP_DIODE_SOD323,
        tag=f"d_tvs_ch{ch_num}",
    )
    d_tvs.fields["LCSC"] = LCSC_D_TVS_PESD12VL1BA_SOD323
    d_tvs.fields["MPN"] = "PESD12VL1BA,115"
    d_tvs.fields["JLCPCB_Class"] = "Extended"
    in_jack & d_tvs & gnd

    r_pd = r_t(value="100K", tag=f"r_pd_ch{ch_num}")
    r_pd.fields["LCSC"] = LCSC_R_100K_0603
    r_pd.fields["MPN"] = "0603WAF1003T5E"
    r_pd.fields["JLCPCB_Class"] = "Basic"
    in_jack & r_pd & gnd

    r_in = r_t(value="1K", tag=f"r_in_ch{ch_num}")
    r_in.fields["LCSC"] = LCSC_R_1K_0603
    r_in.fields["MPN"] = "0603WAF1001T5E"
    r_in.fields["JLCPCB_Class"] = "Basic"
    in_jack & r_in & in_sig

    in_sig += u.p[3]
    buffered_tap_out += u.p[1], u.p[2]

    output_stages = [
        ("A", 5, 6, 7),
        ("B", 10, 9, 8),
        ("C", 12, 13, 14),
    ]

    for suffix, pin_pos, pin_neg, pin_out in output_stages:
        op_out = Net(f"CH{ch_num}_OP_{suffix}")
        jack_tip = Net(f"CH{ch_num}_OUT_{suffix}")

        buffered_tap_out += u.p[pin_pos]
        op_out += u.p[pin_out], u.p[pin_neg]

        r_out = r_t(value="470R", tag=f"r_out_ch{ch_num}_{suffix}")
        r_out.fields["LCSC"] = LCSC_R_470R_0603
        r_out.fields["MPN"] = "0603WAF4700T5E"
        r_out.fields["JLCPCB_Class"] = "Basic"
        op_out & r_out & jack_tip

        j_out = jack_t(value=f"OUT_{ch_num}{suffix}", tag=f"j_out_ch{ch_num}_{suffix}")
        jack_tip += j_out["T"]
        gnd += j_out["S"]
        j_out["TN"] += builtins.NC


def parse_netlist_metadata(net_path: Path) -> dict:
    """Parse component tstamps, sheetpaths, and net classes from a KiCad `.net` file."""
    text = net_path.read_text(encoding="utf-8")
    comp_pattern = re.compile(
        r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]+)"\)'
        r'.*?\(footprint\s+"([^"]+)"\)'
        r'.*?\(name\s+"SKiDL Tag"\)\s+"([^"]+)"'
        r'.*?\(sheetpath\s+\(names\s+"([^"]+)"\)\s+\(tstamps\s+"([^"]+)"\)\)'
        r'\s+\(component_classes\)\s+\(tstamps\s+"([^"]+)"\)',
        re.DOTALL,
    )
    components = [
        {
            "ref": m.group(1),
            "value": m.group(2),
            "footprint": m.group(3),
            "skidl_tag": m.group(4),
            "sheet": m.group(5),
            "sheet_tstamp": m.group(6),
            "comp_tstamp": m.group(7),
        }
        for m in comp_pattern.finditer(text)
    ]
    net_pattern = re.compile(
        r'\(net\s+\(code\s+\d+\)\s+\(name\s+"([^"]+)"\)\s+\(class\s+"([^"]+)"\)'
    )
    nets = [
        {"name": m.group(1), "netclass": m.group(2)} for m in net_pattern.finditer(text)
    ]
    return {"components": components, "nets": nets}


def compute_4hp_jack_grid() -> list[dict]:
    """Return the 6-row x 2-column 4HP F.Cu jack placement grid (X=25/35mm)."""
    row_ys = [27.00, 40.50, 59.00, 72.50, 91.00, 104.50]
    labels = [
        ("J2", "IN_1", 1, "Left"),
        ("J3", "OUT_1A", 1, "Right"),
        ("J4", "OUT_1B", 2, "Left"),
        ("J5", "OUT_1C", 2, "Right"),
        ("J6", "IN_2", 3, "Left"),
        ("J7", "OUT_2A", 3, "Right"),
        ("J8", "OUT_2B", 4, "Left"),
        ("J9", "OUT_2C", 4, "Right"),
        ("J10", "IN_3", 5, "Left"),
        ("J11", "OUT_3A", 5, "Right"),
        ("J12", "OUT_3B", 6, "Left"),
        ("J13", "OUT_3C", 6, "Right"),
    ]
    placements = []
    for ref, val, row_idx, col_side in labels:
        x_mm = 25.00 if col_side == "Left" else 35.00
        y_mm = row_ys[row_idx - 1]
        placements.append(
            {
                "ref": ref,
                "value": val,
                "row": row_idx,
                "col": col_side,
                "x_mm": x_mm,
                "y_mm": y_mm,
                "layer": "F.Cu",
            }
        )
    return placements


def main():
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")
    for rail in (vcc, vee, gnd):
        rail.drive = POWER

    pwr_class = NetClass("Power", priority=1, trace_width=0.5, clearance=0.25)
    sig_class = NetClass("Signal", priority=2, trace_width=0.25, clearance=0.2)
    for rail in (vcc, vee, gnd):
        rail.netclasses = pwr_class

    ch1_buf = Net("CH1_BUF")
    ch2_buf = Net("CH2_BUF")
    ch3_buf = Net("CH3_BUF")
    for buf_net in (ch1_buf, ch2_buf, ch3_buf):
        buf_net.netclasses = sig_class

    eurorack_power(vcc, vee, gnd, tag="pwr")
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")
    buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")
    buffered_channel_1to3(vcc, vee, gnd, ch2_buf, ch3_buf, ch_num=3, tag="ch3")

    ERC()

    net_file = Path("buffered_multiple.net")
    csv_file = Path("layout_placement_plan.csv")
    generate_netlist(file_=str(net_file))

    meta = parse_netlist_metadata(net_file)
    parts = builtins.default_circuit.parts
    smt_parts = [p for p in parts if "THT" not in p.fields.get("JLCPCB_Class", "")]
    tht_front = [
        p for p in parts if "THT" in p.fields.get("JLCPCB_Class", "") and p.ref != "J1"
    ]
    tht_back = [p for p in parts if p.ref == "J1"]

    print("=== Lesson 0006: Netlist & 4HP PCB Assembly Partition ===")
    print(f"  Exported Netlist     : {net_file.name} ({len(meta['nets'])} nets)")
    print(f"  Total Circuit Parts  : {len(parts)}")
    print(f"  B.Cu SMT (JLCPCB)    : {len(smt_parts)} parts (all SMD on back layer)")
    print(
        f"  F.Cu THT (Bench)     : {len(tht_front)} parts (J2-J13 jacks + C1, C2 bulk)"
    )
    print(f"  B.Cu THT (Bench)     : {len(tht_back)} part  (J1 10-pin power header)")

    print("\n=== Deterministic Hierarchical tstamps (from SKiDL tag=...) ===")
    sample_refs = {"J1", "D1", "U1", "J2", "U2", "J6", "U3", "J10"}
    for comp in meta["components"]:
        if comp["ref"] in sample_refs:
            print(
                f"  {comp['ref']:<4} ({comp['value']:<18}) | sheet={comp['sheet']:<6} "
                f"| tag={comp['skidl_tag']:<10} | tstamps={comp['comp_tstamp']}"
            )

    grid = compute_4hp_jack_grid()
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["ref", "value", "row", "col", "x_mm", "y_mm", "layer"]
        )
        writer.writeheader()
        writer.writerows(grid)

    print("\n=== 4HP (20.0 x 108.0 mm) 2x6 Jack Placement Grid (F.Cu) ===")
    for item in grid:
        print(
            f"  Row {item['row']} {item['col']:<5} | {item['ref']:<4} ({item['value']:<6}) "
            f"@ X={item['x_mm']:5.2f} mm, Y={item['y_mm']:6.2f} mm [{item['layer']}]"
        )


if __name__ == "__main__":
    main()
```

### Run & Verify in Your Terminal

```bash title="Terminal · Execute inspect_netlist_and_layout.py and lint with ruff"
.venv/bin/python tutorial/apps/0006-kicad-pcb-layout-and-assembly/inspect_netlist_and_layout.py
ruff check --fix tutorial/apps/0006-kicad-pcb-layout-and-assembly/*.py
ruff format tutorial/apps/0006-kicad-pcb-layout-and-assembly/*.py
```

```bash title="Verified Output · inspect_netlist_and_layout.py" copy=false
ERC INFO: No errors or warnings found while running ERC.

=== Lesson 0006: Netlist & 4HP PCB Assembly Partition ===
  Exported Netlist     : buffered_multiple.net (32 nets)
  Total Circuit Parts  : 44
  B.Cu SMT (JLCPCB)    : 29 parts (all SMD on back layer)
  F.Cu THT (Bench)     : 14 parts (J2-J13 jacks + C1, C2 bulk)
  B.Cu THT (Bench)     : 1 part  (J1 10-pin power header)

=== Deterministic Hierarchical tstamps (from SKiDL tag=...) ===
  D1   (1N5819WS          ) | sheet=/pwr/  | tag=d_prot     | tstamps=755b79ea-9aec-515f-90f3-05736192e469
  J1   (EURORACK_PWR_10PIN) | sheet=/pwr/  | tag=j_pwr      | tstamps=3befb997-e4cd-563a-a2aa-c234de0ee318
  J10  (IN_3              ) | sheet=/ch3/  | tag=j_in_ch3   | tstamps=d591af85-83c0-55d6-851e-1dc3c89a8504
  J2   (IN_1              ) | sheet=/ch1/  | tag=j_in_ch1   | tstamps=a35debec-b72b-5399-9e88-09f481d0ad50
  J6   (IN_2              ) | sheet=/ch2/  | tag=j_in_ch2   | tstamps=3c239617-8d1a-5faf-9b1f-883128d9027a
  U1   (TL074H            ) | sheet=/ch1/  | tag=u_ch1      | tstamps=c569285a-52fc-5dd4-952c-ec299a909882
  U2   (TL074H            ) | sheet=/ch2/  | tag=u_ch2      | tstamps=466fa5c4-4c31-5383-8515-d29a76b7d0dd
  U3   (TL074H            ) | sheet=/ch3/  | tag=u_ch3      | tstamps=89c23ec5-d40f-5b0a-b500-5518e5b8e205

=== 4HP (20.0 x 108.0 mm) 2x6 Jack Placement Grid (F.Cu) ===
  Row 1 Left  | J2   (IN_1  ) @ X=25.00 mm, Y= 27.00 mm [F.Cu]
  Row 1 Right | J3   (OUT_1A) @ X=35.00 mm, Y= 27.00 mm [F.Cu]
  Row 2 Left  | J4   (OUT_1B) @ X=25.00 mm, Y= 40.50 mm [F.Cu]
  Row 2 Right | J5   (OUT_1C) @ X=35.00 mm, Y= 40.50 mm [F.Cu]
  Row 3 Left  | J6   (IN_2  ) @ X=25.00 mm, Y= 59.00 mm [F.Cu]
  Row 3 Right | J7   (OUT_2A) @ X=35.00 mm, Y= 59.00 mm [F.Cu]
  Row 4 Left  | J8   (OUT_2B) @ X=25.00 mm, Y= 72.50 mm [F.Cu]
  Row 4 Right | J9   (OUT_2C) @ X=35.00 mm, Y= 72.50 mm [F.Cu]
  Row 5 Left  | J10  (IN_3  ) @ X=25.00 mm, Y= 91.00 mm [F.Cu]
  Row 5 Right | J11  (OUT_3A) @ X=35.00 mm, Y= 91.00 mm [F.Cu]
  Row 6 Left  | J12  (OUT_3B) @ X=25.00 mm, Y=104.50 mm [F.Cu]
  Row 6 Right | J13  (OUT_3C) @ X=35.00 mm, Y=104.50 mm [F.Cu]
```

:::exercise id="ex-0006-title" title="Retrieval Practice: Deterministic Tags & SMT/THT Layer Partitioning"
Fill in the four blanks below to assign the deterministic `tag` on the power subcircuit call, export `buffered_multiple.net` via `generate_netlist()`, filter SMT parts via `part.fields`, and assign the front copper layer (`F.Cu`) to the 12 Thonkiconn jacks:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
# 1. Call eurorack_power with a deterministic hierarchical tag
eurorack_power(vcc, vee, gnd, {{blank:tag|Keyword argument that sets a deterministic hierarchical identifier: tag|Keyword argument for deterministic SKiDL tag|5}}="pwr")

# 2. Export the KiCad 10 S-expression netlist
{{blank:generate_netlist|SKiDL function that exports the KiCad .net file: generate_netlist|SKiDL function that writes the .net file|17}}(file_="buffered_multiple.net")

# 3. Partition B.Cu SMT parts from manual THT parts using part.fields
smt_parts = [
    p for p in builtins.default_circuit.parts
    if "THT" not in p.{{blank:fields|Dictionary attribute on a SKiDL Part storing custom metadata: fields|Part metadata dictionary attribute|8}}.get("JLCPCB_Class", "")
]

# 4. Place the 12 WQP-PJ398SM jacks on the panel-facing front copper layer
jack_layer = "{{blank:F.Cu|KiCad front copper layer name: F.Cu|KiCad front copper layer name|6}}"
```
:::

:::quiz id="quiz-0006-title" title="Knowledge Check"
- question: "1. Why do we pass explicit `tag=` strings (such as `tag=\"pwr\"`, `tag=\"ch1\"`, and `tag=\"u_ch1\"`) when instantiating subcircuits and parts in SKiDL?"
  options:
    - letter: A
      text: "Explicit tag strings instruct KiCad ten to autoroute every power trace on both layers."
      correct: false
      explain: "KiCad does not autoroute from SKiDL tags; routing is controlled by NetClass rules and manual or interactive routing in pcbnew."
    - letter: B
      text: "Deterministic tags generate stable hierarchical timestamps so netlist re-imports update footprints without scrambling placements."
      correct: true
      explain: "SKiDL hashes the hierarchical tag path into deterministic (tstamps ...) UUIDs inside the .net file so re-importing into pcbnew updates nets in-place without scrambling placed footprints."
    - letter: C
      text: "SKiDL requires manual string tags before any operational amplifier symbol can pass electrical checks."
      correct: false
      explain: "ERC() checks pin electrical types and net drive flags regardless of whether custom tags are provided."
    - letter: D
      text: "Assigning tags automatically converts through-hole audio connectors into surface-mount footprints during netlist file export."
      correct: false
      explain: "Footprints are set explicitly via the footprint= attribute on each Part or Template Part."
- question: "2. Why are all 29 surface-mount components placed on `B.Cu` while `J2`–`J13` and the `10uF` radial bulk capacitors (`C1`, `C2`) mount on `F.Cu`?"
  options:
    - letter: A
      text: "KiCad ten prohibits placing surface-mount resistor footprints on the same layer as plated through holes."
      correct: false
      explain: "KiCad allows mixing SMD and THT footprints on either side of the board."
    - letter: B
      text: "Mounting radial electrolytic capacitors on the back layer shorts their leads against the ribbon cable."
      correct: false
      explain: "Radial capacitor leads are trimmed after soldering; placing C1/C2 on F.Cu utilizes the 10.5mm standoff space behind the front panel."
    - letter: C
      text: "Surface-mount operational amplifiers overheat unless they face away from the aluminum front panel heat sink."
      correct: false
      explain: "Each TL074H dissipates only ~130 mW (<11°C temperature rise) and does not require a panel heat sink."
    - letter: D
      text: "Single-sided back placement enables economical automated assembly while seven-millimeter bulk capacitors fit underneath the panel."
      correct: true
      explain: "Putting all 29 SMD parts on B.Cu allows single-sided JLCPCB PCBA, while the 7mm-tall ECEA1EKS100 bulk caps sit on F.Cu inside the 10.5mm space created by the Thonkiconn jacks."
:::

:::callout-success Primary Sources & Follow-Up Questions
**Primary Sources**: [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md) · [Eurorack Power & Audio Jack Normalling Reference](../reference/eurorack-power-and-normalling.md) · [Glossary](../reference/GLOSSARY.md).<br>**Ask the Agent**: Have questions about how KiCad 10 matches `tstamps` during netlist re-import or how to position decoupling capacitors `C3`–`C8` next to `U1`–`U3` on `B.Cu`? Ask anytime—or continue to **Lesson 0007** to generate the mated 4HP Eurorack front panel in Python!
:::
