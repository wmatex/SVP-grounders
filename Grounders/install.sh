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

function build_swi_prolog() {
    BUILD_DIR="build"

    cd swi-prolog

    if [ ! -d $BUILD_DIR ]; then
        mkdir $BUILD_DIR
    fi

    ./prepare --yes
    ./build.templ --prefix=$(realpath $BUILD_DIR)
}

function build_dlv() {
    BUILD_DIR="dlv"

    # Just download it
    if [ ! -d $BUILD_DIR ]; then
        mkdir $BUILD_DIR
    fi

    cd $BUILD_DIR
    wget http://www.dlvsystem.com/files/dlv.x86-64-linux-elf-static.bin -O dlv
    chmod +x dlv
}

if [ "$1" = "--all" ]; then
    build_clingo
    build_swi_prolog
    build_dlv
elif [ "$1" = "--clingo" ]; then
    build_clingo
elif [ "$1" = "--swi-prolog" ]; then
    build_swi_prolog
elif [ "$1" = "--dlv" ]; then
    build_dlv
else
    print_help
    exit 1
fi
