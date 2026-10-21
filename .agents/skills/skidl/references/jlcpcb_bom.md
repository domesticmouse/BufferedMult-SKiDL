# JLCPCB PCBA BOM & Catalog Integration

When preparing a SKiDL circuit for JLCPCB SMT/PCBA assembly, you must embed component catalog metadata into `part.fields`, verify live stock and Basic/Extended library status, and export a grouped 4-column CSV BOM alongside the KiCad netlist.

---

## 1. Embedding Custom Fields in SKiDL (`part.fields`)

### The `SkidlBaseObject.__setattr__` Gotcha
In SKiDL, `SkidlBaseObject.__setattr__` only writes an attribute into `part.fields` if the key **already exists** in `part.fields`:
```python
if key == "fields" or key not in self.fields:
    super().__setattr__(key, value)
else:
    self.fields[key] = value
```
Therefore, passing arbitrary keyword arguments like `Part(..., LCSC="C49678")` or assigning `part.LCSC = "C49678"` creates a plain Python attribute on the `Part` instance and **will NOT be exported** in `<fields>` by `generate_xml()` or `generate_netlist()`.

### Correct Way to Add Exported Fields
Always assign custom catalog metadata directly into the `part.fields` dictionary:
```python
r_t = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0805_2012Metric")
r_t.fields["LCSC"] = "C17710"
r_t.fields["MPN"] = "0805W8F4700T5E"
r_t.fields["JLCPCB_Class"] = "Basic"

# Template copies automatically inherit a copy of `r_t.fields`
r1, r2 = r_t(2, value="470R", tag="r_out")
```
* **Exception for `dnp` and `exclude_from_bom`**: KiCad's netlist generator (`gen_netlist_comp`) checks `getattr(part, "dnp", False)` and `getattr(part, "exclude_from_bom", False)` as direct attributes on `part` (emitting `(property (name "dnp"))`). Set those directly on the part (`part.dnp = True`), while keeping catalog strings (`LCSC`, `MPN`, etc.) in `part.fields`.

---

## 2. Querying the JLCPCB Catalog for Live Stock & Cost

Never rely purely on memorized LCSC `C`-numbers—parts frequently go out of stock, become deprecated (`(SMTonly)` with `0` stock, such as `C17407`), or map to a different package than expected (e.g., `C6965` is an SO-8 `TL081CDT`, whereas `C12594` and `C6963` are SOIC-14 `TL074`).

### Option A: Live Query Helper Script (Recommended for BOM Verification)
Run [jlcpcb_search.py](../scripts/jlcpcb_search.py) to query JLCPCB's live `selectSmtComponentList/v2` endpoint (with automatic fallback to `jlcsearch.tscircuit.com`):
```bash
python3 .agents/skills/skidl/scripts/jlcpcb_search.py --in-stock-only "100k 0805" "TL074 SOIC-14" "10uF D6.3xL5.4mm"
```
*(Note: Because this script makes HTTPS requests to `jlcpcb.com`, run it outside the sandbox if sandbox network access is disabled.)*

### Option B: Lightweight `jlcsearch` JSON API
Query `https://jlcsearch.tscircuit.com` directly:
* General search: `https://jlcsearch.tscircuit.com/api/search?q=TL074&limit=5`
* Parametric category endpoints: `https://jlcsearch.tscircuit.com/resistors/list.json?package=0805&resistance=470`

### Option C: Full Offline Catalog Downloads
For bulk offline queries without rate limits:
* **`CDFER/jlcpcb-parts-database`** (`https://github.com/CDFER/jlcpcb-parts-database`): Provides daily builds of `jlcpcb-components-basic-preferred.csv` (~3 MB CSV of all Basic and Preferred Extended parts) and a ~1 GB FTS5-indexed SQLite database of all in-stock parts.
* **`yaqwsx/jlcparts`** (`https://yaqwsx.github.io/jlcparts/`): Web UI and upstream scraper for parametric filtering.

