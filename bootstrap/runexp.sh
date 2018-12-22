#!/bin/bash
function waitportopen()
{
	while ! nc -z localhost $1; do
		sleep 0.2
	done
}

function etcdget()
{
	local dt=''
	until dt=`etcdctl get $1 2> /dev/null`
	do
		sleep 0.2
	done
	echo $dt
}

function killandassert()
{
	kill $1
	while kill -0 $1; do
		sleep 0.2
	done
}

function monitorpendingchannels()
{
	local has_pending=''
	while true
	do
		if has_pending=`etcdctl get /cluster/haspendingchan` ; then
			if [ "$has_pending" == "init" ] ; then
				# still init
				sleep 4.5
			elif [ "$has_pending" == "yes" ] ; then
				# has pending channels
				btcctl --simnet --rpcuser=btcd --rpcpass=btcd generate 6
				sleep 4.5
			fi
		else
			sleep 4.5
		fi
	done
}

function killintime()
{
	sleep $2
	kill $1
}

echo "Generating config files for btcd, etcd and lnd"
# create config files
python3 bootstrap.py

echo "Starting btcd, etcd and lnd"
# start btcd, lnd, and etcd
btcd &> /dev/null &
btcd_pid=$!
lnd --noseedbackup --debughtlc &> /dev/null &
etcd --config-file ~/.etcd/etcd.conf &> /dev/null &

# wait for etcd to start
waitportopen 2379 &> /dev/null
echo "Etcd started"

# wait for btcd to start
waitportopen 18556 &> /dev/null
echo "Btcd started"

# wait for lnd to start
waitportopen 10009 &> /dev/null
echo "Lnd started"

# store ip in etcd
echo "Publishing node name and ip address"
etcdctl set "/nodeinfo/$NODENAME/ip" "$NODEIP" &> /dev/null
etcdctl set /cluster/haspendingchan init &> /dev/null

# create btc wallet and store address in etcd
echo "Creating btc wallet"
btc_addr=`lncli -n simnet newaddress np2wkh | jq -r '.address'`
etcdctl set "/nodeinfo/$NODENAME/btcaddr" $btc_addr &> /dev/null

# if we are the mining node, mine coins for each node
miner_node=`cat default_topo.json | jq -r '.miner'`
if [ "$NODENAME" == "$miner_node" ]
then
	for node in `cat default_topo.json | jq -r '.nodes | .[] | .name'`; do
		# wait for the node to publish its btc address
		node_btcaddr=`etcdget /nodeinfo/$node/btcaddr`

		# kill current btcd instance and wait for it to exit
		echo "Restarting btcd to mine for node $node"
		killandassert $btcd_pid &> /dev/null

		# start btcd and set mining addr
		btcd --miningaddr=$node_btcaddr &> /dev/null &
		btcd_pid=$!

		# wait for btcd to restart
		waitportopen 18556 &> /dev/null
		echo "Btcd restarted for $node"

		# mine blocks
		btcctl --simnet --rpcuser=btcd --rpcpass=btcd generate 400 &> /dev/null
		echo "Mined coins for $node"
	done
fi

# store public key in etcd
echo "Publishing lnd pubkey"
pubkey=`lncli -n simnet getinfo | jq -r '.identity_pubkey'`
etcdctl set "/nodeinfo/$NODENAME/pubkey" "$pubkey" &> /dev/null

# establish channel with peers
for chan in `cat default_topo.json | jq -c '.lnd_channels | .[]'`; do
	src=`echo $chan | jq -r '.src'`
	dst=`echo $chan | jq -r '.dst'`
    cap=`echo $chan | jq -r '.capacity'`
	if [ "$NODENAME" == "$src" ]
	then
		echo "Establishing P2P connection to $dst"
		# establish p2p connection
		peer_pubkey=`etcdget /nodeinfo/$dst/pubkey`
		peer_ip=`etcdget /nodeinfo/$dst/ip`
		lncli -n simnet connect $peer_pubkey@$peer_ip:9735 &> /dev/null

		# establish channel
		# we need to retry until succeed because btcd might by syncing
		echo "Creating channel to $dst"
		funding_output=''
        funding_amt=`expr $cap + $cap + 9050`
		until funding_output=`lncli -n simnet openchannel --node_key=$peer_pubkey --local_amt=$funding_amt --push_amt=$cap 2> /dev/null`
		do
			sleep 0.5
		done

		# publish on etcd
		echo "Publishing the new channel"
		funding_txid=`echo $funding_output | jq -r '.funding_txid'`
		etcdctl set "/channels/$src/$dst" "$funding_txid" &> /dev/null
	fi
done

# miner node should mine blocks after all channels has been established
if [ "$NODENAME" == "$miner_node" ]
then
	echo "Starting miner process"
	monitorpendingchannels &> /dev/null &
fi

# monitor how many pending channels are there
echo "Waiting for all channels to get acknowledged"
while true
do
	pending_chans=`lncli -n simnet pendingchannels | jq '.pending_open_channels | length'`
	echo "Pending channels: $pending_chans"
	if (( $pending_chans == 0 )) ; then
		break
	fi
	# if there are still channels pending, tell the miner
	# this info will live for 5 sec. The miner checks this key
	# every (<5) sec, so it will always be seen by the miner
	etcdctl set --ttl=5 /cluster/haspendingchan yes &> /dev/null
	sleep 5
done

# wait for itself to receive all channels
echo "Waiting to see all channels"
num_channels=`cat default_topo.json | jq '.lnd_channels | length'`
until [ `lncli -n simnet getnetworkinfo | jq '.num_channels'` == "$num_channels" ]
do
	sleep 1
done
etcdctl set "/nodeinfo/$NODENAME/seenallchans" "yes" &> /dev/null

# wait for all nodes to receive all channels
echo "Waiting for all nodes to see all channels"
for node in `cat default_topo.json | jq -r '.nodes | .[] | .name'`; do
	echo "Waiting for node $node"
	etcdget /nodeinfo/$node/seenallchans &> /dev/null
done

echo "Running experiments"
./run &
mainpid=$!

sleep 60
kill $mainpid

# enter interactive bash
bash getresults.sh
bash
