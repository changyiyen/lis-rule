#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__glucose_ul = 110
__glucose_ll = 60
__unit = "mg/dl"
__event_dict = {}
__alias = {"glucose": "glucose", "GLU": "glucose", "GLU-AC": "glucose"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to glucose,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "glucose" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "glucose" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["glucose"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        glucose_val = float(lis_struct[time]["glucose"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of glucose (C6H12O6) = 180.16
        factor = (ureg.parse_expression(lis_struct[time]["glucose"]["unit"])).to(__unit, 'chemistry', mw=180.16*ureg('g/mol')).magnitude
        glucose_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["glucose"].keys():
        if lis_struct[time]["glucose"]["lab_value"] > lis_struct[time]["glucose"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperglycemia (current value {}; reference value {} ({}))".format(lis_struct[time]["glucose"]["lab_value"], lis_struct[time]["glucose"]["ref_high"], lis_struct[time]["glucose"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if glucose_val > __glucose_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hyperglycemia (current value {}; reference value {} ({}))".format(glucose_val, __glucose_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["glucose"].keys():
        if lis_struct[time]["glucose"]["lab_value"] < lis_struct[time]["glucose"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypoglycemia (current value {}; reference value {} ({}))".format(lis_struct[time]["glucose"]["lab_value"], lis_struct[time]["glucose"]["ref_low"], lis_struct[time]["glucose"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if glucose_val < __glucose_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypoglycemia (current value {}; reference value {} ({}))".format(glucose_val, __glucose_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Panic if glucose > 500 mg/dl or glucose < 40 mg/dl (Lange Pocket Guide to Diagnostic Tests, 6e, p.147)
    if glucose_val > 500:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hyperglycemia ({} ({}))".format(glucose_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    if glucose_val < 40:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypoglycemia ({} ({}))".format(glucose_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of glucose-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of glucose at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "glucose" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "glucose" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["glucose"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        glucose_val = float(lis_struct[time]["glucose"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of glucose (C6H12O6) = 180.16
        factor = (ureg.parse_expression(lis_struct[time]["glucose"]["unit"])).to(__unit, 'chemistry', mw=180.16*ureg('g/mol')).magnitude
        glucose_val *= factor
    return glucose_val, __unit
