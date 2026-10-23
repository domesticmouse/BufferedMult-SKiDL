# SKiDL & Eurorack Hardware Design Resources

## Knowledge

- [Repository Skill: SKiDL Circuit & KiCad PCB Design (`../.agents/skills/skidl/SKILL.md`)](../.agents/skills/skidl/SKILL.md)
  Verified local reference for SKiDL environment configuration, `search()` / `show()` / `search_footprints()`, `TEMPLATE` instantiation, `part.fields` BOM dictionary rules, pin indexing, `builtins.NC`, `ERC()`, and `ruff` post-run formatting. Use for: every SKiDL code pattern and lint workflow.
- [Repository Script: JLCPCB / LCSC Live Catalog Search (`../.agents/skills/skidl/scripts/jlcpcb_search.py`)](../.agents/skills/skidl/scripts/jlcpcb_search.py)
  CLI tool querying the live JLCPCB/LCSC component database for stock counts, `Basic` vs. `Extended` feeder status, package footprints, and pricing. Use for: programmatic component sourcing and verifying LCSC `Cxxxxx` part numbers.
- [Repository Skill: BOM Management (`../.agents/skills/bom/SKILL.md`)](../.agents/skills/bom/SKILL.md) & [LCSC Skill (`../.agents/skills/lcsc/SKILL.md`)](../.agents/skills/lcsc/SKILL.md)
  Cross-reference tables for SMD passive packages (`0603`), JLCPCB PCBA CSV formatting (`Comment,Designator,Footprint,LCSC Part #`), and THT vs. SMT assembly partitioning. Use for: BOM architecture and manufacturing handoff.
- [Repository Design Guides: `PCB_LAYOUT_GUIDE.md`](../PCB_LAYOUT_GUIDE.md), [`FRONT_PANEL_GUIDE.md`](../FRONT_PANEL_GUIDE.md), and [`DESIGN_REVIEW.md`](../DESIGN_REVIEW.md)
  Project-specific engineering documentation covering the 4HP PCB layout, `WQP-PJ398SM` (Thonkiconn) jack coordinates, `TL074H` stage assignments, and EMC/DFM verification. Use for: tying Python netlist decisions to physical board layout.
- [Official SKiDL Documentation (devbisme.github.io/skidl)](https://devbisme.github.io/skidl/)
  Canonical upstream reference by Dave Vandenbout for `Part`, `Net`, `Bus`, `@subcircuit`, `NetClass`, and `ERC()`. Use for: deep-diving into SKiDL operator overloading (`+=`, `&`, `|`) and netlist generation internals.
- [Texas Instruments `TL074H` / `TL074` Quad Op-Amp Datasheet](https://www.ti.com/lit/ds/symlink/tl074h.pdf)
  Primary component specification for the `TL074HIDR` (`SOIC-14`) quad op-amp used in each buffered channel. Use for: verifying `SOIC-14` unit pinouts (Units A–D, `V+` on pin 4, `V-` on pin 11) and input/output protection requirements.

## Wisdom (Communities)

- [SKiDL GitHub Discussions (`devbisme/skidl`)](https://github.com/devbisme/skidl/discussions)
  Direct Q&A with the SKiDL author and hardware-as-code practitioners. Use for: edge cases in KiCad 9/10 library parsing, custom `@subcircuit` patterns, and SPICE integration.
- [ModWiggler Music Tech DIY Forum](https://www.modwiggler.com/forum/viewforum.php?f=17)
  Long-running community of Eurorack module designers. Use for: practical wisdom on Eurorack power protection, `1V/Oct` pitch CV buffering tolerances, output series resistance (`470R` vs. `1K`), and panel mechanics.
- [r/synthdiy](https://www.reddit.com/r/synthdiy/)
  Active synthesizer DIY community sharing schematics, JLCPCB assembly builds, and troubleshooting tips. Use for: peer design reviews and sourcing alternatives for audio jacks and potentiometers.
- [KiCad Community Forum](https://forum.kicad.info/)
  High-signal forum with KiCad core developers and librarian maintainers. Use for: symbol/footprint conventions, netlist import behavior in `pcbnew`, and DFM/DRC rules.
