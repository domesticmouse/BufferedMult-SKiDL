#!/usr/bin/env python3
"""
Lesson 0005: From .net Netlist to 4HP KiCad 10 PCB Layout & Single-Sided SMT Assembly.

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

    print("=== Lesson 0005: Netlist & 4HP PCB Assembly Partition ===")
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
