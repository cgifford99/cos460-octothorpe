from constants import SERVER_NAME

import logging
logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerClientInterface(object):
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.code_msgs = {101: 'PlayerUpdate', 102:'TreasureProximity', 103: 'TreasureUpdate', 104: 'Map', 200: 'Success', 400: 'UserError', 500: 'ServerError'}

    def send_msg(self, code, msg):
        msg_send_result = bool(self.conn.send(self.resp(code, msg)))
        if not msg_send_result and len(msg) > 0:
            raise ConnectionAbortedError('Received error sending message to client')
        else:
            return True

    def resp(self, code, msg=''):
        if not code or code not in self.code_msgs:
            logger.error('Invalid code given: ' +
                         code if code else 'None')
            code = 500

        code_msg = msg if msg else self.code_msgs.get(code, self.code_msgs.get(500))

        response = f'{code}:{code_msg}\r\n'
        return response.encode('utf-8')