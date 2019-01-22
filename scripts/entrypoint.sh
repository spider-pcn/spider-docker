#!/bin/bash

# set up default environ
export TOPO_FILE=${TOPO_FILE-/root/topology/default_topo.json}  # default topo file
export PAYMENT_SIZE=${PAYMENT_SIZE-100}                         # default payment size
export SPIDER_LOG_FIREBASE=${SPIDER_LOG_FIREBASE-1}             # enable firebase log by default
export SPIDER_QUEUE=${SPIDER_QUEUE-0}                           # disable queue by default
export EXP_TIME=${EXP_TIME-120}                                 # default duration is 120s
export SPIDER_LP_ROUTING=${SPIDER_LP_ROUTING-0}									# disable LP routing by default

mkdir -p /root/log
/root/scripts/runexp.sh &> /root/log/main.log &
bash
