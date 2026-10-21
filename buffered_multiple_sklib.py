from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

from skidl.pin import pin_types

SKIDL_lib_version = '0.0.1'

buffered_multiple = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Conn_02x05_Odd_Even', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Conn_02x05_Odd_Even'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical', 'keywords':'connector', 'description':'Generic connector, double row, 02x05, odd/even pin numbering scheme (row 1 odd numbers, row 2 even numbers), script generated (kicad-library-utils/schlib/autogen/connector/)', 'datasheet':'', 'pins':[
            Pin(num='1',name='Pin_1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='Pin_2',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='Pin_3',func=pin_types.PASSIVE,unit=1),
            Pin(num='4',name='Pin_4',func=pin_types.PASSIVE,unit=1),
            Pin(num='5',name='Pin_5',func=pin_types.PASSIVE,unit=1),
            Pin(num='6',name='Pin_6',func=pin_types.PASSIVE,unit=1),
            Pin(num='7',name='Pin_7',func=pin_types.PASSIVE,unit=1),
            Pin(num='8',name='Pin_8',func=pin_types.PASSIVE,unit=1),
            Pin(num='9',name='Pin_9',func=pin_types.PASSIVE,unit=1),
            Pin(num='10',name='Pin_10',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'D_Schottky', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'D_Schottky'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'Diode_SMD:D_SMA', 'keywords':'diode Schottky', 'description':'Schottky diode', 'datasheet':'', 'pins':[
            Pin(num='1',name='K',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'C_Polarized', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'C_Polarized'}), 'ref_prefix':'C', 'fplist':[''], 'footprint':'Capacitor_THT:CP_Radial_D5.0mm_P2.00mm', 'keywords':'cap capacitor', 'description':'Polarized capacitor', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'TL074', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'TL074'}), 'ref_prefix':'U', 'fplist':['', ''], 'footprint':'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm', 'keywords':'quad opamp', 'description':'Quad Low-Noise JFET-Input Operational Amplifiers, DIP-14/SOIC-14', 'datasheet':'http://www.ti.com/lit/ds/symlink/tl071.pdf', 'pins':[
            Pin(num='1',func=pin_types.OUTPUT,unit=1),
            Pin(num='2',name='-',func=pin_types.INPUT,unit=1),
            Pin(num='3',name='+',func=pin_types.INPUT,unit=1),
            Pin(num='5',name='+',func=pin_types.INPUT,unit=2),
            Pin(num='6',name='-',func=pin_types.INPUT,unit=2),
            Pin(num='7',func=pin_types.OUTPUT,unit=2),
            Pin(num='8',func=pin_types.OUTPUT,unit=3),
            Pin(num='9',name='-',func=pin_types.INPUT,unit=3),
            Pin(num='10',name='+',func=pin_types.INPUT,unit=3),
            Pin(num='12',name='+',func=pin_types.INPUT,unit=4),
            Pin(num='13',name='-',func=pin_types.INPUT,unit=4),
            Pin(num='14',func=pin_types.OUTPUT,unit=4),
            Pin(num='4',name='V+',func=pin_types.PWRIN,unit=5),
            Pin(num='11',name='V-',func=pin_types.PWRIN,unit=5)], 'unit_defs':[{'label': 'uA', 'num': 1, 'pin_nums': ['3', '2', '1']},{'label': 'uB', 'num': 2, 'pin_nums': ['7', '6', '5']},{'label': 'uC', 'num': 3, 'pin_nums': ['9', '8', '10']},{'label': 'uD', 'num': 4, 'pin_nums': ['14', '13', '12']},{'label': 'uE', 'num': 5, 'pin_nums': ['11', '4']}] }),
        Part(**{ 'name':'C', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'C'}), 'ref_prefix':'C', 'fplist':[''], 'footprint':'Capacitor_SMD:C_0805_2012Metric', 'keywords':'cap capacitor', 'description':'Unpolarized capacitor', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'AudioJack2_SwitchT', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'AudioJack2_SwitchT'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles', 'keywords':'audio jack receptacle mono headphones phone TS connector', 'description':'Audio Jack, 2 Poles (Mono / TS), Switched T Pole (Normalling)', 'datasheet':'', 'pins':[
            Pin(num='S',func=pin_types.PASSIVE,unit=1),
            Pin(num='T',func=pin_types.PASSIVE,unit=1),
            Pin(num='TN',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'R', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'R'}), 'ref_prefix':'R', 'fplist':[''], 'footprint':'Resistor_SMD:R_0805_2012Metric', 'keywords':'R res resistor', 'description':'Resistor', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] })])