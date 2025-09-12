import argparse
import logging
import signal
import socket
import sys

from client.clientBase import OctothorpeClient
from client.services.clientCoreService import ClientCoreService
from client.services.clientMapService import ClientMapService
from client.services.clientServerWriterService import ClientServerWriterService
from client.services.clientWriterService import ClientWriterService
from common.services.serviceManager import ServiceManager
from constants import (CLIENT_NAME, DEFAULT_ROOT_PATH, DEFAULT_SERVER_HOST,
                       DEFAULT_SERVER_PORT)

logging.basicConfig()

if __name__ == '__main__':
    logger = logging.getLogger(CLIENT_NAME)
    logger.setLevel(logging.INFO)

    host = 'localhost'

    parser = argparse.ArgumentParser(
        description='A client implementation interfacing with the Octothorpe server')
    parser.add_argument('--port', metavar='p', type=int, help='server port',
                        choices=range(1024, 65535), default=DEFAULT_SERVER_PORT, required=False)
    parser.add_argument('--host', metavar='h', type=str,
                        help='server host', default=DEFAULT_SERVER_HOST, required=False)
    parser.add_argument('--root_path', metavar='r',
                        help='root directory to client resources', default=DEFAULT_ROOT_PATH, required=False)

    args = parser.parse_args()
    port = args.port
    host = args.host
    root_path = args.root_path

    service_manager = ServiceManager()
    service_manager.register(ClientCoreService)
    service_manager.register(ClientWriterService)
    service_manager.register(ClientMapService)
    service_manager.register(ClientServerWriterService)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
        except socket.error as msg:
            logger.error(
                f'Connect failed to server {host} on port {port}: ' + str(msg))
            sys.exit()

        logger.info(f'Successfully connected to server {host} on port {port}')

        octothorpe_client = OctothorpeClient(service_manager, s)

        signal.signal(signal.SIGINT, octothorpe_client.sh_shutdown)
        signal.signal(signal.SIGTERM, octothorpe_client.sh_shutdown)
        if sys.platform == 'win32' and hasattr(signal, 'SIGBREAK'):
            # SIGBREAK is only available in Windows environments
            signal.signal(signal.SIGBREAK, octothorpe_client.sh_shutdown)

        octothorpe_client.client_handler()
