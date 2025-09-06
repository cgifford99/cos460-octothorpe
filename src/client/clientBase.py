import copy
import math
import sys
from threading import Thread

import blessed

from .clientServerReader import OctothorpeServerReader
from .clientWriter import OctothorpeClientWriter


class OctothorpeClient(object):
    '''The Client is responsible for managing all core resources for each client.
    
    The Client is created once on the main thread and does not need a separate thread.
    '''
    def __init__(self, socket, root_path):
        self.socket = socket
        self.root_path = root_path

        self.term = blessed.Terminal()
        if not self.term.is_a_tty:
            raise Exception('A terminal is required to use this program')
        self.input_pos = math.floor(self.term.height * 0.6)
        self.scroll_lines = []

        self.user_info = {'username': None, 'position': None, 'score': None}
        self.shortcuts = {'KEY_UP': 'move north', 'KEY_DOWN': 'move south',
                          'KEY_LEFT': 'move west', 'KEY_RIGHT': 'move east'}

        self.map = []
        # map_mask using array of tuple
        # where tuple = (entity_abbr, x, y)
        # and entity_abbr is preferably a single char
        self.map_mask = []
        self.treasure_mask = []

        self.client_writer = OctothorpeClientWriter(self.socket)
        new_clientwriter_thread = Thread(
            target=self.client_writer.client_writer_handler)
        new_clientwriter_thread.start()

        serverreader = OctothorpeServerReader(self, self.socket)
        new_serverreader_thread = Thread(
            target=serverreader.server_reader_handler)
        new_serverreader_thread.start()

    def sh_shutdown(self, signum, frame):
        self.socket.close()
        sys.exit()

    def build_map(self):
        # add map and map_mask to build string/ascii map with mask
        temp_map = copy.deepcopy(self.map)
        masks = self.treasure_mask + self.map_mask
        for entity_abbr, x, y in masks:
            temp_map[y] = temp_map[y][:x] + entity_abbr + temp_map[y][x+1:]
        return temp_map

    def client_handler(self):
        print(self.term.clear)
        while True:
            raw_input_buffer = ''
            char = ''
            with self.term.cbreak():
                while True:
                    char = self.term.inkey()
                    if not char:
                        continue
                    if char.name == 'KEY_ENTER':
                        char = '\r\n'
                    elif char.name == 'KEY_BACKSPACE' or char.name == 'KEY_DELETE':
                        if len(raw_input_buffer) > 0:
                            raw_input_buffer = raw_input_buffer[:-1]
                            self.print_to_input_line(raw_input_buffer)
                        continue
                    elif char.name in self.shortcuts:
                        char = self.shortcuts[char.name] + '\r\n'
                    raw_input_buffer += char
                    if raw_input_buffer[-2:] == '\r\n':
                        break
                    self.print_to_input_line(raw_input_buffer)
            self.print_to_input_line('')
            self.client_writer.queue.put(raw_input_buffer)

    def update_screen(self):
        self.input_pos = math.floor(self.term.height * 0.6)
        username = self.user_info["username"] or 'N/A'
        position = self.user_info["position"] or 'N/A'
        score = self.user_info["score"] or 'N/A'
        with self.term.hidden_cursor():
            print(self.term.home + self.term.clear_eol +
                  f'Username:{username}, Position:{position}, Score:{score}\n')
            if self.map and self.map_mask:
                temp_map = self.build_map()
                num_map_lines = self.input_pos - 1
                upper_map = 0
                lower_map = num_map_lines
                if self.user_info['username']:
                    zone = self.user_info['position'][1] // num_map_lines
                    upper_map = zone * num_map_lines
                    lower_map = num_map_lines + upper_map
                    if lower_map > len(temp_map):
                        lower_map = len(temp_map)
                        upper_map = lower_map - num_map_lines

                scr_line_idx = 0
                for map_line_idx in range(upper_map, lower_map):
                    line = temp_map[map_line_idx]
                    print(self.term.move_xy(0, scr_line_idx + 1) +
                          self.term.clear_eol + line)
                    scr_line_idx += 1

            for line_idx in range(len(self.scroll_lines)):
                line = self.scroll_lines[line_idx]
                print(self.term.move_xy(0, self.input_pos +
                      line_idx) + self.term.clear_eol + line)
        print(self.term.move_xy(0, self.input_pos + len(self.scroll_lines) - 1))

    def print_to_input_line(self, msg):
        print(self.term.move_xy(0, self.input_pos + len(self.scroll_lines)
                                ) + self.term.clear_eol + msg, flush=True, end='')

    def print_to_scrolling(self, msg):
        self.scroll_lines.append(msg)
        if self.input_pos + len(self.scroll_lines) >= self.term.height:
            lines_for_removal = (
                self.input_pos + len(self.scroll_lines)) - self.term.height + 1
            for line_idx in range(lines_for_removal):
                self.scroll_lines.pop(line_idx)

    def update_player_position(self, entity_abbr, x, y):
        entity_idx = -1
        for index, item in enumerate(self.map_mask):
            if item[0] == entity_abbr:
                entity_idx = index
                break
        if entity_idx != -1:
            self.map_mask[entity_idx] = (entity_abbr, x, y)
        else:
            self.map_mask.append((entity_abbr, x, y))

    def update_treasure_position(self, x, y):
        self.treasure_mask.append(('#', x, y))