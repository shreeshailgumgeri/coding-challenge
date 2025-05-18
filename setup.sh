#!/bin/bash

# set the debug level to your desired level
export DEBUG_LEVEL=DEBUG

mkdir -p ./audios
mkdir -p ./output

sudo apt-get update && sudo apt-get install -y ffmpeg

python -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt 