#!/usr/bin/python
import argparse
import logging
import os
import signal
import socket
import sys

from src.server.serverBase import OctothorpeServer

from constants import SERVER_NAME, DEFAULT_SERVER_PORT, DEFAULT_ROOT_PATH

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

        signal.signal(signal.SIGINT, octothorpe_server.sh_shutdown)
        signal.signal(signal.SIGTERM, octothorpe_server.sh_shutdown)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, octothorpe_server.sh_shutdown)

        s.listen(1)
        while True:
            conn, addr = s.accept()
            octothorpe_server.initialize_client(conn, addr)
