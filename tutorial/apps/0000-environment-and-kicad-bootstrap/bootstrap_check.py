#!/usr/bin/env python3
"""
Lesson 0000: Environment & KiCad 10 Bootstrap Smoke Test.

Verifies:
1. Pre-import environment variable setup for writable cache paths and KiCad 10 libraries.
2. Loading `Device:R` from KiCad 10's symbol library without `NO_LIB` errors.
3. Wiring a minimal driven circuit (`+12V` -> `100K` -> `MID` -> `100K` -> `GND`) and passing `ERC()`.
"""

import os
import sys
from pathlib import Path

# Keep generated .erc, .log, and _sklib.py artifacts inside this lesson's app directory
os.chdir(Path(__file__).resolve().parent)

# 1. Configure writable cache directories and KiCad 10 library paths BEFORE importing skidl
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

from skidl import ERC, KICAD, POWER, TEMPLATE, Net, Part, get_default_tool


def run_bootstrap_check():
    """Verify Python, SKiDL default tool, KiCad 10 paths, and a zero-warning ERC."""
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version.split()[0]}")
    print(f"SKiDL default tool: {get_default_tool()} (aliases {KICAD})")
    print(f"KICAD10_SYMBOL_DIR: {os.environ.get('KICAD10_SYMBOL_DIR', 'NOT SET')}")

    # Instantiate two 100K 0603 resistors and a 100nF bypass capacitor from templates
    r_t = Part(
        "Device",
        "R",
        dest=TEMPLATE,
        value="100K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    c_t = Part(
        "Device",
        "C",
        dest=TEMPLATE,
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r_top, r_bot = r_t(2, tag="r_boot")
    c_dec = c_t(tag="c_boot")

    vcc = Net("+12V")
    mid = Net("DIV_MID")
    gnd = Net("GND")

    # Mark external rails as POWER-driven so ERC knows they have an active source
    vcc.drive = POWER
    gnd.drive = POWER

    # Parallel bypass cap + series voltage divider (every net has >= 2 pins)
    vcc & c_dec & gnd
    vcc & r_top & mid & r_bot & gnd

    ERC()
    print(f"Verified parts    : {[p.ref for p in (r_top, r_bot, c_dec)]}")


if __name__ == "__main__":
    run_bootstrap_check()
