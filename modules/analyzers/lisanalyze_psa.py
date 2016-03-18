#!/usr/bin/python3
#-*- coding: utf-8 -*-

import re
import sys

# Notes on writing modules:
# 1. Names of variables strictly local to the current module should
# begin with 2 underscores; also, they need to be declared global (since state is maintained)
# 2. __event_dict stores *all* PSA-related events for *all* files. Whether this
# is desirable is up for debate.

# Variables local to module
__psa_current_nadir = float('infinity')
__psa_ul = 400 # 4 ng/ml
__psa_ll = 0
__psa_increases = 0
__psa_last_value = None
__unit = "ng/dl"
__event_dict = {}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for PSA-related events, and puts events
    into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns:    False
    """

    global __psa_current_nadir
    global __psa_last_value
    global __psa_increases

    # Basic checks and value-setting
    if "PSA" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["PSA"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        if re.match(">", lis_struct[time]["PSA"]["lab_value"]):
            psa_val = float('infinity')
        elif re.match("<", lis_struct[time]["PSA"]["lab_value"]):
            psa_val = 0
            __psa_current_nadir = 0
        else:
            psa_val = float(lis_struct[time]["PSA"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["PSA"]["unit"])).to(__unit).magnitude
        psa_val *= factor

    if psa_val < __psa_current_nadir:
        __psa_current_nadir = psa_val

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["PSA"].keys():
        if lis_struct[time]["PSA"]["lab_value"] > lis_struct[time]["PSA"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "PSA too high (current value {} ; reference value {} ({}))".format(lis_struct[time]["PSA"]["lab_value"], lis_struct[time]["PSA"]["ref_high"], lis_struct[time]["PSA"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if psa_val > __psa_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "PSA too high (current value {}; reference value {} ({}))".format(psa_val, __psa_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["PSA"].keys():
        if lis_struct[time]["PSA"]["lab_value"] < lis_struct[time]["PSA"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "PSA too low (current value {}; reference value {} ({}))".format(lis_struct[time]["PSA"]["lab_value"], lis_struct[time]["PSA"]["ref_low"], lis_struct[time]["PSA"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if psa_val < __psa_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "PSA too low (current value {}; reference value {} ({}))".format(psa_val, __psa_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # PSA increase by 2.0 ng/dl (Prostate Cancer Foundation)
    if psa_val - __psa_current_nadir > 2:
        event_name = "PSA biochemical failure (PSA increase by 2.0 ng/dl)"
        event_time = time

        event_str = ""

        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []

        event_str = event_name

        if not args.quiet:
            event_str += "(nadir = {}, value = {} ({}))".format(__psa_current_nadir, psa_val, __unit)

        __event_dict[file_name][event_time].append(event_str)

    # 3 consecutive increases in PSA (Lange Pocket Guide to Diagnostic Tests, 6e, p.239)
    if __psa_last_value is not None and psa_val > __psa_last_value:
        __psa_increases += 1
    else:
        __psa_increases = 0
    if __psa_increases >= 3:
        event_name = "PSA biochemical failure (3 consecutive increases)"
        event_time = time

        event_str = ""

        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []

        event_str = event_name
        if not args.quiet:
            event_str += "(nadir = {}, value = {} ({}))".format(__psa_current_nadir, psa_val, __unit)

        __event_dict[file_name][event_time].append(event_str)

    __psa_last_value = psa_val

    return False

def get_results():
    """
    Returns dict of PSA-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of PSA at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """

    # Basic checks and value-setting
    if "PSA" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["PSA"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        psa_val = float(lis_struct[time]["PSA"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        factor = (ureg.parse_expression(lis_struct[time]["PSA"]["unit"])).to(__unit).magnitude
        psa_val *= factor
    return psa_val, __unit
