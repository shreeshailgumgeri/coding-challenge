#!/bin/bash

# set the debug level to your desired level
export DEBUG_LEVEL=DEBUG

mkdir -p ./audios
mkdir -p ./output

python -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt 