import json
import websocket
import threading
from credentials import credentials
from const import *
import requests
import logging
from datetime import datetime

"""
TODO:
Implement logging to file.
"""

class socketInteraction:

    def __init__(self):
        self._credentials = credentials()
        self._socket = None
        self._authenticated = False
        self._authenticationSession = None
        self._authenticationTimeout = public.MAX_INACTIVE_MINUTES
        self._pushSubscriptionId = None
        self._reauthentication = None
        self._customerId = None
        self._securityToken = None

        self._backOffTimestamps = {}
        self._socketHandshakeTimer = None
        self._socketSubscriptions = ['/Avanza.QUOTES/19002'] #When connected, we sub to these
        self._socketMonitor = None
        self._socketLastMetaConnect = 0
        self._adviceTimeout = 30000
        self._socketConnected = False
        self._socketMessageCount = 1
        self._socketClientId = None

        self._header = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }

        self._socket = websocket.WebSocketApp(paths.SOCKET_URL,
                                            on_message = self.on_message,
                                            on_error = self.on_error,
                                            on_close = self.on_close,
                                            on_open = self.on_open)

        socketThread = threading.Thread(name = "socketThread",
                                        target = self._socket.run_forever()
                                        ).start()
        

    def on_open(self):
        self.auth()
        if self._authenticated:
            self.authSocket()

    def on_message(self, msg):
        print('Message: ')
        msg = json.loads(msg)[0]
        channel = msg.get('channel')
        if channel == '/meta/handshake':
            if msg.get('successful'):
                self._socketClientId = msg.get('clientId')
                data = {
                    'advice': {'timeout': 0},
                    'channel': '/meta/connect',
                    'clientId': self._socketClientId,
                    'connectionType': 'websocket',
                    'id': self._socketMessageCount,
                }
                self.socket_send(data)
            elif msg.get('advice').get('reconnect') == 'retry' and self._authenticated:
                self.authSocket(True)
            else:
                self._socketClientId = None
                self._socketConnected = False
                self._pushSubscriptionId = None
                # Schedule re-auth
                print('Error: Repsone from websocket with handshake failed. \n Response: ' + msg)
        if channel == '/meta/connect':
            if msg.get('successful') and \
               (not msg.get('advice') or \
               (msg.get('advice').get('reconnect') != 'none' and not msg.get('advice').get('interval') < 0)):
                self._socketLastMetaConnect = datetime.now()
                data = {
                    'channel': '/meta/connect',
                    'clientId': self._socketClientId,
                    'connectionType': 'websocket',
                    'id': self._socketMessageCount
                }
                self.socket_send(data)
                if not self._socketConnected:
                    self._socketConnected = True
                    for substring in self._socketSubscriptions:
                        self.subscribe(substring)
                        self._socketSubscriptions.remove(substring)
                elif self._socketClientId:
                    self.authSocket(True)
        print(msg)




    def on_error(self, error):
        # Also log this error!
        print(error)
    
    def on_close(self):
        # Set class variables to NA/0/False
        print("WARNING: FUNCTION NOT IMPLEMENTED!")
        print(self._socket._get_close_args())
        print(self._socket.header())

    def socket_send(self, data):
        data = json.dumps([data])
        print(data)
        self._socket.send(data)
        self._socketMessageCount += 1

    def subscribe(self, subscriptionString):
        if(self._socketConnected):
            self.socket_send({
                'channel': '/meta/subscribe',
                'clientId': self._socketClientId,
                'id': self._socketMessageCount,
                'subscription': subscriptionString
            })
    
    def auth(self):
        payload = self._credentials.getAuth()

        # Expected return from getAuth():
        # data = {
        #    "username":self.username,
        #    "password":self.password
        #}
        #return data

        payload['maxInactiveMinutes'] = self._authenticationTimeout
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
                    print("Authenticated!")

                    """
                    Schedule re-auth!
                    """

                else:
                    self._authenticated = False
                    print("Error: Failed to provied a valied TOTP!")
                    print(response.text)
            else:
                self._authenticated = False
                print('Error: 2FA not needed but should be required for Avanza. Report this issue to github.')
        else:
            self._authenticated = False
            print('No user matching the account information')
            print('Response from server: ' + response.text)
    
    def authSocket(self, *args):
        # args[0] If handshake is needed
        if (not self._socketClientId  or args[0]):
            self._socketClientId = None
            self._socketConnected = False
            if (self._pushSubscriptionId):
                # Clear schedule for handshake and set new schedule
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
                self.socket_send(data)
        elif self._socketClientId:
            data = {
                'channel': '/meta/connect',
                'clientId': self._socketClientId,
                'connectionType': 'websocket',
                'id': self._socketMessageCount
            }
            self.socket_send(data)
    

test = socketInteraction()
#test.auth()
#test.authSocket()