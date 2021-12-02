# -*- coding: utf-8 -*-
"""
Created on Thu Dec 2 13:00:00 2021

@author: Prasanna.Bhat
"""

import websocket
import six
import datetime
import time
import json
import threading
import ssl


class SmartWebSocketOrder(object):
    ROOT_URI = 'wss://smartapisocket.angelbroking.com/websocket'
    HB_INTERVAL = 30
    HB_THREAD_FLAG = False
    WS_RECONNECT_FLAG = False
    jwttoken = None
    client_code = None
    apiKey = None
    ws = None

    def __init__(self, JWT_TOKEN, CLIENT_CODE, API_KEY):
        self.root = self.ROOT_URI
        self.jwttoken = JWT_TOKEN
        self.client_code = CLIENT_CODE
        self.apiKey = API_KEY
        if self.client_code == None or self.jwttoken == None or self.apiKey == None:
            return "client_code or jwttoken or api key is missing"

    def _subscribe_on_open(self):
        # Set up heart beat thread
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            # More statements comes here
            if self.HB_THREAD_FLAG:
                break
            print(datetime.datetime.now().__str__() +
                  ' : Start task in the background')

            self.heartBeat()

            time.sleep(self.HB_INTERVAL)

    def subscribe(self):
        # TODO : Print messages based on verbose switch
        print("subscribing...")
        try:
            request = {
                "actiontype": "subscribe",
                "feedtype": "order_feed",
                "jwttoken": self.jwttoken,
                "clientcode": self.client_code,
                "apikey": self.apiKey
            }
            self.ws.send(
                six.b(json.dumps(request))
            )
            return True
        except Exception as e:
            self._close(
                reason="Error while request sending: {}".format(str(e)))
            raise

    def resubscribe(self):
        self.subscribe()

    def heartBeat(self):
        try:
            request = {
                "actiontype": "heartbeat",
                "feedtype": "order_feed",
                "jwttoken": self.jwttoken,
                "clientcode": self.client_code,
                "apikey": self.apiKey
            }
            # request = {"task": "hb", "channel": "", "token": self.feed_token, "user": self.client_code,
            #            "acctid": self.client_code}
            print(request)
            self.ws.send(
                six.b(json.dumps(request))
            )

        except:
            print("HeartBeat Sending Failed")
            # time.sleep(60)

    def _parse_text_message(self, message):
        """Parse text message."""

        data = None

        try:
            data = json.loads(message)
        except ValueError:
            return

        # return data
        if data:
            self._on_message(self.ws, data)

    def connect(self):
        print("Connecting...")
        # websocket.enableTrace(True)
        headers = {
            'jwttoken': self.jwttoken,
            'clientcode': self.client_code,
            'apikey': self.apiKey
        }
        ROOT_URL = f"{self.ROOT_URI}?jwttoken={self.jwttoken}&&clientcode={self.client_code}&&apikey={self.apiKey}"
        print(ROOT_URL)
        self.ws = websocket.WebSocketApp(ROOT_URL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error
                                         )

        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def __on_message(self, ws, message):
        print("Message arrived........")
        print(message)
        self._parse_text_message(message)

    def __on_open(self, ws):
        print("__on_open################")
        self.HB_THREAD_FLAG = False
        self._subscribe_on_open()
        if self.WS_RECONNECT_FLAG:
            self.WS_RECONNECT_FLAG = False
            self.resubscribe()
        else:
            self._on_open(ws)

    def __on_close(self, ws):
        self.HB_THREAD_FLAG = True
        print("__on_close################")
        self._on_close(ws)

    def __on_error(self, ws, error):

        if ("timed" in str(error)) or ("Connection is already closed" in str(error)) or ("Connection to remote host was lost" in str(error)):

            self.WS_RECONNECT_FLAG = True
            self.HB_THREAD_FLAG = True

            if (ws is not None):
                ws.close()
                ws.on_message = None
                ws.on_open = None
                ws.close = None
                # print (' deleting ws')
                del ws

            self.connect()
        else:
            print('Error info: %s' % (error))
            self._on_error(ws, error)

    def _on_message(self, ws, message):
        pass

    def _on_open(self, ws):
        pass

    def _on_close(self, ws):
        pass

    def _on_error(self, ws, error):
        pass
