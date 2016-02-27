#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Remove blank lines and white space from end of python files"""
from __future__ import division, print_function, absolute_import
from guten.count import generate_files

import argparse
import sys
import logging
import os
import re

LOG_FORMAT = "%(module)s.%(function)s:%(lineno)d %(message)s"
DEFAULT_MODEL_PATH = os.path.join('data', 'trained-detector-wsj-ptb.json.gz')

from guten import __version__


__author__ = "Hobson Lane"
__copyright__ = "TotalGood"
__license__ = "mit"

log = logging.getLogger(__name__)


class VAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        # print 'values: {v!r}'.format(v=values)
        if values is None:
            values = '1'
        try:
            values = int(values)
        except ValueError:
            values = values.count('v') + 1
        setattr(args, self.dest, values)


def parse_args(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(description="Python source code file delinter")
    parser.add_argument('--version', action='version',
                        version='{module} {ver}'.format(module=__file__, ver=__version__))
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='enable verbose output, can be provided more than once for greater verbosity')
    parser.add_argument("-f", "--force", action="store_true",
                        help="force write changes to files in-place withotu confirmation")
    parser.add_argument("-vv", "--very-verbose", action="store_true",
                        help="more verbose output")
    return parser.parse_args(args)


def clean_tail(filepath, eol='\n', force=False):
    i = -1
    with open(filepath, 'rw+') as fout:
        c = None
        while True:
            log.debug('{}: {}'.format(fout.name, i))
            try:
                fout.seek(i, os.SEEK_END)
            except IOError:
                pass
            c = fout.read(1)
            log.debug('{}[{}]=[{}]:{}'.format(fout.name, i, fout.tell(), repr(c)))
            if re.match(r'^\s$', c):
                i -= 1
            else:
                c = fout.read(1)
                break
        if c != eol:
            log.info('Preparing to truncate {} at position {} ({}) after character {}'.format(repr(filepath), i, fout.tell(), repr(c)))
            if force:
                log.warn('truncating {} at position {} ({})'.format(repr(filepath), i, c))
                fout.truncate()
                if fout.tell():
                    fout.write('\n')


def main(args):
    args = parse_args(args)
    if args.verbose > 1:
        logging.basicConfig(format=LOG_FORMAT, level="DEBUG")
    elif args.verbose:
        logging.basicConfig(format=LOG_FORMAT, level="INFO")
    else:
        logging.basicConfig(format=LOG_FORMAT)

    for f in generate_files(ext='.py'):
        if f['type'] == 'file':
            clean_tail(f['path'], force=args.force)
    log.info("Finished delinting")


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
