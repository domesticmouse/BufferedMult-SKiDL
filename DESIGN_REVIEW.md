# Design Review: Eurorack Buffered Multiple (`BufferedMult`)

**Date:** 2026-10-21 (Re-Review after commits `340bce0` & `4b54bfd`)
**Project:** `BufferedMult` (SKiDL + KiCad 10, 2-Layer PCB `20.0 × 108.0 mm` / 4HP)
**Analyzers Run:** `kicad-cli pcb drc`, `analyze_pcb.py --full --proximity`, `analyze_gerbers.py --full`, `analyze_emc.py`, SKiDL `ERC()`
**Verdict:** **ELECTRICAL CONNECTIVITY & COPPER CLEARANCE PASS (0 Unconnected Nets, 0 Pad-to-Track Violations); 1 Board-Edge Clearance Item (`0.35 mm` vs `0.50 mm` Rule) on `F.Cu` `-12V`**

All **two critical open-circuit bugs** (`U1` Pin 5 unconnected and `C5` Pad 2 isolated `GND`), the **three `B.Cu` pad-to-track clearance violations** (`C2` Pad 1 and `U2` Pad 12), the duplicate `B.Cu` zone warning, the narrow `0.2 mm` power trace warning, and the `TL074H` op-amp upgrade have been **resolved** in `BufferedMult.kicad_pcb` and `buffered_multiple.py` (`0` unconnected items and `0` pad/track clearance errors in DRC).

The only remaining DRC item before regenerating the Gerbers (`production/BufferedMult.zip`) is **copper-to-edge clearance on a single `F.Cu` `-12V` vertical segment** (and its two corner arcs) at `X = 20.6 mm` (`0.3500 mm` actual edge clearance vs. the `0.5000 mm` board setup constraint).

---

## 1. Previous Review Delta

| Status | Count | Summary |
| :--- | :---: | :--- |
| **Fixed since last review** | **6** | 1. **FIXED (Critical):** `U1` Pin 5 (`INB+`) is now routed to `CH1_BUF` (`0` unconnected nets).<br>2. **FIXED (Critical):** `C5` Pad 2 (`GND`) is now connected to the single unified `GND` island (12 `GND` stitching vias, up from 8).<br>3. **FIXED (Warning):** All 3 `B.Cu` pad-to-track DRC clearance errors on `-12V` (`C2` Pad 1 and `U2` Pad 12) are resolved.<br>4. **FIXED (Warning):** Duplicate `B.Cu` `GND` zone removed; Zone 1 is now `F.Cu` only and Zone 2 is `B.Cu` only.<br>5. **FIXED (Warning):** `+12V` and `-12V` power routing widened from `0.2 mm` to `0.5 mm`.<br>6. **FIXED (Suggestion):** `U1`/`U2` upgraded from `TL074CDR` (`C12594`) to TI `TL074HIDR` (`TL074H`, `C2878713`), eliminating JFET input phase inversion. |
| **Still open** | **1** | `production/BufferedMult.zip` Gerber/drill archive has not yet been re-exported since `17:08`. |
| **Remaining DRC item** | **1** | **DRC Edge Clearance (3 items on 1 trace + 2 arcs):** Widened `0.5 mm` `-12V` trace on `F.Cu` at `X = 20.6 mm` (`Y = 85.31..114.13 mm`) has `0.3500 mm` edge clearance vs. the `0.5000 mm` board setup rule. |

---

## 2. Findings & Recommendations

