#!/usr/bin/env python3
"""
Lesson 0002: Eurorack Power Supply `@subcircuit` & Reverse-Polarity Protection.

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
