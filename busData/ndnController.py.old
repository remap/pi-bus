#!/usr/bin/env python
# encoding: utf-8
"""
controller.py

Created by nano on 2012-06-20.
Copyright (c) 2012 UCLA Regents. All rights reserved.
"""

import sys
import os
import pyccn
import ConfigParser
from time import sleep
import ast

config = ConfigParser.RawConfigParser()
prefix = ""

def main():
	#readConfig()
	#prefix = config.get("publisher", "prefix")
	print "tout: ",getLatestStatus(prefix)
	#print "eta: ",getLatestETA(prefix)
	#print "peeps: ",getLatestOccupancy(prefix)
	#getJsonFromNDNStatus()
	pass

def readConfig():
	configFile = os.path.dirname(__file__)+'/config.cfg'
	config.readfp(open(configFile))
	
def getLatestETA(name):
    name = name+"eta"
    name = pyccn.Name(name)
    handle = pyccn.CCN()
    co = handle.get(name)

    if co is None:
            print("Got no response")
            return 0

    return(co.content)

def getLatestOccupancy(name):
    name = name+"occupancy"
    name = pyccn.Name(name)
    handle = pyccn.CCN()
    co = handle.get(name)

    if co is None:
            print("Got no response")
            return 0

    return(co.content)

def getLatestStatus(name):
    name = pyccn.Name(name)
    handle = pyccn.CCN()
    co = handle.get(name)

    if co is None:
            print("Got no response")
            return("Got no response")

    return(co.content)
    

def getJsonFromNDNStatus():
    readConfig()
    prefix = config.get("publisher", "prefix")
    status = getLatestStatus(prefix)
    # convert string back to dict, this is safer than normal eval
    status = ast.literal_eval(status)
    return 'data = { "occupancy": "'+status["occupancy"]+'", "eta": "'+status["eta"]+'", debug:"'+str(status)+'"}'


if __name__ == '__main__':
	main()