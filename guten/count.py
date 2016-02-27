#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute a vocabulary (gensim.Dictionary) from a folder containing text files"""
from __future__ import division, print_function, absolute_import

import os
import stat
import collections
import warnings
import datetime
from itertools import tee

from gensim.corpora import TextCorpus
from guten.wordvec import generate_tokens

import sys
import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# logging.basicConfig(format='%(name)s.%(module)s:%(lineno)d: %(message)s', stream='ext://sys.stderr')
log = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter('%(name)s.%(module)s:%(lineno)d: %(message)s')
log.addHandler(handler)


# TODO: eol is unused
# TODO: close file or use it as context within iterator
class FileLineGen(object):

    def __init__(self, path, mode='rUb', eol='\n'):
        self.path = path
        # open the file so exception raised if does not exist
        if isinstance(self.path, basestring):
            self.file_obj = open(self.path, mode)
        self.path = self.file_obj.name
        self.eol = eol  # TODO: unused
        self.file_obj.close()

    def __iter__(self):
        with open(self.path) as self.file_obj:
            for line in self.file_obj:
                yield line


def find_files(path='', ext='', level=None, typ=list, dirs=False, files=True, verbosity=0):
    """Recursively find all files in the indicated directory

    Filter by the indicated file name extension (ext)

    Args:
      path (str):  Root/base path to search.
      ext (str):   File name extension. Only file paths that ".endswith()" this string will be returned
      level (int, optional): Depth of file tree to halt recursion at.
        None = full recursion to as deep as it goes
        0 = nonrecursive, just provide a list of files at the root level of the tree
        1 = one level of depth deeper in the tree
      typ (type):  output type (default: list). if a mapping type is provided the keys will be the full paths (unique)
      dirs (bool):  Whether to yield dir paths along with file paths (default: False)
      files (bool): Whether to yield file paths (default: True)
        `dirs=True`, `files=False` is equivalent to `ls -d`

    Returns:
      list of dicts: dict keys are { 'path', 'name', 'bytes', 'created', 'modified', 'accessed', 'permissions' }
        path (str): Full, absolute paths to file beneath the indicated directory and ending with `ext`
        name (str): File name only (everythin after the last slash in the path)
        size (int): File size in bytes
        created (datetime): File creation timestamp from file system
        modified (datetime): File modification timestamp from file system
        accessed (datetime): File access timestamp from file system
        permissions (int): File permissions bytes as a chown-style integer with a maximum of 4 digits
        type (str): One of 'file', 'dir', 'symlink->file', 'symlink->dir', 'symlink->broken'
          e.g.: 777 or 1755

    Examples:
      >>> 'util.py' in [d['name'] for d in find_files(os.path.dirname(__file__), ext='.py', level=0)]
      True
      >>> (d for d in find_files(os.path.dirname(__file__), ext='.py') if d['name'] == 'util.py').next()['size'] > 1000
      True

      There should be an __init__ file in the same directory as this script.
      And it should be at the top of the list.
      >>> sorted(d['name'] for d in find_files(os.path.dirname(__file__), ext='.py', level=0))[0]
      '__init__.py'
      >>> all(d['type'] in ('file','dir','symlink->file','symlink->dir','mount-point->file','mount-point->dir',
      ...       'block-device','symlink->broken','pipe','special','socket','unknown') for d in find_files(level=1, files=True, dirs=True))
      True
      >>> os.path.join(os.path.dirname(__file__), '__init__.py') in find_files(
      ... os.path.dirname(__file__), ext='.py', level=0, typ=dict)
      True
    """
    gen = generate_files(path, ext=ext, level=level, dirs=dirs, files=files, verbosity=verbosity)
    if isinstance(typ(), collections.Mapping):
        return typ((ff['path'], ff) for ff in gen)
    elif typ is not None:
        return typ(gen)
    else:
        return gen


