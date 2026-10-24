# Design Review: Eurorack Buffered Multiple (`BufferedMult`)

**Date:** 2026-10-24 (Re-Review after commit `161f9ae` — 3-Channel Layout, Silkscreen Labels & Rebuilt Gerbers)
**Project:** `BufferedMult` (SKiDL + KiCad 10, 2-Layer PCB `20.0 × 109.0 mm` / 4HP, Rev `V2.0`)
**Analyzers Run:** `kicad-cli pcb drc` (stored & `--refill-zones`), `analyze_pcb.py --full --proximity`, `analyze_emc.py`, `analyze_gerbers.py --full`, `generate_eurorack_panel.py --inspect`, SKiDL `ERC()`
**Verdict:** **PASS — READY FOR FABRICATION (`0` DRC Errors, `32/32` Nets Routed, All Silkscreen Labels & `production/` Archives Up to Date)**

The 3-channel (`V2.0`) PCB layout in [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb) (`20.0 × 109.0 mm`, 44 components, 32 nets) is **100% synchronized** with the 3-channel SKiDL circuit in [`buffered_multiple.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.py) and [`buffered_multiple.net`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.net) (44/44 footprints and 135/135 pad-to-net connections verified with `0` mismatches). Running `kicad-cli pcb drc` (both stored and `--refill-zones`), [`analyze_pcb.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/.agents/skills/kicad/scripts/analyze_pcb.py) (`--full --proximity`), and [`analyze_gerbers.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/.agents/skills/kicad/scripts/analyze_gerbers.py) (`--full`) confirms **`0` DRC errors, `0` unconnected items, `0` multi-island nets, `0` crosstalk proximity pairs, and `0` Gerber findings** across both the main PCB (`production/BufferedMult.zip`) and the mated 12-jack 3U front panel ([`BufferedMult_Panel.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult_Panel.kicad_pcb) / `production/BufferedMult_Panel.zip`).

---

## 1. Previous Review Delta

| Status | Count | Summary |
| :--- | :---: | :--- |
| **Fixed / Completed since last review** | **8** | 1. **COMPLETED (3-Channel Layout Expansion):** [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb) has been expanded from 2 channels (27 components, 21 nets, `20.0 × 108.0 mm`) to the full **3-channel (`1:3 → 1:6 → 1:9`) circuit** (44 components: 29 SMD on `B.Cu`, 14 THT on `F.Cu`, 1 THT on `B.Cu`; 32 nets; `20.0 × 109.0 mm`).<br>2. **VERIFIED (100% Netlist & Pad Sync):** All 44 components and all 135 pad-to-net assignments in [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb) match [`buffered_multiple.net`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.net) with `0` discrepancies.<br>3. **VERIFIED (DRC & Zone Connectivity):** Stored and refilled zones pass `kicad-cli pcb drc` with `0` errors and `0` unconnected pads; `connectivity_graph` confirms `1` unified island for all 32 nets (including all 34 `GND` pads + 7 `GND` stitching vias).<br>4. **VERIFIED (Symmetrical 3-Channel Routing):** All three channels (`U1`, `U2`, `U3`) use identical modular placement (`14.40 mm` jack row pitch, `28.83–29.00 mm` channel stride) with local `100nF` decoupling (`3.46–4.21 mm` from IC centers) and `0.5 mm` power spines (`+12V`, `-12V`, `+12V_RAW`, `-12V_RAW`).<br>5. **FIXED (Required `-12V` Power Header Label):** Added knockout `-12V` silkscreen callout at `(29.8, 127.5 mm)` on `B.SilkS` adjacent to `J1` Pins 1 & 2 (`-12V_RAW`), plus `10uF` value labels on `F.SilkS` for `C1`/`C2`.<br>6. **FIXED (Required Project URL & Revision Labels):** Added mirrored project URL `github.com/domesticmouse/BufferedMult-SKiDL` at `(22.1, 90.3 mm)`, revision `V2.0` at `(23.7, 114.9 mm)`, and a `5 × 5 mm` `B.SilkS` block on [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb) (`silkscreen_completeness` increased from `20%` to `60%` with `board_name: true` and `revision_marking: true`).<br>7. **UPDATED (`production/` Main PCB Fabrication Files):** Rebuilt `production/BufferedMult.zip` (`20.0 × 109.0 mm`, `24` vias, `50` THT holes, `94` SMD paste apertures, `0` Gerber findings), `production/bom.csv`, `production/positions.csv`, `production/designators.csv`, and `production/netlist.ipc` in KiCad (`161f9ae`).<br>8. **UPDATED (`BufferedMult_Panel.kicad_pcb` & `production/BufferedMult_Panel.zip`):** Regenerated the mated 4HP × 3U (`20.0 × 128.5 mm`) front panel with 12 grounded `6.2 mm` PTH jack cutouts (`J2`–`J13`), 2 `3.2 × 5.5 mm` NPTH M3 mounting slots, and rear `B.SilkS` block (`0` DRC errors, `0` Gerber findings). |
| **Pre-Fab Action Items** | **0** | None — all required silkscreen labels (`-12V`, `V2.0`, `github.com/domesticmouse/BufferedMult-SKiDL`), main PCB, front panel, BOM, CPL, and Gerber archives are synchronized and ready to order. |

