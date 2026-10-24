---
title: "Eurorack Power & Audio Jack Normalling Reference"
page_title: "Eurorack Power & Audio Jack Normalling Reference | Eurorack SKiDL Tutorial"
nav_id: "eurorack-power-and-normalling"
nav_label: "Eurorack Ref"
kicker: "Reference Sheet · Hardware Standards"
lead: "Pinout, polarity, and cascaded switched-jack routing reference for Doepfer A-100 10-pin power headers, `1N5819WS` Schottky protection, and `WQP-PJ398SM` (Thonkiconn) 3.5mm jacks."
card:
  title: "Eurorack Power & Audio Jack Normalling Reference"
  summary: "10-pin Doepfer power header pinout, bipolar Schottky/bulk cap polarity, `WQP-PJ398SM` switch mechanics, and the `1:3 / 1:6 / 1:9` truth table."
---

## 1. Standard 10-Pin (`2x5`) Eurorack Power Header & Protection

Table: `Conn_02x05_Odd_Even` pinout and reverse-polarity protection wiring

| Header Pins | Raw Net | Protection & Bulk Filtering | Protected Rail |
| --- | --- | --- | --- |
| `j_pwr[1, 2]`<br><small>Red Stripe (-12V)</small> | `-12V_RAW` | `d_neg["K"]` at `-12V_RAW` ← `d_neg["A"]` at `-12V`<br>`c_bulk_neg[1]` (`+`) at `GND`, `c_bulk_neg[2]` (`-`) at `-12V` | `-12V` (`vee`)<br>`NetClass("Power", 0.5mm)` |
| `j_pwr[3, 4, 5, 6, 7, 8]`<br><small>Centre Ground</small> | `GND` | Direct connection to stitched `F.Cu` and `B.Cu` ground planes | `GND` (`gnd`)<br>`NetClass("Power", 0.5mm)` |
| `j_pwr[9, 10]`<br><small>Top Pair (+12V)</small> | `+12V_RAW` | `d_pos["A"]` at `+12V_RAW` → `d_pos["K"]` at `+12V`<br>`c_bulk_pos[1]` (`+`) at `+12V`, `c_bulk_pos[2]` (`-`) at `GND` | `+12V` (`vcc`)<br>`NetClass("Power", 0.5mm)` |

## 2. `WQP-PJ398SM` (Thonkiconn) Switched Jack Pinout

Table: `Connector_Audio:AudioJack2_SwitchT` symbol pins and mechanical behaviour

| Symbol Pin ID | Contact Role | Unpatched State (No Plug) | Patched State (3.5mm Plug Inserted) | SKiDL Connection in `buffered_multiple.py` |
| --- | --- | --- | --- | --- |
| `j["T"]` | Tip (Signal) | Spring-loaded contact touches `TN` | Connects to patch cable Tip; lifts off `TN` | Input: `in_jack += j_in["T"]`<br>Output: `jack_tip += j_out["T"]` |
| `j["TN"]` | Switched Tip Normal | Conducts default normalled signal into `T` | Mechanically disconnected (open circuit) | Input: `norm_in += j_in["TN"]`<br>Output: `j_out["TN"] += builtins.NC` |
| `j["S"]` | Sleeve (Ground) | Connected to `GND` | Connects patch cable shield/sleeve to `GND` | `gnd += j["S"]` |

## 3. Cascaded Normalling Matrix (`1:3` / `1:6` / `1:9`)

Table: Output routing across all patching combinations of `IN_1` (`J2`), `IN_2` (`J6`), and `IN_3` (`J10`)

| `IN_1` (`J2`) | `IN_2` (`J6`) | `IN_3` (`J10`) | Outputs `1A–1C` | Outputs `2A–2C` | Outputs `3A–3C` | Effective Mode |
| --- | --- | --- | --- | --- | --- | --- |
| Unpatched | Unpatched | Unpatched | `0V` (`GND` via `J2.TN`) | `0V` (`CH1_BUF` via `J6.TN`) | `0V` (`CH2_BUF` via `J10.TN`) | All 9 outputs quiet at `0.00V` |
| **Patched (`V1`)** | Unpatched | Unpatched | `V1` (3×) | `V1` (3× via `CH1_BUF`) | `V1` (3× via `CH2_BUF`) | **1-to-9 Buffered Multiple** |
| **Patched (`V1`)** | Unpatched | **Patched (`V3`)** | `V1` (3×) | `V1` (3× via `CH1_BUF`) | `V3` (3×) | **1-to-6 (CH1+2) + 1-to-3 (CH3)** |
| **Patched (`V1`)** | **Patched (`V2`)** | Unpatched | `V1` (3×) | `V2` (3×) | `V2` (3× via `CH2_BUF`) | **1-to-3 (CH1) + 1-to-6 (CH2+3)** |
| **Patched (`V1`)** | **Patched (`V2`)** | **Patched (`V3`)** | `V1` (3×) | `V2` (3×) | `V3` (3×) | **Triple Independent 1-to-3** |
