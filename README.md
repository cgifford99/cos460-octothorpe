# Octothorpe Console Game

## Background

Author: Christopher Gifford

Platform: Python 3.13 on Windows or Unix.

This program was written for COS 460/540: "Computer Networks" in Fall 2021. Octothorpe is a multiplayer console-based game that involves collecting treasures (denoted with the `#` character, AKA an octothorpe) in an ASCII-based map to achieve the highest score. The program supports as many clients as the server machine can handle and simply uses JSON to store user data.

## Usage

Usage of the provided client is optional, but recommended. To initialize the server and client, see their respective README documents.

In both cases, utilization of pyenv or a python virtual environment and the provided `requirements.txt` is recommended. To activate the virtual environment, in any bash console:

``` bash
# Create the environment
python -m venv .venv
# Activate the environment
source ./.venv/bin/activate
# Install all required packages
pip install -r requirements.txt
```

Or if using pyenv:

``` bash
# Install latest 3.13 python
pyenv install 3.13.7
# Create the virtual environment
pyenv virtualenv 3.13.7 octothorpe
# Create a symbolic link for easy access to the virtual environment and integration with VSCode
ln -s ~/.pyenv/versions/octothorpe ./.venv
```

## How to Play

TBD