---

## 2. Findings & Recommendations

| Severity | Issue | Location / Affected Items | Evidence Basis & Actionable Fix |
| :--- | :--- | :--- | :--- |
| **SUGGESTION** | **BOM CSV Selection for JLCPCB SMT Assembly** | [`buffered_multiple_jlcpcb_bom.csv`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple_jlcpcb_bom.csv) vs. `production/bom.csv` | **Raw-file verified:** Use [`buffered_multiple_jlcpcb_bom.csv`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple_jlcpcb_bom.csv) (or uncheck the THT rows `C1`, `C2`, `J1`–`J13` during upload) when ordering single-sided `B.Cu` SMT assembly on JLCPCB. |
| **SUGGESTION** | **Eurorack Rail Clearance with `109.0 mm` Board Height & Top Jack Nuts** | `Edge.Cuts` (`Y = 19.0..128.0 mm`), `J2`/`J3` (`Y_panel = 18.63 mm`) | **Raw-file verified:** Centering the `109.0 mm` main PCB behind a `128.5 mm` 3U panel leaves **`9.75 mm`** top/bottom overhang (`(128.5 - 109.0) / 2`). Standard Doepfer A-100 rails clear up to `~110 mm` PCBs (`7.5 mm` rail lip), so `109.0 mm` fits with `~0.5–1.0 mm` margin per side, though cases with tall sliding-nut brackets can be tight above `108 mm`. On the front panel, Row 1 bushings (`J2`, `J3`) sit at `Y_panel = 18.63 mm` (nut top edge `~13.88 mm`, clearing the `~11.0 mm` rail lip by `2.88 mm`). |
| **SUGGESTION** | **Additional `GND` Stitching Vias in Channel 3 & Power Entry Area** | `GND` zones (`Y = 75..128 mm`) | **Analyzer-derived:** Of the 7 `GND` stitching vias, 3 are in Ch 1 (`Y = 24.7–29.3 mm`), 3 are in Ch 2 (`Y = 53.7–58.6 mm`), and 1 is in Ch 3 (`(31.1, 86.9 mm)`). While the 15 THT `GND` pads (`J2`–`J13` sleeves, `C1:2`, `C2:1`, `J1:3..8`) stitch `F.Cu` and `B.Cu` solidly across the entire board (`1` island), adding 2–3 `GND` vias near `U3` / `D5` would match Ch 1/Ch 2 via density. |
| **INFO** | **Series Schottky Voltage Drop vs. Output Headroom** | `D1`, `D2` (`1N5819WS`) | **Datasheet / topology derived:** Drops `~0.3V–0.4V` per rail, supplying `±11.6V` to `U1`–`U3`. Unclipped output swing with `TL074H` is `~±10.4V`. |

