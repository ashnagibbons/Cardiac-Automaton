import random
import math
import numpy as np
import os




def initialize(percentFibril = .15, 
               fibrilLength = 5, 
               defaultRefractoryPeriod = 49, 
               patchRefractoryPeriod = 53, 
               gridDimension1 = 576, 
               gridDimension2 = 576,
               gridDimension3 = 5, 
               patchDim1 = 50, 
               patchDim2= 20,
               patchDim3 = 2,
               inputPatches = False):

    #assign all variables
    percentFib = percentFibril
    fibLength = fibrilLength
    dRefracPer = defaultRefractoryPeriod
    pRefracPer = patchRefractoryPeriod
    rows = gridDimension1
    cols = gridDimension2
    z = gridDimension3

    #arrays: excitable, lastactivated, activatenext, refracPer
    excitable = np.ones((rows, cols, z), dtype=np.int64)
    refracPer = np.full((rows, cols, z), dRefracPer, dtype=np.int64)
    lastActivated = np.full((rows, cols, z), -9999, dtype=np.int64)
    activateNext = np.full((rows, cols, z), -9999, dtype=np.int64)
    
    
    #calculate number of fibrils 
    fibrosisCover = math.floor(rows*cols*z*percentFib)
    halfDist = fibLength//2
    numFibrils = math.floor(fibrosisCover/fibLength)

    #place fibers
    for i in range(numFibrils):
        fibCenterX = random.randint((halfDist-1), rows-(halfDist+1))

        fibCenterY = random.randint((halfDist-1), cols-(halfDist+1))

        fibCenterZ = random.randint((halfDist-1), z-(halfDist+1))

        direction = random.randint(0, 2)

        if (direction == 0):
            for i in range(fibLength):
                excitable[fibCenterX + i - halfDist, fibCenterY, fibCenterZ] = 0
        elif (direction == 1):
            for i in range(fibLength):
                excitable[fibCenterX, fibCenterY+i - halfDist, fibCenterZ] = 0
        else:
            for i in range(fibLength):
                excitable[fibCenterX, fibCenterY, fibCenterZ+i-halfDist] = 0
        
    #place refrac patches
    if(inputPatches):
        refracPatch1 = input(f"""Please input the coordinates of the node at the top left corner of the first refractory\n
                            patch in the format x,y,z. Please note the patch must fit in the\n
                            matrix, so please do not input an x more than {rows - patchDim1}, a y more than {cols - patchDim2}\n
                            or a z more than {z - patchDim3}.""")

        patch1x = int(refracPatch1.split(',')[0])
        patch1y = int(refracPatch1.split(',')[1])
        patch1z = int(refracPatch1.split(',')[2])

        refracPatch2 = input(f"""Please do the same for the second refractory patch in the same format. \n
                                 Limits are to x < {rows - patchDim2}, y < {cols - patchDim1}, and z < {z-patchDim3}.""")
        
        patch2x = int(refracPatch2.split(',')[0])
        patch2y = int(refracPatch2.split(',')[1])
        patch2z = int(refracPatch2.split(',')[2])
    else:
        patch1x = 395
        patch1y = 386
        patch1z = 2

        patch2x = 485
        patch2y = 495
        patch2z = 2
    

    for i in range(patchDim1):
        for j in range(patchDim2):
            for k in range(patchDim3):
                refracPer[patch1x + i, patch1y + j, patch1z+k] = pRefracPer
    

    for i in range(patchDim2):
        for j in range(patchDim1):
            for k in range(patchDim3):
                refracPer[patch2x + i, patch2y + j, patch2z + k] = pRefracPer

    # Clear fibrosis from patch regions 
    excitable[patch1x:patch1x+patchDim1, patch1y:patch1y+patchDim2, patch1z:patch1z+patchDim3] = 1
    excitable[patch2x:patch2x+patchDim2, patch2y:patch2y+patchDim1, patch2z:patch2z+patchDim3] = 1
 
    path = input("Input the absolute path to the directory in which files for this instance will be saved.\n")

    os.mkdir(path)

    return excitable, refracPer, lastActivated, activateNext, path

