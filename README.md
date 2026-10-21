# Eurorack Buffered Multiple (SKiDL + KiCad 10)

A precision **Dual 1-to-3 (Normalized to 1-to-6) Eurorack Buffered Multiple** designed in Python using [SKiDL](https://devbisme.github.io/skidl/) and targeting **KiCad 10**.

---

## Features & Architecture

- **Dual 1-to-3 / Cascaded 1-to-6 Routing**:
  - **Channel 1**: 1 input (`IN_1`) driving 3 individually buffered outputs (`OUT_1A`, `OUT_1B`, `OUT_1C`). When `IN_1` is unpatched, its normalled switch contact (`TN`) grounds the input to `0V`.
  - **Channel 2**: 1 input (`IN_2`) driving 3 individually buffered outputs (`OUT_2A`, `OUT_2B`, `OUT_2C`). When `IN_2` is unpatched, its normalled switch contact (`TN`) receives the buffered signal from Channel 1 (`CH1_BUF`), turning the module into a **1-to-6 buffered multiple** with zero loading droop between channels. Patching a cable into `IN_2` breaks the normal connection for independent dual 1-to-3 operation.
- **Dedicated Input & Output Buffering**:
  - Each channel uses one quad `TL074` JFET-input op-amp (`SOIC-14`):
    - **Stage A**: Unity-gain input follower with a `100K` input pull-down resistor (`0805`).
    - **Stages B, C, D**: Three independent unity-gain output followers, each isolated with a `470R` series output protection resistor (`0805`).
- **Eurorack Power Supply Protection**:
  - Standard 10-pin (`2x5`) through-hole shrouded IDC power header (`±12V`, `GND`).
  - Reverse-polarity protection via `1N5819` (`SS14`) Schottky diodes (`SMA`).
  - `10uF` radial through-hole electrolytic bulk bypass capacitors per rail plus `100nF` (`0805`) local ceramic decoupling capacitors at each op-amp's `V+` and `V-` pins.

### Signal Flow

```mermaid
flowchart LR
    subgraph CH1["Channel 1 (U1: TL074)"]
        J_IN1["IN_1 Jack<br/>(TN -> GND)"] --> R_PD1["100K to GND"]
        R_PD1 --> U1A["U1A Input Buffer"]
        U1A --> U1B["U1B Buffer + 470R"] --> OUT_1A["OUT_1A Jack"]
        U1A --> U1C["U1C Buffer + 470R"] --> OUT_1B["OUT_1B Jack"]
        U1A --> U1D["U1D Buffer + 470R"] --> OUT_1C["OUT_1C Jack"]
    end

    subgraph CH2["Channel 2 (U2: TL074)"]
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

| Qty | Value / Part | Package / Footprint | KiCad Symbol | Description |
| --: | :--- | :--- | :--- | :--- |
| 2 | `TL074` | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` | `Amplifier_Operational:TL074` | Quad Low-Noise JFET-Input Op-Amp |
| 8 | `WQP-PJ398SM` | `Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles` | `Connector_Audio:AudioJack2_SwitchT` | 3.5mm Mono Switched Eurorack Jack (Thonkiconn) |
| 1 | `EURORACK_PWR_10PIN` | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | `Connector_Generic:Conn_02x05_Odd_Even` | 10-Pin (`2x5`) Shrouded Eurorack Power Header (THT, Hand-Soldered) |
| 2 | `1N5819` / `SS14` | `Diode_SMD:D_SMA` | `Device:D_Schottky` | Schottky Barrier Diode (Reverse-Polarity Protection) |
| 2 | `10uF` (25V) | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm` | `Device:C_Polarized` | Radial Aluminum Electrolytic Bulk Capacitor (`ECEA1EKS100` / `C713347`, THT, Hand-Soldered) |
| 4 | `100nF` | `Capacitor_SMD:C_0805_2012Metric` | `Device:C` | 0805 Ceramic Decoupling Capacitor |
| 2 | `100K` | `Resistor_SMD:R_0805_2012Metric` | `Device:R` | 0805 Input Pull-Down Resistor |
| 6 | `470R` | `Resistor_SMD:R_0805_2012Metric` | `Device:R` | 0805 Output Series Protection Resistor |

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

3. **Lint and format with `ruff`**:
   ```bash
   ruff check --fix . && ruff format .
   ```

---

## Generated Files

Running `buffered_multiple.py` produces:

- **`buffered_multiple.net`** — KiCad 10 netlist with deterministic hierarchical `tstamps` and `Power` / `Signal` net classes.
- **`buffered_multiple_bom.xml`** — KiCad XML Bill of Materials.
- **`buffered_multiple.svg`** — Top-level hierarchical SVG diagram, plus subcircuit sheets:
  - **`buffered_multiple_pwr.svg`** — Power header, protection diodes, and bulk filtering.
  - **`buffered_multiple_ch1.svg`** — Channel 1 (`IN_1` -> `OUT_1A..1C`).
  - **`buffered_multiple_ch2.svg`** — Channel 2 (`IN_2` -> `OUT_2A..2C`).
- **`buffered_multiple_sklib.py`** — Auto-generated SKiDL backup symbol library.

---

## Importing into KiCad PCB Editor (`pcbnew`)

1. Open **KiCad 10** and create or open a `.kicad_pcb` board file.
2. Select **File -> Import -> Netlist...**
3. Browse to `buffered_multiple.net`, click **Update PCB**, and place your footprints on the board.
