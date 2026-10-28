---
title: "Automated 4HP Eurorack Front Panel Generation in Python (`+6.48 mm` Bushing Offset)"
page_title: "Lesson 0007: Automated 4HP Eurorack Front Panel Generation (+6.48 mm Bushing Offset) | Eurorack SKiDL Tutorial"
nav_id: "0007"
kicker: "Lesson 0007 · Stage 7 (Mechanical CAD-as-Code)"
lead: "Generate a mated Doepfer A-100 3U × 4HP (`20.0 × 128.5 mm`) Eurorack front panel PCB directly from Python—solving the classic `+6.48 mm` `WQP-PJ398SM` (Thonkiconn) sleeve-to-bushing mechanical offset so every `6.2 mm` panel hole aligns to the sub-millimeter with the main circuit board."
badges:
  - text: "Runnable App: generate_panel_plan.py (335 Lines)"
    style: "accent"
  - text: "✓ ERC: 0 Errors, 0 Warnings"
    style: "success"
  - text: "✓ Ruff: Clean"
    style: "success"
card:
  badge: "Lesson 0007 · Stage 7"
  status: "✓ ERC 0/0 · Ruff Clean"
  title: "Automated 4HP Eurorack Front Panel Generation (`+6.48 mm` Bushing Offset)"
  summary: "Transform main-PCB `WQP-PJ398SM` (Thonkiconn) jack coordinates into Doepfer A-100 3U × 4HP (`20 × 128.5 mm`) panel drill holes and export a standalone `.kicad_pcb` front panel in Python."
  meta:
    - "**Code Grown**: `generate_panel_plan.py` (335 lines inline + `.kicad_pcb` exporter)"
    - "**Tooling Skill**: `+6.48 mm` bushing offset math, interactive coordinate calculator, UUIDv5"
  app_dir: "./apps/0007-eurorack-front-panel-generator"
pager_prev:
  href: "0006-kicad-pcb-layout-and-assembly.html"
  label: "← Previous Lesson"
  title: "0006: From .net Netlist to 4HP KiCad 10 PCB Layout & Assembly"
pager_next:
  href: "0008-prefab-design-review-and-drc.html"
  label: "Next Lesson →"
  title: "0008: Programmatic Pre-Fab Design Review, DRC & Gerber Audit"
---

## Step 1. Doepfer A-100 3U × 4HP Geometry & the `+6.48 mm` Thonkiconn Trap

In [Lesson 0006](0006-kicad-pcb-layout-and-assembly.md), we placed our 12 vertical `WQP-PJ398SM` (Thonkiconn) jacks (`J2`–`J13`) on a `20.0 × 108.0 mm` main PCB spanning `X = 20.0..40.0 mm` and `Y = 20.0..128.0 mm`. Now we need a **3U × 4HP Eurorack Front Panel** (`20.0 × 128.5 mm` per the Doepfer A-100 standard) that mates directly over those 12 jack bushings.

If you simply drill front-panel holes at the `(X, Y)` coordinates of the jack footprints from Lesson 0006, **your front panel will not fit!** Here is why:

- **Footprint Origin `(0, 0)` vs. Bushing Shaft Center `(0, +6.48 mm)`**: Inside KiCad 10's `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` footprint, the origin `(0, 0)` is placed at **Pad `S` (Sleeve)** at the top of the jack body. The threaded M6 bushing shaft where your patch cable plugs in (`fp_circle`) sits **`+6.48 mm` lower in Y** (at `0.0, +6.48 mm` when rotation is `0°`).
- **Vertical PCB-to-Panel Centering (`10.25 mm` Rail Margin)**: Centering our `108.0 mm` tall main PCB behind a `128.5 mm` tall 3U panel leaves `(128.5 - 108.0) / 2 = 10.25 mm` of margin at both the top and bottom edges—clearing standard `~7.5 mm` Eurorack mounting rail lips with `2.75 mm` to spare. Because the main PCB starts at `(20.0, 20.0 mm)`, the top-left corner of the centered front panel sits at `(20.0, 9.75 mm)` in main-PCB coordinates.