| Severity | Issue | Location / Affected Items | Impact & Fix |
| :--- | :--- | :--- | :--- |
| **WARNING** | **DRC Copper-to-Edge Clearance Violations (3x) on `0.5 mm` `-12V` track (`F.Cu`)** | `F.Cu` `-12V` vertical spine at `X = 20.6 mm`, `Y = 85.31..114.13 mm` (plus its top/bottom arcs at `X = 21.6, Y = 85.31` & `114.13`) vs. left board edge (`X = 20.0 mm`): **`0.3500 mm`** (rule: `0.5000 mm`) | A `0.5 mm` trace centered at `X = 20.6 mm` puts its outer copper edge `0.35 mm` from the `X = 20.0 mm` board outline (note: JLCPCB's standard routed copper-to-edge minimum is `0.30 mm`, so this is manufacturable as-is, though KiCad's board setup rule is set to `0.50 mm`). **Fix:** Either move the `F.Cu` `-12V` vertical segment from `X = 20.6 mm` inward to `X = 20.8 mm` (and refill zones), or lower *Board Setup -> Constraints -> Copper to edge clearance* from `0.5 mm` to `0.3 mm`. |
| **WARNING** | **Regenerate `production/` Fabrication Outputs When Layout is Final** | `production/BufferedMult.zip`, `positions.csv`, `netlist.ipc` (timestamp `17:08`) | Remember to re-run the KiCad Fabrication Toolkit plugin once routing adjustments are complete so `production/BufferedMult.zip` includes the updated layout. |
| **WARNING** | **Series Schottky Voltage Drop vs. Output Headroom** | `D1`, `D2` (`1N5819` / `SS14`) | Drops `~0.3V–0.4V` per rail, supplying `±11.6V` to `U1`/`U2`. Completely safe and prevents reverse-power damage; unclipped output swing with `TL074H` is `~±10.4V`. |
| **SUGGESTION** | **Input ESD / Overvoltage Current Limiting** | `J2` (`IN_1`), `J6` (`IN_2`) | `TL074H` includes internal ESD diodes to the supply rails (rated to `<10 mA`). Adding a `1kΩ` series resistor between the input jack tip (after the `100kΩ` pull-down) and Pin 3 of `U1A`/`U2A` would limit fault current if `>±12V` is patched in, without introducing any divider error. |
| **SUGGESTION** | **BOM CSV Selection for JLCPCB** | `buffered_multiple_jlcpcb_bom.csv` vs. `production/bom.csv` | Use `buffered_multiple_jlcpcb_bom.csv` for JLCPCB SMT assembly, as `production/bom.csv` includes THT parts (`C1`, `C2`, `J1`–`J9`) with MPN strings in the `LCSC Part #` column. |

---

## 3. Schematic & SKiDL Code Review (`buffered_multiple.py`)

The Python SKiDL implementation (`buffered_multiple.py`) passes `ERC()` with **0 errors and 0 warnings**:
* **Op-Amp Upgrade (`TL074HIDR`, LCSC `C2878713`)**:
  * Upgraded from standard JFET `TL074CDR` to TI's modern CMOS **`TL074H`** (`TL074HIDR`, SOIC-14).
  * **Pin-verified** against TI `TL074H` datasheet (SLOS954, D package SOIC-14): Pin 4 = `V+`, Pin 11 = `V-`, Ch1 = `(1 Out, 2 IN-, 3 IN+)`, Ch2 = `(7 Out, 6 IN-, 5 IN+)`, Ch3 = `(8 Out, 9 IN-, 10 IN+)`, Ch4 = `(14 Out, 13 IN-, 12 IN+)`.
  * Eliminates JFET phase inversion and provides low offset (`1 mV` typ), high slew rate (`20 V/µs`), and wide supply range (`4.5V` to `40V`).
* **Pinout & Polarity Verification (Raw-File Verified)**:
  * **Eurorack Power (`J1`)**: Pins `1, 2` = `-12V_RAW`, Pins `3–8` = `GND`, Pins `9, 10` = `+12V_RAW`.
  * **Reverse Polarity Diodes (`D1`, `D2`)**: `D1` (`+12V`) Anode (Pad 2) on `+12V_RAW`, Cathode (Pad 1) on `+12V`. `D2` (`-12V`) Cathode (Pad 1) on `-12V_RAW`, Anode (Pad 2) on `-12V`.
  * **Bulk Electrolytic Capacitors (`C1`, `C2`)**: `C1` Pin 1 (`+`) on `+12V`, Pin 2 (`-`) on `GND`. `C2` Pin 1 (`+`) on `GND`, Pin 2 (`-`) on `-12V`.
  * **Normalled Cascade Routing**: `J2` (`IN_1`) normalizes `TN` to `GND`. `J6` (`IN_2`) normalizes `TN` to `CH1_BUF` (the buffered output of `U1A`), preventing loading droop when cascading 1-to-3 into 1-to-6.

