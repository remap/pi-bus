#!/usr/bin/env python
# encoding: utf-8
"""
publisher.py

this formats a mongodb record into a filtered dict for use for NDN publishing

Created by nano on 2012-06-08.
Copyright (c) 2012 UCLA Regents. All rights reserved.
"""

import sys
import os
import database as data
from BeautifulSoup import BeautifulSoup
from xml.dom.minidom import parseString
import datetime

def main():
    print getStatusObject()
    #publishStatusObjectsFrom()
    return

def debug():
	#just used for debugging
	#http://borges.metwi.ucla.edu/ai/bus/src/publisher.py/getLatestEntryFromDatabase()
    #return data.getLastEntry
    return makeStatusObject()

def getStatusObject():
    return filterParams(data.getLastEntry())

def publishNewStatusToNDN(status):
    pass

def publishStatusObjectsFrom():
    # this allows development outside of XML schedule (7am-7pm)
    # basically a timeshifter for the data
    
    # 1. start at datetime
    # 2. publish a new sample every config.N seconds
    #time.sleep(float(config.get("archiver", "APIDelay")))
    series = data.getAllEntries(1000)
    # filter for datetime
    #
    
    # this method does not work, is just a scratch pad at the moment
    # the analysis file has better updated working version of this method
    
    for e in series:
        locXML = e['vehicleLocations']
        dom = parseString(locXML)
        #get sample time
        lastTimeXML = dom.getElementsByTagName('lastTime')[0]
        lastTimeEpoch = lastTimeXML.getAttribute('time')
        lastTimeEpochHMS = datetime.datetime.fromtimestamp(float(lastTimeEpoch[:10]))
        lastTime = lastTimeEpochHMS.strftime('%Y-%m-%d %H:%M:%S')
        print lastTime
        print e['_id']


def filterParams(data):
    # extracts just the parameters we are interested in

    # get status & location XML

    locXML = data['vehicleLocations']
    preXML = data['predictions']

	# ElementTree is more pythonic than minidom... perhaps refactor later. meanwhile:
	
	# get ETA from from first prediction 
    dom = parseString(preXML)
    try:
        pre = dom.getElementsByTagName('predictions')[0].getElementsByTagName('prediction')[0]
    except:
	    msg = "there are no predictions. \r\n this is normal between 7a-7p weekdays (7:30-6:30 summer), and all weekends."
	    return msg
    eta = pre.getAttribute('seconds')
    epoch = pre.getAttribute('epochTime')
    epoch = datetime.datetime.fromtimestamp(float(epoch[:10]))
    time  = epoch.strftime('%Y-%m-%d %H:%M:%S')
    # get vehicleID from first prediction
    vehicleID = pre.getAttribute('vehicle')

    # get sample time, passengerCount, predictable, and routeTag from vehicleLocations via vehicleID
    dom = parseString(locXML)

	#get sample time
    lastTimeXML = dom.getElementsByTagName('lastTime')[0]
    lastTimeEpoch = lastTimeXML.getAttribute('time')
    lastTimeEpochHMS = datetime.datetime.fromtimestamp(float(lastTimeEpoch[:10]))
    lastTime = lastTimeEpochHMS.strftime('%Y-%m-%d %H:%M:%S')

	# get all vehicle nodes
    vehicles = dom.getElementsByTagName('vehicle') #[0].getAttribute('id')
	
    routeTag = ""
    passengerCount = ""
    predictable = ""
	
    for node in vehicles:
        if (node.getAttribute('id') == vehicleID):
            routeTag = node.getAttribute('routeTag')
            passengerCount = node.getAttribute('passengerCount')
            predictable = node.getAttribute('predictable')
            break
    #routeTag = dom.getElementsByTagName('vehicle')[0].getAttribute('routeTag')


    return {"route":routeTag, "occupancy":passengerCount, "eta":eta, "predictable":predictable, "vehicleID":vehicleID, 'predictedTime':time, 'sampleTime':lastTime}

    getETADeltasForDay()
    data.getAllEntriesDuringDay(2012,7,25)
    #.sort([('_id',ASCENDING)]).skip(0).limit(limit)

if __name__ == '__main__':
    main()
