#!/usr/bin/env python
# encoding: utf-8
"""
analysis.py

Created by nano on 2012-07-26.
Copyright (c) 2012 UCLA Regents. All rights reserved.
"""

import sys
import os
import database as data

from BeautifulSoup import BeautifulSoup
from xml.dom.minidom import parseString
from datetime import datetime, date, time
    
def getETADeltas():
    
    series = data.getAllEntriesDuringDay(2012,6,15)
    lastETA = ""
    lastVID = ""
    lastTime = ""
    for e in series:
        locXML = e['vehicleLocations']
        preXML = e['predictions']
        dom = parseString(locXML)
        #get sample time
        lastTimeXML = dom.getElementsByTagName('lastTime')[0]
        lastTimeEpoch = lastTimeXML.getAttribute('time')
        lastTimeEpochHMS = datetime.fromtimestamp(float(lastTimeEpoch[:10]))
        sampleTime = lastTimeEpochHMS.strftime('%Y-%m-%d %H:%M:%S')
        dom = parseString(preXML)
        vehicles = dom.getElementsByTagName('predictions') #[0].getAttribute('id')
        pre = dom.getElementsByTagName('predictions')[0].getElementsByTagName('prediction')[0]
        eta = pre.getAttribute('seconds')
        vID = pre.getAttribute('vehicle')
        if vID != lastVID:
            print " "+lastETA + " "+lastVID+" "+lastTime
            #print "eta: "+lastETA + " lastVID "+lastVID+" last time "+lastTime
        lastETA = eta
        lastVID = vID
        lastTime = sampleTime
        #print vehicles[0].toprettyxml()
        

def main():
    pass


if __name__ == '__main__':
    #main()
    getETADeltas()

