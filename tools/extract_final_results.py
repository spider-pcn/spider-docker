import pandas as pd
import glob as glob
import argparse
import os
import pdb
from collections import defaultdict
import re

SUMMARY_FILE_SUFFIX = "/spider0e/main.log"
LATENCY_FILE_SUFFIX = "/spider{docker_name}/exp.log"

def read_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument("-data_dir", type=str, required=False,
            default="/Users/pari/spider-logs", help="")
    parser.add_argument("-exp_name", type=str, required=False,
            default="./woot", help="")
    parser.add_argument("-exp_regex_match", type=str, required=False,
            default="circ0", help="")

    return parser.parse_args()

def calculate_total(summary_file):
    final_total = 0.00
    final_succ = 0.00
    with open(summary_file, "r") as f:
        lines = f.read().split("\n")
        for line in lines:
            if "->" in line:
                tot_line = line[line.find("Total="):]
                total = int(tot_line[tot_line.find("=")+1:tot_line.find(",")])
                succ_line = line[line.find("Success="):]
                succ = int(succ_line[succ_line.find("=")+1:succ_line.find(",")])
                # print(total, succ, succ / total)
                final_total += total
                final_succ += succ
    if final_total == 0:
        return None
    return final_succ / final_total

args = read_flags()
# Scheme,Credit,SuccRatio,SuccRatioMin,SuccRatioMax
data = defaultdict(list)

for i, dir_name in enumerate(glob.glob(args.data_dir + "/*")):
    if not ("lnd" in dir_name or "dctcp" in dir_name):
        continue
    if "lnd" in dir_name:
        scheme = "lnd"
    elif "dctcp" in dir_name:
        scheme = "dctcp"
    # find out credit, and circulation num
    circ_start = dir_name.find("circ")
    circ = dir_name[circ_start+4:circ_start+5]

    # credit
    demand_start_str = dir_name[dir_name.find("demand"):]
    credit = re.findall(r'\d+', demand_start_str)[1]

    summary_file = dir_name + SUMMARY_FILE_SUFFIX
    check_file = dir_name + "/spider0e/exp.log"
    if not os.path.exists(check_file):
        print("skipping ", check_file)
        continue

    succ_frac = calculate_total(summary_file)
    if succ_frac is None:
        print("bad exp: ", summary_file)
        continue

    data["Scheme"].append(scheme)
    data["SuccRatio"].append(succ_frac)
    data["Credit"].append(credit)
    data["Circulation"].append(circ)

df = pd.DataFrame(data)
# Scheme,Credit,SuccRatio,SuccRatioMin,SuccRatioMax
schemes = set(df["Scheme"])
credits = set(df["Credit"])
# circs = set(df["Circulation"])

data = defaultdict(list)
for scheme in schemes:
    for credit in credits:
        print(scheme, credit)
        df2 = df[(df["Scheme"] == scheme) & (df["Credit"] == credit)]
        print(df2)
        pdb.set_trace()
