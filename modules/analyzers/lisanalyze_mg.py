#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__mg_ul = 3
__mg_ll = 1.8
__unit = "mg/dl"
__event_dict = {}
__alias = {"Mg": "Mg", "Magnesium": "Mg", "MG": "Mg"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to magnesium,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "Mg" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "Mg" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Mg"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        mg_val = float(lis_struct[time]["Mg"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["Mg"]["unit"])).to(__unit, 'chemistry', mw=24.31*ureg('g/mol')).magnitude
        mg_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["Mg"].keys():
        if lis_struct[time]["Mg"]["lab_value"] > lis_struct[time]["Mg"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypermagnesemia (current value {}; reference value {} ({}))".format(lis_struct[time]["Mg"]["lab_value"], lis_struct[time]["Mg"]["ref_high"], lis_struct[time]["Mg"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if mg_val > __mg_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypermagnesemia (current value {}; reference value {} ({}))".format(mg_val, __mg_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["Mg"].keys():
        if lis_struct[time]["Mg"]["lab_value"] < lis_struct[time]["Mg"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypomagnesemia (current value {}; reference value {} ({}))".format(lis_struct[time]["Mg"]["lab_value"], lis_struct[time]["Mg"]["ref_low"], lis_struct[time]["Mg"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if mg_val < __mg_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypomagnesemia (current value {}; reference value {} ({}))".format(mg_val, __mg_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Panic if Mg > 4.5 mg/dl or Mg < 0.5 mg/dl (Lange Pocket Guide to Diagnostic Tests, 6e, p.205)
    if mg_val > 4.5:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypermagnesemia ({} ({}))".format(mg_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    if mg_val < 0.5:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypomagnesemia ({} ({}))".format(mg_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of magnesium-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of magnesium at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "Mg" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "Mg" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Mg"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        mg_val = float(lis_struct[time]["Mg"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["Mg"]["unit"])).to(__unit, 'chemistry', mw=24.31*ureg('g/mol')).magnitude
        mg_val *= factor
    return mg_val, __unit
