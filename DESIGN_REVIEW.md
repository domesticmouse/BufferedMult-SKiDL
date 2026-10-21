# Design Review: Eurorack Buffered Multiple (`BufferedMult`)

**Date:** 2026-10-21
**Project:** `BufferedMult` (SKiDL + KiCad 10, 2-Layer PCB `20.0 × 108.0 mm` / 4HP)
**Analyzers Run:** `kicad-cli pcb drc`, `analyze_pcb.py --full --proximity`, `analyze_gerbers.py`, `analyze_emc.py`, SKiDL `ERC()`
**Verdict:** **NOT READY FOR FABRICATION (2 Critical PCB Layout / DRC Open-Circuit Bugs)**

While the SKiDL circuit definition (`buffered_multiple.py`) and netlist (`buffered_multiple.net`) are electrically sound and pass ERC with zero errors, the routed PCB (`BufferedMult.kicad_pcb`) and exported manufacturing archive (`production/BufferedMult.zip`) contain **two unconnected net errors** that will prevent Channel 1 Output A (`OUT_1A`) from working and leave `U2`'s `+12V` decoupling capacitor (`C5`) disconnected from `GND`.

---

## 1. Critical Findings (Must Fix Before Ordering)

| Severity | Issue | Location / Affected Components | Impact |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **Unconnected pin on `CH1_BUF`: `U1` Pin 5 (`INB+`) is floating** | `BufferedMult.kicad_pcb` (`B.Cu`, `(29.48, 26.48)` to `(32.00, 27.50)`) | `U1B` non-inverting input (Pin 5, which drives `R2` -> `J3` / `OUT_1A`) has a short stub track stopping at `(32.00, 27.50)` and never connects to the rest of `CH1_BUF`. **`OUT_1A` (`J3`) will not output the signal** and `U1B`'s JFET input will float. |
| **CRITICAL** | **Isolated `GND` pad on `C5` Pin 2 (`U2` `+12V` bypass cap)** | `BufferedMult.kicad_pcb` (`B.Cu`, `C5` pad 2 at `(36.975, 121.44)`) | `B.Cu` tracks for `+12V` (`y = 119.54`), `CH2_IN` (`x = 38.5`), and `CH2_OP_A` (`x = 39.4`, `y = 123.81`) form a closed loop around `C5` with a `0.5 mm` zone clearance, pinching off the `B.Cu` `GND` pour. `C5` pad 2 sits on an isolated copper island with no via to `F.Cu` `GND`, **completely disabling `+12V` high-frequency decoupling for `U2`**. |

### How to Fix Both Critical PCB Issues in KiCad
1. **`CH1_BUF` (`U1` Pin 5)**: On `B.Cu`, route a `0.2 mm` track connecting `U1` Pin 5's stub at `(32.00, 27.50)` across to the main `CH1_BUF` spine at `(29.48, 26.48)` (mirroring how `CH2_BUF` is routed on `U2` at `(32.475, 121.27) -> (30.0, 121.27)`).
2. **`C5` Pad 2 (`GND`)**: Drop a `GND` stitching via (`0.6 mm` pad / `0.3 mm` drill) directly adjacent to `C5` pad 2 (around `(36.98, 122.3)`) to tie it to the solid `F.Cu` ground plane, or reduce the `GND` zone clearance from `0.5 mm` to `0.25 mm` and press `B` to refill zones.
3. Re-export the Gerbers and drill files (`production/BufferedMult.zip`).

---

## 2. Warnings & Design Recommendations

