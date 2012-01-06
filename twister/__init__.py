# Twister
# Copyright 20011-2012 Jun Kimura
# See LICENSE for details.

"""
Twister: Twitter Streaming Server
"""
__version__ = '0.30'
__author__ = 'Jun Kimura'
__license__ = 'MIT'

from twister.server import Twister, TwisterListener
from twister.handler import EventHandler, DispersionServerHandler
from twister.util import daemonize

# Global, unauthenticated instance of API
#api = API()

def debug(enable=True, level=1):

    import httplib
    httplib.HTTPConnection.debuglevel = level