```mermaid caption="Coordinate pipeline transforming each `WQP-PJ398SM` footprint origin into its panel-local drill coordinate."
flowchart LR
  FP["Main PCB Jack Footprint<br/>J2 Origin (Pad S)<br/>(25.00, 27.00 mm)"] -- "+ (0.00, +6.48 mm)<br/>Bushing Offset" --> BUSH["Main PCB Bushing Center<br/>M6 Shaft Axis<br/>(25.00, 33.48 mm)"]
  BUSH -- "- (20.00, 9.75 mm)<br/>Panel Top-Left Origin" --> PANEL["Panel-Local 6.2 mm Hole<br/>BufferedMult_Panel.kicad_pcb<br/>(5.00, 23.73 mm)"]
```

{{widget:panel-bushing-calc}}

## Step 2. Rotation-Aware Offset Math & Copper Shield Planes

In KiCad, footprint rotations are measured counter-clockwise (CCW) in degrees while the board's Y-axis points downward. Our helper function `rotate_offset(cx, cy, rot_deg)` rotates the local bushing vector `(0.0, 6.48)` by any footprint orientation angle, and `compute_panel_coordinates()` subtracts the panel's top-left origin `(20.0, 9.75 mm)`:

```python title="New Code Added · rotate_offset() & compute_panel_coordinates()"
def rotate_offset(cx: float, cy: float, rot_deg: float) -> tuple[float, float]:
    """Rotate a footprint-local offset (cx, cy) by KiCad's CCW rotation angle (deg)."""
    rad = math.radians(rot_deg)
    dx = cx * math.cos(rad) + cy * math.sin(rad)
    dy = -cx * math.sin(rad) + cy * math.cos(rad)
    return round(dx, 4), round(dy, 4)


def compute_panel_coordinates(jacks: list[Part]) -> tuple[float, list[dict]]:
    """
    Transform main PCB WQP-PJ398SM footprint coordinates into 4HP front panel
    bushing center coordinates in both Main-PCB and Panel-Local coordinate spaces.
    """
    rail_clearance_y = (PANEL_HEIGHT_3U_MM - MAIN_PCB_HEIGHT_MM) / 2.0
    panel_origin_x = MAIN_PCB_MIN_X_MM
    panel_origin_y = MAIN_PCB_MIN_Y_MM - rail_clearance_y  # 20.0 - 10.25 = 9.75 mm

    row_ys = [27.00, 40.50, 59.00, 72.50, 91.00, 104.50]
    dx, dy = rotate_offset(
        THONKICONN_BUSHING_OFFSET_X_MM, THONKICONN_BUSHING_OFFSET_Y_MM, rot_deg=0.0
    )
```

When fabricated as an FR-4 PCB front panel (`BufferedMult_Panel.kicad_pcb`), pouring solid copper planes across `F.Cu` and `B.Cu` with exposed rear solder-mask rings (`B.Mask`) around the `6.2 mm` jack holes gives two hardware wins for free:

1. **Automatic Chassis Shielding**: Tightening the M6 knurled jack nuts presses the grounded jack bushings against the exposed copper rings, bonding both copper planes to `GND` as a full-height Faraday shield over your op-amps.
2. **Zero Light Bleed & Extra Rigidity**: Solid dual-layer copper blocks case LEDs from shining through the fiberglass substrate and stiffens the `1.6 mm` panel against patching flex.

## Step 3. Complete Runnable Script (`generate_panel_plan.py`)

Here is the complete 335-line script in `tutorial/apps/0007-eurorack-front-panel-generator/generate_panel_plan.py`. It instantiates our 3-channel SKiDL circuit, passes `ERC()`, computes all 12 bushing and panel-local coordinates, and writes a standalone KiCad 10 front panel board file (`BufferedMult_Panel_3Ch.kicad_pcb`) with deterministic UUIDv5 identifiers:

```python title="tutorial/apps/0007-eurorack-front-panel-generator/generate_panel_plan.py (Complete 335-Line Script)"
#!/usr/bin/env python3
"""
Lesson 0007: Automated 4HP Eurorack Front Panel Generation in Python.

Builds the 3-channel Eurorack Buffered Multiple netlist, computes the +6.48 mm
WQP-PJ398SM (Thonkiconn) sleeve-to-bushing mechanical offset and Doepfer A-100
3U x 4HP (20.0 x 128.5 mm) panel-local coordinates, and exports a standalone
KiCad 10 front panel board (`BufferedMult_Panel_3Ch.kicad_pcb`).
"""

import builtins
import math
import os
import uuid
from pathlib import Path

# Keep generated .erc, .log, .kicad_pcb, and _sklib.py files inside this lesson's app directory
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
    Part,
    subcircuit,
)

# Footprints & Doepfer A-100 3U x 4HP Mechanical Constants
FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD323 = "Diode_SMD:D_SOD-323"
FP_JACK_EURORACK = (
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
)
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"

PANEL_WIDTH_4HP_MM = 20.00
PANEL_HEIGHT_3U_MM = 128.50
MAIN_PCB_MIN_X_MM = 20.00
MAIN_PCB_MIN_Y_MM = 20.00
MAIN_PCB_HEIGHT_MM = 108.00

# WQP-PJ398SM footprint origin (0, 0) is Pad S (Sleeve); M6 bushing is (0, +6.48 mm)
THONKICONN_BUSHING_OFFSET_X_MM = 0.00
THONKICONN_BUSHING_OFFSET_Y_MM = 6.48
JACK_DRILL_MM = 6.20
JACK_NUT_DIA_MM = 9.50
MOUNT_SLOT_W_MM = 5.50
MOUNT_SLOT_H_MM = 3.20


def det_uuid(namespace: str, name: str) -> str:
    """Return a deterministic UUIDv5 string for reproducible KiCad S-expressions."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"{namespace}:{name}"))


def rotate_offset(cx: float, cy: float, rot_deg: float) -> tuple[float, float]:
    """Rotate a footprint-local offset (cx, cy) by KiCad's CCW rotation angle (deg)."""
    rad = math.radians(rot_deg)
    dx = cx * math.cos(rad) + cy * math.sin(rad)
    dy = -cx * math.sin(rad) + cy * math.cos(rad)
    return round(dx, 4), round(dy, 4)


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
    jack_t = Part(
        "Connector_Audio",
        "AudioJack2_SwitchT",
        dest=TEMPLATE,
        footprint=FP_JACK_EURORACK,
    )

    u = Part(
        "Amplifier_Operational",
        "TL074",
        value="TL074H",
        footprint=FP_OPAMP_SOIC14,
        tag=f"u_ch{ch_num}",
    )
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
    in_jack & d_tvs & gnd

    r_pd = r_t(value="100K", tag=f"r_pd_ch{ch_num}")
    in_jack & r_pd & gnd

    r_in = r_t(value="1K", tag=f"r_in_ch{ch_num}")
    in_jack & r_in & in_sig

    in_sig += u.p[3]
    buffered_tap_out += u.p[1], u.p[2]

    output_stages = [("A", 5, 6, 7), ("B", 10, 9, 8), ("C", 12, 13, 14)]
    for suffix, pin_pos, pin_neg, pin_out in output_stages:
        op_out = Net(f"CH{ch_num}_OP_{suffix}")
        jack_tip = Net(f"CH{ch_num}_OUT_{suffix}")
        buffered_tap_out += u.p[pin_pos]
        op_out += u.p[pin_out], u.p[pin_neg]

        r_out = r_t(value="470R", tag=f"r_out_ch{ch_num}_{suffix}")
        op_out & r_out & jack_tip

        j_out = jack_t(value=f"OUT_{ch_num}{suffix}", tag=f"j_out_ch{ch_num}_{suffix}")
        jack_tip += j_out["T"]
        gnd += j_out["S"]
        j_out["TN"] += builtins.NC


def compute_panel_coordinates(jacks: list[Part]) -> tuple[float, list[dict]]:
    """
    Transform main PCB WQP-PJ398SM footprint coordinates into 4HP front panel
    bushing center coordinates in both Main-PCB and Panel-Local coordinate spaces.
    """
    rail_clearance_y = (PANEL_HEIGHT_3U_MM - MAIN_PCB_HEIGHT_MM) / 2.0
    panel_origin_x = MAIN_PCB_MIN_X_MM
    panel_origin_y = MAIN_PCB_MIN_Y_MM - rail_clearance_y  # 20.0 - 10.25 = 9.75 mm

    row_ys = [27.00, 40.50, 59.00, 72.50, 91.00, 104.50]
    dx, dy = rotate_offset(
        THONKICONN_BUSHING_OFFSET_X_MM, THONKICONN_BUSHING_OFFSET_Y_MM, rot_deg=0.0
    )

    records = []
    for idx, jack in enumerate(jacks):
        row_idx = idx // 2
        is_left = idx % 2 == 0
        fp_x = 25.00 if is_left else 35.00
        fp_y = row_ys[row_idx]

        bush_x = round(fp_x + dx, 2)
        bush_y = round(fp_y + dy, 2)
        panel_x = round(bush_x - panel_origin_x, 2)
        panel_y = round(bush_y - panel_origin_y, 2)
        is_input = jack.value.startswith("IN_")

        records.append(
            {
                "ref": jack.ref,
                "label": jack.value.replace("_", " "),
                "is_input": is_input,
                "fp_x": fp_x,
                "fp_y": fp_y,
                "bush_x": bush_x,
                "bush_y": bush_y,
                "panel_x": panel_x,
                "panel_y": panel_y,
            }
        )
    return rail_clearance_y, records


def export_panel_kicad_pcb(out_path: Path, records: list[dict]) -> None:
    """Write a minimal standalone KiCad 10 `.kicad_pcb` front panel file."""
    lines = [
        '(kicad_pcb (version 20240108) (generator "skidl_panel_generator")',
        '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (37 "F.SilkS" user) (44 "Edge.Cuts" user))',
        (
            f"  (gr_rect (start 0 0) (end {PANEL_WIDTH_4HP_MM:.2f} {PANEL_HEIGHT_3U_MM:.2f}) "
            f'(stroke (width 0.15) (type solid)) (fill none) (layer "Edge.Cuts") '
            f'(uuid "{det_uuid("edge", "4hp_outline")}"))'
        ),
    ]

    for slot_name, sy in [("MOUNT_TOP", 3.00), ("MOUNT_BOT", 125.50)]:
        lines.append(
            f'  (footprint "MountingHole:Slot_M3" (layer "F.Cu") (at 7.50 {sy:.2f}) '
            f'(pad "1" np_thru_hole oval (at 0 0) (size {MOUNT_SLOT_W_MM:.2f} {MOUNT_SLOT_H_MM:.2f}) '
            f'(drill oval {MOUNT_SLOT_W_MM:.2f} {MOUNT_SLOT_H_MM:.2f}) (layers "*.Cu" "*.Mask") '
            f'(uuid "{det_uuid("slot", slot_name)}")))'
        )

    for rec in records:
        u_id = det_uuid("jack_hole", rec["ref"])
        lines.append(
            f'  (footprint "Panel:JackHole_6.2mm" (layer "F.Cu") '
            f"(at {rec['panel_x']:.2f} {rec['panel_y']:.2f}) "
            f'(property "Reference" "{rec["ref"]}") '
            f'(property "Value" "{rec["label"]}") '
            f'(pad "1" thru_hole circle (at 0 0) (size 8.60 8.60) '
            f'(drill {JACK_DRILL_MM:.2f}) (layers "*.Cu" "*.Mask") (uuid "{u_id}")))'
        )

    lines.append(")")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    vcc = Net("+12V")
    vee = Net("-12V")
    gnd = Net("GND")
    for rail in (vcc, vee, gnd):
        rail.drive = POWER

    ch1_buf = Net("CH1_BUF")
    ch2_buf = Net("CH2_BUF")
    ch3_buf = Net("CH3_BUF")

    eurorack_power(vcc, vee, gnd, tag="pwr")
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")
    buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")
    buffered_channel_1to3(vcc, vee, gnd, ch2_buf, ch3_buf, ch_num=3, tag="ch3")

    ERC()

    jacks = [
        p
        for p in builtins.default_circuit.parts
        if "WQP-PJ398SM" in getattr(p, "footprint", "")
    ]
    clearance_y, records = compute_panel_coordinates(jacks)

    panel_pcb = Path("BufferedMult_Panel_3Ch.kicad_pcb")
    export_panel_kicad_pcb(panel_pcb, records)

    print("=== Lesson 0007: 4HP Eurorack Front Panel Coordinate Generator ===")
    print(
        f"  Doepfer 3U x 4HP Panel : {PANEL_WIDTH_4HP_MM:.2f} x {PANEL_HEIGHT_3U_MM:.2f} mm"
    )
    print(
        f"  Top/Bottom Rail Margin : {clearance_y:.2f} mm each "
        f"((128.5 - 108.0) / 2 = 10.25 mm)"
    )
    print(
        f"  Thonkiconn Offset      : (dX={THONKICONN_BUSHING_OFFSET_X_MM:+.2f} mm, "
        f"dY={THONKICONN_BUSHING_OFFSET_Y_MM:+.2f} mm) from Pad S to M6 Bushing"
    )
    print(
        f"  M3 Mounting Slots      : (7.50, 3.00 mm) and (7.50, 125.50 mm) "
        f"[{MOUNT_SLOT_H_MM:.1f} x {MOUNT_SLOT_W_MM:.1f} mm oval]"
    )
    print(f"  Exported Panel Board   : {panel_pcb.name} ({len(records)} jack holes)\n")

    print(
        "  Ref  | Label   | Role | Footprint (X, Y)   | Bushing (X, Y)     | Panel-Local (X, Y)"
    )
    print("  " + "-" * 83)
    for r in records:
        role = "IN *" if r["is_input"] else "OUT "
        print(
            f"  {r['ref']:<4} | {r['label']:<7} | {role} | "
            f"({r['fp_x']:5.2f}, {r['fp_y']:6.2f} mm) | "
            f"({r['bush_x']:5.2f}, {r['bush_y']:6.2f} mm) | "
            f"({r['panel_x']:5.2f}, {r['panel_y']:6.2f} mm)"
        )


if __name__ == "__main__":
    main()
```

