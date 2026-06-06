#!/bin/bash

set -e

REPO="$HOME/FreeDomain"

if [ ! -d "$REPO" ]; then
    git clone https://github.com/DigitalPlatDev/FreeDomain.git "$REPO"
else
    cd "$REPO"
    git pull
fi
