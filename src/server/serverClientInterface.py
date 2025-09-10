import logging
from socket import socket

from constants import SERVER_NAME

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerClientInterface(object):
    '''The Server Client Interface class acts as a subclass/interface for all objects that require communication with the client. It includes core functionality and logic for crafting and sending responses to the client.
    '''
    def __init__(self, conn: socket, addr: str):
        self.conn: socket = conn
        self.addr: str = addr
        self.code_msgs: dict[int, str] = {101: 'PlayerUpdate', 102:'TreasureProximity', 103: 'TreasureUpdate', 104: 'Map', 200: 'Success', 400: 'UserError', 500: 'ServerError'}

    def send_msg(self, code: int, msg: str) -> bool:
        try:
            msg_send_result: bool = bool(self.conn.send(self.resp(code, msg)))
        except Exception as ex:
            logger.error(f'Received error sending message to client: {ex}')
            return False

        if not msg_send_result and len(msg) > 0:
            logger.error(f'Sending message to client failed, but no error message was found')
            return False
        else:
            return True

    def resp(self, code: int, msg: str = '') -> bytes:
        if not code or code not in self.code_msgs:
            logger.error('Invalid code given: ' + str(code) if code else 'None')
            code = 500

        code_msg: str = msg if msg else self.code_msgs.get(code, self.code_msgs.get(500, ''))

        response: str = f'{code}:{code_msg}\r\n'
        return response.encode('utf-8')