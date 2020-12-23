import json
import websocket
import threading
from credentials import credentials
from const import *
import requests
import logging

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
        self._socketSubscriptions = {}
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

        self.socket = websocket.WebSocketApp(paths.SOCKET_URL,
                                            on_message = on_message,
                                            on_error = on_error,
                                            on_close = on_close,
                                            on_open = on_open)

        socketThread = threading.Thread(name = "socketThread",
                                        target = self.socket.run_forever()
                                        ).start()
        

    def on_open(self):
        auth()

    def on_message(self, msg):
        print(msg)

    def on_error(self, error):
        # Also log this error!
        print(error)
    
    def on_close(self):
        # Set class variables to NA/0/False
        print("WARNING: FUNCTION NOT IMPLEMENTED!")
    
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
            print('User credentials OK')
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

                print(json.loads(response.text).get('pushSubscriptionId'))
                if(response):
                    self._authenticated         = True
                    self._securityToken         = response.headers.get('X-SecurityToken')
                    self._authenticationSession = json.loads(response.text).get('authenticationSession')
                    self._pushSubscriptionId    = json.loads(response.text).get('pushSubscriptionId')
                    self._customerId            = json.loads(response.text).get('customerId')
                    print("Authenticated!")

                    """TODO:
                    Schedule re-auth!
                    """

                else:
                    print("Error: Failed to provied a valied TOTP!")
            else:
                print('Error: 2FA not needed but should be required for Avanza. Report this issue to github.')
        else:
            print('No use matching the account information')
            print('Response from server: ' + response.text)
    
test = socketInteraction()
test.auth()
