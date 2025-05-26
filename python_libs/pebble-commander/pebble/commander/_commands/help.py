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

import inspect
import sys

from .. import PebbleCommander, exceptions, parsers


def trim_docstring(var):
    return inspect.getdoc(var) or ''


def get_help_short(cmdr, cmd_name, help_output=None):
    """
    cmd_name is the command's name.
    help_output is the raw output of the `!help` command.
    """
    output = None
    func = cmdr.get_command(cmd_name)
    if func:  # Host command
        # cmdstr is the actual function name
        cmdstr = func.name
        spec = inspect.getargspec(func)

        if len(spec.args) > 1:
            maxargs = len(spec.args) - 1
            if spec.defaults is None:
                cmdstr += " {%d args}" % maxargs
            else:
                minargs = maxargs - len(spec.defaults)
                cmdstr += " {%d~%d args}" % (minargs, maxargs)

        if func.__doc__ is not None:
            output = "%-30s - %s" % (cmdstr, trim_docstring(func).splitlines()[0])
        else:
            output = cmdstr
    else:  # Prompt command
        if cmd_name[0] == '!':  # Strip the bang if it's there
            cmd_name = cmd_name[1:]

        # Get the output if it wasn't provided
        if help_output is None:
            help_output = cmdr.send_prompt_command("help")

        for prompt_cmd in help_output[1:]:
            # Match, even with argument count provided
            if prompt_cmd == cmd_name or prompt_cmd.startswith(cmd_name+" "):
                # Output should be the full argument string with the bang
                output = '!' + prompt_cmd
                break

    return output


def help_arginfo_nodefault(arg):
    return "%s" % arg.upper()


def help_arginfo_default(arg, dflt):
    return "[%s (default: %s)]" % (arg.upper(), str(dflt))


def get_help_long(cmdr, cmd_name):
    output = ""

    func = cmdr.get_command(cmd_name)

    if func:
        spec = inspect.getargspec(func)
        specstr = []
        for i, arg in enumerate(spec.args[1:]):
            if spec.defaults is not None:
                minargs = len(spec.args[1:]) - len(spec.defaults)
                if i >= minargs:
                    specstr.append(help_arginfo_default(arg, spec.defaults[i - minargs]))
                else:
                    specstr.append(help_arginfo_nodefault(arg))
            else:
                specstr.append(help_arginfo_nodefault(arg))

        specstr = ' '.join(specstr)
        cmdstr = func.name + " " + specstr
        if func.__doc__ is None:
            output = "%s\n\nNo help available." % cmdstr
        else:
            output = "%s - %s" % (cmdstr, trim_docstring(func))
    else:  # Prompt command
        cmdstr = get_help_short(cmdr, cmd_name)
        if cmdstr is None:
            output = None
        else:
            output = "%s\n\nNo help available, due to being a prompt command." % cmdstr
    return output


@PebbleCommander.command()
def help(cmdr, cmd=None):
    """ Show help.

    You're lookin' at it, dummy!
    """
    out = []
    if cmd is not None:
        helpstr = get_help_long(cmdr, cmd)
        if helpstr is None:
            raise exceptions.ParameterError("No command '%s' found." % cmd)
        out.append(helpstr)
    else:  # List commands
        out.append("===Host commands===")
        # Bonus, this list is sorted for us already
        for cmd_name in dir(cmdr):
            if cmdr.get_command(cmd_name):
                out.append(get_help_short(cmdr, cmd_name))

        out.append("\n===Prompt commands===")
        ret = cmdr.send_prompt_command("help")
        if ret[0] != 'Available Commands:':
            raise exceptions.PromptResponseError("'help' prompt command output invalid")
        for cmd_name in ret[1:]:
            out.append(get_help_short(cmdr, "!" + cmd_name, ret))
    return out