---

## 3. Component Summary & Power Tree

### Component Breakdown (`44` Total Components)

| Category | Qty | References | Value / MPN | Footprint | Mount Side | LCSC Part # (Class) |
| :--- | :-: | :--- | :--- | :--- | :---: | :--- |
| **Quad Op-Amp (IC)** | 3 | `U1`, `U2`, `U3` | `TL074H` (`TL074HIDR`) | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` | `B.Cu` (SMD) | `C2878713` (Extended) |
| **Schottky Diode** | 2 | `D1`, `D2` | `1N5819WS` | `Diode_SMD:D_SOD-323` | `B.Cu` (SMD) | `C191023` (Basic) |
| **ESD/TVS Diode** | 3 | `D3`, `D4`, `D5` | `PESD12VL1BA` (`PESD12VL1BA,115`) | `Diode_SMD:D_SOD-323` | `B.Cu` (SMD) | `C38558` (Extended) |
| **Ceramic Capacitor** | 6 | `C3`–`C8` | `100nF` (`CC0603KRX7R9BB104`) | `Capacitor_SMD:C_0603_1608Metric` | `B.Cu` (SMD) | `C14663` (Basic) |
| **Input Pull-Down Resistor** | 3 | `R1`, `R6`, `R11` | `100K` (`0603WAF1003T5E`) | `Resistor_SMD:R_0603_1608Metric` | `B.Cu` (SMD) | `C25803` (Basic) |
| **Input Series Resistor** | 3 | `R2`, `R7`, `R12` | `1K` (`0603WAF1001T5E`) | `Resistor_SMD:R_0603_1608Metric` | `B.Cu` (SMD) | `C21190` (Basic) |
| **Output Series Resistor** | 9 | `R3`–`R5`, `R8`–`R10`, `R13`–`R15` | `470R` (`0603WAF4700T5E`) | `Resistor_SMD:R_0603_1608Metric` | `B.Cu` (SMD) | `C23179` (Basic) |
| **Bulk Electrolytic Cap** | 2 | `C1`, `C2` | `10uF` (`ECEA1EKS100`) | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm` | `F.Cu` (THT) | Hand-soldered (DNP for SMT) |
| **3.5mm Switched Jack** | 12 | `J2`–`J13` | `IN_1`..`OUT_3C` (`WQP-PJ398SM`) | `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | `F.Cu` (THT) | Hand-soldered (DNP for SMT) |
| **Eurorack Power Header** | 1 | `J1` | `EURORACK_PWR_10PIN` | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | `B.Cu` (THT) | Hand-soldered (DNP for SMT) |

* **One-Line Stats:** `44` components (`29` SMD on `B.Cu`, `15` THT), `32` nets (`5` power/ground, `27` signal), `135` connected pins, `13` intentional no-connects (`J3`–`J5`, `J7`–`J9`, `J11`–`J13` `TN` pins).
* **Sourcing Coverage:** `43/44` components (`97.7%`) have explicit MPNs (`J1` is a standard generic `2x5` `2.54 mm` shrouded IDC header); `29/29` (`100%`) of SMT components have verified LCSC part numbers in [`buffered_multiple_jlcpcb_bom.csv`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple_jlcpcb_bom.csv) (`5` Basic lines, `2` Extended lines).

### Power Tree

```text
J1 (EURORACK_PWR_10PIN, 2x5 IDC Header on B.Cu)
├── Pins 9, 10 (+12V_RAW) ──► D1 (1N5819WS, A=2 → K=1) ──► +12V (~+11.6V)
│                             ├── C1 (10uF Electrolytic, + = Pin 1, - = Pin 2 to GND)
│                             ├── C3 (100nF 0603) + U1 Pin 4 (V+) [Channel 1 TL074H]
│                             ├── C5 (100nF 0603) + U2 Pin 4 (V+) [Channel 2 TL074H]
│                             └── C7 (100nF 0603) + U3 Pin 4 (V+) [Channel 3 TL074H]
├── Pins 3–8 (GND) ─────────► F.Cu & B.Cu GND Pours (34 GND pads + 7 GND stitching vias)
└── Pins 1, 2 (-12V_RAW) ───► D2 (1N5819WS, K=1 ◄── A=2) ──► -12V (~-11.6V)
                              ├── C2 (10uF Electrolytic, + = Pin 1 to GND, - = Pin 2)
                              ├── C4 (100nF 0603) + U1 Pin 11 (V-) [Channel 1 TL074H]
                              ├── C6 (100nF 0603) + U2 Pin 11 (V-) [Channel 2 TL074H]
                              └── C8 (100nF 0603) + U3 Pin 11 (V-) [Channel 3 TL074H]
