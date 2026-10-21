#!/usr/bin/env python3
"""
Generate the 4HP (3U) Eurorack Front Panel PCB (`BufferedMult_Panel.kicad_pcb`)
for `BufferedMult.kicad_pcb` in KiCad 10.

Features:
- Automatically extracts the main PCB outline and `WQP-PJ398SM` jack positions
  from `BufferedMult.kicad_pcb` and applies the `+6.48 mm` bushing offset.
- Generates a standalone 4HP x 3U (`20.0 x 128.5 mm`) KiCad 10 `.kicad_pcb` file
  with:
  - 2x M3 oval rack mounting slots (`3.2 x 5.5 mm` NPTH) at standard Doepfer
    positions (`Y = 3.0 mm` and `Y = 125.5 mm`, `X = 7.5 mm` in panel coords).
  - 8x grounded jack bushing holes (`6.2 mm` drill, `8.6 mm` rear `B.Mask`
    grounding ring, tented front `F.Mask`, `9.5 mm` M6 nut courtyard on `F.Fab`).
  - Front silkscreen artwork (`F.SilkS`): module header, inverted `IN 1` / `IN 2`
    input callout badges, output labels (`OUT 1A`..`OUT 2C`), and normalled
    cascade line (`NORM 1->2`).
  - Full `F.Cu` and `B.Cu` `GND` shield planes stitched with perimeter vias and
    automatically filled using KiCad's `pcbnew.ZONE_FILLER`.
"""

import pathlib
import re
import subprocess
import sys
import uuid

MAIN_PCB_PATH = pathlib.Path("BufferedMult.kicad_pcb")
PANEL_PCB_PATH = pathlib.Path("BufferedMult_Panel.kicad_pcb")

# Standard Doepfer A-100 3U x 4HP dimensions (mm)
PANEL_WIDTH_MM = 20.0
PANEL_HEIGHT_MM = 128.5

# WQP-PJ398SM (Thonkiconn) bushing center offset relative to footprint origin (Pad S)
THONKICONN_BUSHING_OFFSET_X = 0.0
THONKICONN_BUSHING_OFFSET_Y = 6.48

# Jack hole & M6 nut dimensions (mm)
JACK_DRILL_MM = 6.2
JACK_PAD_MM = 8.6
JACK_NUT_DIA_MM = 9.5

# M3 Eurorack mounting slot dimensions (mm)
MOUNT_SLOT_W_MM = 5.5
MOUNT_SLOT_H_MM = 3.2
MOUNT_X_LOCAL_MM = 7.5
MOUNT_TOP_Y_LOCAL_MM = 3.0
MOUNT_BOT_Y_LOCAL_MM = 125.5