def generate_files(path='', ext='', level=None, dirs=False, files=True, verbosity=0):
    """Recursively generate files (and thier stats) in the indicated directory

    Filter by the indicated file name extension (ext)

    Args:
      path (str):  Root/base path to search.
      ext (str):   File name extension. Only file paths that ".endswith()" this string will be returned
      level (int, optional): Depth of file tree to halt recursion at.
        None = full recursion to as deep as it goes
        0 = nonrecursive, just provide a list of files at the root level of the tree
        1 = one level of depth deeper in the tree
      typ (type):  output type (default: list). if a mapping type is provided the keys will be the full paths (unique)
      dirs (bool):  Whether to yield dir paths along with file paths (default: False)
      files (bool): Whether to yield file paths (default: True)
        `dirs=True`, `files=False` is equivalent to `ls -d`

    Returns:
      list of dicts: dict keys are { 'path', 'name', 'bytes', 'created', 'modified', 'accessed', 'permissions' }
        path (str): Full, absolute paths to file beneath the indicated directory and ending with `ext`
        name (str): File name only (everythin after the last slash in the path)
        size (int): File size in bytes
        created (datetime): File creation timestamp from file system
        modified (datetime): File modification timestamp from file system
        accessed (datetime): File access timestamp from file system
        permissions (int): File permissions bytes as a chown-style integer with a maximum of 4 digits
        type (str): One of 'file', 'dir', 'symlink->file', 'symlink->dir', 'symlink->broken'
          e.g.: 777 or 1755

    Examples:
      >>> 'util.py' in [d['name'] for d in generate_files(os.path.dirname(__file__), ext='.py', level=0)]
      True
      >>> (d for d in generate_files(os.path.dirname(__file__), ext='.py') if d['name'] == 'util.py').next()['size'] > 1000
      True
      >>> sorted(generate_files().next().keys())
      ['accessed', 'created', 'dir', 'mode', 'modified', 'name', 'path', 'size', 'type']

      There should be an __init__ file in the same directory as this script.
      And it should be at the top of the list.
      >>> sorted(d['name'] for d in generate_files(os.path.dirname(__file__), ext='.py', level=0))[0]
      '__init__.py'
      >>> sorted(list(generate_files())[0].keys())
      ['accessed', 'created', 'dir', 'mode', 'modified', 'name', 'path', 'size', 'type']
      >>> all(d['type'] in ('file','dir','symlink->file','symlink->dir','mount-point->file','mount-point->dir','block-device',
      ...        'symlink->broken','pipe','special','socket','unknown') for d in generate_files(level=1, files=True, dirs=True))
      True
    """
    path = path or './'
    ext = str(ext).lower()

    for dir_path, dir_names, filenames in walk_level(path, level=level):
        if verbosity > 0:
            print('Checking path "{}"'.format(dir_path))
        if files:
            for fn in filenames:  # itertools.chain(filenames, dir_names)
                if ext and not fn.lower().endswith(ext):
                    continue
                yield path_status(dir_path, fn, verbosity=verbosity)
        if dirs:
            # TODO: warn user if ext and dirs both set
            for fn in dir_names:
                if ext and not fn.lower().endswith(ext):
                    continue
                yield path_status(dir_path, fn, verbosity=verbosity)


def walk_level(path, level=1):
    """Like os.walk, but takes `level` kwarg that indicates how deep the recursion will go.

    Notes:
      TODO: refactor `level`->`depth`

    References:
      http://stackoverflow.com/a/234329/623735

    Args:
     path (str):  Root path to begin file tree traversal (walk)
      level (int, optional): Depth of file tree to halt recursion at.
        None = full recursion to as deep as it goes
        0 = nonrecursive, just provide a list of files at the root level of the tree
        1 = one level of depth deeper in the tree

    Examples:
      >>> root = os.path.dirname(__file__)
      >>> all((os.path.join(base,d).count('/')==(root.count('/')+1)) for (base, dirs, files) in walk_level(root, level=0) for d in dirs)
      True
    """
    if level is None:
        level = float('inf')
    path = path.rstrip(os.path.sep)
    if os.path.isdir(path):
        root_level = path.count(os.path.sep)
        for root, dirs, files in os.walk(path):
            yield root, dirs, files
            if root.count(os.path.sep) >= root_level + level:
                del dirs[:]
    elif os.path.isfile(path):
        yield os.path.dirname(path), [], [os.path.basename(path)]
    else:
        raise RuntimeError("Can't find a valid folder or file for path {0}".format(repr(path)))


