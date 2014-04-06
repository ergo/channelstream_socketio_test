channelstream
=============
Basic usage::

    YOUR_PYTHON_ENV/bin/pserver channelstream.ini


You can also see simple pyramid/angularjs demo included, open your browser and point it to following url::

    http://127.0.0.1:8000/demo

**To run the demo you will need to have the `requests` package installed in your environment**

Possible config options for the server::

    YOUR_PYTHON_ENV/bin/

example ini file::

    [app:main]
    paste.app_factory = channelstream.wsgi_app:make_app
    admin_secret = admin_secret
    secret = secret
    port = 8000
    allow_posting_from = 127.0.0.1,
                         192.168.1.1

    [server:main]
    use = egg:gevent-socketio#paster
    host = 0.0.0.0
    port = 8000
    resource = socket.io
    transports = websocket, xhr-polling
    policy_server = True
    policy_listener_host = 0.0.0.0
    policy_listener_port = 10843
    heartbeat_interval = 5
    heartbeat_timeout = 60


Data format and endpoints
=========================

/connect
--------------------------

expects a json request in form of::

    { "user": YOUR_USER_NAME,
      "conn_id": CUSTOM_UNIQUE_UID_OF_CONNECTION, # for example uuid.uuid4()
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ]
    }
   
where channels is a list of channels this connection/user should be subscribed to.

/info
--------------------------

expects a json request in form of::

    { 
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ]
    }
   
where channels is a list of channels you want information about.
If channel list is empty server will return full list of all channels and their
information.

/disconnect
--------------------------

expects a json request in form of::

    { "conn_id": CONN_ID}

marks specific connection to be garbage collected

/message
--------------------------

expects a json request in form of::

    {
    "channel": "CHAN_NAME", #optional
    "pm_users": [USER_NAME1,USER_NAME2], #optional
    "user": "NAME_OF_POSTER",
    "message": MSG_PAYLOAD
    }

When just channel is present message is public to all connections subscribed 
to the channel. When channel & pm_users is a private message is sent 
to connections subscribed to this specific channel. 
If only pm_users is present a private message is sent to all connections that are
owned by pm_users.  

/subscribe
----------------------------

expects a json request in form of::

    { "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ], "conn_id": "CONNECTION_ID"}


/user_status
----------------------------

expects a json request in form of::

    { "user": USER_NAME, "status":STATUS_ID_INT}


Example socket.io client usage
----------------------

Responses to client are in form of **list** containing **objects**:

examples:

            socket = io.connect('http://127.0.0.1:8000/stream?username=' + data.username + '&sig=' + encodeURIComponent(data.sig));
            socket.on('connecting', function () {
                console.log('connecting');
            });
            socket.on('connect', function () {
                console.log('connected');
                socket.emit('join', ['pub_chan', 'pub_chan2'])
            });
            socket.on('disconnect', function () {
                console.log('disconnected');
            });
            socket.on('user_connect', function (message, callback) {
                console.log('user_connect', message);
            });
            socket.on('message', function(messages){
                console.log('messages', messages);
            };
            socket.on('join', function (channels) {
                console.log('join', channels);
            });
            socket.on('leave', function (channels) {
                console.log('leave', channels);
            });

Installation and Setup
======================

Obtain source from github and do::

    python setup.py develop