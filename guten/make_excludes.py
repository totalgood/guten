#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find all the different file names in an ls-R file

>>> CRE_EXT.match('hello.world.txt').groups()[1]
'.txt'
>>> CRE_EXT.match('good.bye.world.txt').groups()[1]
'.txt'
>>> CRE_EXT.match('bigfile.iso2_-').groups()[1]
'.iso2_-'
"""
from __future__ import division, print_function, absolute_import

import argparse
import sys
import logging

from guten import __version__

import re

logger = logging.getLogger(__name__)
CRE_EXT = re.compile(r'^([^.]+|[^.]+[.][^.]+|[^.]+[.][^.]+[.][^.]+)([.][^.]*[^:])$')

__author__ = "Hobson Lane"
__copyright__ = "Hack Oregon, Hack University"
__license__ = "MIT"


def extract_extensions(file_path='ls-R.txt', limit=float('inf'), stream=True):
    extensions = set()
    with open(file_path) as fin:
        for i, line in enumerate(fin):
            if not stream and not i % 1000:
                logger.info('After {} lines of file names in {} there are {} unique extensions...'.format(i, file_path, len(extensions)))
            line = line.rstrip('\r\n')
            # print(line.rstrip('\r\n'))
            ext = CRE_EXT.match(line)
            if ext and ext.groups()[1] not in extensions:
                extensions.add(ext.groups()[1])
                if stream:
                    print(ext.groups()[1])
            if len(extensions) > limit:
                break
    return extensions


def write_excludes(extensions, file_path='excludes.txt', include_pattern=re.compile(r'^.txt$')):
    lines = 0
    with open(file_path, 'w') as fout:
        for ext in extensions:
            if not include_pattern.match(ext):
                fout.write('*' + ext + '\n')
                lines += 1
    return lines


def parse_args(args):
    """Parse command line parameters (arguments and options)

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Parse a text file containing a list of file names (with colon (:) terminated path headers) to produce a list of unique")
    parser.add_argument('-v', '--version',
                        action='version',
                        version='guten {ver}'.format(ver=__version__))
    parser.add_argument('file_path', nargs='?', default="../data/ls-R",
                        help='Path to a file containing a list of file names in the format output by `ls -R` > $FILE_PATH')
    return parser.parse_args(args)


def main(args):
    args = parse_args(args)
    extract_extensions(file_path=args.file_path, stream=True)


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
