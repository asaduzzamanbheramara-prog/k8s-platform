#!/bin/bash

set -e

git checkout main
git pull origin main
git push gitlab main
