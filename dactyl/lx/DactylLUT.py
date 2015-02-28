import sys, math
try:  # TODO FIX  but not needed just to read 
    from PIL import Image 
except:
    pass
from os import listdir, stat
from os.path import isfile, join
from parse import * 
import time   
import pickle    
from numpy import array 
PROTOCOL = 2
# DactylLUT
# 11/30/2014
# jburke@ucla.edu

# Lookup table for setting Dactyl colors from images and animations (still sequences).
# Basically, you provide a uv texture map (still or animation sequence) for the Dactyl 3D form,
# and a coordinate map (from light # to uv coordinate) and the LUT generates an rgb array suitable
# for controlling the lights per the 3D form. 
#
# See end of file for usage examples. 
#
# Notes:  
#      Heavy lifting is done in loadImage/loadSequence calls; do these once and outside of timing-critical loops. 
#      Animations are typically accessed with a normalized time parameter t=[0,1]
#
#      Doesn't handle "tail" (umbillical between the two moons) yet. 
#      Texture color / gamma transform probably need to adjust for lighting colorspace difference.
#      No interpolation for queries into the animation sequence that don't match existing times;
#        if temporal accuracy of playback is important, need to write a different playback
#        routine. But for reasonable animation lengths and refresh rates, should be fine.
#
# 


# DEPENDENCIES
# pillow (install via pip)
# parse (install via pip)

# Notes for Adeola:
# - Use Pillow instead of PIL (change of dependency)


# The DactylLUT class encapsulates image- and animation-based
# lookup tables for Dactyl lighting control. 
#

