

import datetime, time
from datetime import timedelta
from lx.SimpleSun import SimpleSun
from enum import Enum

## IMPORTANT: 
## The Enum dependency under Python2.7 should be Enum34, which can be installed with PIP
## 
class State(Enum):
    Unknown = -1
    Dawn = 0 
    Day = 1 
    Dusk = 2
    Night = 3
        
class DactylTime(SimpleSun):


    def __init__(self, crossfade = 0):
        SimpleSun.__init__(self, -118.450043, 34.061893)  # Initialize with sculpture location
        self.state = State.Unknown
        self.cbNightToDawn = None
        self.cbDawnToDay = None
        self.cbDayToDusk = None
        self.cbDuskToNight = None
        self.cbValueUpdate = None
        self.tNight = 0
        self.tDawn = 0
        self.tDay = 0 
        self.tDusk = 0
        self.xfvNight = 0
        self.xfvDawn = 0
        self.xfvDay = 0
        self.xfvDusk = 0 
        
        self.crossfade = 0.1      # percentage time to generate cross fades 
        
    def clip(self, v):
        if v > 1: return 1.0
        if v < 0: return 0.0
        return v 
        
    def update(self, force_now = None): 
        if force_now is not None: 
            now = force_now
        else:
            now = datetime.datetime.now()
        
        self.now = now
        old_state = self.state
        # Update the state
        # This should except in really weird locations where the inequalities are too simplistic
       
        #Relative positions
        self.tNight = 0
        self.tDawn = 0
        self.tDay = 0 
        self.tDusk = 0
        
        # relative progress in a timeline for time=now, given an endpoint and duration
        relt = lambda endpoint, duration: self.clip(1-(endpoint-now).total_seconds() / duration.total_seconds() )
        
        if now > self.dawn and now < self.sunrise:
            self.state = State.Dawn
            self.tDawn = relt(self.sunrise, self.durationDawn)
        elif now >= self.sunrise and now <= self.sunset:
            self.state = State.Day
            self.tDay = relt(self.sunset, self.durationDay) 
        elif now > self.sunset and now < self.dusk:
            self.state = State.Dusk
            self.tDusk = relt(self.dusk, self.durationDusk) 
        elif now >= self.dusk and now <= self.next_dawn:
            self.state = State.Night   
            self.tNight = relt(self.next_dawn, self.durationNight)        
        elif now > self.next_dawn:
            self.state = State.Dawn
            self.calcAlmanac(force_now = now)
            print("Recalculated almanac times \n{!s}\n".format(self))  # Recalculating at dawn keeps us in the same state even when the values change underneat
            self.tDawn = relt(self.sunrise, self.durationDawn) 
        else:
            print("ERROR: Inconsistent time comparison", now, self, "\n")
        
        
        self.calcCrossfades()
                
        # process TRANSITIONS
        if self.state != old_state:
            if self.state==State.Dawn and (old_state==State.Night or old_state==State.Unknown):
                self.TriggerNightToDawn()
            elif self.state==State.Day and (old_state==State.Dawn or old_state==State.Unknown): 
                self.TriggerDawnToDay()
            elif self.state==State.Dusk and (old_state==State.Day or old_state==State.Unknown):
                self.TriggerDayToDusk()
            elif self.state==State.Night and (old_state==State.Dusk or old_state==State.Unknown):
                self.TriggerDuskToNight()
            else:
                print("ERROR: Inconsistent state transition from", old_state, "to", self.state)

        # process VALUE UPDATES
        self.valueUpdate()
 

        return
     
    def calcCrossfades(self):
             
        # 
        # Sort of unnecessarily complicated here
        #
        # For each state transition:
        # self.crossfade defines the percentage (in and out) to where to crossfade
        # for example, a value of 0.1 means the last 10% of previous state, and first 10% of next state
        # Below, values are hardcoded to 0.5 at the transition boundard...
        #
        # Crossfade is active between CF1 (1-crossfade) and CF0 (up to crossfade point)
        # 
        #               CF1  CF0   
        #                |   |
        #  ... state 0 ... | ... state 1 ... | 
        #
        
                
        # Zero everything
        self.xfvNight = 0
        self.xfvDawn = 0
        self.xfvDay = 0 
        self.xfvDusk = 0
        
        if self.crossfade == 0: 
            self.xfvNight = 1 if self.state==State.Night else 0 
            self.xfvDawn = 1 if self.state==State.Dawn else 0 
            self.xfvDay = 1 if self.state==State.Day else 0
            self.xfvDusk = 1 if self.state==State.Dusk else 0
            return
        
        cf0 = self.crossfade
        cf1 = 1-self.crossfade
        
        xf = lambda t, t0, t1, a0, a1:  (t-t0)*(a1-a0)/(t1-t0) + a0          # linear scaling, input t from t0 to t1, output a0 to a1
        
        if self.state==State.Dawn:
            if self.tDawn > cf0 and self.tDawn < cf1: 
                self.xfvDawn = 1
            elif self.tDawn <= cf0: # Beginning of Dawn, End of Night
                self.xfvDawn = xf(self.tDawn, 0, cf0, 0.5, 1)
                self.xfvNight = xf(self.tDawn, 0, cf0, 0.5, 0)             
            elif self.tDawn >= cf1: # End of Dawn, Beginning of Day
                self.xfvDawn = xf(self.tDawn, cf1, 1, 1, 0.5)
                self.xfvDay = xf(self.tDawn, cf1, 1, 0, 0.5)
                
        elif self.state==State.Day:
            if self.tDay > cf0 and self.tDay < cf1: 
                self.xfvDay = 1
            elif self.tDay <= cf0: # Beginning of Day, End of Dawn
                self.xfvDay = xf(self.tDay, 0, cf0, 0.5, 1)
                self.xfvDawn = xf(self.tDay, 0, cf0, 0.5, 0)
            elif self.tDay >= cf1: # End of Day, Beginning of Dusk
                self.xfvDay = xf(self.tDay, cf1, 1, 1, 0.5)
                self.xfvDusk = xf(self.tDay, cf1, 1, 0, 0.5)
                
        elif self.state==State.Dusk:
            if self.tDusk > cf0 and self.tDusk < cf1: 
                self.xfvDusk = 1
            elif self.tDusk <= cf0: # Beginning of Dusk, End of Day
                self.xfvDusk = xf(self.tDusk, 0, cf0, 0.5, 1)
                self.xfvDay = xf(self.tDusk, 0, cf0, 0.5, 0)
            elif self.tDusk >= cf1: # End of Dusk, Beginning of Night
                self.xfvDusk = xf(self.tDusk, cf1, 1, 1, 0.5)
                self.xfvNight = xf(self.tDusk, cf1, 1, 0, 0.5)
                
        elif self.state==State.Night:
            if self.tNight > cf0 and self.tNight < cf1:
                self.xfvNight = 1
            elif self.tNight <= cf0: # Beginning of Night, End of Dusk
                self.xfvNight = xf(self.tNight, 0, cf0, 0.5, 1)
                self.xfvDusk = xf(self.tNight, 0, cf0, 0.5, 0)
            elif self.tNight >= cf1: # End of Night, Beginning of Dawn
                self.xfvNight = xf(self.tNight, cf1, 1, 1, 0.5)
                self.xfvDawn = xf(self.tNight, cf1, 1, 0, 0.5)
            
                         

           
    def valueUpdate(self):
        if self.cbValueUpdate is not None:
            self.cbValueUpdate(self.now, self.state, [self.tDawn, self.tDay, self.tDusk, self.tNight], [self.xfvDawn, self.xfvDay, self.xfvDusk, self.xfvNight])
            
    def TriggerNightToDawn(self):            # now is datetime object, relt is float of time in new state. 
        if self.cbNightToDawn is not None:
            self.cbNightToDawn(self.now, self.tDawn)

    def TriggerDawnToDay(self):
        if self.cbDawnToDay is not None:
            self.cbDawnToDay(self.now, self.tDay)
    
    def TriggerDayToDusk(self):
        if self.cbDayToDusk is not None:
            self.cbDayToDusk(self.now, self.tDusk)
    
    def TriggerDuskToNight(self):
        if self.cbDuskToNight is not None:
            self.cbDuskToNight(self.now, self.tNight )

    def __str__(self):
        return SimpleSun.__str__(self)


if __name__ == '__main__':
    dactyltime = DactylTime(crossfade = 0.1)
    
    #Py
    #dactyltime.cbNightToDawn = lambda now, relt: print("TRANSITION CALLBACK: Night to Dawn", now, relt)   # where relt is the float[0,1] time in Dawn, etc. 
    #dactyltime.cbDawnToDay = lambda now, relt: print("TRANSITION CALLBACK: Dawn to Day", now, relt)
    #dactyltime.cbDayToDusk = lambda now, relt: print("TRANSITION CALLBACK: Day to Dusk", now, relt)
    #dactyltime.cbDuskToNight = lambda now, relt: print("TRANSITION CALLBACK: Dusk to Night", now, relt)
    #dactyltime.cbValueUpdate = lambda now, state, reltarray, xfvarray: print("UPDATE CALLBACK:", now, state, reltarray, xfvarray, "XF SUM ERROR" if round(sum(xfvarray), 2) != 1.0 else "")
    
    print(dactyltime)
    import sys
    #sys.exit(1)
    dt = datetime.datetime.now() 
    
    #for h in range(0, 500):
        #print(dt)
    while (1):
       dactyltime.update(force_now = dt)
       dt += timedelta(minutes=2)
       time.sleep(.040)
    
    