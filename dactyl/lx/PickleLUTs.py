

d = "lut/still"   # input/output director
f = "*.tif"       # glob for input files
coords_fn_sml = 'config/dactyl-coords-sml.txt'   # coordinate mapping to use 
coords_fn_big = 'config/dactyl-coords-big.txt' 

from lx.DactylLUT import DactylLUT
import os.path as path
import glob
from os import stat



spec = path.join(d,f)

n = 0
f = 0 
for fn in glob.glob(spec):
    print ("Read", fn)
    
    lut = DactylLUT()
    
    if fn.find("sml") != -1:    
        lut.loadImage(coords_fn_sml, fn, 1)
        print("Using small coordinate mapping.")
    else:
        lut.loadImage(coords_fn_big, fn, 1)
        print("Using big coordinate mapping.")  

    pfn = path.splitext(fn)[0]+".pickle"

    DactylLUT.pickleToFile(lut, pfn)
    print("Wrote", pfn)
    
    try:
        print("Attempt load", pfn)
        lut2 = DactylLUT.unpickleFromFile(pfn)
        print("SUCCESS", pfn, int(stat(pfn).st_size / 1024), "kb", lut2, "\n")
    except: 
        print("FAILED LOAD TEST", pfn,"\n")
        f+=1
    n+=1 
    
    
    
print (n, "files with", f, "failures.")