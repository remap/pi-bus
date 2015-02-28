from pyndn import Face, Interest, Data, Name
import time

didTimeout = False
didReceive = False
def onData(interest,  data):
    global didReceive
    print "Retreived data named " + data.getName().toUri()
    print "\t"+data.getContent().toRawStr()+"\n"
    didReceive = True

def onTimeout(interest):
    global didTimeout
    print "Timed out waiting for " + interest.getName().toUri()
    didTimeout = True

prefix = Name('/ndn/ucla.edu/apps/transportation/bus/stop/weyburn/')
user_input = ''
face = Face()
try:
    while True:
        user_input=raw_input('Interest suffix: ')
        didTimeout = False
        didReceive = False
        interestName = Name(prefix)
        if len(user_input) > 0:
           interestName = interestName.append(Name(user_input))
        face.expressInterest(interestName, onData, onTimeout)
        while not didTimeout and not didReceive:
            face.processEvents()
            time.sleep(0.01)
except KeyboardInterrupt:
    pass
    

face.shutdown()
