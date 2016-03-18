#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__ast_ul = 35
__ast_ll = 0
__unit = "U/l"
__event_dict = {}
__alias = {"AST": "AST", "SGOT": "AST", "GOT": "AST"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to AST,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "AST" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "AST" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["AST"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        ast_val = float(lis_struct[time]["AST"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        ureg.define('kat = 1 mol / s')
        ureg.define('U = 1.657e-8 kat')
        factor = (ureg.parse_expression(lis_struct[time]["AST"]["unit"])).to(__unit).magnitude
        ast_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["AST"].keys():
        if lis_struct[time]["AST"]["lab_value"] > lis_struct[time]["AST"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST too high (current value {}; reference value {} ({}))".format(lis_struct[time]["AST"]["lab_value"], lis_struct[time]["AST"]["ref_high"], lis_struct[time]["AST"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if ast_val > __ast_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST too high (current value {}; reference value {} ({}))".format(ast_val, __ast_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["AST"].keys():
        if lis_struct[time]["AST"]["lab_value"] < lis_struct[time]["AST"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST too low (current value {}; reference value {} ({}))".format(lis_struct[time]["AST"]["lab_value"], lis_struct[time]["AST"]["ref_low"], lis_struct[time]["AST"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if ast_val < __ast_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST too low (current value {}; reference value {} ({}))".format(ast_val, __ast_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # AST > 1000 suggests ischemia, viral infection, toxicity (Lange Pocket Guide to Diagnostic Tests, 6e, p.531)
    if ast_val > 1000:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "AST markedly elevated ({} ({})); consider ischemia, infection, toxicity".format(ast_val, __unit)
        __event_dict[file_name][event_time].append(event_str)
    
    # AST / ALT > 2 suggests alcoholism (Lange Pocket Guide to Diagnostic Tests, 6e, p.531)
    import lisanalyze_alt
    alt_passthrough = lisanalyze_alt.passthrough(file_name, lis_struct, time, args)
    if alt_passthrough:
        alt, unit = alt_passthrough
        if (ast_val / alt) > 2:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST/ALT > 2 (AST: {}, ALT: {}, AST/ALT: {}); consider alcoholic hepatitis".format(ast_val, alt, ast_val/alt)
            __event_dict[file_name][event_time].append(event_str)

    # AST / ALT > 1 suggests cirrhosis in patients with hepatitis C (Lange Pocket Guide to Diagnostic Tests, 6e, p.73)
    import lisanalyze_alt
    alt_passthrough = lisanalyze_alt.passthrough(file_name, lis_struct, time, args)
    if alt_passthrough:
        alt, unit = alt_passthrough
        if ast_val > alt:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST/ALT > 1 (AST: {}, ALT: {}, AST/ALT: {}); possible cirrhosis if patient has hepatitis C".format(ast_val, alt, ast_val/alt)
            __event_dict[file_name][event_time].append(event_str)

    return False

def get_results():
    """
    Returns dict of AST-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of AST at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "AST" as the standard name
    if ("AST" or "SGOT" or "GOT") in lis_struct[time].keys():
        lis_struct[time] = {__alias[k]: v for k, v in lis_struct[time].items()}

    # Basic checks and value-setting
    if "AST" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["AST"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        ast_val = float(lis_struct[time]["AST"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        ureg.define('kat = 1 mol / s')
        ureg.define('U = 1.657e-8 kat')
        factor = (ureg.parse_expression(lis_struct[time]["AST"]["unit"])).to(__unit).magnitude
        ast_val *= factor
    return ast_val, __unit
