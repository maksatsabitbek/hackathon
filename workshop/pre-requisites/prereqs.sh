#!/bin/bash

cd /project
# install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
# create a python virtual environment. use python3.10 or above only
uv venv myvenv --python 3.12
# activate the virtual environment
source myvenv/bin/activate
# install pre-requisite packages
uv pip install -r setup/requirements.txt