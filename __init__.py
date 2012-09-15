#!/usr/bin/env python

'''A Python module that allows you to connect to IRC in a simple way.'''

try:
    from libirc.libirc import *
except ImportError:
    from libirc import *

__all__=['libirc']

# vim: et ft=python sts=4 sw=4 ts=4