### Run & Verify in Your Terminal

```bash title="Terminal · Execute generate_panel_plan.py and lint with ruff"
.venv/bin/python tutorial/apps/0007-eurorack-front-panel-generator/generate_panel_plan.py
ruff check --fix tutorial/apps/0007-eurorack-front-panel-generator/*.py
ruff format tutorial/apps/0007-eurorack-front-panel-generator/*.py
```

```bash title="Verified Output · generate_panel_plan.py" copy=false
ERC INFO: No errors or warnings found while running ERC.

=== Lesson 0007: 4HP Eurorack Front Panel Coordinate Generator ===
  Doepfer 3U x 4HP Panel : 20.00 x 128.50 mm
  Top/Bottom Rail Margin : 10.25 mm each ((128.5 - 108.0) / 2 = 10.25 mm)
  Thonkiconn Offset      : (dX=+0.00 mm, dY=+6.48 mm) from Pad S to M6 Bushing
  M3 Mounting Slots      : (7.50, 3.00 mm) and (7.50, 125.50 mm) [3.2 x 5.5 mm oval]
  Exported Panel Board   : BufferedMult_Panel_3Ch.kicad_pcb (12 jack holes)

  Ref  | Label   | Role | Footprint (X, Y)   | Bushing (X, Y)     | Panel-Local (X, Y)
  -----------------------------------------------------------------------------------
  J2   | IN 1    | IN * | (25.00,  27.00 mm) | (25.00,  33.48 mm) | ( 5.00,  23.73 mm)
  J3   | OUT 1A  | OUT  | (35.00,  27.00 mm) | (35.00,  33.48 mm) | (15.00,  23.73 mm)
  J4   | OUT 1B  | OUT  | (25.00,  40.50 mm) | (25.00,  46.98 mm) | ( 5.00,  37.23 mm)
  J5   | OUT 1C  | OUT  | (35.00,  40.50 mm) | (35.00,  46.98 mm) | (15.00,  37.23 mm)
  J6   | IN 2    | IN * | (25.00,  59.00 mm) | (25.00,  65.48 mm) | ( 5.00,  55.73 mm)
  J7   | OUT 2A  | OUT  | (35.00,  59.00 mm) | (35.00,  65.48 mm) | (15.00,  55.73 mm)
  J8   | OUT 2B  | OUT  | (25.00,  72.50 mm) | (25.00,  78.98 mm) | ( 5.00,  69.23 mm)
  J9   | OUT 2C  | OUT  | (35.00,  72.50 mm) | (35.00,  78.98 mm) | (15.00,  69.23 mm)
  J10  | IN 3    | IN * | (25.00,  91.00 mm) | (25.00,  97.48 mm) | ( 5.00,  87.73 mm)
  J11  | OUT 3A  | OUT  | (35.00,  91.00 mm) | (35.00,  97.48 mm) | (15.00,  87.73 mm)
  J12  | OUT 3B  | OUT  | (25.00, 104.50 mm) | (25.00, 110.98 mm) | ( 5.00, 101.23 mm)
  J13  | OUT 3C  | OUT  | (35.00, 104.50 mm) | (35.00, 110.98 mm) | (15.00, 101.23 mm)
```

