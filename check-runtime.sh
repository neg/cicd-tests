#!/bin/bash

set -euo pipefail

readonly repo=$1

$repo/build/normal/code
