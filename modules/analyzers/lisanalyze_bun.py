#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__bun_ul = 20
__bun_ll = 8
__unit = "mg/dl"
__event_dict = {}
__alias = {"BUN": "BUN"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to BUN,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "BUN" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "BUN" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["BUN"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        bun_val = float(lis_struct[time]["BUN"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of urea (CH4N2O) = 60.062; molecular weight of N = 14.01
        factor = (ureg.parse_expression(lis_struct[time]["BUN"]["unit"])).to(__unit, 'chemistry', mw=60.06*ureg('g/mol')).magnitude * 60.062/28.02
        bun_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["BUN"].keys():
        if lis_struct[time]["BUN"]["lab_value"] > lis_struct[time]["BUN"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High BUN (current value {}; reference value {} ({}))".format(lis_struct[time]["BUN"]["lab_value"], lis_struct[time]["BUN"]["ref_high"], lis_struct[time]["BUN"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if bun_val > __bun_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High BUN (current value {}; reference value {} ({}))".format(bun_val, __bun_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["BUN"].keys():
        if lis_struct[time]["BUN"]["lab_value"] < lis_struct[time]["BUN"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low BUN (current value {}; reference value {} ({}))".format(lis_struct[time]["BUN"]["lab_value"], lis_struct[time]["BUN"]["ref_low"], lis_struct[time]["BUN"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if bun_val < __bun_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low BUN (current value {}; reference value {} ({}))".format(bun_val, __bun_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Normal blood or serum BUN/creatinine ratio = 10:1 - 20:1 (Lange Pocket Guide to Diagnostic Tests, 6e, p.80)
    import lisanalyze_cr
    cr_passthrough = lisanalyze_cr.passthrough(file_name, lis_struct, time, args)
    if cr_passthrough:
        cr, unit = cr_passthrough
        if (bun_val / cr) > 20:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "BUN/Cr > 20 (BUN: {}, Cr: {}, BUN/Cr: {}); consider dehydration, bleeding, increased catabolism".format(bun_val, cr, bun_val/cr)
            __event_dict[file_name][event_time].append(event_str)
        if (bun_val / cr) < 10:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "BUN/Cr < 10 (BUN: {}, Cr: {}, BUN/Cr: {}); possible acute tubular necrosis, advanced liver disease, low protein intake, hemodialysis".format(bun_val, cr, bun_val/cr)
            __event_dict[file_name][event_time].append(event_str)
    
    return False

def get_results():
    """
    Returns dict of BUN-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of BUN at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "BUN" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "BUN" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["BUN"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        bun_val = float(lis_struct[time]["BUN"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of urea (CH4N2O) = 60.062; molecular weight of N = 14.01
        factor = (ureg.parse_expression(lis_struct[time]["BUN"]["unit"])).to(__unit, 'chemistry', mw=60.06*ureg('g/mol')).magnitude * 60.062/28.02
        bun_val *= factor
    return bun_val, __unit