```

---

## 4. Netlist ↔ PCB Cross-Verification & Pinout Audit

Every component, footprint, pin number, and physical pad assignment was cross-checked between [`buffered_multiple.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.py), [`buffered_multiple.net`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.net), and [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb):

### Component & Pad-to-Net Verification (`44/44` Components, `135/135` Pads Match)

| Ref | Value / MPN | Footprint | Pads | Verification Basis & Pin/Pad Mapping | Status |
| :--- | :--- | :--- | :-: | :--- | :---: |
| `U1`–`U3` | `TL074H` (`TL074HIDR`) | `SOIC-14_3.9x8.7mm_P1.27mm` | 14 | **Raw-file + TI SLOS954 D-pkg pinout:** `4=+12V (V+)`, `11=-12V (V-)`, Stage A: `3=CHn_IN (IN1+)`, `1,2=CHn_BUF (OUT1/IN1-)`; Stage B: `5=CHn_BUF (IN2+)`, `6,7=CHn_OP_A (IN2-/OUT2)`; Stage C: `10=CHn_BUF (IN3+)`, `8,9=CHn_OP_B (OUT3/IN3-)`; Stage D: `12=CHn_BUF (IN4+)`, `13,14=CHn_OP_C (IN4-/OUT4)` | **PASS** |
| `J1` | `EURORACK_PWR_10PIN` | `IDC-Header_2x05_P2.54mm_Vertical` | 10 | **Raw-file + Doepfer A-100 standard:** `1,2=-12V_RAW`, `3..8=GND`, `9,10=+12V_RAW` | **PASS** |
| `D1` | `1N5819WS` | `D_SOD-323` | 2 | **Raw-file + KiCad SOD-323 standard:** `Pad 2 (A)=+12V_RAW`, `Pad 1 (K)=+12V` | **PASS** |
| `D2` | `1N5819WS` | `D_SOD-323` | 2 | **Raw-file + KiCad SOD-323 standard:** `Pad 1 (K)=-12V_RAW`, `Pad 2 (A)=-12V` | **PASS** |
| `D3`–`D5` | `PESD12VL1BA,115` | `D_SOD-323` | 2 | **Raw-file verified (bidirectional TVS):** `Pad 1=CHn_JACK_IN`, `Pad 2=GND` | **PASS** |
| `C1` | `10uF` (`ECEA1EKS100`) | `CP_Radial_D5.0mm_P2.00mm` | 2 | **Raw-file verified (polarized radial):** `Pad 1 (+, rect)=+12V`, `Pad 2 (-, circle)=GND` | **PASS** |
| `C2` | `10uF` (`ECEA1EKS100`) | `CP_Radial_D5.0mm_P2.00mm` | 2 | **Raw-file verified (polarized radial):** `Pad 1 (+, rect)=GND`, `Pad 2 (-, circle)=-12V` | **PASS** |
| `C3`, `C5`, `C7` | `100nF` (`CC0603KRX7R9BB104`) | `C_0603_1608Metric` | 2 | **Raw-file verified (`+12V` local decoupling):** `Pad 1=+12V`, `Pad 2=GND` | **PASS** |
| `C4`, `C6`, `C8` | `100nF` (`CC0603KRX7R9BB104`) | `C_0603_1608Metric` | 2 | **Raw-file verified (`-12V` local decoupling):** `Pad 1=GND`, `Pad 2=-12V` | **PASS** |
| `J2`, `J6`, `J10` | `IN_1`, `IN_2`, `IN_3` (`WQP-PJ398SM`) | `Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | 3 | **Raw-file verified:** `S=GND`, `T=CHn_JACK_IN`, `TN=GND` (`J2`), `CH1_BUF` (`J6`), `CH2_BUF` (`J10`) | **PASS** |
| `J3`–`J5`, `J7`–`J9`, `J11`–`J13` | `OUT_1A`..`OUT_3C` (`WQP-PJ398SM`) | `Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | 3 | **Raw-file verified:** `S=GND`, `T=CHn_OUT_A..C`, `TN=unconnected` | **PASS** |
| `R1`, `R6`, `R11` | `100K` (`0603WAF1003T5E`) | `R_0603_1608Metric` | 2 | **Raw-file verified (input pull-down):** `Pad 1=CHn_JACK_IN`, `Pad 2=GND` | **PASS** |
| `R2`, `R7`, `R12` | `1K` (`0603WAF1001T5E`) | `R_0603_1608Metric` | 2 | **Raw-file verified (input series protection):** `Pad 1=CHn_JACK_IN`, `Pad 2=CHn_IN` | **PASS** |
| `R3`–`R5`, `R8`–`R10`, `R13`–`R15` | `470R` (`0603WAF4700T5E`) | `R_0603_1608Metric` | 2 | **Raw-file verified (output series protection):** `Pad 1=CHn_OP_A..C`, `Pad 2=CHn_OUT_A..C` | **PASS** |

