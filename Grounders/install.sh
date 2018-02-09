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

function build_lparse() {
    BUILD_DIR="build"

    cd lparse
    if [ ! -d $BUILD_DIR ]; then
        mkdir $BUILD_DIR
    fi

    wget http://www.tcs.hut.fi/Software/smodels/src/lparse-1.1.2.tar.gz
    tar xvf lparse-1.1.2.tar.gz
    ./patch.sh
    cd lparse-1.1.2
    ./configure --prefix=../build
    make
    make install
}

function build_postgresql() {
    BUILD_DIR="build"

    cd postgresql
    
    wget https://ftp.postgresql.org/pub/source/v10.1/postgresql-10.1.tar.bz2

}

if [ "$1" = "--all" ]; then
    build_clingo
    cd -
    build_swi_prolog
    cd -
    build_dlv
    cd -
    build_lparse
elif [ "$1" = "--clingo" ]; then
    build_clingo
elif [ "$1" = "--swi-prolog" ]; then
    build_swi_prolog
elif [ "$1" = "--dlv" ]; then
    build_dlv
elif [ "$1" = "--lparse" ]; then
    build_lparse
else
    print_help
    exit 1
fi