def det_uuid(name: str) -> str:
    """Return a deterministic UUIDv5 string for reproducible KiCad file generation."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"BufferedMult_Panel:{name}"))


def parse_main_pcb(pcb_path: pathlib.Path) -> tuple[dict[str, float], list[dict]]:
    """Extract PCB outline and jack bushing coords from `BufferedMult.kicad_pcb`."""
    text = pcb_path.read_text(encoding="utf-8")

    rect_match = re.search(
        r"\(gr_rect\s+\(start\s+([\d.]+)\s+([\d.]+)\)\s+\(end\s+([\d.]+)\s+([\d.]+)\)"
        r'(?:(?!\(gr_rect).)*?\(layer\s+"Edge\.Cuts"\)',
        text,
        re.DOTALL,
    )
    if not rect_match:
        raise ValueError(f"Could not find Edge.Cuts gr_rect in {pcb_path}")

    x1, y1, x2, y2 = (float(rect_match.group(i)) for i in range(1, 5))
    bbox = {
        "min_x": min(x1, x2),
        "min_y": min(y1, y2),
        "max_x": max(x1, x2),
        "max_y": max(y1, y2),
    }

    jacks = []
    fp_pattern = re.compile(
        r'\(footprint\s+"Connector_Audio:Jack_3\.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"'
        r".*?\(at\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?\)"
        r'.*?\(property\s+"Reference"\s+"(J\d+)"'
        r'.*?\(property\s+"Value"\s+"([^"]+)"',
        re.DOTALL,
    )
    for match in fp_pattern.finditer(text):
        fp_x = float(match.group(1))
        fp_y = float(match.group(2))
        ref = match.group(4)
        val = match.group(5)
        jacks.append(
            {
                "ref": ref,
                "value": val,
                "fp_x": fp_x,
                "fp_y": fp_y,
                "bushing_x": round(fp_x + THONKICONN_BUSHING_OFFSET_X, 4),
                "bushing_y": round(fp_y + THONKICONN_BUSHING_OFFSET_Y, 4),
            }
        )

    jacks.sort(key=lambda j: (j["bushing_y"], j["bushing_x"]))
    if len(jacks) != 8:
        raise ValueError(f"Expected 8 jacks in {pcb_path}, found {len(jacks)}")

    return bbox, jacks


def format_jack_footprint(
    jack: dict, panel_origin_x: float, panel_origin_y: float
) -> str:
    """Create an embedded KiCad 10 footprint for a 3.5mm Eurorack jack panel hole."""
    ref = jack["ref"]
    val = jack["value"]
    bx = jack["bushing_x"]
    by = jack["bushing_y"]
    lx = round(bx - panel_origin_x, 2)
    ly = round(by - panel_origin_y, 2)
    nut_r = JACK_NUT_DIA_MM / 2.0
    pad_r = JACK_PAD_MM / 2.0
    crtyd_r = round(pad_r + 0.15, 2)

    descr = (
        f"Eurorack 3.5mm Thonkiconn (WQP-PJ398SM) panel hole "
        f"({JACK_DRILL_MM}mm drill, panel-local {lx:.2f}, {ly:.2f}mm)"
    )

    return f"""\t(footprint "Eurorack_Panel:JackHole_3.5mm_Thonkiconn_6.2mm"
\t\t(layer "F.Cu")
\t\t(uuid "{det_uuid(f"fp_{ref}")}")
\t\t(at {bx:g} {by:g})
\t\t(descr "{descr}")
\t\t(tags "eurorack panel hole thonkiconn 3.5mm")
\t\t(attr board_only exclude_from_pos_files exclude_from_bom)
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{det_uuid(f"fp_{ref}_ref")}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{val}"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{det_uuid(f"fp_{ref}_val")}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(fp_circle
\t\t\t(center 0 0)
\t\t\t(end {nut_r:g} 0)
\t\t\t(stroke
\t\t\t\t(width 0.1)
\t\t\t\t(type dash)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "Dwgs.User")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_dwgs_nut")}")
\t\t)
\t\t(fp_circle
\t\t\t(center 0 0)
\t\t\t(end {pad_r:g} 0)
\t\t\t(stroke
\t\t\t\t(width 0.1)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_fab_nut")}")
\t\t)
\t\t(fp_circle
\t\t\t(center 0 0)
\t\t\t(end {crtyd_r:g} 0)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_crtyd")}")
\t\t)
\t\t(pad "1" thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {JACK_PAD_MM:g} {JACK_PAD_MM:g})
\t\t\t(drill {JACK_DRILL_MM:g})
\t\t\t(layers "*.Cu" "B.Mask")
\t\t\t(remove_unused_layers no)
\t\t\t(net "GND")
\t\t\t(pintype "passive")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_pad1")}")
\t\t)
\t)"""


def format_mount_slot_footprint(ref: str, x: float, y: float) -> str:
    """Create an embedded KiCad 10 footprint for an M3 Eurorack oval mounting slot."""
    hw = MOUNT_SLOT_W_MM / 2.0 + 0.25
    hh = MOUNT_SLOT_H_MM / 2.0 + 0.25
    descr = (
        f"Eurorack M3 oval mounting slot ({MOUNT_SLOT_H_MM}x{MOUNT_SLOT_W_MM}mm NPTH)"
    )
    return f"""\t(footprint "Eurorack_Panel:MountingSlot_M3_3.2x5.5mm_NPTH"
\t\t(layer "F.Cu")
\t\t(uuid "{det_uuid(f"fp_{ref}")}")
\t\t(at {x:g} {y:g})
\t\t(descr "{descr}")
\t\t(tags "eurorack m3 mounting slot npth")
\t\t(attr board_only exclude_from_pos_files exclude_from_bom)
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{det_uuid(f"fp_{ref}_ref")}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "M3_SLOT"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{det_uuid(f"fp_{ref}_val")}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(fp_rect
\t\t\t(start {-hw:g} {-hh:g})
\t\t\t(end {hw:g} {hh:g})
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_crtyd")}")
\t\t)
\t\t(pad "" np_thru_hole oval
\t\t\t(at 0 0)
\t\t\t(size {MOUNT_SLOT_W_MM:g} {MOUNT_SLOT_H_MM:g})
\t\t\t(drill oval {MOUNT_SLOT_W_MM:g} {MOUNT_SLOT_H_MM:g})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{det_uuid(f"fp_{ref}_pad")}")
\t\t)
\t)"""


def build_panel_sexpr(bbox: dict[str, float], jacks: list[dict]) -> str:
    """Build the complete KiCad 10 `.kicad_pcb` S-expression for the 4HP front panel."""
    # Center the 108.0 mm main PCB vertically inside the 128.5 mm 3U panel (+10.25 mm)
    pcb_h = bbox["max_y"] - bbox["min_y"]
    overhang_y = (PANEL_HEIGHT_MM - pcb_h) / 2.0

    panel_x0 = bbox["min_x"]
    panel_x1 = panel_x0 + PANEL_WIDTH_MM
    panel_y0 = round(bbox["min_y"] - overhang_y, 4)
    panel_y1 = round(panel_y0 + PANEL_HEIGHT_MM, 4)
    center_x = (panel_x0 + panel_x1) / 2.0

    # Mounting slot global coordinates
    mount_x = panel_x0 + MOUNT_X_LOCAL_MM
    mount_top_y = panel_y0 + MOUNT_TOP_Y_LOCAL_MM
    mount_bot_y = panel_y0 + MOUNT_BOT_Y_LOCAL_MM

    footprints_str = "\n".join(
        [
            format_mount_slot_footprint("H1", mount_x, mount_top_y),
            format_mount_slot_footprint("H2", mount_x, mount_bot_y),
            *(format_jack_footprint(j, panel_x0, panel_y0) for j in jacks),
        ]
    )

    # Row Y positions in global coordinates:
    # Row 1: 38.98, Row 2: 53.48, Row 3: 91.98, Row 4: 106.48
    r1_y = jacks[0]["bushing_y"]
    r2_y = jacks[2]["bushing_y"]
    r3_y = jacks[4]["bushing_y"]
    r4_y = jacks[6]["bushing_y"]
    col1_x = jacks[0]["bushing_x"]
    col2_x = jacks[1]["bushing_x"]

    # Label Y positions (outside the 4.75mm nut radius + margin)
    r1_lbl_y = round(r1_y - 7.28, 2)  # 31.70 mm
    r2_lbl_y = round(r2_y + 7.32, 2)  # 60.80 mm
    r3_lbl_y = round(r3_y - 7.28, 2)  # 84.70 mm
    r4_lbl_y = round(r4_y + 7.32, 2)  # 113.80 mm
    mid_norm_y = round((r2_lbl_y + r3_lbl_y) / 2.0, 2)

    return f"""(kicad_pcb
\t(version 20260206)
\t(generator "pcbnew")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t\t(39 "User.1" user)
\t\t(41 "User.2" user)
\t\t(43 "User.3" user)
\t\t(45 "User.4" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(grid_origin {panel_x0:g} {panel_y0:g})
\t\t(aux_axis_origin {panel_x0:g} {panel_y0:g})
\t\t(tenting
\t\t\t(front yes)
\t\t\t(back yes)
\t\t)
\t\t(covering
\t\t\t(front yes)
\t\t\t(back yes)
\t\t)
\t\t(plugging
\t\t\t(front yes)
\t\t\t(back yes)
\t\t)
\t\t(capping no)
\t\t(filling no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00000000_00000000_55555555_5755f5ff)
\t\t\t(plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12)
\t\t\t(dashed_line_gap_ratio 3)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(pdf_metadata yes)
\t\t\t(pdf_single_document no)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plot_black_and_white yes)
\t\t\t(sketchpadsonfab no)
\t\t\t(plotpadnumbers no)
\t\t\t(hidednponfab no)
\t\t\t(sketchdnponfab yes)
\t\t\t(crossoutdnponfab yes)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "production/panel/")
\t\t)
\t)
{footprints_str}
\t(gr_rect
\t\t(start {panel_x0:g} {panel_y0:g})
\t\t(end {panel_x1:g} {panel_y1:g})
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(locked yes)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{det_uuid("edge_cuts_rect")}")
\t)
\t(gr_rect
\t\t(start {bbox["min_x"]:g} {bbox["min_y"]:g})
\t\t(end {bbox["max_x"]:g} {bbox["max_y"]:g})
\t\t(stroke
\t\t\t(width 0.12)
\t\t\t(type dash)
\t\t)
\t\t(fill no)
\t\t(layer "B.Fab")
\t\t(uuid "{det_uuid("main_pcb_outline_ref")}")
\t)
\t(gr_line
\t\t(start {panel_x0 + 2.0:g} {panel_y0 + 13.0:g})
\t\t(end {panel_x1 - 2.0:g} {panel_y0 + 13.0:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("header_line_top")}")
\t)
\t(gr_text "BUF MULT"
\t\t(at {center_x:g} {panel_y0 + 10.25:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("title_buf_mult")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.8 1.8)
\t\t\t\t(thickness 0.3)
\t\t\t\t(bold yes)
\t\t\t)
\t\t)
\t)
\t(gr_rect
\t\t(start {col1_x - 3.6:g} {r1_lbl_y - 1.45:g})
\t\t(end {col1_x + 3.6:g} {r1_lbl_y + 1.45:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("badge_in1")}")
\t)
\t(gr_text "IN 1"
\t\t(at {col1_x:g} {r1_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_in1")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.22)
\t\t\t\t(bold yes)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 1A"
\t\t(at {col2_x:g} {r1_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out1a")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 1B"
\t\t(at {col1_x:g} {r2_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out1b")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 1C"
\t\t(at {col2_x:g} {r2_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out1c")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_line
\t\t(start {col1_x:g} {r2_lbl_y + 3.0:g})
\t\t(end {col1_x:g} {r3_lbl_y - 3.2:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type dash)
\t\t)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("norm_cascade_line")}")
\t)
\t(gr_line
\t\t(start {col1_x - 1.1:g} {r3_lbl_y - 4.5:g})
\t\t(end {col1_x:g} {r3_lbl_y - 3.0:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("norm_arrow_l")}")
\t)
\t(gr_line
\t\t(start {col1_x + 1.1:g} {r3_lbl_y - 4.5:g})
\t\t(end {col1_x:g} {r3_lbl_y - 3.0:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("norm_arrow_r")}")
\t)
\t(gr_text "NORM"
\t\t(at {col2_x - 1.5:g} {mid_norm_y - 1.2:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_norm_1")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.1 1.1)
\t\t\t\t(thickness 0.18)
\t\t\t)
\t\t)
\t)
\t(gr_text "1 -> 2"
\t\t(at {col2_x - 1.5:g} {mid_norm_y + 1.2:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_norm_2")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.1 1.1)
\t\t\t\t(thickness 0.18)
\t\t\t)
\t\t)
\t)
\t(gr_rect
\t\t(start {col1_x - 3.6:g} {r3_lbl_y - 1.45:g})
\t\t(end {col1_x + 3.6:g} {r3_lbl_y + 1.45:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(fill no)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("badge_in2")}")
\t)
\t(gr_text "IN 2"
\t\t(at {col1_x:g} {r3_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_in2")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.22)
\t\t\t\t(bold yes)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 2A"
\t\t(at {col2_x:g} {r3_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out2a")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 2B"
\t\t(at {col1_x:g} {r4_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out2b")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_text "OUT 2C"
\t\t(at {col2_x:g} {r4_lbl_y:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("lbl_out2c")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.2 1.2)
\t\t\t\t(thickness 0.2)
\t\t\t)
\t\t)
\t)
\t(gr_line
\t\t(start {panel_x0 + 2.0:g} {panel_y1 - 19.5:g})
\t\t(end {panel_x1 - 2.0:g} {panel_y1 - 19.5:g})
\t\t(stroke
\t\t\t(width 0.25)
\t\t\t(type solid)
\t\t)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("footer_line_bot")}")
\t)
\t(gr_text "1:3 / 1:6"
\t\t(at {center_x:g} {panel_y1 - 16.0:g} 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{det_uuid("footer_subtitle")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.3 1.3)
\t\t\t\t(thickness 0.22)
\t\t\t\t(bold yes)
\t\t\t)
\t\t)
\t)
\t(gr_text "JLCJLCJLCJLC"
\t\t(at {center_x:g} {(r2_y + r3_y) / 2.0:g} 0)
\t\t(layer "B.SilkS")
\t\t(uuid "{det_uuid("jlc_order_placeholder")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.0 1.0)
\t\t\t\t(thickness 0.15)
\t\t\t)
\t\t\t(justify mirror)
\t\t)
\t)
\t(gr_text "BUF MULT 4HP"
\t\t(at {center_x:g} {panel_y0 + 16.0:g} 0)
\t\t(layer "B.SilkS")
\t\t(uuid "{det_uuid("rear_panel_title")}")
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.0 1.0)
\t\t\t\t(thickness 0.15)
\t\t\t)
\t\t\t(justify mirror)
\t\t)
\t)
\t(zone
\t\t(net "GND")
\t\t(layer "F.Cu")
\t\t(uuid "{det_uuid("zone_f_cu")}")
\t\t(hatch edge 0.5)
\t\t(priority 1)
\t\t(connect_pads yes
\t\t\t(clearance 0.4)
\t\t)
\t\t(min_thickness 0.25)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t\t(island_removal_mode 0)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {panel_x0:g} {panel_y0:g})
\t\t\t\t(xy {panel_x1:g} {panel_y0:g})
\t\t\t\t(xy {panel_x1:g} {panel_y1:g})
\t\t\t\t(xy {panel_x0:g} {panel_y1:g})
\t\t\t)
\t\t)
\t)
\t(zone
\t\t(net "GND")
\t\t(layer "B.Cu")
\t\t(uuid "{det_uuid("zone_b_cu")}")
\t\t(hatch edge 0.5)
\t\t(priority 1)
\t\t(connect_pads yes
\t\t\t(clearance 0.4)
\t\t)
\t\t(min_thickness 0.25)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t\t(island_removal_mode 0)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {panel_x0:g} {panel_y0:g})
\t\t\t\t(xy {panel_x1:g} {panel_y0:g})
\t\t\t\t(xy {panel_x1:g} {panel_y1:g})
\t\t\t\t(xy {panel_x0:g} {panel_y1:g})
\t\t\t)
\t\t)
\t)
\t(embedded_fonts no)
)
"""


def refill_zones_with_kicad(pcb_path: pathlib.Path) -> None:
    """Refill all copper zones in-place using KiCad 10's Python `pcbnew` API."""
    kicad_python = pathlib.Path(
        "/Applications/KiCad/KiCad.app/Contents/Frameworks/"
        "Python.framework/Versions/Current/bin/python3"
    )
    if not kicad_python.exists():
        print(
            "Warning: KiCad Python runtime not found; skipping zone fill.",
            file=sys.stderr,
        )
        return

    fill_code = (
        "import pcbnew; "
        f"b = pcbnew.LoadBoard({str(pcb_path)!r}); "
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones()); "
        f"pcbnew.SaveBoard({str(pcb_path)!r}, b)"
    )
    subprocess.run([str(kicad_python), "-c", fill_code], check=True)


def main() -> None:
    bbox, jacks = parse_main_pcb(MAIN_PCB_PATH)
    sexpr = build_panel_sexpr(bbox, jacks)
    PANEL_PCB_PATH.write_text(sexpr, encoding="utf-8")
    refill_zones_with_kicad(PANEL_PCB_PATH)
    print(
        f"Generated and filled zones in {PANEL_PCB_PATH} "
        f"({len(jacks)} jack cutouts + 2 M3 slots)."
    )


if __name__ == "__main__":
    main()
