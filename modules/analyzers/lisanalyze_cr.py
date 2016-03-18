#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__cr_ul = 0.6
__cr_ll = 1.2
__unit = "mg/dl"
__event_dict = {}
__alias = {"Creatinine": "Cr"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to creatinine,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "Cr" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "Cr" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Cr"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        cr_val = float(lis_struct[time]["Cr"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of creatinine (C4H7N3O) = 113.126
        factor = (ureg.parse_expression(lis_struct[time]["Cr"]["unit"])).to(__unit, 'chemistry', mw=113.126*ureg('g/mol')).magnitude
        cr_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["Cr"].keys():
        if lis_struct[time]["Cr"]["lab_value"] > lis_struct[time]["Cr"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High creatinine (current value {}; reference value {} ({}))".format(lis_struct[time]["Cr"]["lab_value"], lis_struct[time]["Cr"]["ref_high"], lis_struct[time]["Cr"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if cr_val > __cr_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High creatinine (current value {}; reference value {} ({}))".format(cr_val, __cr_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["Cr"].keys():
        if lis_struct[time]["Cr"]["lab_value"] < lis_struct[time]["Cr"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low creatinine (current value {}; reference value {} ({}))".format(lis_struct[time]["Cr"]["lab_value"], lis_struct[time]["Cr"]["ref_low"], lis_struct[time]["Cr"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if cr_val < __cr_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low creatinine (current value {}; reference value {} ({}))".format(cr_val, __cr_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Normal blood or serum BUN/creatinine ratio = 10:1 - 20:1 (Lange Pocket Guide to Diagnostic Tests, 6e, p.80)
    import lisanalyze_bun
    bun_passthrough = lisanalyze_bun.passthrough(file_name, lis_struct, time, args)
    if bun_passthrough:
        bun, unit = bun_passthrough
        if (bun / cr_val) > 20:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "BUN/Cr > 20 (BUN: {}, Cr: {}, BUN/Cr: {}); consider dehydration, bleeding, increased catabolism".format(bun, cr_val, bun/cr_val)
            __event_dict[file_name][event_time].append(event_str)
        if (bun / cr_val) < 10:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "BUN/Cr < 10 (BUN: {}, Cr: {}, BUN/Cr: {}); possible acute tubular necrosis, advanced liver disease, low protein intake, hemodialysis".format(bun, cr_val, bun/cr_val)
            __event_dict[file_name][event_time].append(event_str)
    
    return False

def get_results():
    """
    Returns dict of creatinine-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of creatinine at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "Cr" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "Cr" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Cr"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        cr_val = float(lis_struct[time]["Cr"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of creatinine (C4H7N3O) = 113.126
        factor = (ureg.parse_expression(lis_struct[time]["Cr"]["unit"])).to(__unit, 'chemistry', mw=113.126*ureg('g/mol')).magnitude
        cr_val *= factor
    return cr_val, __unit
