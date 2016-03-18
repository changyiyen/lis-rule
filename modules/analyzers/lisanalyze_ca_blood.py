#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__ca_ul = 10.5
__ca_ll = 8.5
__unit = "mg/dl"
__event_dict = {}
__alias = {"Ca": "Ca", "Calcium": "Ca", "CA": "Ca"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to calcium,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "Ca" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "Ca" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Ca"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        ca_val = float(lis_struct[time]["Ca"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["Ca"]["unit"])).to(__unit, 'chemistry', mw=40.08*ureg('g/mol')).magnitude
        ca_val *= factor

    # Correction for albumin (Lange Pocket Guide to Diagnostic Tests, 6e, p.87; note that 'mg' for albumin should be 'g')
    if not args.no_correct:
        import lisanalyze_albumin_blood
        albumin_passthrough = lisanalyze_albumin_blood.passthrough(file_name, lis_struct, time, args)
        if albumin_passthrough:
            albumin, value = albumin_passthrough
            if albumin < 3.4:
                ca_val += (3.4 - albumin) * 0.8

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["Ca"].keys():
        if lis_struct[time]["Ca"]["lab_value"] > lis_struct[time]["Ca"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypercalcemia (current value {}; reference value {} ({}))".format(lis_struct[time]["Ca"]["lab_value"], lis_struct[time]["Ca"]["ref_high"], lis_struct[time]["Ca"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if ca_val > __ca_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypercalcemia (current value {}; reference value {} ({}))".format(ca_val, __ca_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["Ca"].keys():
        if lis_struct[time]["Ca"]["lab_value"] < lis_struct[time]["Ca"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Hypocalcemia (current value {}; reference value {} ({}))".format(lis_struct[time]["Ca"]["lab_value"], lis_struct[time]["Ca"]["ref_low"], lis_struct[time]["Ca"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if ca_val < __ca_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
               __event_dict[file_name][event_time] = []
            event_str = "Hypocalcemia (current value {}; reference value {} ({}))".format(ca_val, __ca_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # Panic if Ca > 13.5 mg/dl or Ca < 6.5 mg/dl (Lange Pocket Guide to Diagnostic Tests, 6e, p.87)
    if ca_val > 13.5:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypercalcemia ({} ({}))".format(ca_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    if ca_val < 6.5:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Severe hypocalcemia ({} ({}))".format(ca_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    return False

def get_results():
    """
    Returns dict of serum or plasma calcium-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of blood calcium at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "Ca" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "Ca" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["Ca"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        ca_val = float(lis_struct[time]["Ca"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["Ca"]["unit"])).to(__unit, 'chemistry', mw=40.08*ureg('g/mol')).magnitude
        ca_val *= factor
    # Correction for albumin (Lange Pocket Guide to Diagnostic Tests, 6e, p.87; note that 'mg' for albumin should be 'g')
    if not args.no_correct:
        import lisanalyze_albumin_blood
        albumin_passthrough = lisanalyze_albumin_blood.passthrough(file_name, lis_struct, time, args)
        if albumin_passthrough:
            albumin, value = albumin_passthrough
            if albumin < 3.4:
                ca_val += (3.4 - albumin) * 0.8
    return ca_val, __unit
