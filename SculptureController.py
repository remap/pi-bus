# THIS IS NOT USING A REPO YET
# TODO: put query interval in config

from pyndn import Name, Data, Interest, ThreadsafeFace, Exclude
from pyndn.security import KeyChain
from ConfigParser import RawConfigParser
from lighting.light_command_pb2 import LightCommandMessage
from random import randrange, randint

import json
import math
import time

import logging
import traceback

from pyndn.encoding import ProtobufTlv

import trollius as asyncio
from trollius import Return, From

from dactyl.lx.DactylLUT import DactylLUT
from itertools import izip_longest

logging.getLogger('trollius').addHandler(logging.StreamHandler())

dactylBasePath='dactyl/lx/'

USE_LOOKUP=0

class SculptureController:
    def __init__(self, config):
        self.busAddress = config.get('busData', 'address')
        self.lightAddress = config.get('lighting', 'address')

        self.busPrefix = config.get('busData', 'prefix')
        self.lightPrefix = config.get('lighting', 'prefix')

        self.nLights = 3

        self.busFace = None
        self.lightFace = None
        self.loop = None

        self.currentETA = 1000
        self.startTime = 0
        self.animLength = 10.0 #seconds

        self.lightArray = [(randint(0,255), randint(0,255), randint(0,255)) 
                for i in range(25)]
        self.keychain = KeyChain()
        self.certificateName = self.keychain.getDefaultCertificateName()

    def loadAnimation(self, coordsFile, seqfolder, seqname, seqrate=24, txScale=0.125):
        lut = DactylLUT()
        lut.loadSequence(coordsFile, seqfolder, seqname, seqrate, txScale)
        return lut

