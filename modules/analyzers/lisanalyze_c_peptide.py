#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__c_peptide_ul = 4
__c_peptide_ll = 0.8
__unit = "ng/ml"
__event_dict = {}
__alias = {"C-peptide": "C-peptide", "C peptide": "C-peptide"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to C-peptide,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "C-peptide" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "C-peptide" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["C-peptide"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        c_peptide_val = float(lis_struct[time]["C-peptide"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of C-peptide (C129H211N35O48) = 3020.29
        factor = (ureg.parse_expression(lis_struct[time]["C-peptide"]["unit"])).to(__unit, 'chemistry', mw=3020.29*ureg('g/mol')).magnitude
        c_peptide_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["C-peptide"].keys():
        if lis_struct[time]["C-peptide"]["lab_value"] > lis_struct[time]["C-peptide"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High C-peptide (current value {}; reference value {} ({}))".format(lis_struct[time]["C-peptide"]["lab_value"], lis_struct[time]["C-peptide"]["ref_high"], lis_struct[time]["C-peptide"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if c_peptide_val > __c_peptide_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "High C-peptide (current value {}; reference value {} ({}))".format(c_peptide_val, __c_peptide_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["c_peptide"].keys():
        if lis_struct[time]["C-peptide"]["lab_value"] < lis_struct[time]["C-peptide"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low C-peptide (current value {}; reference value {} ({}))".format(lis_struct[time]["C-peptide"]["lab_value"], lis_struct[time]["C-peptide"]["ref_low"], lis_struct[time]["C-peptide"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if c_peptide_val < __c_peptide_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "Low C-peptide (current value {}; reference value {} ({}))".format(c_peptide_val, __c_peptide_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # C-peptide >= 2 nmol/l (6.04058 ng/ml) suggestive of insulinoma (Lange Pocket Guide to Diagnostic Tests, 6e, p.83)
    if c_peptide_val > 6.04058:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "Very high C-peptide; suggestive of insulinoma ({} ({}))".format(c_peptide_val, __unit)
        __event_dict[file_name][event_time].append(event_str)

    return False

def get_results():
    """
    Returns dict of C-peptide-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of C-peptide at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "C-peptide" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})
    # Basic checks and value-setting
    if "C-peptide" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["C-peptide"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        c_peptide_val = float(lis_struct[time]["C-peptide"]["lab_value"])
    else:
        return None
    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        # Molecular weight of C-peptide (C129H211N35O48) = 3020.29
        factor = (ureg.parse_expression(lis_struct[time]["C-peptide"]["unit"])).to(__unit, 'chemistry', mw=3020.29*ureg('g/mol')).magnitude
        c_peptide_val *= factor
    return c_peptide_val, __unit
