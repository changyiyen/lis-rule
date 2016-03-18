#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__prl_ul = 25
__prl_ll = 0
__unit = "ng/ml"
__event_dict = {}
__alias = {"PRL": "PRL", "Prolactin": "PRL"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to prolactin,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "PRL" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "PRL" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["PRL"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        prl_val = float(lis_struct[time]["PRL"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["PRL"]["unit"])).to(__unit).magnitude
        prl_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["PRL"].keys():
        if lis_struct[time]["PRL"]["lab_value"] > lis_struct[time]["PRL"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Prolactin too high (current value {}; reference value {} ({}))".format(lis_struct[time]["PRL"]["lab_value"], lis_struct[time]["PRL"]["ref_high"], lis_struct[time]["PRL"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if prl_val > __prl_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "PRL too high (current value {}; reference value {} ({}))".format(prl_val, __prl_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # In patients with macroadenoma, PRL is usually > 500 ng/ml; in patients with microadenoma, PRL is usually > 150 (Lange Pocket Guide to Diagnostic Tests, 6e, p.260)
    if prl_val > 500:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "PRL > 500 ng/ml; suspect macroadenoma of pituitary ({} ({}))".format(prl_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    elif prl_val > 150:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "PRL > 150 ng/ml; suspect microadenoma of pituitary ({} ({}))".format(prl_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of prolactin-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of prolactin at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "PRL" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "PRL" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["PRL"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        prl_val = float(lis_struct[time]["PRL"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["PRL"]["unit"])).to(__unit).magnitude
        prl_val *= factor
    return prl_val, __unit