def read_color_palette(path): 
    #put your own path to the colorscale.txt file when you download it
    colorfile = open(path)
    colors = colorfile.readlines()
    rgb_colors = []

    for line in colors:
        rgb_line = [int(x) for x in line.split()]
        rgb_colors.append(rgb_line)

    return rgb_colors

 
def iter_epochs(excitable, refracPer, lastActivated, activateNext, save_path, color_palette_path, num_epochs = 1234, stimInt = 51, aniso = 'x'):

    color_matrix = np.array(read_color_palette(color_palette_path), np.float32)/255.0

    init_coords = input("Please input the coordinates from where the stimulus will initiate in the form x,y,z: ")
    init_point_x = int(init_coords.split(',')[0])
    init_point_y= int(init_coords.split(',')[1])
    init_point_z = int(init_coords.split(',')[2])
    
    lastActivated[init_point_x, init_point_y, init_point_z] = 0
    activateNext[init_point_x, init_point_y, init_point_z] = 1

    
    frames_path = os.path.join(save_path, 'frames')
    os.makedirs(frames_path, exist_ok=True)

    for epoch in range(num_epochs):#runtime = num_epochs * 2 ms
      

        timeSinceActivated = epoch - lastActivated
        color_idx = np.clip(1 + (timeSinceActivated * 998 // 500), 1, 999).astype(np.int64)

        color_idx[lastActivated == -9999] = 0
        color_idx[lastActivated == epoch + 1] = 0
        color_idx[excitable == 0] = 0
        
        mask = color_idx > 0
        coords = np.argwhere(mask).astype(np.float32)
        colors = (color_matrix[color_idx[mask]] * 255).astype(np.uint8)

        np.savez_compressed(os.path.join(frames_path, f'epoch_{epoch}.npz'),
                        coords=coords, colors=colors)
        
        
        if epoch == stimInt:
            activateNext[init_point_x, init_point_y, init_point_z] = stimInt
        
        firing = (activateNext == epoch)

        lastActivated[firing] = epoch

        can_fire = (excitable == 1) & (epoch - lastActivated > refracPer)

        from_left  = np.roll(firing,  1, axis=1);  from_left[:,  0] = False
        from_right = np.roll(firing, -1, axis=1);  from_right[:,-1] = False
        from_above = np.roll(firing,  1, axis=0);  from_above[0, :] = False
        from_below = np.roll(firing, -1, axis=0);  from_below[-1,:] = False
        from_front = np.roll(firing, 1, axis=2); from_front[:, :, 0] = False
        from_behind = np.roll(firing, -1, axis=2); from_behind[:, :, -1] = False

        if aniso == 'x':
            activateNext[(from_left | from_right) & can_fire] = epoch + 2
            activateNext[(from_above | from_below) & can_fire] = epoch + 1
            activateNext[(from_front | from_behind) & can_fire] = epoch + 1
        elif aniso == 'y':
            activateNext[(from_above | from_below) & can_fire] = epoch + 2
            activateNext[(from_left | from_right) & can_fire] = epoch + 1
            activateNext[(from_front | from_behind) & can_fire] = epoch + 1
        elif aniso == 'z':
            activateNext[(from_front | from_behind) & can_fire] = epoch + 2
            activateNext[(from_above | from_below) & can_fire] = epoch + 1
            activateNext[(from_left | from_right) & can_fire] = epoch + 1
    

    print(f"Instance successfully stored in {save_path}")


def main():
    excitable, refracPer, lastActivated, activateNext, path = initialize(percentFibril=.3, defaultRefractoryPeriod=40, patchRefractoryPeriod=55)
    iter_epochs(excitable, refracPer, lastActivated, activateNext, path, color_palette_path='/Users/ashnagibbons/Documents/CMP487/FinalFiles/colorscale.txt')

if __name__ == "__main__":
    main()


