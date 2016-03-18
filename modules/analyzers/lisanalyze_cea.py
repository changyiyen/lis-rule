#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__cea_ul = 2.5
__cea_ll = 0
__unit = "ng/ml"
__event_dict = {}
__alias = {"CEA": "CEA"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to carcinoembryonic antigen,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "CEA" as the standard name
    for k in list(lis_struct[time]):
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "CEA" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["CEA"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        cea_val = float(lis_struct[time]["CEA"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        lis_struct[time]["CEA"]["unit"] = lis_struct[time]["CEA"]["unit"].lower()
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["CEA"]["unit"])).to(__unit).magnitude
        cea_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["CEA"].keys():
        if lis_struct[time]["CEA"]["lab_value"] > lis_struct[time]["CEA"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High CEA (current value {}; reference value {} ({}))".format(lis_struct[time]["CEA"]["lab_value"], lis_struct[time]["CEA"]["ref_high"], lis_struct[time]["CEA"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if cea_val > __cea_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High CEA (current value {}; reference value {} ({}))".format(cea_val, __cea_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["CEA"].keys():
        if lis_struct[time]["CEA"]["lab_value"] < lis_struct[time]["CEA"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low CEA (current value {}; reference value {} ({}))".format(lis_struct[time]["CEA"]["lab_value"], lis_struct[time]["CEA"]["ref_low"], lis_struct[time]["CEA"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if cea_val < __cea_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low CEA (current value {}; reference value {} ({}))".format(cea_val, __cea_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Cancer suspicion if elevation > 20 ng/ml; possible breast cancer recurrence if > 5 ng/ml (Lange Pocket Guide to Diagnostic Tests, 6e, p.93)
    if cea_val > 20:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Possible cancer ({} ({}))".format(cea_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    if cea_val > 5:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Possible breast cancer recurrence ({} ({}))".format(cea_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of CEA-related tests.
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
    # Use "CEA" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "CEA" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["CEA"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        cea_val = float(lis_struct[time]["CEA"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        lis_struct[time]["CEA"]["unit"] = lis_struct[time]["CEA"]["unit"].lower()
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["CEA"]["unit"])).to(__unit).magnitude
        cea_val *= factor
    return cea_val, __unit
