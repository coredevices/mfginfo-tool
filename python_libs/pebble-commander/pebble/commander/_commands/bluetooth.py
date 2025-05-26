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

from .. import PebbleCommander, exceptions, parsers


@PebbleCommander.command()
def bt_airplane_mode(cmdr, enter=True):
    """ Enter or exit airplane mode.

    `enter` should either be a boolean, "enter", or "exit".
    """
    if parsers.str2bool(enter, also_true=["enter"], also_false=["exit"]):
        enter = "enter"
    else:
        enter = "exit"

    ret = cmdr.send_prompt_command("bt airplane mode %s" % enter)
    if ret:
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def bt_prefs_wipe(cmdr):
    """ Wipe bluetooth preferences.
    """
    ret = cmdr.send_prompt_command("bt prefs wipe")
    if ret:
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def bt_mac(cmdr):
    """ Get the bluetooth MAC address.
    """
    ret = cmdr.send_prompt_command("bt mac")
    if not ret[0].startswith("0x"):
        raise exceptions.PromptResponseError(ret)
    retstr = ret[0][2:]
    return [':'.join(retstr[i:i+2] for i in range(0, len(retstr), 2))]


@PebbleCommander.command()
def bt_set_addr(cmdr, new_mac=None):
    """ Set the bluetooth MAC address.

    Don't specify `new_mac` to revert to default.
    `new_mac` should be of the normal 6 hex octets split with colons.
    """
    if not new_mac:
        new_mac = "00:00:00:00:00:00"
    mac = parsers.str2mac(new_mac)
    macstr = ''.join(["%02X" % byte for byte in mac])
    ret = cmdr.send_prompt_command("bt set addr %s" % macstr)
    if ret[0] != new_mac:
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def bt_set_name(cmdr, new_name=None):
    """ Set the bluetooth name.
    """
    if not new_name:
        new_name = ""
    # Note: the only reason for this is because prompt sucks
    # This can probably be removed when prompt goes away
    if ' ' in new_name:
        raise exceptions.ParameterError("bluetooth name must not have spaces")
    ret = cmdr.send_prompt_command("bt set name %s" % new_name)
    if ret:
        raise exceptions.PromptResponseError(ret)
