


from pyndn import Name, Data, Interest, ThreadsafeFace, Exclude
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv

from lx.DactylTime import DactylTime, State

from lx.DactylLUT import DactylLUT
import datetime, time, math
from datetime import timedelta
import sys, argparse



if sys.version_info[0] < 3: 
    import cPickle as pickle
    print("Python version less than 3, enabling protobuf and sending lighting commands")
    from ConfigParser import RawConfigParser
    from lx.light_command_pb2 import LightCommandMessage
    SENDLIGHTING=True
    ASYNCIO_DEBUG = False   # Set to get stack traces from coroutines in Python 2, used in the main loop setup below
else:
    import pickle
    print("Python version 3, not sending lighting commands...")
    from configparser import RawConfigParser
    SENDLIGHTING=False
    ASYNCIO_DEBUG = False
    
from random import randint
import traceback

import json

import trollius as asyncio
from trollius import Return, From

import logging
logging.getLogger('trollius').addHandler(logging.StreamHandler())


USE_LOOKUP = True 
GUIAVAILABLE = True
SHOWGUI = True
try:
    import cairo
    from gi.repository import Gtk
    print("GUI available.")
except:
    print("GUI not available because of import error for cairo or gtk.")
    GUIAVAILABLE = False
rgbarray = None

#Utility
def clip(v):
    if v > 1: return 1
    if v < 0: return 0
    return v 

def linmix( A, B, alpha, outscale=1):     # alpha => 1, output goes to B   must be same length
    LA = len(A)
    LB = len(B)
    if LA != LB:
        print("ERROR - linmix passed arguments of different lengths")
        L = LA if LA < LB else LB
    else:
        L = LA
        
    out = []
    a = float(alpha)
    for k in range(0,L):
        out.append( (A[k]*(1-a) + B[k]*a) * outscale)
    return out