| Severity | Finding | Details & Recommendation |
| :--- | :--- | :--- |
| **WARNING** | **Duplicate overlapping `GND` zones on `B.Cu`** | `BufferedMult.kicad_pcb` defines two `GND` zones over the exact same `20.0 × 108.0 mm` outline: Zone 1 covers `["F.Cu", "B.Cu"]` (priority 0) and Zone 2 covers `["B.Cu"]` (priority 1). Change Zone 1 to `F.Cu` only and keep Zone 2 on `B.Cu` (both priority 0). |
| **WARNING** | **SKiDL `NetClass` definitions are not imported into `.kicad_pro`** | `build_buffered_multiple()` defines `Power` (`0.5 mm` width) and `Signal` (`0.25 mm` width) net classes, and writes `(class "Power,Default")` to `buffered_multiple.net`. However, `BufferedMult.kicad_pro` only defines the `Default` class (`0.2 mm` width), so `+12V` and `-12V` were routed at `0.2 mm–0.3 mm` instead of `0.5 mm`. While `0.2 mm` easily handles the `~15 mA` op-amp current thermally, widened `0.5 mm` power traces lower supply inductance. |
| **WARNING** | **Series Schottky Voltage Drop vs. Output Headroom** | Using series `1N5819` (`SS14`) diodes (`D1`, `D2`) drops approximately `0.3V–0.4V` per rail, supplying `±11.6V` to `U1`/`U2`. This is completely safe and prevents power supply shorting on reverse-plugging, though maximum unclipped output swing will be roughly `±10.1V` (standard for Eurorack). |
| **SUGGESTION** | **Input ESD / Overvoltage Clamping & RF Filtering** | If an external source patches voltages exceeding `±11.6V` into `IN_1` (`J2`) or `IN_2` (`J6`), current can flow into the `TL074` input ESD diodes without an input series resistor. Adding a small `1kΩ` series resistor between the input jack tip and `U1A`/`U2A` non-inverting input (after the `100kΩ` pull-down so there is zero voltage divider attenuation) plus a `47pF–100pF` cap to `GND` provides both RF demodulation immunity and overvoltage input current limiting. |
| **SUGGESTION** | **`TL074CDR` Input Common-Mode Range (Phase Inversion)** | Standard JFET `TL074` op-amps have a common-mode input range that stops `~3V–4V` above `V-` (`-12V`). Signals dropping below `-8V` can trigger JFET phase inversion. This is normal for `±5V` (`10Vpp`) Eurorack CV/audio, but if full rail-to-rail `±10V` signals are needed, consider Texas Instruments **`TL074H`** (`TL074HIDR`, pin-compatible SOIC-14, rail-to-rail inputs, no phase inversion). |
| **SUGGESTION** | **Capacitive Cable Loading & `470Ω` Output Resistor** | Placing `470Ω` outside the op-amp feedback loop (`R2`–`R4`, `R6`–`R8`) guarantees unconditional stability when driving long Eurorack patch cables. Note that against a standard `100kΩ` downstream module input impedance, `470Ω` introduces a `-0.47%` gain error (`~56 cents` over 10V if used for uncalibrated 1V/Oct pitch CV). For precision pitch CV buffering, `100Ω` outside the loop (or a compensated in-the-loop resistor) reduces droop, though `470Ω` matches the upstream `domesticmouse/Buffered-Mult` reference design. |
| **SUGGESTION** | **BOM CSV Selection for JLCPCB** | There are two BOM files in the repo: `buffered_multiple_jlcpcb_bom.csv` (SMT-only, clean) and `production/bom.csv` (which puts MPN strings like `ECEA1EKS100` and `WQP-PJ398SM` into the `LCSC Part #` column for THT parts). When ordering SMT assembly on JLCPCB, be sure to upload `buffered_multiple_jlcpcb_bom.csv` or mark the THT parts as DNP in KiCad before running the Fabrication Toolkit plugin. |

---

## 3. Schematic & SKiDL Code Review (`buffered_multiple.py`)

The Python SKiDL implementation is clean and well-structured:
* **Pinout & Polarity Verification**:
  * **Eurorack Power (`J1`)**: Correctly maps Pins `1, 2` to `-12V_RAW`, Pins `3–8` to `GND`, and Pins `9, 10` to `+12V_RAW`.
  * **Reverse Polarity Diodes (`D1`, `D2`)**: `D1` (`+12V`) has Anode (Pin 2) on `+12V_RAW` and Cathode (Pin 1) on `+12V`. `D2` (`-12V`) has Cathode (Pin 1) on `-12V_RAW` and Anode (Pin 2) on `-12V`. Verified against KiCad's `Device:D_Schottky` and `Diode_SMD:D_SMA` pad numbering (Pad 1 = Cathode, Pad 2 = Anode).
  * **Bulk Electrolytic Capacitors (`C1`, `C2`)**: `C1` has Pin 1 (`+`) on `+12V` and Pin 2 (`-`) on `GND`. `C2` has Pin 1 (`+`) on `GND` and Pin 2 (`-`) on `-12V`—correctly polarized since `GND` (`0V`) is positive relative to `-12V`.
  * **`TL074` Quad Op-Amps (`U1`, `U2`)**: Pin 4 (`V+`) is on `+12V`, Pin 11 (`V-`) is on `-12V`. All four stages (Unit A: `3+, 2-, 1 out`; Unit B: `5+, 6-, 7 out`; Unit C: `10+, 9-, 8 out`; Unit D: `12+, 13-, 14 out`) match the standard SOIC-14 `TL074` pinout.
  * **Normalled Cascade Routing**: `J2` (`IN_1`) normalizes `TN` to `GND` (`0V` default when unpatched). `J6` (`IN_2`) normalizes `TN` to `CH1_BUF` (the buffered output of `U1A` rather than the raw unbuffered `CH1_IN` jack), preventing any loading droop when cascading 1-to-3 into 1-to-6.
