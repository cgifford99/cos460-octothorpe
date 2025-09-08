import argparse
import logging
import signal
import socket
import sys

from constants import DEFAULT_ROOT_PATH, DEFAULT_SERVER_PORT, SERVER_NAME
from src.server.serverBase import OctothorpeServer

logging.basicConfig()

if __name__ == '__main__':
    logger = logging.getLogger(SERVER_NAME)
    logger.setLevel(logging.INFO)

    host = 'localhost'

    parser = argparse.ArgumentParser(
        description='An implementation of Octothorpe with sockets and a custom protocol')
    parser.add_argument('--port', metavar='p', type=int, help='port to bind server',
                        choices=range(1024, 65535), default=DEFAULT_SERVER_PORT, required=False)
    parser.add_argument('--root_path', metavar='r',
                        help='root directory to game resources', default=DEFAULT_ROOT_PATH, required=False)

    args = parser.parse_args()
    port = args.port
    root_path = args.root_path
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except socket.error as msg:
            logger.error(f'Bind failed on host {host} for port {port}')
            sys.exit()

        logger.info(f'Started {SERVER_NAME} on port {port}')

        octothorpe_server = OctothorpeServer(root_path)

        # configure shutdown procedures for each type of kill/termination signal
        signal.signal(signal.SIGINT, octothorpe_server.sh_shutdown)
        signal.signal(signal.SIGTERM, octothorpe_server.sh_shutdown)
        if sys.platform == 'win32' and hasattr(signal, 'SIGBREAK'):
            # SIGBREAK is only available in Windows environments
            signal.signal(signal.SIGBREAK, octothorpe_server.sh_shutdown)

        # begin listening for new client connections
        s.listen(1)
        while True:
            conn, addr = s.accept()
            octothorpe_server.initialize_client(conn, addr)