class DactylLUT:

    class LUTType:
        UNKNOWN = 0 
        IMAGE = 1
        ANIMATION = 2
        
    def __init__(self):
        self.textureType = self.LUTType.UNKNOWN
        self.debug = True
        
    def loadImage(self, coordFilename, textureFilename, texturescale):
        self.coordFilename = coordFilename
        self.coords, self.coordsMeta = self.readCoordinateFile(coordFilename, texturescale)
        self.textureScale = texturescale
        self.textureFilename = textureFilename
        self.textureType = self.LUTType.IMAGE
        self.texture = Image.open(textureFilename).convert('RGB')
        if not self.coordinateSanityCheck( self.texture, self.coords, self.coordsMeta ):
            print("DactylLUT: coordinateSanityCheck fails for %s and %s" % (self.coordFilename, self.textureFilename))
        self.rgbarray = [0] * 3 * self.coordsMeta["max_id"]    
        self.fillLightArray(self.rgbarray, self.texture, self.coords)
        if self.debug:
            print(self.coords)
            print(self.coordsMeta)
            print(self.rgbarray)
        self.texture=None   # Storing this to prevent pickling (for some images), and makes files larger / objects take more memory
    
    def loadSequence(self, coordFilename, seqfolder, seqname, seqrate, texturescale ):
        self.coordFilename = coordFilename
        self.coords, self.coordsMeta = self.readCoordinateFile(coordFilename, texturescale)
        self.textureScale = texturescale
        self.textureSeqFolder = seqfolder
        self.textureSeqName = seqname
        self.textureSeqRate = seqrate
        self.textureType = self.LUTType.ANIMATION
        self.textureSeqLen = 0 # frames
        self.textureSequence = []
        self.textureSeqTotalTime = 0
        
        filenames = [ f for f in listdir(seqfolder) if isfile(join(seqfolder,f)) ]
        sequence_pre = []
        t_max = 0 
        for f in filenames:
            try:
                if f[0] == '.': continue   # skips .DS_STORE, etc.
                n = parse(seqname, f)[0]   # exception thrown if parsing doesn't match
                t = float(n) / float(seqrate)
                if t > t_max: t_max = t
                sequence_pre.append({'t_abs':t, 'n':n, 'filename':join(seqfolder,f)})
                #print ("time %05.2f sec, frame %04d, %s" % (t, n,f))
            except:
                print("DactylLUT: Exception parsing filename %s %s" % (f, sys.exc_info()[0]))
                #raise
        self.textureSeqTotalTime = t_max
        
        # sort by frame position
        sequence_pre = sorted(sequence_pre, key = lambda seq:seq['n'])
        for frame in sequence_pre: 
            try:
                frame['t'] = frame['t_abs'] / t_max  # add normalized time
                if self.debug: print ("Loading t=%0.03f %04d %s" % (frame['t'], frame['n'], frame['filename'])) 
                texture = Image.open(frame['filename']).convert('RGB')
                rgbarray = [0] * 3 * self.coordsMeta["max_id"] 
                self.fillLightArray(rgbarray, texture, self.coords)
                frame['rgbarray'] = rgbarray 
                # TODO: Calc tail 
                self.textureSequence.append(frame) # no exception thrown by this point, add to final list
            except:
                print("DactylLUT: Exception processing filename %s %s" % (frame['filename'], sys.exc_info()))
                #raise
        self.textureSeqLen = len(self.textureSequence)
        if self.debug: print ("Total memory consumed by animation: %d kb for %d steps" % (int(sys.getsizeof(self.textureSequence)/1024 + 0.5), self.textureSeqLen) )
    
        self.textureSequence = None # Storing this to prevent pickling (for some images), and makes files larger / objects take more memory
        
    # Return an rgb string for optional time t
    # for the big and small moons  
    def getRGB(self, t=0):
        if self.textureType == self.LUTType.IMAGE:
            return self.rgbarray
        elif self.textureType == self.LUTType.ANIMATION:
            if t > 1: t = 1 
            if t < 0: t = 0 
            k = int(math.floor(t*(self.textureSeqLen-1)))
            # TODO: Consider interpolating here between frames in the seq 
            frame = self.textureSequence[k]
            return frame['rgbarray'], frame['t'], frame['n'], frame['filename']
        else:
            return [] 
    
    def getRGBnumpy(self, t=0):
        return array(self.getRGB(t))
    # Read files with lines:
    # <light>,<face>,<texture_x>,<texture_y> 
    # Allow whitespace and '#' as comment.
    #
    # Returns list of dicts, { id (int), face (int), texture_coords (tuple x,y) } 
    # 
    def readCoordinateFile(self, filename, texture_scale=1):
        if self.debug: print("DactylLUT readCoordinateFile(%s, %0.3f)" % (filename, texture_scale))
        coords = [] 
        max_u = 0 
        min_u = sys.maxsize
        max_v = 0 
        min_v = sys.maxsize 
        max_id = 0 
        min_id = sys.maxsize
        count = 0 
        f = open(filename,'r')
        N = 0
        for line in f:
            N += 1
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            tokens = line.split(",")
            if len(tokens) != 4:
                print("DactylLUT readCoordinateFile: Error on line %i of %s, incorrect number of parameters" % (N, filename))
                continue 
            try:
                id = int(tokens[0])
                face = int(tokens[1])
                u = int( int(tokens[2]) * texture_scale)
                v = int( int(tokens[3]) * texture_scale)
                coords.append( { "id": id, 
                                 "face":  face, 
                                 "uv": (u,v) })
                if u > max_u: max_u = u
                if v > max_v: max_v = v
                if u < min_u: min_u = u
                if v < min_v: min_v = v 
                if id > max_id: max_id = id
                if id < min_id: min_id = id
                count += 1
            except: 
                print("Exception parsing line %i of %s" % (N, filename), sys.exc_info()[0])
                #raise
        meta = { "max_uv": (max_u, max_v), "min_uv": (min_u, min_v), "count": count, "max_id": max_id, "min_id": min_id, "filename": filename }
        return (coords, meta)
    
    
    def coordinateSanityCheck (self, texture, coords, coords_meta): 
        if coords_meta["min_uv"][0] < 0:
            print("minimum u value outside image bounds, %i < 0" % coords_meta["min_uv"][0] )
            return False
        if coords_meta["min_uv"][1] < 0:
            print("minimum v value outside image bounds, %i < 0" % coords_meta["min_uv"][1] )
            return False
        if coords_meta["max_uv"][0] > texture.size[0]:
            print("maximum u value outside image bounds, %i > %i" % (coords_meta["max_uv"][0], texture.size[0]) )
            return False
        if coords_meta["max_uv"][1] > texture.size[1]:
            print("maximum v value outside image bounds, %i > %i" % (coords_meta["min_uv"][1], texture.size[1]) )
            return False
        # TODO: Other sanity checks go here
        return True
        
    # R, G, B, R, G, B, etc. 
    # Assumes eight-bit image!  
    #
    def fillLightArray(self, values, texture, coords):
        for light in coords:
            r, g, b = texture.getpixel(light["uv"])
            n = 3*(light["id"] - 1)
            
            values[n] = r
            values[n+1] = g
            values[n+2] = b
            if r==0 and g==0 and b==0: print(light["uv"], n, r, g, b)
        print("Filled array len", len(coords))
        return 

    @classmethod
    def pickleToFile(cls, object, filename):    
        f = open(filename, "wb")
        pickle.dump(object, f, PROTOCOL)
        f.close()
    
    @classmethod
    def unpickleFromFile(cls, filename):
        f = open(filename, "rb")
        obj = pickle.load(f)
        f.close() 
        return obj
    