---

## 5. PCB Layout, Signal Integrity, Power & EMC Analysis

### Board Overview & Placement Geometry
* **Dimensions & Stackup:** `20.0 × 109.0 mm` (`2180.0 mm²`, `X = 20.0..40.0 mm`, `Y = 19.0..128.0 mm`), 2 copper layers (`F.Cu`, `B.Cu`), `1.6 mm` FR-4 thickness.
* **Assembly Split:**
  * **Front Side (`F.Cu`, 14 THT parts, 0 SMD):** 12× Thonkiconn jacks (`J2`–`J13`) arranged on a uniform 2-column × 6-row grid (`X = 25.00 mm` and `35.00 mm`, `Y = 21.40, 35.80, 50.20, 64.60, 79.00, 93.40 mm` — `14.40 mm` vertical row pitch) plus 2× radial `10uF` bulk capacitors (`C1` at `(25.00, 112.24)`, `C2` at `(25.00, 118.79)`).
  * **Back Side (`B.Cu`, 29 SMD + 1 THT):** All 29 SMD components (`U1` at `(30.00, 29.67)`, `U2` at `(30.00, 58.50)`, `U3` at `(30.00, 87.50)` and their surrounding `0603` passives and `SOD-323` diodes) sit on `B.Cu` for single-sided SMT assembly. The rear `2x5` Eurorack power header `J1` (`(33.66, 122.36)`) is placed on the right side of the lower power section on `B.Cu`, horizontally offset from `C1`/`C2`/`D1`/`D2` (`X = 25.00 mm`) so through-hole leads and capacitor bodies never overlap.

