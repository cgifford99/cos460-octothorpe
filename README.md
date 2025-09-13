# Octothorpe Console Game

## Background

Author: Christopher Gifford

Platform: Python 3.13 on Windows or Unix.

This program was written for COS 460/540: "Computer Networks" in Fall 2021. Octothorpe is a multiplayer console-based game that involves collecting treasures (denoted with the `#` character, AKA an octothorpe) in an ASCII-based map to achieve the highest score. The program supports as many clients as the server machine can handle and uses JSON to store user data. It uses low-level networking objects (Python sockets) to communicate between the server and clients.

The protocol used to send different types of messages and data is a custom protocol designed by our class and our professor in COS 460.

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

Once the server and at least one client is running, within the client's terminal, type `login [username]` to create a new user and initialize your player into the game. A map should appear with the first letter of your username on the map's spawnpoint (denoted 'S'). Use the arrow keys on your keyboard to move your player.\

The messages section of the terminal will give you any necessary information regarding your connection to the server, other player's movements and actions and the status of your player.

As you approach any treasure, you will receive a `102` message with the `(x, y)` coordinates and the value of the treasure. You should also see a `#` character appear on the map. Move your player to overlap this `#` character and you will collect the treasure. The value of the treasure is then added to your score and all other currently connected players will be notified of your score increase.

Collect as many treasures as you can find and get a highscore!
