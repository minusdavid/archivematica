#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

"""Assign UUIDs to all directories in a unit, i.e., Transfer.

This client script assigns a UUID to all subdirectories of a Transfer by
generating a new UUID for each and recording that UUID in a ``Directory``
database row (model instance).

Command-line arguments are the path to the Transfer and the Transfer's UUID. If
the --include-dirs option is something other than 'Yes', the script will exit
without doing anything.

"""

from __future__ import print_function

import argparse
from functools import wraps
import os
import sys
from uuid import uuid4

import django
django.setup()
# dashboard
from main.models import Directory, Transfer
# archivematicaCommon
from custom_handlers import get_script_logger


logger = get_script_logger('archivematica.mcp.client.assignUUIDsToDirectories')


class DirsUUIDsException(Exception):
    """If I am raised, return 1."""
    exit_code = 1


class DirsUUIDsWarning(Exception):
    """If I am raised, return 0."""
    exit_code = 0


def exit_on_known_exception(func):
    """Decorator that makes this module's ``main`` function cleaner by handling
    early exiting by catching particular exceptions.
    """
    @wraps(func)
    def wrapped(*_args, **kwargs):
        try:
            func(*_args, **kwargs)
        except (DirsUUIDsException, DirsUUIDsWarning) as exc:
            return exc.exit_code
    return wrapped


def _exit_if_not_include_dirs(include_dirs):
    """Quit processing if include_dirs is not truthy."""
    if not include_dirs:
        logger.info('Configuration indicates that directories in this Transfer'
                    ' should not be given UUIDs.')
        raise DirsUUIDsWarning


def _get_transfer_mdl(transfer_uuid):
    """Get the ``Transfer`` model with UUID ``transfer_uuid``."""
    try:
        return Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        logger.warning('There is no transfer with UUID %s', transfer_uuid)
        raise DirsUUIDsException


def _format_dir_path(dir_path, transfer_path):
    """Add "/" to end of ``dir_path`` and replace actual root directory
    ``transfer_path`` with a constant.
    """
    return os.path.join(dir_path, '').replace(
        transfer_path, '%transferDirectory%', 1)


def _get_dir_paths(transfer_path):
    """Return a generator of subdirectory paths in ``transfer_path``."""
    if not os.path.isdir(transfer_path):
        logger.warning('Transfer path %s is not a path to a directory',
                       transfer_path)
        raise DirsUUIDsException
    # objects/ and root dirs need no UUIDs.
    exclude_paths = (transfer_path, os.path.join(transfer_path, 'objects'))
    return (_format_dir_path(dir_path, transfer_path) for dir_path, __, ___ in
            os.walk(transfer_path) if dir_path not in exclude_paths)


def _get_dir_uuids(dir_paths):
    """Return a generator of 2-tuples containing a directory path and its newly
    minted UUID.
    """
    for dir_path in dir_paths:
        uuid = str(uuid4())
        msg = 'Assigning UUID {} to directory path {}'.format(
            uuid, dir_path)
        print(msg)
        logger.info(msg)
        yield dir_path, uuid


def _create_directory_models(dir_paths_uuids, transfer_mdl):
    """Create ``Directory`` models to encode the relationship between each
    directory path, the UUID for that directory, and the ``Transfer`` model
    that the directories are a part of.
    """
    Directory.objects.bulk_create([
        Directory(uuid=dir_uuid,
                  transfer=transfer_mdl,
                  originallocation=dir_path,
                  currentlocation=dir_path)
        for dir_path, dir_uuid in dir_paths_uuids])


def str2bool(val):
    """'True' is ``True``; aught else is ``False."""
    if val == 'True':
        return True
    return False


@exit_on_known_exception
def main(transfer_path, transfer_uuid, include_dirs):
    """Assign UUIDs to all of the directories (and subdirectories, i.e., all
    unique directory paths) in the absolute system path ``transfer_path``, such
    being the root directory of the transfer with UUID ``transfer_uuid``. Do
    this only if ``include_dirs`` is ``True``.
    TODO: deal with reingest (and SIPs) later, if applicable. Just focusing on
    transfer for now.
    """
    _exit_if_not_include_dirs(include_dirs)
    _create_directory_models(
        _get_dir_uuids(_get_dir_paths(transfer_path)),
        _get_transfer_mdl(transfer_uuid))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('transfer_path', type=str,
                        help='The path to the Transfer on disk.')
    parser.add_argument('transfer_uuid', type=str,
                        help='The UUID of the Transfer.')
    parser.add_argument('--include-dirs', action='store', type=str2bool,
                        dest="include_dirs", default='No')
    args = parser.parse_args()
    logger.info('assignUUIDsToDirectories called with args: %s', vars(args))
    sys.exit(main(**vars(args)))
