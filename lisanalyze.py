#!/usr/bin/python3
#-*- coding: utf-8 -*-
import argparse
import io
import json
import re
import sys
import datetime
import os

import jsonschema

import modules
from modules.analyzers import *

# Build argument parser
parser = argparse.ArgumentParser(
        description='Simple analyzer for LIS data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--compat', action='store_true', help='disables ISO8601 time format check')
parser.add_argument('-d', '--dir', type=str, default='', help='specify directory where result files will be put')
parser.add_argument('-f', '--file', type=str, nargs = '*', default=["data.txt"], help='set path of JSON-formatted LIS data files to read')
parser.add_argument('-o', '--output', type=str, help='set path of output file (only when -r specified)')
parser.add_argument('-r', '--human-readable', action='store_true', help='human-readable output')
parser.add_argument('-s', '--suffix', type=str, default='_result.json', help='set suffix of output files (only when -r not specified)')
parser.add_argument('-q', '--quiet', action='store_true', help='suppresses verbose messages')
parser.add_argument('-w', '--warn', action='store_true', help='enable extra warnings')
parser.add_argument('--no-correct', action='store_true', help='disable corrections for biochemical data')
parser.add_argument('--no-convert', action='store_false', dest='convert', help='disable unit conversion (conversion enabled by default)')
parser.add_argument('--version', action='version', version='%(prog)s 0.1 "Blizzard"')
args = parser.parse_args()

def merge(*results):
        result_dict = {}
        for item in results:
                for file_name in item.keys():
                        for event_time in item[file_name].keys():
                                if file_name not in result_dict.keys():
                                        result_dict[file_name] = {}
                                if event_time not in result_dict[file_name].keys():
                                        result_dict[file_name][event_time] = []
                                result_dict[file_name][event_time].extend(item[file_name][event_time])
        return result_dict

# Load data files from list
for file_name in args.file:
        lis_file = io.open(file_name)
        try:
                lis_struct = json.load(lis_file)
        except ValueError:
                raise Exception("Invalid JSON file")

        # Basic checks:
        # 0. Check against schema
        # 1. Time format should be ISO8061 unless overridden by '--compat'
        # 2. Level 1 values should be dicts
        schema = {
                "$schema": "http://json-schema.org/schema#",
                "name": "Lab",
                "type": "object",
                "definitions": {
                        "entry": {
                                "lab_item": {"type": "string"},
                                "lab_value": {"type": "string"},
                                "unit": {"type": "string"},
                                "date": {"type": "string"},
                                "required": [
                                        "lab_item",
                                        "lab_value",
                                        "unit",
                                        "date"
                                ]
                        },
                        "patient_id": {"type": "string"}
                },
                "properties": {}
        }
        jsonschema.validate(lis_struct, schema)
        
        time_re = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}")

        for x in lis_struct.keys():
                if not args.compat and time_re.match(x) == None:
                        raise Exception("Top level keys not ISO8601 formatted")
                if not isinstance(lis_struct[x], dict):
                        raise Exception("Level 1 values not dicts")

        ## Analysis section ##
        for time in sorted(lis_struct.keys()):
                # calls analyze() for each loaded lisanalyze module
                for f in [i for i in sys.modules.keys() if re.match('.*lisanalyze', str(i))]:
                        getattr(eval(f), 'analyze')(file_name, lis_struct, time, args)
        # Merge results; total_results now contains the results of every analyzed file
        j = []
        for f in [i for i in sys.modules.keys() if re.match('.*lisanalyze', str(i))]:
                j.append(getattr(eval(f), 'get_results')())
        total_results = merge(*j)

for file_name in total_results.keys():
        outfile = open(os.path.join(os.path.normpath(args.dir), file_name) + args.suffix, mode='w')

        # Add file_name and analysis_time params before we print
        total_results[file_name]["file_name"] = file_name
        total_results[file_name]["analysis_time"] = datetime.datetime.now().isoformat()
        
        print(json.dumps(total_results[file_name]))
        print(json.dumps(total_results[file_name]), file=outfile)
        outfile.close()

        if args.human_readable and not args.quiet and not eventstr:
                print("All is well for data file {}!".format(file_name))
