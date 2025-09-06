import os
import sys

# server constants
DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 8001
DEFAULT_ROOT_PATH = os.path.split(os.path.abspath(sys.argv[0]))[0]
SERVER_NAME = 'cgif-octothorpe-gameserver'
USER_AUTOSAVE_INTERVAL = 60 # in seconds
POLLING_INTERVAL = 0.1 # in seconds

# client constants
CLIENT_NAME = 'cgif-octothorpe-gameclient'