### Routing, Power Delivery & Decoupling
* **Routing Completeness:** `32/32` nets (`100%`) routed across `170` track segments (`582.22 mm` total copper length) and `24` through-hole vias (`0.6 mm` pad / `0.3 mm` drill; `0.15 mm` annular ring).
* **Power Distribution:**
  * `+12V` (`121.35 mm`, 20 segments, 3 vias) and `-12V` (`124.20 mm`, 19 segments, 3 vias) run along the right (`X = 38.0 mm`) and left (`X = 22.0 mm`) board edges at **`0.50 mm` trace width** (carrying `~17 mA` total quiescent current for three `TL074H` ICs — `<2%` of IPC-2221 `0.5 mm` 1 oz capacity).
  * `+12V_RAW` (`11.58 mm`) and `-12V_RAW` (`11.10 mm`) are routed on `B.Cu` at `0.50 mm` width between `J1` and `D1`/`D2` (with one `0.02 mm` connection stub at `0.2 mm` width entirely inside `J1` Pad 1 at `(33.66, 122.36)`).
* **Decoupling Placement (`analyze_pcb.py`):**
  * `U1` (`TL074H`): `C3` (`+12V`, `3.70 mm`), `C4` (`-12V`, `3.84 mm`) — same side (`B.Cu`).
  * `U2` (`TL074H`): `C5` (`+12V`, `3.46 mm`), `C6` (`-12V`, `4.21 mm`) — same side (`B.Cu`).
  * `U3` (`TL074H`): `C7` (`+12V`, `3.62 mm`), `C8` (`-12V`, `3.89 mm`) — same side (`B.Cu`).
* **Ground Planes:**
  * `F.Cu` `GND` zone: `55.2%` fill ratio (`1203.86 mm²` filled of `2180.0 mm²`).
  * `B.Cu` `GND` zone: `56.8%` fill ratio (`1239.15 mm²` filled of `2180.0 mm²`).
  * Unified into a single connected island (`0` isolated copper islands, `0` disconnected `GND` pads).

### Thermal & DFM Assessment
* **Thermal Dissipation (Manual Calculation):** Each `TL074H` draws `5.6 mA` typical (`7.2 mA` max) quiescent current across `23.2V` (`±11.6V`), dissipating `~130 mW` (`167 mW` max) per SOIC-14 package (`θJA ≈ 85°C/W`), or `<15°C` junction temperature rise above ambient.
* **DFM Tier:** **Standard JLCPCB 2-Layer Tier** (`min_track_width = 0.20 mm`, `min_drill = 0.30 mm`, `min_annular_ring = 0.15 mm`, board size `20.0 × 109.0 mm`).

---

## 6. Mated 3U Front Panel Alignment (`generate_eurorack_panel.py --inspect`)

When centered behind a standard `20.0 × 128.5 mm` (4HP × 3U) front panel (`Panel Origin = (20.00, 9.25 mm)` in main-PCB global coordinates), the 12 jack bushings (`+6.48 mm` Y offset from the `WQP-PJ398SM` footprint origin) map to:

| Row | Left Jack (`X_panel = 5.00 mm`) | Right Jack (`X_panel = 15.00 mm`) | Main PCB FP `Y` | Bushing Global `Y` | **Panel-Local `Y`** *(from top edge)* | Drill |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: |
| **1** | `J2` (`IN_1`) | `J3` (`OUT_1A`) | `21.40 mm` | `27.88 mm` | **`18.63 mm`** | `6.2 mm` |
| **2** | `J4` (`OUT_1B`) | `J5` (`OUT_1C`) | `35.80 mm` | `42.28 mm` | **`33.03 mm`** | `6.2 mm` |
| **3** | `J6` (`IN_2`) | `J7` (`OUT_2A`) | `50.20 mm` | `56.68 mm` | **`47.43 mm`** | `6.2 mm` |
| **4** | `J8` (`OUT_2B`) | `J9` (`OUT_2C`) | `64.60 mm` | `71.08 mm` | **`61.83 mm`** | `6.2 mm` |
| **5** | `J10` (`IN_3`) | `J11` (`OUT_3A`) | `79.00 mm` | `85.48 mm` | **`76.23 mm`** | `6.2 mm` |
| **6** | `J12` (`OUT_3B`) | `J13` (`OUT_3C`) | `93.40 mm` | `99.88 mm` | **`90.63 mm`** | `6.2 mm` |

