#-*- coding:utf-8 -*-
# Twister
# Copyright 2011-2012 Jun Kimura
# See LICENSE for details.

from tweepy.streaming import StreamListener, Stream, timeout, httplib, sleep
from tweepy.error import TweepError
from twister.error import NoResponse
from twister.util import logger
from _ssl import SSLError
import threading, Queue, sys, socket, urllib

STREAM_VERSION = 1

class TwisterStream(Stream):

    def __init__(self, *args, **kw):
        self.http_retry = kw.get('http_retry', 3)
        Stream.__init__(self, *args, **kw)
        
    '''
    @summary: streaming serverの起動メソッド
    '''
    def _run(self):
        # Authenticate
        url = "%s://%s%s" % (self.scheme, self.host, self.url)

        # Connect and process the stream
        error_counter = 0
        conn = None
        exception = None
        
        logger.debug(u"run streaming server.")
        while self.running:
            # quit if error count greater than retry count
            if self.retry_count is not None and error_counter > self.retry_count:
                break
            try:
                if self.scheme == "http":
                    conn = httplib.HTTPConnection(self.host)
                else:
                    conn = httplib.HTTPSConnection(self.host)
                self.auth.apply_auth(url, 'POST', self.headers, self.parameters)
                conn.connect()
                conn.sock.settimeout(self.timeout)
                conn.request('POST', self.url, self.body, headers=self.headers)
                logger.debug(u"wait response.")
                resp = conn.getresponse()
                logger.debug(u"connect response: %s" % str(resp))
                if resp.status != 200:
                    if self.listener.on_error(resp.status) is False:
                        break
                    error_counter += 1
                    logger.error("response status: error(%s)", (str(resp.status),))
                    sleep(self.retry_time)
                else:
                    error_counter = 0
                    logger.info("response status: ok(%s)", (str(resp.status),))
                    self._read_loop(resp)
                    
            except socket.error, err:
                self.listener.on_socket_error(err)
                    
            except socket.gaierror, err:
                self.listener.on_socket_error(err)
                    
            except NoResponse, err:
                self.listener.on_noresponse(err)
                
            except timeout:
                logger.info("response status: timeout")
                if self.listener.on_timeout() == False:
                    break
                if self.running is False:
                    break
                conn.close()
                sleep(self.snooze_time)
                
            except Exception, exception:
                if self.listener.on_fatal_error(exception):
                    continue
                raise
                # any other exception is fatal, so kill loop
                #break
                
        logger.error("(%s):%s" % ("_run", "false"))

        # cleanup
        self.running = False
        if conn:
            conn.close()

        # need to catch exception
        if exception:
            logger.error("(%s):%s" % ("_run", str(exception)))
            raise
    
    '''
    @todo:
    @summary: read HTTPResponse
    @param resp: HTTPResponse
    '''
    def _read_loop(self, resp):
        logger.debug("_read_loop init")
        # retry limit for http connecting
        http_count = 0
        while self.running:
            if resp.isclosed():
                break
            logger.debug("_readloop start(%s)" % str(resp.status))
            # read length
            data = ''
            while True:
                try:
                    c = resp.read(1)
                    if c == '\n':
                        http_count = 0
                        break
                    data += c
                except SSLError, exception:
                    logger.info("(%s retry:%d):%s" % ("_read_loop", http_count, str(exception)))
                    http_count += 1
                    if http_count > self.http_retry:
                        logger.error("over retry max")
                        raise NoResponse("break loop")
                    
            data = data.strip()

            # read data and pass into listener
            if self.listener.on_data(data) is False:
                self.running = False
    
    '''
    @summary: streaming thread.
    @param async: bool
    @param daemon: bool
    '''
    def _start(self, async, daemon=False):
        self.running = True
        try:
            if async:
                th = threading.Thread(target=self._run)
                if daemon:
                    th.setDaemon(True)
                th.start()
            else:
                self._run()
        except Exception, exception:
            raise

    '''@param daemon: bool'''
    def userstream(self, count=None, async=False, secure=True, daemon=False):
        if self.running:
            raise TweepError('Stream object already connected!')
        self.url = '/2/user.json'
        self.host='userstream.twitter.com'
        if count:
            self.url += '&count=%s' % count
        self._start(async, daemon)
        
    '''@param daemon: bool'''
    def firehose(self, count=None, async=False, daemon=False):
        self.parameters = {'delimited': 'length'}
        if self.running:
            raise TweepError('Stream object already connected!')
        self.url = '/%i/statuses/firehose.json?delimited=length' % STREAM_VERSION
        if count:
            self.url += '&count=%s' % count
        self._start(async, daemon)

    '''@param daemon: bool'''
    def retweet(self, async=False, daemon=False):
        self.parameters = {'delimited': 'length'}
        if self.running:
            raise TweepError('Stream object already connected!')
        self.url = '/%i/statuses/retweet.json?delimited=length' % STREAM_VERSION
        self._start(async, daemon)

    '''@param daemon: bool'''
    def sample(self, count=None, async=False, daemon=False):
        self.parameters = {'delimited': 'length'}
        if self.running:
            raise TweepError('Stream object already connected!')
        self.url = '/%i/statuses/sample.json?delimited=length' % STREAM_VERSION
        if count:
            self.url += '&count=%s' % count
        self._start(async, daemon)

    '''@param daemon: bool'''
    def filter(self, follow=None, track=None, async=False, locations=None, count = None, daemon=False):
        self.parameters = {}
        self.headers['Content-type'] = "application/x-www-form-urlencoded"
        if self.running:
            raise TweepError('Stream object already connected!')
        self.url = '/%i/statuses/filter.json?delimited=length' % STREAM_VERSION
        if follow:
            self.parameters['follow'] = ','.join(map(str, follow))
        if track:
            self.parameters['track'] = ','.join(map(str, track))
        if locations and len(locations) > 0:
            assert len(locations) % 4 == 0
            self.parameters['locations'] = ','.join(['%.2f' % l for l in locations])
        if count:
            self.parameters['count'] = count
        self.body = urllib.urlencode(self.parameters)
        self.parameters['delimited'] = 'length'
        self._start(async, daemon=False)
        
    