# Eurorack Buffered Multiple (SKiDL + KiCad 10)

A precision **Dual 1-to-3 (Normalized to 1-to-6) Eurorack Buffered Multiple** designed in Python using [SKiDL](https://devbisme.github.io/skidl/) and targeting **KiCad 10**.

This project is a SKiDL re-implementation of [domesticmouse/Buffered-Mult](https://github.com/domesticmouse/Buffered-Mult), omitting the LED feedback circuitry.

---

## Features & Architecture

- **Dual 1-to-3 / Cascaded 1-to-6 Routing**:
  - **Channel 1**: 1 input (`IN_1`) driving 3 individually buffered outputs (`OUT_1A`, `OUT_1B`, `OUT_1C`). When `IN_1` is unpatched, its normalled switch contact (`TN`) grounds the input to `0V`.
  - **Channel 2**: 1 input (`IN_2`) driving 3 individually buffered outputs (`OUT_2A`, `OUT_2B`, `OUT_2C`). When `IN_2` is unpatched, its normalled switch contact (`TN`) receives the buffered signal from Channel 1 (`CH1_BUF`), turning the module into a **1-to-6 buffered multiple** with zero loading droop between channels. Patching a cable into `IN_2` breaks the normal connection for independent dual 1-to-3 operation.
- **Dedicated Input & Output Buffering**:
  - Each channel uses one quad `TL074H` (`TL074HIDR`) op-amp (`SOIC-14`):
    - **Stage A**: Unity-gain input follower with a `100K` input pull-down resistor (`0805`).
    - **Stages B, C, D**: Three independent unity-gain output followers, each isolated with a `470R` series output protection resistor (`0805`).
- **Eurorack Power Supply Protection**:
  - Standard 10-pin (`2x5`) through-hole shrouded IDC power header (`±12V`, `GND`).
  - Reverse-polarity protection via `1N5819` (`SS14`) Schottky diodes (`SMA`).
  - `10uF` radial through-hole electrolytic bulk bypass capacitors per rail plus `100nF` (`0805`) local ceramic decoupling capacitors at each op-amp's `V+` and `V-` pins.

### Signal Flow

```mermaid
flowchart LR
    subgraph CH1["Channel 1 (U1: TL074H)"]
        J_IN1["IN_1 Jack<br/>(TN -> GND)"] --> R_PD1["100K to GND"]
        R_PD1 --> U1A["U1A Input Buffer"]
        U1A --> U1B["U1B Buffer + 470R"] --> OUT_1A["OUT_1A Jack"]
        U1A --> U1C["U1C Buffer + 470R"] --> OUT_1B["OUT_1B Jack"]
        U1A --> U1D["U1D Buffer + 470R"] --> OUT_1C["OUT_1C Jack"]
    end

    subgraph CH2["Channel 2 (U2: TL074H)"]
        J_IN2["IN_2 Jack<br/>(TN <- CH1_BUF)"] --> R_PD2["100K to GND"]
        R_PD2 --> U2A["U2A Input Buffer"]
        U2A --> U2B["U2B Buffer + 470R"] --> OUT_2A["OUT_2A Jack"]
        U2A --> U2C["U2C Buffer + 470R"] --> OUT_2B["OUT_2B Jack"]
        U2A --> U2D["U2D Buffer + 470R"] --> OUT_2C["OUT_2C Jack"]
    end

    U1A -- "CH1_BUF (Normalled to IN_2 TN)" --> J_IN2
```

---

## Bill of Materials (BOM)

The design separates **SMT components** (factory-assembled on `B.Cu` by JLCPCB) from **Through-Hole (THT) components** (hand-soldered after receiving the boards):

| Ref | Qty | Value / Part | Package / Footprint | KiCad Symbol | LCSC Part # | Assembly / Description |
| :--- | --: | :--- | :--- | :--- | :--- | :--- |
| `U1`, `U2` | 2 | `TL074H` (`TL074HIDR`) | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` | `Amplifier_Operational:TL074` | `C2878713` | **SMT (`B.Cu`, Extended)** — Quad Low-Noise High-Voltage Op-Amp |
| `D1`, `D2` | 2 | `1N5819` / `SS14` | `Diode_SMD:D_SMA` | `Device:D_Schottky` | `C2480` | **SMT (`B.Cu`, Basic)** — Schottky Reverse-Polarity Protection Diode |
| `C3`–`C6` | 4 | `100nF` (`50V X7R`) | `Capacitor_SMD:C_0805_2012Metric` | `Device:C` | `C49678` | **SMT (`B.Cu`, Basic)** — Ceramic Decoupling Capacitor (`CC0805KRX7R9BB104`) |
| `R1`, `R5` | 2 | `100K` (`1%`) | `Resistor_SMD:R_0805_2012Metric` | `Device:R` | `C149504` | **SMT (`B.Cu`, Basic)** — Input Pull-Down Resistor (`0805W8F1003T5E`) |
| `R2`–`R4`, `R6`–`R8` | 6 | `470R` (`1%`) | `Resistor_SMD:R_0805_2012Metric` | `Device:R` | `C17710` | **SMT (`B.Cu`, Basic)** — Output Series Protection Resistor (`0805W8F4700T5E`) |
| `J2`–`J9` | 8 | `WQP-PJ398SM` | `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | `Connector_Audio:AudioJack2_SwitchT` | — | **THT (`F.Cu`, Hand-Soldered)** — 3.5mm Mono Switched Eurorack Jack (Thonkiconn) |
| `C1`, `C2` | 2 | `10uF` (`25V`) | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm` | `Device:C_Polarized` | `C713347` | **THT (`F.Cu`, Hand-Soldered)** — Radial Electrolytic Bulk Cap (`ECEA1EKS100`) |
| `J1` | 1 | `EURORACK_PWR_10PIN` | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | `Connector_Generic:Conn_02x05_Odd_Even` | — | **THT (`B.Cu`, Hand-Soldered)** — 10-Pin (`2x5`) Shrouded Eurorack Power Header |

---

## Getting Started

### Prerequisites

- **KiCad 10** installed (default macOS symbol/footprint path `/Applications/KiCad/KiCad.app/Contents/SharedSupport/` is detected automatically by `buffered_multiple.py`).
- **Python 3.12–3.14** and [`uv`](https://docs.astral.sh/uv/).

### Setup & Run

1. **Create the virtual environment and install SKiDL**:
   ```bash
   uv venv --clear --python 3.14 .venv
   uv pip install skidl
   ```

2. **Generate the circuit outputs and run Electrical Rules Checking (ERC)**:
   ```bash
   .venv/bin/python buffered_multiple.py
   ```

3. **Generate or update the 4HP Eurorack front panel PCB and Gerbers**:
   ```bash
   /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
       .agents/skills/eurorack-panel/scripts/generate_eurorack_panel.py \
       --main-pcb BufferedMult.kicad_pcb \
       --output BufferedMult_Panel.kicad_pcb \
       --title "BUF MULT" \
       --subtitle "1:3 / 1:6" \
       --gerber-dir production/panel \
       --zip production/BufferedMult_Panel.zip \
       --drc
   ```

4. **Lint and format with `ruff`**:
   ```bash
   ruff check --fix . && ruff format .
   ```

---

## Generated Files

Running `buffered_multiple.py` produces:

- **`buffered_multiple.net`** — KiCad 10 netlist with deterministic hierarchical `tstamps` and `Power` / `Signal` net classes.
- **`buffered_multiple_bom.xml`** — KiCad XML Bill of Materials.
- **`buffered_multiple_jlcpcb_bom.csv`** — Grouped JLCPCB SMT PCBA Bill of Materials (`Comment,Designator,Footprint,LCSC Part #`), excluding hand-soldered THT parts by default.
- **`buffered_multiple.svg`** — Top-level hierarchical SVG diagram, plus subcircuit sheets:
  - **`buffered_multiple_pwr.svg`** — Power header, protection diodes, and bulk filtering.
  - **`buffered_multiple_ch1.svg`** — Channel 1 (`IN_1` -> `OUT_1A..1C`).
  - **`buffered_multiple_ch2.svg`** — Channel 2 (`IN_2` -> `OUT_2A..2C`).
- **`buffered_multiple.erc`** / **`buffered_multiple.log`** — SKiDL ERC report and execution log (`0` errors, `0` warnings).
- **`buffered_multiple_sklib.py`** — Auto-generated SKiDL backup symbol library.

---

## KiCad 10 PCBs & Fabrication Outputs

Both the main circuit board and a mated 3U × 4HP Eurorack front panel are included and ready for fabrication (`0` DRC errors):

- **Main Circuit PCB ([`BufferedMult.kicad_pro`](BufferedMult.kicad_pro) / [`BufferedMult.kicad_pcb`](BufferedMult.kicad_pcb))**:
  - **Dimensions**: `20.0 × 108.0 mm` (4HP), 2-layer PCB with stitched `F.Cu` and `B.Cu` `GND` planes and `0.5 mm` `±12V` power spines.
  - **Assembly**: Single-sided SMT placement on `B.Cu` (16 SMD parts) and hand-soldered THT jacks/bulk caps on `F.Cu` (`J2`–`J9`, `C1`, `C2`) plus the 10-pin power header on `B.Cu` (`J1`).
- **4HP Eurorack Front Panel ([`BufferedMult_Panel.kicad_pro`](BufferedMult_Panel.kicad_pro) / [`BufferedMult_Panel.kicad_pcb`](BufferedMult_Panel.kicad_pcb))**:
  - **Dimensions**: `20.0 × 128.5 mm` (Doepfer A-100 3U × 4HP standard).
  - **Features**: 8× `6.2 mm` NPTH jack holes aligned to the `+6.48 mm` `WQP-PJ398SM` (Thonkiconn) bushing centers, 2× `3.2 × 5.5 mm` M3 mounting slots, input callout badges (`IN 1`, `IN 2`), normalling cascade indicator (`CH1 → IN 2`), and solid `F.Cu` / `B.Cu` copper shield planes with exposed rear ground rings.
- **Fabrication Archives (`production/`)**:
  - [`production/BufferedMult.zip`](production/BufferedMult.zip) — Main PCB Gerbers and Excellon drill files.
  - [`production/BufferedMult_Panel.zip`](production/BufferedMult_Panel.zip) — 4HP Front Panel Gerbers and Excellon drill files (also unpacked in `production/panel/`).
  - [`production/positions.csv`](production/positions.csv), [`production/bom.csv`](production/bom.csv), [`production/designators.csv`](production/designators.csv), [`production/netlist.ipc`](production/netlist.ipc) — Fabrication Toolkit pick-and-place, BOM, and IPC-D-356 netlist files (use [`buffered_multiple_jlcpcb_bom.csv`](buffered_multiple_jlcpcb_bom.csv) for SMT-only JLCPCB assembly).

---

## Documentation & Guides

- **[`PCB_LAYOUT_GUIDE.md`](PCB_LAYOUT_GUIDE.md)** — Step-by-step KiCad 10 PCB layout, component placement, routing, and JLCPCB export guide.
- **[`FRONT_PANEL_GUIDE.md`](FRONT_PANEL_GUIDE.md)** — 4HP Eurorack front panel mechanical dimensions, bushing offset coordinate table, and automated generation workflow.
- **[`DESIGN_REVIEW.md`](DESIGN_REVIEW.md)** — Full schematic, PCB, DRC, Gerber, and EMC pre-compliance design review report.

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE.txt](LICENSE.txt) for details.

*This is not an official Google product.*

