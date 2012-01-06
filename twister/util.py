#-*- coding:utf-8 -*-
# Twister
# Copyright 2011-2012 Jun Kimura
# See LICENSE for details.

from tweepy.auth import OAuthHandler
import os, sys, re, logging

logger = None
def set_logger():
    global logger
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s (%(threadName)-2s) %(message)s',
                    #filename='/tmp/twister.log',
                    #filemode='w'
                    )
    logger = logging.getLogger("server")

'''
@summary: 実行環境を確認します
'''
def check_environ():
    require_python_version = 260
    ver = 0
    for i, v in enumerate(reversed(sys.version_info[0:3])):
        ver += v * (10 ** i)
    if ver <= require_python_version or ver >= 300:
        raise Exception("This module need to use Python >=2.6.x")

'''
@todo: refactoring
@summary: oauth認証を行います
'''
def get_oauth(consumer_key, consumer_secret, access_token, access_secret):
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    return auth
    
'''
@summary: 第二引数に指定したメソッドをデーモンとして実行します
@param pidfile: file path
@param daemonfunc: function
'''
def daemonize(pidfile, daemonfunc, *args, **kw):
    try:
        pid = os.fork()
        if (pid > 0):
            sys.exit(0)
    except OSError:
        print >>sys.stderr, 'daemonize: fork #1 failed.'
        sys.exit(1)
 
    try:
        os.setsid()
    except:
        print >>sys.stderr, 'daemonize: setsid failed.'
        sys.exit(1)
 
    try:
        pid = os.fork()
        if (pid > 0):
            sys.exit(0)
    except OSError:
        print >>sys.stderr, 'daemonize: fork #2 failed.'
        sys.exit(1)
 
    try:
        f = file(pidfile, 'w')
        f.write('%d' % os.getpid())
        f.close()
    except IOError:
        print >>sys.stderr, 'daemonize: failed to write pid to %s' % pidfile
        sys.exit(1)
 
    # Now I'm a daemon.
    try:
        os.chdir('/')        
        os.umask(0)
        sys.stdin = open('/dev/null', 'r')
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
    except:
        pass
 
    daemonfunc(*args, **kw)
    

'''
@summary: 指定したタグのリストにマッチするようにマッチする
@param tags: list(str or unicode)
'''
def create_re_hashtag(tags):
    return re.compile(u"(?P<hashtag>%s)" % u"|".join(map(guess_decode, tags)))

'''
@summary: 指定したテキストのエンコードを推測して、デコードして返します
@param text: str
'''
def guess_decode(text):
    if type(text) == unicode:
        return text
    for dec in ['utf-8','shift-jis','euc-jp']:
        try:
            return text.decode(dec)
        except:
            pass
    return dec

def to_utf8(text):
    return guess_decode(text).encode('utf8')

def setup():
    set_logger()
    
setup()

    