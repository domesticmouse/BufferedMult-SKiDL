---
title: "KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference"
page_title: "KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference | Eurorack SKiDL Tutorial"
nav_id: "kicad-jlcpcb-lookup"
nav_label: "Lookup Ref"
kicker: "Reference Sheet · Component Discovery"
lead: "Command-line and Python patterns for discovering exact KiCad 10 symbols, pin numbers/names, `.pretty` footprints, and live JLCPCB/LCSC catalog part numbers."
card:
  title: "KiCad 10 Symbol, Footprint & JLCPCB Lookup Reference"
  summary: "Four-step discovery workflow (`search`, `show`, `search_footprints`, `jlcpcb_search.py`) and complete component pinout/LCSC table."
---

## 1. Four-Step Programmatic Discovery Workflow

```mermaid caption="Verify every symbol, pinout, footprint, and LCSC part number programmatically before wiring a subcircuit."
flowchart LR
  S1["1. search('keyword')<br/>Find KiCad Symbol"] --> S2["2. show('Lib', 'Part')<br/>Verify Pin Numbers & Types"]
  S2 --> S3["3. search_footprints('pkg')<br/>Get Lib:Footprint String"]
  S3 --> S4["4. jlcpcb_search.py<br/>Verify Stock & Basic/Ext Class"]
```

```bash title="Interactive discovery commands (Terminal / Python)"
# 1. Search symbols, inspect pinouts, and search footprints via .venv/bin/python
.venv/bin/python tutorial/apps/0001-programmatic-component-discovery/discover_parts.py

# 2. Query live JLCPCB/LCSC stock, Basic vs. Extended feeder status, and pricing
.venv/bin/python .agents/skills/skidl/scripts/jlcpcb_search.py --in-stock-only \
    "100k 0603" "1k 0603" "470R 0603" "100nF 0603" "1N5819WS SOD-323" "PESD12VL1BA" "TL074H SOIC-14"
```

## 2. Complete `buffered_multiple.py` Symbol, Pinout & LCSC Matrix

Table: Verified KiCad 10 symbols, pin mappings, footprints, and LCSC catalog numbers

| Component Role | KiCad 10 Symbol (`Lib`, `Name`) | Verified Pin IDs & Types | KiCad 10 Footprint | LCSC # & Class |
| --- | --- | --- | --- | --- |
| Quad Op-Amp (`U1`–`U3`) | `Amplifier_Operational`, `TL074` | Unit A: `1` (OUT), `2` (`-`), `3` (`+`)<br>Unit B: `5` (`+`), `6` (`-`), `7` (OUT)<br>Unit C: `8` (OUT), `9` (`-`), `10` (`+`)<br>Unit D: `12` (`+`), `13` (`-`), `14` (OUT)<br>Rails: `4` (`V+`, PWRIN), `11` (`V-`, PWRIN) | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` | `C2878713` (`TL074HIDR`, Extended) |
| Reverse-Polarity Schottky (`D1`, `D2`) | `Device`, `D_Schottky` | `1` (`K`, PASSIVE), `2` (`A`, PASSIVE) | `Diode_SMD:D_SOD-323` | `C191023` (`1N5819WS`, Basic) |
| Input ESD/TVS Diode (`D3`–`D5`) | `Device`, `D_TVS` | `1` (`A1`, PASSIVE), `2` (`A2`, PASSIVE) | `Diode_SMD:D_SOD-323` | `C38558` (`PESD12VL1BA,115`, Extended) |
| Decoupling Cap `100nF` (`C3`–`C8`) | `Device`, `C` | `1` (PASSIVE), `2` (PASSIVE) | `Capacitor_SMD:C_0603_1608Metric` | `C14663` (`CC0603KRX7R9BB104`, Basic) |
| Input Pull-Down `100K` (`R1`, `R6`, `R11`) | `Device`, `R` | `1` (PASSIVE), `2` (PASSIVE) | `Resistor_SMD:R_0603_1608Metric` | `C25803` (`0603WAF1003T5E`, Basic) |
| Input Series `1K` (`R2`, `R7`, `R12`) | `Device`, `R` | `1` (PASSIVE), `2` (PASSIVE) | `Resistor_SMD:R_0603_1608Metric` | `C21190` (`0603WAF1001T5E`, Basic) |
| Output Series `470R` (`R3`–`R5`, `R8`–`R10`, `R13`–`R15`) | `Device`, `R` | `1` (PASSIVE), `2` (PASSIVE) | `Resistor_SMD:R_0603_1608Metric` | `C23179` (`0603WAF4700T5E`, Basic) |
| Switched 3.5mm Mono Jack (`J2`–`J13`) | `Connector_Audio`, `AudioJack2_SwitchT` | `S` (Sleeve), `T` (Tip), `TN` (Switched Tip Normal) | `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | Manual THT (`WQP-PJ398SM`, DNP for SMT) |
| Bulk Electrolytic Cap `10uF` (`C1`, `C2`) | `Device`, `C_Polarized` | `1` (`+`, PASSIVE), `2` (`-`, PASSIVE) | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm` | Manual THT (`ECEA1EKS100`, DNP for SMT) |
| 10-Pin Eurorack Power Header (`J1`) | `Connector_Generic`, `Conn_02x05_Odd_Even` | `1, 2` (`-12V`), `3..8` (`GND`), `9, 10` (`+12V`) | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | Manual THT (DNP for SMT) |