class Dactyl:
    
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
     
        
        self.lightInterestName = [0,0,0]    
        lightName = Name(self.lightPrefix).append('light'+str(0))   
        self.lightInterestName[0] = Name(lightName).append('setRGB')
        lightName = Name(self.lightPrefix).append('light'+str(1))  
        self.lightInterestName[1] = Name(lightName).append('setRGB')
        lightName = Name(self.lightPrefix).append('light'+str(2))  
        self.lightInterestName[2] = Name(lightName).append('setRGB')
        self.lightCommand = [0,0,0]
        self.lightCommand[0] = Interest()
        self.lightCommand[1] = Interest()
        self.lightCommand[2] = Interest()
        
        self.lightCommand[0].setInterestLifetimeMilliseconds(500)  # If we don't have this, the defaults cause a lot of time to be spent in node.isTimedOut
        self.lightCommand[1].setInterestLifetimeMilliseconds(500)
        self.lightCommand[2].setInterestLifetimeMilliseconds(500)
        
    
    def draw(self, da, ctx): 
        ## Draw in Visualizer 
        self.drawStatusString(da, ctx)
        self.drawTimeProgress(da, ctx)
        self.drawValueUpdates(da, ctx)
        self.drawBreathingBlobs(da, ctx)
        self.drawRgbarrays(da, ctx)
    
    def drawStatusString(self, da, ctx):
        global last_update, bus_prox # TODO: not locked
        
        ctx.set_source_rgb(0,0,0)
        ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(18);
        ctx.move_to(5,20)
        s = "DACTYL LIGHTING VISUALIZATION"
        ctx.show_text(s)    
    
        ctx.set_font_size(14);
        y = 40
        for s in (lastUpdate["dactyltimestr"].split("\n")):
            y+=20 
            ctx.move_to(5,y)
            ctx.show_text(s)
          
        y += 30 
        
        ctx.set_font_size(16)
        ctx.move_to(5,y)
        ctx.show_text(str(lastUpdate["now"]))
        
        
        ctx.set_font_size(32)
        ctx.move_to(750,y)
        ctx.show_text(str(lastUpdate["state"]))
        
        y += 30 
        
        ctx.set_font_size(18)
        ctx.move_to(5,y)
        ctx.show_text(str("Bus proximity: {:0.3f}".format(bus_prox)))
          
            
        # "XF SUM ERROR" if round(sum(xfvarray), 2) != 1.0 else "")
        
    def drawTimeProgress(self, da, ctx):
        
        y0 = 300
        x0 = 10
        global lastUpdate
        tnames=["tDawn", "tDay", "tDusk", "tNight"]
        for i in range(0,4):
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            ctx.rectangle(x0, y0 + i*35, 400, 20)
            ctx.fill()
            
        ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(14)
        for i in range(0,4):
            ctx.set_source_rgb(0.2, 0.2, 0.7)
            ctx.rectangle(x0, y0 + i*35, 400*lastUpdate["reltarray"][i], 20)
            ctx.fill()
            
            ctx.move_to(x0,y0 +i*35 - 2)
            ctx.set_source_rgb(0,0,0)
    
            ctx.show_text(tnames[i])
          
    def drawValueUpdates(self, da, ctx):
        y0 = 300
        x0 = 500
        global lastUpdate
        tnames=["xfvDawn", "xfvDay", "xfvDusk", "xfvNight"]
        for i in range(0,4):
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            ctx.rectangle(x0, y0 + i*35, 400, 20)
            ctx.fill()
            
        ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(14)
        for i in range(0,4):
            ctx.set_source_rgb(0.2, 0.2, 0.7)
            ctx.rectangle(x0, y0 + i*35, 400*lastUpdate["xfvarray"][i], 20)
            ctx.fill()
            
            ctx.move_to(x0,y0 +i*35 - 2)
            ctx.set_source_rgb(0,0,0)
    
            ctx.show_text(tnames[i])  
    
    def drawRgbarrays(self, da, ctx): 
        global rgbarray
        
        y0 = 700
        
        # Big
        x0 = 100 
        
        #print(rgbarray["big"])
        #print(rgbcoords["big"])
        
        radius = 6
        scaling = 1*0.125
        gamma = 2
        for light in rgbcoords["big"]:
            #print(light["uv"])
            n = (light["id"]-1)*3
            ctx.arc((light["uv"][0])*scaling+x0, (light["uv"][1])*scaling+y0, radius, 0.0, 2*math.pi)           
            ctx.set_source_rgb(math.pow(rgbarray["big"][n]/255.0,1.0/gamma), math.pow(rgbarray["big"][n+1]/255.0,1.0/gamma), math.pow(rgbarray["big"][n+2]/255.0,1.0/gamma))
            ctx.fill()
    
            
        # Small, includes tail
        y0 = 800
        x0 = 530
        radius = 6
        scaling = 0.6*0.125
        for light in rgbcoords["sml"]:
            #print(light["uv"])
            n = (light["id"]-1)*3
            ctx.arc((light["uv"][0])*scaling + x0, (light["uv"][1])*scaling + y0, radius, 0.0, 2*math.pi)             
            ctx.set_source_rgb(math.pow(rgbarray["sml"][n]/255.0,1.0/gamma), math.pow(rgbarray["sml"][n+1]/255.0,1.0/gamma), math.pow(rgbarray["sml"][n+2]/255.0, 1.0/gamma))
            ctx.fill()
    
    
       # print(rgbarray["sml"])
        
               
    def drawBreathingBlobs(self, da, ctx):
        
        global breath
        y0 = 600
        # Big   
        ctx.set_source_rgb(breath[0], breath[0], breath[0])
        ctx.arc(200, y0, 70, 0.0, 2*math.pi)   
        ctx.fill()
     
        # Small   
        ctx.set_source_rgb(breath[2], breath[2], breath[2])
        ctx.arc(580, y0+30, 40, 0.0, 2*math.pi)   
        ctx.fill()   
    
        # umbilical    
        ctx.set_source_rgb(breath[1], breath[1], breath[1])
        ctx.rectangle(290, y0+37, 230, 10) 
        ctx.fill()  
        
    def cbValueUpdate(self, now, state, reltarray, xfvarray):
        global lastUpdate, dactyltime
        lastUpdate = {} 
        lastUpdate["now"] = now
        lastUpdate["dactyltimestr"] = str(dactyltime)  # should we pass this object? 
        
        lastUpdate["state"] = state
        lastUpdate["reltarray"] = reltarray
        lastUpdate["xfvarray"] = xfvarray
        
    
    #
    def wave(self, t, x, y, bus_prox):
    
        # LENGTHWISE WAVE 1 (FAST)
        
        q = 0.5  # not really a q, but sharpness
        f = 0.11 * (1+bus_prox)  # freq   # 0.09 good slow
        bias = 0.0
        W1 = (1 - math.exp( abs(math.sin(t*(f*2.0*math.pi)+(x+y)*q))) / math.exp(1))*(1.0-bias) + bias
        
        
        return W1   # flip to re-orient
    
    def square(self, t, x, y, bus_prox):
        f = bus_prox*0.75
        if abs(math.sin(t* (f*2.0*math.pi) )) > 0.5: return 1.0
        return 0.0
    
    
    # Adeola unmodified except for From() to from
    def onBusData(self, interest, data):
        ## TODO: handle multiple ETAs
        #busStr = json.loads(data.getContent().toRawStr())
        dataList = json.loads(data.getContent().toRawStr())
        etaList = [x['eta'] for x in dataList]
        print ("BUS ETA", etaList)
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
                #print("Expressed Interest")
                self.busFace.expressInterest(interestName, self.onBusData, self.onBusTimeout)
            except IOError:
                print("Cannot resolve bus data publisher")
                self.busFace.shutdown()
                self.busFace = None
                yield From(asyncio.sleep(10))
            else:
                yield From(self.busDataEvent.wait())
                yield From(asyncio.sleep(2))
    

        
    def cbNightToDawn(self, now, relt):
        print("TRANSITION CALLBACK: Night to Dawn", now, relt)
    def cbDawnToDay(self, now, relt):
        print("TRANSITION CALLBACK: Dawn to Day", now, relt)
    def cbDayToDusk(self, now, relt):
        print("TRANSITION CALLBACK: Day to Dusk", now, relt)
    def cbDuskToNight(self, now, relt):
        print("TRANSITION CALLBACK: Dusk to Night", now, relt)
        
    def _sendLightCommand(self, lightNum, colorArray):
        #self.lightInterestName
        #commandParams = LightCommandMessage()
        #print("setup command params")
        #for (r,g,b) in colorArray:
        #    messageColor = commandParams.command.pattern.colors.add()
        #    messageColor.r = r
        #    messageColor.g = g
        #    messageColor.b = b
        #print('finished rgb loop')
        #self.lightCommand.setName(Name(self.lightInterestName[lightNum]).append(pickle.dumps(colorArray))) # ProtobufTlv.encode(commandParams))
        n = Name(self.lightInterestName[lightNum]).append(pickle.dumps(colorArray))
        #command = Interest(n)
        self.lightCommand[lightNum].setName(n)
        #print (self.lightCommand.toUri())
        #self.lightFace.makeCommandInterest(command)
        self.lightFace.expressInterest(self.lightCommand[lightNum], self.onLightingResponse, self.onLightingTimeout)
        #print('finish expressing control interest', lightNum)
    def onLightingTimeout(self, interest):
        pass
    
    def onLightingResponse(self, interest):
        pass
    
    @asyncio.coroutine
    def issueLightingCommands(self):
        global rgbarray
    
        
        sml = []
        big = []
        for i in range(0,50*3): 
            sml.append(0)
        for i in range(0,100*3):
            big.append(0)
        T0 = time.time()
        while True:
            t = time.time()+1
            #print (1.0/(t-T0), "Hz")
            T0 = t
            if rgbarray is not None and SENDLIGHTING:
                for light in rgbcoords["sml"]:
                    n = (light["id"]-1)*3
                    r = int(rgbarray["sml"][n])
                    g = int(rgbarray["sml"][n+1])
                    b = int(rgbarray["sml"][n+2])
                    sml[n] = r
                    sml[n+1] = g
                    sml[n+2] = b
                for light in rgbcoords["big"]:
                    n = (light["id"]-1)*3  
                    r = int(rgbarray["big"][n])
                    g = int(rgbarray["big"][n+1])
                    b = int(rgbarray["big"][n+2])
                    big[n] = r
                    big[n+1] = g
                    big[n+2] = b
                    
                self._sendLightCommand(0, sml)
                self._sendLightCommand(1, big[0:150])
                self._sendLightCommand(2, big[150:])
            yield From(asyncio.sleep(0.001))
                
    @asyncio.coroutine    
    def calcmain(self):
        global USELOOKUP, SHOWGUI

   
        ## VISUALIZER
        #
        if GUIAVAILABLE and SHOWGUI:
            win = Gtk.Window()
            win.connect('destroy', lambda w: Gtk.main_quit())
            win.set_default_size(1024, 1024)
            drawingarea = Gtk.DrawingArea()
            win.add(drawingarea)
            drawingarea.connect('draw', self.draw)
            win.show_all()
    
    
        # Load the LUTs
        import os.path 
        lutdir = "lut/still"
        
        # index by dawn, day, dusk, night
        states = ["dawn", "day", "dusk", "night"]
        
        print("Loading lookup tables - remember to rerun PickleLUTs if things have changed")
        LUT_big_inhale = {}
        LUT_big_exhale = {}
        LUT_sml_inhale = {}
        LUT_sml_exhale = {}
        for s in states:
            s = s.lower()
            LUT_big_inhale[s] = DactylLUT.unpickleFromFile( os.path.join(lutdir, s+"-big-inhale.pickle" ) )
            print("big", "inhale", s, LUT_big_inhale[s])
            LUT_big_exhale[s] = DactylLUT.unpickleFromFile( os.path.join(lutdir, s+"-big-exhale.pickle" ) )
            print("big", "exhale", s, LUT_big_exhale[s])
            LUT_sml_inhale[s] = DactylLUT.unpickleFromFile( os.path.join(lutdir, s+"-sml-inhale.pickle" ) )
            print("sml", "inhale", s, LUT_sml_inhale[s])
            LUT_sml_exhale[s] = DactylLUT.unpickleFromFile( os.path.join(lutdir, s+"-sml-exhale.pickle" ) )
            print("sml", "exhale", s, LUT_sml_exhale[s])
            
        
        global lastUpdate, dactyltime, breath, bus_prox
        lastUpdate = {} 
        
        breath=[0,0,0]   # big, umbilical, small 
        
        dactyltime = DactylTime(crossfade = 0.1)
        
        dactyltime.cbNightToDawn = self.cbNightToDawn
        dactyltime.cbDawnToDay = self.cbDawnToDay
        dactyltime.cbDayToDusk = self.cbDayToDusk
        dactyltime.cbDuskToNight = self.cbDuskToNight
        dactyltime.cbValueUpdate = self.cbValueUpdate
        
        print(dactyltime)
    
        dt = datetime.datetime.now() 
    
    
        T = time.time()
        t1 = 0
        bus_prox = 0.0
        
        global rgbarray, rgbcoords  # latter for visualization
        rgbarray = {}
        rgbarray["big"] = []
        rgbarray["sml"] = [] 
        rgbcoords = {}
        rgbcoords["big"] = []
        rgbcoords ["sml"] = []     
        
    

        while True:
            
            # Generate breathing wave
            t = time.time()-T
            # bus_prox goes to 1 when bus arrives
            
            ## TESTING:
            #bus_prox += (t-t1)/30.0
            #print (t, t-t1, bus_prox)
            #if bus_prox > 1: bus_prox = 0.0
            
            ## FIELD
            bus_prox = 1 - self.currentETA/1000.0
            if bus_prox < 0.1: bus_prox = 0 
            
            ## As bus is really close start flashing

            prox_cutoff = 0.8
            if bus_prox > prox_cutoff: 
                  breath = [
                      self.square(t,0,0,bus_prox), 
                      self.square(t,0,0,bus_prox),
                      self.square(t,0,0,bus_prox)
                      ]        
            # Calculate breath
            else:
                breath = [
                          self.wave(t, 0, 0, bus_prox), 
                          self.wave(t, 0.75, 0, bus_prox),
                          self.wave(t, 1, 0, bus_prox) 
                          ]  
                     
            t1 = t
            
            # Time forcing
            
            ## JB FIELD: 
            dactyltime.update()
            
            ## TESTING:
            
            #dactyltime.update(force_now = dt)
            #dt += timedelta(minutes=4)
  
    
    
            # Get RGB values, do inhale / exhale mix and states
            
            sname = lastUpdate["state"].name.lower()
            #print(sname)
    
           # print(lastUpdate["xfvarray"])
           
            # Force position
            
            ## FORCE STATE
            
            #lastUpdate["xfvarray"] = [1,0,0,0] # dawn
            #lastUpdate["xfvarray"] = [0,1,0,0] # day
            #lastUpdate["xfvarray"] = [0,0,1,0] # dusk
            #lastUpdate["xfvarray"] = [0,0,0,1] # night
            
            rgbarray["big"] = ( (LUT_big_inhale["dawn"].getRGBnumpy(0)*(1-breath[0]) + LUT_big_inhale["dawn"].getRGBnumpy(0)*(breath[0])) * lastUpdate["xfvarray"][0] + 
                                (LUT_big_inhale["day"].getRGBnumpy(0)*(1-breath[0]) + LUT_big_exhale["day"].getRGBnumpy(0)*(breath[0])) * lastUpdate["xfvarray"][1] +
                                (LUT_big_inhale["dusk"].getRGBnumpy(0)*(1-breath[0]) + LUT_big_exhale["dusk"].getRGBnumpy(0)*(breath[0])) * lastUpdate["xfvarray"][2] +
                                (LUT_big_inhale["night"].getRGBnumpy(0)*(1-breath[0]) + LUT_big_exhale["night"].getRGBnumpy(0)*(breath[0])) * lastUpdate["xfvarray"][3])
                     
            rgbcoords["big"] = LUT_big_exhale[sname].coords    # Get RGB arrays at time t
             
       
            
            rgbarray["sml"] = ( (LUT_sml_inhale["dawn"].getRGBnumpy(0)*(1-breath[2]) + LUT_sml_exhale["dawn"].getRGBnumpy(0)*(breath[2])) * lastUpdate["xfvarray"][0] + 
                                (LUT_sml_inhale["day"].getRGBnumpy(0)*(1-breath[2]) + LUT_sml_exhale["day"].getRGBnumpy(0)*(breath[2])) * lastUpdate["xfvarray"][1] +
                                (LUT_sml_inhale["dusk"].getRGBnumpy(0)*(1-breath[2]) + LUT_sml_exhale["dusk"].getRGBnumpy(0)*(breath[2])) * lastUpdate["xfvarray"][2] +
                                (LUT_sml_inhale["night"].getRGBnumpy(0)*(1-breath[2]) + LUT_sml_exhale["night"].getRGBnumpy(0)*(breath[2])) * lastUpdate["xfvarray"][3])
            
            rgbcoords["sml"] = LUT_sml_exhale[sname].coords    # Get RGB arrays at time t
    
             
            if GUIAVAILABLE and SHOWGUI:
                try:
                    # Draw in visualizer
                    if Gtk.events_pending():
                        Gtk.main_iteration()
                    drawingarea.queue_draw()               
         
                except KeyboardInterrupt as k:   
                    sys.exit(1)  
                
            yield From(asyncio.sleep(0.01))

    def start(self):
        # uncomment for LUT
        global USE_LOOKUP, ASYNCIO_DEBUG
        #if USE_LOOKUP:
        #    self.initLookup()
        self.loop = asyncio.get_event_loop()
        if ASYNCIO_DEBUG: self.loop.set_debug(True)
        self.getBusFace()
        self.getLightFace()

        self.startTime = time.time()
    
        self.busDataEvent = asyncio.Event(loop=self.loop)
        asyncio.async(self.issueLightingCommands())
        asyncio.async(self.requestBusData())
        
        asyncio.async(self.calcmain())
        
        try:
            self.loop.run_forever()
        except Exception as e:
            
            traceback.print_stack()
            raise
                
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

                
if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Main controller for Dactyl')
    parser.add_argument("--gui", action="store_true", help="show gui")
    args=parser.parse_args()
    SHOWGUI = args.gui
    
    parser.add_argument("--trolliusdebug", action="store_true", help="force trollius debug on")
    args=parser.parse_args()
    if args.trolliusdebug:
        ASYNCIO_DEBUG = True
    
    
    
    
    filename="config.cfg"
    config = RawConfigParser()
    config.read(filename)
    
    while True:
        d = Dactyl(config)
        try:
            d.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            traceback.print_stack()
            print(e)
        finally:
            d.stop()