#   def initLookup(self):
#       lut = self.loadAnimation(dactylBasePath+'config/dactyl-coords-big.txt',
#                   dactylBasePath+'animation-test', 'testseq{:03d}.png')
#       self.bigLutRed = self.bigLutWhite = lut
#       self.smallLutWhite = self.loadAnimation(
#                   dactylBasePath+'config/dactyl-coords-sml.txt',
#                   dactylBasePath+'animation-test', 'testseq{:03d}.png')


    def initLookup(self):
        self.bigLutRed = DactylLUT()
        self.bigLutWhite = DactylLUT()
        self.smallLutWhite = DactylLUT()

        self.bigLutRed.loadImage(dactylBasePath+'config/dactyl-coords-big.txt',
                dactylBasePath+'still-test/test-uv-shade-red-256.png', 0.125)
        self.bigLutWhite.loadImage(dactylBasePath+'config/dactyl-coords-big.txt',
                dactylBasePath+'still-test/test-uv-shade-white-256.png', 0.125)
        self.smallLutWhite.loadImage(dactylBasePath+'config/dactyl-coords-sml.txt',
                dactylBasePath+'still-test/test-uv-shade-white-256.png', 0.125)
        #TODO: test with animation instead

    def getLightArraysForEta(self, eta):
        if eta < 60:
            bigLut = self.bigLutRed
        else:
            bigLut = self.bigLutWhite
        tdiff = time.time()-self.startTime
        try:
            animTime = math.fmod(tdiff, bigLut.textureSeqTotalTime)/bigLut.textureSeqTotalTime
            bigValues = bigLut.getRGB(animTime)[0]
        except AttributeError:
            # using still
            bigValues = bigLut.getRGB()
        try:
            animTime = math.fmod(tdiff, self.smallLutWhite.textureSeqTotalTime)/self.smallLutWhite.textureSeqTotalTime
            smallValues = self.smallLutWhite.getRGB(animTime)[0]
        except AttributeError:
            smallValues = self.smallLutWhite.getRGB()
        # chunk them into the (r,g,b) tuples we expect
        # animation has different return type vs still - that's bad :(
        bigRgb = list(izip_longest(*[iter(bigValues)]*3))
        smlRgb = list(izip_longest(*[iter(smallValues)]*3))

        return (bigRgb[:50], bigRgb[50:], smlRgb)

    def lightArrayForETA(self, eta):
        MAX_VAL = 255
        def rgbClamp(color):
            return tuple(b & 0xff for b in color)
            # don't wanna go blind!!!
            #return tuple(((b&0xff)>>1) for b in color)

        fadeN = lambda a, b: int(a*MAX_VAL/b)

        if eta <= 15:
            colorFunc = lambda x: (fadeN(x/4,25), randrange(int(MAX_VAL/4), MAX_VAL), fadeN(x/4,25))
        elif eta <= 60:
            colorFunc = lambda x: (fadeN(x,15), 255, 0)
        elif eta <= 120:
            colorFunc = lambda x: (0, fadeN(x,10), MAX_VAL-fadeN(x,10))
        elif eta <= 180:
            colorFunc = lambda x: (fadeN(x,10), 0, MAX_VAL)
        elif eta <= 240:
            colorFunc = lambda x: (MAX_VAL, 0, fadeN(x,10))
        elif eta <= 300:
            colorFunc = lambda x: (fadeN(x,10), 0, 0)
        elif eta <= 600:
            colorFunc = lambda x: (fadeN(x,8), 0, 0)
        else:
            colorFunc = lambda x: (MAX_VAL, 0, 0)

        animTime = math.fmod(time.time()-self.startTime, self.animLength)
        animIdx = 25*animTime
        lightArray = [rgbClamp(colorFunc(animIdx))]*50
        return lightArray

    def onBusData(self, interest, data):
        ## TODO: handle multiple ETAs
        #busStr = json.loads(data.getContent().toRawStr())
        dataList = json.loads(data.getContent().toRawStr())
        etaList = [x['eta'] for x in dataList]
        #print etaList
        busStr = etaList[0]
        self.currentETA = int(busStr)
        self.busDataEvent.set()

    def onBusTimeout(self, interest):
        #TODO: backoff?
        print('bus data timeout')
        self.busDataEvent.set()

    @asyncio.coroutine
    def requestBusData(self, latestVersion = None):
        while True:
            self.busDataEvent.clear()
            #interestName = Name(self.busPrefix).append('eta')
            interestName = Name(self.busPrefix)
            interest = Interest(interestName)
            if latestVersion is not None:
                e = Exclude()
                e.appendAny()
                e.appendComponent(latestVersion)
                interest.setExclude(e)
            interest.setInterestLifetimeMilliseconds(4000)
            try:
                # avoid blocking when WiFi is down
                self.busFace.expressInterest(interestName, self.onBusData, self.onBusTimeout)
            except IOError:
                print("Cannot resolve bus data publisher")
                self.busFace.shutdown()
                self.busFace = None
                yield From(asyncio.sleep(10))
            else:
                yield From(self.busDataEvent.wait())
                yield From(asyncio.sleep(2))

            
    def _sendLightCommand(self, lightNum, colorArray):
        lightName = Name(self.lightPrefix).append('light'+str(lightNum))        
        interestName = Name(lightName).append('setRGB')
        commandParams = LightCommandMessage()
        
        for (r,g,b) in colorArray:
            messageColor = commandParams.command.pattern.colors.add()
            messageColor.r = r
            messageColor.g = g
            messageColor.b = b 

        commandName = interestName.append(ProtobufTlv.encode(commandParams))
        command = Interest(commandName)
        
        #self.lightFace.makeCommandInterest(command)
        self.lightFace.expressInterest(command, self.onLightingResponse, self.onLightingTimeout)

    @asyncio.coroutine
    def issueLightingCommands(self):
        while True:
            if USE_LOOKUP:
            # uncomment below to use LUT
                lightArrays = self.getLightArraysForEta(self.currentETA)
            #comment below to use LUT
            else:
                lightArrays = [self.lightArrayForETA(self.currentETA) for i in range(3)]
            for i in range(self.nLights):
                self._sendLightCommand(i, lightArrays[i])        
            #TODO: set animation delay
            yield From(asyncio.sleep(0.010))
            


    def onLightingTimeout(self, interest):
        pass

    def onLightingResponse(self, interest, data):
        #TODO: check if the light controller really sent this
        pass

    def stop(self):
        self.loop.close()
        self.busFace.shutdown()
        self.lightFace.shutdown()

    def getBusFace(self):
      if self.busFace is None:
         self.busFace = ThreadsafeFace(self.loop, '')

    def getLightFace(self):
      if self.lightFace is None:
         self.lightFace =  ThreadsafeFace(self.loop, '')

    def start(self):
        # uncomment for LUT
        if USE_LOOKUP:
            self.initLookup()
        self.loop = asyncio.get_event_loop()
        self.getBusFace()
        self.getLightFace()

        self.startTime = time.time()
    
        self.busDataEvent = asyncio.Event(self.loop)
        asyncio.async(self.issueLightingCommands())
        asyncio.async(self.requestBusData())
        try:
            self.loop.run_forever()
        except:
            traceback.print_stack()
            raise

if __name__ == '__main__':
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'config.cfg'

    config = RawConfigParser()
    config.read(filename)
    # auto-restart on exceptions
    while True:
        s = SculptureController(config)
        try:
            s.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            traceback.print_stack()
            print e
        finally:
            s.stop()
