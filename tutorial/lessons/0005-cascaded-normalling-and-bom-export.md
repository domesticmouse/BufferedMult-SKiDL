---
title: "Completing `buffered_multiple.py`: Cascaded Normalling (`1:3 → 1:6 → 1:9`), `NetClass` & JLCPCB BOM"
page_title: "Lesson 0005: Completing buffered_multiple.py — Cascaded Normalling, NetClass & JLCPCB BOM | Eurorack SKiDL Tutorial"
nav_id: "0005"
kicker: "Lesson 0005 · Stage 5 (255 → 334 Lines · Complete Script)"
lead: "Finish growing our Python script into the complete 334-line `buffered_multiple.py`: add automated SMT-filtered JLCPCB BOM generation, embed KiCad 10 PCB routing rules with `NetClass`, and chain three `buffered_channel_1to3` instances through their switched jack contacts."
badges:
  - text: "Script Growth: 255 → 334 Lines (44 Total Parts, 29 SMT)"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0005 · Stage 5"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "Completing `buffered_multiple.py`: Cascaded Normalling & JLCPCB BOM"
  summary: "Add `generate_jlcpcb_bom()`, assign KiCad `Power` and `Signal` `NetClass` rules, and cascade Channels 1–3 (`1:3 → 1:6 → 1:9`)."
  meta:
    - "**Code Grown**: `255 → 334 lines` (Complete `buffered_multiple.py` inline)"
    - "**Tooling Skill**: `NetClass`, SMT CSV grouping, interactive normalling simulator"
  app_dir: "./apps/0005-cascaded-normalling-and-bom-export"
pager_prev:
  href: "0004-single-buffered-channel.html"
  label: "← Previous Lesson"
  title: "0004: Growing the Script — Adding buffered_channel_1to3()"
pager_next:
  href: "0006-kicad-pcb-layout-and-assembly.html"
  label: "Next Lesson →"
  title: "0006: From .net Netlist to 4HP KiCad 10 PCB Layout & Assembly"
---

## Step 1. Add `generate_jlcpcb_bom()` for Automated SMT PCBA

In [Lesson 0004](0004-single-buffered-channel.md), we completed both `eurorack_power` and `buffered_channel_1to3`. Before we wire all three channels together, let's add a helper function `generate_jlcpcb_bom()` right below `buffered_channel_1to3`.

Personally, I love letting JLCPCB's pick-and-place machines handle the tiny `0603` passives and `SOIC-14` op-amps while I hand-solder the chunky through-hole Thonkiconn jacks, radial bulk capacitors, and 10-pin IDC power header at the bench. To order SMT-assembled boards without paying manual through-hole soldering fees, `generate_jlcpcb_bom()` iterates over `builtins.default_circuit.parts` and applies three clean transformations:

1. **Filter out THT parts by default**: Skips any component without an `LCSC` entry in `part.fields` or with `"THT"` in `part.fields.get("JLCPCB_Class", "")` when `include_tht=False`.
2. **Strip the KiCad library nickname from footprints**: `getattr(part, "footprint", "").split(":")[-1]` turns `"Resistor_SMD:R_0603_1608Metric"` into `"R_0603_1608Metric"` so JLCPCB's placement parser recognises the package immediately.
3. **Group identical `(comment, footprint, lcsc)` tuples**: Combines all 9 output resistors (`R3, R4, R5, R8, R9, R10, R13, R14, R15`) into a single CSV row under JLCPCB's required 4-column header: `Comment,Designator,Footprint,LCSC Part #`.

