#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__k_ul = 5
__k_ll = 3.5
__unit = "mmol/l"
__event_dict = {}
__alias = {"K": "K", "Potassium": "K"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to potassium,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "K" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "K" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["K"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        k_val = float(lis_struct[time]["K"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        lis_struct[time]["K"]["unit"] = lis_struct[time]["K"]["unit"].lower().replace("eq", "mol")
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["K"]["unit"])).to(__unit).magnitude
        k_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["K"].keys():
        if lis_struct[time]["K"]["lab_value"] > lis_struct[time]["K"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperkalemia (current value {}; reference value {} ({}))".format(lis_struct[time]["K"]["lab_value"], lis_struct[time]["K"]["ref_high"], lis_struct[time]["K"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if k_val > __k_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperkalemia (current value {}; reference value {} ({}))".format(k_val, __k_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["K"].keys():
        if lis_struct[time]["K"]["lab_value"] < lis_struct[time]["K"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypokalemia (current value {}; reference value {} ({}))".format(lis_struct[time]["K"]["lab_value"], lis_struct[time]["K"]["ref_low"], lis_struct[time]["K"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if k_val < __k_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypokalemia (current value {}; reference value {} ({}))".format(k_val, __k_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Panic if K > 6 mmol/l or K < 3 mmol (Lange Pocket Guide to Diagnostic Tests, 6e, p.236)
    if k_val > 6:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hyperkalemia ({} ({}))".format(k_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    if k_val < 3:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypokalemia ({} ({}))".format(k_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of potassium-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of potassium at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "K" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "K" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["K"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        k_val = float(lis_struct[time]["K"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["K"]["unit"])).to(__unit).magnitude
        k_val *= factor
    return k_val, __unit
