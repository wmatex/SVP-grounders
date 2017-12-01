#!/bin/bash

function build_clingo() {
    BUILD_DIR="build"

    cd clingo

    git submodule update --init --recursive

    if [ ! -d $BUILD_DIR ]; then
        mkdir $BUILD_DIR 
    fi

    cmake -H. -B$BUILD_DIR -DCMAKE_BUILD_TYPE=Release
    cmake --build $BUILD_DIR
}

if [ "$1" = "--all" ]; then
    build_clingo
elif [ "$1" = "--clingo" ]; then
    build_clingo
else
    print_help
    exit 1
fi
