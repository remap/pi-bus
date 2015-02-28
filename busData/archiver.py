#!/usr/bin/env python
# encoding: utf-8
"""
archiver.py

this polls and stores an XML webservice into a mongo database. 

Created by nano on 2012-06-08.
Copyright (c) 2012 UCLA Regents. All rights reserved.
"""
import sys
import os
import ConfigParser
import xml
import json
import urllib
import time
from BeautifulSoup import BeautifulSoup
from xml.dom.minidom import parseString
import datetime
import database as data

config = ConfigParser.RawConfigParser()

sysStartTime = time.time()

def readConfig():
	configFile = os.path.dirname(__file__)+'/config.cfg'
	config.readfp(open(configFile))

def main():
	readConfig()
	while True:
		time.sleep(float(config.get("archiver", "APIDelay")))
		try:
			pollLoop()
		except:
			sysStopTime = time.time()
			print " there is a problem... runtime:",sysStopTime-sysStartTime 
			break

def pollLoop():
	loc = getLocations()
	print ("got locations")
	eta = getETAs()
	print  ("got ETAS")
	writeLocAndETA(loc,eta)
	print ("wrote everything")
	return True

def getLocations():
	print "getting locations..."
	status = urllib.urlopen(config.get("archiver","locationURL"))
	xml = status.read()
	#print xml
	return xml
	
def getETAs():
	print "getting ETAs..."
	status = urllib.urlopen(config.get("archiver","predictionURL"))
	xml = status.read()
	#print xml
	return xml
	
def writeLocAndETA(locXML, preXML):
	print " writing location & eta at ", time.time()-sysStartTime 
	# ideally, derive the params we are most interested in
	# meanwhile, just write the XML & we can derive later in 'NDN publisher'
	# logDatabase(predictionXML, locationXML, nextBusRoute, nextBusOccupancy, nextBusETA, nextBusPredictable):
	dom = parseString(preXML)
	try:
	    pre = dom.getElementsByTagName('predictions')[1].getElementsByTagName('prediction')[0]
	except:
	    msg = "there are no predictions. \r\n this is normal between 7a-7p weekdays (7:30-6:30 summer), and all weekends."
	    print msg
	eta = pre.getAttribute('seconds')
	epoch = pre.getAttribute('epochTime')
	epoch = datetime.datetime.fromtimestamp(float(epoch[:10]))
	preTime  = epoch.strftime('%Y-%m-%d %H:%M:%S')
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
	
	
	status = {"route":routeTag, "occupancy":passengerCount, "eta":eta, "predictable":predictable, "vehicleID":vehicleID, 'predictedTime':preTime, 'sampleTime':lastTime}
	print status
	# logDatabase(predictionXML, locationXML, nextBusRoute, nextBusOccupancy, nextBusETA, nextBusPredictable):
	
	#data.logDatabase(preXML, locXML, routeTag, passengerCount, eta, predictable, sampleTime, predictedTime, status)
	#logDatabase(preXML, locXML, routeTag, passengerCount, eta, predictable, lastTime, preTime)
	
	#old
	data.logDatabase(preXML, locXML, routeTag, passengerCount, eta, predictable, status, lastTime)


if __name__ == '__main__':
	main()

