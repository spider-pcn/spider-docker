# Spider Distributed Testbed

## Setting Up

1. Clone this repository to somewhere that you like
2. Add a line `Include config.d/spider` to the beginning of your `~/.ssh/config`
3. `mkdir -p ~/.ssh/config.d`. We will write EC2 instance info to `config.d/spider`
4. Install AWS CLI (use `brew install awscli` on MAC) 
5. Configure your root key / IAM key. This involves creating a `~/.aws` directory and creating a `~/.aws/config` with the right availability zone and a `~/.aws/credentials` file with the right credentials.
6. Install `jq`, a command line json parser
7. `cd` into `tools/`, and use `run.sh` to control the experiment

## `run.sh` Usage

```
Manage AWS EC2 Instances

    start-instances n
        Start n EC2 instances

    stop-instances
        Terminate EC2 instances

Setup Experiment Environment

    init-docker
        Initialize docker swarm

    uninit-docker
        Destroy docker swarm

Manage Experiment Files

    init-image
        Sync testbed, download binaries and package image

    sync-testbed
        Sync testbed directory to remotes

    repackage-image
        Repackage docker image

    rebuild-binary bin1 bin2 ...
        Recompile bin1, bin2, ... (lnd, expctrl, bitcoind, etcdjq)

    download-binary
        Download precompiled binaries

Control Experiment

    start-exp topofile expname exptime
        Start an experiment

    stop-exp
        Stop an experiment

Connect to Testbed

    run-all cmd
        Run command on all instances

    ssh i
        SSH to the i-th server (1-based index)

    attach node
        Attach to container node
        Always use ^-p ^-q and not exit to detach from the container

Parse Logs
	
		python3 parse_logs.py -data_dir LOG_DIR -exp_name EXP_NAME	
				LOG_DIR would be the directory supplied to the copy-logs command, with
				directories like spider0e etc. This will parse all the log files there
				and generate two plots:
					- EXP_NAME_per_channel_info.pdf
					- EXP_NAME_src_dest.pdf	
```

## Typical Experiment Flow

```bash
./run.sh start-instances 3
# wait for about two minutes for EC2 to start and auto-install docker, go, etc.
./run.sh init-docker
./run.sh init-image
./run.sh start-exp ../topology/some-topo-file.json experiment-name 120
# after the experiment have finished
./run.sh stop-exp
./run.sh stop-instances
```

# Notes
^-p ^-q: detach from the container

# Topology File

See some examples in `topology/`. Here are some pitfalls

- Channel capacity is defined as the "one way" capacity - that is, how much satoshi are there at each end when channel is first established.
- Due to lnd and bitcoin limitations, the smallest channel capacity is 10000.
- The most efficient way to connect bitcoind is connecting each node to the miner node, forming a star topology. However, note that bitcoind only supports 8 outgoing connections, so be sure to set the miner node as the `dst`.

# Bugs

Currently, all messages are exchanged in etcd, which ultimatally falls on to a single leader node. This may become a problem when we run a large topology, or send transactions at a high-speed. We need to use golang RPC to replace etcd in those situations to avoid centralization.

