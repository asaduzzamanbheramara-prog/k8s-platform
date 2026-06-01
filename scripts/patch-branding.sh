#!/bin/bash

set -e

echo "Applying branding..."

BRANDING_SRC="/branding"
KPI_STATIC="/srv/src/kpi/static"

# Logos
cp $BRANDING_SRC/shopnoltdlogo.png $KPI_STATIC/
cp $BRANDING_SRC/favicon.png $KPI_STATIC/

# CSS/JS overrides
mkdir -p $KPI_STATIC/custom
cp $BRANDING_SRC/custom.css $KPI_STATIC/custom/
cp $BRANDING_SRC/custom.js $KPI_STATIC/custom/

echo "Branding applied"
