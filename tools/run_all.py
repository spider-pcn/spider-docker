import argparse
import subprocess as sp
import time
import glob
import os

CMD_TEMPLATE = "./run.sh start-exp {topo_file} {exp_name} {exp_time}"
# TOPO_NAMES = [""]
TOPO_NAMES = ["three", "five"]
# FILE = "sf_20_routers_circ0_demand10"
TOPO_DIR = "../topology/"

'''
sequence of commands:
    - start instances N
    - init docker
    - init image
    - sync
    - rebuild
    - repackage
'''

def read_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument("-exp_time", type=int, required=False,
            default=60, help="")
    parser.add_argument("-num_instances", type=int, required=False,
            default=3, help="")
    parser.add_argument("-exp_regex_match", type=str, required=False,
            default="circ0", help="")

    parser.add_argument("-exp_prefix", type=str, required=False,
            default="test", help="")
    parser.add_argument("-stop_instances", action='store_true',
                                help="")
    # parser.add_argument("-restart_instances", action='store_true',
                                # help="")
    parser.add_argument("-start_instances", type=int, required=False,
                        default=0, help="")
    return parser.parse_args()

def run_exp(exp_num, topo_name, scheme):
    # going to set the appropriate entrypoint file, and repackage
    cp_cmd = "cp ../scripts/entrypoint-{}.sh ../scripts/entrypoint.sh".\
            format(scheme)
    p = sp.Popen(cp_cmd, shell=True)
    p.wait()

    p = sp.Popen("./run.sh sync-testbed", shell=True)
    p.wait()
    print("syncing testbed done")

    p = sp.Popen("./run.sh repackage-image", shell=True)
    p.wait()
    print("repackage-image done")

    print("going to run exp: ", topo_name)
    exp_name = args.exp_prefix + os.path.basename(topo_name)
    exp_name = exp_name.replace(".json", "")
    print("exp name is: ", exp_name)

    cmd = CMD_TEMPLATE.format(topo_file =topo_name,
                              exp_name = exp_name,
			      exp_time = args.exp_time)
    print("cmd: ", cmd)
    sp.Popen(cmd, shell=True)
    # sleep a bit extra, because why not
    if args.exp_time <= 150:
        time.sleep(args.exp_time*2)
    else:
        time.sleep(args.exp_time + 50)

    log_dir = exp_name + scheme
    print(log_dir)
    p = sp.Popen("./run.sh copy-logs {}".format(log_dir), shell=True)
    p.wait()
    time.sleep(5)
    p = sp.Popen("./run.sh stop-exp", shell=True)
    p.wait()
    time.sleep(5)
    p = sp.Popen("mv {} ~/spider-logs/".format(log_dir), shell=True)
    p.wait()
    # plot latency
    # try:
        # latency_fn = "~/spider-logs/" + log_dir + "/spider0e/exp.log"
        # print(latency_fn)
        # p = sp.Popen("python plot_latency.py {}".format(latency_fn))
        # p.wait()
    # except:
        # pass

args = read_flags()

if args.start_instances:
    p = sp.Popen("./run.sh stop-instances", shell=True)
    p.wait()
    p = sp.Popen("./run.sh start-instances " + str(args.num_instances),
            shell=True)
    p.wait()
    # sleep extra for instances to start
    time.sleep(180)
    p = sp.Popen("./run.sh mount-nvme", shell=True)
    print("mount nvme done!")
    p.wait()
    p = sp.Popen("./run.sh init-docker", shell=True)
    p.wait()
    time.sleep(2)
    p = sp.Popen("./run.sh init-image", shell=True)
    p.wait()
    print("init image done!")
    p = sp.Popen("./run.sh sync-testbed", shell=True)
    p.wait()
    p = sp.Popen("./run.sh rebuild-binary lnd expctrl", shell=True)
    p.wait()
    print("sync-testbed done")
    p = sp.Popen("./run.sh repackage-image", shell=True)
    p.wait()
    print("repackage-image done")

# list all the files we want to run it on
fns = glob.glob(TOPO_DIR + "*")
for i, fn in enumerate(fns):
    if args.exp_regex_match in fn:
        # run lnd, and then run dctcp
        run_exp(i, fn, scheme="dctcp")
        print("executed dctcp on ", fn)
        time.sleep(1)
        run_exp(i, fn, scheme="lnd")
        print("executed lnd on ", fn)

# shut down it all
if args.stop_instances:
    sp.Popen("./run.sh stop-instances", shell=True)
    time.sleep(5)
