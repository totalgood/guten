"""Find all the different file names in an ls-R file

>>> CRE_EXT.match('hello.world.txt').groups()[1]
'.txt'
>>> CRE_EXT.match('good.bye.world.txt').groups()[1]
'.txt'
>>> CRE_EXT.match('bigfile.iso2_-').groups()[1]
'.iso2_-'
"""
import re

CRE_EXT = re.compile(r'^([^.]+|[^.]+[.][^.]+|[^.]+[.][^.]+[.][^.]+)([.][^.]*[^:])$')


def extract_extensions(file_path='ls-R.txt', limit=float('inf')):
    extensions = set()
    with open(file_path) as fin:
        for i, line in enumerate(fin):
            line = line.rstrip('\r\n')
            # print(line.rstrip('\r\n'))
            ext = CRE_EXT.match(line)
            if ext:
                extensions.add(ext.groups()[1])
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
