#-*- coding:utf-8 -*-
# Twister
# Copyright 2011-2012 Jun Kimura

from twister.util import create_re_hashtag, guess_decode, to_utf8, logger
from twister.error import NotFoundEvent, TwisterError

from functools import wraps
from collections import deque
import threading, Queue, SocketServer, sys


'''
@summary: syncronize method
@note: decorator
'''
def syncronized(f):
    @wraps(f)
    def _syncronized(self, *args, **kw):
        with self.LOCK:
            return f(self, *args, **kw)
    return _syncronized


class AbstractHandler(object):

    def call(self):
        raise TwisterError("Handler need to define 'call' method.")
    
        
class EventHandler(AbstractHandler):
    
    __error__ = 'error'
    # dataの必須値。順にイベント名、コールバック、ユーザー名
    _param = ('name', 'callback', 'allowuser')
            
    def __init__(self, **opts):
        AbstractHandler.__init__(self)
        self.thread_count = opts.get('thread_count', 3)
        self.events = []
        self.LOCK = threading.RLock()
        self.processed = []
        self.priority = 0
        self._create_thread(self.thread_count)        
         
    '''
    @summary: create threads for callback
    @param thread_count: int
    '''   
    def _create_thread(self, thread_count):
        self.evqueue = Queue.Queue()
        self.th_pool = []
        for x in xrange(thread_count):
            th = threading.Thread(target=self.worker)
            th.setDaemon(True)
            self.th_pool.append(th)
            th.start()
        
    '''
    @summary: parse event object
    @param data: list or dict
    @return: bool
    '''
    def parse(self, data):
        # not transaction
        if isinstance(data, list) or isinstance(data, tuple):
            for ev in data:
                if not isinstance(ev, dict):
                    raise TypeError("Each event data must be type 'dict'.")
                self._parse_structure(ev)
        elif isinstance(data, dict):
            self._parse_structure(data)
        else:
            raise TypeError("Each event data must be type 'dict'.")
       
        return True
    '''
    @summary: 第一引数に渡されたイベントの構造を確認します
    @param ev: dict
    '''         
    def _parse_structure(self, event):
        try:
            for k in self._param:
                event[k]
        except:
            raise
        
        if not isinstance(event['allowuser'], list) and not isinstance(event['allowuser'], tuple):
            event['allowuser'] = [event['allowuser']]
        
        if event.has_key('priority'):
            if self.priority < event['priority']:
                self.priority = event['priority']
        else:
            self.priority += 1
            event['priority'] = self.priority
            
        if event.has_key('hashtag'):
            if isinstance(event['hashtag'], list) or isinstance(event['hashtag'], tuple):
                event['hashtag'] = create_re_hashtag(event['hashtag'])
            else:
                event['hashtag'] = create_re_hashtag([event['hashtag']])
            
        # insert sort?
        self.events.append(event)
        self.events.sort(key=lambda x:int(x['priority']), reverse=True)
    
    '''
    @summary: 取得したイベントを振り分けます
    '''
    def dispatch(self, status):
        for ev in self.events:
            if status.author.screen_name in ev['allowuser']:
                status.text = guess_decode(status.text)
                if not ev.has_key('hashtag') or ev['hashtag'].search(status.text):
                    logger.info("callback by %s" % (status.author.screen_name,))
                    try:
                        ev["callback"](self, status)
                        return
                    except Exception:
                        raise
        
    '''
    @summary: 処理済みのイベントならTrueを返します。
    @param status: Tweet
    @return bool
    '''
    def is_processed(self, status):
        evstr = "%s::%s" % (status.author.screen_name, str(status.created_at))
        if evstr in self.processed:
            return False
        else:
            self.processed.append(evstr)
            return True
        
    @syncronized
    def call(self, status):
        if self.is_processed(status):
            logger.debug("put %s" % (status.text,))
            self.evqueue.put(status, block=True, timeout=None)
        
    '''
    @summary: イベント処理を行うワーカースレッド
    '''
    def worker(self):
        while True:
            try:
                logger.debug("wait..")
                status = self.evqueue.get(block=True, timeout=None)
                logger.debug("get by %s" % (status.author.screen_name,))
                self.dispatch(status)
            except TwisterError, err:
                logger.error(err)
            except Exception, err:
                logger.error(err)
                     
                
    '''
    @summary: 第一引数に指定したイベントに第二引数に指定したアカウントを許可ユーザーとして追加します
    @param name: str: event name
    @param user: str or list or tuple: allowed user or users
    @exception: NotFoundEvent: イベント名が見つからない際に発生します
    @exception: TwisterError: Fatal Error.
    '''
    @syncronized
    def add_user(self, name, user):
        try:
            if not (isinstance(user, list) or isinstance(user, tuple)):
                if not isinstance(user, dict):
                    user = [user]
                else:
                    raise TypeError("'user' should specify str or list or tuple.")
            self.events[self.get_event_index(name)] += list(user)
        except NotFoundEvent:
            raise
        except TypeError:
            raise
        except:
            raise TwisterError("(Fatal Error) ev_remove.")
        else:
            logger.debug("Remove event '%s'" % self.events[name]) 
        
    '''
    @summary: 第一引数に指定したイベントから第二引数に指定したアカウントを許可ユーザーから削除します
    @param name: str: event name
    @param user: str or list or tuple: allowed user or users
    @exception: NotFoundEvent: イベント名が見つからない際に発生します
    @exception: TwisterError: Fatal Error.
    '''
    @syncronized
    def remove_user(self, name, user):
        if self.events.has_key(name):
            self.events[name].remove(user)
        else:
            raise Exception("Not Found event '%s'." % name)
        
    @syncronized
    def add_event(self, data):
        try:
            self.parse(data)
        except TypeError, err:
            raise
        except Exception,err:
            raise
        
    '''
    @summary: 第一引数に指定したイベントを削除します
    @exception: NotFoundEvent: イベント名が見つからない際に発生します
    @exception: TwisterError: Fatal Error.
    '''
    @syncronized
    def remove_event(self, name):
        try:
            index = self.get_event_index(name)
            del self.events[index]
        except NotFoundEvent:
            raise
        except:
            raise
        else:
            logger.info("Remove event '%s'" % name) 
        
    '''
    @summary: 第一引数に指定したイベントのリスト中のインデックスを返します
    @exception: NotFoundEvent: イベント名が見つからない際に発生します
    @param name: str: event name
    @return: int
    '''
    @syncronized
    def get_event_index(self, name):
        for i, ev in enumerate(self.events):
            if ev['name'] == name:
                return i
        else:
            raise NotFoundEvent("Not Found event '%s'." % name)
        
    '''
    @summary: イベントの内容を出力します
    '''
    def dump_event(self):
        return self.events
    
    