```python title="New Code Added · generate_jlcpcb_bom()"
def generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False):
    """
    Export a grouped JLCPCB PCBA BOM CSV (`Comment,Designator,Footprint,LCSC Part #`).
    By default, exports all SMT components with an assigned LCSC part number and
    excludes hand-soldered through-hole connectors unless `include_tht=True`.
    """
    groups = {}
    for part in builtins.default_circuit.parts:
        lcsc = part.fields.get("LCSC", "")
        jlc_class = part.fields.get("JLCPCB_Class", "")
        if not lcsc:
            continue
        if not include_tht and "THT" in jlc_class:
            continue

        comment = part.value_to_str()
        footprint = getattr(part, "footprint", "").split(":")[-1]
        key = (comment, footprint, lcsc)
        groups.setdefault(key, []).append(part.ref)

    with open(file_, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (comment, footprint, lcsc), refs in groups.items():
            writer.writerow([comment, ", ".join(refs), footprint, lcsc])
```

## Step 2. Grow the Entry Point into `build_buffered_multiple()` with `NetClass` & Cascaded Normalling

Now we replace Lesson 0004's single-channel runner with the complete top-level assembly function `build_buffered_multiple()`:

- **Assigning KiCad PCB Routing Rules with `NetClass`**: Power rails (`+12V`, `-12V`, `GND`) use wider copper traces (`0.5 mm`) and larger clearances (`0.25 mm`) than low-current analog signal nets (`0.25 mm` trace width, `0.2 mm` clearance). SKiDL's **Net Routing Class (`NetClass`)** embeds those PCB design rules directly into the exported `.net` file via `rail.netclasses = pwr_class` and `buf_net.netclasses = sig_class`.
- **Chaining Channels 1 → 2 → 3 (`1:3 → 1:6 → 1:9`)**: Because we designed `buffered_channel_1to3(vcc, vee, gnd, norm_in, buffered_tap_out, ch_num)` to accept `norm_in` (wired to the input jack's **Switched Tip Normal Contact (`TN`)**) and `buffered_tap_out` (driven by Stage A's unity-gain output), assembling the entire 3-channel cascade takes just three calls:
  1. **Channel 1**: `buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")` — When `IN_1` (`J2`) is unpatched, its `TN` switch grounds the input to `0.00V` so none of the op-amp inputs float.
  2. **Channel 2**: `buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")` — When `IN_2` (`J6`) is unpatched, its `TN` switch receives `ch1_buf` (the *buffered* output of `U1A`, not the raw `IN_1` jack tip!), cascading Channels 1 and 2 into a zero-droop **1-to-6 multiple**.
  3. **Channel 3**: `buffered_channel_1to3(vcc, vee, gnd, ch2_buf, ch3_buf, ch_num=3, tag="ch3")` — When `IN_3` (`J10`) is unpatched, its `TN` switch receives `ch2_buf` (the buffered output of `U2A`), cascading all three channels into a **1-to-9 multiple**—or splitting into `1:3 + 1:6` whenever a cable is patched into `IN_2`!

```mermaid caption="Top-level subcircuit chaining across `gnd`, `ch1_buf`, `ch2_buf`, and `ch3_buf`."
flowchart LR
  GND["GND (0.00V)"] -- "norm_in" --> CH1["Channel 1 (tag='ch1')<br/>J2.TN → U1A → OUT_1A..1C"]
  CH1 -- "ch1_buf (U1.1, U1.2)" --> CH2["Channel 2 (tag='ch2')<br/>J6.TN → U2A → OUT_2A..2C"]
  CH2 -- "ch2_buf (U2.1, U2.2)" --> CH3["Channel 3 (tag='ch3')<br/>J10.TN → U3A → OUT_3A..3C"]
  CH3 -- "ch3_buf (U3.1, U3.2)" --> END["Available for<br/>4th Channel Expansion"]
```

```python title="New Code Added · build_buffered_multiple()"
def build_buffered_multiple():
    """Assemble top-level Eurorack Buffered Multiple circuit and export KiCad files."""
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")

    # Mark power rails as driven for ERC verification
    vcc.drive = POWER
    vee.drive = POWER
    gnd.drive = POWER

    # Assign net classes for KiCad PCB layout
    pwr_class = NetClass("Power", priority=1, trace_width=0.5, clearance=0.25)
    sig_class = NetClass("Signal", priority=2, trace_width=0.25, clearance=0.2)
    for rail in (vcc, vee, gnd):
        rail.netclasses = pwr_class

    # 1. Instantiate Eurorack power supply & protection
    eurorack_power(vcc, vee, gnd, tag="pwr")

    # 2. Buffered signal nets for Channel 1, Channel 2, and Channel 3
    ch1_buf = Net("CH1_BUF")
    ch2_buf = Net("CH2_BUF")
    ch3_buf = Net("CH3_BUF")
    for buf_net in (ch1_buf, ch2_buf, ch3_buf):
        buf_net.netclasses = sig_class

    # 3. Channel 1: Input normalled to GND (0V reference when unpatched)
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")

    # 4. Channel 2: Input normalled to Channel 1's buffered signal (cascades 1-to-3 into 1-to-6)
    buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")

    # 5. Channel 3: Input normalled to Channel 2's buffered signal (cascades 1-to-6 into 1-to-9!)
    buffered_channel_1to3(vcc, vee, gnd, ch2_buf, ch3_buf, ch_num=3, tag="ch3")

    # Run Electrical Rules Check
    ERC()

    # Export KiCad Netlist (.net), XML BOM (.xml), and JLCPCB BOM (.csv)
    generate_netlist(file_="buffered_multiple.net")
    generate_xml(file_="buffered_multiple_bom.xml")
    generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False)
```

## Step 3. Interactive Cascaded Normalling Simulator

Patch or unpatch cables into `IN_1` (`J2`), `IN_2` (`J6`), and `IN_3` (`J10`) and drag the CV sliders below to test how the physical `TN` leaf-spring switches and `CH1_BUF` / `CH2_BUF` nets route signals across all 9 outputs:

{{widget:normalling-sim}}

## Step 4. The Complete 334-Line `buffered_multiple.py` Script & Outputs

And there we have it! Here is the **complete, final 334-line Python script** that we grew from an empty file in Lesson 0001—combining the pre-import environment setup, footprint/LCSC constants, `eurorack_power`, `buffered_channel_1to3`, `generate_jlcpcb_bom`, and `build_buffered_multiple` (saved at `tutorial/apps/0005-cascaded-normalling-and-bom-export/buffered_multiple.py`):

```python title="Complete Stage 5 Script · tutorial/apps/0005-cascaded-normalling-and-bom-export/buffered_multiple.py"
#!/usr/bin/env python3
"""
Lesson 0005: Cascaded Normalling (`1:3 -> 1:6 -> 1:9`), `NetClass` & JLCPCB BOM Export.