if __name__ == '__main__':

### SAMPLE STARTUP CODE (ONLY DONE ONCE)
  
    # sml = for the small moon
    # big = for the big moon

  
    # Create still image look up tables
    # Texture files must be 24-bit rgb images only
    # 
    
    # Let's do two versions using the same coordinate translation table
    # Showing two different color maps for the big moon - e.g., to change lighting by swapping LUT / rgb output
    dactylLUT_big_still_red = DactylLUT()
    dactylLUT_big_still_white = DactylLUT()
    
    # Just do a single LUT example for the small moon
    dactylLUT_sml_still = DactylLUT()
    
    # args: Coordinate file, Texture file, Texture scale (coord file / texture)
    print("Loading still DactylLUTs")

    # Load same coordinate table, different image map
    # view the image maps to see the difference
    t0 = time.time()
    dactylLUT_big_still_red.loadImage('config/dactyl-coords-big.txt', 'still-test/test-uv-shade-red-256.png', 0.125)
    dactylLUT_big_still_white.loadImage('config/dactyl-coords-big.txt', 'still-test/test-uv-shade-white-256.png', 0.125)
    
    # Load one coordinate table, one map for this example 
    # (note small moon is same 3D form as big object, so uses same uv texture map, but different light-to-texture coordinate system)
    #
    dactylLUT_sml_still.loadImage('config/dactyl-coords-sml.txt', 'still-test/test-uv-shade-white-256.png', 0.125)

    print("Done loading from images.", int(1000*(time.time() - t0)), "ms")
       
    # Test a simple caching process:
    print("Pickling still DactylLUTs")
    DactylLUT.pickleToFile(dactylLUT_big_still_red, "dactylLUT_big_still_red.pickle")
    print( int(stat("dactylLUT_big_still_red.pickle").st_size / 1024), "kb")
    DactylLUT.pickleToFile(dactylLUT_big_still_red, "dactylLUT_big_still_white.pickle")
    print( int(stat("dactylLUT_big_still_white.pickle").st_size / 1024), "kb")
    DactylLUT.pickleToFile(dactylLUT_sml_still, "dactylLUT_sml_still.pickle")
    print( int(stat("dactylLUT_sml_still.pickle").st_size / 1024), "kb")
    print("Loading pickled still DactylLUTs")
    t0 = time.time()
    dactylLUT_big_still_red = DactylLUT.unpickleFromFile("dactylLUT_big_still_red.pickle")
    dactylLUT_big_still_white = DactylLUT.unpickleFromFile("dactylLUT_big_still_white.pickle")
    dactylLUT_sml_still = DactylLUT.unpickleFromFile("dactylLUT_sml_still.pickle")
    print("Done loading pickled stills...", int(1000*(time.time() - t0)), "ms")
    

 
    # DMX CONFIGURATION NOTE
    #
    # NOTE:  These coordinate files define the dmx arrangement of the lights.
    #        The dactyl-coords-big file generates a 100*3 array of RGB values for the big moon.
    #        The dactyl-coords-sml file generates a 50*3 array of RGB values for the small moon, with the first 13 left zero for the tail. 

    # Create animation look up tables, one animation LUT per moon 
    # 
    dactylLUT_big_animation = DactylLUT()
    dactylLUT_sml_animation = DactylLUT()

    # args: coordinate file, texture folder, texture filename pattern, frame rate, texture scale
    print("Loading animation DactylLUTs")
    t0 = time.time()
    dactylLUT_big_animation.loadSequence('config/dactyl-coords-big.txt','animation-test', 'testseq{:03d}.png', 24, 0.125)
    dactylLUT_sml_animation.loadSequence('config/dactyl-coords-sml.txt','animation-test','testseq{:03d}.png', 24, 0.125)
    print("Done loading from image sequence.", int(1000*(time.time() - t0)), "ms")
 
    print("Pickling animation DactylLUTs")
    DactylLUT.pickleToFile(dactylLUT_big_animation, "dactylLUT_big_animation.pickle")
    print( int(stat("dactylLUT_big_animation.pickle").st_size / 1024), "kb")
    DactylLUT.pickleToFile(dactylLUT_sml_animation, "dactylLUT_sml_animation.pickle")
    print( int(stat("dactylLUT_sml_animation.pickle").st_size / 1024), "kb")
    print("Loading pickled animation DactylLUTs")
    t0 = time.time()
    dactylLUT_big_animation = DactylLUT.unpickleFromFile("dactylLUT_big_animation.pickle")
    dactylLUT_sml_animation = DactylLUT.unpickleFromFile("dactylLUT_sml_animation.pickle")
    print("Done loading pickled animations...", int(1000*(time.time() - t0)), "ms")
 
    sys.exit(1)
 