class RequestHandler(SocketServer.BaseRequestHandler):
    queue_list = {}

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def setup(self):
        pass


    # 接続ごとにハンドラを生成
    def handle(self):
        logger.debug("connect by %s" % str(self.client_address))
        self.queue_list[self.client_address] = Queue.Queue()
        while True:
            try:
                status = self.queue_list[self.client_address].get(block=True, timeout=None)
                self.request.send(to_utf8(status.text))
            except Exception, err:
                # エラー発生で切断
                logger.error(err)
                # can do on finish?
                del self.queue_list[self.client_address]
                break

    def finish(self):
        pass


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
    
'''
@summary: 取得したeventを分散するクラスです
'''    
class DispersionServerHandler(AbstractHandler):
    
    '''
    @todo: allow hostを設定
    '''
    def __init__(self, **opts):
        AbstractHandler.__init__(self)
        self.LOCK = threading.RLock()
        self.queue_list = RequestHandler.queue_list
        self.server = ThreadedTCPServer(
                            (opts.get('host', '127.0.0.1'), opts.get('port', 8080)),
                            RequestHandler,
                            )
        
    ''' @summary: tweet取得時に呼ばれます '''
    @syncronized
    def call(self, status):
        logger.debug("callback")
        logger.debug(status.text)
        self.dispatch(status)
        
    ''' @summary: tweetを接続クライアントに振り分けます '''
    def dispatch(self, status):
        for k, q in self.queue_list.items():
            try:
                q.put(status, block=True, timeout=None)
                logger.debug("put %s" % str(k))
            except Exception, err:
                logger.debug("%s" % err)
                continue
    
    ''' @summary: start server '''          
    def start_server(self):
        logger.debug("start server.")
        self.server.serve_forever()
        
        
        