import argparse
import subprocess as sp
import time

CMD_TEMPLATE = "./run.sh start-exp {topo_file} {exp_name} {time}"
TOPO_NAMES = ["two_node_circ", "three_node_circ", "four_node_circ",
        "five_node_circ"]
TOPO_NODES = [4, 4, 4, 5]

# TOPO_NAMES = ["three_node_circ", "four_node_circ",
        # "five_node_circ"]
# TOPO_NODES = [3, 4, 5]

FIREBASE_TEMPLATE = "python ~/lightning_routing/lnd-vis/main.py -exp_name {exp_name}"

'''
sequence of commands:
    - stop instances
    - start instances N
    - init docker
    - init image
    - sync 
    - rebuild 
    - repackage
'''

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
    parser.add_argument("-restart_instances", action='store_true',
                                help="")
    return parser.parse_args()

def run_exp(exp_num, exp_suffix):
    topo_name = TOPO_NAMES[exp_num]
    if args.restart_instances:
        p = sp.Popen("./run.sh stop-instances", shell=True)
        p.wait()
        p = sp.Popen("./run.sh start-instances " + str(TOPO_NODES[exp_num]),
                shell=True)
        p.wait()
        # sleep extra for instances to start
        time.sleep(180)
        p = sp.Popen("./run.sh init-docker", shell=True) 
        p.wait()
        time.sleep(2)
        p = sp.Popen("./run.sh init-image", shell=True) 
        p.wait()
        time.sleep(4)
        p = sp.Popen("./run.sh rebuild-binary lnd expctrl", shell=True)
        p.wait()
        print("rebuilt binaries")
        time.sleep(5)
        p = sp.Popen("./run.sh repackage-image", shell=True)
        p.wait()
        time.sleep(5)

    print("going to run exp: ", topo_name)
    exp_name = args.exp_prefix + "-" + topo_name + "-" + exp_suffix
    cmd = CMD_TEMPLATE.format(topo_file = "../topology/" + topo_name + ".json",
                              exp_name = exp_name,
                              time = args.exp_time)
    print("cmd: ", cmd)

    sp.Popen(cmd, shell=True)
    # sleep a bit extra, because why not
    if args.exp_time <= 100:
        time.sleep(args.exp_time*2)
    else:
        time.sleep(args.exp_time + 600)
    p = sp.Popen("./run.sh stop-exp", shell=True)
    p.wait()
    time.sleep(5)
    # test it.
    cmd = FIREBASE_TEMPLATE.format(exp_name = exp_name)
    try:
        p = sp.Popen(cmd, shell=True)
        p.wait()
    except:
        pass
        # nothing
    # time.sleep(10)

args = read_flags()
for i in range(args.reps):
    if args.topos == -1:
        for j, _ in enumerate(TOPO_NAMES):
            run_exp(j, str(i))
    else:
        run_exp(args.topos, str(i))

# shut down it all
if args.stop_instances:
    sp.Popen("./run.sh stop-instances", shell=True)
    time.sleep(5)
