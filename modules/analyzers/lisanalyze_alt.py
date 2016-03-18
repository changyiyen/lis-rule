#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sys

# Variables local to module
__alt_ul = 35
__alt_ll = 0
__unit = "U/l"
__event_dict = {}
__alias = {"ALT": "ALT", "SGPT": "ALT", "GPT": "ALT"}

def analyze(file_name, lis_struct, time, args):
    """
    Analyzes LIS results, looking for events related to ALT,
    and puts events into a dict {file_name -> {event_time -> (event_str)}}.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: False
    """

    #global __alias

    # Use "ALT" as the standard name
    for k in lis_struct[time].keys():
        if k in __alias.keys():
            lis_struct[time].update({__alias[k]: lis_struct[time][k]})

    # Basic checks and value-setting
    if "ALT" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["ALT"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        alt_val = float(lis_struct[time]["ALT"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        ureg.define('kat = 1 mol / s')
        ureg.define('U = 1.657e-8 kat')
        factor = (ureg.parse_expression(lis_struct[time]["ALT"]["unit"])).to(__unit).magnitude
        alt_val *= factor

    # Out-of-normal-range warning; provided values take precedence
    if "ref_high" in lis_struct[time]["ALT"].keys():
        if lis_struct[time]["ALT"]["lab_value"] > lis_struct[time]["ALT"]["ref_high"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "ALT too high (current value {}; reference value {} ({}))".format(lis_struct[time]["ALT"]["lab_value"], lis_struct[time]["ALT"]["ref_high"], lis_struct[time]["ALT"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: higher reference value not provided; falling back to built-in value", file=sys.stderr)
        if alt_val > __alt_ul:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "ALT too high (current value {}; reference value {} ({}))".format(alt_val, __alt_ul, __unit)
            __event_dict[file_name][event_time].append(event_str)
    if "ref_low" in lis_struct[time]["ALT"].keys():
        if lis_struct[time]["ALT"]["lab_value"] < lis_struct[time]["ALT"]["ref_low"]:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "ALT too low (current value {}; reference value {} ({}))".format(lis_struct[time]["ALT"]["lab_value"], lis_struct[time]["ALT"]["ref_low"], lis_struct[time]["ALT"]["unit"])
            __event_dict[file_name][event_time].append(event_str)
    else:
        if args.warn:
            print("WARNING: lower reference value not provided; falling back to built-in value", file=sys.stderr)
        if alt_val < __alt_ll:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "ALT too low (current value {}; reference value {} ({}))".format(alt_val, __alt_ll, __unit)
            __event_dict[file_name][event_time].append(event_str)

    # ALT > 1000 suggests ischemia, viral infection, toxicity (Lange Pocket Guide to Diagnostic Tests, 6e, p.531)
    if alt_val > 1000:
        event_time = time
        if file_name not in __event_dict.keys():
            __event_dict[file_name] = {}
        if event_time not in __event_dict[file_name].keys():
            __event_dict[file_name][event_time] = []
        event_str = "ALT markedly elevated ({} ({})); consider ischemia, infection, toxicity".format(alt_val, __unit)
        __event_dict[file_name][event_time].append(event_str)

    # AST / ALT > 2 suggests alcoholism (Lange Pocket Guide to Diagnostic Tests, 6e, p.531)
    import lisanalyze_ast
    ast_passthrough = lisanalyze_ast.passthrough(file_name, lis_struct, time, args)
    if ast_passthrough:
        ast, unit = alt_passthrough
        if (ast / alt_val) > 2:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST/ALT > 2 (AST: {}, ALT: {}, AST/ALT: {}); consider alcoholic hepatitis".format(ast, alt_val, ast/alt_val)
            __event_dict[file_name][event_time].append(event_str)

    # AST / ALT > 1 suggests cirrhosis in patients with hepatitis C (Lange Pocket Guide to Diagnostic Tests, 6e, p.73)
    import lisanalyze_ast
    ast_passthrough = lisanalyze_ast.passthrough(file_name, lis_struct, time, args)
    if ast_passthrough:
        ast, unit = alt_passthrough
        if ast > alt_val:
            event_time = time
            if file_name not in __event_dict.keys():
                __event_dict[file_name] = {}
            if event_time not in __event_dict[file_name].keys():
                __event_dict[file_name][event_time] = []
            event_str = "AST/ALT > 1 (AST: {}, ALT: {}, AST/ALT: {}); possible cirrhosis if patient has hepatitis C".format(ast, alt_val, ast/alt_val)
            __event_dict[file_name][event_time].append(event_str)

    return False

def get_results():
    """
    Returns dict of ALT-related tests.
    Parameters: none
    Return value: dict {file_name -> {event_time -> (event_str)}}
    """
    return __event_dict

def passthrough(file_name, lis_struct, time, args):
    """
    Passes tuple of (value, unit) of ALT at indicated time, in a standardized form.

    :param file_name: (str) name of current JSON file being read
    :param lis_struct: (dict) dict containing item and value pairs
    :param time: (str) time when results were obtained (as contained in JSON file)
    :param args: (dict) switches provided to lisanalyze.py via argparse

    :returns: tuple (value, unit)
    """
    # Use "ALT" as the standard name
    if ("ALT" or "SGPT" or "GPT") in lis_struct[time].keys():
        lis_struct[time] = {__alias[k]: v for k, v in lis_struct[time].items()}

    # Basic checks and value-setting
    if "ALT" in lis_struct[time].keys():
        if args.warn and lis_struct[time]["ALT"]["unit"] != __unit:
            print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
        alt_val = float(lis_struct[time]["ALT"]["lab_value"])
    else:
        return None

    # Unit conversion
    if args.convert:
        import pint
        ureg = pint.UnitRegistry()
        ureg.define('kat = 1 mol / s')
        ureg.define('U = 1.657e-8 kat')
        factor = (ureg.parse_expression(lis_struct[time]["ALT"]["unit"])).to(__unit).magnitude
        alt_val *= factor
    return alt_val, __unit
