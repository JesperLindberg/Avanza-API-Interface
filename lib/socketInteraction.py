import json, websocket, threading, requests, logging, os.path, sys, mintotp
try:
    from credentials import credentials
except:
    print("No credentials class found, credentials should be supplied by arugemtns when executing this file!")
from const import *
from datetime import datetime

"""
TODO:
Implement logging to file.
"""

class socketInteraction:

    def __init__(self, *args):
        self._args = args[0]
        try:
            self._credentials = credentials()
        except:
            pass
        self._socket = None
        self._authenticated = False
        self._authenticationSession = None
        self._authenticationTimeoutMinutes = public.MAX_INACTIVE_MINUTES
        self._pushSubscriptionId = None
        self._reauthentication = None
        self._customerId = None
        self._securityToken = None

        self._backOffTimestamps = {}
        self._socketHandshakeTimer = None
        self._socketSubscriptions = ['/quotes/19002'] #When connected, we sub to these
        self._socketMonitor = None
        self._socketLastMetaConnect = 0
        self._adviceTimeout = 30000
        self._socketConnected = False
        self._socketMessageCount = 1
        self._socketClientId = None

        self._pathToSaveData = 'data/'

        self._header = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }
        
        self._socket = websocket.WebSocketApp(paths.SOCKET_URL,
                                            on_message = self._on_message,
                                            on_error = self._on_error,
                                            on_close = self._on_close,
                                            on_open = self._on_open)

        self._create_data_folder()

        self._socket.run_forever()
        #self.socketThread = threading.Thread(name = str(self)+"_socketThread",
        #                                target = self._socket.run_forever()
        #                                )

    def _reauth(self):
        self._auth()
        self._authSocket(True)
        
    def _create_data_folder(self):
        if not os.path.exists(self._pathToSaveData):
            os.mkdir(self._pathToSaveData)

    def connected(self):
        return self._authenticated

    def _on_open(self):
        self._auth()
        if self._authenticated:
            self._authSocket(True)

    def _on_message(self, msg):
        msg = json.loads(msg)[0]
        print(str(msg) + " " + str(datetime.now().strftime("%H:%M:%S")))
        channel = msg.get('channel')
        if '/quotes/' in channel:
            quote = msg.get('data')
            quote['timeReceived'] = datetime.now().strftime("%H:%M:%S")

            file_ = self._pathToSaveData +\
                    str(datetime.date(datetime.now())) +\
                    '-' + 'quotes' + '-' +\
                    channel.split('/')[-1]

            try:
                txt = open(file_, 'a')
                txt.write(str(quote) + '\n')
                txt.close()
            except:
                self._create_data_folder()
                txt = open(file_, 'a')
                txt.write(str(quote) + '\n')
                txt.close()
            
        elif channel == '/meta/handshake':
            if msg.get('successful'):
                self._socketClientId = msg.get('clientId')
                data = {
                    'advice': {'timeout': 0},
                    'channel': '/meta/connect',
                    'clientId': self._socketClientId,
                    'connectionType': 'websocket',
                    'id': self._socketMessageCount,
                }
                self._socket_send(data)
            elif msg.get('advice').get('reconnect') == 'retry' and self._authenticated:
                self._authSocket(True)
            else:
                self._socketClientId = None
                self._socketConnected = False
                self._pushSubscriptionId = None
                # Schedule re-auth
                print('Error: Repsone from websocket with handshake failed. \n Response: ' + msg)
        elif channel == '/meta/connect':
            if msg.get('successful') and (\
                    (not msg.get('advice') or \
                        (msg.get('advice').get('reconnect') != 'none' and \
                        (not msg.get('advice').get('interval') < 0))
                    )
                ):
                self._socketLastMetaConnect = datetime.now()
                data = {
                    'channel': '/meta/connect',
                    'clientId': self._socketClientId,
                    'connectionType': 'websocket',
                    'id': self._socketMessageCount
                }
                self._socket_send(data)
                if not self._socketConnected:
                    self._socketConnected = True
                    for substring in self._socketSubscriptions:
                        self._subscribe(substring)
            elif self._socketClientId:
                self._authSocket(True)
        elif channel == '/meta/subscribe':
            self._socketSubscriptions[msg.get('subscription')] = self._socketClientId
        else:
            print("Websocket message debug-info: \n")
            print(msg)

    def _on_error(self, error):
        # Also log this error!
        print('ERROR: \n')
        print(error)
#        self.__init__()
    
    def _on_close(self):
        # Set class variables to NA/0/False
        print("WARNING: FUNCTION NOT IMPLEMENTED!")
        print(self._socket._get_close_args())
        print(self._socket.header())
#        self.__init__()
        
    def _socket_send(self, data):
        data = json.dumps([data])
        print(str(data) + " " + str(datetime.now().strftime("%H:%M:%S")))
        self._socket.send(data)
        self._socketMessageCount += 1

    def _subscribe(self, subscriptionString):
        if(self._socketConnected):
            self._socket_send({
                'channel': '/meta/subscribe',
                'clientId': self._socketClientId,
                'id': self._socketMessageCount,
                'subscription': subscriptionString
            })
    
    def _auth(self):
        if len(self._args) > 1:
            print("we got args!")
            payload = {
                'username':self._args[1],
                'password':self._args[2]
            }

        else:
            print("No args!")
            payload = self._credentials.getAuth()
        

        # Expected return from getAuth():
        # data = {
        #    "username":self.username,
        #    "password":self.password
        #}
        #return data

        payload['maxInactiveMinutes'] = self._authenticationTimeoutMinutes
        payload = json.dumps(payload)
        header = self._header
        header.update({'Content-Length' : str(len(payload))})
        response = requests.request('POST', paths.AUTHENTICATION_PATH, headers=header, data=payload)
        # Expected return: {'twoFactorLogin':{'transactionId':'someID','method':'TOTP'}}

        if(response):
            response = json.loads(response.text)
            transactionID = response.get('twoFactorLogin').get('transactionId')
            if(response.get('twoFactorLogin').get('method') == 'TOTP'):
                # Time to provide TOTP for 2FA
                if len(self._args) > 1:
                    payload = {
                    'method': 'TOTP',
                    'totpCode': str(mintotp.totp(self._args[3]))
                }
                else:
                    payload = {
                        'method': 'TOTP',
                        'totpCode': str(self._credentials.getTOTP())
                        # Expected return from getTOTP():
                        # import mintotp
                        # return mintotp.totp(self.totp)
                        # Where self.totp is the totp code given by Avanza.
                    }
                payload = json.dumps(payload)
                header = self._header
                header.update({'Content-Length': str(len(payload)), 'Cookie': 'AZAMFATRANSACTION='+transactionID})
                response = requests.request('POST', paths.TOTP_PATH, headers=header, data=payload)

                # Expected return: {"authenticationSession":"sessionID",
                #                   "pushSubscriptionId":"123d",
                #                   "customerId":"123",
                #                   "registrationComplete":true}

                if(response):
                    self._authenticated         = True
                    self._securityToken         = response.headers.get('X-SecurityToken')
                    self._authenticationSession = json.loads(response.text).get('authenticationSession')
                    self._pushSubscriptionId    = json.loads(response.text).get('pushSubscriptionId')
                    self._customerId            = json.loads(response.text).get('customerId')
                    # Schedule reauth after timout limit minus one minute times 60 to get it in seconds.
                    threading.Timer((self._authenticationTimeoutMinutes - 1 )*60, self._reauth).start()
                    print("Authenticated!")

                else:
                    self._authenticated = False
                    print("Error: Failed to provied a valied TOTP!")
                    print(str(payload))
                    print(str(header))
                    print(response.text)
#                    self._on_open()
            else:
                self._authenticated = False
                print('Error: 2FA not needed but should be required for Avanza. Report this issue to github.')
        else:
            self._authenticated = False
            print('No user matching the account information')
            print('Response from server: ' + response.text)
    
    def _authSocket(self, handshake = False):
        if (not self._socketClientId  or handshake):
            self._socketClientId = None
            self._socketConnected = False
            if (self._pushSubscriptionId):
                data = {
                    'advice': {
                        'timeout': '60000',
                        'interval': '0'
                    },
                    'channel': '/meta/handshake',
                    'ext': {'subscriptionId': self._pushSubscriptionId},
                    'id': self._socketMessageCount,
                    'minimumVersion': '1.0',
                    'supportedConnectionTypes': ['websocket', 'long-polling', 'callback-polling'],
                    'version': '1.0'
                }
                self._socket_send(data)
        elif self._socketClientId != None:
            data = {
                'channel': '/meta/connect',
                'clientId': self._socketClientId,
                'connectionType': 'websocket',
                'id': self._socketMessageCount
            }
            self._socket_send(data)

    def _call(self, method = 'GET', path = '', data = {}):
        header = {
            'X-AuthenticationSession': self._authenticationSession,
            'X-SecurityToken': self._securityToken
            }
        payload = json.dumps(data)
        response = requests.request(method, path, headers=header, data=payload)
        return response
    
    def getInspirationLists(self):
        response = self._call('GET', paths.INSPIRATION_LIST_PATH.replace('{0}', ''))
        if response:
            print(response.text)

    def getWatchlists(self):
        response = self._call('GET', paths.WATCHLISTS_PATH)
        if response:
            print(response.text)

socket = socketInteraction(sys.argv)
