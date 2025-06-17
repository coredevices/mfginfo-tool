#! /usr/bin/env python
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


import argparse
import json
import logging
import os
import requests
import sys
import zipfile

import logdehash
import newlogging


DICT_FIRMWARE = 'build/src/fw/loghash_dict.json'
DICT_PRF = 'build/prf/src/fw/loghash_dict.json'

BUILD_ID_STR = 'BUILD ID: '
HASH_STR_LEN = 40


SETTINGS = {
    # Hagen Daas stuff:
    'files': 'https://files.pebblecorp.com/dict/',

    # Go to https://auth.pebblecorp.com/show to get this value:
    'hd_session': None,
}


class AuthException(Exception):
    pass


def load_user_settings():
    settings_path = '~/.triage'
    try:
        user_settings_file = open(os.path.expanduser(settings_path), 'rb')
        user_settings = json.load(user_settings_file)
    except IOError as e:
        if e.errno == 2:
            logging.error("""Please create %s with credentials: """
                          """'{ "user": "$USER", "password": "$PASSWORD" }'""",
                          settings_path)
        return
    SETTINGS.update(user_settings)

    if not SETTINGS["hd_session"]:
        msg = "Missing 'hd_session' token in user settings.\n" \
              "1. Get the cookie from https://auth.pebblecorp.com/show\n" \
              "2. Add as value with key 'hd_session' to %s" % settings_path
        logging.error(msg)
        sys.exit(-1)


def get_loghash_dict_from_hagen_daas_files(hash):
    load_user_settings()

    url = SETTINGS['files'] + hash
    r = requests.get(url, headers={'Cookie': 'hd_session=%s' % SETTINGS['hd_session']})
    if (r.status_code > 400):
        r.raise_for_status()
    if "accounts.google.com" in r.url:
        raise AuthException("Not authenticated, see instructions at the top of %s" %
                            "https://pebbletechnology.atlassian.net/wiki/"
                            "display/DEV/Quickly+triaging+JIRA+FW+issues+with+pbldebug")
    return r.text


class Log(object):
    def __init__(self, output=False):
        self.output = output

    def setOutput(self, output):
        self.output = output

    def debug(self, format, *args):
        if self.output:
            sys.stderr.write(format % args)
            sys.stderr.write("\r\n")


def get_dict_from_pbz(filename):
    if zipfile.is_zipfile(filename):
        with zipfile.ZipFile(filename) as dict_zip:
            return dict_zip.read('loghash_dict.json')
    return None


def main():
    parser = argparse.ArgumentParser(description='Dehash a log',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Description:
    dehash.py is a script that tries to dehash whatever log is provided, however
    it is provided. 'Files' on Hagen-Daas will be consulted if a loghash
    dictionary isn't specified.

Input File(s):
    Can be the log to dehash and/or log hash dictionaries to decode the log.

    dehash.py assumes that the hashed log is passed via stdin.
    If specified in the file list, the hashed log must not have the extension
    .elf, .pbz, or .json.

    loghash dictionaries can be .json files, .elf files, or bundles (.pbz).
    Only one dictionary per core may be specified.

Examples:
    dehash.py pbl-123456.log tintin_fw.elf bt_da14681_main.elf > log.txt
    dehash.py normal_silk_v4.0-alpha11-20-g6661346.pbz < pbl-12345.log > log.txt
    gzcat crash_log.gz | dehash.py
    dehash.py --prf log_from_watch.log
''')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fw', action='store_true',
                       help='Use the fw loghash_dict from your build. Default.')
    group.add_argument('--prf', action='store_true',
                       help='Use the prf loghash_dict from your build.')
    parser.add_argument('-v', action='store_true',
                        help='Verbose debug to stderr')
    parser.add_argument('file', nargs='*',
                        help='Input file(s). See below for more info.')
    args = parser.parse_args()

    logger = Log(args.v)

    # Make a copy of the file list
    filelist = list(args.file)
    # Add the PRF dict to filelist, if appropriate
    if args.prf:
        filelist.append(DICT_PRF)

    loghash_dict = {}
    log = None

    # Examine the file list
    for f in filelist:
        if f.endswith('.json') or f.endswith('.elf'):
            logger.debug('Loading dictionary from %s', f)
            d = newlogging.get_log_dict_from_file(f)
            loghash_dict = newlogging.merge_dicts(loghash_dict, d)
        elif f.endswith('.pbz'):
            logger.debug('Loading dictionary from %s', f)
            d = get_dict_from_pbz(f)
            if not d:
                raise Exception("Unable to load loghash_dict.json from %s" % f)
            loghash_dict = newlogging.merge_dicts(loghash_dict, json.loads(d))
        else:
            logger.debug('Log file %s', f)
            if log:
                raise Exception("More than one log file specified")
            log = f

    # Now consider the --fw option. Don't fail unless it was explicitly specified
    if args.fw or (not args.prf and not loghash_dict):
        logger.debug('Loading dictionary from %s', DICT_FIRMWARE)
        if os.path.isfile(DICT_FIRMWARE) or args.fw:
            d = newlogging.get_log_dict_from_file(DICT_FIRMWARE)
            loghash_dict = newlogging.merge_dicts(loghash_dict, d)
        else:
            logger.debug('Ignoring default fw dict -- %s not found', DICT_FIRMWARE)

    # Create the dehasher
    dehash = logdehash.LogDehash('', monitor_dict_file=False)
    dehash.load_log_strings_from_dict(loghash_dict)

    # Input file or stdin?
    infile = open(log) if log else sys.stdin

    # Dehash the log
    for line in infile:
        line_dict = dehash.dehash(line)
        if 'unhashed' in line_dict:
            dhl = line_dict['formatted_msg']
        else:
            dhl = dehash.basic_format_line(line_dict)
        sys.stdout.write(dhl.strip())
        sys.stdout.write('\r\n')
        sys.stdout.flush()

        # If we have a dictionary, continue
        if loghash_dict:
            continue

        # No dictionary -- see if we can load one
        index = dhl.upper().rfind(BUILD_ID_STR)
        if index == -1:
            continue

        build_id = dhl[index + len(BUILD_ID_STR):(index + len(BUILD_ID_STR) + HASH_STR_LEN)]

        try:
            logger.debug('Loading dictionary from Hagen-Daas for ID %s', build_id)
            d = get_loghash_dict_from_hagen_daas_files(build_id)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError, AuthException) as error:
            sys.stderr.write("Could not get build id %s from files. %s\r\n" % (build_id, error))
            continue

        if d:
            loghash_dict = json.loads(d)
            dehash.load_log_strings_from_dict(loghash_dict)
        else:
            sys.stderr.write("Could not get build id %s from files.\r\n" % build_id)

    if infile is not sys.stdin:
        infile.close()

if __name__ == '__main__':
    main()
