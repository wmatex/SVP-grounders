#!/bin/bash

#PBS -N DP-Grounders
#PBS -l select=1:ncpus=4:mem=128gb:scratch_local=20gb
#PBS -l walltime=10:00:00
#PBS -j oe
#PBS -m e

function sync_result() {
    rsync -az --exclude='*.gz' experiments/grid-search/ $DATADIR/$GRID_DATA
}

trap "sync_result && clean_scratch" TERM EXIT

DATADIR="/storage/praha1/home/wmatex/SVP-grounders"
GRID_DATA="Datasets/experiments/grid-search"

# Prepare data
rsync -az --exclude='*.gz' $DATADIR/ $SCRATCHDIR/

# Switch to the scratch dir
cd $SCRATCHDIR/Datasets

module add python36-modules-gcc

# Compute
./grid_search.py -p 4 -t 36000 >> experiments/grid-search/result.out

# Sync computed results
sync_result || export CLEAN_SCRATCH=false
