#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__afp_ul = 0
__afp_ll = 15
__unit = "ng/ml"
__event_dict = {}
__alias = {"AFP": "AFP", "aFP": "AFP"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to alpha-fetoprotein,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    # Use "AFP" as the standard name
    for k in list(lis_struct[time]):
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "AFP" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["AFP"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        afp_val = float(lis_struct[time]["AFP"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        lis_struct[time]["AFP"]["unit"] = lis_struct[time]["AFP"]["unit"].lower()
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["AFP"]["unit"])).to(__unit).magnitude
        afp_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["AFP"].keys():
        if lis_struct[time]["AFP"]["lab_value"] > lis_struct[time]["AFP"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High AFP (current value {}; reference value {} ({}))".format(lis_struct[time]["AFP"]["lab_value"], lis_struct[time]["AFP"]["ref_high"], lis_struct[time]["AFP"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if afp_val > __afp_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High AFP (current value {}; reference value {} ({}))".format(afp_val, __na_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["AFP"].keys():
        if lis_struct[time]["AFP"]["lab_value"] < lis_struct[time]["AFP"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low AFP (current value {}; reference value {} ({}))".format(lis_struct[time]["AFP"]["lab_value"], lis_struct[time]["AFP"]["ref_low"], lis_struct[time]["AFP"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if afp_val < __afp_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low AFP (current value {}; reference value {} ({}))".format(afp_val, __afp_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    return False

def get_results():
    """
    Returns dict of AFP-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of sodium at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "AFP" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "AFP" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["AFP"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        na_val = float(lis_struct[time]["AFP"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        lis_struct[time]["AFP"]["unit"] = lis_struct[time]["AFP"]["unit"].lower()
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["AFP"]["unit"])).to(__unit).magnitude
        afp_val *= factor
    return na_val, __unit
