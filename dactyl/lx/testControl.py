import sys, math
from PIL import Image 
from os import listdir
from os.path import isfile, join
from parse import * 

    
# DEPENDENCIES
# pillow (install via pip)
# parse (install via pip)


# Notes for Adeola:
# - Use Pillow instead of PIL (change of dependency)
# - 

# Read files with lines:
# <light>,<face>,<texture_x>,<texture_y> 
# Allow whitespace and '#' as comment.
#
# Returns list of dicts, { id (int), face (int), texture_coords (tuple x,y) } 
# 
def readCoordinateFile(filename, texture_scale):
    print("readCoordinateFile(%s, %0.2f)" % (filename, texture_scale))
    coords = [] 
    max_u = 0 
    min_u = sys.maxint
    max_v = 0 
    min_v = sys.maxint 
    max_id = 0 
    min_id = sys.maxint
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
            print("Error on line %i of %s, incorrect number of parameters" % (N, filename))
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


def coordinate_sanity_check (texture, coords, coords_meta): 
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
def fill_light_array(values, texture, coords):
    for light in coords:
        r, g, b = texture.getpixel(light["uv"])
        n = 3*(light["id"] - 1)
        #print light["uv"], n, r, g, b
        values[n] = r
        values[n+1] = g
        values[n+2] = b
    return 
    
if __name__ == '__main__':

## SAMPLE OF STILL IMAGE LOADER

    # big = big moon,  sml = small moon, tail = connector
    # tail is on strand used for small moon
        
    # Texture files must be 24-bit rgb images only
    # 
    texture_filename_big = 'still-test/test-uv-rainbow-256.png'
    texture_filename_sml = 'still-test/test-uv-rainbow-256.png'
    coords_filename_big = 'config/dactyl-coords-big.txt'
    coords_filename_sml = 'config/dactyl-coords-sml.txt'
    texture_scale = 0.125    # scale of texture image relative to coordinates provided. 
    
    # Load images, strip alpha channel / convert to RGB
    texture_big = Image.open(texture_filename_big).convert('RGB')
    texture_sml = Image.open(texture_filename_sml).convert('RGB')
    
    # TODO: Texture color/gamma transform to adjust for lighting
    # 

    coords_big, coords_meta_big = readCoordinateFile(coords_filename_big, texture_scale)
    coords_sml, coords_meta_sml = readCoordinateFile(coords_filename_sml, texture_scale)

    if not coordinate_sanity_check( texture_big, coords_big, coords_meta_big ):
        print("coordinate_sanity_check fails for %s and %s" % (coords_filename_big, texture_filename_big))
    if not coordinate_sanity_check( texture_sml, coords_sml, coords_meta_sml ):  
        print("coordinate_sanity_check fails for %s and %s" % (coords_filename_sml, texture_filename_sml))
    
    # Create arrays for RGB values that we can address up to max_id
    # 
    rgbarray_big = [0] * 3 * coords_meta_big["max_id"]    
    rgbarray_sml = [0] * 3 * coords_meta_sml["max_id"]  
    tail_length = coords_meta_sml["min_id"] - 1   # TAIL lights are on strand used for small moon 
    
    fill_light_array (rgbarray_big, texture_big, coords_big)
    fill_light_array (rgbarray_sml, texture_sml, coords_sml)

    # TODO: Tail interpolator

    # ** Now, values would get passed for DMX control ** 
    #
    # lights_big[0] to lights_big[3*49]  are the first strand on the big moon
    # lights_big[3*49] to lights_big[3*99] are the second strand on the big moon 
    # lights_sml[tail_length*3] to lights_sml[3*49] are the strand on the small moon
    # lights_sml[0] to [(tail_length-1)*3] are the tail between moons

    # DMX goes here

        
    print(coords_big)
    print(coords_meta_big)
    print(coords_sml)
    print(coords_meta_sml)
    print(rgbarray_big)
    print(rgbarray_sml)
    
    #texture_big.show()
    
    
## SAMPLE OF ANIMATION LOADER

    # Format for animations:
    # Anything that can be loaded by Pillow
    # One sequence per folder
    
    seqfolder = "animation-test"
    seqname = "testseq{:03d}.png"  # in format() format  
    seqrate = 24  # fps 
    seqlen = 0 # frames 
    
    filenames = [ f for f in listdir(seqfolder) if isfile(join(seqfolder,f)) ]
    sequence_pre = []
    t_max = 0 
    for f in filenames:
        try:
            n = parse(seqname, f)[0]   # exception thrown if parsing doesn't match
            t = float(n) / float(seqrate)
            if t > t_max: t_max = t
            sequence_pre.append({'t_abs':t, 'n':n, 'filename':join(seqfolder,f)})
            #print ("time %05.2f sec, frame %04d, %s" % (t, n,f))
        except:
            print("Exception parsing filename %s %s" % (f, sys.exc_info()[0]))
            #raise
    
    # sort by frame position
    sequence_pre = sorted(sequence_pre, key = lambda seq:seq['n'])
    sequence = []
    for frame in sequence_pre: 
        try:
            frame['t'] = frame['t_abs'] / t_max  # add normalized time
            print ("Loading t=%0.03f %04d %s" % (frame['t'], frame['n'], frame['filename']))
            rgbarray_big = [0] * 3 * coords_meta_big["max_id"] 
            rgbarray_sml = [0] * 3 * coords_meta_sml["max_id"]  
            texture = Image.open(frame['filename']).convert('RGB')
            fill_light_array(rgbarray_big, texture, coords_big)
            fill_light_array(rgbarray_sml, texture, coords_sml)
            frame['rgbarray_big'] = rgbarray_big 
            frame['rgbarray_sml'] = rgbarray_sml   
            # TODO: Calc tail 
            sequence.append(frame) # no exception thrown by this point, add to final list
        except:
            print("Exception processing filename %s %s" % (frame['filename'], sys.exc_info()[0]))
            #raise
    seqlen = len(sequence)
    print ("Total memory consumed by animation: %d kb for %d steps" % (int(sys.getsizeof(sequence)/1024 + 0.5), seqlen) )
      
    # result
    # dict with keys t, t_abs, n, filename, rgbarray_big, rgbarray_sml 
    
    # Test getting the lighting string for a particular normalized time
    
    t = 0.25 
    k = int(math.floor(t*seqlen))
    frame = sequence[k]
    print ("\nQuery %0.3f, Accessing t=%0.03f %04d %s" % (t, frame['t'], frame['n'], frame['filename']))
    print (frame)
       
     
    
