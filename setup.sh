#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
ollama pull sam860/lfm2.5:1.2b