---

## 3. JLCPCB Part Classes & Cost Optimization

JLCPCB categorizes SMT components into three tiers:
1. **Basic Parts (`componentLibraryType == "base"`)**: Pre-loaded on SMT machines; **\$0 feeder loading fee**. Always prefer Basic Parts for standard passives, diodes, regulators, and common ICs.
2. **Preferred Extended Parts (`preferredComponentFlag == True`)**: Promotional extended parts with **\$0 feeder loading fee**.
3. **Extended Parts (`componentLibraryType == "expand"`)**: Incur a **~\$3.00 setup/feeder loading fee per unique part line** per order. Consolidate values/footprints where possible to minimize unique Extended part lines.
4. **Panel-Mounted / Manual Through-Hole Parts**: Controls that must be aligned physically against a front panel before soldering (such as `WQP-PJ398SM` / Thonkiconn 3.5mm jacks or potentiometers) usually have `0` SMT stock on JLCPCB and should be omitted from the JLCPCB PCBA BOM for manual assembly.

### Commonly Used In-Stock Parts Reference
| Component | Package | Verified LCSC # | MPN | Library Class |
| :--- | :--- | :--- | :--- | :--- |
| `100nF` 50V X7R MLCC | `0805` | `C49678` | `CC0805KRX7R9BB104` | Basic |
| `100K` 1% Thick Film Resistor | `0805` | `C149504` *(not `C17407`)* | `0805W8F1003T5E` | Basic |
| `470R` 1% Thick Film Resistor | `0805` | `C17710` | `0805W8F4700T5E` | Basic |
| `1N5819` / `SS14` 40V 1A Schottky | `SMA (DO-214AC)` | `C2480` | `SS14` | Basic |
| `TL074` Quad JFET Op-Amp | `SOIC-14` | `C12594` *(TI)* / `C6963` *(ST)* | `TL074CDR` / `TL074CDT` | Extended |
| `10uF` 50V SMD Electrolytic | `SMD,D6.3xL5.4mm` | `C14162` *(or `C72488`)* | `RVT1H100M0605` | Extended |
| `10uF` 16V SMD Tantalum | `CASE-A (3216)` | `C7171` | `TAJA106K016RNJ` | Basic |
| `2x5P` 2.54mm Shrouded IDC Header | `Through-Hole` | `C53207560` | `IDC2.54-2*5PZ` | Extended (THT) |

---

## 4. Exporting a JLCPCB-Compatible BOM CSV from SKiDL

JLCPCB does not accept KiCad `.xml` BOMs directly; it requires a `.csv` with four columns: `Comment`, `Designator`, `Footprint`, and `LCSC Part #`, with identical parts grouped onto a single row.

Include this helper in your SKiDL script and call it right after `generate_xml()`:

```python
import builtins
import csv


def generate_jlcpcb_bom(file_="jlcpcb_bom.csv", include_tht=False):
    """
    Export a grouped JLCPCB PCBA BOM CSV (`Comment,Designator,Footprint,LCSC Part #`).
    By default, exports all SMT components with an assigned LCSC part number and
    excludes hand-soldered through-hole connectors unless `include_tht=True`.
    """
    groups = {}
    for part in builtins.default_circuit.parts:
        lcsc = part.fields.get("LCSC", "")
        jlc_class = part.fields.get("JLCPCB_Class", "")
        if (
            not lcsc
            or getattr(part, "dnp", False)
            or getattr(part, "exclude_from_bom", False)
        ):
            continue
        if not include_tht and "THT" in jlc_class:
            continue

        comment = part.value_to_str()
        footprint = getattr(part, "footprint", "").split(":")[-1]
        key = (comment, footprint, lcsc)
        groups.setdefault(key, []).append(part.ref)

    with open(file_, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (comment, footprint, lcsc), refs in groups.items():
            writer.writerow([comment, ", ".join(refs), footprint, lcsc])
```