Complete 3-channel Eurorack Buffered Multiple circuit matching the root `buffered_multiple.py`,
exporting `.net`, `.xml`, and the SMT-filtered `buffered_multiple_jlcpcb_bom.csv`.
"""

import builtins
import csv
import os
from pathlib import Path

# Keep generated .erc, .log, .net, .xml, .csv, and _sklib.py files inside this lesson's app directory
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
LCSC_C_100NF_0603 = "C14663"  # YAGEO CC0603KRX7R9BB104 (50V X7R, Basic Part)
LCSC_R_100K_0603 = "C25803"  # UNI-ROYAL 0603WAF1003T5E (100k 1%, Basic Part)
LCSC_R_1K_0603 = "C21190"  # UNI-ROYAL 0603WAF1001T5E (1k 1%, Basic Part)
LCSC_R_470R_0603 = "C23179"  # UNI-ROYAL 0603WAF4700T5E (470R 1%, Basic Part)
LCSC_D_1N5819WS_SOD323 = "C191023"  # CJ 1N5819WS (40V 1A Schottky SOD-323, Basic Part; Alt SOD-123: B5819W / C8598)
LCSC_D_TVS_PESD12VL1BA_SOD323 = "C38558"  # Nexperia PESD12VL1BA,115 (12V Bidirectional TVS SOD-323, Extended Part; Alt 15V: PESD15VL1BA,115 / C85378)
LCSC_U_TL074H_SOIC14 = (
    "C2878713"  # Texas Instruments TL074HIDR (SOIC-14, Extended Part)
)


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

    # Reverse-polarity protection Schottky diodes (1N5819WS in SOD-323; alt: B5819W in SOD-123)
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


@subcircuit
def buffered_channel_1to3(vcc, vee, gnd, norm_in, buffered_tap_out, ch_num=1):
    """
    Single 1-to-3 buffered multiple channel built around one quad TL074H op-amp:
    - Unit A (pins 1, 2, 3): Unity-gain input buffer
    - Units B, C, D: Three independent unity-gain output buffers with 470R series protection
    - Input jack TN pin connects to `norm_in` (GND for CH1, CH1 buffered tap for CH2, CH2 buffered tap for CH3)
    """
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

    # Quad high-voltage CMOS/FET-input op-amp (TL074H in SOIC-14)
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

    # Op-amp power pins & local 100nF ceramic decoupling capacitors
    vcc += u["V+"]  # Pin 4
    vee += u["V-"]  # Pin 11

    c_dec_pos, c_dec_neg = c_t(2, value="100nF", tag=f"c_dec_ch{ch_num}")
    vcc & c_dec_pos & gnd
    gnd & c_dec_neg & vee

    # Input jack, bidirectional TVS ESD diode, 100k input pull-down, and 1k series input protection resistor
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
    d_tvs.fields["Notes"] = (
        "12V bidirectional low-capacitance (19pF, <50nA) ESD/TVS diode; Alt 15V: PESD15VL1BA,115 (LCSC C85378) or Basic SOD-123FL: SMF12CA (LCSC C19077508)"
    )
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

    # Stage A (Pins: + = 3, - = 2, Out = 1): Unity-gain input buffer
    in_sig += u.p[3]
    buffered_tap_out += u.p[1], u.p[2]

    # Stages B, C, D: 3 independent output buffers driving 3 output jacks via 470R resistors
    output_stages = [
        ("A", 5, 6, 7),
        ("B", 10, 9, 8),
        ("C", 12, 13, 14),
    ]

    for suffix, pin_pos, pin_neg, pin_out in output_stages:
        op_out = Net(f"CH{ch_num}_OP_{suffix}")
        jack_tip = Net(f"CH{ch_num}_OUT_{suffix}")

        # Unity-gain follower fed by the buffered input tap
        buffered_tap_out += u.p[pin_pos]
        op_out += u.p[pin_out], u.p[pin_neg]

        # Series output protection resistor (470R)
        r_out = r_t(value="470R", tag=f"r_out_ch{ch_num}_{suffix}")
        r_out.fields["LCSC"] = LCSC_R_470R_0603
        r_out.fields["MPN"] = "0603WAF4700T5E"
        r_out.fields["JLCPCB_Class"] = "Basic"
        op_out & r_out & jack_tip

        # Output jack
        j_out = jack_t(value=f"OUT_{ch_num}{suffix}", tag=f"j_out_ch{ch_num}_{suffix}")
        jack_tip += j_out["T"]
        gnd += j_out["S"]
        j_out["TN"] += builtins.NC


def generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False):
    """
    Export a grouped JLCPCB PCBA BOM CSV (`Comment,Designator,Footprint,LCSC Part #`).
    By default, exports all SMT components with an assigned LCSC part number and
    excludes hand-soldered through-hole connectors unless `include_tht=True`.
    """
    groups = {}
    for part in builtins.default_circuit.parts:
        lcsc = part.fields.get("LCSC", "")
        jlc_class = part.fields.get("JLCPCB_Class", "")
        if not lcsc:
            continue
        if not include_tht and "THT" in jlc_class:
            continue

        comment = part.value_to_str()
        footprint = getattr(part, "footprint", "").split(":")[-1]
        key = (comment, footprint, lcsc)
        groups.setdefault(key, []).append(part.ref)

    with open(file_, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (comment, footprint, lcsc), refs in groups.items():
            writer.writerow([comment, ", ".join(refs), footprint, lcsc])


def build_buffered_multiple():
    """Assemble top-level Eurorack Buffered Multiple circuit and export KiCad files."""
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")

    # Mark power rails as driven for ERC verification
    vcc.drive = POWER
    vee.drive = POWER
    gnd.drive = POWER

    # Assign net classes for KiCad PCB layout
    pwr_class = NetClass("Power", priority=1, trace_width=0.5, clearance=0.25)
    sig_class = NetClass("Signal", priority=2, trace_width=0.25, clearance=0.2)
    for rail in (vcc, vee, gnd):
        rail.netclasses = pwr_class

    # 1. Instantiate Eurorack power supply & protection
    eurorack_power(vcc, vee, gnd, tag="pwr")

    # 2. Buffered signal nets for Channel 1, Channel 2, and Channel 3
    ch1_buf = Net("CH1_BUF")
    ch2_buf = Net("CH2_BUF")
    ch3_buf = Net("CH3_BUF")
    for buf_net in (ch1_buf, ch2_buf, ch3_buf):
        buf_net.netclasses = sig_class

    # 3. Channel 1: Input normalled to GND (0V reference when unpatched)
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")

    # 4. Channel 2: Input normalled to Channel 1's buffered signal (cascades 1-to-3 into 1-to-6)
    buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")

    # 5. Channel 3: Input normalled to Channel 2's buffered signal (cascades 1-to-6 into 1-to-9!)
    buffered_channel_1to3(vcc, vee, gnd, ch2_buf, ch3_buf, ch_num=3, tag="ch3")

    # Run Electrical Rules Check
    ERC()

    # Export KiCad Netlist (.net), XML BOM (.xml), and JLCPCB BOM (.csv)
    generate_netlist(file_="buffered_multiple.net")
    generate_xml(file_="buffered_multiple_bom.xml")
    generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False)

    print("=== Complete 3-Channel Buffered Multiple Verification ===")
    print(f"  Total circuit parts  : {len(builtins.default_circuit.parts)}")
    for buf_net in (ch1_buf, ch2_buf, ch3_buf):
        sorted_pins = sorted(buf_net.pins, key=lambda p: (p.part.ref, str(p.num)))
        pins = ", ".join(f"{p.part.ref}.{p.num}" for p in sorted_pins)
        classes = ", ".join(sorted(buf_net.netclasses.keys()))
        print(f"  {buf_net.name:<8} [{classes}] -> {pins}")


if __name__ == "__main__":
    build_buffered_multiple()
```

### Run the Complete Circuit & Verify All Outputs

```bash title="Terminal · Run buffered_multiple.py and lint with ruff"
.venv/bin/python tutorial/apps/0005-cascaded-normalling-and-bom-export/buffered_multiple.py
ruff check --fix tutorial/apps/0005-cascaded-normalling-and-bom-export/*.py
ruff format tutorial/apps/0005-cascaded-normalling-and-bom-export/*.py
```

```bash title="Verified Output · buffered_multiple.py" copy=false
ERC INFO: No errors or warnings found while running ERC.

INFO: 0 errors found while generating netlist.
INFO: 0 errors found while generating XML.

=== Complete 3-Channel Buffered Multiple Verification ===
  Total circuit parts  : 44
  CH1_BUF  [Default, Signal] -> J6.TN, U1.1, U1.10, U1.12, U1.2, U1.5
  CH2_BUF  [Default, Signal] -> J10.TN, U2.1, U2.10, U2.12, U2.2, U2.5
  CH3_BUF  [Default, Signal] -> U3.1, U3.10, U3.12, U3.2, U3.5
```

```csv title="Generated CSV · buffered_multiple_jlcpcb_bom.csv (29 SMT components across 7 unique lines)"
Comment,Designator,Footprint,LCSC Part #
1N5819WS,"D1, D2",D_SOD-323,C191023
TL074H,"U1, U2, U3",SOIC-14_3.9x8.7mm_P1.27mm,C2878713
100nF,"C3, C4, C5, C6, C7, C8",C_0603_1608Metric,C14663
PESD12VL1BA,"D3, D4, D5",D_SOD-323,C38558
100K,"R1, R6, R11",R_0603_1608Metric,C25803
1K,"R2, R7, R12",R_0603_1608Metric,C21190
470R,"R3, R4, R5, R8, R9, R10, R13, R14, R15",R_0603_1608Metric,C23179
```

:::exercise id="ex-0005-title" title="Retrieval Practice: Wire the Cascaded Normalling & BOM Exporter"
Fill in the four blanks below to assign the `Power` routing class to `rail.netclasses`, pass `ch1_buf` as Channel 2's `norm_in` net, pass `ch2_buf` as Channel 3's `norm_in` net, and iterate over `builtins.default_circuit.parts` inside `generate_jlcpcb_bom()`:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
pwr_class = NetClass("Power", priority=1, trace_width=0.5, clearance=0.25)
for rail in (vcc, vee, gnd):
    rail.{{blank:netclasses|Plural attribute on a SKiDL Net for assigning NetClass rules: netclasses|Net attribute for assigning a SKiDL NetClass|11}} = pwr_class

# Cascade Channels 1 -> 2 -> 3 (1:3 -> 1:6 -> 1:9)
buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")
buffered_channel_1to3(vcc, vee, gnd, {{blank:ch1_buf|Channel 1 buffered tap net variable: ch1_buf|Buffered net from Channel 1 feeding Channel 2 norm_in|8}}, ch2_buf, ch_num=2, tag="ch2")
buffered_channel_1to3(vcc, vee, gnd, {{blank:ch2_buf|Channel 2 buffered tap net variable: ch2_buf|Buffered net from Channel 2 feeding Channel 3 norm_in|8}}, ch3_buf, ch_num=3, tag="ch3")

# Iterate all instantiated parts in the active circuit for JLCPCB BOM export
for part in builtins.{{blank:default_circuit|Active Circuit object injected into builtins: default_circuit|Active SKiDL Circuit singleton on builtins|16}}.parts:
    lcsc = part.fields.get("LCSC", "")
```
:::

:::quiz id="quiz-0005-title" title="Knowledge Check"
- question: "1. Why does Channel 2's input jack normal contact (`J6.TN`) connect to `ch1_buf` (the output of `U1A`) rather than directly to Channel 1's raw input jack tip (`CH1_JACK_IN`)?"
  options:
    - letter: A
      text: "KiCad netlists forbid connecting two switched audio jack symbols onto the same signal net."
      correct: false
      explain: "KiCad allows connecting any number of passive jack pins to a net, but doing so unbuffered loads down the source."
    - letter: B
      text: "Direct tip connections invert the phase of every downstream operational amplifier output buffer stage."
      correct: false
      explain: "All four stages in buffered_channel_1to3 are non-inverting unity-gain followers with 0° phase shift."
    - letter: C
      text: "Buffering before normalling isolates the patched source from cascaded input pull-down resistor loading droop."
      correct: true
      explain: "Normalising from U1A's low-impedance buffered output (ch1_buf) means the external CV source only ever sees Channel 1's single 100K pull-down, preventing voltage droop on 1V/Oct pitch CV."
    - letter: D
      text: "SKiDL raises a fatal routing exception whenever passive jack pins connect across subcircuit boundaries."
      correct: false
      explain: "SKiDL allows any Net passed as an argument to connect pins across @subcircuit calls."
- question: "2. Why does `generate_jlcpcb_bom()` use `part.footprint.split(\":\")[-1]` and skip components marked `Manual THT` when `include_tht=False`?"
  options:
    - letter: A
      text: "JLCPCB expects bare package names and assembles only surface-mount parts during single-sided SMT orders."
      correct: true
      explain: "JLCPCB's BOM parser expects the bare package footprint (e.g. R_0603_1608Metric) without KiCad's library prefix, and skipping THT connectors avoids manual wave/hand-soldering fees during SMT PCBA."
    - letter: B
      text: "KiCad ten deletes library colons from every footprint string whenever exporting standard XML files."
      correct: false
      explain: "KiCad's XML and .net exports retain the full <Library>:<Footprint> string."
    - letter: C
      text: "Through-hole connectors lack reference designators inside SKiDL's default circuit parts list at export time."
      correct: false
      explain: "Every instantiated Part in default_circuit.parts receives a reference designator (such as J1..J13 and C1..C2)."
    - letter: D
      text: "Splitting the footprint string automatically converts extended surface-mount components into zero-fee basic library parts."
      correct: false
      explain: "Basic vs. Extended feeder status is determined by the LCSC catalog number on JLCPCB's line, not by string splitting."
:::

:::callout-success Mission Complete & Next Custom Module Ideas
**Primary Sources**: [Eurorack Power & Audio Jack Normalling Reference](../reference/eurorack-power-and-normalling.md) · [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md) · [KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference](../reference/kicad-jlcpcb-lookup.md).<br>**Ask the Agent**: You now have the complete 334-line Python/SKiDL script grown from scratch! Want to add a precision LED polarity indicator subcircuit, adapt this script into a 4-channel DC-coupled mixer, or inspect how the `.net` file imports into KiCad 10? Ask in chat anytime!
:::
