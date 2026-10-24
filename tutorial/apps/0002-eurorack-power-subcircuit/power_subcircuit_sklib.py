from skidl import SKIDL, TEMPLATE, Alias, Part, Pin, SchLib
from skidl.pin import pin_types

SKIDL_lib_version = "0.0.1"

power_subcircuit = SchLib(tool=SKIDL).add_parts(
    *[
        Part(
            name="Conn_02x05_Odd_Even",
            dest=TEMPLATE,
            tool=SKIDL,
            aliases=Alias({"Conn_02x05_Odd_Even"}),
            ref_prefix="J",
            fplist=[""],
            footprint="Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical",
            keywords="connector",
            description="Generic connector, double row, 02x05, odd/even pin numbering scheme (row 1 odd numbers, row 2 even numbers), script generated (kicad-library-utils/schlib/autogen/connector/)",
            datasheet="",
            pins=[
                Pin(num="1", name="Pin_1", func=pin_types.PASSIVE, unit=1),
                Pin(num="2", name="Pin_2", func=pin_types.PASSIVE, unit=1),
                Pin(num="3", name="Pin_3", func=pin_types.PASSIVE, unit=1),
                Pin(num="4", name="Pin_4", func=pin_types.PASSIVE, unit=1),
                Pin(num="5", name="Pin_5", func=pin_types.PASSIVE, unit=1),
                Pin(num="6", name="Pin_6", func=pin_types.PASSIVE, unit=1),
                Pin(num="7", name="Pin_7", func=pin_types.PASSIVE, unit=1),
                Pin(num="8", name="Pin_8", func=pin_types.PASSIVE, unit=1),
                Pin(num="9", name="Pin_9", func=pin_types.PASSIVE, unit=1),
                Pin(num="10", name="Pin_10", func=pin_types.PASSIVE, unit=1),
            ],
            unit_defs=[],
        ),
        Part(
            name="D_Schottky",
            dest=TEMPLATE,
            tool=SKIDL,
            aliases=Alias({"D_Schottky"}),
            ref_prefix="D",
            fplist=[""],
            footprint="Diode_SMD:D_SOD-323",
            keywords="diode Schottky",
            description="Schottky diode",
            datasheet="",
            pins=[
                Pin(num="1", name="K", func=pin_types.PASSIVE, unit=1),
                Pin(num="2", name="A", func=pin_types.PASSIVE, unit=1),
            ],
            unit_defs=[],
        ),
        Part(
            name="C_Polarized",
            dest=TEMPLATE,
            tool=SKIDL,
            aliases=Alias({"C_Polarized"}),
            ref_prefix="C",
            fplist=[""],
            footprint="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
            keywords="cap capacitor",
            description="Polarized capacitor",
            datasheet="",
            pins=[
                Pin(num="1", func=pin_types.PASSIVE, unit=1),
                Pin(num="2", func=pin_types.PASSIVE, unit=1),
            ],
            unit_defs=[],
        ),
    ]
)