:::exercise id="ex-0007-title" title="Retrieval Practice: Bushing Offset & Doepfer 3U Panel Math"
Fill in the four blanks below to define the standard Doepfer 3U panel height (`128.50 mm`), the `WQP-PJ398SM` Y bushing offset (`6.48 mm`), the recommended jack hole drill diameter (`6.20 mm`), and the panel-local Y coordinate calculation:

```python title="Interactive Python Exercise (Prism keep-markup)" copy=false
# Standard Doepfer A-100 3U panel height in millimeters
PANEL_HEIGHT_3U_MM = {{blank:128.5/128.50|Standard 3U Eurorack panel height in mm: 128.50|Doepfer 3U panel height in mm|7}}

# WQP-PJ398SM (Thonkiconn) sleeve-to-bushing offset in Y (mm)
THONKICONN_BUSHING_OFFSET_Y_MM = {{blank:6.48/+6.48|Distance in mm from Pad S (0,0) to M6 bushing shaft center: 6.48|Thonkiconn Y bushing offset in mm|6}}

# Recommended drill diameter (mm) for M6 Thonkiconn bushings
JACK_DRILL_MM = {{blank:6.2/6.20|Panel hole drill diameter in mm for 6.0mm M6 bushings: 6.20|Jack drill hole diameter in mm|6}}

# Transform main-PCB bushing Y coordinate into panel-local Y coordinate
panel_y = round(bush_y - {{blank:panel_origin_y/9.75|Variable holding the panel top edge Y coordinate (9.75 mm): panel_origin_y|Variable holding the panel top edge Y origin in main PCB space|15}}, 2)
```
:::

