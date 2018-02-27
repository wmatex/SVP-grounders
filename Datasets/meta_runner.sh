#!/bin/bash

#PBS -N DP-Grounders
#PBS -l select=1:ncpus=5:mem=256gb:scratch_local=20gb
#PBS -l walltime=10:00:00
#PBS -j oe
#PBS -m e

trap "clean_scratch" TERM EXIT

DATADIR="/storage/praha1/home/wmatex/SVP-grounders"

# Switch to the scratch dir
cd $DATADIR/Datasets

module add python36-modules-gcc

# Compute
./grid_search.py -p 4 -d $SCRATCHDIR -t 36000
