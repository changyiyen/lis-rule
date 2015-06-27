#!/usr/bin/python3
#-*- coding: utf-8 -*-
import argparse
import io
import json
import re
import sys

# Build argument parser
parser = argparse.ArgumentParser(
        description='Simple analyzer for LIS data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--compat', action='store_true', help='disables ISO8601 time format check')
parser.add_argument('-f', '--file', type=str, nargs = '*', default=["data.txt"], help='set path of JSON-formatted LIS data file to read')
parser.add_argument('-o', '--output', type=str, help='set path of output file')
parser.add_argument('-q', '--quiet', action='store_true', help='suppresses verbose messages')
parser.add_argument('-w', '--warn', action='store_true', help='enable extra warnings')
#parser.add_argument('--convert', action='store_true', help='enable unit conversion')
parser.add_argument('--version', action='version', version='%(prog)s 0.1 "Blizzard"')
args = parser.parse_args()

# Load data files from list
for filename in args.file:
        lis_file = io.open(filename)
        try:
                lis_struct = json.load(lis_file)
        except ValueError:
                raise Exception("Invalid JSON file")

        # Basic checks:
        # 1. Time format should be ISO8061 unless overridden by '--compat'
        # 2. Level 1 values should be dicts
        # comment: this section may be augmented with jsonschema
        time_re = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}")

        for x in lis_struct.keys():
                if not args.compat and time_re.match(x) == None:
                        raise Exception("Top level keys not ISO8601 formatted")
                if not isinstance(lis_struct[x], dict):
                        raise Exception("Level 1 values not dicts")

        ## Analysis section ##

        # global variables #
        units = {
                "PSA": "ng/dl"
                }
        psa_current_nadir = float('infinity')

        # logic #
        for time in sorted(lis_struct.keys()):
                # == PSA == #
                if "PSA" in lis_struct[time]:
                        if args.warn and lis_struct[time]["PSA"]["units"] != units["PSA"]:
                                print("WARNING: unit mismatch in entry for {}".format(time), file=sys.stderr)
                        if re.match(">", lis_struct[time]["PSA"]):
                                psa_current_nadir = float('infinity')
                        if re.match("<", lis_struct[time]["PSA"]):
                                psa_current_nadir = 0
                        PSA_val = float(lis_struct[time]["PSA"])
                else:
                        continue
                if PSA_val < psa_current_nadir:
                        psa_current_nadir = PSA_val
                if PSA_val - psa_current_nadir > 2:
                        warnflag = True
                        failstr = "{}: PSA failure at {} ".format(filename, time)
                        if not args.quiet:
                                failstr += "(nadir = {}, value = {} ({}))".format(psa_current_nadir, PSA_val, units["PSA"])
                        if args.output:
                                outfile = open(args.output, mode='w')
                                print(failstr, file=outfile)
                        print(failstr)
                # == End PSA == #
        ## End analysis section ##
        if not args.quiet and not failstr:
                print("All is well for data file {}!".format(filename))