def path_status(path, filename='', status=None, verbosity=0):
    """Retrieve the access, modify, and create timetags for a path along with its size

    Arguments:
        path (str): full path to the file or directory to be statused
        status (dict): optional existing status to be updated/overwritten with new status values

    Returns:
        dict: {'size': bytes (int), 'accessed': (datetime), 'modified': (datetime), 'created': (datetime)}

    >>> path_status('.')
    """
    status = status or {}
    if not filename:
        dir_path, filename = os.path.split()  # this will split off a dir and as `filename` if path doesn't end in a /
    else:
        dir_path = path
    full_path = os.path.join(dir_path, filename)
    if verbosity > 1:
        print(full_path)
    status['name'] = filename
    status['path'] = full_path
    status['dir'] = dir_path
    status['type'] = []
    stat_types = dict(zip('sock chr blk fifo'.split(), 'socket special block-device pipe'.split()))
    try:
        status['size'] = os.path.getsize(full_path)
        status['accessed'] = datetime.datetime.fromtimestamp(os.path.getatime(full_path))
        status['modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
        status['created'] = datetime.datetime.fromtimestamp(os.path.getctime(full_path))
        status['mode'] = os.stat(full_path).st_mode   # first 3 digits are User, Group, Other permissions: 1=execute,2=write,4=read
        for t in ('mount', 'file', 'link', 'dir'):
            status['type'] += int(getattr(os.path, 'is' + t)(full_path)) * [t]
        if not status['type']:
            for t, name in stat_types.iteritems():
                status['type'] += int(getattr(stat, 'S_IS' + t.upper())(status['mode'])) * [name]
        status['type'] = status['type'] or ['unknown']
        if status['type'] and status['type'][-1] == 'link':
            status['type'] += ['broken']
    except OSError:
        status['type'] = ['nonexistent'] + status['type']
        if verbosity > -1:
            warnings.warn("Unable to stat path '{}'".format(full_path))
    status['type'] = '->'.join(status['type'])

    return status


class GensimCorpus(TextCorpus):
    """Simple iterator to mimic exactly what gensim does internally with its iterators

    Modeled after gensim.corpora.WikiCorpus
    """

    def __init__(self, input=None, dictionary=None, tokenize=None):
        if dictionary is not None:
            super(GensimCorpus, self).__init__(input=None)
            self.dictionary = dictionary
            self.input = input
        else:
            self.original_input = input
            # tokenize must be defined twice, before and after super init
            self.tokenize = tokenize or generate_tokens
            super(GensimCorpus, self).__init__(input=input)
        self.tokenize = tokenize or generate_tokens

    def get_texts(self):
        """Iterate over the documents, yielding lists of tokens for each document.

        To compute the dictionary, the Corpus iterates throught the docs on `__init__`
        >>> corpus = GensimCorpus(d for d in ('A B C', 'A B X Y Z'))
        >>> corpus.length
        2
        >>> list(corpus.get_texts())
        [['A', 'B', 'C'], ['A', 'B', 'X', 'Y', 'Z']]
        You can generate the same iterable twice (even a generator).
        >>> list(corpus.get_texts())
        [['A', 'B', 'C'], ['A', 'B', 'X', 'Y', 'Z']]
        And document statistics are available **after** a complete pass through the iterable
        >>> corpus.length
        2
        >>> corpus.num_tokens
        8
        >>> len(corpus.dictionary)
        6
        If you want sparse vectors, use the standard __iter__ on a TextCorpus instead of this method,
        like so:
        >> for vec in :
        >>     print(vec)
        """
        self.original_input, self.input = tee(self.original_input)
        num_tokens = 0
        for doc_num, text in enumerate(self.input):
            tokens = list(self.tokenize(text))
            num_tokens += len(tokens)
            if self.metadata:
                yield tokens, (doc_num,)
            else:
                yield tokens

        log.info("Finished iterating over a GensimCorpus of {} documents with {} tokens ({} unique).".format(
                 doc_num + 1, num_tokens, len(self.dictionary)))
        self.length = self.num_docs = doc_num + 1
        self.num_tokens = num_tokens
