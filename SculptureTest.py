from SculptureController import SculptureController

import trollius as asyncio

from pyndn import Name, Data, Interest, ThreadsafeFace, Exclude
from pyndn.security import KeyChain
from ConfigParser import RawConfigParser
import traceback

from random import uniform

import time
import json

class FakePublisher(object):
    # this assumes a bus comes every 10mins = 600s
    BUS_INTERVAL = 600
    UPDATE_INTERVAL = 1.5
    def __init__(self, prefix):
        self.prefix = Name(prefix)

    def start(self):
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, '')
        self.keyChain = KeyChain()
        self.lastQueryTime = time.time()
        self.busETA = self.BUS_INTERVAL
        self.face.setCommandSigningInfo(self.keyChain,
            self.keyChain.getDefaultCertificateName())
        self.face.registerPrefix(self.prefix, self.onInterest, self.onFailure)

        # run_forever is not called because it would hang and prevent 
        # SculptureController from running

    def onFailure(self, prefix):
        print 'Registration failed for {}'.format(self.prefix.toUri())
         # try again, without bound
        self.face.registerPrefix(self.prefix, self.onInterest, self.onFailure)
        
    def onInterest(self, prefix, interest, transport, prefixId):
        # no checking of interest name
        # this is only using single ETAs, no other data fields
        # change this to pull from some data source if you wish
        now = time.time()
        dt = now - self.lastQueryTime
        if dt >= self.UPDATE_INTERVAL:
            # make the bus 5s later to 10s sooner
            self.busETA = self.busETA - dt + uniform(-5.0, 10.0)
            if self.busETA < 0:
                self.busETA = self.BUS_INTERVAL

	fakeData = [{'eta':self.busETA}]
        d = Data(Name(interest.getName()).appendTimestamp(int(now)))
        d.setContent(json.dumps(fakeData))

        transport.send(d.wireEncode().buf())
        
testPrefix = '/testData'
if __name__ == '__main__':
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'config.cfg'

    config = RawConfigParser()
    config.read(filename)
    # change the bus data prefix to our test prefix
    config.set('busData', 'prefix', testPrefix)

    s = SculptureController(config)
    f = FakePublisher(Name(testPrefix))
    try:
        f.start() 
        s.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_stack()
        print e
    finally:
        s.stop()
        f.face.shutdown()
