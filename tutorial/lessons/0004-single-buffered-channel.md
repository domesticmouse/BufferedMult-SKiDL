---
title: "Growing the Script: Adding `buffered_channel_1to3()`"
page_title: "Lesson 0004: Growing the Script — Adding buffered_channel_1to3() | Eurorack SKiDL Tutorial"
nav_id: "0004"
kicker: "Lesson 0004 · Stage 4 (155 → 255 Lines)"
lead: "Take our Stage 3 power supply script and grow it by adding `@subcircuit def buffered_channel_1to3(...)` around a single quad `TL074H` op-amp: wire input ESD/TVS clamping, Stage A input buffering, three loop-generated output followers with `470R` series isolation, and `builtins.NC` on unused jack switches."
badges:
  - text: "Script Growth: 155 → 255 Lines (18 Parts)"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0004 · Stage 4"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "Growing the Script: Adding `buffered_channel_1to3()`"
  summary: "Add the 1-to-3 op-amp channel subcircuit (`TL074H`, `PESD12VL1BA` TVS diode, `U1A` input buffer, and 3 loop-generated `470R` output followers with `builtins.NC`)."
  meta:
    - "**Code Grown**: `155 → 255 lines` (Full runnable `single_channel.py` inline)"
    - "**Tooling Skill**: Series `&` operator, tuple-loop stage wiring, `builtins.NC`"
  app_dir: "./apps/0004-single-buffered-channel"
pager_prev:
  href: "0003-eurorack-power-subcircuit.html"
  label: "← Previous Lesson"
  title: "0003: Growing the Script — Adding eurorack_power()"
pager_next:
  href: "0005-cascaded-normalling-and-bom-export.html"
  label: "Next Lesson →"
  title: "0005: Completing buffered_multiple.py — Cascade & BOM"
---

## Anatomy of `buffered_channel_1to3`

In [Lesson 0003](0003-eurorack-power-subcircuit.md), our script reached 155 lines with a verified `eurorack_power(vcc, vee, gnd)` subcircuit. Now, let's add our second reusable `@subcircuit` directly below `eurorack_power`: `def buffered_channel_1to3(vcc, vee, gnd, norm_in, buffered_tap_out, ch_num=1):`.

Why do we need active buffering in a Eurorack multiple in the first place? If you passively split a `1V/Octave` pitch CV signal across three oscillator inputs using a passive ninja-star or unbuffered mult, the parallel input impedances form a slight voltage divider with the source's output resistor. Even a few millivolts of droop will pull your oscillators noticeably flat.

So, each 1-to-3 channel in our design maps all four internal operational amplifiers of one `TL074H` (`SOIC-14`) package to a two-tier buffer hierarchy:

- **Stage A (Input Follower, Pins 1, 2, 3)**: Presents a high-impedance load (`100K` pull-down) to the patched CV/audio source and produces a low-impedance buffered signal on `buffered_tap_out`.
- **Stages B, C, D (Output Followers, Pins 5–14)**: Three independent unity-gain followers driven by `buffered_tap_out`, each driving its own output jack through a `470R` series protection resistor so a short circuit or cable capacitance on one output never disturbs the other two outputs—or any downstream normalled channel.

```mermaid caption="Signal path inside `buffered_channel_1to3` showing all 14 signal/power pins of `U1` (`TL074H`)."
flowchart LR
  NORM["norm_in<br/>(GND on CH1)"] --> JIN_TN["J2: IN_1<br/>Pin TN"]
  JIN_TN -. "Normalled when<br/>unpatched" .-> JIN_T["J2: IN_1<br/>Pin T (CH1_JACK_IN)"]
  JIN_T --> PROT["D3: PESD12VL1BA TVS<br/>+ R1: 100K to GND"]
  PROT --> RIN["R2: 1K Series<br/>(CH1_IN)"]
  RIN --> U1A["U1A Follower<br/>+ (3), - (2), Out (1)"]
  U1A --> TAP["buffered_tap_out<br/>(CH1_BUF)"]
  TAP --> U1B["U1B Follower<br/>+ (5), - (6), Out (7)"] --> R3["R3: 470R"] --> J3["J3: OUT_1A<br/>(TN → builtins.NC)"]
  TAP --> U1C["U1C Follower<br/>+ (10), - (9), Out (8)"] --> R4["R4: 470R"] --> J4["J4: OUT_1B<br/>(TN → builtins.NC)"]
  TAP --> U1D["U1D Follower<br/>+ (12), - (13), Out (14)"] --> R5["R5: 470R"] --> J5["J5: OUT_1C<br/>(TN → builtins.NC)"]
```