:::quiz id="quiz-0007-title" title="Knowledge Check"
- question: "1. Why must we add `+6.48 mm` to the Y coordinate of each vertical `WQP-PJ398SM` (Thonkiconn) jack footprint when drilling front-panel holes?"
  options:
    - letter: A
      text: "The footprint origin sits at the sleeve pad while the bushing center sits offset below."
      correct: true
      explain: "In KiCad's WQP-PJ398SM footprint, (0, 0) is Pad S (Sleeve) at the top of the housing, whereas the threaded M6 bushing center is located at (0, +6.48 mm)."
    - letter: B
      text: "KiCad ten automatically subtracts six millimeters from every non-plated drill coordinate during Excellon file generation."
      correct: false
      explain: "KiCad exports drill holes at their exact placed coordinates without subtracting any offset."
    - letter: C
      text: "Doepfer mounting rails shift every attached circuit board downward by six millimeters inside the case."
      correct: false
      explain: "The main PCB is mechanically supported by the 12 jack bushings bolted directly to the front panel, not by the case rails."
    - letter: D
      text: "Surface-mount operational amplifiers on the back layer push the audio jacks downward during reflow soldering."
      correct: false
      explain: "Reflow soldering of B.Cu SMD components happens before hand-soldering the F.Cu THT jacks and does not shift THT hole positions."
- question: "2. Why do we pour grounded `F.Cu` and `B.Cu` copper zones with exposed rear `B.Mask` rings around the jack holes on an FR-4 Eurorack front panel?"
  options:
    - letter: A
      text: "Solid copper planes double the maximum output current rating of every unity-gain follower stage."
      correct: false
      explain: "Op-amp output current is set by the TL074H output stage and 470R series resistor, not by front-panel copper."
    - letter: B
      text: "JLCPCB rejects bare fiberglass front panels unless both copper layers exceed ninety percent coverage."
      correct: false
      explain: "JLCPCB can manufacture panels with or without copper pours."
    - letter: C
      text: "Tightening the jack nuts grounds the copper planes for shielding while blocking light bleed."
      correct: true
      explain: "Exposed rear copper rings bond the panel planes to the grounded jack sleeves when the nuts are tightened, shielding the audio circuitry and blocking light bleed through the FR-4."
    - letter: D
      text: "Exposed rear solder mask rings prevent the knurled panel nuts from scratching the silkscreen."
      correct: false
      explain: "B.Mask rings are on the back surface of the panel where the jack shoulder contacts the panel, while the knurled nut sits on the front (F.Cu) face."
:::

:::callout-success Primary Sources & Follow-Up Questions
**Primary Sources**: [Eurorack Power & Audio Jack Normalling Reference](../reference/eurorack-power-and-normalling.md) · [KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference](../reference/kicad-jlcpcb-lookup.md) · [Glossary](../reference/GLOSSARY.md).<br>**Ask the Agent**: Want to add potentiometer bushing offsets or LED light-pipe cutouts to your front panel generator? Ask in chat anytime—or head to **Lesson 0008** to run a programmatic pre-fabrication design review and DRC audit!
:::
