# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import collections
import struct
from datetime import datetime

import pebble.pulse2.exceptions

from .. import exceptions


class Prompt(object):

    PORT_NUMBER = 0x3e20

    def __init__(self, link):
        self.socket = link.open_socket('reliable', self.PORT_NUMBER)

    def command_and_response(self, command_string, timeout=20):
        log = []
        self.socket.send(command_string.encode())

        is_done = False
        while not is_done:
            try:
                response = PromptResponse.parse(
                        self.socket.receive(timeout=timeout))
                if response.is_done_response:
                    is_done = True
                elif response.is_message_response:
                    log.append(response.message.decode())
            except pebble.pulse2.exceptions.ReceiveQueueEmpty:
                raise exceptions.CommandTimedOut
        return log

    def close(self):
        self.socket.close()


class PromptResponse(collections.namedtuple('PromptResponse',
                     'response_type timestamp message')):

    DONE_RESPONSE = 101
    MESSAGE_RESPONSE = 102

    response_struct = struct.Struct('<BQ')

    @property
    def is_done_response(self):
        return self.response_type == self.DONE_RESPONSE

    @property
    def is_message_response(self):
        return self.response_type == self.MESSAGE_RESPONSE

    @classmethod
    def parse(cls, response):
        result = cls.response_struct.unpack(response[:cls.response_struct.size])

        response_type = result[0]
        timestamp = datetime.fromtimestamp(result[1] / 1000.0)
        message = response[cls.response_struct.size:]

        return cls(response_type, timestamp, message)
