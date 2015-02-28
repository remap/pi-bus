
import Sun
import datetime
from datetime import timedelta
import time
import math


# Timeline - 
#
#                dawn           sunrise       sunset         dusk
#                  |              |             |              |
#    ... night ... | ... dawn ... | ... day ... | ... dusk ... | ... night ... 
#
#

class SimpleSun:
	
	def __init__(self, lon, lat):
		self.lat = lat
		self.lon = lon
		self.s = Sun.Sun()
		self.sunrise = None			# Hold today's times (for calcDate), datetime object
		self.sunset = None
		self.dawn = None
		self.dusk = None
		self.next_sunrise = None	# Hold tomorrow's times, datetime object
		self.next_sunset = None
		self.next_dawn = None
		self.next_dusk = None
		self.durationDawn = None
		self.durationDay = None
		self.durationDusk = None
		self.durationNight = None
		self.calcDate = None
		self.calcAlmanac()
		
	def hoursToHM(self, hours):
		h = int(hours)
		m = int(round((hours-int(hours))*60))
		if m==60:
			h += 1
			m = 0 
		if h==25:
			h=1
		return (h,m)
			
	def __str__(self):
		s = "Today's    Dawn {!s} Sunrise {!s} Sunset {!s} Dusk {!s}\n".format(self.dawn, self.sunrise, self.sunset, self.dusk)
		s+= "Tomorrow's Dawn {!s} Sunrise {!s} Sunset {!s} Dusk {!s}\n".format(self.next_dawn, self.next_sunrise, self.next_sunset, self.next_dusk)
		s+= "Today's durations:  Dawn {!s} Day {!s} Dusk {!s} Night {!s}\n".format(self.durationDawn, self.durationDay, self.durationDusk, self.durationNight)
		s+= "Calculated for day {!s} with location ({:f}, {:f})".format(self.calcDate, self.lat, self.lon) 
		return s	
	
	def calcAlmanac(self, force_now = None):
		
		# What day is today
		if force_now is not None:
			now = force_now
		else:
			now = datetime.datetime.today()
		now = now.replace(microsecond=0, second=0)
		year = now.year
		month = now.month
		day = now.day
		self.calcDate = now.replace(hour=0, minute=0)			# This 
				
		# How many hours from UTC?
		tzadjust = time.timezone/60/60

		# Could use pytzwhere to check latitude and longitude against timezone, but just sanity check for now.
		if tzadjust < 7: 
			print("ERROR: Your timezone is", -tzadjust, "from UTC. Are you sure things are configured correctly?\nEdit SimpleSun.py to remove this warning if it is and you know what you are doing.")
			import sys
			sys.exit(1)
		
		# Calculate today's times
		
		# Rise / set 
		# These are today's sunrise, etc. 
		RS = self.s.sunRiseSet(year, month, day, self.lon, self.lat)
		RS = (RS[0] - tzadjust, RS[1] - tzadjust)
				
		h, m = self.hoursToHM(RS[0])
		self.sunrise = now.replace(hour=h, minute=m)
		
		h, m = self.hoursToHM(RS[1])
		self.sunset  = now.replace(hour=h, minute=m)
		
		#Twilight / Dawn
		TW = self.s.civilTwilight(year, month, day, self.lon, self.lat)
		TW = (TW[0] - tzadjust, TW[1] - tzadjust)
		
		h, m = self.hoursToHM(TW[0])
		self.dawn = now.replace(hour=h, minute=m)
		
		h, m = self.hoursToHM(TW[1])
		self.dusk = now.replace(hour=h, minute=m)

		#print(RS, TW)
		# But our values are actually the *NEXT* sunrise / sunset, so go through and check. 
		
		# Calculate tomorrow's times
		nextday = now + timedelta(days=1)
		year = nextday.year
		month = nextday.month
		day = nextday.day
		RS = self.s.sunRiseSet(year, month, day, self.lon, self.lat)
		RS = (RS[0] - tzadjust, RS[1] - tzadjust)
		TW = self.s.civilTwilight(year, month, day, self.lon, self.lat)
		TW = (TW[0] - tzadjust, TW[1] - tzadjust)
		

		h, m = self.hoursToHM(RS[0])
		self.next_sunrise = nextday.replace(hour=h, minute=m)

		h, m = self.hoursToHM(RS[1])
		self.next_sunset  = nextday.replace(hour=h, minute=m)

		h, m = self.hoursToHM(TW[0])
		self.next_dawn = nextday.replace(hour=h, minute=m)

		h, m = self.hoursToHM(TW[1])
		self.next_dusk = nextday.replace(hour=h, minute=m)

		self.durationDawn = self.sunrise - self.dawn
		self.durationDay = self.sunset - self.sunrise
		self.durationDusk = self.dusk - self.sunset
		self.durationNight = self.next_sunrise - self.dusk
		
		

if __name__ == "__main__":
	t0 = time.time()
	ss = SimpleSun(-118.450043, 34.061893)
	ss_str = str(ss)
	t = ((time.time() - t0)*1000)
	print(t, "ms")
	print(ss)


	#print("range", ss["range"])
	
