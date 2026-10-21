#!/usr/bin/env python3
"""
Eurorack Buffered Multiple (Dual 1-to-3, Normalized to 1-to-6)
Designed with SKiDL for KiCad 10.

Architecture:
- Power Supply:
  - Standard 10-pin (2x5) Eurorack IDC power header (+/-12V, GND)
  - Reverse-polarity protection via 1N5819 (SS14) Schottky diodes (SMA)
  - 10uF SMD electrolytic bulk capacitors + 100nF 0805 ceramic decoupling caps per op-amp rail
- Channel 1 (1-to-3):
  - Input 1 jack (normalled to GND when unpatched) -> 100k pull-down -> U1A unity-gain input buffer
  - U1A buffered output drives U1B, U1C, U1D unity-gain output buffers -> 470R series protection -> Outputs 1A, 1B, 1C
  - U1A buffered output also normalizes to Channel 2 Input jack's switched tip (TN)
- Channel 2 (1-to-3, or outputs 4-6 when Input 2 is unpatched):
  - Input 2 jack (TN normalled to Channel 1 buffered signal; broken when a cable is patched into Input 2)
  - 100k pull-down -> U2A unity-gain input buffer
  - U2A buffered output drives U2B, U2C, U2D unity-gain output buffers -> 470R series protection -> Outputs 2A, 2B, 2C
"""

import builtins
import csv
import os

# Configure writable cache directories and KiCad 10 library paths if not already set in the environment
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
    generate_svg,
    generate_xml,
    subcircuit,
)

# Footprints (SMD passives, ICs & power header, through-hole Eurorack jacks)
FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0805 = "Resistor_SMD:R_0805_2012Metric"
FP_C_0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C_ELEC = "Capacitor_SMD:CP_Elec_6.3x5.4"
FP_DIODE_SMA = "Diode_SMD:D_SMA"
FP_JACK_EURORACK = (
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
)
FP_PWR_HEADER_10P = "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical_SMD"

