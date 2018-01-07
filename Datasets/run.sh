#!/bin/bash

# Constants
EXPERIMENT_ROOT="experiments"
DATASET_GENERATOR="Syntetic/datasets.py"
RULES_GENERATOR="Syntetic/rules.py"
PROGRAM_NAME="$0"
GROUNDERS="../Grounders"

# Command line options
DATASET=""
RULES=""
GENERATE_OPTIONS=""
RULES_OPTIONS=""
GROUNDER=""
COMBINED=false


function print_help() {
    if [ -n "$1" ]; then
        echo "Error: $1"
    fi

    cat <<EOF
Usage: $PROGRAM_NAME [--generate "<dataset options>" --rules-gen "<rules options>" | 
                      --dataset <file> --rules <file> | --combined <combined>] 
                      --grounder <grounder>

Runs (and generates) given dataset with rules against given grounder.

OPTIONS:

 General options:

  --help                             Show this message

 Options for generators:

  --generate "<dataset options>"     Generates new syntetic dataset with given options
                                     and uses this dataset with the given grounder

  --rules-gen "<rules options>"      Generates new rules for the generated dataset
                                     with given options

 Options for existing datasets:

  --dataset <file>                   Use given dataset as source for the grounder
  
  --rules <file>                     Use given rules as source for the grounder
  
  --combined <file>                  Use given combined dataset file with rules as source for the grounder

EOF
}

if [[ $# -le 0 ]]; then
    print_help "No options given"
    exit 1
fi

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --generate)
            GENERATE_OPTIONS="$2"
            shift # past argument
            shift # past value
            ;;
        --rules-gen)
            RULES_OPTIONS="$2"
            shift # past argument
            shift # past value
            ;;
        --dataset)
            DATASET="$2"
            shift # past argument
            shift # past value
            ;;
        --rules)
            RULES="$2"
            shift
            shift # past argument
            ;;
        -g|-grounder)
            GROUNDER="$2"
            shift
            shift
            ;;
        --combined)
            COMBINED=true
            DATASET="$2"
            shift
            shift
            ;;
        --grounder)
            GROUNDER="$2"
            shift
            shift
            ;;
        -h|-help)
            print_help
            exit 0
            ;;
        *)  # unknown option
            print_help "Uknown option '$key'"
            exit 1
            break # past argument
            ;;
    esac
done

if [ -n "$GENERATE_OPTIONS" ] && [ -n "$DATASET" ]; then
    print_help "Cannot use both generated and existing datasets"
    exit 1
fi

if [ -n "$RULES_OPTIONS" ] && [ -n "$RULES" ]; then
    print_help "Cannot use both generated and existing rules"
    exit 1
fi

function setup_experiment() {
    dir=$EXPERIMENT_ROOT/$(create_name $GENERATE_OPTIONS $RULES_OPTIONS)

    if [ ! -d $dir ]; then
        mkdir -p $dir
    fi

    echo $dir
}

function create_name() {
    echo $@ | tr -d '\- '
}

function generate_dataset() {
    $DATASET_GENERATOR $GENERATE_OPTIONS > $1/dataset.txt

    echo $1/dataset.txt
}

function generate_rules() {
    format=$(grounder_to_format $GROUNDER)
    $RULES_GENERATOR $RULES_OPTIONS --type $format $2 > $1/rules-$format.txt

    echo $1/rules-$format.txt
}

function grounder_to_format() {
    case $1 in
        gringo|dlv)
            echo "datalog"
            ;;

        swi-prolog)
            echo "prolog"
            ;;

        *)
            echo $1
            ;;
    esac
}

function run_gringo() {
    RUNS="$1/runs-gringo.txt"

    $GROUNDERS/clingo/build/bin/clingo --text $2 > $RUNS
    cat $RUNS
}

function run_swi_prolog() {
    RUNS="$1/runs-swi-prolog.txt"

    $GROUNDERS/swi-prolog/build/bin/swipl -s $2 > $RUNS
    cat $RUNS
}

function run_dlv() {
    RUNS="$1/runs-dlv.txt"

    $GROUNDERS/dlv/dlv -silent -nofacts -instantiate $2 > $RUNS
    cat $RUNS
}

experiment_dir=$(setup_experiment)
dataset=""
if [ -n "$GENERATE_OPTIONS" ]; then
    dataset=$(generate_dataset $experiment_dir)
fi

if [ -n "$RULES_OPTIONS" ]; then
    rules=$(generate_rules $experiment_dir $dataset)
fi

dataset_rules=$(mktemp)
cat $dataset $rules > $dataset_rules

case $GROUNDER in
    gringo)
        run_gringo $experiment_dir $dataset_rules
        ;;

    swi-prolog)
        run_swi_prolog $experiment_dir $dataset_rules
        ;;

    dlv)
        run_dlv $experiment_dir $dataset_rules
        ;;
esac
