from lighting.KinetSender import KinetSender
import logging
import time
import sys

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn import Sha256WithRsaSignature
from pyndn.security import KeyChain

from pyndn.encoding import ProtobufTlv
from lighting.light_command_pb2 import LightCommandMessage
from ConfigParser import RawConfigParser

from itertools import cycle, chain

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class LightController():
    shouldSign = False
    COLORS_PER_LIGHT = 3
    STRAND_SIZE = 50
    def __init__(self, nStrands=1, myIP="192.168.1.1", lightIP="192.168.1.50", prefix="/testlight"):
        self.log = logging.getLogger("LightController")
        self.log.setLevel(logging.WARNING)
        sh = logging.StreamHandler()
        sh.setLevel(logging.WARNING)
        self.log.addHandler(sh)
        fh = logging.FileHandler("LightController.log")
        fh.setLevel(logging.DEBUG)
        self.log.addHandler(fh)

        self.numStrands = nStrands
        self.payloadBuffer = [[0]*self.STRAND_SIZE*self.COLORS_PER_LIGHT for n in range(nStrands)]

        self.kinetsender = None
        self.prefix = Name(prefix)

        self.address = myIP
        self.lightAddress = lightIP
        self._isStopped = True


    def start(self, loop, face):
        self.kinetsender = KinetSender(self.address, self.lightAddress, 
            self.numStrands, self.STRAND_SIZE*self.COLORS_PER_LIGHT)
        self.loop = loop
        self.face = face
        self._isStopped = False
        self.face.stopWhen(lambda:self._isStopped)
        self._registerPrefix()

    def _registerPrefix(self):
        self.face.registerPrefix(self.prefix, self.onLightingCommand, self.onRegisterFailed)

    def stop(self):
        self._isStopped = True
        self.kinetsender.stop = True
        self.kinetsender.complete.wait()         
        self.kinetsender = None
        self.face = None

    def signData(self, data):
        if LightController.shouldSign:
            self.keychain.sign(data, self.certificateName)
        else:
            data.setSignature(Sha256WithRsaSignature())

    def onLightingCommand(self, prefix, interest, transport, prefixId):
        # NOTE: mix pattern is currently ignored
        interestName = Name(interest.getName())
        d = Data(interest.getName())
        try:
            commandComponent = interest.getName()[len(prefix)]
            commandParams = interest.getName()[len(prefix)+1]

            lightingCommand = LightCommandMessage()
            ProtobufTlv.decode(lightingCommand, commandParams.getValue())

            # if values are missing and repeat is false, keep previous values
            payloadLen = self.STRAND_SIZE*self.COLORS_PER_LIGHT
            commandInfo = lightingCommand.command
            pattern = chain(*[(c.r, c.g, c.b) for c in commandInfo.pattern.colors])
            if commandInfo.repeat:
                pattern = cycle(pattern)
                newPayload = [pattern.next() for i in range(payloadLen)]
            else:
                pattern = list(pattern)
                patternLen = min(len(pattern), payloadLen)
                newPayload = pattern[:patternLen]+self.payloadBuffer[0][patternLen:]
            
            self.log.debug('New payload:\n\t{}'.format(newPayload))
            self.payloadBuffer[0] = newPayload
            self.sendLightPayload(1)
            d.setContent('ACK')
        except Exception as e:
            print e
            d.setContent("Bad command\n")
        finally:
            d.getMetaInfo().setFinalBlockID(0)
            d.getMetaInfo().setFreshnessPeriod(500)
            #self.signData(d)

        encodedData = d.wireEncode()
        transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        self.log.error("Could not register " + prefix.toUri())
        #self.stop()
        #self.loop.call_soon(self._registerPrefix)

    def sendLightPayload(self, port):
        self.kinetsender.setPayload(port, self.payloadBuffer[port-1])

done = False
if __name__ == '__main__':
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'config.cfg'
 
    config = RawConfigParser()
    config.read(filename)

    lightIPs = config.get('lighting', 'lightAddresses').split(',')
    lightPrefix = Name(config.get('lighting', 'prefix'))
    myIP = config.get('lighting', 'address')


    allLights = []
    for i in range(len(lightIPs)):
        lightName = Name(lightPrefix).append('light'+str(i))
        controller = LightController(prefix=lightName, lightIP=lightIPs[i])
        allLights.append(controller)


    eventLoop = asyncio.get_event_loop()
    # make it auto-restart, unless we did ^C
    keychain = KeyChain()
    certificateName = keychain.getDefaultCertificateName()
    while True:
        face = ThreadsafeFace(eventLoop, "")
        face.setCommandSigningInfo(keychain, certificateName)
        try:
            for l in allLights:
                l.start(eventLoop, face)
            eventLoop.run_forever()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.getLogger('LightController').exception(e, exc_info=True)
        finally:
            for l in allLights:
                l.stop()
            face.shutdown()
