#!/bin/bash

run() {
    local -r name=$1
    shift
    local -r targets=$1
    shift

    if [ ! -d build/$name ]; then
        if ! meson setup -Denable_kmods=false $* build/$name; then
            echo "Meason setup failed for $name" >&2
            exit 1
        fi
    fi

    ninja -C build/$name $targets
}

set -euo pipefail

readonly repo=$1
readonly commit=$2

cd $repo

# Checkout corrrect commit
git checkout --quiet $commit

# Build using default compiler
run normal all
