import argparse
import subprocess as sp
import time

CMD_TEMPLATE = "./run.sh start-exp {topo_file} {exp_name} {time}"
TOPO_NAMES = ["two_node_circ", "three_node_circ", "four_node_circ",
        "five_node_circ"]

def read_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument("-topos", type=int, required=False,
            default=0, help="index of topo to run. -1 runs all.")
    parser.add_argument("-exp_time", type=int, required=False,
            default=60, help="")
    parser.add_argument("-reps", type=int, required=False,
            default=1, help="")
    parser.add_argument("-exp_prefix", type=str, required=True,
                                help="")
    parser.add_argument("-stop_instances", action='store_true',
                                help="")
    return parser.parse_args()

def run_exp(topo_name, exp_suffix):
    print("going to run exp: ", topo_name)
    cmd = CMD_TEMPLATE.format(topo_file = "../topology/" + topo_name + ".json",
                              exp_name = args.exp_prefix + "-" + topo_name + "-" + exp_suffix,
                              time = args.exp_time)
    print("cmd: ", cmd)

    sp.Popen(cmd, shell=True)
    # sleep a bit extra, because why not
    if args.exp_time <= 100:
        time.sleep(args.exp_time*2)
    else:
        time.sleep(args.exp_time + 600)
    sp.Popen("./run.sh stop-exp", shell=True)
    time.sleep(5)

args = read_flags()
for i in range(args.reps):
    if args.topos == -1:
        for topo_name in TOPO_NAMES:
            run_exp(topo_name, str(i))
    else:
        run_exp(TOPO_NAMES[args.topos], str(i))

# shut down it all
if args.stop_instances:
    sp.Popen("./run.sh stop-instances", shell=True)
    time.sleep(5)