* **Minor SKiDL Log Warning**: Running `buffered_multiple.py` logs `WARNING: Missing tag on instantiated at ...` because the template parts (`d_t`, `c_bulk_t`, `r_t`, `c_t`, `jack_t`) do not pass a `tag=` when `dest=TEMPLATE` is created (even though the instantiated copies do). This is benign, as all 27 actual circuit components receive deterministic tags and UUIDs.

---

## 4. PCB & Gerber Verification Summary

| Check | Status | Notes |
| :--- | :--- | :--- |
| **Component Count** | **27 / 27 Match** | 16 SMD on `B.Cu`, 10 THT on `F.Cu` (`J2`–`J9`, `C1`, `C2`), 1 THT on `B.Cu` (`J1`) |
| **Net Count** | **21 / 21 Match** | All 21 nets in `buffered_multiple.net` match `BufferedMult.kicad_pcb` |
| **Pad-to-Net Mapping** | **27 / 27 Match** | All footprint pads match the SKiDL netlist assignments |
| **Connectivity / DRC** | **FAIL (2 Errors)** | `CH1_BUF` open stub at `U1:5`; `GND` island at `C5:2` |
| **Gerber Completeness** | **PASS (9 Layers + 2 Drills)** | `F.Cu`, `B.Cu`, `F.Mask`, `B.Mask`, `F.Paste`, `B.Paste`, `F.SilkS`, `B.SilkS`, `Edge.Cuts`, `PTH.drl`, `NPTH.drl` |
| **DFM Tier** | **JLCPCB Standard** | Min track `0.20 mm`, min spacing `0.47 mm`, min drill `0.30 mm`, min annular ring `0.15 mm` |

---

## 5. False Positives & Reviewer Overrides

The following automated analyzer findings were reviewed and confirmed to be **benign / expected** for this form factor:
* **Edge Clearance (`PM-002`) on `J1`–`J9`**: The PCB analyzer flags `J2`–`J9` at `0.0 mm` from the `20.0 × 108.0 mm` (4HP) board edge and `J1` at `0.32 mm`. For `WQP-PJ398SM` (Thonkiconn) jacks placed at `X = 25.0 mm` and `X = 35.0 mm` (`5.0 mm` from the left/right edges at `X = 20.0` and `X = 40.0`), the `10.0 mm` wide jack housing aligns flush with the `20.0 mm` board edges by design, while all copper pads sit well inside the `0.5 mm` edge clearance rule.
* **No Opposite-Layer Copper (`CP-002`) under `J1`–`J9`**: Caused by through-hole pad clearances and the `0.5 mm` zone clearance around the multi-pin connectors; not an issue.
* **Unfiltered I/O (`IO-001`)**: The EMC analyzer flags `J2`–`J9` for lacking ferrite beads or TVS diodes. For an internal analog Eurorack module with `470Ω` series output resistors, dedicated ferrite beads and TVS diodes on every 3.5mm jack are not required.

---

## 6. Not Performed / Review Limits

* **KiCad `.kicad_sch` Schematic Analyzer (`analyze_schematic.py`)**: Not applicable because the circuit is authored directly in Python via SKiDL (`buffered_multiple.py` -> `buffered_multiple.net`) with no `.kicad_sch` file. All schematic checks were performed directly against `buffered_multiple.py` and `buffered_multiple.net`.
* **SPICE Simulation (`simulate_subcircuits.py`)**: Not performed (`ngspice`, `ltspice`, and `xyce` are not installed in the local environment).
* **Distributor Lifecycle API Audit**: Not performed (offline sandbox environment).
