#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__p_ul = 4.5
__p_ll = 2.5
__unit = "mg/dl"
__event_dict = {}
__alias = {"Phosphorus": "P"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to phosphorus,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "P" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "P" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["P"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        p_val = float(lis_struct[time]["P"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["P"]["unit"])).to(__unit, 'chemistry', mw=113.126*ureg('g/mol')).magnitude
        p_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["P"].keys():
        if lis_struct[time]["P"]["lab_value"] > lis_struct[time]["P"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperphosphatemia (current value {}; reference value {} ({}))".format(lis_struct[time]["P"]["lab_value"], lis_struct[time]["P"]["ref_high"], lis_struct[time]["P"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if p_val > __p_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperphosphatemia (current value {}; reference value {} ({}))".format(p_val, __p_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["P"].keys():
        if lis_struct[time]["P"]["lab_value"] < lis_struct[time]["P"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypophosphatemia (current value {}; reference value {} ({}))".format(lis_struct[time]["P"]["lab_value"], lis_struct[time]["P"]["ref_low"], lis_struct[time]["P"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if p_val < __p_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypophosphatemia (current value {}; reference value {} ({}))".format(p_val, __p_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Panic if P < 1 mg/dl (Lange Pocket Guide to Diagnostic Tests, 6e, p.230)
    if p_val < 1:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypophosphatemia ({} ({}))".format(p_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    
    return False

def get_results():
    """
    Returns dict of phosphorus-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of phosphorus at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "P" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "P" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["P"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        p_val = float(lis_struct[time]["P"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["P"]["unit"])).to(__unit, 'chemistry', mw=30.97*ureg('g/mol')).magnitude
        p_val *= factor
    return p_val, __unit
