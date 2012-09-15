#!/usr/bin/env python

'''A Python module that allows you to connect to IRC in a simple way.'''

try:
    from libirc.ircconnection import *
except ImportError:
    from ircconnection import *

__all__=['ircconnection']

# vim: et ft=python sts=4 sw=4 ts=4
