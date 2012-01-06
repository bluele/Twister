#-*- coding:utf-8 -*-

from twister import Twister, TwisterListener, EventHandler
    
# callback
def cbone(event, status):
    print "callback one."
    print status.text
def cbtwo(event, status):
    print "callback two"
    print status.text
    
# twitter auth-key
auth_key = {
    'consumer_key' : 'xxxxxxxxxxxxxx',
    'consumer_secret' : 'xxxxxxxxxxxxxx',
    'access_token' : 'xxxxxxxxxxxxxx',
    'access_secret' : 'xxxxxxxxxxxxxx'
}


def main():
    twist = Twister(
                    auth_key=auth_key,
                    listener=TwisterListener(
                                handler_class=EventHandler,
                                thread_count=3,
                            ),
                    )
      
    twist.handler.add_event((
        {'name':'callback_one',
        'callback' : cbone,
        'allowuser' : ('User1', 'User2'),
        'hashtag' : ('#you',),
        'priority' : 2,
        },
        {'name':'callback_two',
        'callback' : cbtwo,
        'allowuser' : ('User3',),
        'hashtag' : ('#python','#happy'),
        'priority' : 1,
        },) 
        )
    
    twist.userstream(
                    count=None, 
                    async=False, 
                    secure=True, 
                    daemon=True,) 
    

if __name__ == "__main__":
    main()
