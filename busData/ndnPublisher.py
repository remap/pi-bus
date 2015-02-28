#/usr/bin/env python
# encoding: utf-8
"""
ndnPublisher.py

this publishes a python dict into a namespace as a content object

Created by nano on 2012-06-15.
Copyright (c) 2012 UCLA Regents. All rights reserved.
"""


import sys
import os
from pyndn import Name, Face, Interest, Data
from pyndn.security import KeyChain
from pyndn.sha256_with_rsa_signature import Sha256WithRsaSignature
import time
from datetime import datetime
from threading import Thread
import ConfigParser
import database as data
import logging
import json

config = ConfigParser.RawConfigParser()

def timestampStrToUnix(timeStr):
        dt = datetime.strptime(timeStr, '%Y-%m-%d %H:%M:%S')
        epochTime = dt - datetime(1970,1,1)
        
        return epochTime.total_seconds()

def main():
        readConfig()
        prefix = config.get("publisher", "prefix")
        ndnserver = NDServer(prefix)
        #thread = Thread(target=ndnserver.listen)
        print "Starting NDN server on", prefix, "and waiting for interests"
        try:
            #thread.start()
            ndnserver.listen()
        except KeyboardInterrupt:
            ndnserver.stop()

def readConfig():
        configFile = os.path.dirname(__file__)+'config.cfg'
        config.readfp(open(configFile))

import struct

class NDServer(Thread):
    def __init__(self, prefix, logger=None):
        self.prefix = Name(prefix)
        self.keychain = KeyChain()
        self.certificateName = self.keychain.getDefaultCertificateName()
        
        self.face = None
        self._isStopped = True
        
        # setup logging
        if logger is not None:
            self.logger = logger
        else:
            logFormat = "%(levelname)-10s %(asctime)-10s %(funcName)-20s  %(message)s"
            self.logger = logging.getLogger("NDN_Bus_Publisher")
            self.logger.setLevel(logging.DEBUG)
      
            logFile = config.get("publisher", "logFile")
            if logFile is not None:
                fh = logging.FileHandler(logFile)
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(logging.Formatter(logFormat))
                self.logger.addHandler(fh)
            sh = logging.StreamHandler()
            sh.setLevel(logging.WARNING)
            sh.setFormatter(logging.Formatter(logFormat))
            self.logger.addHandler(sh)
        
    

    def registerFailed(self, prefix):
        # TODO: logging
        self.logger.error("Could not register "+prefix.toUri())
        self.stop()


    def publish(self, name, content, timestamp=None):
        content = json.dumps(content)
        self.logger.debug( "PUBLISHING: " + content)
        dataName = Name(name)
        if timestamp is not None:
            dataName.appendVersion(int(timestamp))
        d = Data(dataName)
        d.finalBlockID = b'\x00' # there are no more segments
        d.getMetaInfo().setFreshnessPeriod(int(config.get("publisher", "freshness")))
        d.setContent(content)
        self.keychain.sign(d, self.certificateName)
        return d
     

    def listen(self):
        #listen to requests in namespace
        self.face = Face() # TODO: DO I NEED TO SPECIFY AN ADDRESS?
        self.face.setCommandSigningInfo(self.keychain, self.certificateName)
        self.face.registerPrefix(self.prefix, self.receivedInterest, self.registerFailed)
        self._isStopped = False
        try:
            while not self._isStopped:
                self.face.processEvents()
                time.sleep(0.01)
        except KeyboardInterrupt:
             pass
        self.face.shutdown()
        self.face = None

    def stop(self):
        self._isStopped = True # maybe have to do other cleanup?

    def receivedInterest(self, prefix, interest, transport, prefixID):
        message = None
        name = interest.getName()
        self.logger.debug( "Interest Received for "+name.toUri())
        # if root requested, reply with full dict...

        dbEntry = data.getLastEntry()
        if u'status' in dbEntry:
            status = dbEntry['status']
            ts = None
            if 'sampleTime' in status:
                ts = timestampStrToUnix(status['sampleTime'])
                
            if name.equals(prefix):   # root 
                message = self.publish(name, status, ts)

            # return requested status value, if exists
            elif (name.size() == self.prefix.size()+1):
                suffix = name.get(-1) 
                self.logger.debug("Request for one deeper than root: %s" % suffix.toEscapedString())
                key = suffix.toEscapedString()
                if type(status) is dict and key in status:
                    self.logger.debug( "Returning: {}: {}".format(key, status[key]))
                    # should use time from bus data sample, but for now we'll use system time
                    message = self.publish(name, status[key], ts)
                else:
                    self.logger.info("requested parameter not in status object")
                    err = "unexpected interest : "+ key
                    message = self.publish(name, err)
            else:
                self.logger.warn("not sure what is being requested... publish error")
                message = self.publish(name, "unexpected interest")

        if message is not None:
            encodedData = message.wireEncode()
            transport.send(encodedData.buf())


if __name__ == '__main__':
        main()

