#!/usr/bin/env bash

# get VMs Nodes 
IFS=',' read -ra HOSTS <<< "$AZ_BATCH_HOST_LIST"
nodes=${#HOSTS[@]}
# print configuration
echo num nodes: $nodes
echo "hosts: ${HOSTS[@]}"
echo "print end configuration"

# create hostfile

touch hostfile

>| hostfile

for node in "${HOSTS[@]}"

do

    echo $node slots=1 max-slots=1 >> hostfile

done
echo "start mpi job"

mpirun --allow-run-as-root --mca btl_tcp_if_exclude docker0 --hostfile hostfile  -np $nodes  -npernode 1 python /parasail/deploytrainingdata.py

echo "end mpi job"
