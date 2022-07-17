#!/usr/bin/env bash

VENV=".venv"
PYTHON=${PYTHON:-python3}

if [ -d "$VENV" ]; then
    . "$VENV"/bin/activate
else
    virtualenv --system-site-packages -p $PYTHON "$VENV"
    . "$VENV"/bin/activate
    pip install gi-docgen -I
fi
