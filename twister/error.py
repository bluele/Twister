#-*- coding:utf-8 -*-
# Twister
# Copyright 20011-2012 Jun Kimura
# See LICENSE for details.

'''
@summary: Exception at no response.
'''
class NoResponse(Exception):
    def __init__(self, reason, response=None):
        self.reason = unicode(reason)
        self.response = response

    def __str__(self):
        return self.reason

'''
@summary: Exception at event error.
'''
class NotFoundEvent(Exception):
    def __init__(self, reason, response=None):
        self.reason = unicode(reason)
        self.response = response

    def __str__(self):
        return self.reason

'''
@summary: Twister exception.
'''
class TwisterError(Exception):

    def __init__(self, reason, response=None):
        self.reason = unicode(reason)
        self.response = response

    def __str__(self):
        return self.reason
