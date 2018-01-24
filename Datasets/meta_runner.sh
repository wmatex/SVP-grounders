#!/bin/bash
#PBS -N DP-Grounders
#PBS -l select=1:ncpus=4:mem=16gb:scratch_local=20gb
#PBS -l walltime=4:00:00
#PBS -j oe
#PBS -m e

function sync_result() {
    rsync -az experiments/grid-search/ $DATADIR/$GRID_DATA
}

trap "sync_result && clean_scratch" TERM EXIT

DATADIR="/storage/praha1/home/wmatex/SVP-grounders"
GRID_DATA="Datasets/experiments/grid-search"

# Prepare data
rsync -az $DATADIR/SVP-grounders/ $SCRATCHDIR/

# Switch to the scratch dir
cd $SCRATCHDIR/SVP-grounders/Datasets

module add python34-modules-intel

# Compute
./grid-search -t 4 >> experiments/grid-search/result.out

# Sync computed results
sync_result || export CLEAN_SCRATCH=false # copies result to your input data directory. The result will not be removed if the copying fails.
