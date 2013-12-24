###############################################################################
##
##  Copyright (C) 2013 Tavendo GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
                                       WebSocketClientFactory


import asyncio


class MyClientProtocol(WebSocketClientProtocol):

   def onConnect(self, response):
      print("Server connected: {}".format(response.peer))

   @asyncio.coroutine
   def slow_sqrt_coroutine(self, x):
      yield from asyncio.sleep(1)
      if x >= 0:
         return math.sqrt(x)
      else:
         raise Exception("negative number")

   def onOpen(self):
      print("WebSocket connection open.")
      value = yield from self.slow_sqrt_coroutine(2)
      #value = 2.1
      msg = "result = {}".format(value)
      self.sendMessage(msg.encode('utf8'))

   def onOpen2(self):
      print("WebSocket connection open.")

      def hello():
         self.sendMessage(u"Hello, world!".encode('utf8'))
         self.sendMessage(b"\x00\x01\x03\x04", binary = True)
         self.factory.loop.call_later(1, hello)

      ## start sending messages every second ..
      hello()

   def onMessage(self, payload, isBinary):
      if isBinary:
         print("Binary message received: {} bytes".format(len(payload)))
      else:
         print("Text message received: {}".format(payload.decode('utf8')))

   def onClose(self, wasClean, code, reason):
      print("WebSocket connection closed: {}".format(reason))



if __name__ == '__main__':

   import asyncio

   factory = WebSocketClientFactory("ws://localhost:9000", debug = True)
   factory.protocol = MyClientProtocol

   loop = asyncio.get_event_loop()
   coro = loop.create_connection(factory, '127.0.0.1', 9000)
   loop.run_until_complete(coro)
   loop.run_forever()
   loop.close()