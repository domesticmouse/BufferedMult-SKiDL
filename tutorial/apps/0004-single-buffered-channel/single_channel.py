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

from skidl import (
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
