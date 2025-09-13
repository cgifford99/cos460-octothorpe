import logging
import math
import time

import client.models.clientWriterEvent as cwe
from client.services.clientCoreService import ClientCoreService
from client.services.clientMapService import ClientMapService
from client.services.clientWriterService import ClientWriterService
from common.services.serviceManager import ServiceManager
from constants import CLIENT_NAME, POLLING_INTERVAL

logger = logging.getLogger(CLIENT_NAME)
logger.setLevel(logging.INFO)


class ClientWriter(object):
    def __init__(self, service_manager: ServiceManager) -> None:
        self.service_manager: ServiceManager = service_manager
        self.client_map_service: ClientMapService = self.service_manager.get_service(ClientMapService)
        self.client_core_service: ClientCoreService = self.service_manager.get_service(ClientCoreService)
        self.client_writer_service = self.service_manager.get_service(ClientWriterService)

        self.input_pos: int = math.floor(self.client_core_service.term.height * 0.6)
        self.scroll_lines: list[str] = []

    def client_writer_handler(self) -> None:
        while True:
            if self.client_writer_service.queue.qsize() != 0:
                event = self.client_writer_service.queue.get()
                self.execute_cmd(event)
            else:
                # this allows the client to poll for incoming requests only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)

    def execute_cmd(self, event: cwe.ClientWriterEventBase) -> bool:
        if isinstance(event, cwe.ClientWriterEventPrintInputLine):
            self.print_to_input_line(event.line)
        elif isinstance(event, cwe.ClientWriterEventPrintScrolling):
            self.print_to_scrolling(event.line)
        elif isinstance(event, cwe.ClientWriterEventUpdateScreen):
            self.update_screen()

        return True

    def update_screen(self) -> None:
        self.input_pos = math.floor(self.client_core_service.term.height * 0.6)
        username = self.client_core_service.user_info.username or 'N/A'
        position = self.client_core_service.user_info.position or 'N/A'
        score = self.client_core_service.user_info.score or 'N/A'
        with self.client_core_service.term.hidden_cursor():
            print(self.client_core_service.term.home + self.client_core_service.term.clear_eol +
                  f'Username:{username}, Position:{position}, Score:{score}\n')
            if self.client_map_service.has_valid_map():
                temp_map: list[str] = self.client_map_service.build_map()
                num_map_lines: int = self.input_pos - 1
                upper_map: int = 0
                lower_map: int = num_map_lines
                if self.client_core_service.user_info.username:
                    zone: int = (self.client_core_service.user_info.position[1] if self.client_core_service.user_info.position else 0) // num_map_lines
                    upper_map = zone * num_map_lines
                    lower_map = num_map_lines + upper_map
                    if lower_map > len(temp_map):
                        lower_map = len(temp_map)
                        upper_map = lower_map - num_map_lines

                scr_line_idx: int = 0
                for map_line_idx in range(upper_map, lower_map):
                    line: str = temp_map[map_line_idx]
                    print(self.client_core_service.term.move_xy(0, scr_line_idx + 1) +
                          self.client_core_service.term.clear_eol + line)
                    scr_line_idx += 1

            for line_idx in range(len(self.scroll_lines)):
                line: str = self.scroll_lines[line_idx]
                print(self.client_core_service.term.move_xy(0, self.input_pos +
                      line_idx) + self.client_core_service.term.clear_eol + line)
        print(self.client_core_service.term.move_xy(0, self.input_pos + len(self.scroll_lines) - 1))

    def print_to_input_line(self, msg: str) -> None:
        print(self.client_core_service.term.move_xy(0, self.input_pos + len(self.scroll_lines)
                                ) + self.client_core_service.term.clear_eol + msg, flush=True, end='')

    def print_to_scrolling(self, msg: str) -> None:
        self.scroll_lines.append(msg)
        if self.input_pos + len(self.scroll_lines) >= self.client_core_service.term.height:
            lines_for_removal = (
                self.input_pos + len(self.scroll_lines)) - self.client_core_service.term.height + 1
            for line_idx in range(lines_for_removal):
                self.scroll_lines.pop(line_idx)