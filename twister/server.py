#-*- coding:utf-8 -*-
# Twister
# Copyright 2011-2012 Jun Kimura
# See LICENSE for details.

from tweepy.streaming import StreamListener
from twister.util import get_oauth, logger
from twister.stream import TwisterStream
from twister.handler import EventHandler
from datetime import timedelta
from time import sleep


class TwisterListener(StreamListener):
    '''
    @summary: set event handler in listener class
    @param event_handler: EvHandler
    '''
    def __init__(self, handler_class, api=None, **opts):
        StreamListener.__init__(self)
        self.handler = handler_class(**opts)
        
    '''
    @summary: Called when receive tweet
    @param status: Tweet Status
    '''
    def on_status(self, status):
        try:
            status.created_at += timedelta(hours=9)
            self.handler.call(status)
        except Exception, exception:
            logger.error(str(exception))
        
        
    def on_limit(self, track):
        """Called when a limitation notice arrvies"""
        logger.debug("[limit]")
        return

    '''
    @summary: Called when a non-200 status code is returned
    @param status_code: int
    @return: bool
    '''
    def on_error(self, status_code):
        logger.error("[error] %d" % int(status_code))
        return True
        
    ''' 
    @summary: Called when stream connection times out
    @return: bool
    '''
    def on_timeout(self):
        logger.info("[timeout]")
        return True
            
    '''
    @todo: User should override this method.
    @summary: Called when response don't return from host.
    '''
    def on_noresponse(self, err):
        logger.info(u"[response error] %s." % err)
            
    '''
    @todo: User should override this method.
    @summary: Called when socket error occur.
    '''
    def on_socket_error(self, err):
        logger.error(u"[socket error] %s." % err)
        sleep(5)
        
    '''
    @todo: User should override this method.
    @summary: Called when socket error occur.  
    '''
    def on_fatal_error(self, err):
        return True


class Twister(TwisterStream):
    
    def __init__(self, auth_key, listener, **opts):
        self.auth = get_oauth(**auth_key)
        self.listener = listener
        self.handler = self.listener.handler
        TwisterStream.__init__(self,
                             self.auth,
                             self.listener,
                             secure=True,
                             http_retry=opts.get('http_retry', 3),
                             retry_time=opts.get('retry_time', 3), # streaming socket's retry time.
                             timeout=opts.get('timeout', 30), # streaming socket's timeout
                             )
        
    def start_server(self):
        #assert hasattr(self.handler, 'start_server'), "handler "
        if hasattr(self.handler, 'start_server'):
            self.handler.start_server()
            

