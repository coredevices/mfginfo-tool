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
def click_short(cmdr, button):
    """ Click a button.
    """
    button = int(str(button), 0)
    if not 0 <= button <= 3:
        raise exceptions.ParameterError('button out of range: %d' % button)
    ret = cmdr.send_prompt_command("click short %d" % button)
    if not ret[0].startswith("OK"):
        raise exceptions.PromptResponseError(ret)


@PebbleCommander.command()
def click_long(cmdr, button, hold_ms=20):
    """ Hold a button.

    `hold_ms` is how many ms to hold the button down before releasing.
    """
    return cmdr.click_multiple(button, hold_ms=hold_ms)


@PebbleCommander.command()
def click_multiple(cmdr, button, count=1, hold_ms=20, delay_ms=0):
    """ Rhythmically click a button.
    """
    button = int(str(button), 0)
    count = int(str(count), 0)
    hold_ms = int(str(hold_ms), 0)
    delay_ms = int(str(delay_ms), 0)
    if not 0 <= button <= 3:
        raise exceptions.ParameterError('button out of range: %d' % button)
    if not count > 0:
        raise exceptions.ParameterError('count out of range: %d' % count)
    if hold_ms < 0:
        raise exceptions.ParameterError('hold_ms out of range: %d' % hold_ms)
    if delay_ms < 0:
        raise exceptions.ParameterError('delay_ms out of range: %d' % delay_ms)
    ret = cmdr.send_prompt_command(
        "click multiple {button:d} {count:d} {hold_ms:d} {delay_ms:d}".format(**locals()))
    if not ret[0].startswith("OK"):
        raise exceptions.PromptResponseError(ret)
