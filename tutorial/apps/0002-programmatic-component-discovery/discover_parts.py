#!/usr/bin/env python3
"""
Lesson 0002: Programmatic Component, Pinout, Footprint & JLCPCB Discovery.

Demonstrates how to inspect KiCad 10 symbols, pin numbers/names/types, `.pretty`
footprints, and custom `part.fields` BOM metadata programmatically in Python
for the parts used in `buffered_multiple.py`.
"""

import os
from pathlib import Path

# Keep generated .erc, .log, and _sklib.py artifacts inside this lesson's app directory
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

from skidl import ERC, POWER, TEMPLATE, Net, Part

# Core symbols used in `buffered_multiple.py`
BUFFERED_MULT_SYMBOLS = [
    ("Connector_Generic", "Conn_02x05_Odd_Even", "10-pin Eurorack IDC power header"),
    ("Device", "D_Schottky", "1N5819WS reverse-polarity protection diode"),
    ("Device", "C_Polarized", "10uF radial electrolytic bulk capacitor"),
    ("Amplifier_Operational", "TL074", "TL074H quad JFET/CMOS op-amp"),
    ("Connector_Audio", "AudioJack2_SwitchT", "WQP-PJ398SM switched 3.5mm mono jack"),
    ("Device", "D_TVS", "PESD12VL1BA bidirectional ESD/TVS protection diode"),
    ("Device", "R", "0603 SMD resistor (100K, 1K, 470R)"),
    ("Device", "C", "0603 SMD ceramic decoupling capacitor (100nF)"),
]

# Target `<Library>:<FootprintName>` strings from `buffered_multiple.py`
BUFFERED_MULT_FOOTPRINTS = [
    "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "Resistor_SMD:R_0603_1608Metric",
    "Capacitor_SMD:C_0603_1608Metric",
    "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "Diode_SMD:D_SOD-323",
    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles",
    "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical",
]


def inspect_symbols():
    """Load each symbol as a TEMPLATE and print its exact pin numbers, names, and types."""
    print("=== 1. KiCad 10 Symbol & Pinout Inspection ===")
    for lib_name, sym_name, role in BUFFERED_MULT_SYMBOLS:
        part_t = Part(lib_name, sym_name, dest=TEMPLATE)
        sorted_pins = sorted(
            part_t.pins,
            key=lambda pin: (
                (0, int(pin.num)) if str(pin.num).isdigit() else (1, str(pin.num))
            ),
        )
        pins_summary = ", ".join(
            f"pin {p.num} ('{p.name}', {p.func.name})" for p in sorted_pins
        )
        print(f"\n[{lib_name}:{sym_name}] — {role}")
        print(f"  Pin count: {len(part_t.pins)}")
        print(f"  Pins     : {pins_summary}")


def verify_footprints():
    """Verify every `<Lib>:<Footprint>` resolves to a `.kicad_mod` file on disk."""
    print("\n=== 2. KiCad 10 Footprint Verification ===")
    fp_root = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", ""))
    for fp_id in BUFFERED_MULT_FOOTPRINTS:
        lib_nick, fp_name = fp_id.split(":", 1)
        mod_path = fp_root / f"{lib_nick}.pretty" / f"{fp_name}.kicad_mod"
        status = "FOUND" if mod_path.is_file() else "MISSING"
        print(f"  [{status}] {fp_id} -> {mod_path.name}")


def verify_template_fields_and_erc():
    """Demonstrate why custom BOM metadata belongs in `part.fields` and run ERC."""
    print("\n=== 3. Template Metadata (`part.fields`) & ERC Smoke Check ===")
    r_t = Part(
        "Device",
        "R",
        dest=TEMPLATE,
        value="100K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # Correct pattern: store catalog keys in `part.fields` so clones and BOM exports inherit them
    r_t.fields["LCSC"] = "C25803"
    r_t.fields["MPN"] = "0603WAF1003T5E"
    r_t.fields["JLCPCB_Class"] = "Basic"

    r_pd = r_t(tag="r_pd_test")
    d_tvs = Part(
        "Device",
        "D_TVS",
        value="PESD12VL1BA",
        footprint="Diode_SMD:D_SOD-323",
        tag="d_tvs_test",
    )
    d_tvs.fields["LCSC"] = "C38558"
    d_tvs.fields["MPN"] = "PESD12VL1BA,115"
    d_tvs.fields["JLCPCB_Class"] = "Extended"
    print(f"  Instantiated {r_pd.ref} ({r_pd.value}) with fields: {r_pd.fields}")
    print(f"  Instantiated {d_tvs.ref} ({d_tvs.value}) with fields: {d_tvs.fields}")

    in_jack = Net("CH1_JACK_IN")
    gnd = Net("GND")
    in_jack.drive = POWER
    gnd.drive = POWER
    in_jack & (d_tvs | r_pd) & gnd

    ERC()


if __name__ == "__main__":
    inspect_symbols()
    verify_footprints()
    verify_template_fields_and_erc()
