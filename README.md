# pi-bus
just the code for the raspberry pi on the bus. 

that is, it's essentially a fork of https://github.com/remap/ndn-sculptures/tree/integrate-lighting/ai-bus
to ease production & maintenance of the bus bench (ie allow direct git pull from pi in the field). 

# other related repositories:
There is the initial archiver / publisher and web status viewer here - https://github.com/remap/ai_bus
There is the summer 2014 NDN-IOT sculpture work here - https://github.com/remap/ndn-sculptures


# dependencies

NFD
Python2.7 
sudo pip install Enum34 parse

# how to run

from a fresh reboot:
```
export PYTHONPATH=/home/pi/ai-bus/dactyl
nfdc register / udp://borges.metwi.ucla.edu
cd /home/pi/ai-bus/dactyl/lx
python DactylMaster.py 
```
