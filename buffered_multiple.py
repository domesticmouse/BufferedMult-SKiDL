#!/usr/bin/env python3
"""
Eurorack Buffered Multiple (Dual 1-to-3, Normalized to 1-to-6)
Designed with SKiDL for KiCad 10.

Architecture:
- Power Supply:
  - Standard 10-pin (2x5) through-hole Eurorack IDC power header (+/-12V, GND)
  - Reverse-polarity protection via 1N5819 / B5819W Schottky diodes (SOD-123; alt: 1N5819WS in SOD-323 if space is tight)
  - 10uF through-hole radial electrolytic bulk capacitors + 100nF 0603 ceramic decoupling caps per op-amp rail
- Channel 1 (1-to-3):
  - Input 1 jack (normalled to GND when unpatched) -> PESD12VL1BA bidirectional TVS diode + 100k pull-down -> 1k series input protection resistor -> U1A unity-gain input buffer
  - U1A buffered output drives U1B, U1C, U1D unity-gain output buffers -> 470R series protection -> Outputs 1A, 1B, 1C
  - U1A buffered output also normalizes to Channel 2 Input jack's switched tip (TN)
- Channel 2 (1-to-3, or outputs 4-6 when Input 2 is unpatched):
  - Input 2 jack (TN normalled to Channel 1 buffered signal; broken when a cable is patched into Input 2)
  - PESD12VL1BA bidirectional TVS diode + 100k pull-down -> 1k series input protection resistor -> U2A unity-gain input buffer
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
    generate_xml,
    subcircuit,
)

# Footprints (SMD passives & ICs, through-hole Eurorack jacks, power header & bulk caps)
FP_OPAMP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIODE_SOD123 = (
    "Diode_SMD:D_SOD-123"  # Alt if space gets tight: "Diode_SMD:D_SOD-323"
)
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
LCSC_D_B5819W_SOD123 = "C8598"  # CJ B5819W / 1N5819 (40V 1A Schottky SOD-123, Basic Part; Alt SOD-323: 1N5819WS / C191023)
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

    # Reverse-polarity protection Schottky diodes (1N5819 / B5819W in SOD-123; alt: 1N5819WS in SOD-323)
    d_t = Part(
        "Device",
        "D_Schottky",
        dest=TEMPLATE,
        value="1N5819",
        footprint=FP_DIODE_SOD123,
    )
    d_t.fields["LCSC"] = LCSC_D_B5819W_SOD123
    d_t.fields["MPN"] = "B5819W"
    d_t.fields["JLCPCB_Class"] = "Basic"
    d_t.fields["Notes"] = (
        "Alt smaller package if space gets tight: 1N5819WS in Diode_SMD:D_SOD-323 (LCSC C191023, Basic)"
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
    - Input jack TN pin connects to `norm_in` (GND for CH1, CH1 buffered tap for CH2)
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

    # Export KiCad Netlist (.net), XML BOM (.xml), and JLCPCB BOM (.csv)
    generate_netlist(file_="buffered_multiple.net")
    generate_xml(file_="buffered_multiple_bom.xml")
    generate_jlcpcb_bom(file_="buffered_multiple_jlcpcb_bom.csv", include_tht=False)


if __name__ == "__main__":
    build_buffered_multiple()
