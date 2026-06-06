#!/bin/bash

set -e

NAME=$1
TEMPLATE=$2

if [ -z "$NAME" ] || [ -z "$TEMPLATE" ]; then
    echo "Usage:"
    echo "./create-app.sh APP TEMPLATE"
    exit 1
fi

cd ~/k8s-platform

python3 <<EOF
from platform_controller.domain_manager import create

create(
    "$NAME",
    "$TEMPLATE"
)
EOF