---

## 7. False Positives & Reviewer Overrides

The following automated analyzer findings were reviewed against the physical design and confirmed to be **benign / expected**:
* **`kicad-cli pcb drc` `lib_footprint_issues` (44 warnings):** Triggered because `kicad-cli` runs inside the sandbox without read access to `~/Library/Preferences/kicad/10.0/fp-lib-table`; all 44 footprints are embedded directly inside [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb).
* **Board Edge Clearance (`PM-002` error in `analyze_pcb.py`) on `J1`–`J13`:** Flags `J2`–`J13` at `0.0 mm` from the `20.0 mm` wide board edges and `J1` courtyard at `0.04 mm` from the `X = 40.0 mm` right edge. On a 4HP (`20.0 mm`) Eurorack PCB, two `10.0 mm` wide `WQP-PJ398SM` jacks side-by-side at `X = 25.0 mm` and `X = 35.0 mm` intentionally sit flush with the left and right board edges, while all copper pads meet the `0.5 mm` edge clearance rule (`0` copper-to-edge DRC violations).
* **No Opposite-Layer Copper (`CP-002` info) under `J1`–`J13`:** Caused by through-hole pad clearances and the `0.5 mm` zone clearance around the connectors; benign.
* **EMC Reference Plane Gaps (`GP-001` / `GP-004`) & Signal Via Stitching (`RP-001`) in `analyze_emc.py`:** `analyze_emc.py` treats signal traces crossing THT jack clearance cutouts in the `GND` pour and signal layer transitions (`CH1_OP_C`, `CH2_OP_C`, `CH3_OP_C`, `CH1_BUF`, `CH2_BUF`, `CH1_JACK_IN`, `CH2_JACK_IN`, `CH3_JACK_IN`) as high-speed return-path discontinuities. For DC-to-audio-frequency (`<100 kHz`) Eurorack CV/audio signals with `1 kΩ` input / `470 Ω` output series resistors and solid dual-layer `GND` pours, these have negligible EMC or signal-integrity impact.
* **No Fiducials (`FD-001`) & Test Points (`TE-001`):** Largest fine-pitch part is `SOIC-14` (`1.27 mm` pitch) + `0603` passives on a `20 × 109 mm` board; JLCPCB panel rails provide global fiducials, and all 12 THT jacks + `J1` pins serve as accessible test points.

---

## 8. Not Performed / Review Limits

* **KiCad `.kicad_sch` Schematic Analyzer (`analyze_schematic.py`), `cross_analysis.py`, & `analyze_thermal.py`:** Not applicable because the circuit is authored directly in Python via SKiDL ([`buffered_multiple.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.py) → [`buffered_multiple.net`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.net)) without a `.kicad_sch` file. Full 44/44 component and 135/135 pin-to-pad cross-verification and manual thermal calculations were performed directly against [`buffered_multiple.net`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.net) and [`BufferedMult.kicad_pcb`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/BufferedMult.kicad_pcb).
* **Local PDF Datasheet Cache (`datasheets/`):** No `datasheets/` directory is present in the workspace; IC pinouts (`TL074HIDR` SOIC-14, TI SLOS954) and diode/jack footprints were verified against standard package specifications and embedded KiCad 10 footprint definitions.
* **SPICE Simulation (`simulate_subcircuits.py`):** Not performed (`ngspice`, `ltspice`, and `xyce` are not installed in the local environment).
* **Distributor Lifecycle API Audit (`--lifecycle`):** Not performed (offline sandbox environment; all 7 SMT part types carry verified LCSC catalog numbers in [`buffered_multiple.py`](file:///Users/brett/Documents/GitHub/BufferedMult-SKiDL/buffered_multiple.py)).