### SAMPLE SINGLE QUERY CODE 

    # Get the lighting array from the lookup table for a still image 
    # Note:  big is 100 r,g,b 
    #        small is 50 r,g,b where first 13 correspond to the tail and are empty
    print("Test still queries")
    print(dactylLUT_big_still_red.getRGB())
    print(dactylLUT_big_still_white.getRGB())
    print(dactylLUT_sml_still.getRGB())

    # defaults to time = 0 
    print("Test animation queries, default time")
    print(dactylLUT_big_animation.getRGB())
    print(dactylLUT_sml_animation.getRGB())
                
    # test arbitrary time lookup and extra arguments
    # pass *normalized* time from 0 to 1
    # use self.textureSeqTotalTime to convert to/from absolute time
    # 
    print("Test animation queries, specified time")
    t = 0.24   # normalized time [0,1]
    rgbarray, t_actual, frame, framefile = dactylLUT_big_animation.getRGB(0.24)
    print ("\nQuery %0.3f, Accessing t=%0.03f %04d %s" % (t, t_actual, frame, framefile))
                
    
### PERIODIC REFRESH EXAMPLE SHOWING TIME-BASED ACCESS TO ANIMATION 
### TRY A TEST LIKE THIS IN THE MAIN LIGHTING LOOP

    print("Start time-based query to animation LUT")
    from time import time, sleep
    t = 0 # will hold normalized time from [0,1]
    T = 10.0 # seconds
    t_start = time()    
    while(t <= 1):
        rgbarray_big = dactylLUT_big_animation.getRGB(t)    # Get RGB arrays at time t
        rgbarray_sml = dactylLUT_sml_animation.getRGB(t)    # Get RGB arrays at time t
        print (t, rgbarray_big, rgbarray_sml)                               # Comment out print for performance
        sleep(0.050)  # Approx 50 ms sleep
        t = (time() - t_start) / T     
    t = 1    
    rgbarray = dactylLUT_big_animation.getRGB(t)
    print (t, rgbarray_big, rgbarray_sml)
    print ("End")
    
    

