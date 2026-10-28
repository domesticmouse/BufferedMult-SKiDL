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
