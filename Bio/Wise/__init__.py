#!/usr/bin/env python2.3

__version__ = "$Revision: 1.6 $"

import os
import sys

try:
    import poly

    _NamedTemporaryFile = poly.NamedTemporaryFile
except ImportError:
    import tempfile
    
    _NamedTemporaryFile = tempfile.NamedTemporaryFile

def _build_align_cmdline(cmdline, pair, output_filename, kbyte=None, force_type=None, quiet=False):
    """
    >>> os.environ["WISE_KBYTE"]="300000"
    >>> _build_align_cmdline(["dnal"], ("seq1.fna", "seq2.fna"), "/tmp/output", kbyte=100000)
    'dnal -kbyte 100000 seq1.fna seq2.fna > /tmp/output'
    >>> _build_align_cmdline(["psw"], ("seq1.faa", "seq2.faa"), "/tmp/output_aa")
    'psw -kbyte 300000 seq1.faa seq2.faa > /tmp/output_aa'

    """
    cmdline = cmdline[:]

    if force_type:
        cmdline.insert(0, "WISE_FORCE_TYPE=%s" % force_type)

    if kbyte is None:
        try:
            cmdline.extend(("-kbyte", os.environ["WISE_KBYTE"]))
        except KeyError:
            pass
    else:
        cmdline.extend(("-kbyte", str(kbyte)))

    try:
        import poly
        if poly.jobid:
            cmdline.append("-quiet")
    except ImportError:
        pass

    cmdline.extend(pair)
    cmdline.extend((">", output_filename))
    if quiet:
        cmdline.extend(("2>", "/dev/null"))
    cmdline_str = ' '.join(cmdline)

    return cmdline_str

def align(cmdline, pair, kbyte=None, force_type=None, dry_run=False, quiet=False, debug=False):
    """
    Returns a filehandle
    """
    temp_file = _NamedTemporaryFile(mode='r')
    cmdline_str = _build_align_cmdline(cmdline,
                                       pair,
                                       temp_file.name,
                                       kbyte,
                                       force_type,
                                       quiet)

    if dry_run:
        print cmdline_str
        return

    if debug:
        print >>sys.stderr, cmdline_str
        
    os.system(cmdline_str)
    return temp_file

def all_pairs(singles):
    """
    Generate pairs list for all-against-all alignments

    >>> all_pairs(range(4))
    [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    """
    pairs = []

    singles = list(singles)
    while singles:
        suitor = singles.pop(0) # if sorted, stay sorted
        pairs.extend([(suitor, single) for single in singles])

    return pairs

def main():
    pass

def _test(*args, **keywds):
    import doctest, sys
    doctest.testmod(sys.modules[__name__], *args, **keywds)

if __name__ == "__main__":
    if __debug__:
        _test()
    main()