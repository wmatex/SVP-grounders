#!/bin/bash

#PBS -N DP-Grounders
#PBS -l select=1:ncpus=4:mem=128gb:scratch_local=20gb
#PBS -l walltime=10:00:00
#PBS -j oe
#PBS -m e

START=$(date +%s)

function sync_result() {
    cp experiments/grid-search/results.db $DATADIR/$GRID_DATA
}

trap "sync_result && clean_scratch" TERM EXIT

DATADIR="/storage/praha1/home/wmatex/SVP-grounders"
GRID_DATA="Datasets/experiments/grid-search"

# Prepare project
cp -a $DATADIR $SCRATCHDIR

# Switch to the scratch dir
cd $SCRATCHDIR/SVP-grounders/Datasets

module add python36-modules-gcc

END=$(date +%s)
SECONDS=$((36000 - ($END - $START)))

echo "Syncing took $SECONDS s"
# Compute
./grid_search.py -p 4 -t $SECONDS

# Sync computed results
sync_result || export CLEAN_SCRATCH=false
