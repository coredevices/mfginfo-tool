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
def app_list(cmdr):
    """ List applications.
    """
    return cmdr.send_prompt_command("app list")


@PebbleCommander.command()
def app_load_metadata(cmdr):
    """ Ghetto metadata loading for pbw_image.py
    """
    ret = cmdr.send_prompt_command("app load metadata")
    if not ret[0].startswith("OK"):
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def app_launch(cmdr, idnum):
    """ Launch an application.
    """
    idnum = int(str(idnum), 0)
    if idnum == 0:
        raise exceptions.ParameterError('idnum out of range: %d' % idnum)
    ret = cmdr.send_prompt_command("app launch %d" % idnum)
    if not ret[0].startswith("OK"):
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def app_remove(cmdr, idnum):
    """ Remove an application.
    """
    idnum = int(str(idnum), 0)
    if idnum == 0:
        raise exceptions.ParameterError('idnum out of range: %d' % idnum)
    ret = cmdr.send_prompt_command("app remove %d" % idnum)
    if not ret[0].startswith("OK"):
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def app_resource_bank(cmdr, idnum=0):
    """ Get resource bank info for an application.
    """
    idnum = int(str(idnum), 0)
    if idnum < 0:
        raise exceptions.ParameterError('idnum out of range: %d' % idnum)
    ret = cmdr.send_prompt_command("resource bank info %d" % idnum)
    if not ret[0].startswith("OK "):
        raise exceptions.PromptResponseError(ret)
    return [ret[0][3:]]


@PebbleCommander.command()
def app_next_id(cmdr):
    """ Get next free application ID.
    """
    return cmdr.send_prompt_command("app next id")


@PebbleCommander.command()
def app_available(cmdr, idnum):
    """ Check if an application is available.
    """
    idnum = int(str(idnum), 0)
    if idnum == 0:
        raise exceptions.ParameterError('idnum out of range: %d' % idnum)
    return cmdr.send_prompt_command("app available %d" % idnum)