# Verified JLCPCB / LCSC Catalog Part Numbers
LCSC_C_100NF_0805 = "C49678"  # YAGEO CC0805KRX7R9BB104 (50V X7R, Basic Part)
LCSC_R_100K_0805 = "C149504"  # UNI-ROYAL 0805W8F1003T5E (100k 1%, Basic Part)
LCSC_R_470R_0805 = "C17710"  # UNI-ROYAL 0805W8F4700T5E (470R 1%, Basic Part)
LCSC_D_SS14_SMA = "C2480"  # MDD SS14 / 1N5819 (40V 1A Schottky SMA, Basic Part)
LCSC_U_TL074_SOIC14 = "C12594"  # Texas Instruments TL074CDR (SOIC-14, Extended Part)
LCSC_C_10UF_ELEC = "C14162"  # Honor Elec RVT1H100M0605 (10uF 50V 6.3x5.4mm, Extended)
LCSC_J_IDC_10P = (
    "C41376028"  # hanxia HX JN2.54-2x5P TP H8.9 (2x5P 2.54mm Shrouded Header, SMD)
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
    j_pwr.fields["LCSC"] = LCSC_J_IDC_10P
    j_pwr.fields["MPN"] = "HX JN2.54-2x5P TP H8.9"
    j_pwr.fields["JLCPCB_Class"] = "Extended"

    vcc_raw = Net("+12V_RAW")
    vee_raw = Net("-12V_RAW")

    # Standard 10-pin Eurorack pinout:
    # Pins 1, 2: -12V (Red stripe)
    # Pins 3..8: GND
    # Pins 9, 10: +12V
    vee_raw += j_pwr[1, 2]
    gnd += j_pwr[3, 4, 5, 6, 7, 8]
    vcc_raw += j_pwr[9, 10]

    # Reverse-polarity protection Schottky diodes (1N5819 / SS14)
    d_t = Part(
        "Device",
        "D_Schottky",
        dest=TEMPLATE,
        value="1N5819",
        footprint=FP_DIODE_SMA,
    )
    d_t.fields["LCSC"] = LCSC_D_SS14_SMA
    d_t.fields["MPN"] = "SS14"
    d_t.fields["JLCPCB_Class"] = "Basic"
    d_pos, d_neg = d_t(2, tag="d_prot")

    # +12V protection: Anode (A) at header -> Cathode (K) at +12V rail
    vcc_raw += d_pos["A"]
    vcc += d_pos["K"]

    # -12V protection: Cathode (K) at header <- Anode (A) at -12V rail
    vee_raw += d_neg["K"]
    vee += d_neg["A"]

    # Bulk electrolytic bypass capacitors (10uF / 50V)
    c_bulk_t = Part(
        "Device",
        "C_Polarized",
        dest=TEMPLATE,
        value="10uF",
        footprint=FP_C_ELEC,
    )
    c_bulk_t.fields["LCSC"] = LCSC_C_10UF_ELEC
    c_bulk_t.fields["MPN"] = "RVT1H100M0605"
    c_bulk_t.fields["JLCPCB_Class"] = "Extended"
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
    Single 1-to-3 buffered multiple channel built around one quad TL074 op-amp:
    - Unit A (pins 1, 2, 3): Unity-gain input buffer
    - Units B, C, D: Three independent unity-gain output buffers with 470R series protection
    - Input jack TN pin connects to `norm_in` (GND for CH1, CH1 buffered tap for CH2)
    """
    r_t = Part("Device", "R", dest=TEMPLATE, footprint=FP_R_0805)
    c_t = Part("Device", "C", dest=TEMPLATE, footprint=FP_C_0805)
    c_t.fields["LCSC"] = LCSC_C_100NF_0805
    c_t.fields["MPN"] = "CC0805KRX7R9BB104"
    c_t.fields["JLCPCB_Class"] = "Basic"

    jack_t = Part(
        "Connector_Audio",
        "AudioJack2_SwitchT",
        dest=TEMPLATE,
        footprint=FP_JACK_EURORACK,
    )
    jack_t.fields["MPN"] = "WQP-PJ398SM"
    jack_t.fields["JLCPCB_Class"] = "Manual THT (DNP for SMT)"

    # Quad JFET op-amp (TL074 in SOIC-14)
    u = Part(
        "Amplifier_Operational",
        "TL074",
        value="TL074",
        footprint=FP_OPAMP_SOIC14,
        tag=f"u_ch{ch_num}",
    )
    u.fields["LCSC"] = LCSC_U_TL074_SOIC14
    u.fields["MPN"] = "TL074CDR"
    u.fields["JLCPCB_Class"] = "Extended"

    # Op-amp power pins & local 100nF ceramic decoupling capacitors
    vcc += u["V+"]  # Pin 4
    vee += u["V-"]  # Pin 11

    c_dec_pos, c_dec_neg = c_t(2, value="100nF", tag=f"c_dec_ch{ch_num}")
    vcc & c_dec_pos & gnd
    gnd & c_dec_neg & vee

    # Input jack & 100k input pull-down resistor
    j_in = jack_t(value=f"IN_{ch_num}", tag=f"j_in_ch{ch_num}")
    in_sig = Net(f"CH{ch_num}_IN")

    gnd += j_in["S"]
    norm_in += j_in["TN"]
    in_sig += j_in["T"]

    r_pd = r_t(value="100K", tag=f"r_pd_ch{ch_num}")
    r_pd.fields["LCSC"] = LCSC_R_100K_0805
    r_pd.fields["MPN"] = "0805W8F1003T5E"
    r_pd.fields["JLCPCB_Class"] = "Basic"
    in_sig & r_pd & gnd

    # Stage A (Pins: + = 3, - = 2, Out = 1): Unity-gain input buffer
    in_sig += u.p[3]
    buffered_tap_out += u.p[1], u.p[2]

    # Stages B, C, D: 3 independent output buffers driving 3 output jacks via 470R resistors
    # Stage B: + = 5,  - = 6,  Out = 7
    # Stage C: + = 10, - = 9,  Out = 8
    # Stage D: + = 12, - = 13, Out = 14
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
        r_out.fields["LCSC"] = LCSC_R_470R_0805
        r_out.fields["MPN"] = "0805W8F4700T5E"
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

    # 2. Buffered signal nets for Channel 1 and Channel 2
    ch1_buf = Net("CH1_BUF")
    ch2_buf = Net("CH2_BUF")
    ch1_buf.netclasses = sig_class
    ch2_buf.netclasses = sig_class

    # 3. Channel 1: Input normalled to GND (0V reference when unpatched)
    buffered_channel_1to3(vcc, vee, gnd, gnd, ch1_buf, ch_num=1, tag="ch1")

    # 4. Channel 2: Input normalled to Channel 1's buffered signal (cascades 1-to-3 into 1-to-6!)
    buffered_channel_1to3(vcc, vee, gnd, ch1_buf, ch2_buf, ch_num=2, tag="ch2")

    # Run Electrical Rules Check
    ERC()

    # Export KiCad Netlist (.net), XML BOM (.xml), JLCPCB BOM (.csv), and SVG schematics (.svg)
    generate_netlist(file_="buffered_multiple.net")
    generate_xml(file_="buffered_multiple_bom.xml")
    generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False)
    generate_svg(filepath=".", top_name="buffered_multiple")


if __name__ == "__main__":
    build_buffered_multiple()
