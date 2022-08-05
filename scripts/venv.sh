#!/usr/bin/env bash

VENV=".venv"
PYTHON=${PYTHON:-python3}

if [ -d "$VENV" ]; then
    . "$VENV"/bin/activate
else
    virtualenv --system-site-packages -p $PYTHON "$VENV"
    . "$VENV"/bin/activate
    python3 -m pip install git+https://github.com/fcole90/gi-docgen.git -I
fi
