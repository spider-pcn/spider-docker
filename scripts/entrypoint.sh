#!/bin/bash

# set up default environ
export TOPO_FILE=${TOPO_FILE-/root/topology/default_topo.json}  # default topo file
export PAYMENT_SIZE=${PAYMENT_SIZE-400}                         # default payment size
export SPIDER_LOG_FIREBASE=${SPIDER_LOG_FIREBASE-0}             # enable firebase log by default
export SPIDER_QUEUE=${SPIDER_QUEUE-1}                           # enable queue by default
export EXP_TIME=${EXP_TIME-120}                                 # default duration is 120s
export STATS_INTERVAL=${STATS_INTERVAL-1000}                    # default duration is 1000ms
export SPIDER_DCTCP_ROUTING=${SPIDER_DCTCP_ROUTING-1}									# disable LP routing by default
export SPIDER_USE_WINDOWS=${SPIDER_USE_WINDOWS-1}	
export SPIDER_TIMEOUT=${SPIDER_TIMEOUT-1}	
export ROUTINGALGO=${ROUTINGALGO-dctcp}

export ALPHA=${ALPHA-10}
export BETA=${BETA-0.1}
export QUEUE_THRESHOLD=${QUEUE_THRESHOLD-300}
export SPIDER_QUEUE_UPDATE_TIME=${SPIDER_QUEUE_UPDATE_TIME-10}	# default queue busy waiting time
export SPIDER_START_TIME=${SPIDER_START_TIME-50}
export SPIDER_END_TIME=${SPIDER_END_TIME-150}

mkdir -p /root/log
/root/scripts/runexp.sh &> /root/log/main.log &
bash
