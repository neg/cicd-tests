#!/bin/bash

run() {
    local name=$1
    shift
    local targets=$1
    shift
    local isbaseline=$1
    shift

    local ninjaopt=""
    if [[ "$isbaseline" == "yes" ]]; then
        ninjaopt="--quiet"
        rm -fr build/$name
    fi

    if [ ! -d build/$name ]; then
        if ! meson setup -Denable_kmods=false $* build/$name; then
            echo "Meason setup failed for $name" >&2
            exit 1
        fi
    fi

    ninja $ninjaopt -C build/$name $targets
}

set -euo pipefail

readonly repo=$1
readonly commit=$2
readonly baseline=$3

cd $repo

# Checkout corrrect commit
git checkout --quiet $commit

# Build using default compiler
run normal all $baseline