---

## 4. PCB & Gerber Verification Summary

| Check | Status | Notes |
| :--- | :--- | :--- |
| **Component Count** | **27 / 27 Match** | 16 SMD on `B.Cu`, 10 THT on `F.Cu` (`J2`–`J9`, `C1`, `C2`), 1 THT on `B.Cu` (`J1`) |
| **Net Count & Connectivity** | **21 / 21 Routed (PASS)** | `0` unrouted nets; `0` multi-island nets; `U1:5` and `C5:2` open-circuit bugs are fixed |
| **DRC Check (`kicad-cli`)** | **0 Pad/Track Errors; 3 Edge Errors** | `0` unconnected items; `0` copper-to-copper clearance errors; 3 copper-to-edge items (`0.350 mm` vs. `0.500 mm` rule) on the `F.Cu` `-12V` spine at `X = 20.6 mm` |
| **Power Routing** | **PASS (`0.5 mm`)** | `+12V` (`129.7 mm`) and `-12V` (`117.3 mm`) routed at `0.5 mm` width |
| **Ground Planes & Vias** | **PASS (2 Zones, 12 GND Vias)** | Dedicated `F.Cu` (`64.1%` fill) and `B.Cu` (`59.5%` fill) `GND` zones stitched with 12 `GND` vias |
| **Gerber Archive Sync** | **FAIL (Stale Archive)** | `production/BufferedMult.zip` dates from `17:08` (13 vias) and does not reflect the `20:02` PCB re-route (17 vias) |

---

## 5. False Positives & Reviewer Overrides

The following automated analyzer findings were reviewed and confirmed to be **benign / expected** for this form factor:
* **Missing Footprint Library Warnings in `kicad-cli pcb drc` (27 warnings)**: Caused by `kicad-cli` running in a sandbox without read access to `~/Library/Preferences/kicad/10.0/fp-lib-table`; all footprints are embedded directly inside `BufferedMult.kicad_pcb`.
* **Edge Clearance (`PM-002`) on `J1`–`J9`**: The PCB analyzer flags `J2`–`J9` courtyard/body at `0.0 mm` from the `20.0 × 108.0 mm` (4HP) board edge and `J1` at `0.32 mm`. For `WQP-PJ398SM` (Thonkiconn) jacks placed at `X = 25.0 mm` and `X = 35.0 mm`, the `10.0 mm` wide jack housing aligns flush with the `20.0 mm` board edges by design, while all jack pads sit well inside the board outline.
* **No Opposite-Layer Copper (`CP-002`) under `J1`–`J9`**: Caused by through-hole pad clearances and the `0.5 mm` zone clearance around the connectors; benign.
* **Unfiltered I/O (`IO-001`) & Reference Plane Gaps (`GP-001`)**: The EMC analyzer flags `J2`–`J9` for lacking ferrite beads/TVS diodes and notes reference plane apertures where THT jack clearances perforate the `20 mm` narrow strip. Expected for a 4HP analog audio/CV Eurorack module with `470Ω` series output resistors.

---

## 6. Not Performed / Review Limits

* **KiCad `.kicad_sch` Schematic Analyzer (`analyze_schematic.py`) & `cross_analysis.py` / `analyze_thermal.py`**: Not applicable because the circuit is authored directly in Python via SKiDL (`buffered_multiple.py` -> `buffered_multiple.net`) with no `.kicad_sch` file. All schematic-to-PCB cross-checks were performed directly between `buffered_multiple.py`, `buffered_multiple.net`, and `BufferedMult.kicad_pcb`. (Manual thermal check: `TL074H` quiescent current is `~5.6 mA` per quad package at `±11.6V` = `~130 mW` dissipation, or `<11°C` rise in SOIC-14.)
* **SPICE Simulation (`simulate_subcircuits.py`)**: Not performed (`ngspice`, `ltspice`, and `xyce` are not installed in the local environment).
* **Distributor Lifecycle API Audit**: Not performed (offline sandbox environment).
