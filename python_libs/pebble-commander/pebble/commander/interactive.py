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

import shlex
import traceback

from log_hashing.logdehash import LogDehash
import prompt_toolkit

from .commander import PebbleCommander


class InteractivePebbleCommander(object):
    """ Interactive Pebble Commander.
        Most/all UI implementations should either use this directly or sub-class it.
    """
    def __init__(self, loghash_path=None, tty=None, capfile=None):
        self.cmdr = PebbleCommander(tty=tty, interactive=True, capfile=capfile)
        if loghash_path is None:
            loghash_path = "build/src/fw/loghash_dict.json"
        self.dehasher = LogDehash(loghash_path)
        self.cmdr.attach_log_listener(self.log_listener)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.cmdr.close()
        except:
            pass

    def attach_prompt_toolkit(self):
        """ Attaches prompt_toolkit things
        """
        self.history = prompt_toolkit.history.InMemoryHistory()
        self.cli = prompt_toolkit.CommandLineInterface(
            application=prompt_toolkit.shortcuts.create_prompt_application(u"> ",
                                                                           history=self.history),
            eventloop=prompt_toolkit.shortcuts.create_eventloop())
        self.patch_context = self.cli.patch_stdout_context(raw=True)
        self.patch_context.__enter__()

    def log_listener(self, msg):
        """ This is called on every incoming log message.
            `msg` is the raw log message class, without any dehashing.

            Subclasses should override this probably.
        """
        line_dict = self.dehasher.dehash(msg)
        line = self.dehasher.commander_format_line(line_dict)
        print line

    def dispatch_command(self, string):
        """ Dispatches a command string.

            Subclasses should not override this.
        """
        args = shlex.split(string)
        # Starting with '!' passes the rest of the line directly to prompt.
        # Otherwise we try to run a command; if that fails, the line goes to prompt.
        if string.startswith("!"):
            string = string[1:]  # Chop off the '!' marker
        else:
            cmd = self.cmdr.get_command(args[0])
            if cmd:  # If we provide the command, run it.
                return cmd(*args[1:])

        return self.cmdr.send_prompt_command(string)

    def input_handle(self, string):
        """ Handles an input line.
            Generally the flow is to handle any UI-specific commands, then pass on to
            dispatch_command.

            Subclasses should override this probably.
        """
        # Handle "quit" strings
        if string in ["exit", "q", "quit"]:
            return False

        try:
            resp = self.dispatch_command(string)
            if resp is not None:
                print "\x1b[1m" + '\n'.join(resp) + "\x1b[m"
        except:
            print "An error occurred!"
            traceback.print_exc()

        return True

    def get_command(self):
        """ Get a command input line.
            If there is no line, return an empty string or None.
            This may block.

            Subclasses should override this probably.
        """
        if self.cli is None:
            self.attach_prompt_toolkit()
        doc = self.cli.run(reset_current_buffer=True)
        if doc:
            return doc.text
        else:
            return None

    def command_loop(self):
        """ The main command loop.

            Subclasses could override this, but it's probably not useful to do.
        """
        while True:
            try:
                cmd = self.get_command()
                if cmd and not self.input_handle(cmd):
                    break
            except (KeyboardInterrupt, EOFError):
                break
