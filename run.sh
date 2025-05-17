#!/bin/bash

# this is the setup part, comment it out after the first execution
export DEBUG_LEVEL=WARNING 
set -ex

mkdir -p ./audios
mkdir -p ./output

python -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt 
# end of setup part

echo "Debug: Running stitch.py with message 'hello, Shreeshail'..."
python stitch.py -m "hello, Shreeshail" -a ./audios -o "./output/hello_shreeshail.mp3"