## Step 1. Add Channel Templates, `TL074H` Power & Local Decoupling

At the top of `buffered_channel_1to3`, we define three local `TEMPLATE` blueprints (`r_t`, `c_t`, `jack_t`), instantiate the quad `TL074H` op-amp (`u`), connect its supply pins by name (`u["V+"]` and `u["V-"]`), and wire two `100nF` ceramic decoupling capacitors across the rails using SKiDL's series `&` operator:

```python title="New Code Added · buffered_channel_1to3() Part 1: Templates, TL074H & Decoupling"
@subcircuit
def buffered_channel_1to3(vcc, vee, gnd, norm_in, buffered_tap_out, ch_num=1):
    """
    Single 1-to-3 buffered multiple channel built around one quad TL074H op-amp:
    - Unit A (pins 1, 2, 3): Unity-gain input buffer
    - Units B, C, D: Three independent unity-gain output buffers with 470R series protection
    - Input jack TN pin connects to `norm_in`
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
```

## Step 2. Add the Input Jack, ESD Protection & Stage A Input Follower

Next, we wire the switched input jack (`j_in`), connecting its Sleeve (`"S"`) to `gnd`, its **Switched Tip Normal Contact (`"TN"`)** to the incoming `norm_in` net, and its Tip (`"T"`) to `in_jack`. Then we use the `&` operator to wire the `PESD12VL1BA` bidirectional TVS diode (`d_tvs`), the `100K` input pull-down (`r_pd`), and the `1K` series current-limiting resistor (`r_in`), feeding Stage A of the `TL074H` (pins `3`, `2`, `1`):

```python title="New Code Added · buffered_channel_1to3() Part 2: Input Protection & Stage A Follower"
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
```

Notice how `buffered_tap_out += u.p[1], u.p[2]` attaches *both* the op-amp output (`pin 1`) and the inverting input (`pin 2`) to `buffered_tap_out` at once—closing the unity-gain feedback loop AND feeding the downstream output stages (`u.p[5]`, `u.p[10]`, `u.p[12]`) on the same net!

## Step 3. Loop Over Output Stages B, C, D & Mark Unused Switches with `builtins.NC`

Now, here is one of my favourite moments in hardware-as-code. In a GUI schematic editor, wiring three identical output buffers means drawing, dragging, and labelling the exact same op-amp + resistor + jack cluster three times. In Python, we simply express Stages B, C, and D as a compact list of `(suffix, pin_pos, pin_neg, pin_out)` tuples and write a `for` loop:

Table: `TL074H` (`SOIC-14`) unit pin assignments in `buffered_channel_1to3`

| Op-Amp Stage | Role | Non-Inverting (`+`) | Inverting (`-`) | Output | Unity-Gain Feedback Expression |
| --- | --- | --- | --- | --- | --- |
| Unit A | Input Buffer | `u.p[3]` | `u.p[2]` | `u.p[1]` | `buffered_tap_out += u.p[1], u.p[2]` |
| Unit B (`"A"`) | Output Buffer A | `u.p[5]` | `u.p[6]` | `u.p[7]` | `op_out += u.p[7], u.p[6]` |
| Unit C (`"B"`) | Output Buffer B | `u.p[10]` | `u.p[9]` | `u.p[8]` | `op_out += u.p[8], u.p[9]` |
| Unit D (`"C"`) | Output Buffer C | `u.p[12]` | `u.p[13]` | `u.p[14]` | `op_out += u.p[14], u.p[13]` |

```python title="New Code Added · buffered_channel_1to3() Part 3: Output Stage Loop & builtins.NC"
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
```

:::callout-warn Why Output Jacks Use `j_out["TN"] += builtins.NC` (Pin on the Left)
All 12 jacks on the board use the same physical part (`WQP-PJ398SM` / `AudioJack2_SwitchT`) to keep purchasing and panel assembly simple. On the output jacks, however, the **Switched Tip Normal Contact (`TN`)** is unused. Turns out, SKiDL's **No-Connect Net (`builtins.NC`)** has two quirks worth knowing. First, it is injected into Python's `builtins` module at import time and is not exported in `skidl.__all__` (so `from skidl import NC` raises an `ImportError`). Second, if you write `builtins.NC += j_out["TN"]`, Python's augmented assignment rules reassign the attribute. Putting the pin on the left—`j_out["TN"] += builtins.NC`—reads cleanly and keeps both Python and `ruff` happy.
:::

## Step 4. Complete Stage 4 Script & Terminal Verification

Putting our Stage 3 power supply together with our new `buffered_channel_1to3` subcircuit gives us the **complete, standalone 255-line Stage 4 Python script** (saved at `tutorial/apps/0004-single-buffered-channel/single_channel.py`):

```python title="Complete Stage 4 Script · tutorial/apps/0004-single-buffered-channel/single_channel.py"
#!/usr/bin/env python3
"""
Lesson 0004: Single 1-to-3 Buffered Channel (`TL074H` & Switched Jacks).

Combines `eurorack_power` with one `buffered_channel_1to3` instance to verify:
- Op-amp power pins (`u["V+"]`, `u["V-"]`) and local 100nF ceramic decoupling (`&`)
- Input protection network (`PESD12VL1BA` TVS, `100K` pull-down, `1K` series resistor)
- Stage A unity-gain input buffer (`u.p[3]`, `u.p[1], u.p[2]`)
- Loop-generated Stages B, C, D output buffers with `470R` resistors and `builtins.NC`
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

FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD323 = "Diode_SMD:D_SOD-323"
FP_JACK_EURORACK = (
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
)
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"

LCSC_C_100NF_0603 = "C14663"
LCSC_R_100K_0603 = "C25803"
LCSC_R_1K_0603 = "C21190"
LCSC_R_470R_0603 = "C23179"
LCSC_D_1N5819WS_SOD323 = "C191023"
LCSC_D_TVS_PESD12VL1BA_SOD323 = "C38558"
LCSC_U_TL074H_SOIC14 = "C2878713"


@subcircuit
def eurorack_power(vcc, vee, gnd):
    """10-pin Eurorack power input with Schottky reverse-polarity protection and bulk caps."""
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
    """
    Single 1-to-3 buffered multiple channel built around one quad TL074H op-amp:
    - Unit A (pins 1, 2, 3): Unity-gain input buffer
    - Units B, C, D: Three independent unity-gain output buffers with 470R series protection
    - Input jack TN pin connects to `norm_in`
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


def run_single_channel():
    """Verify a single 1-to-3 buffered channel powered by `eurorack_power`."""
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")
    ch1_buf = Net("CH1_BUF")

    vcc.drive = POWER
    vee.drive = POWER
    gnd.drive = POWER

    eurorack_power(vcc, vee, gnd, tag="pwr")
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")

    ERC()
    generate_netlist(file_="single_channel.net")
    generate_xml(file_="single_channel_bom.xml")

    print("=== Single 1-to-3 Buffered Channel Verification ===")
    print(f"  Total instantiated parts : {len(builtins.default_circuit.parts)}")
    sorted_buf_pins = sorted(ch1_buf.pins, key=lambda p: (p.part.ref, int(p.num)))
    buf_pins = ", ".join(f"{p.part.ref}.{p.num}" for p in sorted_buf_pins)
    print(f"  CH1_BUF connected pins   : {buf_pins}")


if __name__ == "__main__":
    run_single_channel()
```

```bash title="Terminal · Run single_channel.py and format with ruff"
.venv/bin/python tutorial/apps/0004-single-buffered-channel/single_channel.py
ruff check --fix tutorial/apps/0004-single-buffered-channel/*.py
ruff format tutorial/apps/0004-single-buffered-channel/*.py
```

```bash title="Verified Output · single_channel.py" copy=false
ERC INFO: No errors or warnings found while running ERC.

INFO: 0 errors found while generating netlist.
INFO: 0 errors found while generating XML.

=== Single 1-to-3 Buffered Channel Verification ===
  Total instantiated parts : 18
  CH1_BUF connected pins   : U1.1, U1.2, U1.5, U1.10, U1.12
```

:::exercise id="ex-0004-title" title="Retrieval Practice: Wire the Input Protection, Follower & Output Jack"
Fill in the four blanks below to wire the input jack's switched normal contact (`"TN"`), place the `1K` input resistor in series using `&`, close Stage A's unity-gain feedback loop across pins `1` and `2`, and mark the output jack's unused `"TN"` pin as no-connect via `builtins`:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
gnd += j_in["S"]
norm_in += j_in["{{blank:TN|Two-letter pin ID for Switched Tip Normal contact: TN|Pin ID for Switched Tip Normal contact on AudioJack2_SwitchT|4}}"]
in_jack += j_in["T"]

# 1K series resistor between in_jack and in_sig
in_jack {{blank:&|Single-character SKiDL series network operator: &|SKiDL series network operator|3}} r_in & in_sig

# Stage A unity-gain follower (+ = 3, - = 2, Out = 1)
in_sig += u.p[3]
buffered_tap_out += u.p[1], u.p[{{blank:2|SOIC-14 pin number for Unit A inverting (-) input: 2|Pin number for Unit A inverting input on TL074|3}}]

# Mark output jack TN switch contact as intentionally unconnected
j_out["TN"] += builtins.{{blank:NC|Two-letter No-Connect net on builtins: NC|No-connect object on Python builtins module|4}}
```
:::

:::quiz id="quiz-0004-title" title="Knowledge Check"
- question: "1. Inside `buffered_channel_1to3`, why do we wire each output jack's unused normal contact using `j_out[\"TN\"] += builtins.NC` instead of `from skidl import NC`?"
  options:
    - letter: A
      text: "KiCad ten netlists reject any unconnected pin unless its net name starts with builtins."
      correct: false
      explain: "KiCad netlists do not require net names to start with 'builtins'; SKiDL omits NC pins from netlists after ERC passes."
    - letter: B
      text: "SKiDL injects the no-connect net into Python builtins rather than exporting it from skidl."
      correct: true
      explain: "SKiDL injects NC and default_circuit into Python's builtins namespace at import time and excludes them from skidl.__all__."
    - letter: C
      text: "Python decorators automatically delete all imported module constants inside every nested subcircuit function scope."
      correct: false
      explain: "Python decorators do not delete module-level imports; NC simply isn't in skidl.__all__."
    - letter: D
      text: "Importing NC directly from skidl shorts all unused switched jack contacts together onto ground."
      correct: false
      explain: "from skidl import NC raises an ImportError immediately rather than shorting pins to ground."
- question: "2. What does the SKiDL statement `buffered_tap_out += u.p[1], u.p[2]` accomplish on Stage A of the `TL074H` op-amp?"
  options:
    - letter: A
      text: "It connects positive and negative twelve volt supply rails directly across operational amplifier pins."
      correct: false
      explain: "Power rails on TL074 connect to pin 4 (V+) and pin 11 (V-), not pins 1 and 2."
    - letter: B
      text: "It wires two series protection resistors between the input jack tip and ground plane."
      correct: false
      explain: "Input resistors r_pd and r_in are wired using the & operator on in_jack, not u.p[1], u.p[2]."
    - letter: C
      text: "It assigns physical pins one and two into separate differential audio bus routing classes."
      correct: false
      explain: "NetClasses are assigned to Net objects via net.netclasses, not via pin tuple attachment."
    - letter: D
      text: "It ties output pin one to inverting pin two creating a unity-gain voltage follower."
      correct: true
      explain: "On TL074 Unit A, pin 1 is the output and pin 2 is the inverting (-) input; tying both to buffered_tap_out forms a unity-gain voltage follower."
:::

:::callout-success Primary Sources & Follow-Up Questions
**Primary Sources**: [SKiDL API & Pin Indexing Cheat Sheet](../reference/skidl-cheatsheet.md) · [Eurorack Power & Audio Jack Normalling Reference](../reference/eurorack-power-and-normalling.md).<br>**Ask the Agent**: Have a question about why `470R` was chosen for the output series resistors or how `PESD12VL1BA` clamps ESD spikes? Ask in chat, or continue to **Lesson 0005** to finish growing `buffered_multiple.py` with 3-channel cascaded normalling and JLCPCB BOM generation!
:::
